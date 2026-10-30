# Scan 6 — Diag APKs (service menus)

**5 diagnostic apps + 1 AIDL backend, from firmware `0040`.** Static analysis on 2026-10-24, from the deodex of the APKs in `tooling/apks-dumped/dump-0040/vendor-app/`.

## The apps

| APK | Role |
|---|---|
| `DealerDiag` | Dealer menu — **91 screens** for diagnostics/testing |
| `DeveloperDiag` | Developer variant |
| `PreShipmentDiag` | Factory pre-shipment diagnostics |
| `LetDiag` | Line End Tester (factory end-of-line test) |
| `DiagApService` | AIDL backend that runs the commands (reads/writes the vehicle via CAN) |
| `DiagServiceLib` (framework) | Shared library for the above |

## Access model — there is no PIN

- The 91 `DealerDiag` Activities are **all `exported="false"`** and the app has **no** permission/UID/SystemProperties/password check whatsoever. Confirmed: `DealerDiagActivity` extends `BaseButtonMenuActivity`, `onCreate` has no gate.
- Access control is purely `exported=false`. "Official" launching happens via the **LET** tool or via trigger files that an `inlinediag` component writes to `/data/data/inlinediag/rcv_dealer_launch` and `/data/data/inlinediag/rcv_let_launch`.
- **Our path (with root):** `su -c "am start -n com.mitsubishielectric.ada.app.dealerdiag/.DealerDiagActivity"` — root bypasses `exported` on Android 4.2. **To be validated in the car.**
- **There is no hardcoded "dealer PIN".** The `KEY_UNLOCK_CODE`/`getUnLockCode` is **Garmin** map licensing (`GARMINUNLOCK`, `GarminUnlock*.csv not found`, `CSVFILE_ITEM_ESN`): it reads the ESN and receives a code to unlock map updates. Not a menu gate.

## How read vs. write was classified

Every screen fires a diagnostic function in `doRequest()` via `getRequestKind()` + `requestDiagService()`. The verb of the `Param*` in that domain (337 classes in `appservice/diag/`) defines the nature:

- **Read:** `Get*`, `*Diagnosis`, `*Check`, `Load*` (reads and displays status/history/version).
- **Write:** `Set*`, `Save*`, `Reset*`, `Clear*`, `Delete*`, `Start*`/`Stop*` (triggers hardware), `*Repro` (reprograms), `*Correction`, `Import/Export`.

> Classification is by static analysis — **to be confirmed in the car**. "Opening" a screen is almost always safe (it just builds UI); the risk is in **interacting** with the write controls.

## 🔴 WRITE / CONFIG — mutates state, use with care

**High risk (may brick / erase):**
- `DisplayReprogram`, `DisplayReprogramConfirmation` → `DisplayStartRepro` (reprograms the display — brick risk)
- `BackupDataCleat` → `DealerClearAll` (erases data)

**Config / persistent calibration (writes a parameter that sticks):**
- `CameraDisplayAdjustment`, `CornerCameraViewAdjustment`, `MonitorAdjustment`, `TouchPanelAdjustment` (`Set*`/`TouchSetCorrection`)
- `TravelOperationLimitSetting` (`RunningLimitSet`/`MileageLimitSet` — vehicle operation limits)
- `EmergencySetting`, `QqCallSetting`, `FunctionalSetup`, `GuidelineSetup`, `GuidelineCameraSelect`, `FacePhotoDisplaySettings`, `DetailInformationAndSetting`
- `DateInput`, `UserInput`, `SaveUsersMemory`

**Sensitive command exposed directly on `DiagApService` (AIDL, no screen):** `factoryResetSettings` (`TRANSACTION_factoryResetSettings`).

## 🟡 HARDWARE/MEDIA TEST — opening is OK; controls actually drive the hardware

- **Audio/radio/media:** `AirConditioner`, `Amp`, `AudioCheck`, `SpeakerCheck`, `HftMic`, `Cd`, `Dvd`, `Dtv`, `AuxVideo`, `Xm`, `Sxm`, `HdRadioFunction`, `HdTraffic`, `RemoteTuner`, `FmVics`, `PandoraFunction` (test `Start*`/`Play*`/`Set*`)
- **Projection:** `AndroidAuto`, `MirrorLink`, `AppMode`
- **Cameras:** `CornerCamera`, `CornerCameraView`, `FrontCamera`, `RearWideCamera`, `Mvc`, `LaneWatch`
- **Display patterns (harmless, display-only):** `BlackRaster`, `WhileRaster`, `ColorPattern`, `GrayTone`, `RgbColor`, `CenterDisplay`
- **Input/test diag:** `HardKey`, `TouchPanelDiagnosis`, `Beacon`, `Etc`, `TcuTest`, `RtDiag`, `RtDiagnosis`, `LogData`, `Other`

## 🟢 READ-ONLY — query, safe to open and use

- **Info/status:** `CarStatus`, `Version`, `GpsInformation`, `GpsAntenna`, `TcuStatus`, `TcuDtcs`, `TcuLog`, `TcuTelInfo`, `TrafficInformation`, `UsbMemoryDetailInformation`, `EtcDetail`, `SystemLinks`, `SystemLinksHelp`, `AppModeConnectionSequenceInformation`, `AppModeDetailInformation`, `MirrorLinkConnectionSequenceInformation`, `MirrorLinkDetailInformation`, `LaneWatchDetailInformation`
- **Errors/history:** `ErrorHistory`, `HardError`, `SoftError`, `PowerFluctuationHistory`, `ReceptionHistory`, `ReceptionHistoryDetail`, `ReportHistory`
- **Checks/sensors (read):** `MonitorCheck`, `UnitCheck`, `HmiUnit` (DRAM/Flash), `YawRate`, `YawSensor`, `BCan`, `FCan` (`CanDataGet*` — read the bus)

`DealerDiagActivity` is the root menu (navigation, neutral).

## Next steps

- **Validate in the car:** does `su -c "am start -n ...dealerdiag/.DealerDiagActivity"` open the menu? And a read screen (e.g. `CarStatus`, `Version`)?
- Confirm the ambiguous verdicts (`BCan`/`FCan`, `LogData`, `SaveUsersMemory`) by opening and observing.
- **Do not** trigger `DisplayReprogram` or `BackupDataCleat`/`factoryResetSettings` without a prepared rollback.

## Cross-references

- [`01-apis-aidl.md`](../../raio-x/01-apis-aidl.md) (Portuguese) — AIDL contracts (includes `appservice.diag`)
- [`05-trust-map.md`](../../raio-x/05-trust-map.md) (Portuguese) — diagnostic apps permissions
- `tooling/apks-decoded/DealerDiag-deodexed.apk` (+ other `*-deodexed.apk`) — local smali
