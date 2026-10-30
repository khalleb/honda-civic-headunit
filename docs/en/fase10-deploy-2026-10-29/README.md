# Phase 10 — Deploy result (2026-10-29)

Deploy executed on 2026-10-29 (postponed from 2026-10-27 due to car availability). This document is the final record of what happened, based on the `.OK/.FAIL` gate, the updater-script logs and the `logcat.txt` / `kmsgcat.txt` the HU wrote to the pendrive at each step. Checklist followed in full (Portuguese): [`../../fase10-execucao-2026-10-27.md`](../../fase10-execucao-2026-10-27.md).

## Result in one line

**The opening warning is gone for good.** The 1-instruction smali patch in `DaLauncher.apk` forces the boot flow to skip the `DisclaimerFragment` and fall straight into the `EcoFragment`, which then hands off to `CarPlayMainActivity`. CarPlay projecting, navigation working, zero crashes across boots. A Phase 10.1 prepared the same day cuts the Eco screen from ~6 s down to ~1 s via a second 1-instruction smali patch.

## Timeline

### §2.1 — Rollback package validation (10:00 BRT)

**Goal:** prove the safety net works before risking the install. Since the DaLauncher on the car matched the original the rollback expected, the result had to be a no-op (identical bytes written over themselves).

Package: `tooling/ota-build/output-dalauncher-restore/20261027T020209Z/0040/SwUpdate.mdt` (SHA-256 `6445ec80…`).

Result:
- Gate `ROLLBACK-RESTORED.OK` present, content `OK`
- `ROLLBACK-RESTORED.FAIL` absent
- `restore-verified-OK` in `dalauncher-restore-0040.log`
- `mv-trigger-exit=0`, `rm-copy-complete-exit=0` (loop break confirmed)
- `chown-exit=0 chmod-exit=0` on both `perm` lines (APK and odex) — **first time busybox `chown`/`chmod` ran on this car** (§17.18)
- md5 pre-restore == md5 post-restore for APK and odex → identical-byte no-op as predicted
- Updater-script duration: 6 s (`12:56:47 → 12:56:53 UTC`)
- CAP mounted as ext4 (without CAP the odex `.OK` would be a false positive — §17.18)

Logs preserved in `~/backup-honda-civic-g10/pendrive-fase10-restore-2026-10-29/`.

### §2.2 — Phase 10 deploy (10:10 BRT)

Package: `tooling/ota-build/output-dalauncher-fase10/20261027T020208Z/0040/SwUpdate.mdt` (SHA-256 `4c31cb4d…`, APK `1774136c…`, md5 `fc8e87f6…`).

Updater-script result:
- Gate `FASE10-ODEX-REMOVED.OK` present, content `removed`
- `.FAIL` absent
- `odex-removed-OK` in the log
- `chown-exit=0 chmod-exit=0` on the `perm /system/vendor/app/DaLauncher.apk` line
- post-deploy APK md5 = `fc8e87f6bba2713c0703f6b9d37a29cf` ← **positive proof** (closes the false `.OK` of §17.18: it's the patched APK on the device, not a silent restore)
- Loop break OK, duration 5 s (`13:11:44 → 13:11:49 UTC`)
- daupdater `result.log` present with `OK` (missing in §2.1)

**In the car, with the patch now active (next boot, 13:13 UTC):**

```
13:13:12.503 — ActivityManager starts OpeningDivideActivity (NORMAL_STARTUP)
13:13:13.103 — OpeningDivideActivity.onCreate (patched class)
13:13:13.673 — OpeningDivideActivity.createEcoIntent():EcoStart!  ← first time on this car
13:13:13.763 — EcoFragment.onCreateView                           ← "-eco-" screen shows
13:13:14.053 — EcoFragment.onResume / onServiceListComplete
… 6 s of Eco screen …
13:13:19.823 — EcoFragment.startNextActivity → CarPlayMainActivity
13:13:19.833 — NavigationApService.disclaimerDisappeared
13:13:19.863 — AppManagerService.setDisclaimerPassed(true)
13:13:19.863 — CarPlayApService.setDisplayPermission(status=true)  ← CarPlay unlocked
13:13:19.873 — DISCLAIMER_COMPLETE broadcast fired
13:13:19.933 — EcoFragment.onPause / onDestroy
13:13:21.503 — reasserts setDisclaimerPassed + setDisplayPermission
13:13:35.763 — reasserts a 3rd time (final boot)
13:13:31+   — NavigationApService active (TBT, RDS-TMC, NMEA)
```

Zero stacktraces in `logcat`, zero errors in `kmsg`. Logs in `~/backup-honda-civic-g10/pendrive-fase10-install-2026-10-29/`.

### Side note: the "-eco-" screen (10:20 BRT)

After the deploy, the HU started showing a screen titled **-eco-** with three leaf bars (ecoscore) for ~6 s before reaching the main launcher. **This screen had never been seen by the car's owner** — not even before our project. Why:

The original flow inside `OpeningDivideActivity` tested `sDisclamerFlg` (`static boolean` in memory, §17.16) and had two destinations:
- `sDisclamerFlg == false` → `createDisclaimerOnHomeIntent()` → `DisclaimerFragment` (the warning)
- `sDisclamerFlg == true`  → `createEcoIntent()` → `EcoFragment` (never reached)

Since `sDisclamerFlg` **resets to `false` on every class boot**, the `EcoFragment` was dead code in real use. The patch (`if-nez v0, :cond_9` → `goto :cond_9`) ignores the flag and always routes to `createEcoIntent()`. Result: the Eco screen woke up for the first time on this car, exactly as MAPA §11.1.1 predicted.

**Decision:** the Eco path wasn't picked by chance — `EcoFragment.startNextActivity()` is what fires the 4 calls CarPlay / Navigation / SystemDisplayApService expect (`disclaimerDisappeared`, `setDisclaimerPassed(true)`, `setDisplayPermission(true)`, `DISCLAIMER_COMPLETE` broadcast). Skipping Eco without reimplementing those calls would break CarPlay. But shrinking the `EcoFragment` time to near-zero preserves the 4 calls and visually makes the screen "blink". That's the Phase 10.1 patch.

## Phase 10.1 — shrink the Eco screen

Second smali patch, one instruction, in `EcoFragment.startNoOperationTimer()`:

```diff
     iget-object v0, p0, ...->mNoOperationTimer:Lcom/mitsubishielectric/ada/app/dalauncher/CommonTimer;

-    const/16 v1, 0x1388
+    const/16 v1, 0x1f4

     iget-object v2, p0, ...->mNoOperationTimerCallBack:...
     invoke-virtual {v0, v1, v2}, ...CommonTimer;->start(ILcom/mitsubishielectric/ada/app/dalauncher/CommonTimer$TimerCallBack;)V
```

- `0x1388` = 5000 ms (factory default, confirmed in today's logs = 5 s of timer + ~770 ms of animation = the 6 s observed)
- `0x1f4` = 500 ms
- **Expected result:** Eco screen visible for ~1 s (500 ms timer + animation)
- **Kept intact:** `onServiceListComplete`, the callback that fires `startEndAnimeAndNextActivity → startNextActivity → DISCLAIMER_COMPLETE + setDisplayPermission + disclaimerDisappeared + setDisclaimerPassed`. Only the gap between `onServiceListComplete` and `onTimerComplete` shrinks.
- **Not touched:** EcoFragment's `displayOffTimerStart()` (the fragment's internal screensaver, also `0x1388`, unrelated to our flow).

### Why 500 ms and not 0 ms

From today's timeline, AutoOk v0.5.4 is still active in the system (safety net of §4.1) and taps `(400, 350)` **~1 s after** the `am_create_activity` of `OpeningDivideActivity`. With the Phase 10 patch:

- `13:13:13.103` — AutoOk detects the `am_create_activity`
- `13:13:14.103` — AutoOk taps (DELAY_SECONDS_AFTER_DETECT = 1 s)

With the Eco screen at 500 ms:
- `13:13:13.763` — `EcoFragment.onCreateView`
- `13:13:14.263` — `onTimerComplete` fires `startEndAnimeAndNextActivity`
- `13:13:14.103` — AutoOk taps → **lands on the EcoFragment background** (confirmed safe: in both layouts `mm_07_04_06`/`_ziba`, `(400, 350)` has only a background `ImageView`, nothing clickable — see [`../../raio-x/07-services-re.md`](../../raio-x/07-services-re.md) and the `cysin/honda_hacking_analysis` writeup of Eco layouts)

With a 0 ms timer the flow would end in < 500 ms and the AutoOk tap would land on `CarPlayMainActivity` or the `Launcher`, which **do** have clickable elements — risk of play/pausing music, clicking an icon, etc. 500 ms solves it without having to deploy a new AutoOk alongside or bump `BOOT_INITIAL_WAIT_MS`.

### Bytecode proof check

`tooling/fase10/rebuild-dalauncher.sh` now applies both patches and requires the DEX diff orig→patch to be **exactly** `EcoFragment.smali` + `OpeningDivideActivity.smali`. Any other class changing in the diff aborts the rebuild. Confirmed on this run:

```
confirmado: so EcoFragment e OpeningDivideActivity mudaram entre orig e patch
```

### Package ready

| Field | Phase 10 (2026-10-29 10:10 BRT) | **Phase 10.1 (prepared 2026-10-29 10:46)** |
|---|---|---|
| OTA folder | `output-dalauncher-fase10/20261027T020208Z` | `output-dalauncher-fase10/20261029T134614Z` |
| `SwUpdate.mdt` SHA-256 | `4c31cb4d018afbfcf7fc8a48c0d10d95d489fd929e3e4d4eaf98ffbb1bc02fb0` | `f571af751dc9be6619cf33e7eb5d11268dd3f004b1c93587dd47f05d6cf3f453` |
| APK SHA-256 | `1774136cfad10919eb03698badc259179521e5fe7e69b82fc349029aaceb1807` | `65481d45acd01ad67359b1174b57150eecb959377bde3379a30e2eb17a8d4a4c` |
| APK md5 (§2.2 gate) | `fc8e87f6bba2713c0703f6b9d37a29cf` | **`655c01a3b17fe20b23c70114e1e0dae7`** |
| Updater-script | — | **byte-for-byte identical to v1 (md5 `2cca09a3…`)**: the only byte different inside the `.mdt` is the APK |

The rollback (`output-dalauncher-restore/20261027T020209Z/`, SHA `6445ec80…`) **does not need to be rebuilt** — it still restores the original DaLauncher it was built for.

## How to apply Phase 10.1

Follow the same §2.2 of the checklist, just swap the expected SHA and md5.

```bash
# On the PC (sudo)
sudo tooling/scripts/prepare-pendrive-install.sh /dev/sda tooling/ota-build/output-dalauncher-fase10
```

The script picks the newest build in the directory (= `20261029T134614Z`), asks for `yes`, writes, verifies the SHA-256 read back from the pendrive. Expected:

```
OK   SwUpdate2.txt       <sha>
OK   0040/SwUpdate.mdt   f571af751dc9be6619cf33e7eb5d11268dd3f004b1c93587dd47f05d6cf3f453
```

**In the car:**
1. Pendrive in the front USB-A port, key in ON
2. AUDIO 5 s → "Restart?" → OK
3. Wait ~2 min, pull the pendrive on the third screen
4. First post-deploy boot will be slow (~10-30 s extra, `dexopt` of the new classes.dex)

**On the PC (§2.2 gate adapted for Phase 10.1):**
- `FASE10-ODEX-REMOVED.OK` present, `.FAIL` absent
- In `dalauncher-fase10-0040.log`:
  - `chown-exit=0 chmod-exit=0` for the APK
  - post-deploy APK md5 = **`655c01a3b17fe20b23c70114e1e0dae7`** (**new** — no longer `fc8e87f6…`)

**Watch on the screen:**
- Warning does **not** appear
- "-eco-" screen appears for **~1 s** (no longer 6 s)
- Main launcher / CarPlay come up normally
- CarPlay projects, navigation works, rear camera works

## Phase 10 closed

With Phase 10.1 applied, the project's original goal is met:

- Warning removed from the boot flow via a 1-instruction bytecode patch (`OpeningDivideActivity.smali:671`)
- Intermediate Eco screen reduced to ~1 s via a second 1-instruction patch (`EcoFragment.smali:3094`)
- CarPlay / Navigation / SystemDisplay get the 4 calls they needed (`DISCLAIMER_COMPLETE`, `setDisplayPermission`, `disclaimerDisappeared`, `setDisclaimerPassed`)
- Safety net tested and functional (`output-dalauncher-restore`)
- Zero `assert`/`abort` in the packages, busybox `chown`/`chmod` instead of `set_perm` on `/system` (§17.18)
- Packages signed with the AOSP testkey, accepted by our car's `daupdater`

### Post-deploy — keep the safety net

Kept §4.1 from the original checklist: AutoOk v0.5.4 stays in `/system/app/` as the net. It will keep logging `aviso detectado` + `tap ok=true` on every boot — **not a failure** (the needle matches `OpeningDivideActivity`'s `am_create_activity`, which the patch doesn't touch; only its contents changed).

Stable week starting with the Phase 10.1 deploy → one may consider removing AutoOk via its own rollback (`tooling/ota-build/output-rollback/`). Optional, with the single benefit of leaving `/system` 100% clean.

### Still open

- Documentation updated in MAPA (§10.3 new + §18 new item), ROADMAP (Phase 10 closed), CLAUDE.md (current AutoOk version stays v0.5.4), and here.
- `tooling/fase10/opening-divide-activity-skip-disclaimer.patch` and `eco-fragment-reduce-timer.patch` are the two versioned patches in the repo (sources of truth).
- `tooling/fase10/rebuild-dalauncher.sh` now applies both patches and requires the "only EcoFragment and OpeningDivideActivity changed" bytecode proof. Ran OK on 2026-10-29.

## Cross-references

- [`../../fase10-pre-planejamento-2026-10-20.md`](../../fase10-pre-planejamento-2026-10-20.md) — original technical briefing (Portuguese)
- [`../../fase10-decisao-rotas-2026-10-23.md`](../../fase10-decisao-rotas-2026-10-23.md) — Route B chosen (resign with AOSP testkey) (Portuguese)
- [`../../fase10-execucao-2026-10-27.md`](../../fase10-execucao-2026-10-27.md) — execution checklist followed in full (Portuguese)
- [`../../MAPA.md`](../../MAPA.md) §11.1.1 (internals), §16.4 (packages), §17.16 (`sDisclamerFlg` gate), §17.18 (`set_perm` on `/system`) (Portuguese)
- [`../../raio-x/07-services-re.md`](../../raio-x/07-services-re.md) — RE of the services receiving `DISCLAIMER_COMPLETE` (Portuguese)
