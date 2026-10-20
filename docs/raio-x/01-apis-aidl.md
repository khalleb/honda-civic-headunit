# Scan 1 — APIs AIDL (Binder interfaces)

**364 interfaces únicas em 63 domínios.** Esta é a lista de contratos IPC do shipping da safra `0040`. Qualquer app com UID adequado pode fazer `bindService` + `IFoo.Stub.asInterface(binder)` para consumir.

## Como foi coletado

```
grep -rl 'Landroid/os/IInterface' bulk-smali/
  | filtra arquivos cujo basename começa com I*.smali e não é $Stub|$Proxy
```

**Pattern de identificação de interface binder em smali:**
```
.class public interface abstract L.../IFoo;
.super Ljava/lang/Object;
...
.implements Landroid/os/IInterface;
```

Dedupe por nome fully-qualified (as mesmas interfaces aparecem em pares APK↔Lib porque libs vendor são referenciadas via `<uses-library>`).

## Highlights — o que o inventário revela

### `appservice.vehicleinfomanager` (37 interfaces) 🎯 maior superfície

Mediator central do veículo. Nome dos listeners deixa claro o que ele pode entregar:

| Interface | Significado inferido |
|---|---|
| `IVehicleGearInformationListener` | Marcha atual (**útil pra ré sem logcat polling**) |
| `IVehicleShiftPositionListener` + `IVehicleShiftParkPositionListener` | Posição da alavanca |
| `IVehicleIgnitionStatusListener` + `IVehicleIGInformationListener` + `IVehicleIGVoltageInformationListener` | Estado da ignição e voltagem |
| `IVehicleBatteryAndVspPulseInformationListener` | Bateria + pulso de velocidade |
| `IVehicleVspPulseInformationListener` + `IVehiclePassThresholdSpeedInformationListener` | Velocidade e trigger por limite |
| `IVehicleSteeringAngleListener` | Ângulo do volante |
| `IVehicleParkSensInformationListener` + `IVehicleParkSens2InformationListener` + `IVehicleParkingInformationListener` + `IVehicleBcanParkingBrakeListener` | Sensores de estacionamento (frontais, traseiros, freio de mão) |
| `IVehicleFOBKeyNumberInformationListener` | Qual chave FOB foi usada (perfil por motorista!) |
| `IVehicleVinCodeInformationListener` + `IVehicleVinNoInformationListener` | VIN do carro |
| `IVehicleMaintenanceInformationListener` + `IVehicleMicuBcmInformationListener` | Diagnóstico de manutenção, BCM |
| `IVehicleFcanInformationListener` + `IVehicleBcanInformationListener` | Barramento F-CAN e B-CAN raw |

Service principal: `IVehicleInfoManagerApService`. **Toda a telemetria do carro passa por aqui.**

### `framework.vehicledbmanager` (18 interfaces) — DB versioned de dados do veículo

Uma `IVehicleDbManagerX` por domínio consumidor: `IVehicleDbManagerCamera`, `IVehicleDbManagerAv`, `IVehicleDbManagerDiag`, `IVehicleDbManagerEmergency`, `IVehicleDbManagerHft`, `IVehicleDbManagerNavigation`, `IVehicleDbManagerTelematics`, `IVehicleDbManagerVoicePortal`, `IVehicleDbManagerWifi`, `IVehicleDbManagerVehicleInfoManager`, `IVehicleDbManagerVehicleCoordination`, etc.

Padrão clássico de "feature-sliced DB access" — cada consumidor tem a sua façade.

### `framework.cpucomservice` (20 interfaces) — mediator CPU↔CPU

A central tem **dois processadores** separados (ADS para infotainment + outro para funções do veículo). O `ICpuComService` é o canal. Os 20 listeners são **um por appservice** espelhando o estado remoto:
`IAcuraLinkApServiceListener`, `IAvApServiceListener`, `ICameraApServiceListener`, `IDiagApServiceListener`, `IEmergencyApServiceListener`, `IExternalDisplayApServiceListener`, `IHudApServiceListener`, `INavigationApServiceListener`, `IPhoneApServiceListener`, `IPhoneCoordinationApServiceListener`, `IPowerManagerApServiceListener`, `IRaspApServiceListener`, `IRoadToVehicleApServiceListener`, `IStrgSwApServiceListener`, `ISystemUpdateApServiceListener`, `IUnitInfoManagerApServiceListener`, `IVehicleCoordinationApServiceListener`, `IVehicleInfoManagerApServiceListener`, `IErrorApServiceListener`, `IRaspApServiceListener`.

### `appservice.camera` (21 interfaces) 🎯 alvo da Fase 9

- `ICameraAPService` (service principal)
- `ICameraAPServiceReverseSignalListener` ⭐ — **esse é o receiver dedicado da ré**
- `ICameraAPServiceChangeViewModeListener` — mudança de modo (front/rear/lanewatch/mvc)
- `ICameraAPServiceDrivingStatusListener` + `ICameraAPServiceDrivingOperationStatusListener`
- `ICameraAPServiceIgOnStateListener` — ignição on
- `ICameraAPServiceLaneWatchListener` + `ICameraAPServicLaneWatchComunicateListener`
- `ICameraAPServiceMvcCameraStatusListener` + `ICameraAPServiceMvc*` (Multi-View Camera)
- `IBsiCtmListener` + `ICameraAPServiceBsiCtmListener` (Blind Spot Info?)
- `IParkingSensorListener` (talvez disponível aqui também)
- `IUpdateGuidelineListener` (overlay das linhas-guia da ré)
- `ITransparentRequestListener` (transparência da UI?)

**Oportunidade confirmada:** `ICameraAPServiceReverseSignalListener` tornaria o fluxo de ré do AutoOk v0.5.0 trivial (bind no service + registra listener → recebe callback direto quando a marcha vira ré). Sem logcat polling.

### `appservice.strgsw` (10 interfaces) — volante do carro

- `IStrgSwApService` + 8 listeners cobrindo eventos: `IStrgSwEventApServiceListener`, `IStrgSwEventPriorityApServiceListener`, `IStrgSwEventLogApServiceListener`, `IStrgSwMotionMenuApServiceListener`, `IStrgSwRaspEventApServiceListener`, `IStrgSwRotaryKeyEventApServiceListener`, `IStrgSwStatusApServiceListener`, `IStrgSwCenterVolXYApServiceListener`.
- `IStrgSwBcanInformationListener` — dados brutos do B-CAN relacionados ao volante.

**Mapa dos botões físicos do volante vive aqui.** Baixo custo pra hookar atalhos personalizados num APK nosso.

### `appservice.hft` (13) — hands-free telephony

Interface principal + listeners para `Call`, `Data`, `Grammar`, `Mail`, `Phone`, `SmartPhoneLink`, `SupportedState`, `VoiceTag`, `VoiceTagRecord`, `VrCallHistory`, `VrStatus`.

### `app.systeminfoservice` (18) — telops e overlays do sistema

Toda a parte de **telops** (notificações flutuantes), **InfoTopScreen/InfoMenuScreen** (telas de informação) e **DisplayOffScreen** (tela desligada mas o sistema ativo). O `ISystemDisplayApService` é o service, callbacks separados por capability. Vale olhar se abre caminho pra suprimir outros avisos sem o loop logcat+tap.

### `appservice.diag` (3) + mais 2 em `app.systeminfoservice`

- `IDiagPublicService` — talvez interface pública (consultável sem permissão especial)
- `IDiagService` — interno
- `IDiagServiceListner` [sic, typo "Listner" no original]

Pontos de entrada para explorar menus de dealer/developer. Pode conter PINs, versões, dumps diagnósticos.

### Capacidades que não imaginávamos

| Interface | Especula o quê |
|---|---|
| `avapservice.voiceportal/IMusicSearchListener` + `IMusicBundleSearchListener` | Voice-driven music search no USB/BT |
| `appservice.vehiclecoordination/ISolarAngleCallback` | Ângulo do sol — usado pra ajustar brilho? |
| `appservice.vehiclecoordination/IFuelConsumptionCanDataCallback` | Dados de consumo de combustível em tempo real do CAN |
| `appservice.unitinfomanager/IGetMainBoardTemperatureListener` | Temperatura da placa-mãe |
| `appservice.unitinfomanager/IColorVariationChangedListener` + `IMeterColorVariationChangedListener` | Variação de cor do painel (perfil visual?) |
| `appservice.unitinfomanager/IWallPaperInformationListener` | Papel de parede dinâmico? |
| `appservice.unitinfomanager/IVehicleRunOperationControlFlagListener` | **Flag que controla regulação durante direção** — pode ser o knob que impede inputs em movimento |
| `system.beacon/IBCNTspsControl` | Beacon TSPS (algo relacionado a semáforo inteligente?) |
| `system.dsrc/IDSRCControl` | DSRC (Dedicated Short-Range Comms, V2V/V2I) |
| `system.applicationinfo/IApplicationInfoService` | Catálogo de apps conhecidos |

## Lista completa (364 interfaces, 63 domínios)

> Agrupadas por domínio (`<path>.<ultimo>.<penúltimo>` do FQDN).

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

### Domínios com 3 ou menos interfaces

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

## Observações metodológicas

- **"Listner" é grafia recorrente no shipping** (ex: `IWifiStateListner`, `IDiagServiceListner`, `ILinkManagerIAPListner`). Não é erro de transcrição nossa — está no código.
- O domínio `android.music` vem de `IMediaPlaybackService` que é padrão AOSP; não é vendor.
- `com.mitsubishielectric.ada.framework.*` são **frameworks** (consumidos via `<uses-library>`), não APKs instaláveis. `com.mitsubishielectric.ada.appservice.*` são **services** com APK + lib dual.
- `app.systeminfoservice` tem path incomum (`app`, não `appservice`) mas é internamente um service — exceção do shipping.

## Próximos passos sugeridos (não escopados aqui)

Para transformar cada entrada em algo acionável, a sequência padrão é:

1. **Deodex do APK** que implementa (ver `tooling/deodex/deodex-apk.sh`).
2. **Decompilar** a interface em si (`inspect-android-class` via REA) — dá a lista de métodos e assinaturas.
3. **Decompilar** o `.Stub.onTransact` — dá os TRANSACTION_* codes.
4. **Testar** com um app privilegiado nosso (ou via `service call <nome> <code>` no shell com su).

Para o **ICameraAPServiceReverseSignalListener**, por exemplo, isso seria o caminho pra abrir a Fase 9 (ré sem logcat).
