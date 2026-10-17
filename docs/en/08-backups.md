# 08 — Backups and rollback

Complete catalog of what we have as backup, what it's for, and what we **don't** have (remaining risks).

## Backup matrix

### ✅ What we have in the project

| Artifact | Location | Size | Reproducible? | Use case |
|---|---|---|---|---|
| **OTA INSTALL package** | `tooling/ota-build/output/<ts>/0040/SwUpdate.mdt` | 870 KB | ✅ Via `build.py` | Re-install AutoOk+su |
| **OTA ROLLBACK package** | `tooling/ota-build/output-rollback/<ts>/0040/SwUpdate.mdt` | 870 KB | ✅ Via `build-rollback.py` | Remove AutoOk+su |
| **Compiled APK** | `our-apk/app/build/outputs/apk/release/AutoOk.apk` | 17 KB | ✅ Via `./gradlew assembleRelease` | Binary reproducibility |
| **APK source** | `our-apk/app/src/` | ~5 KB | — | Future APK modification |
| **Pre-deploy /system dump** | `tooling/apks-dumped/dump-0040/` | 192 MB | ⚠️ Requires dumping via car | Inspection, post-deploy comparison, find coords/activity in adjacent firmware |
| **Final install logs** | `docs/fase7-deploy-2026-10-16/artefatos-deploy/install-0040-final.log` | <2 KB | — | Proof deploy worked |
| **Raw bootable dumps** | `~/backup-honda-civic-g10/dump-raw-2026-10-17/*.img.gz` | 275 MB | ⚠️ Via `build-dump-raw.py` + car | Full restore via `dd` reverse |

### ❌ What we DON'T have — remaining risks

| Missing | Risk | Possible mitigation |
|---|---|---|
| **Bootloader + recovery image** (NOR flash) | If bootloader/recovery corrupts, only JTAG fixes | Dump via `dd if=/dev/mtd/mtd2 of=...` inside updater-script (complex) |
| **/data backup** | Lose saved configurations (paired Bluetooth, presets, etc.) | Dump via OTA package |

**In other words:** our rollback covers "APK had a problem, want to go back to normal". **Does NOT cover** "HU bricked and I need to restore entire firmware" (unless you built raw bootable dumps — then it does, within limitations).

For firmware `1.F187.16` BR, brick risk with our procedure is low:
- We never modify existing `/system` files
- We only add 2 new files (AutoOk.apk + su)
- Updater-script uses edify `mount`/`unmount` official from AOSP recovery
- Deploy test successful 2026-10-16

But risk is **never zero** with firmware modification in an automotive system. For maximum safety margin, consider making raw backup (section below).

## Simple rollback

**Scenario:** you want to remove `AutoOk.apk` and `su` from `/system`. HU returns to original state.

### Prerequisites
- Rollback package already built in `tooling/ota-build/output-rollback/<ts>/0040/SwUpdate.mdt`.
- Available FAT32 MSDOS pendrive.
- Car accessible + `AUDIO 5s` combo works.

### Procedure
Detailed in [`07-rollback.md`](07-rollback.md). Summary:

```bash
sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sdX
# Then in the car: front port + AUDIO 5s + confirm reboot
```

Time: ~5 min on laptop + ~10 min in car.

## Emergency rollback

**Scenario:** HU in boot loop, won't boot normally, bigger problem.

See [`07-rollback.md § Emergency rollback`](07-rollback.md#emergency-rollback).

Options (in order of nuclearity):
1. OTA rollback deploy (if HU still reaches recovery)
2. Pull radio fuse for 15-20 min (forces full shutdown)
3. Disconnect battery for 30 min (total reset)
4. HU replacement (R$ 1,000-2,000 / ~USD 200-400)

## Raw partition backup (optional, but recommended)

For total safety margin, we can build an **OTA package that dumps the entire `APP` and `CAP` and `MITSU` partitions** to the pendrive. This gives:
- `app.img.gz` (~110 MB gzipped from 512 MB) — bootable image of `/system`
- `cap.img.gz` (~130 MB gzipped from 768 MB) — image of `/system/vendor`
- `mitsu.img.gz` (~40 MB gzipped from 1 GB) — image of `/data/MitsubishiElectric`

Restoration would be via another OTA package that `dd`s the raw image back to the partition. This is the **only real way** to have complete recovery without JTAG.

**Build this backup:**

```bash
python3 tooling/ota-build/build-dump-raw.py
sudo ./tooling/scripts/prepare-pendrive-dump-raw.sh /dev/sdX
# Deploy in car: ~18 min
```

Package already exists in the project. See [`04-build-do-pacote.md § Step 6`](../pt-BR/04-build-do-pacote.md).

Pendrive needs at least 2 GB free.

## Verify backup status

Helper script that lists what's present:

```bash
./tooling/scripts/verificar-backups.sh
```

Output shows what each folder has, SHA-1 of critical files, and warns if anything is missing.

## Reproducibility

Any of these backups can be rebuilt if lost:

### Rebuild INSTALL package

```bash
cd our-apk
./gradlew clean assembleRelease
$ANDROID_SDK_ROOT/build-tools/33.0.2/apksigner sign \
  --ks ~/.android/debug.keystore --ks-pass pass:android \
  --out app/build/outputs/apk/release/AutoOk.apk \
  app/build/outputs/apk/release/app-release-unsigned.apk
cp app/build/outputs/apk/release/AutoOk.apk \
   ../tooling/ota-build/overlay/system/app/AutoOk.apk
cd ..
python3 tooling/ota-build/build.py
```

Result in `tooling/ota-build/output/<timestamp>/0040/SwUpdate.mdt`.

### Rebuild ROLLBACK package

```bash
python3 tooling/ota-build/build-rollback.py
```

Result in `tooling/ota-build/output-rollback/<timestamp>/0040/SwUpdate.mdt`.

### Re-dump /system

Procedure in [`../fase7-deploy-2026-10-16/06-dumps-obtidos.md § Como re-dumpar`](../fase7-deploy-2026-10-16/06-dumps-obtidos.md#como-re-dumpar) (Portuguese). Requires:
- Temporarily modify `build.py` to generate dump updater-script (not install)
- Deploy in car via normal protocol
- Pendrive comes back with 192MB of dumps

### Reproduce APK with same SHA-1

**Not guaranteed.** APKs signed with debug keystore have SHA-1 that depends on internal timestamp and local keystore. To reproduce identical SHA-1, you'd need the same `~/.android/debug.keystore`. For your peace of mind, the SHA-1 of your final deploy is in the artifact manifest: `docs/fase7-deploy-2026-10-16/02-descobertas-tecnicas.md § Hardware version`.

## What to do NOW to have 100% guaranteed rollback

Checklist before any future modification or long absence:

- [ ] ROLLBACK package built and verified via `verificar-backups.sh`
- [ ] Extra pendrive FAT32 MSDOS loaded with ROLLBACK (keep in glove compartment)
- [ ] Raw image of APP+CAP+MITSU dumped and saved on laptop (optional but recommended)
- [ ] Backup of `~/.android/debug.keystore` in a safe location (to re-sign a compatible APK)

## In case of official Honda OTA update

If Honda issues an OTA (unlikely for 2017 firmware but possible):
1. **Before applying their OTA**: deploy our ROLLBACK to remove our files.
2. Apply the Honda OTA normally.
3. Post-OTA: dump the new `/system` to see what changed (new rom_type? new warning layout?).
4. Adjust `build.py` and `AutoOkConfig.java` with new values.
5. Redeploy.

Procedure in [`../fase7-deploy-2026-10-16/05-manutencao-e-futuro.md § Após atualização OTA Honda`](../fase7-deploy-2026-10-16/05-manutencao-e-futuro.md#após-atualização-ota-honda) (Portuguese).
