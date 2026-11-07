# Scan 9 — Câmera (Camada 2: AIDL + broadcasts + sinal CAN)

**Data:** 2026-10-31
**Metodologia:** deodex de `Camera.apk` + `CameraAPService.apk` + `CameraAPServiceLib.jar` (baksmali 2.5.2, API 17, bootclasspath completo), leitura dos smalis gerados (384 + 92 + 127 arquivos), aapt sobre os manifests binários, grep cruzado.
**Alvo:** descobrir se a Fase 9 (AutoOk sem logcat polling pra ré) tem caminho real pela plataforma.

Este scan complementa o §11.4 do MAPA — que só tinha a Activity do ponto de vista do needle do watcher — com o IPC inteiro: binder, listeners, broadcast, sinal CAN e lançamento da Activity. Linka com [`07-services-re.md`](07-services-re.md) (VehicleInfoManager + CAN) e [`01-apis-aidl.md`](01-apis-aidl.md) (catálogo AIDL).

## 1. Trust e manifest

### 1.1 CameraAPService (`vendor-app/CameraAPService.apk`)

```
package           com.mitsubishielectric.ada.appservice.camera
service           CameraAPService
  exported        true
  intent-filter   action com.mitsubishielectric.ada.appservice.camera.ICameraAPService
sharedUserId      —   (nenhum)
uses-permission   com.mitsubishielectric.ada.permission.VEHICLE_RW
                  android.permission.WRITE_EXTERNAL_STORAGE
                  android.permission.WRITE_MEDIA_STORAGE
                  android.permission.ACCESS_ALL_EXTERNAL_STORAGE
uses-library      cpucomservice, vehicledbmanager, appmanagerservice, avapservice,
                  unitinfomanager, vehicleinfomanager, vehiclecoordination,
                  cameraapservice, systeminfoservice, videomanager (todas as libs
                  do framework da plataforma)
```

### 1.2 Camera app (`vendor-app/Camera.apk`)

```
package           com.mitsubishielectric.ada.app.camera
sharedUserId      —   (nenhum)
uses-permission   com.mitsubishielectric.ada.permission.VEHICLE_RW
                  android.permission.CAMERA
                  android.permission.VIBRATE
                  android.permission.STATUS_BAR_SERVICE
                  android.permission.SYSTEM_ALERT_WINDOW
                  android.permission.INTERNAL_SYSTEM_WINDOW
                  android.permission.CHANGE_CONFIGURATION
activity          .activity.RearWideCameraDisplayActivity (taskAffinity dedicada)
                  .activity.RearWideCameraGuideLineAdjustActivity
                  .activity.RearWideCameraSettingActivity
                  .activity.SteerAngleAdjustmentResultActivity
                  .activity.CornerCameraDisplayActivity + {View,Setting,GuideLineAdjust}
                  .activity.FrontCameraDisplayActivity + .FrontCameraSettingActivity
                  .activity.LaneWatchDisplayActivity + {Caution,Setting}
                  .activity.MvcDisplayActivity + {Setting,CtmSetting}
                  .activity.CameraSettingActivity, DisplaySettingActivity,
                  BsiCtmSettingActivity, CameraColdBootActivity
receiver          .util.BroadcastReceiverForCTS
                  (intent-filter: android.media.action.IMAGE_CAPTURE / VIDEO_CAPTURE)
```

Nenhuma Activity do Camera app tem `intent-filter` com action `com.mitsubishielectric.android.action.camera.*`. Elas são lançadas por `IAppManagerService.startActivity(Intent, int)` com `setClassName` direto — ver §5.

### 1.3 Permissão `VEHICLE_RW` — crítica

Declarada em `vendor-app/VehicleRW.apk`:

```
<permission android:name="com.mitsubishielectric.ada.permission.VEHICLE_RW"
            android:label="vehicle data access"
            android:protectionLevel="0x3" />
```

`protectionLevel=0x3` = `signatureOrSystem`. Qualquer APK em `/system/app/` ou `/system/vendor/app/` é elegível automaticamente, independente da assinatura — basta declarar `<uses-permission>`. Isto é determinante pra viabilidade da Opção A em §6 (o AutoOk hoje já mora em `/system/app/`, logo pode receber `VEHICLE_RW` só adicionando o `uses-permission`).

## 2. AIDL — `ICameraAPService` (164 transações)

Interface `Lcom/mitsubishielectric/ada/appservice/camera/ICameraAPService;` em `CameraAPServiceLib.jar`. 164 constantes `TRANSACTION_*` no `$Stub`. Agrupadas por função:

### 2.1 Gestão de listeners (12 pares register/unregister)

| Listener | regist TX | unregist TX | Interface |
|---|---|---|---|
| ReverseSignal 🎯 | `0x57` | `0x58` | `ICameraAPServiceReverseSignalListener` |
| BindComplete | `0x5b` | `0x5c` | `ICameraAPServiceBindCompleteListener` |
| SetViewMode (resultado) | `0x5e` | `0x5f` | `ICameraAPServiceSetViewModeResultListener` |
| ChangeViewMode | `0x6c` | `0x6d` | `ICameraAPServiceChangeViewModeListener` |
| TransparentRequest | `0x6e` | `0x6f` | `ITransparentRequestListener` |
| IgState | `0x6a` | `0x6b` | `ICameraAPServiceIgOnStateListener` |
| DrivingOperationStatus | `0x4c` | `0x4d` | `ICameraAPServiceDrivingOperationStatusListener` |
| DrivingStatus | `0x50` | `0x51` | `ICameraAPServiceDrivingStatusListener` |
| LaneWatch | `0x28` / `0x61` | `0x29` / `0x62` | `ICameraAPServiceLaneWatchListener`, `*ComunicateListener` |
| MVC | `0x85` / `0x80` / `0x87` | `0x86` / `0x81` / `0x88` | `ICameraAPServiceMvcListener`, `*ComunicateListener`, `*CameraStatusListener` |
| BsiCtm | `0x44` | `0x45` | `ICameraAPServiceBsiCtmListener` |
| CameraError / CameraCommon / UpdateGuideline / BsiCtm / ParkingSensor / Ctm | `set*` / `deset*` (TXs 0x10-0x1a) | mesmo nome | `ICameraErrorListener`, `ICameraAPServiceCommonListener`, `IUpdateGuidelineListener`, `IBsiCtmListener`, `IParkingSensorListener`, `ICtmListener` |

**Observação sobre naming:** o Mitsubishi usa duas convenções inconsistentes: `register*Listener`/`unregist*Listener` **em uns** (os `regist*`/`unregist*` novos — note o typo "regist" em vez de "register"), e `set*Listener`/`deset*Listener` nos antigos. Ambos existem na mesma interface.

### 2.2 Estado (síncronos)

- Estado da câmera / ré: `getCameraState`, `isCameraFinished`, `getCameraDestination`
- Ré-específicos: `getRearWideCameraGuidelineAdjust`, `getRearWideCameraFixGuidelinePoint`, `getRearWideCameraCautionAdjust`, `isRearWideCameraLoadFileExists`
- MVC: `getMvcDisplayStateRequest`, `getMvcLastDisplayMode`, `getMVCMoveDirection`, `getMVCParkingAssist`, `getMemoryLastScreenModeSetting`
- Veículo: `getSteeringAngle`, `getMaxSteerAngle`, `getAngleSensor`, `getIgStatus`, `getIgOnAfterPowerOn`, `getDrivingOperationStatus`, `getDrivingStatus`, `getChangeSpeedReference`, `getHandlePosision` (sic)
- Diagnóstico/debug: `isDiagMode`, `isDisclaimerScreenPassed` 🎯, `isParkingAssist`, `isShowBrightnessBar`, `isStrageDeviceExists` (sic)
- Ajustes salvos: `getCornerCameraGuidelineAdjust`, `getCornerCameraViewAdjust`, `getCornerGuidelineInfo`, `getGuidelineInfo`, `getGuidelineMode`, `getSteerAngleSetting`, `getCameraSettings`

### 2.3 Comando (lado efeito-colateral)

- Lançar câmera: `startCameraCommonApplication` (0x02), `startCameraActivity` (0x9b), `exitCameraCommonApplication` (0x03), `finishCameraCommonApplication` (0x42)
- Ré direto: `startReverseStateWatcherRequest` (0x7f), `setRearWideCameraPowerStatus` (0x99), `endEarlyRvcPreview` (0x5a), `notifyEarlyRvcPreviewStatus` (0x59)
- MVC: `notifyMvcDisplayOff/On/MenuOn/TouchEvent/VideoCancelAndFinish/VideoDisplayCancel/DisplayState`, `setMvcDispStatusDestroy/Resume`
- Câmera power: `cameraPowerOn` (0x39), `cameraPowerOff` (0x3a)
- Brightness/display: `setBacklightBrightness`, `showBrightnessBar`/`dismissBrightnessBar`, `showDisplayOffScreen`/`dismissDisplayOffScreen`, `showParkingSensorHmi`/`dismissParkingSensorHmi`
- Diag/CTM: `setCtmSystemStatus`, `notifyCtmSwStatus`, `getCtmSystemStatus`, `getBsiCtmConnectHistory`, `getCtmConnectHistory`

A chave da ré é o par **`registReverseSignalStatusListener`/`unregistReverseSignalStatusListener`** (TX `0x57`/`0x58`), que ancora a Opção A em §6.

## 3. Listeners — callbacks assíncronos

Todos moram em `CameraAPServiceLib.jar` como interface + `$Stub` + `$Stub$Proxy`. Métodos abstratos:

| Interface | Callback(s) | Tipo de evento |
|---|---|---|
| `ICameraAPServiceReverseSignalListener` 🎯 | `onNotifyReverseSignalStatus(int)` | 0 = fora da ré; 1 = em ré |
| `ICameraAPServiceCommonListener` | `onDisplayModeChanged(int)` | Mudança do display mode (dia/noite, etc.) |
| `ICameraAPServiceChangeViewModeListener` | `onNotifyChangeViewMode(int)` | Mudança de view mode (câmera traseira / lateral / etc.) |
| `ICameraAPServiceSetViewModeResultListener` | `onNotifyChangeSetViewModeResult(int)` | ack do `setViewMode` |
| `ICameraAPServiceBindCompleteListener` | `onBindComplete(int)` | Bind do service terminou (fase de inicialização) |
| `ICameraAPServiceIgOnStateListener` | `onNotifyIgState(int)` | Estado da ignição (via VehicleInfoManager) |
| `ICameraAPServiceDrivingStatusListener` | `onNotifyDrivingStatus(int)` | Estado "dirigindo/parado" |
| `ICameraAPServiceDrivingOperationStatusListener` | `onNotifyDrivingOperationStatus(int)`, `onNotifyDrivingOperationCameraStatus(int)` | Estado de operação (câmbio etc.) |
| `ICameraAPServiceMvcListener` | `onNotifyMoveDirectionChenge`, `onNotifyMvcCustomSettingChange`, `onNotifyMvcDisplayState`, `onNotifyMvcParkingAssistStatus` | Multi-View |
| `ICameraAPServiceMvcCameraStatusListener` | `onMvcCameraStatus(int)` | — |
| `ICameraAPServiceMvcComunicateListener` | `onNotifyMvcComunicateResult(int)` | — |
| `ICameraAPServiceLaneWatchListener` | `onAimingState`, `onBcanState`, `onConnectState`, `onLaneWatchSwitch`, `onTroubleState` | Lane Watch (câmera lateral) |
| `ICameraAPServicLaneWatchComunicateListener` (sic) | `onNotifyLaneWatchComunicateResult(int)` | — |
| `ICameraAPServiceBsiCtmListener` | `onNotifyBcanInformation(int, Bundle, int)` | B-CAN raw |
| `IBsiCtmListener` | `onBsiCtm(BsiCtmInfo)` | BSI/CTM |
| `ICtmListener` | `onCtm(CtmInfo)` | CTM |
| `IParkingSensorListener` | `onParkingSensor(ParkingSensorInfo)`, `onParkingSensorExt(ParkingSensorInfoExt)`, `onParkingSensorFailedState(int)` | Sensores de estacionamento |
| `IUpdateGuidelineListener` | `onUpdateGuideline(GuidelineInfo)` | Mudança nas linhas-guia |
| `ITransparentRequestListener` | `onTransparentRequest(int, int)` | — |
| `ICameraErrorListener` | `onCameraError(CameraId, CameraError)`, `onCtmError(CameraId, CtmError)`, `onNotifyCameraConnectState(CameraId, CameraState)` | Erros / conexão |

`RemoteCallbackList` interno garante entrega aos múltiplos listeners (ver §5 pra snippet).

## 4. Broadcasts `com.mitsubishielectric.android.action.camera.*`

Catálogo completo (grep bruto nos smalis):

| Action | Enviada por | Escutada por |
|---|---|---|
| `EXIT_REAR_WIDE_CAMERA` 🎯 | CameraAPService (`RearWideCameraManager.finishApp`) e Camera.apk (`CameraAppBaseActivity`, `RearWideCameraSettingActivity`, `RearWideCameraDisplayActivity$18`, `DisplaySettingActivity`) | **Ninguém no sistema atual** (nenhum manifest fora do Camera.apk; nenhum bytecode fora dele referencia a string) |
| `EXIT_REAR_WIDE_CAMERA_SET` | CameraAPService | Camera.apk (receivers em runtime, não no manifest) |
| `EXIT_FRONT_CAMERA`, `EXIT_FRONT_CAMERA_SET` | CameraAPService + Camera.apk | Idem — fluxo interno |
| `EXIT_CORNER_CAMERA`, `EXIT_CORNER_CAMERA_SET` | CameraAPService + Camera.apk | Idem |
| `EXIT_MVC`, `EXIT_MVC_SET` | CameraAPService + Camera.apk | Idem |
| `EXIT_LANEWATCH`, `EXIT_LANEWATCH_CAUTION`, `EXIT_LANEWATCH_SET` | CameraAPService + Camera.apk | Idem |
| `EXIT_DISPLAY_SET` | CameraAPService + Camera.apk | Idem |
| `PAUSE_MVC` | CameraAPService + Camera.apk | Idem |
| `ACTION_MVC_CTM` | CameraAPService + Camera.apk | Idem |
| `DISP_LANEWATCH_CAUTION` | Camera.apk | Camera.apk |
| `NOTIFY_COMMAND_RESULT_FROM_PSI` | Camera.apk | Camera.apk |

**Não existe `ENTER_REAR_WIDE_CAMERA` ou equivalente.** O service não publica o *início* da ré como broadcast — só o *fim*. O início é propagado por 2 canais paralelos:

1. **AIDL:** `ICameraAPServiceReverseSignalListener.onNotifyReverseSignalStatus(1)` pra quem estiver registrado;
2. **Activity:** `IAppManagerService.startActivity(Intent{setClassName(..., RearWideCameraDisplayActivity)}, 4)` — detalhado em §5.

Verificado por grep bruto em todos os `AndroidManifest.xml` + `classes.dex` de `vendor-app/` e `system-app/` do dump: **zero hits de `EXIT_REAR_WIDE_CAMERA` fora do Camera.apk** (manifest *e* bytecode). Ou seja, hoje esse broadcast morre no ar — é "fire-and-forget" sem ninguém escutando. Para o AutoOk receber, basta um `<receiver>` com `<intent-filter>` pra essa action no `AndroidManifest.xml` — nenhuma permissão exigida.

## 5. Fluxo da ré ponta a ponta

### 5.1 Mapa

```
B-CAN publica CVT_SHFT_IN_REVERSE
          ↓
VehicleInfoManagerApService (bind do CameraAPService em `uses-library`)
          ↓
IVehicleCanInformationForCameraApServiceListener (registrado por CameraAPService)
          ↓
CameraAPService → ReverseStateWatcher.getReverseStatus() → RearWideCameraManager.reverseChanged(int)
          ↓
          ├─→ Entrou na ré (p1 == 1):
          │     • startCameraCommonApplicationImpl(StartMode.RVC, …)
          │     • monta Intent setClassName("com.mitsubishielectric.ada.app.camera",
          │                                 ".activity.RearWideCameraDisplayActivity")
          │     • IAppManagerService.startActivity(intent, 4)   ← Activity sobe
          │     • dispara RemoteCallbackList → onNotifyReverseSignalStatus(1)
          │
          └─→ Saiu da ré (p1 == 0):
                • finishApp() → sendBroadcast("com.mitsubishielectric.android.action.camera.EXIT_REAR_WIDE_CAMERA")
                • dispara RemoteCallbackList → onNotifyReverseSignalStatus(0)
                • (Activity faz pop sozinha ao receber o próprio EXIT_REAR_WIDE_CAMERA via receiver interno)
```

### 5.2 Snippet 1 — `RearWideCameraManager.reverseChanged(int)` dispara o callback

Trecho em `camaps-smali/com/mitsubishielectric/ada/appservice/camera/internal/RearWideCameraManager.smali`, método `reverseChanged`, linhas ~6244-6400:

```smali
# int signalStatus = (p1 == 1) ? 1 : 0;
if-ne v13, p1, :cond_4f           # v13 = 0x1 (constante)
const/4 v6, 0x1
:cond_4f
# if (signalStatus != mReverseSignalStatus) { broadcast(signalStatus); }
iget v9, p0, …RearWideCameraManager;->mReverseSignalStatus:I
if-eq v9, v6, :cond_f1
invoke-virtual {v9}, …CameraAPService;->getReverseSignalListenerCallbackList()Landroid/os/RemoteCallbackList;
invoke-virtual {v9}, Landroid/os/RemoteCallbackList;->beginBroadcast()I
move-result v7
:goto_5e                           # loop pelos listeners
if-ge v2, v7, :cond_f7
invoke-virtual {v9, v2}, Landroid/os/RemoteCallbackList;->getBroadcastItem(I)Landroid/os/IInterface;
check-cast v9, …ICameraAPServiceReverseSignalListener;
invoke-interface {v9, v6}, …ICameraAPServiceReverseSignalListener;->onNotifyReverseSignalStatus(I)V
```

Entra em `reverseChanged` por 5 pontos distintos dentro do `CameraAPService.smali` (linhas 1512, 1911, 9763, 10093, …). Todos resolvem o estado atual via `ReverseStateWatcher.getReverseStatus()` antes de chamar. `ReverseStateWatcher` é a classe que faz a ponte do callback do VehicleInfoManager pro `reverseChanged` interno — assim o service tem **uma fonte única de verdade pra ré**, independente do caminho de entrada (power on, cold boot, resume de LP0, mudança de câmbio em tempo real).

### 5.3 Snippet 2 — `RearWideCameraManager.finishApp()` publica o EXIT

```smali
# Linhas 2190-2220
.method protected finishApp()Z
    new-instance v0, Landroid/content/Intent;
    const-string v1, "com.mitsubishielectric.android.action.camera.EXIT_REAR_WIDE_CAMERA"
    invoke-direct {v0, v1}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V
    iget-object v1, p0, …RearWideCameraManager;->mService:…CameraAPService;
    invoke-virtual {v1, v0}, …CameraAPService;->sendBroadcast(Landroid/content/Intent;)V
    const/4 v1, 0x1
    return v1
.end method
```

Sem permission, sem receiver filter, sem flag — broadcast implícito simples.

### 5.4 Snippet 3 — lançamento da Activity via `AppManagerService`

Trecho em `startCameraCommonApplicationImpl` (RearWideCameraManager, linhas 4987-5137):

```smali
new-instance v3, Landroid/content/Intent;
invoke-direct {v3}, Landroid/content/Intent;-><init>()V
const-string v11, "com.mitsubishielectric.ada.app.camera"
const-string v12, "com.mitsubishielectric.ada.app.camera.activity.RearWideCameraDisplayActivity"
invoke-virtual {v3, v11, v12}, Landroid/content/Intent;->setClassName(Ljava/lang/String;Ljava/lang/String;)…
# …
invoke-interface {v11, v3, v4}, …IAppManagerService;->startActivity(Landroid/content/Intent;I)I
#                                                  ↑ v4 = display ID (4 = camera)
```

**Isto não é `Context.startActivity`**: o service não lança a Activity direto, delega para o `AppManagerService` central da plataforma (`com.mitsubishielectric.ada.appservice.appmanagerservice`), que é o window manager interno Honda/Mitsubishi responsável por priorizar quem fica no topo (ver [`01-apis-aidl.md`](01-apis-aidl.md) — a AIDL `IAppManagerService` é o choke point de todas as transições de tela da plataforma). É por isso que a câmera "sobe sobre qualquer Activity" com precedência correta (incluindo o aviso) — não é o launcher que coordena, é o AppManagerService.

### 5.5 Vida pré/durante LP0

`AccOffBroadcastReceiver.smali` dentro do CameraAPService registra 4 actions do PowerManager:

- `ACTION_CHANGE_BOOT_CAUSE`
- `ACTION_HMI_SERVICE_STOP_A`
- `ACTION_HMI_SERVICE_STOP_J`
- `ACTION_HMI_SERVICE_STOP_COMPLETE_J`

Estados internos: `STATE_ACC_OFF (0)`, `STATE_ACC_ON (1)`, `STATE_ACC_OFF_PRE (2)`, `STATE_ACC_ON_RESTART (3)`, `STATE_RESUME (4)`. Significa que o service **sabe quando entra/sai de LP0** e tem lógica dedicada pra re-inicializar o `ReverseStateWatcher` no RESUME — alinha com o cenário do §17.13 do MAPA (bug do v0.3.0, resolvido no v0.4.0 por outra via).

### 5.6 `sendResumeCameraIntent` — não implementado

A memória `whitelist-nao-afeta-lp0` cita `sendResumeCameraIntent` como "oportunidade" em contraste à whitelist. Varredura em todo o bytecode do dump (vendor-app + system-app + CameraAPServiceLib) **não encontra nenhum símbolo com esse nome**. É um nome aspiracional, não existe função dessa assinatura hoje. O equivalente real é o par (`startCameraCommonApplicationImpl` + `IAppManagerService.startActivity`) descrito em §5.4.

## 6. Oportunidade da Fase 9 — veredito

Objetivo: tirar o AutoOk do logcat polling pra ré, de modo a (a) economizar CPU no watch, (b) tirar o acoplamento com `am_create_activity`/`am_new_intent` que já quebrou 3× nas versões v0.5.0-v0.5.3 (§17.15 do MAPA).

### 6.1 Opção A — bind no `ICameraAPService` + register `ReverseSignalListener`

**Mecânica:**

```java
Intent i = new Intent("com.mitsubishielectric.ada.appservice.camera.ICameraAPService");
i.setPackage("com.mitsubishielectric.ada.appservice.camera");
bindService(i, conn, BIND_AUTO_CREATE);
// onServiceConnected:
ICameraAPService s = ICameraAPService.Stub.asInterface(binder);
s.registReverseSignalStatusListener(new ICameraAPServiceReverseSignalListener.Stub() {
    public void onNotifyReverseSignalStatus(int status) {
        // status == 1 → ré ativa; 0 → saiu
    }
});
```

**Requisitos no AutoOk:**

- `<uses-permission android:name="com.mitsubishielectric.ada.permission.VEHICLE_RW" />` — concedido automaticamente por estar em `/system/app/` (protectionLevel `signatureOrSystem`, §1.3).
- `<uses-library android:name="com.mitsubishielectric.ada.appservice.cameraapservice.lib" android:required="true" />` — a biblioteca mora em `/system/vendor/framework/CameraAPServiceLib.jar` e expõe as classes AIDL (`ICameraAPService`, `*ReverseSignalListener`). Permissão XML em `/system/etc/permissions/com.mitsubishielectric.ada.appservice.cameraapservice.lib.xml`.

**Riscos:**

- **Reconexão em LP0:** o service pode ser destruído/recriado no ciclo ACC OFF → RESUME; o AutoOk precisa reagir ao `onServiceDisconnected` e re-bindar + re-registrar o listener (ou escutar o próprio `ACTION_HMI_SERVICE_START` que o AutoOk já tem e usar como gatilho de rebind — paralelo bonito ao `HmiServiceReceiver` existente).
- **Classpath/compile-time:** nosso AutoOk compila em JDK 17 contra o SDK Android 13 (compileSdk 13 no manifest atual — ver §17.15/MAPA). Pra referenciar `ICameraAPService` precisa ter o `.aidl` ou os `.class` do `CameraAPServiceLib.jar` como compileOnly. Tem como extrair via `dex2jar` sobre o `CameraAPServiceLib.odex` já deodexado — fricção baixa, mas trabalho novo.
- **Testabilidade em JVM:** o AutoOk hoje tem a saga toda das lições v0.5.x cobertas por testes puros (needle match, dedup). Trocar pra AIDL perde esse pattern — o teste vira "mocka ICameraAPService.Stub" em vez de "alimenta logcat sintético". É regressão, não melhora.

**Força:** zero polling, latência de ms (o callback entrega direto do service), e **captura tanto o entrar quanto o sair** da ré num único listener. Independente do formato do logcat (que quebrou 3×).

### 6.2 Opção B — BroadcastReceiver pra `EXIT_REAR_WIDE_CAMERA`

**Mecânica:**

```xml
<receiver android:name=".RearExitReceiver" android:exported="true">
    <intent-filter>
        <action android:name="com.mitsubishielectric.android.action.camera.EXIT_REAR_WIDE_CAMERA"/>
    </intent-filter>
</receiver>
```

**Requisitos no AutoOk:**

- Nenhum — a action é pública, sem permissão exigida (§4), e nenhum outro app a escuta hoje (sem conflito de prioridade).

**Riscos:**

- **Só o lado "saiu da ré"** — não existe `ENTER_*` análogo (§4). Pra detectar o *início* da ré, Opção B precisa combinar com algo: ou continuar polling do logcat (meia troca), ou usar `ICameraAPServiceReverseSignalListener` só pra entrada (vira híbrido com A).
- Broadcast implícito em Android 4.2 pode sofrer com `startup wait` — o receiver só é entregue depois do app ter visto o primeiro `BOOT_COMPLETED`. O AutoOk já tem `BootReceiver`, então ok, mas se o deploy for em meio ao deploy OTA, pode perder o primeiro EXIT até o reboot completar.

**Força:** zero fricção, sem AIDL, sem classpath exótico, sem bind lifecycle. Casa com a arquitetura já existente de BroadcastReceivers no AutoOk (`BootReceiver`, `HmiServiceReceiver`).

### 6.3 Opção C — ficar como está (logcat polling)

**Força:** v0.5.4 está em prod há 11 dias (deploy 2026-10-20, Fase 10 em 2026-10-29) sem incidente. A saga v0.5.0→v0.5.4 pagou o custo de aprender o formato certo (`-b events` + `am_create_activity|am_new_intent` + `NORMAL_STARTUP`), e os testes puros em JVM cobrem a regressão. Após Fase 10, o próprio papel do AutoOk mudou — ele vira safety net, não path principal, então o "zero polling" perde urgência.

**Fraqueza:** continua acoplado ao formato de log, que é privado do Android (poderia ter mudado em uma versão futura — mas essa central tá cristalizada em 4.2.2).

### 6.4 Recomendação

**Opção C + mudança oportunística pra B quando houver próximo rebuild do AutoOk** por outro motivo. Rationale:

1. A Fase 9 só valia a pena *antes* da Fase 10 — hoje o AutoOk nem precisa agir, exceto como safety net quando o patch do DaLauncher sumir (atualização OTA Honda).
2. Opção A tem o maior upside técnico, mas o custo (classpath AIDL, lifecycle de bind, perda do pattern de teste atual) não é compensado pela redução de CPU — o watcher atual é barato.
3. Opção B é **praticamente free** se feita junto do próximo rebuild (Chainfire SR1 swap já pendente, output `20261029T150600Z`): só adiciona um `<receiver>` no manifest e um `onReceive` que chama o mesmo `forceRestartWatcher()` que o `HmiServiceReceiver` já chama hoje. Vale como "handshake extra" pra rearme preciso ao sair da ré, melhorando o cenário do §17.13.

Se um dia a janela de teste do carro voltar a ser confortável (pós-garantia, hoje é apertada), Opção A pode ser retomada — mas aí o escopo deveria ser maior: usar o `ICameraAPService` também pra outros usos (vehicle info, ignition state), não só ré.

## 7. Known limits — não investigado

- **RE nativa das libs da câmera** — bloqueada. Não temos dump raw da partição onde moram as `.so` (`libcameraapservice.so`, `libcamera_metadata.so` do Mitsubishi, etc.). Depende do deploy do `output-dump-raw/20261030T115127Z/` no carro (§3.3 do MAPA; MTD + SDA incluídos).
- **V4L2 e eventos do kernel do Tegra 3** — fora de escopo, exigem acesso ao sistema vivo.
- **CTM, BSI, Lane Watch** — mapeadas as interfaces/callbacks (§2.1, §3), mas não aprofundadas no fluxo. Fase 9 só pede o pedaço da ré; o resto fica catalogado.
- **IAppManagerService** — tratado como choke point sem destrinchar a lógica interna (prioridade entre múltiplas Activities concorrentes). Candidato de Camada 2 futuro.

## Cross-references

- MAPA §11.4 (Câmera de ré — ponto Activity) — este scan complementa com todo o IPC
- MAPA §16.3 (whitelist Mitsubishi descartada) — `sendResumeCameraIntent` mencionado como oportunidade, aqui comprovado como aspiracional (§5.6)
- MAPA §17.13 (v0.3.0 bug "aviso persiste pós-câmera") — resolvido via HmiServiceReceiver (não via escuta de câmera); confirma que Opção B supre o rearme sem precisar de Opção A
- [`01-apis-aidl.md`](01-apis-aidl.md) — `ICameraAPService` + listeners listados no catálogo geral
- [`05-trust-map.md`](05-trust-map.md) — Camera.apk e CameraAPService.apk sem sharedUserId
- [`07-services-re.md`](07-services-re.md) — VehicleInfoManager é a fonte do sinal CAN que alimenta o `ReverseStateWatcher`
- `tooling/apks-decoded/Camera-deodexed.apk`, `CameraAPService-deodexed.apk`, `CameraAPServiceLib-smali/` — artefatos locais usados neste scan
