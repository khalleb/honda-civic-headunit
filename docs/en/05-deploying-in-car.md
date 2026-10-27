# 05 — Deploying in the car

How to transfer the OTA package from the flash drive to the head unit and apply it.

**Prerequisite:** `SwUpdate.mdt` already generated under `tooling/ota-build/output/<timestamp>/0040/`. If not, see [`04-building-the-package.md`](04-building-the-package.md).

**Mandatory safety net:** before deploying INSTALL, build the ROLLBACK package. If something goes wrong you need rollback ready on the spot. Never deploy without rollback on the laptop.

**Time:** ~5 min on the PC (prepare flash drive) + ~5-10 min in the car (OTA deploy).

---

## Part 1 — On the PC

### 1.1 Plug in the flash drive

```bash
lsblk -o NAME,SIZE,MODEL,TRAN
```

Identify the flash drive device. Example:
```
NAME        SIZE MODEL                 TRAN
sda         29G  USB  DISK            usb      ← flash drive
nvme0n1     238G INTEL SSD              nvme   ← laptop SSD, DO NOT TOUCH
```

**Confirm three times that it's the flash drive!** The wrong script on `/dev/nvme0n1` wipes the laptop SSD.

### 1.2 Prepare the flash drive (format + copy package)

```bash
# Format FAT32 MSDOS (destroys content!)
sudo ./tooling/scripts/format-pendrive.sh /dev/sda

# Copy the latest INSTALL package
sudo ./tooling/scripts/prepare-pendrive-install.sh /dev/sda
```

**What `prepare-pendrive-install.sh` does** (the shared sequence lives in `tooling/scripts/lib-pendrive.sh`, same for all five `prepare-pendrive-*.sh`):
1. Confirms `/dev/sda` is the whole disk of a USB stick (guards against `/dev/nvme` and against passing `/dev/sda1`)
2. Picks the newest build in `tooling/ota-build/output/` (or in the directory passed as the 2nd argument) and checks it has `SwUpdate2.txt` + `0040/SwUpdate.mdt` before touching the drive
3. Checks MSDOS table + vfat partition, the format the daupdater expects
4. Mounts the flash drive (or reuses the desktop mount)
5. Shows the model, label and current contents and only proceeds if you type `yes`
6. Wipes previous content and copies `SwUpdate2.txt` (trigger) + `0040/SwUpdate.mdt` (package)
7. Verifies the SHA-256 of both files read back from the drive (cache dropped) and stops with an error if they don't match
8. Unmounts, even when the mount was the desktop's

Expected output:
```
=== Vai APAGAR o conteúdo deste pendrive ===
  Device:   /dev/sda (Cruzer Fit 29,3G)
  Rótulo:   HONDA_OTA
  Montado:  /run/media/<user>/HONDA_OTA
  Conteúdo: 0040 install-0040.log SwUpdate2.txt.done ...
Apagar e gravar o pacote INSTALL? (yes/no): yes
...
=== Conferindo a cópia (SHA-256 lido do pendrive, sem cache) ===
OK   SwUpdate2.txt  <sha256>
OK   0040/SwUpdate.mdt  <sha256>

=== PRONTO ===
Pendrive em /dev/sda carregado com pacote INSTALL de <build directory>.
Já está desmontado: pode puxar.
```

### 1.3 Pull the flash drive from the laptop

No manual unmount needed — the script already did it. Pull it out.

---

## Part 2 — In the car

### 2.1 Flash drive on the front USB-A port

The front port sits near the steering wheel/center console (not the secondary center console one). On BR Civics it's usually next to the engine start/stop button or behind the gearshift.

**DO NOT use the USB-C port** — that one is for phone charging only, the daupdater doesn't scan it.

### 2.2 Car in ACC or ON

Key in ACC (no engine) or ON (key fully turned, engine off). The engine **does not need to be running**.

Head unit on and normal: can be on the main screen, in CarPlay, on the radio, whatever. Doesn't matter.

### 2.3 Cold boot combo: AUDIO 5s

**Hold the AUDIO button for 5 seconds** without letting go. After ~5s, a dialog appears:

```
┌─────────────────────────────┐
│                              │
│  Reboot the system?          │
│                              │
│       [ Cancel ]  [ OK ]     │
│                              │
└─────────────────────────────┘
```

**Confirm OK.**

If the dialog **doesn't appear** after 5s of holding AUDIO:
- The button might not be pressed hard enough (hold firmly on the center)
- The system might be in deep suspend — open the door first to "wake" it
- Your firmware might have a different combo — [`06-troubleshooting.md`](06-troubleshooting.md)

### 2.4 Head unit reboots (real shutdown + cold boot)

The screen goes black for 1-2 seconds. Then:

1. **Honda logo** appears
2. **Progress bar appears** (above the logo, small, can be fast)
3. May show the "Software Update" or "Copying..." screen — that's SystemUpdate.apk receiving the package
4. **Head unit reboots again** on its own (second time)
5. Recovery progress bar may appear (usually blue)
6. **Third reboot** — returns to normal mode
7. Warning screen appears as usual (on this first time, you need to tap OK manually once)

**Total time:** 3-10 minutes. Depends on the package size. INSTALL packages are small (~870 KB) and apply in ~2-3 min.

### 2.5 When the head unit comes back to the normal screen

**Pull the flash drive out.** Simple.

### 2.6 Tap OK manually once

**IMPORTANT:** on this first post-install run, the APK **hasn't started yet** (no `BOOT_COMPLETED` fired — the OTA happened during the boot itself). Tap OK manually on this first warning appearance.

**On the next boot** (when you turn the car off and on), the APK will already be active and will dismiss the warning automatically.

---

## Part 3 — Testing

### 3.1 Turn the car off and on

- Key OFF (full power down)
- Wait 5 seconds
- Key ACC or ON

Head unit comes up.

### 3.2 Watch for the warning

- Warning shows up as usual (nothing except Xposed can stop it from appearing)
- **Wait ~5-10 seconds**
- Warning should disappear on its own

If it does: **🎉 it worked. Project complete.**

### 3.3 Repeat 2-3 times

- Off, on. Should intercept.
- Off, on. Should intercept.
- At least 3 cycles with no failure for confidence.

---

## Reading the logs (optional, useful for confirmation)

After the deploy, you can read the OTA process log left on the flash drive:

```bash
cat /run/media/<user>/HONDA_OTA/result.log
# Expected: 2026/10/17 11:19:29 : OK

cat /run/media/<user>/HONDA_OTA/install-0040.log
# Expected: everything with exit=0, APK and su confirmed under /system
```

**To read our APK's log** (after the first post-install boot), you need root via adb — if you have that path active:

```bash
adb shell su -c "cat /data/data/com.khalleb.civichmi.autook/files/autook.log"
```

The log shows:
```
2026-10-17 11:23:11 === session start versionCode=3 ===
2026-10-17 11:23:11 watcher started needle=...OpeningDivideActivity
2026-10-17 11:23:14 warning detected
2026-10-17 11:23:16 tap ok=true coords=3
2026-10-17 11:23:28 rearmed (watcher reused)
```

If you see that, the APK is running perfectly.

---

## Post-deploy checklist

- [ ] Flash drive `result.log` shows `OK`
- [ ] First post-install cycle: warning dismissed on its own in ~5s
- [ ] Second cycle: same
- [ ] Third cycle: same
- [ ] CarPlay/Bluetooth/audio/navigation work normally
- [ ] No crash/instability observed
- [ ] ROLLBACK package on the laptop, available at any time
- [ ] (Optional) Extra flash drive with ROLLBACK in the glove box

---

## Didn't work?

See [`06-troubleshooting.md`](06-troubleshooting.md) — decision tree for common scenarios:

- "Reboot?" dialog never appears
- OTA flow starts but aborts
- Progress bar hangs
- APK doesn't fire after boot
- Head unit in boot loop

**If bricked:** [`07-rollback.md`](07-rollback.md) — recovery procedure.

---

## Next step

Worked? Please report your firmware via [issue](../../.github/ISSUE_TEMPLATE/nova-safra.md) and help the community.

To understand what the APK is doing at runtime: [`../fase7-deploy-2026-10-16/04-apk-autook-detalhes.md`](../fase7-deploy-2026-10-16/04-apk-autook-detalhes.md) (Portuguese).

For a complete safety net (bootable raw dump): [`08-backups.md`](08-backups.md).
