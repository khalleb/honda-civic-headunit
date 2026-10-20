# 06 — Troubleshooting

Decision tree for when something doesn't work.

**Before trying anything here:**
- Confirm you have the **ROLLBACK package ready** on the laptop. See [`07-rollback.md`](07-rollback.md).
- Back up `~/.android/debug.keystore` to a separate location.

---

## 🧭 Decision tree

```
Problem → where is it?

├─ Build (PC)
│   ├─ gradlew assembleRelease fails ............. § APK build fails
│   ├─ apksigner fails .......................... § Signing fails
│   └─ build.py fails ........................... § OTA build fails
│
├─ Flash drive
│   ├─ prepare-pendrive-install.sh fails ........ § Flash drive not detected
│   └─ Flash drive copied but car doesn't read .. § Car won't read the drive
│
├─ Car (during OTA deploy)
│   ├─ AUDIO 5s doesn't open dialog ............. § Cold boot combo doesn't work
│   ├─ Dialog shows but then nothing happens .... § Package doesn't apply
│   ├─ Progress bar hangs ........................ § OTA hangs mid-way
│   └─ Boot loop after OTA ...................... § Boot loop (CRITICAL)
│
└─ Car (after deploy)
    ├─ Warning still appears without dismiss .... § APK doesn't fire
    ├─ Warning dismisses but screen is stuck .... § Wrong tap
    ├─ APK only works on 1st boot ............... § Service dies between boots
    └─ CarPlay/Bluetooth stop working ........... § Modification damaged something
```

---

## § APK build fails

### Error: "D8: NullPointerException"
D8 (dexer) bug with anonymous inner classes. Convert to **named** inner classes.

Example that fails:
```java
new Runnable() {
    @Override public void run() { ... }
}
```

Example that works:
```java
static class MyRunnable implements Runnable {
    @Override public void run() { ... }
}
new MyRunnable();
```

### Error: "Unsupported Java version" or "class file version"
Wrong JDK. Needs to be **17**.
```bash
java -version   # must show 17.X
JAVA_HOME=/usr/lib/jvm/java-17-openjdk ./gradlew clean assembleRelease
```

### Error: "SDK location not found"
Create `our-apk/local.properties`:
```properties
sdk.dir=/home/<your-user>/sdks/Android
```

### Error: "Could not resolve dependencies"
Gradle's first build needs internet to download dependencies. Confirm you have a connection.

---

## § Signing fails

### Error: "keystore was tampered with, or password was incorrect"
Wrong keystore. Default is `~/.android/debug.keystore` with password `android`:
```bash
ls ~/.android/debug.keystore
$APKSIGNER sign --ks ~/.android/debug.keystore --ks-pass pass:android \
  --out AutoOk.apk app-release-unsigned.apk
```

If the keystore is lost, regenerate it:
```bash
keytool -genkey -v -keystore ~/.android/debug.keystore \
  -alias androiddebugkey -keyalg RSA -keysize 2048 \
  -validity 10000 -dname "CN=Android Debug,O=Android,C=US" \
  -storepass android -keypass android
```

**WARNING:** new keystore = new signature = Android refuses to upgrade the APK already on the head unit. You need to ROLLBACK before installing an APK signed with a new key.

---

## § OTA build fails

### Error: "ImportError: cannot import name 'main' from 'main'"
`tooling/references/ic1101/` doesn't exist. Clone it:
```bash
git clone https://github.com/librick/ic1101.git tooling/references/ic1101
```

### Error: "FileNotFoundError: tooling/ota-build/bin/busybox"
Extract busybox from the HondaHack APK:
```bash
unzip -o tooling/references/root-honda/packages/HondaHack.apk -d /tmp/hondahack
cp /tmp/hondahack/res/raw/busybox tooling/ota-build/bin/busybox
```

### Error: "FileNotFoundError: tooling/ota-build/bin/su"
```bash
cp tooling/references/root-honda/su tooling/ota-build/bin/su
```

### Package generated but empty (< 10 KB)
The overlay wasn't included. Confirm the APK exists:
```bash
ls -la tooling/ota-build/overlay/system/app/AutoOk.apk
```

If not, copy:
```bash
cp our-apk/app/build/outputs/apk/release/AutoOk.apk \
   tooling/ota-build/overlay/system/app/AutoOk.apk
```

---

## § Flash drive not detected

### `lsblk` doesn't show the drive
- Plug into a different USB port
- Try on another machine (confirms the drive works)
- `dmesg | tail -20` after plugging — look for messages like `[sdb] Attached SCSI`

### `prepare-pendrive-install.sh` says "not USB"
The script checks `lsblk -no TRAN` to confirm it's USB. If your drive shows up as `TRAN=sata` or empty, use another drive.

### Script runs but drive comes back empty
The script may have run on the wrong device! Confirm:
```bash
sudo mount /dev/sda1 /mnt/temp
ls -la /mnt/temp
sudo umount /mnt/temp
```

Should contain `SwUpdate2.txt` and the `0040/` folder.

---

## § Car won't read the drive

### No progress bar after AUDIO 5s + confirm
Possible causes:
1. **Flash drive on the wrong port**: USE THE FRONT USB-A PORT (near the steering wheel), not USB-C, not the secondary console one
2. **Wrong FAT32 format**: must be MSDOS FAT32, not exFAT, not NTFS
3. **Drive too large** (>128 GB) — some automotive BIOSes reject it. Use 8-32 GB
4. **Wrong rom_type**: the folder on the drive must be named exactly `0040` (or your firmware's rom_type). Check with `ls /run/media/<user>/HONDA_OTA/`
5. **SwUpdate2.txt missing**: trigger file. Must be 28 bytes with `Ver:1\n`

### Bar shows briefly and disappears
Normal — may be `SystemUpdate.apk` detecting but rejecting (wrong signature or rom_type). Go to `Error History` to read the log:
- Audio off: `DAY/NIGHT + AUDIO + MENU` 2s → service menu
- `Detail Information & Setting → Error History → Save`
- Pull the drive, read `logcat.txt`:
```bash
grep "daupdater\|SystemUpdate" /run/media/<user>/HONDA_OTA/logcat.txt
```

---

## § Cold boot combo doesn't work

### AUDIO 5s doesn't open dialog
Tests:
1. **Button not pressed well**: hold firmly on the center of the AUDIO button, not the edge
2. **Head unit too "cold"**: open the door to turn on the dome light + head unit (wakes it from deep suspend), try again
3. **Different combo for your firmware**: very old firmware may need `AUDIO + HOME` or `HOME 5s`. Try combinations
4. **Pull the radio fuse for 15-20 min**: forces full head unit shutdown. Replug the fuse, start the car → combo should work

### "Reboot?" shows but confirm does nothing
Tap exactly on the OK button (not "Cancel"). Confirm visually that you hit the right one. If it persists, see [`07-rollback.md § Emergency rollback`](07-rollback.md#rollback-de-emergência).

---

## § Package doesn't apply

### OTA flow starts but aborts
Logs on the drive after deploy show the reason. Look for:

```bash
cat /run/media/<user>/HONDA_OTA/result.log
# Expected: "2026/XX/XX : OK"
# If it shows "FAIL" or wrong:
cat /run/media/<user>/HONDA_OTA/install-0040.log  # (or any *.log)
```

Common causes:
- `signature verification failed`: package not signed with the AOSP testkey. Check `build.py`.
- `no partition APP`: edify failed to mount. May indicate your firmware's recovery is different.
- `set_perm failed`: embedded busybox missing. Confirm it's in the overlay.

### Package accepted but APK doesn't appear in `/system/`
`install-0040.log` should show `post-install-check` with `AutoOk.apk` listed. If not, `package_extract_file` failed — rebuild and try again.

---

## § OTA hangs mid-way

### Progress bar stuck at 29% for minutes
Normal! The 29% phase is usually `SystemUpdate.apk` copying the package from `/mnt/usbdrive1` to `/data/system-update/`. Can take up to 5-10 min depending on size (large raw-dump packages take longer).

**Wait at least 15 minutes before concluding it hung.**

If it really hung:
1. **DO NOT turn off the car any way you can.** Let it process.
2. If you must interrupt: pull the radio fuse for 15 min.
3. Never interrupt during a /system write — can brick.

---

## § Boot loop (CRITICAL)

**Scenario:** head unit reboots infinitely after OTA deploy.

### 1. Stay calm
A boot loop without normal bootloader access **still has a recovery path**: the recovery is still reachable via combo + flash drive.

### 2. Deploy ROLLBACK URGENTLY

```bash
# On the PC
sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sda
```

### 3. In the car
1. Flash drive on the front port
2. **AUDIO 5s + confirm** (the head unit will be in some abnormal state, but the combo should still work — it's interpreted by the bootloader, not Android)
3. Recovery picks up the rollback automatically
4. ~2-3 min: rollback applies
5. Head unit comes back normal

### 4. If AUDIO 5s doesn't even respond (head unit in recovery loop)
- **Pull the radio fuse** for 15-20 min in the internal fuse box
- Replug the fuse, start the car, try combo + rollback
- Still doesn't work: **disconnect the battery** (negative) for 30 min
- Nuclear option: **replace the head unit** (R$ 1,000-2,000 at the dealer)

---

## § APK doesn't fire (warning still needs manual tap)

**Scenario:** OTA applied successfully, but the warning still needs a human touch.

### 1. Check whether the APK is installed
Via adb (if you have that path):
```bash
adb shell "ls -la /system/app/AutoOk.apk /system/xbin/su"
```

Expected:
```
-rw-r--r-- 1 root root 16890 ... AutoOk.apk
-rwsr-sr-x 1 root root 133472 ... su
```

If missing: deploy didn't apply. Retry.

### 2. Check whether the Service is active
```bash
adb shell "ps | grep khalleb.civichmi"
```

Must show process `com.khalleb.civichmi.autook`.

### 3. Check the APK logs
```bash
adb shell "su -c 'cat /data/data/com.khalleb.civichmi.autook/files/autook.log'"
```

Must show lines like `warning detected` and `tap ok=true`.

If the log exists but has no `warning detected`:
- **Wrong logcat needle**: your firmware may have a different name for `OpeningDivideActivity`. Check with:
  ```bash
  adb shell "su -c 'logcat -v brief ActivityManager:I *:S'" | grep -i disclaimer
  ```
  Grab the real name, update `AVISO_ACTIVITY_NAME` in `AutoOkConfig.java`.

If the log shows `warning detected` but `tap ok=false`:
- `su` isn't working. Test `adb shell su -c id` — must show `uid=0(root)`.

If the log shows `tap ok=true` but the warning stays:
- **Wrong coord**: the tap hits a pixel that isn't the OK button. See [`03-finding-your-firmware.md § 4`](03-finding-your-firmware.md) to adjust.

### 4. Check permissions
```bash
adb shell "pm list packages | grep khalleb"
# Must return: package:com.khalleb.civichmi.autook
```

If it doesn't list: the APK is in `/system/app/` but wasn't installed as a package. Could be the signature. Verify.

---

## § Wrong tap (warning dismisses but something freezes)

**Scenario:** the warning disappears, but after the tap another odd screen shows or the launcher doesn't load right.

That means the tap hit a point outside the OK button. Possible causes:
- Your screen resolution ≠ 800×480. Check in the service menu.
- Warning layout slightly different on your firmware.

Fix: adjust `BUTTON_OK_X` and `BUTTON_OK_Y` in `AutoOkConfig.java`.

To find the right coords: [`03-finding-your-firmware.md § 4`](03-finding-your-firmware.md).

---

## § Service dies between boots

Shouldn't happen on APK v0.3.0+ (Service is `START_STICKY`, Watchdog recreates on death, LogcatWatcher reused between taps).

If it happens:
1. Check installed version: `autook.log` must show `versionCode=3` or higher
2. If v0.1 or v0.2, update to v0.3.0+ (has the `stopSelf()` and EPERM fixes)

---

## § CarPlay/Bluetooth stop working

**This should NOT happen.** Our modification is surgical:
- Zero preexisting files modified
- Zero changes under `/system/vendor/`
- Zero changes to base Android services

If something stops working after deploy, suspect:
1. **OTA applied badly**: the APK may have conflicted with the Mitsubishi whitelist. Deploy ROLLBACK and test again.
2. **Coincidence**: could be a separate problem (flaky CarPlay, phone Bluetooth, etc.). Test with another phone, another cable.
3. **Rollback + re-test**: if services come back after rollback, our mod is the cause — open an issue.

---

## Collect diagnostic info to open an issue

If nothing here resolved it, open an issue on [GitHub](https://github.com/khalleb/honda-civic-headunit/issues) with:

1. **Firmware**: DA version + market (`1.F187.16 BR`, `1.F1A5.15 US`, etc.)
2. **Deploy logs**: `result.log` + `install-*.log` from the drive
3. **Head unit logcat** (if you can):
   ```bash
   adb shell "su -c 'logcat -d -v brief'" > logcat-full.txt
   ```
4. **APK log**:
   ```bash
   adb shell "su -c 'cat /data/data/com.khalleb.civichmi.autook/files/autook.log'" > autook.log
   ```
5. **Observed behavior**: before vs after deploy, which cycle it started on, intermittent or always.

---

## Safety net: emergency package in the glove box

Leave an extra flash drive, formatted FAT32 MSDOS, with the ROLLBACK package loaded, in the car's glove box. In an emergency (e.g. car froze on a trip), you plug in + AUDIO 5s + confirm, and everything is back to normal in 5 min.

A flash drive costs R$ 20. Permanent peace of mind.
