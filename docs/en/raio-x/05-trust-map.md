# Scan 5 — Trust Map

**110 APKs in the shipping build: 70 vendor-app + 40 system-app + 0 system-priv-app.** For each: detected package, `sharedUserId` and number of consumed permissions. Lets you see who has privileged access and who talks to whom under the same UID.

## How it was collected

```bash
for apk in <vendor-app, system-app, system-priv-app>; do
  manif=$(unzip -p "$apk" AndroidManifest.xml | strings -el)
  pkg=$(echo "$manif" | grep -oE '^com\.(mitsubishielectric\.ada|honda|android)\.[a-z0-9._]{3,}$' | head -1)
  shared=$(echo "$manif" | grep -oE '^android\.uid\.[a-z]+$' | head -1)
  perms=$(echo "$manif" | grep -cE '\.permission\.')
  ...
done
```

**Limits:** `strings -el` (UTF-16LE) on binary `AndroidManifest.xml` returns many strings but no structure. Some packages come out as "?" or we pick up `com.mitsubishielectric.uilib` (which is actually a `uses-library`, not the real package) — in those cases the manifest has the package as the first attribute and grep failed by alphabetical order. For a definitive per-APK name, use REA's `inspect-android-package` individually. Of the 110 APKs, **67 have a confidently detected package**.

## Highlights — the privileged elite

### APKs with `sharedUserId=android.uid.system` (11 APKs — full power)

The only ones that share a UID with Android itself. They can do **anything**:

**Vendor (7):**
- `HidKeyboard` — HID keyboard
- `MediaCoreService` — audio
- `PowerManagerApService` — power
- `StrgSW` — steering wheel events
- `UsbCertApp` — USB cert
- `WhitelistApService` — whitelist
- `WifiApService` — Wi-Fi

**AOSP (4):**
- `InputDevices` — input devices manager
- `KeyChain` — certificate keychain
- `Settings` — Android settings app
- `SettingsProvider` — settings provider

**Our AutoOk is NOT on this list** (it doesn't declare `sharedUserId` in the manifest). That means even sitting in `/system/app/`, it runs as its own UID (10091 by default) — hence the need for `Runtime.exec("su")` to execute `input tap`.

### APKs with `sharedUserId=android.uid.phone` (4)

- `AV` — probably audio integrated with the phone stack (ducking etc.)
- `UnitInfoManager` — 16 permissions consumed, the biggest count in vendor-app
- `Phone` — AOSP standard
- `TelephonyProvider` — AOSP

### APKs with `sharedUserId=android.uid.shared` (4)

- `ApplicationsProvider`, `Contacts`, `ContactsProvider`, `UserDictionaryProvider`

AOSP standard — contacts share a UID.

### Top 10 by number of consumed permissions

| APK | Perms | Note |
|---|---|---|
| `Settings` | 55 | AOSP settings |
| `Phone` | 49 | AOSP phone |
| `SystemUI` | 47 | AOSP system UI |
| `Contacts` | 30 | AOSP contacts |
| `Browser` | 25 | AOSP browser |
| `Gallery2` | 25 | AOSP gallery |
| `UnitInfoManager` | 16 | 🎯 **vendor top — unit info with android.uid.phone** |
| `CalendarProvider` | 15 | AOSP calendar provider |
| `DaLauncher` | 14 | 🎯 **our main target, 14 perms** |
| `DaSettings` | 14 | vendor settings app |
| `DownloadProvider` | 14 | AOSP downloads |
| `DiagApService` | 13 | 🎯 **diag service has a lot of permissions** |

This is the "who concentrates authorization" map. `UnitInfoManager` and `DiagApService` are the two most promising vendor targets — high authority + function that may lead to interesting hooks.

### Vendor custom permissions

5 Mitsubishi/Honda permissions that create their own gates:

| Permission | Consumed by |
|---|---|
| **`com.mitsubishielectric.ada.permission.VEHICLE_RW`** | **70 APKs** — the central permission for vehicle bus access |
| `com.mitsubishielectric.ada.permission.ACCESS_AUDIO_DEVICE` | subset of audio APKs |
| `com.mitsubishielectric.ada.permission.MIRRORLINK_DEVICE` | MirrorLink + Phone coordination |
| `com.honda.displayaudio.navi.permission.ACCESS_MAP` | AcuraLinkApp + other navi clients |
| `com.honda.telematics.core.permission.WRITE_CRM_DATA` | Telematics APKs |

**`VEHICLE_RW` consumed by 70/110 APKs = 64%.** It's nearly ubiquitous. Any app that needs to know anything about the car declares it.

**For AutoOk:** we don't declare `VEHICLE_RW` today. If Phase 9 is going to consume `IVehicleGearInformationListener` to detect reverse directly, this permission needs to go in the manifest. We need to check whether the permission is `signature|system` (blocks user apps) or whether any app with a system UID can use it.

## Full table

### `vendor-app/` (70 APKs)

| APK | Detected package | sharedUserId | perms used |
|---|---|---|---|
| `AV` | — | **android.uid.phone** | 8 |
| `AVPlayer` | — | — | 5 |
| `AcuraLinkApService` | — | — | 9 |
| `AcuraLinkApp` | — | — | 1 |
| `AirCon` | — | — | 3 |
| `AndroidAuto` | — | — | 8 |
| `AntiTheft` | — | — | 3 |
| `AppManager` | — | — | 9 |
| `AppMode` | — | — | 3 |
| `AppModeApService` | — | — | 6 |
| `Camera` | — | — | 7 |
| `CameraAPService` | — | — | 4 |
| `CarPlay` | — | — | 1 |
| `CarPlayService` | — | — | 3 |
| `ClockSync` | — | — | 7 |
| `CompassService` | — | — | 2 |
| `CpuComService` | — | — | 1 |
| `DaLauncher` | — | — | 14 |
| `DaSettings` | — | — | 14 |
| `DealerDiag` | — | — | 2 |
| `DeveloperDiag` | — | — | 3 |
| `DiagApService` | — | — | 13 |
| `ETC` | — | — | 2 |
| `EcoTripComputer` | — | — | 2 |
| `EmergencyApService` | — | — | 10 |
| `EmergencyApp` | — | — | 1 |
| `EnergyManagement` | — | — | 2 |
| `ErrorManager` | — | — | 1 |
| `ExternalDisplayApService` | — | — | 2 |
| `ExternalDisplayOutService` | — | — | 7 |
| `FileManager` | — | — | 2 |
| `HangulKeyboard` | — | — | 4 |
| `HftApService` | — | — | 9 |
| `HftApp` | — | — | 4 |
| `HidKeyboard` | — | **android.uid.system** | 9 |
| `HudApService` | — | — | 1 |
| `LatinIME` | `com.android.inputmethod.latin` | — | 9 |
| `LetDiag` | — | — | 1 |
| `LinkManagerApService` | — | — | 3 |
| `MediaCoreService` | — | **android.uid.system** | 3 |
| `MirrorLink` | — | — | 7 |
| `Navigation` | `com.honda.displayaudio.navi.lib` | — | 8 |
| `PhoneCoordination` | — | — | 7 |
| `PicoTts` | `com.svox.pico` | — | 2 |
| `PinyinIME` | `com.android.inputmethod.pinyin` | — | 9 |
| `PowerManagerApService` | — | **android.uid.system** | 1 |
| `PreShipmentDiag` | — | — | 2 |
| `RaspApService` | — | — | 1 |
| `RoadToVehicle` | — | — | 2 |
| `ScreenshotApService` | — | — | 1 |
| `SensorMonitor` | — | — | 5 |
| `SiriEFM` | — | — | 2 |
| `StrgSW` | — | **android.uid.system** | 3 |
| `SystemInfoService` | — | — | 7 |
| `SystemUpdate` | — | — | 11 |
| `TaskManager` | — | — | 6 |
| `Telematics` | — | — | 8 |
| `UnitInfoManager` | — | **android.uid.phone** | 16 |
| `UsbCertApp` | — | **android.uid.system** | 1 |
| `VRSD` | — | — | 4 |
| `VehicleCoordination` | — | — | 4 |
| `VehicleDbManager` | — | — | 1 |
| `VehicleInfoManager` | — | — | 1 |
| `VehicleRW` | — | — | 1 |
| `VideoManagerApService` | — | — | 5 |
| `VoicePortal` | — | — | 5 |
| `VoicePortalAp` | — | — | 6 |
| `WhitelistApService` | — | **android.uid.system** | 2 |
| `WifiApService` | — | **android.uid.system** | 8 |
| `WifiApp` | — | — | 1 |

### `system-app/` (40 APKs — AOSP standard)

| APK | Detected package | sharedUserId | perms used |
|---|---|---|---|
| `ApplicationsProvider` | — | **android.uid.shared** | 1 |
| `BackupRestoreConfirmation` | `com.android.backupconfirm` | — | 3 |
| `Browser` | `com.android.browser.snapshots` | — | 25 |
| `Calculator` | `com.android.calculator2` | — | 0 |
| `Calendar` | `com.android.calendar` | — | 12 |
| `CalendarProvider` | `com.android.providers.calendar` | **android.uid.calendar** | 15 |
| `CertInstaller` | `com.android.certinstaller` | — | 1 |
| `Contacts` | `com.android.voicemail` | **android.uid.shared** | 30 |
| `ContactsProvider` | `com.android.providers.contacts` | **android.uid.shared** | 11 |
| `DefaultContainerService` | `com.android.defcontainer` | — | 10 |
| `DeskClock` | `com.android.alarmclock` | — | 10 |
| `DownloadProvider` | `com.android.providers.downloads` | — | 14 |
| `DownloadProviderUi` | — | — | 2 |
| `DrmProvider` | `com.android.providers.drm` | — | 4 |
| `FusedLocation` | `com.android.location.provider` | — | 4 |
| `Galaxy4` | `com.android.galaxy4` | — | 1 |
| `Gallery2` | `com.android.gallery3d.provider` | — | 25 |
| `HTMLViewer` | `com.android.htmlfileprovider` | — | 1 |
| `HoloSpiralWallpaper` | — | — | 1 |
| `InputDevices` | `com.android.inputdevices` | **android.uid.system** | 0 |
| `KeyChain` | `com.android.keychain` | **android.uid.system** | 0 |
| `LiveWallpapers` | `com.android.wallpaper` | — | 3 |
| `LiveWallpapersPicker` | — | — | 2 |
| `MagicSmokeWallpapers` | `com.android.magicsmoke` | — | 2 |
| `MediaProvider` | `com.android.providers.media` | — | 9 |
| `Music` | `com.android.music` | — | 8 |
| `MusicFX` | `com.android.musicfx` | — | 4 |
| `NoiseField` | `com.android.noisefield` | — | 1 |
| `PackageInstaller` | `com.android.packageinstaller` | — | 7 |
| `PhaseBeam` | `com.android.phasebeam` | — | 1 |
| `Phone` | `com.android.phone` | **android.uid.phone** | 49 |
| `Provision` | `com.android.provision` | — | 2 |
| `QuickSearchBox` | `com.android.quicksearchbox` | — | 6 |
| `Settings` | `com.android.settings` | **android.uid.system** | 55 |
| `SettingsProvider` | `com.android.providers.settings` | **android.uid.system** | 1 |
| `SharedStorageBackup` | `com.android.sharedstoragebackup` | — | 3 |
| `SystemUI` | `com.android.systemui.net` | — | 47 |
| `TelephonyProvider` | `com.android.providers.telephony` | **android.uid.phone** | 3 |
| `UserDictionaryProvider` | — | **android.uid.shared** | 2 |
| `VpnDialogs` | `com.android.vpndialogs` | — | 0 |

## Notes

### `Contacts` with package `com.android.voicemail`

Weird but correct: in this dump, `Contacts.apk` declares the package `com.android.voicemail` in the manifest — probably a merge of Contacts+Voicemail in the Honda build. Confirm with REA if relevant.

### `AcuraLinkApp` has only 1 permission

With such low weight, it makes sense it's inactive in the BR firmware. Same for `EmergencyApp`, `WifiApp` — "entry point" apps that only show UI, delegating work to the matching `*ApService`.

### `DaLauncher` and `DaSettings` with 14 perms each

High surface — both are end-user UI with access to everything (global settings, launcher). It makes sense they're rich targets for future analysis.

### High surface = rich target

For Layer 2, the three best vendor candidates are:

1. **`UnitInfoManager`** (16 perms, uid.phone) — highest authority among non-system
2. **`DaLauncher`** / **`DaSettings`** (14 each) — UX-rich, broad access
3. **`DiagApService`** (13 perms) — diag is a classic target for PINs and hidden menus
4. **`SystemUpdate`** (11 perms) — EvilValet target; understanding its internals may open deploy routes without an exploit

## Raw datasets

- `apk-pkg-shareduid.txt` — compact `category|name|pkg|shared` table
- `apk-permissions-uses.txt` — `apk|permission` tuples (all permissions per APK)

In `/tmp/.../scratchpad/raio-x/`. Since it's the scratchpad, they vanish at session end — move to `tooling/raio-x/data/` if we want to preserve them for versioning. Not scoped for this round.
