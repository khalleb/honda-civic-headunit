# Scan 1 — AIDL APIs (binder interfaces)

**364 unique interfaces across 63 domains.** This is the IPC contract list of the shipping firmware `0040`. Any app with the right UID can `bindService` + `IFoo.Stub.asInterface(binder)` to consume them.

## How it was collected

```
grep -rl 'Landroid/os/IInterface' bulk-smali/
  | filtra arquivos cujo basename começa com I*.smali e não é $Stub|$Proxy
```

**Binder-interface identification pattern in smali:**
```
.class public interface abstract L.../IFoo;
.super Ljava/lang/Object;
...
.implements Landroid/os/IInterface;
```

Dedupe by fully-qualified name (the same interfaces show up in APK↔Lib pairs because vendor libs are referenced via `<uses-library>`).

## Highlights — what the inventory reveals

### `appservice.vehicleinfomanager` (37 interfaces) 🎯 biggest surface

Central vehicle mediator. The listener names make clear what it can deliver:

| Interface | Inferred meaning |
|---|---|
| `IVehicleGearInformationListener` | Current gear (**useful for reverse without logcat polling**) |
| `IVehicleShiftPositionListener` + `IVehicleShiftParkPositionListener` | Shift lever position |
| `IVehicleIgnitionStatusListener` + `IVehicleIGInformationListener` + `IVehicleIGVoltageInformationListener` | Ignition state and voltage |
| `IVehicleBatteryAndVspPulseInformationListener` | Battery + speed pulse |
| `IVehicleVspPulseInformationListener` + `IVehiclePassThresholdSpeedInformationListener` | Speed and threshold-triggered events |
| `IVehicleSteeringAngleListener` | Steering wheel angle |
| `IVehicleParkSensInformationListener` + `IVehicleParkSens2InformationListener` + `IVehicleParkingInformationListener` + `IVehicleBcanParkingBrakeListener` | Parking sensors (front, rear, parking brake) |
| `IVehicleFOBKeyNumberInformationListener` | Which FOB key was used (per-driver profile!) |
| `IVehicleVinCodeInformationListener` + `IVehicleVinNoInformationListener` | Vehicle VIN |
| `IVehicleMaintenanceInformationListener` + `IVehicleMicuBcmInformationListener` | Maintenance diagnostics, BCM |
| `IVehicleFcanInformationListener` + `IVehicleBcanInformationListener` | Raw F-CAN and B-CAN bus |

Main service: `IVehicleInfoManagerApService`. **All car telemetry flows through here.**

### `framework.vehicledbmanager` (18 interfaces) — versioned vehicle-data DB

One `IVehicleDbManagerX` per consumer domain: `IVehicleDbManagerCamera`, `IVehicleDbManagerAv`, `IVehicleDbManagerDiag`, `IVehicleDbManagerEmergency`, `IVehicleDbManagerHft`, `IVehicleDbManagerNavigation`, `IVehicleDbManagerTelematics`, `IVehicleDbManagerVoicePortal`, `IVehicleDbManagerWifi`, `IVehicleDbManagerVehicleInfoManager`, `IVehicleDbManagerVehicleCoordination`, etc.

Classic "feature-sliced DB access" pattern — each consumer gets its own façade.

### `framework.cpucomservice` (20 interfaces) — CPU↔CPU mediator

The head unit has **two separate processors** (ADS for infotainment + another for vehicle functions). `ICpuComService` is the channel. The 20 listeners are **one per appservice**, mirroring the remote state:
`IAcuraLinkApServiceListener`, `IAvApServiceListener`, `ICameraApServiceListener`, `IDiagApServiceListener`, `IEmergencyApServiceListener`, `IExternalDisplayApServiceListener`, `IHudApServiceListener`, `INavigationApServiceListener`, `IPhoneApServiceListener`, `IPhoneCoordinationApServiceListener`, `IPowerManagerApServiceListener`, `IRaspApServiceListener`, `IRoadToVehicleApServiceListener`, `IStrgSwApServiceListener`, `ISystemUpdateApServiceListener`, `IUnitInfoManagerApServiceListener`, `IVehicleCoordinationApServiceListener`, `IVehicleInfoManagerApServiceListener`, `IErrorApServiceListener`, `IRaspApServiceListener`.

### `appservice.camera` (21 interfaces) 🎯 Phase 9 target

- `ICameraAPService` (main service)
- `ICameraAPServiceReverseSignalListener` ⭐ — **this is the dedicated receiver for reverse gear**
- `ICameraAPServiceChangeViewModeListener` — view-mode change (front/rear/lanewatch/mvc)
- `ICameraAPServiceDrivingStatusListener` + `ICameraAPServiceDrivingOperationStatusListener`
- `ICameraAPServiceIgOnStateListener` — ignition on
- `ICameraAPServiceLaneWatchListener` + `ICameraAPServicLaneWatchComunicateListener`
- `ICameraAPServiceMvcCameraStatusListener` + `ICameraAPServiceMvc*` (Multi-View Camera)
- `IBsiCtmListener` + `ICameraAPServiceBsiCtmListener` (Blind Spot Info?)
- `IParkingSensorListener` (possibly also available here)
- `IUpdateGuidelineListener` (reverse-camera guideline overlay)
- `ITransparentRequestListener` (UI transparency?)

**Confirmed opportunity:** `ICameraAPServiceReverseSignalListener` would make the AutoOk v0.5.0 reverse flow trivial (bind the service + register listener → receive a direct callback when the gear flips to reverse). No logcat polling.

### `appservice.strgsw` (10 interfaces) — car steering wheel

- `IStrgSwApService` + 8 listeners covering events: `IStrgSwEventApServiceListener`, `IStrgSwEventPriorityApServiceListener`, `IStrgSwEventLogApServiceListener`, `IStrgSwMotionMenuApServiceListener`, `IStrgSwRaspEventApServiceListener`, `IStrgSwRotaryKeyEventApServiceListener`, `IStrgSwStatusApServiceListener`, `IStrgSwCenterVolXYApServiceListener`.
- `IStrgSwBcanInformationListener` — raw B-CAN data related to the steering wheel.

**The physical steering-wheel button map lives here.** Low cost to hook custom shortcuts in one of our APKs.

### `appservice.hft` (13) — hands-free telephony

Main interface + listeners for `Call`, `Data`, `Grammar`, `Mail`, `Phone`, `SmartPhoneLink`, `SupportedState`, `VoiceTag`, `VoiceTagRecord`, `VrCallHistory`, `VrStatus`.

### `app.systeminfoservice` (18) — system telops and overlays

Everything about **telops** (floating notifications), **InfoTopScreen/InfoMenuScreen** (information screens) and **DisplayOffScreen** (screen off but the system active). `ISystemDisplayApService` is the service, with callbacks split by capability. Worth looking at whether it opens a path to suppress other warnings without the logcat+tap loop.

### `appservice.diag` (3) + 2 more in `app.systeminfoservice`

- `IDiagPublicService` — maybe a public interface (queryable with no special permission)
- `IDiagService` — internal
- `IDiagServiceListner` [sic, typo "Listner" in the original]

Entry points to explore dealer/developer menus. May contain PINs, versions, diagnostic dumps.

### Capabilities we weren't expecting

| Interface | What it probably does |
|---|---|
| `avapservice.voiceportal/IMusicSearchListener` + `IMusicBundleSearchListener` | Voice-driven music search on USB/BT |
| `appservice.vehiclecoordination/ISolarAngleCallback` | Sun angle — used to adjust brightness? |
| `appservice.vehiclecoordination/IFuelConsumptionCanDataCallback` | Real-time fuel-consumption data from CAN |
| `appservice.unitinfomanager/IGetMainBoardTemperatureListener` | Mainboard temperature |
| `appservice.unitinfomanager/IColorVariationChangedListener` + `IMeterColorVariationChangedListener` | Dashboard color variation (visual profile?) |
| `appservice.unitinfomanager/IWallPaperInformationListener` | Dynamic wallpaper? |
| `appservice.unitinfomanager/IVehicleRunOperationControlFlagListener` | **Flag that controls regulation while driving** — may be the knob that blocks inputs in motion |
| `system.beacon/IBCNTspsControl` | Beacon TSPS (something related to a smart traffic light?) |
| `system.dsrc/IDSRCControl` | DSRC (Dedicated Short-Range Comms, V2V/V2I) |
| `system.applicationinfo/IApplicationInfoService` | Catalog of known apps |

## Full list (364 interfaces, 63 domains)

> Grouped by domain (`<path>.<last>.<second-to-last>` of the FQDN).

### `appservice.vehicleinfomanager` (37 interfaces)

- `IVehicleAntiTheftInformationListener`
- `IVehicleAntiTheftValidateListener`
- `IVehicleAtSerialCodeInformationListener`
- `IVehicleBackupClearInformationListener`
- `IVehicleBatteryAndVspPulseInformationListener`
- `IVehicleBcanInformationListener`
- `IVehicleBcanParkingBrakeListener`
- `IVehicleCanInformationForAvApServiceListener`
- `IVehicleCanInformationForCameraApServiceListener`
- `IVehicleDrivingOperationStatusListener`
- `IVehicleFOBKeyNumberInformationListener`
- `IVehicleFcanInformationListener`
- `IVehicleGearInformationListener`
- `IVehicleHDSConnectInformationListener`
- `IVehicleIGInformationListener`
- `IVehicleIGVoltageInformationListener`
- `IVehicleIgnitionStatusListener`
- `IVehicleInfoManagerApService`
- `IVehicleLetDiagInformationListener`
- `IVehicleMaintenanceInformationListener`
- `IVehicleMetCustomInformationListener`
- `IVehicleMeterIllStatusInformationListener`
- `IVehicleMicuBcmInformationListener`
- `IVehicleParkSens2InformationListener`
- `IVehicleParkSensInformationListener`
- `IVehicleParkingInformationListener`
- `IVehiclePassThresholdSpeedInformationListener`
- `IVehicleShiftParkPositionListener`
- `IVehicleShiftPositionListener`
- `IVehicleSpecificBcanStatusListener`
- `IVehicleSpecificFcanStatusListener`
- `IVehicleSteeringAngleListener`
- `IVehicleVehicleCustomizeInformationListener`
- `IVehicleVinCodeInformationListener`
- `IVehicleVinNoInformationListener`
- `IVehicleVspPulseInformationListener`
- `IVehicleWelcomeStateListener`

### `appservice.navigation` (25 interfaces)

- `IAddNewFavoriteListener`
- `IBCanTBTInfoListener`
- `IDeleteRouteListener`
- `IDestinationEntryStatusListener`
- `IDestinationHistoryListener`
- `IDriveRangeCallbackListener`
- `IFavoriteListListener`
- `IFmInfoListener`
- `IGoHomeListener`
- `IIconStatusListener`
- `IMapUpdateListener`
- `IMapVersionInfoListener`
- `IMarkerListener`
- `IMinimapImageListener`
- `INavigationApService`
- `INavigationNaviInfoListener`
- `INavigationNaviInfoNmeaListener`
- `INearbySearchListener`
- `IPoixInfoListener`
- `IRadioAreaPresetInfoCallbackListener`
- `IRoutePreferenceChangeListener`
- `ISetRouteInfoListener`
- `ISetRouteListener`
- `ITBTInfoListener`
- `ITrafficProviderInfoListener`

### `appservice.camera` (21 interfaces)

- `IBsiCtmListener`
- `ICameraAPServicLaneWatchComunicateListener`
- `ICameraAPService`
- `ICameraAPServiceBindCompleteListener`
- `ICameraAPServiceBsiCtmListener`
- `ICameraAPServiceChangeViewModeListener`
- `ICameraAPServiceCommonListener`
- `ICameraAPServiceDrivingOperationStatusListener`
- `ICameraAPServiceDrivingStatusListener`
- `ICameraAPServiceIgOnStateListener`
- `ICameraAPServiceLaneWatchListener`
- `ICameraAPServiceMvcCameraStatusListener`
- `ICameraAPServiceMvcComunicateListener`
- `ICameraAPServiceMvcListener`
- `ICameraAPServiceReverseSignalListener`
- `ICameraAPServiceSetViewModeResultListener`
- `ICameraErrorListener`
- `ICtmListener`
- `IParkingSensorListener`
- `ITransparentRequestListener`
- `IUpdateGuidelineListener`

### `framework.cpucomservice` (20 interfaces)

- `IAcuraLinkApServiceListener`
- `IAvApServiceListener`
- `ICameraApServiceListener`
- `ICpuComService`
- `IDiagApServiceListener`
- `IEmergencyApServiceListener`
- `IErrorApServiceListener`
- `IExternalDisplayApServiceListener`
- `IHudApServiceListener`
- `INavigationApServiceListener`
- `IPhoneApServiceListener`
- `IPhoneCoordinationApServiceListener`
- `IPowerManagerApServiceListener`
- `IRaspApServiceListener`
- `IRoadToVehicleApServiceListener`
- `IStrgSwApServiceListener`
- `ISystemUpdateApServiceListener`
- `IUnitInfoManagerApServiceListener`
- `IVehicleCoordinationApServiceListener`
- `IVehicleInfoManagerApServiceListener`

### `app.systeminfoservice` (18 interfaces)

- `IChangeSourceCallback`
- `IDismissDisplayOffScreenResultCallback`
- `IDismissTelopInterruptCallback`
- `IDisplayOffScreenStatusCallback`
- `IDisplayOffScreenTouchCallback`
- `IInfoMenuScreenCallback`
- `IInfoTopScreenCallback`
- `IJudgeShowTelopCallback`
- `IShowTelopResultCallback`
- `ISystemDisplayApService`
- `ISystemDisplayApServiceAnyScreenCallback`
- `ISystemDisplayApServiceBrightnessBarCallback`
- `ISystemDisplayApServiceCallback`
- `ISystemDisplayApServiceDisplayOffScreenCallback`
- `ITelopNotifyCallback`
- `ITelopStatusCallback`
- `InfoMenuScreen`
- `InfoTopScreen`

### `appservice.unitinfomanager` (18 interfaces)

- `IAudioFunctionAddressManagerApServiceListener`
- `IColorVariationChangedListener`
- `IExternalAmpKindManagerApServiceListener`
- `IExternalDeviceManagerApServiceListener`
- `IGetAudioSettingFileVersionListener`
- `IGetInspectedSpeakersListener`
- `IGetLetModelListener`
- `IGetMainBoardTemperatureListener`
- `IMeterColorVariationChangedListener`
- `IUSBDeviceErrorStatusListener`
- `IUnitInformationListener`
- `IUnitInformationManagerApService`
- `IUsbDeviceManagerApServiceListener`
- `IUsbStatusListener`
- `IVehicleModelSettingCompleteListener`
- `IVehicleModelSettingPreCompleteListener`
- `IVehicleRunOperationControlFlagListener`
- `IWallPaperInformationListener`

### `framework.vehicledbmanager` (18 interfaces)

- `IVehicleDbManagerAv`
- `IVehicleDbManagerCamera`
- `IVehicleDbManagerCompass`
- `IVehicleDbManagerDiag`
- `IVehicleDbManagerEmergency`
- `IVehicleDbManagerErrorManager`
- `IVehicleDbManagerExternalDisplay`
- `IVehicleDbManagerHft`
- `IVehicleDbManagerMirrorLink`
- `IVehicleDbManagerNavigation`
- `IVehicleDbManagerPhoneCoordination`
- `IVehicleDbManagerRoadToVehicle`
- `IVehicleDbManagerTelematics`
- `IVehicleDbManagerUnit`
- `IVehicleDbManagerVehicleCoordination`
- `IVehicleDbManagerVehicleInfoManager`
- `IVehicleDbManagerVoicePortal`
- `IVehicleDbManagerWifi`

### `appservice.avapservice` (14 interfaces)

- `IAvApService`
- `IAvApServiceCallback`
- `IAvApServiceCallbackForAppMode`
- `IAvApServiceCallbackForCarPlay`
- `IAvApServiceCallbackForDiag`
- `IAvApServiceCallbackForErrorInfo`
- `IAvApServiceCallbackForErrorList`
- `IAvApServiceCallbackForExternalDisplay`
- `IAvApServiceCallbackForRasp`
- `IDeviceManagerCallback`
- `ITiltDisplayCallback`
- `IVideoFuncCallback`
- `IXMPhoneticsCallback`
- `IXmCallback`

### `appservice.phonecoordination` (14 interfaces)

- `IGpsTimeCommunicationInfoListener`
- `ILinkingPhoneAppsConfigurationUpdateListener`
- `IPhoneCoordinationAndroidAutoListener`
- `IPhoneCoordinationApService`
- `IPhoneCoordinationAppModeListener`
- `IPhoneCoordinationApplicationListener`
- `IPhoneCoordinationAvListener`
- `IPhoneCoordinationCarPlayListener`
- `IPhoneCoordinationClockSyncListener`
- `IPhoneCoordinationCrmDiagProgressStateListener`
- `IPhoneCoordinationFCanInformationForDiagListener`
- `IPhoneCoordinationFCanInformationForEmergencyListener`
- `IPhoneCoordinationHomeApplicationListener`
- `IUserLogManager`

### `appservice.hft` (13 interfaces)

- `IHftApService`
- `IHftApplicationListener`
- `IHftCallListener`
- `IHftDataListener`
- `IHftGrammarListener`
- `IHftMailListener`
- `IHftPhoneListener`
- `IHftSmartPhoneLinkListener`
- `IHftSupportedStateListener`
- `IHftVoiceTagListener`
- `IHftVoiceTagRecordListener`
- `IHftVrCallHistoryListener`
- `IHftVrStatusListener`

### `appservice.vehiclecoordination` (12 interfaces)

- `IAirConditionerClimateCallback`
- `IAirConditionerDisplayDataCallback`
- `IAirConditionerErrorInfoCallback`
- `IAirConditionerManager`
- `IAirConditionerSensorDataCallback`
- `IAirConditionerStatusCallback`
- `IAirConditionerUserCustomCallback`
- `IEcoAndTripInformationManager`
- `IFuelConsumptionCanDataCallback`
- `ISolarAngleCallback`
- `IVehicleCoordinationBcanStateCallback`
- `IVehicleCoordinationFcanStateCallback`

### `appservice.acuralink` (11 interfaces)

- `IAcuraLinkApService`
- `IAcuraLinkNotifyHfpStateListener`
- `IAcuraLinkPoiInformationListener`
- `IAcuraLinkStateListener`
- `IAcuraLinkTcuConnectionListener`
- `IAcuraLinkTcuDiagnosticInformationListener`
- `IAcuraLinkTcuReflashStateListener`
- `IAcuraLinkTcuSignalStrengthListener`
- `IAcuraLinkUsbConnectionListener`
- `IAcuraLinkVehicleLocationListener`
- `IAcuraLinkVinCodeInformationListener`

### `appservice.carplayapservice` (10 interfaces)

- `ICarPlayApService`
- `ICarPlayApServiceCallback`
- `ICarPlayApServiceCallbackForCarPlayApp`
- `ICarPlayApServiceCallbackForEmergency`
- `ICarPlayApServiceCallbackForHftApp`
- `ICarPlayApServiceCallbackForNavi`
- `ICarPlayApServiceCallbackForPhone`
- `ICarPlayApServiceCallbackForPhoneCoordination`
- `ICarPlayApServiceSiriCallback`
- `ICarPlayApServiceTelCallback`

### `appservice.strgsw` (10 interfaces)

- `IStrgSwApService`
- `IStrgSwBcanInformationListener`
- `IStrgSwCenterVolXYApServiceListener`
- `IStrgSwEventApServiceListener`
- `IStrgSwEventLogApServiceListener`
- `IStrgSwEventPriorityApServiceListener`
- `IStrgSwMotionMenuApServiceListener`
- `IStrgSwRaspEventApServiceListener`
- `IStrgSwRotaryKeyEventApServiceListener`
- `IStrgSwStatusApServiceListener`

### `appservice.emergency` (9 interfaces)

- `IEmergencyApService`
- `IEmergencyDeviceDetectListener`
- `IEmergencyE911TestInfoListener`
- `IEmergencyFcanInfomationListener`
- `IEmergencyNotifyGuidanceStateListener`
- `IEmergencyNotifyHfpStateListener`
- `IEmergencyStateListener`
- `IEmergencyStateListenerForEmg`
- `IEmergencyVehicleLocationListener`

### `appservice.appmanagerservice` (6)
`IAppManagerService` · `IApplicationInfoListener` · `IAutomotiveActivityHub` · `IDisplayInfoListener` · `IDisplayObjectListener` · `IFrameworkObserver`

### `system.traffic` (6)
`IFMMControl` · `IFMMControlCallback` · `IHdTrafficCallBacks` · `IHdTrafficService` · `IRDSTMCCallBacks` · `IRDSTMCService`

### `app.androidauto` (5)
`IAndroidAutoControl` · `IAndroidAutoControlCallback` · `IAndroidAutoService` · `IAndroidAutoServiceListener` · `ILogMonitorService`

### `appservice.appmodeapservice` (5)
`IAppModeApService` · `IAppModeApServiceCallBackForDiag` · `IAppModeApServiceCallback` · `IAppModeApServiceCallbackForPhoneCoordination` · `IAppModeApServiceCallbackSoftKeyboardStatusEvent`

### `appservice.voiceportalap` (5)
`IVoicePortalApService` · `IVoicePortalMeterCallback` · `IVoicePortalPrepareListener` · `IVoicePortalSpeechListener` · `IVoicePortalStrgSwCallback`

### `avapservice.voiceportal` (5)
`IAvVoicePortalService` · `IDictionaryStateCallback` · `IMusicBundleSearchListener` · `IMusicSearchListener` · `IPhoneticModificationCallback`

### `framework.mcservice` (5)
`IMediaCoreAppModeListener` · `IMediaCoreLinkManagerListener` · `IMediaCoreLpaListener` · `IMediaCoreService` · `IMediaCoreServiceListener`

### `framework.speech` (5)
`IAsrConfigService` · `IG2pService` · `IVoiceTagManagerService` · `IVrsdConfigService` · `IVrsdVoiceTagManagerService`

### `appservice.externaldisplay` (4)
`IContentsCustomizeListener` · `IExternalDisplayApService` · `IExternalDisplayApServiceDiagListener` · `IExternalDisplayEventApServiceListener`

### `appservice.telematics` (4)
`IDialupTelematicsApServiceListener` · `IProvisioningHmilogTelematicsApServiceListener` · `IProvisioningTelematicsApServiceListener` · `ITelematicsApService`

### `system.beacon` (4)
`IBCNControl` · `IBCNControlCallBack` · `IBCNTspsControl` · `IBCNTspsControlCallback`

### Domains with 3 or fewer interfaces

- `app.systemupdate` (3): `ISystemUpdateApService`, `ISystemUpdateApServiceCallback`, `IUnitInfoManagerApServiceCallback`
- `appservice.diag` (3): `IDiagPublicService`, `IDiagService`, `IDiagServiceListner` [sic]
- `appservice.raspapservice` (3): `IRaspApService`, `IRaspApServiceCallbackForRaspKeyLock`, `IRaspEventApServiceListener`
- `appservice.roadtovehicle` (3): `IIBCNControlListener`, `IRoadToVehicleApService`, `IRoadToVehicleListener`
- `mirrorlink.service` (3): `IMirrorLinkService`, `IMirrorLinkServiceCallBackForDiag`, `IMirrorLinkServiceConnectStatusListener`
- `system.naviinfo` (3): `INaviInfoListener`, `INaviInfoProvider`, `INaviInfoSupplier`
- `android.phone` (2): `INetworkQueryService`, `INetworkQueryServiceCallback`
- `appservice.errormanager` (2): `IErrorDisplayTempAlertListener`, `IErrorManagerApService`
- `appservice.hudapservice` (2): `IHudApService`, `IHudEventApServiceListener`
- `appservice.videomanager` (2): `IVideoManagerApService`, `IVideoStatusListener`
- `displayaudio.navi` (2): `IRadioAreaPresetInfo`, `IRadioAreaPresetInfoCallback`
- `link.iap` (2): `ILinkManagerIAPAdapter`, `ILinkManagerIAPListner` [sic]
- `system.applicationinfo` (2): `IApplicationInfoCallBacks`, `IApplicationInfoService`
- `system.dsrc` (2): `IDSRCControl`, `IDSRCControlCallback`
- `system.meter` (2): `ITBTInformation`, `ITBTInformationCallback`
- `system.speech` (2): `IVRStatus`, `IVRStatusCallback`
- `system.vehicleinfo` (2): `IVehicleInfoCallBacks`, `IVehicleInfoService`
- `android.music` (1): `IMediaPlaybackService`
- `appservice.clocksync` (1): `IClockSyncService`
- `appservice.compassservice` (1): `ICompassApService`
- `appservice.powermanager` (1): `IPowerManagerApService`
- `appservice.screenshot` (1): `IScreenshotApService`
- `appservice.sensormonitor` (1): `ISensorMoniterApService` [sic, Moniter]
- `appservice.whitelist` (1): `IWhitelistApService`
- `appservice.wifi` (1): `IWifiApService`
- `inputmethod.pinyin` (1): `IPinyinDecoderService`
- `net.link` (1): `ILinkManager`
- `providers.media` (1): `IMtpService`
- `system.driveinfo` (1): `IDriveInfoService`
- `system.hmilog` (1): `IHmiLogInformation`
- `system.modelinfo` (1): `IModelInfo`
- `system.telemainfo` (1): `ITelemaInfoService`
- `traffic.hd` (1): `IHdTrafficListener`
- `traffic.rds` (1): `IRDSTMCListener`
- `voiceportal.preload` (1): `IVoicePortalPreLoadService`
- `wifi.core` (1): `IWifiStateListner` [sic, Listner]
- `wifi.test` (1): `IWifiTestListner` [sic, Listner]

## Methodological notes

- **"Listner" is a recurring spelling in the shipping firmware** (e.g. `IWifiStateListner`, `IDiagServiceListner`, `ILinkManagerIAPListner`). It is not our transcription error — it is in the code.
- The `android.music` domain comes from `IMediaPlaybackService`, which is standard AOSP; not vendor-specific.
- `com.mitsubishielectric.ada.framework.*` are **frameworks** (consumed via `<uses-library>`), not installable APKs. `com.mitsubishielectric.ada.appservice.*` are **services** with a dual APK + lib layout.
- `app.systeminfoservice` has an unusual path (`app`, not `appservice`) but is internally a service — a shipping-firmware exception.

## Suggested next steps (not in scope here)

To turn each entry into something actionable, the standard sequence is:

1. **Deodex the APK** that implements it (see `tooling/deodex/deodex-apk.sh`).
2. **Decompile** the interface itself (`inspect-android-class` via REA) — gives the method list and signatures.
3. **Decompile** the `.Stub.onTransact` — gives the TRANSACTION_* codes.
4. **Test** with one of our privileged apps (or via `service call <name> <code>` in the shell with su).

For **ICameraAPServiceReverseSignalListener**, for example, this would be the path to open Phase 9 (reverse without logcat).
