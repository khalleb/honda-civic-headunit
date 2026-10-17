# 07 — Rollback (remove AutoOk + su)

If you need to revert the modification — crash, instability, pending Honda update, any reason — this is the procedure.

**Rollback is SYMMETRIC to deploy.** Same pendrive, same car protocol, but different package.

## When to rollback

- APK causing crashes/instability (very rare — our modification is surgical)
- Before applying an official Honda OTA update
- Selling the car (leave it in original state)
- Any doubt/regret
- Diagnosis — temporarily remove to isolate whether a problem comes from our mod

## Procedure

### 1. Build the rollback package (if not done yet)

```bash
cd /path/to/project
python3 tooling/ota-build/build-rollback.py
```

Output:

```
INFO: rollback mdt: tooling/ota-build/output-rollback/<timestamp>/0040/SwUpdate.mdt
```

### 2. Load pendrive

```bash
sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sdX
```

The script:
1. Checks that `/dev/sdX` is USB (guards against formatting the SSD)
2. Mounts the pendrive
3. Deletes all existing content
4. Copies the rollback package (busybox + sleep + removal updater-script)

### 3. Deploy in the car

Same protocol as the install deploy:

1. **Pendrive into the front USB-A port**
2. **Car on**
3. **`AUDIO 5s`** → "Reboot?" → **confirm**
4. "Software update → Copying" flow appears
5. HU reboots → recovery applies → normal reboot
6. When HU returns to the normal screen, **remove the pendrive**

## What the rollback does

Internally, the updater-script in recovery:

1. Mounts `/system` via edify (partition `APP` = `mmcblk0p3`)
2. `rm -f /system/app/AutoOk.apk`
3. `rm -f /system/xbin/su`
4. Confirms removal by listing both (should return "No such file or directory")
5. `sync` + unmount
6. Sleep 30s window for pendrive removal

Writes `rollback-0040.log` to the pendrive with each step's output — for later verification.

## Verify removal

After deploy, plug pendrive into laptop, open `rollback-0040.log`:

```
=== ROLLBACK START Fri Oct XX ... ===
-rw-r--r-- ... AutoOk.apk           ← existed, was removed
-rwsr-sr-x ... su                   ← existed, was removed
rm-done
removal-confirmed                   ← both successfully removed
=== ROLLBACK END ... ===
```

If you see `removal-confirmed`, rollback worked.

After this, when you turn on the car again:

- Warning appears normally, you need to manually tap OK (as before)
- No visual sign that the APK/su ever existed
- Android services (CarPlay, Bluetooth) remain intact

## Emergency rollback (HU won't boot)

Rare scenario: APK or another problem causes boot loop. Procedure:

1. **Don't panic.** OTA rollback should still work.
2. Plug rollback pendrive into front port.
3. **Combo `AUDIO 5s`** to force reboot.
4. Flow should apply — recovery picks up the package.
5. If it works, done.

If even OTA rollback doesn't work (HU in permanent recovery loop or endless boot loop), options:

- **Pull the radio fuse** from the interior fuse box for 15-20 minutes. Forces full HU shutdown, may unlock.
- **Disconnect car battery** (negative) for 30 minutes. Nuclear option — total reset.
- **Replace the HU** — last resort, R$ 1,000-2,000 (~USD 200-400).

See [`docs/fase7-deploy-2026-10-16/05-manutencao-e-futuro.md § Troubleshooting`](../fase7-deploy-2026-10-16/05-manutencao-e-futuro.md#troubleshooting) for detailed troubleshooting (Portuguese).

## After rollback — can I reinstall?

Yes. Everything you did for the initial deploy works again. Same OTA install package, same protocol. But remember:

- If you changed anything in the APK/updater-script since last time, rebuild first.
- If you changed pendrive, verify it's correctly FAT32 MSDOS.

## Safety net: have rollback ready ALWAYS

**Rule:** never deploy the INSTALL package without the ROLLBACK package already built and accessible on the laptop.

```
tooling/ota-build/output-rollback/<timestamp>/0040/SwUpdate.mdt
```

If for any reason you need to revert quickly, you already have it.

For travel/long distance situations, consider having an extra pendrive already loaded with rollback — kept in the glove compartment, ready if needed.
