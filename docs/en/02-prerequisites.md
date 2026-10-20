# 02 — Prerequisites

Everything you need before running the deploy.

**Total setup time:** ~30 minutes on the laptop (one time). After that, build + deploy runs in ~20 minutes each time.

---

## Hardware

| Item | Spec | Required |
|---|---|---|
| **Honda Civic G10** | 2017 EXL BR with DA version `1.F187.16` (confirmed) or adjacent firmware you'll adapt | Yes |
| **Laptop/PC** | Linux (Fedora, Ubuntu, Debian, Arch — any distro with modern `glibc`) | Yes |
| **USB-A flash drive** | ≥ 100 MB free for the INSTALL package. ≥ 2 GB if you plan to do a bootable raw dump | Yes |
| **Extra USB-A flash drive** | Optional — loaded with ROLLBACK package, kept in the glove box as insurance | Recommended |
| **Physical access to the car** | To insert the flash drive, hold AUDIO for 5s, watch the progress bar | Yes |

**Notes on the flash drive:**
- Must be **USB-A** (not USB-C) — the Civic's front port is Type A.
- FAT32 MSDOS format (our script formats it if needed).
- No multiple partitions — a single primary FAT32.
- Very large drives (>128GB) can have recognition issues on some automotive BIOSes. Prefer 8-32 GB.

---

## Software

### System dependencies

**Fedora:**
```bash
sudo dnf install -y java-17-openjdk-devel android-tools git curl unzip \
                    parted dosfstools python3 zip imagemagick
```

**Ubuntu / Debian:**
```bash
sudo apt install -y openjdk-17-jdk android-tools-adb git curl unzip \
                    parted dosfstools python3 zip imagemagick
```

**Arch:**
```bash
sudo pacman -S jdk17-openjdk android-tools git curl unzip parted dosfstools \
               python zip imagemagick
```

### Android SDK (for `apksigner`)

```bash
# Download command-line tools
mkdir -p ~/sdks/Android/cmdline-tools
cd ~/sdks/Android/cmdline-tools
curl -L -o cmdtools.zip \
  https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip cmdtools.zip && rm cmdtools.zip && mv cmdline-tools latest

# Export paths
export ANDROID_SDK_ROOT=~/sdks/Android
export PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin

# Accept licenses
yes | sdkmanager --licenses

# Install build-tools 33 (apksigner v2+ required)
sdkmanager "build-tools;33.0.2"
```

To persist, add to your shell rc:
```bash
echo 'export ANDROID_SDK_ROOT=~/sdks/Android' >> ~/.bashrc
echo 'export PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin' >> ~/.bashrc
```

### JDK 17 (not 21+, not 11-)

**Important:** AGP 7.4.2 (our `build.gradle`) **does not support JDK 21+**. It has to be JDK 17 Temurin or OpenJDK.

Verify:
```bash
java -version
# Expected: openjdk version "17.0.X" or "17.X.X"
```

If your system has a newer JDK as default, install 17 side by side and use it explicitly:

```bash
# Fedora
sudo dnf install java-17-openjdk-devel

# Run the build with specific JDK 17:
JAVA_HOME=/usr/lib/jvm/java-17-openjdk ./gradlew assembleRelease
```

### Python 3.9+

Our `build.py` uses `datetime.UTC` (Python 3.11+ native). Python 3.9/3.10 works with a minor adjustment. Tested on 3.13 and 3.14.

### Android debug keystore

Android automatically generates `~/.android/debug.keystore` when you run `gradle` or other Android tools for the first time. Check if it exists:

```bash
ls ~/.android/debug.keystore
```

If it doesn't, force any build to generate it OR manually:
```bash
mkdir -p ~/.android
keytool -genkey -v -keystore ~/.android/debug.keystore \
  -alias androiddebugkey -keyalg RSA -keysize 2048 \
  -validity 10000 \
  -dname "CN=Android Debug,O=Android,C=US" \
  -storepass android -keypass android
```

**IMPORTANT:** if you modify the APK later (version v0.3 → v0.4), **you must sign with the SAME keystore** — Android refuses APK upgrades with a different signature. Back it up right away:

```bash
mkdir -p ~/backup-honda-civic-g10
cp ~/.android/debug.keystore ~/backup-honda-civic-g10/debug.keystore.bak
```

---

## Reference projects (clone into `tooling/references/`)

Projects we use as a base. None redistributed — you clone them yourself:

```bash
cd /path/to/honda-civic-headunit
mkdir -p tooling/references

# ic1101 — ota-builder (our build.py wraps this)
git clone https://github.com/librick/ic1101.git tooling/references/ic1101

# root-honda — setuid su + Mitsubishi whitelist
git clone https://github.com/codeage/root-honda.git tooling/references/root-honda
```

Alternatively, our `MIGRATION/setup.sh` does this automatically:
```bash
./MIGRATION/setup.sh
```

---

## Binaries (busybox + su + sleep)

They come from the third-party projects cloned above. Helper script copies them to the right places:

```bash
mkdir -p tooling/ota-build/bin

# Static ARM busybox (from the HondaHack APK bundled with root-honda)
unzip -o tooling/references/root-honda/packages/HondaHack.apk -d /tmp/hondahack
cp /tmp/hondahack/res/raw/busybox tooling/ota-build/bin/busybox

# Setuid su (straight from root-honda)
cp tooling/references/root-honda/su tooling/ota-build/bin/su

# sleep (compiled by ic1101 — ships ready)
# Already available at ic1101/ota-builder/input/sleep/output/sleep
```

---

## Verify everything is ready

Helper script that checks installation:

```bash
./tooling/scripts/verificar-backups.sh
```

Plus a quick manual check:

```bash
# JDK 17
java -version 2>&1 | grep "17\."

# Python
python3 --version

# apksigner
$ANDROID_SDK_ROOT/build-tools/33.0.2/apksigner --version

# Project's gradlew
cd our-apk && ./gradlew --version

# Binaries
ls -la tooling/ota-build/bin/{busybox,su}

# References
ls tooling/references/ic1101 tooling/references/root-honda
```

All green = ready to build.

---

## What you do NOT need

- ❌ Unlocked bootloader
- ❌ Working ADB on the head unit (our attack bypasses it entirely)
- ❌ Honda signature or approval
- ❌ Paid Honda Hack (USD 25) — this project replaces it
- ❌ JTAG / serial cable / special hardware
- ❌ Someone else's car to test on — you learn on your own

---

## Final checklist before the build

- [ ] JDK 17 installed and `java -version` shows `17.X`
- [ ] Android SDK + build-tools 33.0.2 installed
- [ ] Python 3.11+ (or 3.9+ with the `build.py` adjustment)
- [ ] `~/.android/debug.keystore` exists and has an external backup
- [ ] Project cloned at `honda-civic-headunit/`
- [ ] `tooling/references/ic1101/` and `tooling/references/root-honda/` exist
- [ ] `tooling/ota-build/bin/busybox` and `tooling/ota-build/bin/su` exist
- [ ] USB-A flash drive available

All checked? → [`04-building-the-package.md`](04-building-the-package.md).
