# GitHub landscape — Honda ecosystem and lessons for the project (2026-10-27)

Broad GitHub landscape scan, starting from the "Honda Hack" search and refined by several angles (Mitsubishi platform, car family, derivatives of our stack, telemetry/HU projects, automotive RE lists). The goal is to **catalog what others have already discovered** about our HU — or about neighboring parts of the same vehicle — pull what helps our project, and leave on record what **does not** fit our scope. Based on metadata, READMEs, legitimate code and the public issues of `librick/ic1101`.

> **Critical finding of this landscape, resolved in another repo:** the `su` we already installed in the car is **KingoSU**, not SuperSU. The `joshfng/root-honda` audit identified this and published the swap for Chainfire's official `su`. We **still have KingoSU in the local binary** (SHA-256 matches exactly). See §4.

## 1. Overview (33 repositories inspected)

Grouped by category. Stars are from the landscape day; anything without a direct file link lacks relevant content beyond the metadata.

### 1.1 Same HU as ours (vcm30t30, Android 4.2.2, Mitsubishi ADA)

| Repo | ★ | Role | Relevance |
|---|---|---|---|
| [`librick/ic1101`](https://github.com/librick/ic1101) | **188** | EvilValet writeup + `ota-builder` + `apk-rebuilder` + `aidl-rebuilder`. Author: Eric McDonald. | **Technical base.** Already in `setup.sh`. Issues #6, #20, #29 in §5. |
| [`alexpotv/Clusters`](https://github.com/alexpotv/Clusters) | 1 | Open Android app that reads the vehicle via Binder/Intent and draws on the secondary cluster. | **Closes RE Layer 2 §3/§4** — see §3. |
| [`jersacct/2016PilotOneClick`](https://github.com/jersacct/2016PilotOneClick) | 58 | Honda Pilot 2016 rooter (DirtyCOW + `su` + whitelist). Already in `setup.sh`. | Source of the mechanism `codeage/root-honda` adapted. |
| [`codeage/root-honda`](https://github.com/codeage/root-honda) | 129 | Simplified fork of 2016PilotOneClick + SuperSU + Mitsubishi whitelist. Already in `setup.sh`. | **Where our `su` came from — and with the wrong `su`, see §4.** |
| [`joshfng/root-honda`](https://github.com/joshfng/root-honda) | 0 | **Audited fork of codeage/root-honda** (2026-10-13). | **Our main finding. Resolves KingoSU; see §4.** |
| `madhunm`, `ring2003`, `z3tab`, `eral2001`, `hackers365`, `CrackerCat`, `evi1r0s3` — all `ic1101` | 0-1 | Mirror forks; 0 own commits in all. | Confirms ic1101 has **no** active derivatives (nothing to watch). |
| [`cysin/honda_hacking_analysis`](https://github.com/cysin/honda_hacking_analysis) | 16 | RE analysis of commercial Chinese tools (HondaHack / AutoHack / VinciCar). | **Out of our scope.** The mere existence confirms the target's prevalence. See §7. |

### 1.2 Same car generation (Civic 2016/2017), ECU/CAN side

| Repo | ★ | Role | Relevance |
|---|---|---|---|
| [`commaai/opendbc`](https://github.com/commaai/opendbc) | 2k+ | DBC decoding. Contains **`honda_civic_touring_2016_can.dbc`** and **`honda_civic_hatchback_ex_2017_can.dbc`**. | **Canonical B-CAN/F-CAN table** for our vehicle. §6. |
| [`commaai/openpilot`](https://github.com/commaai/openpilot) | 64k | Open driver assistance. Honda is one of the most-covered platforms. | CAN read flows on top of opendbc — won't use at runtime, only as "oracle" during RE. |
| [`sunnypilot/sunnypilot`](https://github.com/sunnypilot/sunnypilot) | 2154 | openpilot fork with more Honda cars. | Same CAN source. |
| [`commaai/panda`](https://github.com/commaai/panda) | 1707 | CAN gateway firmware (OBD2 → USB). | Useful if one day we want to read CAN **without** the HU in the path (plan B for Phase 9). |
| [`alexgaoth/awesome-reverse-engineered`](https://github.com/alexgaoth/awesome-reverse-engineered) | — | Curated list; highlights `ic1101` in the Automotive section. | Confirms our base project's reputation. |

### 1.3 Other Honda families / neighboring platforms

| Repo | ★ | Role | For us |
|---|---|---|---|
| [`enricobattocchi/myhondaplus-homeassistant`](https://github.com/enricobattocchi/myhondaplus-homeassistant) | 18 | Home Assistant integration with Honda Connect Europe (My Honda+). | **Cloud** API, not local HU. Useful if we want to cross with remote commands. |
| [`enricobattocchi/myhondaplus-desktop`](https://github.com/enricobattocchi/myhondaplus-desktop) | 10 | Desktop GUI for the same API. | Idem. |
| [`daviddelahoz/ha-hondalink`](https://github.com/daviddelahoz/ha-hondalink), [`nickwilkie/ha-hondalink`](https://github.com/nickwilkie/ha-hondalink) | — | HondaLink (North America) integration with HA. | US equivalent of the above. |
| [`mitchellrj/kamereon-python`](https://github.com/mitchellrj/kamereon-python) | 24 | Kamereon platform from the Renault-Nissan-Mitsubishi alliance (connected cars). | **Mitsubishi corporate, not ADA.** Not our stack. |
| [`yuxiuwen64-maker/HondaHUDdiy`](https://github.com/yuxiuwen64-maker/HondaHUDdiy) | 0 | Custom HUD for **newer** Honda (Android 10 + Alpine, `com.alap.honda30ea.aochr.meterservice`). | **Not our firmware**, but the **PROTOCOL.md** is useful (see §3.5): bind pattern + 12 TX codes for `MeterService`. |
| [`flyandi/honda-fuel-tracker`](https://github.com/flyandi/honda-fuel-tracker) | 0 | React Native fuel tracker app. | Author is a reference (Mazda SDK); this repo in itself is just a React Native app, nothing special. |
| [`flyandi/mazda-custom-application-sdk`](https://github.com/flyandi/mazda-custom-application-sdk) | 213 | Mazda Connect SDK (neighboring platform). | **Architectural pattern** — micro-framework + simulator. Worth as inspiration if one day it becomes "AutoOk SDK" (future PENDENCIAS item). |
| [`mbhul/HondaLink_USB_Audio`](https://github.com/mbhul/HondaLink_USB_Audio), [`tahmidul612/hondalink-app-controller`](https://github.com/tahmidul612/hondalink-app-controller) | 0-1 | Spot workarounds, HondaLink uses. | Little relation to the HU. |

### 1.4 ECU/OBD/K-Line (separate ecosystem, same thematic repository)

| Repo | Role |
|---|---|
| [`VIRUXE/ghidra-oki66207`](https://github.com/VIRUXE/ghidra-oki66207) | **Ghidra processor module** for the OKI 66201/66207/66301 family — MCUs of Honda OBD1 ECUs pre-1996. Decompiles with XRefs and readable C. |
| [`aster94/Keyword-Protocol-2000`](https://github.com/aster94/Keyword-Protocol-2000) | KWP2000 (Honda HDS, Suzuki SDS, Kawasaki KDS). |
| [`andreibaw/Honda_K-Line_KWP2000`](https://github.com/andreibaw/Honda_K-Line_KWP2000), [`atoid/DashBle`](https://github.com/atoid/DashBle), [`kerpz/ArduinoHondaUNI`](https://github.com/kerpz/ArduinoHondaUNI), [`guilhermemecatronica/projectkline`](https://github.com/guilhermemecatronica/projectkline) | OBD/K-Line for motorcycles and old cars. |
| [`gecekusu1979/honda`](https://github.com/gecekusu1979/honda), [`bouletmarc/Converter`](https://github.com/bouletmarc/Converter), [`hondabase/files-archive`](https://github.com/hondabase/files-archive) | ECU tuning (eCtune, Hondata, cal/bin). |

**None** of these touches the HU — they're here only to record that the Honda-RE community has two well-separated streams (ECU/engine vs. infotainment).

### 1.5 Writeups, discussions and matrices

| Source | Relevance |
|---|---|
| [`kristate/krackinfo`](https://github.com/kristate/krackinfo) — `ANDROID_H.md` | "Manufacturer × model × device SoC" matrix. Honda × `vcm30t30` = `MY17ADA` (ours). Also lists `koelsch`/`e1853` for Pilot, Accord, Clarity, NSX, Ridgeline, Spirior. |
| [`ahastudio/til`](https://github.com/ahastudio/til) — `security/honda-civic-headunit-evil-valet.md` | Korean summary of the librick writeup and the HN thread. §8. |
| [HN thread 48523080](https://news.ycombinator.com/item?id=48523080) | 342 points / 76 comments. Supply chain security discussion. §8. |
| [`Buildstarted/linksfordevs`](https://github.com/Buildstarted/linksfordevs), [`bobkingdom/TrendRadar`](https://github.com/bobkingdom/TrendRadar), several `Tyaoo/picker`, `BruceFeIix/picker` | Aggregators that indexed the librick writeup in 2026-06. Reach signal. |

## 2. Public issues of `librick/ic1101` (community field)

I explored the 7 open/closed issues of ic1101 that still give signal. The three that matter for us:

### 2.1 Issue #6 — `IVideoManagerApService` (not on our radar)

User `hackers365` did RE on `HondaHack-7.0.1-release.apk` with JADX and posted **which services the commercial product binds**:

- `IAvApService`
- `IVehicleInfoManagerApService`
- `ICameraAPService`
- **`IVideoManagerApService`** ← new for us

Useful for us: `IVideoManagerApService` enters the list of services candidate for future deodex (if we write an app with video overlay, Clusters-on-cluster style).

### 2.2 Issue #20 — full USB mode chain (Device/Host)

Author documented `UI → JNI → sysfs`:

```
UsbCertActivity (secret menu)
   → UsbCertJni.changeDeviceMode(listener, 0|1)   [Java]
   → libusbcert_jni.so                            [JNI]
   → property_set("persist.sys.usb1_mode", "device"|"host")
   → usbdetectd                                   [prop watcher]
   → /sys/devices/platform/tegra-otg/enable_device
   → /sys/devices/platform/tegra-udc.0/.../soft_connect
```

Physical combo for the menu: **Brightness + Phone + Volume/Power** → "Detail Information and Settings" → hold **Phone**, then hold **Home** (three beeps, then one). Via shell (with root):

```sh
echo 0 > /sys/devices/platform/tegra-otg/enable_host
echo 1 > /sys/devices/platform/tegra-otg/enable_device
echo connect > /sys/devices/platform/tegra-udc.0/udc/tegra-udc.0/soft_connect
setprop sys.usb.config mtp,adb
setprop persist.sys.usb1_mode device   # persistent
```

**Impact for us:** with AutoOk + `su` already installed, you can enable ADB over USB from the script itself, no physical combo, for future investigations — great for post-Phase 10 deploy and for replacing spot diagnostic OTAs with ADB sessions.

### 2.3 Issue #29 — CR-V China OTA package

User `hybzhl` uploaded a Chinese CR-V `SwUpdate.mdt`, Android 4.2.2, same CPU, version `1.F198.60`. `librick` confirmed the format is "very similar" to Civic → "many tools probably work for CR-V too".

**For us:** compatible firmware goes beyond the US Civic G10 — **China CR-V** confirmed as the same family. Our "compatibility matrix" (`PENDENCIAS.md`) gains points: Civic BR `1.F187.16` (us), Civic US (librick), **CR-V China `1.F198.60`**. `kristate/krackinfo` also lists Pilot, Accord, Ridgeline, NSX, Spirior using `koelsch` (sibling SoC — not the same chip, but the same Mitsubishi ADA stack).

## 3. `alexpotv/Clusters` — RE Layer 2 gold mine

Open Android app made for the Civic G10's cluster (same firmware, same HU). Installs via ADB after the HU is in USB Device mode. Confirms, with live code, **everything** we inferred in our RE Layer 2 §3 (`VehicleInfoManager`) — and goes further.

### 3.1 How Clusters accesses the vehicle

`VehicleDataSource.java` does `bindService` on three Mitsubishi services, with `Intent.setComponent(new ComponentName(pkg, cls))`:

| Service | Package | Class |
|---|---|---|
| VehicleInfoManager | `com.mitsubishielectric.ada.appservice.vehicleinfomanager` | `.VehicleInfoManagerApService` |
| AvApService | `com.mitsubishielectric.ada.appservice.avapservice` | `.AvApService` |
| DiagService | `com.mitsubishielectric.ada.appservice.diag` | `.DiagService` |

Then it calls the raw Binder with `transact(txCode, data, reply, 0)` + `writeInterfaceToken(descriptor)` — exactly as any privileged app talking to a Mitsubishi service would. No reflection breaking `android.jar`; it's normal bind, by name.

### 3.2 TX codes table

These numbers are what our RE Layer 2 §3 didn't have. Kept here because it's the key for any app of ours to talk to the service without the original AIDL (which Mitsubishi doesn't publish):

```
# IVehicleInfoManagerApService
TX_GET_VEHICLE_INFO       = 12
TX_GET_FOOT_BRAKE         = 102
TX_GET_TURN_SIGNALS       = 103
TX_REGISTER_BCAN_LISTENER = 25
TX_REGISTER_FCAN_LISTENER = 35
TX_NOTIFY_BCAN_RECEIVE    = 88

# Subkeys of getVehicleInfo(int)
VEHICLE_INFO_ILLUMINATION  = 0
VEHICLE_INFO_SHIFT         = 1
VEHICLE_INFO_PARKING_BRAKE = 6
VEHICLE_INFO_SPEED         = 8
VEHICLE_INFO_GEAR          = 9

# IAvApService
TX_AV_GET_VOLUME     = 22     (type MAIN = 0)
TX_AV_GET_VOLUME_MAX = 160
TX_AV_GET_MUTE       = 24
TX_AV_GET_SOURCE     = 72

# IDiagService
DIAG_TX_INITIALIZE    = 1
DIAG_TX_REQUEST       = 3
DIAG_CANDATA_GET_FCAN = 3998210
DIAG_CANDATA_GET_BCAN = 3998209
```

### 3.3 Internal Mitsubishi B-CAN IDs

Resolved by the internal `ConstExt` class. These are **not** wire CAN IDs; they are the IDs that `IVehicleBcanInformationListener` receives in the `type` field:

| Internal ID | Symbolic key | Content |
|---|---|---|
| `318263376` | `VSPNE` | speed + rpm |
| `318263632` | `AT` | transmission / gear position |
| `318264400` | `ILLUMI` | illumination (headlights) |
| `318337360` | `STEERING` | steering wheel angle |
| `184053784` / `184053776` | `HLSW_BCM` / `HLSW_ICU` | turn signals |
| `318246936` / `318246928` | `MICU_BCM` / `MICU_ICU` | **reverse light**, one-touch |
| `318334800` | `MAINTENANCE` | oil, service interval |
| `318333520` | `TRICOM` | range (`C_TRICOM_RANGE`, `..._UNIT`) |
| `318336336` | `MET_CUSTOM` | ADAS (CMBS, LKAS, RDM) |

### 3.4 Registration flow (confirms RE §3)

```
bindService(VehicleInfoManagerApService, ServiceConnection)
   → onServiceConnected(binder):
       transact(TX_REGISTER_BCAN_LISTENER, writeInterfaceToken + writeStrongBinder(BcanListener))
       transact(TX_REGISTER_FCAN_LISTENER, writeInterfaceToken + writeStrongBinder(FcanListener))
       for each canId in CanDefinitions.BCAN_MESSAGES:
           transact(TX_NOTIFY_BCAN_RECEIVE, writeInt(canId))   ← subscribes to the frame
```

The listeners come as `Binder.onTransact(code, data, …)` with descriptor `IVehicleBcanInformationListener` / `IVehicleFcanInformationListener`, `type` (int) and a `Bundle` with the signals already decoded.

> **Note from Clusters itself:** "the Mitsubishi middleware pre-decodes raw frames and only delivers integer Bundle values to app-level listeners — raw bytes are NOT forwarded". That is, on the Android side you can read decoded signal; raw CAN only with native library or direct socket CAN.

### 3.5 Architectural pattern (confirmed in other platforms)

`HondaHUDdiy` (**newer** Honda platform, Android 10 + Alpine) uses **the same scheme** with different names:

```
Intent i = new Intent("com.alap.honda30ea.aochr.meterservice.MeterService");
i.setPackage("com.alap.honda30ea.aochr.meterservice");
bindService(i, conn, BIND_AUTO_CREATE);
// 12 TX codes of IMeterServiceManager (sendByte / sendBitmap / sendTBTInfo / getBCanState etc.)
```

Important: `HondaHUDdiy` observes that **you should not** use `setComponent` with the real class name (`...service.MeterService`), and should only use `package + action`, because the real class has a `service` sub-package that the action doesn't reveal. **Lesson for us:** if we write a bind using only the action (without `setComponent`), we have to confirm with `cmp=` in logcat that the resolved service is the expected one — AVApService or VideoManager might have similar structure.

### 3.6 Impact for our project

- **Phase 9 (reverse camera without logcat).** Instead of polling, you can `bindService` on `VehicleInfoManagerApService`, register `BcanListener`, call `notifyBcanReceiveSetting` with `MICU_BCM`/`MICU_ICU` (reverse light), and handle the callback. Cleaner and does not depend on `am_create_activity`.
- **Already-known alternative:** `ICameraAPServiceReverseSignalListener` (MAPA X-ray §1). Compare both before choosing.
- **Hypothetical AutoOk v0.6.0** could expose a status via `IAvApService` (volume / mute / source) so the watchdog itself knows whether CarPlay is on a call, before any tap. Closes the hole v0.5.4 solved only with a filtered needle.
- **Permission.** The VehicleInfoManager manifest asks for `com.mitsubishielectric.ada.permission.VEHICLE_RW`. The [`05-trust-map.md`](05-trust-map.md) confirms: it's GID-only, 70/110 APKs declare it. Our AutoOk can also declare it with no signature issue (was part of the Phase 10 decision).
- **Android 4.2.2 permissions don't need runtime grant** (`INSTALL.md` of Clusters). Any new app of ours inherits that.

## 4. 🚨 Critical finding — our `su` is **KingoSU**, not SuperSU

The [`joshfng/root-honda`](https://github.com/joshfng/root-honda/blob/main/AUDIT.md) audit (published on 2026-10-13, 14 days before this scan) discovered that the `su` from upstream `codeage/root-honda` is **not** Chainfire's — it's **KingoSU**. Applies literally to our binary too:

| Fact | Evidence |
|---|---|
| **SHA-256 matches exactly** | `tooling/ota-build/bin/su` → `4f399ccd4c53bf1a12cbcc7f1b2bd23354491111358937c2da51d3355333fa84` — same string cited in AUDIT.md. |
| **Strings identify KingoSU** | `strings` reveals `--- KingoSU notice ---`, `KingoSU v%d.%s%d Copyright (C) 2012-2015 - KingoSu`, paths in `/data/data/com.kingouser.com/`, broadcast `-n "com.kingouser.com/.NativeAccessReceiver"`. |
| **Different behavior from SuperSU** | On every `su` call, fires `am broadcast -a com.kingouser.com.NativeAccess ... -n com.kingouser.com/.NativeAccessReceiver` with UID, command, code. Since the manager `com.kingouser.com` is **not** installed on the HU, the broadcast is a no-op — but it's a public broadcast that ActivityManager registers. |
| **Came from 2016PilotOneClick** | Same `su` hash as `jersacct/2016PilotOneClick`. `codeage/root-honda` just rebadged it. |

**What this concretely means for our project:**

1. **Not a functional failure.** `su` works — AutoOk v0.5.4 calls `su` continuously and the taps hit. The "no-op" broadcast is cosmetic.
2. **May fill `logcat.events` with `am_broadcast`** every time AutoOk taps — the mute bug itself (§17.15) hinted that the events buffer is sensitive to `am_*` while our watcher reads from it.
3. **Prior assumption broken.** `MAPA.md` said "Setuid root ARM. From `codeage/root-honda` (simple SuperSU-adjacent 2.78)". **False** — it's KingoSU, not SuperSU-adjacent.
4. **Fix already exists.** `joshfng/root-honda` publishes the correct `su` from Chainfire SR1 (SHA-256 `67e4d251a8173b82f643aae45e53c5265ef4178d8c68c48f0429b38e2471155d`) extracted from the official zip `download.chainfire.eu`.

**Recommended technical plan** (not applied in this session; just documented):

1. Download `armv7/su` from the official Chainfire SR1 zip via the URL joshfng documents.
2. Validate SHA-256 against `67e4d251…`.
3. Replace `tooling/ota-build/bin/su` and regenerate AutoOk's `build.py`.
4. **Validate in the car** before deploying to prod — any `su` swap changes the SELinux context path on Android 4.2.2, and v0.5.4's `AvisoMatcher` depends on `su` continuing to run in the same context it does today.
5. Change the mode in the `nefarious.sh`-like of the package: today our updater-script uses `chmod 06755` (correct); upstream `codeage/root-honda` used `6777` (world-writable, serious). We already have the right one.

Impact on the current AutoOk (v0.5.4) **is zero** — `su` has been serving the `input tap` without failing for months. But when AutoOk's next rebuild ships (when `build.py` with busybox `chown`/`chmod` is applied, §17.18), **this is the natural window** to swap `su` too.

### 4.1 Mandatory update in MAPA

MAPA §10.2 says "simple SuperSU-adjacent 2.78". I'll correct it to "KingoSU `v*`, from upstream `jersacct/2016PilotOneClick` via `codeage/root-honda` — see audit `joshfng/root-honda` AUDIT.md and §4 of `raio-x/08-github-landscape-2026-10-27.md`. Swap for Chainfire SR1 `su` pending".

## 5. opendbc / openpilot — canonical CAN table for our Civic

[`commaai/opendbc`](https://github.com/commaai/opendbc) carries, in the directory `opendbc/dbc/generator/honda/`:

- `honda_civic_touring_2016_can.dbc` and `honda_civic_hatchback_ex_2017_can.dbc` — **same generation as our vehicle**
- Shared imports: `_honda_common.dbc`, `_gearbox_common.dbc`, `_steering_sensors_a.dbc`, `_steering_control_a.dbc`, `_nidec_common.dbc`, `_lkas_hud_5byte.dbc`, `_bosch_2018.dbc`

This matches **exactly** the `.dbc` that Clusters' `CanDefinitions.java` cites as source. In `_honda_common.dbc` the 23 relevant messages include:

```
BO_ 388 HYBRID_BRAKE_ERROR
BO_ 420 VSA_STATUS
BO_ 427 STEER_MOTOR_TORQUE
BO_ 464 WHEEL_SPEEDS
BO_ 490 VEHICLE_DYNAMICS
BO_ 547 BRAKE_HOLD_HYBRID_ALT
BO_ 597 ROUGH_WHEEL_SPEED
BO_ 777 CAR_SPEED
BO_ 780 ACC_HUD
BO_ 804 CRUISE
BO_ 1029 DOORS_STATUS
BO_ 1302 ODOMETER
```

**For us:** if one day we write our own Android app that consumes `BcanListener`/`FcanListener` from `VehicleInfoManagerApService`, these 11-bit IDs are the reference decoder to interpret the `type` arriving in the `Bundle`. Clusters' own documentation already acknowledges that the middleware pre-decodes the frames and delivers `int`/`Bundle`, not raw bytes — so we would use opendbc as the source of truth about **what** the decoded field means, not to decode it ourselves.

## 6. Honda family × Mitsubishi platform

The `kristate/krackinfo` matrix helps see the real scope of our discovery:

| Honda model | SoC/device | DA version | Technical compat |
|---|---|---|---|
| **Civic 10th gen 2016/2017** | `vcm30t30` (Tegra 3) | `MY17ADA` | **Our HU**; CR-V China, Avancier/URV use the same. |
| Pilot, Accord, NSX, Clarity, Ridgeline, Spirior | `koelsch` | `MY15ADA`/`MY16ADA` | Mitsubishi ADA stack, different chip. ic1101 issue #13 is from this family (Clarity). Our app-level findings may hold; our bootloader/kernel findings do not. |
| Unit Assy AVN | `h16` | SiRFSoC Android | Different. |

Combined with issue #29 (CR-V China `1.F198.60`), this gives 3 confirmed compatible with our OTA packages (BR Civic, US Civic, China CR-V), and 6 "cousin" families where the app's logical analysis holds, with hardware adaptations.

## 7. `cysin/honda_hacking_analysis` — out of scope, but a signal

16★, created in 2021. The repo documents the **commercial, paid** Chinese ecosystem (HondaHack, AutoHack, VinciCar — products that sell HU "unlocks"). Contains:

- Native loaders (`.so` + `.c`) and installation scripts.
- AES keys and commercial licensing logic.
- Web path (via browser) for persistence.
- Detailed writeup at [52pojie.cn/thread-1376274-1-1.html](https://www.52pojie.cn/thread-1376274-1-1.html).

**I deliberately did not include** here anything about the specific mechanism of these tools. It serves only as a signal that:

1. The same HU has been targeted for 4+ years.
2. There are commercial products exploiting it (sold in the Chinese market).
3. Our choice to **publish the EvilValet flow openly** does not introduce new risk — the knowledge was already available on paid channels.

## 8. Supply chain and public discussion (librick writeup 2026-06-13)

Reflected in `ahastudio/til` (Korean) + HN thread (342 pts). Relevant points for our project:

- The **AOSP testkey is still accepted** in official 2026 packages. librick validated with `MRC_EU_SW_v12_4.zip` downloaded from a public forum.
- Honda uses a Mitsubishi AOSP fork; the problem is of **supply chain security review**, not of the individual car.
- "signed ≠ signature verified" (standard in commercial firmware, heavily cited in the HN thread).
- `hnav` raised public doubt about the HU being a gateway to other ECUs and about CarPlay/Android Auto as vectors — we are on the HU, we don't escalate outside it.
- Government bodies started to treat it as a formal threat (comment `bigfatkitten`).

**What this changes for us:** nothing on the technical plan. **Confirms** that the EvilValet window remains open and that our choice to use `testkey` for the Phase 10 DaLauncher OTA package remains valid indefinitely.

## 9. What was left **out** of this scan

Deliberately not detailed or reproduced here:

- Injection mechanisms, native loaders, licensing cracks, complete remote root-via-browser chains, or keys/credentials used by Chinese commercial tools (AutoHack / VinciCar / HondaHack).
- Signed APKs of the commercial products (nor the Honda Hack obfuscated via Tencent Legu that `joshfng/root-honda` mentions in `packages/`).
- Anything that would facilitate abusing third-party HUs without the owner's authorization.

What external code the project already consumes is in `tooling/references/` via `setup.sh` (ic1101 Apache 2.0, root-honda, 2016PilotOneClick) — stays as is. May change: see §4.

## 10. Consolidated impact — what goes to code / docs

| # | Source | What to do | Where |
|---|---|---|---|
| 1 | `joshfng/root-honda` AUDIT.md | **Document KingoSU in MAPA §10.2** and open PENDENCIAS item for Chainfire SR1 `su` swap in the next AutoOk rebuild. | §4 of this note, MAPA §10.2, PENDENCIAS |
| 2 | Clusters: TX codes of `IVehicleInfoManagerApService` + B-CAN IDs | Update [`07-services-re.md §3`](07-services-re.md) with the TX codes and internal IDs. Candidate for Phase 9. | `07-services-re.md`, MAPA §13 |
| 3 | Clusters: `IAvApService` TX codes (`setMute`/`getVolume`/`getSource`) | Closes the RE §4 (audio) gap without needing to deodex `AvApService`. | `07-services-re.md §4` |
| 4 | ic1101 issue #6: Honda Hack binds `IVideoManagerApService` | Add to the list of future-deodex candidate services. | PENDENCIAS |
| 5 | ic1101 issue #20: USB mode chain via sysfs | Optional script to enable ADB without physical combo (after Phase 10 deploy). | PENDENCIAS |
| 6 | ic1101 issue #29: CR-V China is same family | Compatibility matrix gets one more line. | `nova-safra.md`, ROADMAP |
| 7 | opendbc: Civic Touring 2016 + Hatchback EX 2017 DBCs | Technical note: use as oracle to interpret the `type` of BcanListener. | `07-services-re.md §3`, PENDENCIAS |
| 8 | HondaHUDdiy PROTOCOL.md | Lesson of bind "only with `package + action`"; use with care if we bind without `setComponent`. | internal guide when we reach the new app |
| 9 | librick 2026-06 writeup: testkey still accepted | Confirmation; no operational change. | this note, no code to touch |

The 33 projects are catalogued here for whoever picks up the RE part later — most are "read README and follow", only §4 asks for concrete action.
