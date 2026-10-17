# 03 — Finding your firmware

**If you do NOT have a Civic 2017 EXL BR with DA version `1.F187.16`**, read this doc before deploying. You need to adapt 2 things:

1. **`rom_type`** in `build.py` — the EvilValet key; if wrong, the OTA package isn't even recognized.
2. **OK button coordinates** in `AutoOkConfig.java` — if your screen layout differs, the tap can miss.

This doc has 2 paths:
- **Fast path (no risk):** adapt publicly known data about your firmware.
- **Full path:** run our diagnostic package to discover everything directly from your HU.

---

## Step 1 — What's your firmware?

To find the DA version of your head unit:

1. Car in ACC, HU on
2. Go to: **Settings → System → About this Device**
3. Look for **"Software"**, **"Version"**, **"DA Version"**, or **"Build ID"**
4. Expected format: `1.F<X><YYY>.<Z>` (e.g., `1.F187.16`, `1.F197.70`, `1.F1A5.15`)

Alternative — service menu:

1. With audio off, hold `DAY/NIGHT + AUDIO + MENU` for 2 seconds
2. Enters Mitsubishi service menu
3. Look for "Version Info" or similar

Write it down.

## Step 2 — Check compatibility matrix

See if your firmware was reported:

| DA Version | Market | Rom type | Status | Source |
|---|---|---|---|---|
| `1.F187.16` | BR | `0040` | ✅ Deployed successfully | This project, 2026-10-16 |
| `1.F1A5.15` | US | `1115` | ✅ EvilValet confirmed | ic1101 docs/updates.md |
| `1.F197.70` | EU | `2250` | ⚠️ Public update file, not deployed | ic1101 docs/updates.md |
| ...others | — | — | ❓ Not reported | — |

**If your firmware is in the table**: use the listed rom_type and coordinates (when available).

**If not**: follow Step 3.

After deploying, please [open an issue](../../.github/ISSUE_TEMPLATE/nova-safra.md) reporting your firmware to help the community.

## Step 3 — Discover your `rom_type` via diagnostic package

This is the important part: **we won't guess your rom_type.** We'll build an OTA package that, when applied, saves info from your HU to the pendrive. Zero brick risk (pure diagnostic mode, doesn't write anything to `/system`).

### 3.1 Build the diagnostic package

**ATTENTION**: this requires temporarily modifying the project's `build.py` to generate a wide range of rom_types + dump updater-script. Specific procedure in [`docs/fase7-deploy-2026-10-16/06-dumps-obtidos.md § Como re-dumpar`](../fase7-deploy-2026-10-16/06-dumps-obtidos.md#como-re-dumpar) (Portuguese).

Summary:

```python
# In tooling/ota-build/build.py, change:
ROM_TYPES = ["0040"]
# To:
ROM_TYPES = [f"{n:04d}" for n in range(0, 10000, 10)]  # 1000 values
```

Build:

```bash
rm -rf tooling/ota-build/output/*
python3 tooling/ota-build/build.py
```

May take several minutes (will generate ~1000 signed packages).

### 3.2 Load pendrive

```bash
sudo ./tooling/scripts/format-pendrive.sh /dev/sdX
sudo ./tooling/scripts/prepare-pendrive-install.sh /dev/sdX
```

### 3.3 Deploy in the car

1. Pendrive into front USB-A port.
2. **Force cold boot** of the HU — hold `AUDIO` for 5 seconds until "Reboot?" dialog appears. Confirm.
3. HU reboots. If any rom_type matches, the updater-script saves info to the pendrive. If none match, pendrive comes back "empty".

### 3.4 After deploy, extract logs

Before removing the pendrive from the car, save system logs:

1. With audio off: `DAY/NIGHT + AUDIO + MENU` for 2 seconds.
2. `Detail Information & Setting → Error History → Save`.
3. Wait for 100%. HU saves `logcat.txt`, `kmsgcat.txt`, exception dumps + PowerLog to pendrive.

Remove pendrive, plug into laptop.

### 3.5 Analyze the logs

Search for `daupdater` in logcat:

```bash
grep "daupdater" /path/to/pendrive/logcat*
```

Something like this will appear:

```
E daupdater: getNewDaVersion(228):Can't open /mnt/usbdrive1/0040/SwUpdate.mdt
```

**The number is your `rom_type`!**

Alternatively, if any rom_type in your range matches, a `MATCH-<rom>.txt` + `diag-<rom>-vendor-build.prop` file comes back on the pendrive. The last one contains `custom_rom.type=<value>` — exact value.

### 3.6 Update `build.py` with the correct value

```python
# tooling/ota-build/build.py
ROM_TYPES = ["<your_rom_type>"]  # e.g., ["0040", "1115", "2250"...]
```

Now the actual OTA package (APK installation) will use the correct value.

## Step 4 — Discover OK button coordinates

### 4.1 Your screen resolution

Via service menu: `DAY/NIGHT + AUDIO + MENU` 2s → `Detail Information & Setting → Unit Check → Display` (or similar).

Our firmware has **800×480**. If yours is different, button coords will be different.

### 4.2 Via DaLauncher dump

After discovering your rom_type (Step 3), use the full dump package (also in [`docs/fase7-deploy-2026-10-16/06-dumps-obtidos.md`](../fase7-deploy-2026-10-16/06-dumps-obtidos.md)) to extract `DaLauncher.apk` from your HU.

Decompile:

```bash
cd tooling/apks-decoded
apktool d -o DaLauncher tooling/apks-dumped/<your-rom>/vendor-app/DaLauncher.apk
```

Look for the Warning layout:

```bash
grep -l "disclaimer" DaLauncher/res/layout/*.xml
```

Should be `mm_02_01_02.xml` (ours) or similar. Open it and find the `btnOK`:

```xml
<... android:id="@id/btnOK"
     android:layout_width="354.0px"
     android:layout_height="44.0px"
     android:layout_x="223.0px"
     android:layout_y="328.0px">
```

Button center: `(x + width/2, y + height/2)`. Our case: `(223 + 354/2, 328 + 44/2) = (400, 350)`.

### 4.3 Update `AutoOkConfig.java`

```java
public static final int BUTTON_OK_X = <center_x>;
public static final int BUTTON_OK_Y = <center_y>;
```

Rebuild APK:

```bash
cd our-apk
./gradlew assembleRelease
# ...sign with apksigner
cp AutoOk.apk ../tooling/ota-build/overlay/system/app/AutoOk.apk
```

Rebuild OTA, deploy, test.

## Step 5 — Confirm Activity name

If your firmware has `com.mitsubishielectric.ada.app.dalauncher.OpeningDivideActivity` (same as ours), nothing changes.

If different:

```bash
grep -rln "DisclaimerFragment" DaLauncher/smali/ | grep -v DisclaimerFragment\$
```

The class instantiating `DisclaimerFragment` is the warning Activity.

Update `AutoOkConfig.AVISO_ACTIVITY_NAME` with format `pkg/.ClassName` (slash-dot):

```java
public static final String AVISO_ACTIVITY_NAME =
    "<package>/.<ClassName>";
```

---

## Checklist before deploying on your firmware

- [ ] DA version noted
- [ ] Rom type discovered (via diagnostic or matrix)
- [ ] `build.py` updated with your rom_type
- [ ] Screen resolution confirmed
- [ ] OK button coords extracted from your DaLauncher.apk
- [ ] `AutoOkConfig.java` updated
- [ ] APK rebuilt and signed
- [ ] Overlay updated with new APK
- [ ] OTA package built
- [ ] ROLLBACK package built (always!)
- [ ] Report your firmware in the matrix via issue 😊

---

**Questions?** Open an issue using the new firmware template. The community grows with reported data.
