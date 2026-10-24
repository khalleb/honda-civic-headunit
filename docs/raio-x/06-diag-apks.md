# Scan 6 — Diag APKs (menus de serviço)

**5 apps de diagnóstico + 1 backend AIDL, da safra `0040`.** Análise estática em 2026-10-24 a partir do deodex dos APKs em `tooling/apks-dumped/dump-0040/vendor-app/`.

## Os apps

| APK | Papel |
|---|---|
| `DealerDiag` | Menu de dealer — **91 telas** de diagnóstico/teste |
| `DeveloperDiag` | Variante de developer |
| `PreShipmentDiag` | Diagnóstico pré-envio de fábrica |
| `LetDiag` | Line End Tester (teste de fim de linha de fábrica) |
| `DiagApService` | Backend AIDL que executa os comandos (lê/escreve no veículo via CAN) |
| `DiagServiceLib` (framework) | Lib compartilhada dos acima |

## Modelo de acesso — não há PIN

- As 91 Activities do `DealerDiag` são **todas `exported="false"`** e o app **não tem nenhuma** checagem de permission/UID/SystemProperties/senha interna. Confirmado: `DealerDiagActivity` estende `BaseButtonMenuActivity`, `onCreate` sem gate.
- O controle de acesso é puramente o `exported=false`. Lançamento "oficial" é via a ferramenta **LET** ou por arquivos de trigger que um componente `inlinediag` grava em `/data/data/inlinediag/rcv_dealer_launch` e `/data/data/inlinediag/rcv_let_launch`.
- **Rota nossa (com root):** `su -c "am start -n com.mitsubishielectric.ada.app.dealerdiag/.DealerDiagActivity"` — root bypassa `exported` no Android 4.2. **A validar no carro.**
- **Não existe "PIN de dealer" hardcoded.** O `KEY_UNLOCK_CODE`/`getUnLockCode` é licenciamento de mapa **Garmin** (`GARMINUNLOCK`, `GarminUnlock*.csv not found`, `CSVFILE_ITEM_ESN`): pega o ESN e recebe um código pra liberar atualização de mapa. Não é gate de menu.

## Como leitura vs escrita foi classificado

Cada tela dispara uma função de diagnóstico em `doRequest()` via `getRequestKind()` + `requestDiagService()`. O verbo do `Param*` daquele domínio (337 classes no `appservice/diag/`) define a natureza:

- **Leitura:** `Get*`, `*Diagnosis`, `*Check`, `Load*` (lê e exibe status/histórico/versão).
- **Escrita:** `Set*`, `Save*`, `Reset*`, `Clear*`, `Delete*`, `Start*`/`Stop*` (aciona hardware), `*Repro` (reprograma), `*Correction`, `Import/Export`.

> Classificação por análise estática — **a confirmar no carro**. "Abrir" uma tela é quase sempre seguro (só monta UI); o risco está em **interagir** com os controles de escrita.

## 🔴 ESCRITA / CONFIG — altera estado, usar com cuidado

**Alto risco (pode inutilizar / apagar):**
- `DisplayReprogram`, `DisplayReprogramConfirmation` → `DisplayStartRepro` (reprograma o display — risco de brick)
- `BackupDataCleat` → `DealerClearAll` (apaga dados)

**Config / calibração persistente (escreve parâmetro que fica):**
- `CameraDisplayAdjustment`, `CornerCameraViewAdjustment`, `MonitorAdjustment`, `TouchPanelAdjustment` (`Set*`/`TouchSetCorrection`)
- `TravelOperationLimitSetting` (`RunningLimitSet`/`MileageLimitSet` — limites de operação do veículo)
- `EmergencySetting`, `QqCallSetting`, `FunctionalSetup`, `GuidelineSetup`, `GuidelineCameraSelect`, `FacePhotoDisplaySettings`, `DetailInformationAndSetting`
- `DateInput`, `UserInput`, `SaveUsersMemory`

**Comando sensível exposto direto no `DiagApService` (AIDL, sem tela própria):** `factoryResetSettings` (`TRANSACTION_factoryResetSettings`).

## 🟡 TESTE DE HARDWARE/MÍDIA — abrir = ok; controles acionam o hardware

- **Áudio/rádio/mídia:** `AirConditioner`, `Amp`, `AudioCheck`, `SpeakerCheck`, `HftMic`, `Cd`, `Dvd`, `Dtv`, `AuxVideo`, `Xm`, `Sxm`, `HdRadioFunction`, `HdTraffic`, `RemoteTuner`, `FmVics`, `PandoraFunction` (`Start*`/`Play*`/`Set*` de teste)
- **Projeção:** `AndroidAuto`, `MirrorLink`, `AppMode`
- **Câmeras:** `CornerCamera`, `CornerCameraView`, `FrontCamera`, `RearWideCamera`, `Mvc`, `LaneWatch`
- **Padrões de tela (inofensivos, só exibem):** `BlackRaster`, `WhileRaster`, `ColorPattern`, `GrayTone`, `RgbColor`, `CenterDisplay`
- **Input/diag de teste:** `HardKey`, `TouchPanelDiagnosis`, `Beacon`, `Etc`, `TcuTest`, `RtDiag`, `RtDiagnosis`, `LogData`, `Other`

## 🟢 SÓ LEITURA — consulta, seguro abrir e usar

- **Info/status:** `CarStatus`, `Version`, `GpsInformation`, `GpsAntenna`, `TcuStatus`, `TcuDtcs`, `TcuLog`, `TcuTelInfo`, `TrafficInformation`, `UsbMemoryDetailInformation`, `EtcDetail`, `SystemLinks`, `SystemLinksHelp`, `AppModeConnectionSequenceInformation`, `AppModeDetailInformation`, `MirrorLinkConnectionSequenceInformation`, `MirrorLinkDetailInformation`, `LaneWatchDetailInformation`
- **Erros/histórico:** `ErrorHistory`, `HardError`, `SoftError`, `PowerFluctuationHistory`, `ReceptionHistory`, `ReceptionHistoryDetail`, `ReportHistory`
- **Checks/sensores (leitura):** `MonitorCheck`, `UnitCheck`, `HmiUnit` (DRAM/Flash), `YawRate`, `YawSensor`, `BCan`, `FCan` (`CanDataGet*` — leem o barramento)

`DealerDiagActivity` é o menu raiz (navegação, neutro).

## Próximos passos

- **Validar no carro:** `su -c "am start -n ...dealerdiag/.DealerDiagActivity"` abre o menu? E uma tela de leitura (ex.: `CarStatus`, `Version`)?
- Confirmar os vereditos ambíguos (`BCan`/`FCan`, `LogData`, `SaveUsersMemory`) abrindo e observando.
- **Não** acionar `DisplayReprogram` nem `BackupDataCleat`/`factoryResetSettings` sem rollback preparado.

## Referências cruzadas

- [`01-apis-aidl.md`](01-apis-aidl.md) — contratos AIDL (inclui `appservice.diag`)
- [`05-trust-map.md`](05-trust-map.md) — permissões dos apps de diagnóstico
- `tooling/apks-decoded/DealerDiag-deodexed.apk` (+ demais `*-deodexed.apk`) — smali local
