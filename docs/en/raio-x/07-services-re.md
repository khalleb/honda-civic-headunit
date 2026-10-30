# X-ray Layer 2 — RE of the services (steering wheel, official OTA, vehicle, audio)

Static analysis from 2026-10-27, based on the dumps we already have (`tooling/apks-dumped/dump-0040/vendor-app/*.odex`), deodexed with baksmali 2.5.2 (API 17, bootclasspath = `system-framework` + `vendor-framework`). No car visits.

Four services deodexed in this pass: `StrgSW`, `SystemUpdate`, `VehicleInfoManager`, `SystemInfoService`. First step (API + mechanism), not a line-by-line dive.

> **Native RE is blocked with the current dumps.** `daupdater` lives in the recovery ramdisk (MTD `recovery`), which was never dumped, and **there is no `.so` in the dump** (`vendor-framework` is odexed `.jar`, not native library). So "Ghidra on `daupdater` / on the `.so`" is not doable now — it depends on dumping the recovery ramdisk and the libraries in `/system/lib` and `/system/vendor/lib`.

---

## 1. Steering wheel — `StrgSwApService`

Service `StrgSW` (`com.mitsubishielectric.ada.appservice.strgsw`). 12 classes. Receives steering wheel keys from `cpucomservice` (object `KeyCommandData`) and dispatches them to registered clients via `RemoteCallbackList`.

**Flow:** hardware → B-CAN → `cpucomservice` (`KeyCommandData`) → `StrgSwApService.judgeSendEvent()` → `convertKeyType`/`convertKeyStatus` → sends to callbacks + native bridge `sendStrgSwEventToFramework(II)` (**`native`** method). There's also a hardware gate at `/dev/vehicle_sts/key_consumed_status`.

**Exposed event flows** (each has its own `RemoteCallbackList` for registration):
- `sendStrgKeyEvent` / `sendPriorityStrgKeyEvent` — normal and priority keys
- `sendRotaryKeyEvent` — the rotary controller (4-way)
- `sendMotionMenuEvent` — motion menu
- `sendRaspKeyEvent` — "RASP" events
- `sendStrgSwBcanInformation` — raw B-CAN information
- `sendStrgSwStatus` — steering wheel status
- `sendStrgKeyEventLog` — event log

**Payload** (`KeyCommandData`, 17 private fields, most relevant):
- `mStrgKeyCode:I` — **raw key code** (1..17 on the 2017 Civic EXL B-CAN)
- `mStrgKeyDetail:I` / `mStrgKeyDetail2:I` — details (short/long press, timing)
- `mKeyType:I` — raw event type
- `mVol:I`, `mVolXcoordinate:I`, `mVolYcoordinate:I` — rotary controller values
- `mAudio:I`, `mBack:I`, `mHome:I`, `mMenu:I`, `mNavi:I`, `mPhone:I`, `mPower:I`, `mTilt:I`, `mDayNight:I` — flags for specific keys

**`raw code → logical type` mapping** (extracted from `StrgSwApService.convertKeyType(I)` via `scratchpad/extract_keys.py`, 17 cases):

| Raw | 0x | Logical type | Note |
|---|---|---|---|
| 1 | 0x01 | 1 | |
| 2 | 0x02 | 2 | |
| 3 | 0x03 | -100 (default/error) | not used in this firmware |
| 4 | 0x04 | 4 | |
| 5 | 0x05 | 5 | **press** (press/release of the same button pair up) |
| 6 | 0x06 | 6 | **press** |
| 7 | 0x07 | 7 | **press** |
| 8 | 0x08 | 8 | **press** |
| 9 | 0x09 | 5 | **release** (pairs with raw 5) |
| 10 | 0x0a | 6 | **release** (pairs with raw 6) |
| 11 | 0x0b | 7 | **release** (pairs with raw 7) |
| 12 | 0x0c | 8 | **release** (pairs with raw 8) |
| 13-14 | — | -100 | not used |
| 15 | 0x0f | 10 (0xa) | |
| 16 | 0x10 | 11 (0xb) | |
| 17 | 0x11 | 12 (0xc) | |

**Symbolic name ↔ logical type is still unresolved** without the car. What we found (`C_TALK`, `C_PICKUP`, `C_FOURWAY_ENTER` etc.) are actually **BCAN status `Bundle` keys** (`mBcanStSwPadInfo.putInt("C_VOLUME_TOUCH", -1)`), not key type constants. The correlation `logical type 1=TALK`, `2=PICKUP`, etc. requires 1 test in the car — press each key with a registered listener and read `getKeyType()`. Low cost, high value for any future app.

**Exposed event flows** (each has its own `RemoteCallbackList` for registration):
- `sendStrgKeyEvent` / `sendPriorityStrgKeyEvent` — normal and priority keys
- `sendRotaryKeyEvent` — the rotary controller (4-way)
- `sendMotionMenuEvent` — motion menu
- `sendRaspKeyEvent` — "RASP" events
- `sendStrgSwBcanInformation` — raw B-CAN information (the `C_*` from the Bundle)
- `sendStrgSwStatus` — steering wheel status
- `sendStrgKeyEventLog` — event log

**How an app of ours would use it:** register a callback on the `IStrgSwApService` Binder (bind on the `StrgSW` service) implementing the `IStrgSwApServiceListener.onKeyEvent(KeyCommandData)` interface. Needs the service permission (to confirm — likely GID vehicle, like the rest). This gives steering wheel buttons without logcat polling — useful for replacing AutoOk with a real listener, or for Phase 9.

---

## 2. Official OTA — `SystemUpdateApService`

This is the **official update path**, the app-level sibling of `daupdater` (native, in recovery) that our EvilValet uses. `SystemUpdateApService` + `SystemUpdateUtility` (139 classes).

**Central finding:** the official app stages the recovery command **the same way** `daupdater` does, and is the one that writes the files our updater-script needs to clean:
- Reads the trigger on the pendrive: `SwUpdate2.txt` (and `SwUpdate.txt`, states `SWUPDATE_ONE`/`SWUPDATE_TWO`) in `/mnt/usbdrive1` and `/mnt/usbdrive2`
- Copies the command to `/cache/recovery/` (`SwUpdate.mdt`, `custom_rom`, `version`) with `--update_package=` pointing to the `.mdt`
- Writes **`/cache/.copy_complete`** — exactly the flag our `build-*.py` erases before the final sleep so it doesn't re-apply in a loop (§17.17). Now we know who writes it: `SystemUpdateApService`
- Logs `"Cannot copy command file to /cache partition"` / `"/cache partition may be broken!!"` on failure
- Calls `IPowerManagerApService.rebootRequest()` (`"!!! REBOOTING TO INSTALL"`, `ColdReboot`/`AccOnReboot`) → "Go to recovery mode"
- Announces at the end with the broadcast `com.mitsubishielectric.ada.app.systemupdate.ACTION_SWUPDATE_COMPLETE_NOTIFY`

It also processes `modelinfo_setting.txt`, `syscomver.txt` and `SystemInf.bin` on the pendrive (reprograms model info / syscom version — classes `SystemUpdateReprogramData`, `SystemUpdateHeader1/2/3`, `SwUpdateCommandType/Version/Line`).

**Why it matters:** confirms why `build.py` keeps `NEW_DA_VERSION="IC1101"` — to **avoid** falling into the app-based SystemUpdate flow and use `daupdater` directly. And it gives a Plan B for deploy that doesn't depend on EvilValet: deliver a `.mdt` via the path `SystemUpdateApService` already accepts. Kept as an alternative route to investigate if `daupdater` ever refuses our packages.

### 2.1 Concrete validations in SystemUpdateUtility (deodex of 2026-10-30)

Deodex of `SystemUpdate.apk` (139 smali) + `SystemUpdateLib.odex` (10 smali, only IAIDL + consts) revealed that the real implementation of the flow lives in `SystemUpdateUtility.smali` (34,138 lines). The gates the `.mdt` has to pass before the reboot:

1. **`checkVersion(int)`** — reads `Build:ID` from the pendrive's `/system/build.prop`, checks it against the family regex `"1.F"`, does `Integer.parseInt` of what comes after `1.F` and `Double.parseDouble` on the sub-parts. Logs `"New::"` vs `"Cur::"`. Our packages carry `ro.build.id=IC1101` precisely so this check **fails** and the app-based flow is skipped — forcing the use of `daupdater` directly via EvilValet.
2. **`compareCustomRomInfo(int, String, String)`** — reads the pendrive's `system/vendor/build.prop`, searches for a `key=value` line, compares `"Current string :: ..."` with `"New string :: ..."`. It's the `custom_rom.type` filter — ensures the package firmware matches the car's. Our packages carry `custom_rom.type=0040`, identical to the car, so when we want to use route B this passes.
3. **`copyFileToCache(String)`** — copies the `.mdt` from the pendrive to `/cache/recovery/SwUpdate.mdt`. **There is no own signature verification here** — the AOSP testkey validation happens inside the native `daupdater`, not in this app-based flow.
4. **`createCopyCompleteFile(String)`** — writes `/cache/.copy_complete` with content `"version :: ..."`. It's the flag all our `build-*.py` erase before the final sleep so they don't re-apply in a loop (§17.17).
5. **`bootCommand(IPowerManagerApService, String)`** — writes `/cache/recovery/command` (log `"Cache command file write success"`), then calls `IPowerManagerApService.rebootRequest()` with reason `"recovery"`. Logs `"Go to recovery mode"` and `"IPowerManagerApService.rebootRequest()"`.

**Implication for route B:** delivering a `.mdt` via the official path requires swapping `NEW_DA_VERSION` for something `checkVersion` accepts as a legitimate update (e.g. `1.F187.17`, higher than the firmware's `1.F187.16`) and keeping `custom_rom.type=0040` in `vendor/build.prop`. No additional signature: `SystemUpdateApService` only watches version and rom_type, leaves the cryptographic verification to the recovery's `daupdater`.

---

## 3. Vehicle — `VehicleInfoManagerApService`

Service `VehicleInfoManager` (36 classes). Centralizes B-CAN signals and exposes them via AIDL. Reads from `/dev/vehicle_sts/vehiclesignal` and `/dev/vehicle_sts/vehiclespeedpulse`.

**API (public methods):** `getVehicleInfo`/`setVehicleInfo`, `getDrivingOperationStatus`/`checkDrivingOperationStatus`, `setSpeed`/`setVspSpeed`, `setParkingStatus`/`setTVParkingStatus`, `getCanInformationForAvApService`, `bcanReceiveSetting`, `setBcanCommonData`, plus the customization block (`sendCustomizeSettingChange/Value`, `sendRequestCustomizeReset`, TPMS, maintenance).

**Confirmed signals:** speed (`vehiclespeedpulse`), VIN (`C_VINBYTE2..7`, `C_VINDATACOUNT`, `VINNO`), parking brake (`C_PBRAKE`), and CVT gear position: **`CVT_SHFT_IN_PARKING`**, **`CVT_SHFT_IN_REVERSE`**, `CVT_GEAR_POSITION_IND_CVT`, plus the parking sensors (`PARKSENS`/`PARKSENS2`).

**Resolved TX codes** (via [`alexpotv/Clusters`](https://github.com/alexpotv/Clusters), 2026-10-27 landscape scan — see [`08-github-landscape-2026-10-27.md §3.2`](08-github-landscape-2026-10-27.md)):

| TX | Method |
|----|--------|
| 12 | `getVehicleInfo(int subkey)` |
| 25 | `registerBcanListener(IBinder)` |
| 35 | `registerFcanListener(IBinder)` |
| 88 | `notifyBcanReceiveSetting(int canId)` — subscribes to the frame |
| 102 | `getFootBrake()` |
| 103 | `getTurnSignals()` |

Subkeys of `getVehicleInfo(int)`: `0=ILLUMINATION`, `1=SHIFT`, `6=PARKING_BRAKE`, `8=SPEED`, `9=GEAR`.

**Internal B-CAN IDs** (`type` that `IVehicleBcanInformationListener.onReceive` receives): `318263376 VSPNE` (speed+rpm), `318263632 AT` (gearbox), `318264400 ILLUMI`, `318337360 STEERING`, `318246936/318246928 MICU_BCM/ICU` (**reverse light**), `318334800 MAINTENANCE`, `318333520 TRICOM` (range), `318336336 MET_CUSTOM` (ADAS). Full list in `08-github-landscape §3.3`.

**Why it matters (Phase 9):** `CVT_SHFT_IN_REVERSE` is the reverse signal **via B-CAN**, not via logcat. With the TX codes above + the `MICU_*` IDs, you can `bindService(VehicleInfoManagerApService)` → `transact(25, bcanListener)` → `transact(88, writeInt(318246936))` and handle the callback — without logcat polling. Already-known alternative: `ICameraAPServiceReverseSignalListener` (MAPA X-ray §1).

---

## 4. Audio / mute — `SystemInfoService`

Large service (440 classes). **The audio mute itself does not live here** — it's done via `IAvApService.setMute(boolean)` / `IAvApService.getMute()`, i.e. in `AvApService` (deodexed and analyzed in §5). `SystemInfoService` calls this API and handles the upper layer:
- `VstMute` (+ `VstMuteListener`, `VstMuteTouchMonitorView`) — the "Vst" mute and its touch on screen
- `VolumeOperationController` (+ `VolumeBar*`) — volume operation and long-push of the volume key
- `EXCLUSIVE_STATUS_SOUND_BAR_DISPLAY_MUTE`
- "Interrupt header" (telops) system: `ACTION_INTERRUPT_FAN_CLIMATE`, `hideHeaderInterrupt`, and a branch `"Disclaimer not Passed and CLIMATE_INTERRUPT_TYPE0"` tying into the disclaimer gate

**Relation to the mute bug (v0.4.0):** the AutoOk false tap hit a mute button whose final action is `IAvApService.setMute`. To understand real ducking (lower vs. mute, transient focus) the next step is to deodex `AvApService` and follow `setMute`/`getMute` + the mix list (`Can not get MixPlayList`). With v0.5.4 the bug no longer happens (the needle no longer matches the wrong context), so this is background investigation, not pending fix.

**TX codes of `IAvApService`** — complete table (213/214 resolved, mapped from `onTransact` on 2026-10-29). §5 below presents them by group. Note: the `getSource` Clusters named corresponds to the real method `getCurrentSource` (TX 72).

**For a hypothetical AutoOk v0.6.0:** `getMute` + `getCurrentSource` + a dedup by audio source would remove the remainder of the mute bug risk that v0.5.4 still carries as "proven absent in v0.5.4" rather than "impossible by construction".

---

## 5. Audio — `AvApService` (deodex of 2026-10-29)

Service `AV.apk` (`com.mitsubishielectric.ada.appservice.avapservice`), 719 classes. **Runs as `android.uid.phone`** (same UID as radio/telephone — super privileged). Interface `IAvApService` has **213 public abstract methods** (one of the largest services on the platform). The `SystemInfoService` from §4 talks to it via bind + binder.

Reads from: internal `AudioFocusManager`, controls all car audio.

### 5.1 Mute / volume / source group — TX codes

On 2026-10-29 I mapped the 214 TX codes of `IAvApService` by extracting the `sparse-switch` of `IAvApService$Stub.onTransact` (213/214 methods resolved — the remainder is `0x5f4e5446` = `INTERFACE_TRANSACTION` standard of Android IAIDL, discarded).

| TX | 0x | Method |
|----|-----|--------|
| 22 | 0x16 | `getVolume(int type)` |
| 23 | 0x17 | `setVolume(int type, int value)` |
| 24 | 0x18 | **`getMute(int type)`** |
| 25 | 0x19 | **`setMute(int type)`** |
| 26 | 0x1a | `setMuteExtInfo(...)` |
| 72 | 0x48 | **`getCurrentSource()`** ← Clusters had called this `getSource` |
| 160 | 0xa0 | `getVolumeMax(int type)` |
| 161 | 0xa1 | `getVolumeType(int)` |
| 162 | 0xa2 | `setVolumeRange(int, int, int)` |
| 113 | 0x71 | `getVolumeAdjustParameter(int)` |
| 114 | 0x72 | `setVolumeAdjustParameter(...)` |
| 183 | 0xb7 | `getVolumeDefault(int)` |
| 11 | 0x0b | `getAudioSetting(int)` |
| 12 | 0x0c | `setAudioSetting(...)` |
| 13 | 0x0d | `getAudioPowerStatus()` |
| 81 | 0x51 | `setAudioPowerStatus(...)` |
| 106 | 0x6a | `getAudioList(int, int, Map)` |
| 135 | 0x87 | `getAudioListNum(int, int)` |
| 136 | 0x88 | `getAudioListNumPlusFilter(int, int, Map)` |
| 181 | 0xb5 | `getAudioInterruptEnableStatus(int)` |
| 5 | 0x05 | `getLastSource()` |
| 6 | 0x06 | `setLastSource(...)` |
| 180 | 0xb4 | `getLastSourceIndex()` |
| 196 | 0xc4 | `getVideoSourceType()` |

**Confirms what Clusters had mapped** (22, 24, 72, 160) with a single name correction: TX 72 is `getCurrentSource`, not `getSource`.

### 5.2 Audio focus / interrupt / ducking group — TX codes

| TX | 0x | Method |
|----|-----|--------|
| 132 | 0x84 | `cancelInterrupt(int)` |
| 206 | 0xce | `abandonAudioFocus(int)` |

Only 2 direct TX methods — the rest of the focus/duck flow is via **registered callbacks** (see §5.4 "Register callbacks"), and the concrete logic lives in the service's internal `AudioFocusManager`. Revealing strings:
- `check transient or duck :` — makes the transient (duck) vs. interrupt decision
- `AA-MediaTransient command in AA-VR` — special treatment for Android Auto + voice recognition
- `AA-MediaTransient command in RingTone, dual source path` — dual source path for ringtone
- `change AppMode interrupt.`, `clear interrupt parameter`
- `AudioFocusManager create failed`, `already abandon audio focus`, `focusChange =`

Revealing strings in bytecode:
- `check transient or duck :` — makes the transient (duck) vs. interrupt decision
- `AA-MediaTransient command in AA-VR` — special treatment for Android Auto + voice recognition
- `AA-MediaTransient command in RingTone, dual source path` — dual source path for ringtone
- `change AppMode interrupt.`, `clear interrupt parameter`
- `AudioFocusManager create failed`, `already abandon audio focus`, `focusChange =`

It's the traditional Android `AudioFocusManager`, but with additional layers for `AppMode`/`CarPlay`/`Rasp` (many `registerCallbackForXxx` APIs).

#### 5.2.1 Internal AudioFocusManager (deodex of 2026-10-30)

`com.mitsubishielectric.ada.appservice.avapservice.audiostatemachine.AudioFocusManager` is a singleton (`getInstance(Context)`) of 1448 smali lines that wraps Android's standard `AudioManager.requestAudioFocus(..., streamType, durationHint)`. Three public methods:

- `requestAudioFocus(int source)` → `boolean` — requests focus from Android with `(stream, duration)` derived from the source.
- `abandonAudioFocus(int source)` → `boolean` — releases focus for that source.
- `abandonAudioFocus()` → `boolean` — releases the current focus.

The "ducking vs. interrupt" is decided by `changeDurationFromSourceType(int source)`:

| Sources (hex) | Duration used | Behavior |
|---|---|---|
| `0x0c, 0x1f, 0x22, 0x2e, 0x2f, 0x30, 0x31, 0x32, 0x37, 0x39` | **`0x3` = `AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK`** | the other source's audio is lowered (duck) |
| **rest** (default) | `0x2` = `AUDIOFOCUS_GAIN_TRANSIENT` | the other source's audio is interrupted (pause) |

And the stream type via `changeStreamTypeFromSourceType(int source)` which indexes `AudioStateMachineDefine.PRIORITYTYPE[source]`. The output streams are **Mitsubishi-customized** (`0x100`–`0x10a`), not Android's standard `STREAM_MUSIC=3`/`VOICE_CALL=0` — i.e. the internal pipeline runs with private stream types that the platform's `audio_policy.conf` maps to PCM.

**Dedicated ducks** (`com.mitsubishielectric.ada.appservice.avapservice.audio`):

- `CarPlayDuck` (74 lines): `start(AvPlayParameter)` / `stop()`. Called when the active source is CarPlay.
- `AndroidAutoDuck` (74 lines): `start(AvPlayParameter)` / `stop()`. Called when the active source is Android Auto.

Both classes are trivial — they just enable/disable ducking for that specific source, delegating the real logic to `AudioFocusManager`.

**What this says about the AutoOk v0.4.0 mute bug:** the false tap matched a mute button whose final action was `IAvApService.setMute(true)` — that's raw, total mute, doesn't go through `AudioFocusManager`. So `v0.5.4` fixing the logcat needle patches the bug at the root; messing with ducking wouldn't have solved it.

**Future opportunity (not a current bug):** anyone wanting to bypass ducking on a specific source (e.g. GPS prompt no longer lowering music in CarPlay) has to either (a) intercept `changeDurationFromSourceType` to always return `0x2` (total interrupt) or (b) remove the source from the `PRIORITYTYPE` table. Both are patches on `AV.apk` with the same risk as the Phase 10 patch on `DaLauncher`.

### 5.3 Video path / display group — TX codes

Surprise: `AvApService` also controls **video path**, not just audio (`AvApService` = "**A**udio+**V**ideo **Ap**plication Service").

| TX | 0x | Method |
|----|-----|--------|
| 40 | 0x28 | `openVideoPath(int)` |
| 41 | 0x29 | `closeVideoPath(int)` |
| 44 | 0x2c | `getDisplayParameter(int)` |
| 45 | 0x2d | `setDisplayParameter(...)` |
| 46 | 0x2e | `getDisplayMode()` |
| 70 | 0x46 | `setDisplayMode(...)` |
| 90 | 0x5a | `getBlendMode(int)` |
| 91 | 0x5b | `setBlendMode(...)` |
| 102 | 0x66 | `getDisplayAdjustParameter(int, int, int, int, int)` |
| 103 | 0x67 | `setDisplayAdjustParameter(...)` |
| 125 | 0x7d | `getDisplayPosition()` |
| 126 | 0x7e | `setDisplayPosition(...)` |
| 186 | 0xba | `notifyDisplayData(...)` |

### 5.4 Additional groups — TX codes for the main operations

**Microphones / speakers:**

| TX | 0x | Method |
|----|-----|--------|
| 59 | 0x3b | `getMicMute()` |
| 60 | 0x3c | `setMicMute(...)` |
| 76 | 0x4c | `startMicDiagnosis(...)` |
| 77 | 0x4d | `stopMicDiagnosis(...)` |
| 123 | 0x7b | `execSpeakerCheck(int, int, int, int, int)` |
| 172 | 0xac | `getArrayMicMode()` |
| 173 | 0xad | `setArrayMicMode(...)` |

**Radio** (XM/DAB/HD/Pandora, 23 TX — highlights):

| TX | 0x | Method |
|----|-----|--------|
| 30 | 0x1e | `tune(...)` |
| 100 | 0x64 | `setPandora(...)` |
| 101 | 0x65 | `getPandora()` |
| 120 | 0x78 | `createPandoraStation(int, String)` |
| 121 | 0x79 | `getXmTunerInfo(...)` |
| 131 | 0x83 | `sendItunesTag(...)` |
| 182 | 0xb6 | `deleteItunesTag()` |

**Cover art / metadata:**

| TX | 0x | Method |
|----|-----|--------|
| 36 | 0x24 | `getCurrentPlayTime()` |
| 37 | 0x25 | `getPlayStatus()` |
| 63 | 0x3f | `getCoverArtSettings(int)` |
| 69 | 0x45 | `getCoverArt()` |
| 122 | 0x7a | `getRadioArtwork(...)` |
| 130 | 0x82 | `getArtWork(int, Map)` |
| 188 | 0xbc | `notifyCurrentPlayTime(...)` |

**Environment / system:**

| TX | 0x | Method |
|----|-----|--------|
| 42 | 0x2a | `getBacklightBrightness()` |
| 43 | 0x2b | `setBacklightBrightness(...)` |
| 189 | 0xbd | `getDayNightStatus()` |
| 202 | 0xca | `e911GuidanceCarPlayStatus(int)` |

**Register callbacks** (pattern to receive push events from the service — 26 TX, highlights):

| TX | 0x | Method |
|----|-----|--------|
| 1 | 0x01 | `registerCallback(IAvApServiceCallback)` |
| 2 | 0x02 | `unregisterCallback(IAvApServiceCallback)` |
| 3 | 0x03 | `registerCallbackForExternalDisplay(...)` |
| 124 | 0x7c | `changeHftBandSpeech(int)` |
| 127 | 0x7f | `registerDeviceManagerCallback(...)` |
| 133 | 0x85 | `registerXmCallback(...)` |

**Complete table of the 213 TX** generated by `scratchpad/extract_tx.py` over `IAvApService$Stub.onTransact`. Doesn't fit in full here — if one day all are needed, run the script against the deodexed `.smali`.

### 5.5 Impact for our project

- **AutoOk v0.6.0 (hypothetical)**: `setMute(false)` to undo a false mute is possible, but better is to **gate before the tap**: read `getMute(MAIN)` + `getCurrentSource()` + if `source == CARPLAY && mute == true` → **don't tap**. Eliminates the class of bug "tap at (400,350) hits the mute button in the wrong context" (v0.4.0 §17.15).
- **For our future apps**: you can read `getCurrentSource`/`getCoverArt` to draw a music cluster on top of the secondary cluster (style `alexpotv/Clusters`).
- **Low risk** because it's read-only — the `set*` methods need specific permission (to confirm; likely `android.uid.phone` is required, i.e. privileged apps only).

---

## 6. Video and camera — `VideoManagerApService` (deodex of 2026-10-29)

Service `VideoManagerApService.apk` (`com.mitsubishielectric.ada.appservice.videomanager`), 30 classes. Interface `IVideoManagerApService` has **12 abstract methods** (small, focused service). Permissions: `android.permission.CAMERA`, `android.permission.SYSTEM_ALERT_WINDOW`, `android.permission.INTERNAL_SYSTEM_WINDOW`, `android.permission.STATUS_BAR_SERVICE`, `com.mitsubishielectric.ada.permission.VEHICLE_RW`.

### 6.1 API

```
openVideoPath(...)          closeVideoPath(...)
showVideoAuto(...)          hideVideoAuto(...)
showVideoManual(...)        hideVideoManual(...)
updateVideo(...)            isVideoOn(...)
changeVideoPathToDefault(...)
notifyAppStarted(...)
registVideoStatusListener(IVideoStatusListener)
unregistVideoStatusListener(IVideoStatusListener)
```

The `register*Listener`/`unregister*Listener` pattern + the `show*/hide*` in two variants (`Auto` and `Manual`) suggest the difference is whether the status change came from a hardware trigger (camera engaged, user on the button) or from an app controlling it programmatically.

### 6.2 🎯 Dedicated camera broadcasts — NEW route for Phase 9

**Main finding:** `VideoManagerApService` emits two dedicated broadcasts for camera open/close:

```
com.mitsubishielectric.ada.appservice.videomanager.CAMERA_START
com.mitsubishielectric.ada.appservice.videomanager.CAMERA_FINISH
```

(line 531 of `VideoManagerApService.smali`; `sendBroadcast(Intent)` on line 479 of the same file).

**This opens a much simpler route than the Phase 9 originally planned:**

| Route | Mechanism | Complexity |
|---|---|---|
| Today (AutoOk v0.5.4) | Logcat polling for camera's `am_create_activity` | Medium (polling, line parsing) |
| Original Phase 9 | `bindService` + `transact` on `ICameraAPServiceReverseSignalListener` | High (raw Binder, TX code discovery) |
| **Alternative Phase 9 (via VideoManager)** | `BroadcastReceiver` with filter `CAMERA_START`/`CAMERA_FINISH` | **Minimum (Android standard, 15 lines of code)** |
| Alternative Phase 9 #2 (via VehicleInfoManager) | `BcanListener` + `notifyBcanReceiveSetting(MICU_BCM/ICU)` | Medium (RE Layer 2 §3) |

The `BroadcastReceiver` route is the cleanest. It also works for side and front cameras (the other Activities that appeared in bytecode: `CornerCameraDisplayActivity`, `FrontCameraDisplayActivity`), not just reverse.

### 6.3 Confirmation of ic1101 issue #6

Issue #6 of `librick/ic1101` reported that the commercial `HondaHack` binds on `IVideoManagerApService` (one of the 4 services it uses, together with `IAvApService`, `IVehicleInfoManagerApService`, `ICameraAPService`). Now we know **what HondaHack does with that bind**: probably asks `isVideoOn()` + registers a listener via `registVideoStatusListener` to know when the camera screen opens, so it can overlay its HUD on top.

### 6.4 Impact for our project

- **Phase 9 becomes easy**: our AutoOk's `AndroidManifest.xml` gets a `<receiver>` with `<intent-filter>` for the two actions above; the receiver fires the same path that camera's `am_create_activity` fires today. The AutoOk logcat polling can remain as a fallback.
- **A future "cluster" app of ours** (style `alexpotv/Clusters`) could use `registVideoStatusListener` to know when to pause the overlay if the camera opened.

---

## 7. Next RE steps (still without the car)

- Decide which route to implement in Phase 9 (current logcat polling × `CAMERA_START`/`CAMERA_FINISH` from VideoManager × `MICU_BCM` from VehicleInfoManager × `ICameraAPServiceReverseSignalListener` from CameraAPService) — my recommendation is the 2nd (BroadcastReceiver, simpler).

For native RE (`daupdater`, `.so`): need to first dump the recovery ramdisk and the libraries from `/system/lib` + `/system/vendor/lib` (a new `cp -L`/`dd` OTA). Only then Ghidra.

**Resolved on 2026-10-29:**
- TX codes of `IAvApService` (213/214) mapped from `onTransact` with `scratchpad/extract_tx.py`
- `KeyCommandData` structure + partial table of `convertKeyType` (raw → logical type). Only the `logical type ↔ symbolic name` correlation is missing, which is 1 test in the car
- Deodex of `AvApService` and `VideoManagerApService` (closed §§5-6)

**Resolved on 2026-10-30:**
- Concrete validations of `SystemUpdateApService` (route B of deploy) via deodex of `SystemUpdate.apk` + `SystemUpdateLib.odex` — see §2.1
- Internal `AudioFocusManager` of `AvApService` (real ducking) via deodex of `AV.apk` — see §5.2.1
