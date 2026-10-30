# 09 — Phase 10: remove the warning for good (patch DaLauncher)

This guide is for applying **Layer 2** of the solution — the smali patch in `DaLauncher.apk` that makes the warning **never appear** in the boot flow. Successfully applied on the Brazilian 2017 Civic EXL on 2026-10-29 (see [`fase10-deploy-2026-10-29/README.md`](fase10-deploy-2026-10-29/README.md)).

**Mandatory prerequisite:** Layer 1 (AutoOk) already deployed and stable for at least one week. Phase 10 **replaces** the warning with a short ecoscore screen (~1 s) and depends on the 4 post-warning calls that AutoOk also triggered, so having both active is the safest configuration during the transition.

## Why do it

| With | Experience | Risk |
|---|---|---|
| Layer 1 only (AutoOk) | Warning appears and vanishes in ~3 s | Minimal |
| **Layers 1 + 2 (Phase 10)** | **Warning never appears.** Ecoscore screen for ~1 s | Medium (patches the main launcher; safety net = DaLauncher restore package) |

Layer 2 is worth it if the visual noise of the warning on every boot bothers you. Otherwise, stopping at Layer 1 is fine.

## What the patch does

Inside `com.mitsubishielectric.ada.app.dalauncher.OpeningDivideActivity` (the warning Activity), one bytecode line decides between two destinations:

- `sDisclamerFlg == false` → `DisclaimerFragment` (the warning you know)
- `sDisclamerFlg == true`  → `EcoFragment` (branch that was dead because the flag always starts `false`)

Our patch 1 ignores the flag:

```diff
     sget-boolean v0, Lcom/mitsubishielectric/ada/app/dalauncher/OpeningDivideActivity;->sDisclamerFlg:Z

-    if-nez v0, :cond_9
+    goto :cond_9

     invoke-direct {p0}, Lcom/mitsubishielectric/ada/app/dalauncher/OpeningDivideActivity;->createDisclaimerOnHomeIntent()Landroid/content/Intent;
```

Result: always goes to the `EcoFragment`, which triggers in `startNextActivity()` **the 4 calls CarPlay/Navigation/SystemDisplay expect** after the warning is dismissed — so nothing breaks.

Patch 2 (Phase 10.1) reduces the EcoFragment timer:

```diff
     iget-object v0, p0, ...->mNoOperationTimer:Lcom/mitsubishielectric/ada/app/dalauncher/CommonTimer;

-    const/16 v1, 0x1388        # 5000 ms
+    const/16 v1, 0x1f4         # 500 ms

     invoke-virtual {v0, v1, v2}, ...CommonTimer;->start(ILcom/mitsubishielectric/ada/app/dalauncher/CommonTimer$TimerCallBack;)V
```

Eco screen stays visible for ~1 s instead of ~6 s. Leaving 500 ms (not 0 ms) is necessary because AutoOk v0.5.4 keeps tapping `(400, 350)` ~1 s after boot — with 500 ms the tap still lands on the safe background of the EcoFragment (no clickable widget in either `mm_07_04_06` / `_ziba` layouts at that coordinate).

## Prerequisites

### Hardware
- G10 Civic with Layer 1 (AutoOk v0.5.4) already applied and stable
- **2 FAT32 USB sticks** (or 1 stick, prepared twice)
- Linux PC

### PC software
- JDK 17 (`~/sdks/jdk-17/bin/java` or `/usr/lib/jvm/java-17-openjdk-devel`)
- Android SDK build-tools 33.0.2 (for `apksigner` and `zipalign`)
- Python 3.12 stdlib (no extras)
- Dump of your firmware's `/system/vendor/app/DaLauncher.apk` + `DaLauncher.odex` in `tooling/apks-dumped/dump-0040/vendor-app/` — from the firmware discovery process, see [`03-finding-your-firmware.md`](03-finding-your-firmware.md)

### Verify invariant
```bash
python3 -m unittest discover -s tooling/ota-build/tests
# Expected: 42 tests OK
```

## Step 1 — Build the patched APK

```bash
cd honda-civic-headunit
export PATH="$HOME/sdks/jdk-17/bin:$PATH"
bash tooling/fase10/rebuild-dalauncher.sh
```

The script:
1. Deodexes `DaLauncher.odex` fresh with baksmali
2. Applies both versioned patches (`opening-divide-activity-skip-disclaimer.patch` + `eco-fragment-reduce-timer.patch`)
3. Verifies each patch landed in the expected place
4. Builds the new `classes.dex` with smali
5. **Proves** the orig→patch bytecode diff is **exactly** `EcoFragment.smali` + `OpeningDivideActivity.smali` (fails otherwise)
6. Repackages the APK, removes old META-INF, injects `classes.dex`
7. Zipaligns 4
8. Signs with AOSP testkey
9. Verifies the cert is the expected AOSP testkey

Output:
```
OK.
  saida:  tooling/fase10/output/DaLauncher-fase10.apk
  size:   17798948 bytes
  cert:   a40da80a... (AOSP testkey)
  sha256: 65481d45acd01ad67359b1174b57150eecb959377bde3379a30e2eb17a8d4a4c
```

## Step 2 — Build the OTA packages

```bash
# Phase 10 install (will apply the patched APK)
python3 tooling/ota-build/build-dalauncher-fase10.py

# Original DaLauncher restore (safety net — use to abort)
python3 tooling/ota-build/build-dalauncher-restore.py
```

Result: two packages in `tooling/ota-build/output-dalauncher-{fase10,restore}/<timestamp>/0040/SwUpdate.mdt`. Save the printed SHA-256s to verify later.

## Step 3 — Prepare the USB sticks

```bash
# Stick A — ROLLBACK (safety net, apply FIRST to validate the path)
sudo tooling/scripts/prepare-pendrive-rollback.sh /dev/sdX tooling/ota-build/output-dalauncher-restore

# (after §4 validated, repeat with Stick B)
# Stick B — INSTALL (applies the real patch)
sudo tooling/scripts/prepare-pendrive-install.sh /dev/sdY tooling/ota-build/output-dalauncher-fase10
```

The script asks `yes` before wiping, shows model+label+contents, writes, verifies the SHA-256 read back from the drive against the build, and unmounts. **If the SHA doesn't match, it exits with error and the stick does not go to the car.**

## Step 4 — Validate the rollback in the car (intentional no-op)

**Before installing anything new**, apply the rollback package. Since the DaLauncher in your car today = DaLauncher original expected by the rollback, this is a **byte-identical no-op**: validates mount + extract + perms + md5 + loop break + unmount without real risk.

1. Stick A into the front USB-A port
2. Key in ON (not START)
3. **AUDIO 5 s** → "Restart?" → **OK**
4. Wait ~2 min, pull the stick when the screen comes on for the third time
5. **On the PC**, plug Stick A back in and verify:
   - `ROLLBACK-RESTORED.OK` exists (and `.FAIL` does **not**)
   - In `dalauncher-restore-0040.log`:
     - `restore-verified-OK`
     - `mv-trigger-exit=0`, `rm-copy-complete-exit=0`
     - `chown-exit=0 chmod-exit=0` on both `perm` lines (APK and odex)

If any gate fails: **do not proceed to step 5.** Investigate first.

## Step 5 — Deploy Phase 10

Only proceed if §4 passed everything.

1. Stick B into the front USB-A port
2. Key in ON
3. **AUDIO 5 s** → "Restart?" → **OK**
4. Wait ~2 min, pull the stick on the third screen
5. **First post-deploy boot will be slow** (~10-30 s extra — Dalvik `dexopt` on the new `classes.dex`)
6. **On the PC**, plug Stick B and verify:
   - `FASE10-ODEX-REMOVED.OK` exists (and `.FAIL` does **not**)
   - In `dalauncher-fase10-0040.log`:
     - `chown-exit=0 chmod-exit=0` on the `perm /system/vendor/app/DaLauncher.apk` line
     - md5 of the deployed APK matches the SHA that `rebuild-dalauncher.sh` printed (positive proof: patched APK is in place, not a silent restore)

## Step 6 — Validate in real use

Take a drive around the block. Check:
- Warning **does not appear**
- "-eco-" screen appears for ~1 s on every ignition
- CarPlay projects normally
- Navigation works
- Backup camera works
- Bluetooth calls work
- Steering wheel buttons work

Monitor for 1 week. If all OK, you can (optionally) run the AutoOk rollback to free up `/system`:

```bash
sudo tooling/scripts/prepare-pendrive-rollback.sh /dev/sdX tooling/ota-build/output-rollback
```

This removes `/system/app/AutoOk.apk` + `/system/xbin/su`. The Phase 10 patch stays active because it's inside the `DaLauncher.apk` itself.

## If something goes wrong

| Symptom | Action |
|---|---|
| Launcher doesn't appear (black screen or boot loop) | Apply Stick A (rollback). Normal boot returns because the original DaLauncher is restored. |
| Launcher appears but warning still appears | The patch may not have been applied. Check the APK md5 in `dalauncher-fase10-0040.log`. |
| CarPlay won't project | The Eco path may not have emitted `setDisplayPermission`. Investigate the `logcat.txt` on the stick. |
| Real boot loop (head unit reboots continuously) | Stick A before key-on + AUDIO 5 s. If even that doesn't help: `~/backup-honda-civic-g10/dump-raw-*.img.gz` + external tool. |

Full decision tree: [`06-troubleshooting.md`](06-troubleshooting.md). Minute-by-minute checklist: [`../fase10-execucao-2026-10-27.md`](../fase10-execucao-2026-10-27.md) (Portuguese).

## Understanding what happens under the hood

See [`DISCOVERIES.md`](../../DISCOVERIES.md) for the technical details:
- How `sDisclamerFlg` is a `static boolean` in memory that resets to `false` on every boot
- Why the Eco path (`createEcoIntent()`) existed but never ran before the patch
- Which 4 calls the `EcoFragment` triggers that keep the rest of the system working

Full timeline of the real deploy in [`fase10-deploy-2026-10-29/README.md`](fase10-deploy-2026-10-29/README.md).

Route decision discussion (resign with AOSP testkey vs. odex-level patch): [`../fase10-decisao-rotas-2026-10-23.md`](../fase10-decisao-rotas-2026-10-23.md) (Portuguese).
