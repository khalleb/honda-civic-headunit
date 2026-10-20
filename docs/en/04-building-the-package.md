# 04 — Building the package

Step-by-step from the repo code to a `SwUpdate.mdt` ready to copy onto the flash drive.

**Prerequisite:** [`02-prerequisites.md`](02-prerequisites.md) fully checked.

**Time:** ~2-5 minutes on the first build (Gradle dependency download). ~30 seconds on subsequent builds.

---

## Overview — 3 artifacts

The "build" produces 3 distinct things:

| Artifact | Command | Output |
|---|---|---|
| **1. APK** (`AutoOk.apk`) | `./gradlew assembleRelease` + `apksigner` | `our-apk/app/build/outputs/apk/release/AutoOk.apk` |
| **2. OTA package INSTALL** | `python3 tooling/ota-build/build.py` | `tooling/ota-build/output/<timestamp>/0040/SwUpdate.mdt` |
| **3. OTA package ROLLBACK** | `python3 tooling/ota-build/build-rollback.py` | `tooling/ota-build/output-rollback/<timestamp>/0040/SwUpdate.mdt` |

The OTA packages reference the APK — so the flow is **APK first, OTA after**.

---

## Step 1 — Build the APK

```bash
cd our-apk
./gradlew clean assembleRelease
```

**What happens:**
1. Gradle resolves dependencies (first time: downloads ~500 MB of Android SDK stuff)
2. Compiles Java with javac
3. Converts Java bytecode → Dalvik DEX with D8
4. Bundles everything into an unsigned APK

**Expected output:**
```
BUILD SUCCESSFUL in 10s
39 actionable tasks: 38 executed, 1 up-to-date
```

APK produced at:
```
our-apk/app/build/outputs/apk/release/app-release-unsigned.apk
```

### Build troubleshooting

**Error: "D8: NullPointerException" with anonymous inner classes:**
D8 bug in older versions (4.0.52). Our code **does not use** anonymous inner classes for exactly that reason — it uses named inner classes. If you're modifying the code, keep explicit names (`class AvisoCallback implements OnDetected { ... }` instead of `new OnDetected() { ... }`).

**Error: "Unsupported Java version":**
Make sure you're using JDK 17:
```bash
java -version
# If not, force it:
JAVA_HOME=/usr/lib/jvm/java-17-openjdk ./gradlew clean assembleRelease
```

**Error: "SDK location not found":**
Create `our-apk/local.properties`:
```properties
sdk.dir=/home/<your-user>/sdks/Android
```

---

## Step 2 — Sign the APK

```bash
cd /path/to/honda-civic-headunit  # back to root
APKSIGNER=$ANDROID_SDK_ROOT/build-tools/33.0.2/apksigner

$APKSIGNER sign \
  --ks ~/.android/debug.keystore \
  --ks-pass pass:android \
  --out our-apk/app/build/outputs/apk/release/AutoOk.apk \
  our-apk/app/build/outputs/apk/release/app-release-unsigned.apk
```

**Verify the signature:**
```bash
$APKSIGNER verify --print-certs \
  our-apk/app/build/outputs/apk/release/AutoOk.apk
```

Should show the "Android Debug" certificate and `Verifies` at the end.

---

## Step 3 — Copy to the OTA package overlay

```bash
cp our-apk/app/build/outputs/apk/release/AutoOk.apk \
   tooling/ota-build/overlay/system/app/AutoOk.apk
```

The `tooling/ota-build/overlay/` is the "virtual tree" that `build.py` stuffs inside the OTA package. Whatever lives here lands in `/system/` on the head unit.

**Check the SHA-256 to make sure the copy succeeded:**
```bash
sha256sum our-apk/app/build/outputs/apk/release/AutoOk.apk \
          tooling/ota-build/overlay/system/app/AutoOk.apk
# Both hashes must match
```

---

## Step 4 — Build the OTA INSTALL package

```bash
python3 tooling/ota-build/build.py
```

**What happens:**
1. Imports `main` from `ic1101/ota-builder/src/main.py`
2. Monkey-patches `stage_tree` to include our overlay + embedded busybox
3. Generates an edify `updater-script` with our commands (mount, package_extract_file, set_perm)
4. Calls `build_mdt` that bundles everything into a zip + signs with the AOSP testkey
5. Drops the final `.mdt` at `output/<timestamp>/0040/SwUpdate.mdt`

**Expected output:**
```
INFO: deploy: /system/app/AutoOk.apk owner=0:0 mode=0644
INFO: rom_type=0040 -> /path/to/output/20261017T131606Z/0040/SwUpdate.mdt
OK: /path/to/output/20261017T131606Z
```

### OTA build troubleshooting

**Error: "no such file: tooling/ota-build/bin/busybox":**
Forgot to extract busybox from HondaHack.apk. See [`02-prerequisites.md § Binaries`](02-prerequisites.md).

**Error: "ImportError: cannot import name 'main' from 'main'":**
`tooling/references/ic1101/` wasn't cloned. Run `./MIGRATION/setup.sh`.

**Package generated but empty (~1KB) instead of ~870KB:**
The overlay isn't being included. Check that the APK is at `tooling/ota-build/overlay/system/app/AutoOk.apk`.

---

## Step 5 — Build the OTA ROLLBACK package (ALWAYS!)

**Golden rule:** never deploy INSTALL without having ROLLBACK ready.

```bash
python3 tooling/ota-build/build-rollback.py
```

**What this package does on the head unit:**
- `rm /system/app/AutoOk.apk`
- `rm /system/xbin/su`
- Verifies both are gone
- Writes a log to the flash drive

Returns the head unit to the exact state before INSTALL.

**Expected output:**
```
INFO: rollback mdt: /path/to/output-rollback/<timestamp>/0040/SwUpdate.mdt
```

---

## Step 6 — (Optional) Raw dump / deep scan builds

Two extra OTA packages that can be useful:

### Bootable raw dump (full brick recovery)

```bash
python3 tooling/ota-build/build-dump-raw.py
```

This package **dumps the APP + CAP + MITSU partitions** whole to the flash drive as `.img.gz` files. Takes ~18 minutes in the car. Result: bootable images you can use to restore via reverse `dd` if the firmware ends up inoperable.

See [`08-backups.md`](08-backups.md).

### Deep scan (complete textual map)

```bash
python3 tooling/ota-build/build-deep-scan.py
```

This package does a textual "scan" of all partitions + build.prop + packages.xml + /proc/* and bundles it in `scan.tar.gz`. Useful to sync [`../MAPA.md`](../MAPA.md) with the real state of the head unit.

After deploying:
```bash
python3 tooling/scripts/gen-mapa.py
```

Produces `~/backup-honda-civic-g10/deep-scan-YYYY-MM-DD/RELATORIO.md`.

---

## Verify the package is ready

```bash
ls -la tooling/ota-build/output/<timestamp>/0040/
# -rw-r--r--. 1 khalleb khalleb 872053 ... SwUpdate.mdt
```

Expected size: **~870 KB** (varies with APK). If much smaller (<10 KB) or much larger (>5 MB), something went wrong.

**Verify the OTA package signature (optional):**
```bash
unzip -l tooling/ota-build/output/<timestamp>/0040/SwUpdate.mdt
# Should list META-INF/MANIFEST.MF, CERT.SF, CERT.RSA + system/ + busybox
```

---

## "All-in-one" script (future)

To automate steps 1-5, we could add a `tooling/scripts/full-build.sh`. Doesn't exist yet — see [`PENDENCIAS.md`](../../PENDENCIAS.md). For now, paste the commands manually:

```bash
#!/bin/bash
set -e
cd our-apk && ./gradlew clean assembleRelease && cd ..
$ANDROID_SDK_ROOT/build-tools/33.0.2/apksigner sign \
  --ks ~/.android/debug.keystore --ks-pass pass:android \
  --out our-apk/app/build/outputs/apk/release/AutoOk.apk \
  our-apk/app/build/outputs/apk/release/app-release-unsigned.apk
cp our-apk/app/build/outputs/apk/release/AutoOk.apk \
   tooling/ota-build/overlay/system/app/AutoOk.apk
python3 tooling/ota-build/build.py
python3 tooling/ota-build/build-rollback.py
echo "✓ INSTALL + ROLLBACK ready."
ls -la tooling/ota-build/output/*/0040/SwUpdate.mdt
ls -la tooling/ota-build/output-rollback/*/0040/SwUpdate.mdt
```

---

## Next step

Package ready? → [`05-deploying-in-car.md`](05-deploying-in-car.md) to prepare the flash drive and deploy.
