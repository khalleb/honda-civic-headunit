# Raio-X Camada 2 — RE das services (volante, OTA oficial, veículo, áudio)

Análise estática de 2026-10-27, a partir dos dumps que já temos (`tooling/apks-dumped/dump-0040/vendor-app/*.odex`), deodexados com baksmali 2.5.2 (API 17, bootclasspath = `system-framework` + `vendor-framework`). Nenhuma ida ao carro.

Quatro services deodexadas nesta passada: `StrgSW`, `SystemUpdate`, `VehicleInfoManager`, `SystemInfoService`. É um primeiro passo (API + mecanismo), não um mergulho linha a linha.

> **RE nativa está bloqueada com os dumps atuais.** O `daupdater` vive no ramdisk do recovery (MTD `recovery`), que nunca foi dumpado, e **não há nenhum `.so` no dump** (o `vendor-framework` é `.jar` odexado, não biblioteca nativa). Então "Ghidra no `daupdater` / nos `.so`" não dá pra fazer agora — depende de dumpar o ramdisk do recovery e as libs de `/system/lib` e `/system/vendor/lib`.

---

## 1. Volante — `StrgSwApService`

Service `StrgSW` (`com.mitsubishielectric.ada.appservice.strgsw`). 12 classes. Recebe as teclas do volante do `cpucomservice` (objeto `KeyCommandData`) e distribui para clientes registrados via `RemoteCallbackList`.

**Fluxo:** hardware → B-CAN → `cpucomservice` (`KeyCommandData`) → `StrgSwApService.judgeSendEvent()` → `convertKeyType`/`convertKeyStatus` → envia para os callbacks + ponte nativa `sendStrgSwEventToFramework(II)` (método **`native`**). Há também um gate de hardware em `/dev/vehicle_sts/key_consumed_status`.

**Fluxos de evento expostos** (cada um tem seu `RemoteCallbackList` de registro):
- `sendStrgKeyEvent` / `sendPriorityStrgKeyEvent` — teclas normais e por prioridade
- `sendRotaryKeyEvent` — o controlador rotativo (4-way)
- `sendMotionMenuEvent` — menu por movimento
- `sendRaspKeyEvent` — eventos "RASP"
- `sendStrgSwBcanInformation` — informação bruta do B-CAN
- `sendStrgSwStatus` — status do volante
- `sendStrgKeyEventLog` — log de eventos

**Payload** (`KeyCommandData`, 17 fields privados, mais relevantes):
- `mStrgKeyCode:I` — **código raw da tecla** (1..17 no B-CAN do Civic 2017 EXL)
- `mStrgKeyDetail:I` / `mStrgKeyDetail2:I` — detalhes (short/long press, timing)
- `mKeyType:I` — tipo bruto do evento
- `mVol:I`, `mVolXcoordinate:I`, `mVolYcoordinate:I` — valores do controlador rotativo
- `mAudio:I`, `mBack:I`, `mHome:I`, `mMenu:I`, `mNavi:I`, `mPhone:I`, `mPower:I`, `mTilt:I`, `mDayNight:I` — flags das teclas específicas

**Mapeamento `code raw → tipo lógico`** (extraído de `StrgSwApService.convertKeyType(I)` via `scratchpad/extract_keys.py`, 17 cases):

| Raw | 0x | Tipo lógico | Observação |
|---|---|---|---|
| 1 | 0x01 | 1 | |
| 2 | 0x02 | 2 | |
| 3 | 0x03 | -100 (default/erro) | não usado nessa safra |
| 4 | 0x04 | 4 | |
| 5 | 0x05 | 5 | **press** (press/release do mesmo botão agrupam par) |
| 6 | 0x06 | 6 | **press** |
| 7 | 0x07 | 7 | **press** |
| 8 | 0x08 | 8 | **press** |
| 9 | 0x09 | 5 | **release** (par com raw 5) |
| 10 | 0x0a | 6 | **release** (par com raw 6) |
| 11 | 0x0b | 7 | **release** (par com raw 7) |
| 12 | 0x0c | 8 | **release** (par com raw 8) |
| 13-14 | — | -100 | não usado |
| 15 | 0x0f | 10 (0xa) | |
| 16 | 0x10 | 11 (0xb) | |
| 17 | 0x11 | 12 (0xc) | |

**Nome simbólico ↔ tipo lógico ainda não resolvido** sem carro. O que achamos (`C_TALK`, `C_PICKUP`, `C_FOURWAY_ENTER` etc.) na verdade são **chaves de `Bundle` do BCAN status** (`mBcanStSwPadInfo.putInt("C_VOLUME_TOUCH", -1)`), não constantes de tipo de tecla. A correlação `tipo lógico 1=TALK`, `2=PICKUP`, etc. precisa de 1 teste no carro — pressionar cada tecla com um listener registrado e ler o `getKeyType()`. Baixo custo, alto valor pra qualquer app futuro.

**Fluxos de evento expostos** (cada um tem seu `RemoteCallbackList` de registro):
- `sendStrgKeyEvent` / `sendPriorityStrgKeyEvent` — teclas normais e por prioridade
- `sendRotaryKeyEvent` — o controlador rotativo (4-way)
- `sendMotionMenuEvent` — menu por movimento
- `sendRaspKeyEvent` — eventos "RASP"
- `sendStrgSwBcanInformation` — informação bruta do B-CAN (os `C_*` do Bundle)
- `sendStrgSwStatus` — status do volante
- `sendStrgKeyEventLog` — log de eventos

**Como um app nosso usaria:** registrar um callback no Binder `IStrgSwApService` (bind no service `StrgSW`) implementando a interface `IStrgSwApServiceListener.onKeyEvent(KeyCommandData)`. Precisa da permissão do service (a confirmar — provável GID vehicle, como o resto). Isso dá os botões do volante sem polling de logcat — útil para substituir o AutoOk por um listener de verdade, ou para a Fase 9.

---

## 2. OTA oficial — `SystemUpdateApService`

Este é o **caminho oficial de atualização**, o irmão app-level do `daupdater` (nativo, no recovery) que o nosso EvilValet usa. `SystemUpdateApService` + `SystemUpdateUtility` (139 classes).

**Descoberta central:** o app oficial encena o comando de recovery **do mesmo jeito** que o `daupdater`, e é quem escreve os arquivos que o nosso updater-script precisa limpar:
- Lê o trigger no pendrive: `SwUpdate2.txt` (e `SwUpdate.txt`, estados `SWUPDATE_ONE`/`SWUPDATE_TWO`) em `/mnt/usbdrive1` e `/mnt/usbdrive2`
- Copia o comando para `/cache/recovery/` (`SwUpdate.mdt`, `custom_rom`, `version`) com `--update_package=` apontando para o `.mdt`
- Escreve **`/cache/.copy_complete`** — é exatamente o flag que o nosso `build-*.py` apaga antes do sleep final pra não reaplicar em loop (§17.17). Agora sabemos quem o escreve: o `SystemUpdateApService`
- Loga `"Cannot copy command file to /cache partition"` / `"/cache partition may be broken!!"` se falhar
- Chama `IPowerManagerApService.rebootRequest()` (`"!!! REBOOTING TO INSTALL"`, `ColdReboot`/`AccOnReboot`) → "Go to recovery mode"
- Avisa no fim com o broadcast `com.mitsubishielectric.ada.app.systemupdate.ACTION_SWUPDATE_COMPLETE_NOTIFY`

Também processa `modelinfo_setting.txt`, `syscomver.txt` e `SystemInf.bin` no pendrive (reprograma model info / versão do syscom — classes `SystemUpdateReprogramData`, `SystemUpdateHeader1/2/3`, `SwUpdateCommandType/Version/Line`).

**Por que importa:** confirma por que o `build.py` mantém `NEW_DA_VERSION="IC1101"` — é pra **evitar** cair nesse fluxo app-based do SystemUpdate e usar o `daupdater` direto. E dá um Plano B de deploy que não depende do EvilValet: entregar um `.mdt` pelo caminho que o `SystemUpdateApService` já aceita. Fica como rota alternativa a investigar se o `daupdater` algum dia recusar nossos pacotes.

---

## 3. Veículo — `VehicleInfoManagerApService`

Service `VehicleInfoManager` (36 classes). Centraliza os sinais de B-CAN e os expõe por AIDL. Lê de `/dev/vehicle_sts/vehiclesignal` e `/dev/vehicle_sts/vehiclespeedpulse`.

**API (métodos públicos):** `getVehicleInfo`/`setVehicleInfo`, `getDrivingOperationStatus`/`checkDrivingOperationStatus`, `setSpeed`/`setVspSpeed`, `setParkingStatus`/`setTVParkingStatus`, `getCanInformationForAvApService`, `bcanReceiveSetting`, `setBcanCommonData`, além do bloco de customização (`sendCustomizeSettingChange/Value`, `sendRequestCustomizeReset`, TPMS, manutenção).

**Sinais confirmados:** velocidade (`vehiclespeedpulse`), VIN (`C_VINBYTE2..7`, `C_VINDATACOUNT`, `VINNO`), freio de mão (`C_PBRAKE`), e posição do câmbio CVT: **`CVT_SHFT_IN_PARKING`**, **`CVT_SHFT_IN_REVERSE`**, `CVT_GEAR_POSITION_IND_CVT`, mais os sensores de estacionamento (`PARKSENS`/`PARKSENS2`).

**TX codes resolvidos** (via [`alexpotv/Clusters`](https://github.com/alexpotv/Clusters), varredura de 2026-10-27 — ver [`08-github-landscape-2026-10-27.md §3.2`](08-github-landscape-2026-10-27.md)):

| TX | Método |
|----|--------|
| 12 | `getVehicleInfo(int subkey)` |
| 25 | `registerBcanListener(IBinder)` |
| 35 | `registerFcanListener(IBinder)` |
| 88 | `notifyBcanReceiveSetting(int canId)` — inscreve no frame |
| 102 | `getFootBrake()` |
| 103 | `getTurnSignals()` |

Subkeys de `getVehicleInfo(int)`: `0=ILLUMINATION`, `1=SHIFT`, `6=PARKING_BRAKE`, `8=SPEED`, `9=GEAR`.

**IDs internos do B-CAN** (`type` que o `IVehicleBcanInformationListener.onReceive` recebe): `318263376 VSPNE` (speed+rpm), `318263632 AT` (câmbio), `318264400 ILLUMI`, `318337360 STEERING`, `318246936/318246928 MICU_BCM/ICU` (**luz de ré**), `318334800 MAINTENANCE`, `318333520 TRICOM` (autonomia), `318336336 MET_CUSTOM` (ADAS). Lista completa em `08-github-landscape §3.3`.

**Por que importa (Fase 9):** `CVT_SHFT_IN_REVERSE` é o sinal de ré **por B-CAN**, não por logcat. Com os TX codes acima + os IDs `MICU_*`, dá para `bindService(VehicleInfoManagerApService)` → `transact(25, bcanListener)` → `transact(88, writeInt(318246936))` e tratar o callback — sem polling de logcat. Alternativa já conhecida: `ICameraAPServiceReverseSignalListener` (MAPA Raio-X §1).

---

## 4. Áudio / mute — `SystemInfoService`

Service grande (440 classes). **O mute de áudio em si não mora aqui** — é feito via `IAvApService.setMute(boolean)` / `IAvApService.getMute()`, ou seja, no `AvApService` (deodexado e analisado em §5). O `SystemInfoService` chama essa API e cuida da camada de cima:
- `VstMute` (+ `VstMuteListener`, `VstMuteTouchMonitorView`) — o mute "Vst" e seu toque na tela
- `VolumeOperationController` (+ `VolumeBar*`) — operação de volume e long-push da tecla de volume
- `EXCLUSIVE_STATUS_SOUND_BAR_DISPLAY_MUTE`
- Sistema de "interrupt header" (telops): `ACTION_INTERRUPT_FAN_CLIMATE`, `hideHeaderInterrupt`, e um ramo `"Disclaimer not Passed and CLIMATE_INTERRUPT_TYPE0"` que amarra com o gate do disclaimer

**Relação com o bug do mudo (v0.4.0):** o tap falso do AutoOk acertava um botão de mute cuja ação final é `IAvApService.setMute`. Para entender o ducking de verdade (abaixar vs. mutar, foco transiente) o próximo passo é deodexar o `AvApService` e seguir `setMute`/`getMute` + a lista de mix (`Can not get MixPlayList`). Com o v0.5.4 o bug já não acontece (o needle não casa mais o contexto errado), então isto é investigação de fundo, não correção pendente.

**TX codes do `IAvApService`** — tabela completa (213/214 resolvidos, mapeados do `onTransact` em 2026-10-29). A §5 abaixo apresenta por grupo. Nota: o `getSource` que o Clusters nomeou corresponde ao método real `getCurrentSource` (TX 72).

**Para um AutoOk v0.6.0:** `getMute` + `getCurrentSource` + um dedup por fonte de áudio removeria o restante do risco do bug do mudo que o v0.5.4 ainda carrega como "ausência comprovada no v0.5.4" em vez de "impossível por construção".

---

## 5. Áudio — `AvApService` (deodex de 2026-10-29)

Service `AV.apk` (`com.mitsubishielectric.ada.appservice.avapservice`), 719 classes. **Roda como `android.uid.phone`** (mesmo UID do rádio/telefone — super privilegiado). Interface `IAvApService` tem **213 métodos públicos abstract** (um dos maiores services da plataforma). O `SystemInfoService` da §4 fala com ele por bind + binder.

Lê de: `AudioFocusManager` interno, controla todo o áudio do carro.

### 5.1 Grupo mute / volume / source — TX codes

Em 2026-10-29 mapeei os 214 TX codes do `IAvApService` extraindo o `sparse-switch` do `IAvApService$Stub.onTransact` (213/214 métodos resolvidos — o restante é `0x5f4e5446` = `INTERFACE_TRANSACTION` padrão do IAIDL do Android, descartado).

| TX | 0x | Método |
|----|-----|--------|
| 22 | 0x16 | `getVolume(int type)` |
| 23 | 0x17 | `setVolume(int type, int value)` |
| 24 | 0x18 | **`getMute(int type)`** |
| 25 | 0x19 | **`setMute(int type)`** |
| 26 | 0x1a | `setMuteExtInfo(...)` |
| 72 | 0x48 | **`getCurrentSource()`** ← o Clusters tinha chamado de `getSource` |
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

**Confirma o que o Clusters tinha mapeado** (22, 24, 72, 160) com uma única correção de nome: TX 72 é `getCurrentSource`, não `getSource`.

### 5.2 Grupo audio focus / interrupt / ducking — TX codes

| TX | 0x | Método |
|----|-----|--------|
| 132 | 0x84 | `cancelInterrupt(int)` |
| 206 | 0xce | `abandonAudioFocus(int)` |

Apenas 2 métodos TX diretos — o resto do fluxo de focus/duck é via **callbacks registrados** (ver §5.4 "Register callbacks"), e a lógica concreta mora no `AudioFocusManager` interno do service. Strings reveladoras:
- `check transient or duck :` — faz a decisão transiente (duck) vs. interrupt
- `AA-MediaTransient command in AA-VR` — tratamento especial para Android Auto + voice recognition
- `AA-MediaTransient command in RingTone, dual source path` — dual source path para ringtone
- `change AppMode interrupt.`, `clear interrupt parameter`
- `AudioFocusManager create failed`, `already abandon audio focus`, `focusChange =`

Strings reveladoras no bytecode:
- `check transient or duck :` — faz a decisão transiente (duck) vs. interrupt
- `AA-MediaTransient command in AA-VR` — tratamento especial para Android Auto + voice recognition
- `AA-MediaTransient command in RingTone, dual source path` — dual source path para ringtone
- `change AppMode interrupt.`, `clear interrupt parameter`
- `AudioFocusManager create failed`, `already abandon audio focus`, `focusChange =`

É o `AudioFocusManager` tradicional do Android, mas com camadas adicionais para `AppMode`/`CarPlay`/`Rasp` (muitas APIs `registerCallbackForXxx`).

### 5.3 Grupo video path / display — TX codes

Surpresa: o `AvApService` também controla **video path**, não só áudio (`AvApService` = "**A**udio+**V**ideo **Ap**plication Service").

| TX | 0x | Método |
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

### 5.4 Grupos adicionais — TX codes das principais operações

**Microfones / alto-falantes:**

| TX | 0x | Método |
|----|-----|--------|
| 59 | 0x3b | `getMicMute()` |
| 60 | 0x3c | `setMicMute(...)` |
| 76 | 0x4c | `startMicDiagnosis(...)` |
| 77 | 0x4d | `stopMicDiagnosis(...)` |
| 123 | 0x7b | `execSpeakerCheck(int, int, int, int, int)` |
| 172 | 0xac | `getArrayMicMode()` |
| 173 | 0xad | `setArrayMicMode(...)` |

**Rádio** (XM/DAB/HD/Pandora, 23 TX — destaques):

| TX | 0x | Método |
|----|-----|--------|
| 30 | 0x1e | `tune(...)` |
| 100 | 0x64 | `setPandora(...)` |
| 101 | 0x65 | `getPandora()` |
| 120 | 0x78 | `createPandoraStation(int, String)` |
| 121 | 0x79 | `getXmTunerInfo(...)` |
| 131 | 0x83 | `sendItunesTag(...)` |
| 182 | 0xb6 | `deleteItunesTag()` |

**Cover art / metadata:**

| TX | 0x | Método |
|----|-----|--------|
| 36 | 0x24 | `getCurrentPlayTime()` |
| 37 | 0x25 | `getPlayStatus()` |
| 63 | 0x3f | `getCoverArtSettings(int)` |
| 69 | 0x45 | `getCoverArt()` |
| 122 | 0x7a | `getRadioArtwork(...)` |
| 130 | 0x82 | `getArtWork(int, Map)` |
| 188 | 0xbc | `notifyCurrentPlayTime(...)` |

**Ambiente / sistema:**

| TX | 0x | Método |
|----|-----|--------|
| 42 | 0x2a | `getBacklightBrightness()` |
| 43 | 0x2b | `setBacklightBrightness(...)` |
| 189 | 0xbd | `getDayNightStatus()` |
| 202 | 0xca | `e911GuidanceCarPlayStatus(int)` |

**Register callbacks** (padrão para receber eventos push do service — 26 TX, aqui destaques):

| TX | 0x | Método |
|----|-----|--------|
| 1 | 0x01 | `registerCallback(IAvApServiceCallback)` |
| 2 | 0x02 | `unregisterCallback(IAvApServiceCallback)` |
| 3 | 0x03 | `registerCallbackForExternalDisplay(...)` |
| 124 | 0x7c | `changeHftBandSpeech(int)` |
| 127 | 0x7f | `registerDeviceManagerCallback(...)` |
| 133 | 0x85 | `registerXmCallback(...)` |

**Tabela completa dos 213 TX** gerada por `scratchpad/extract_tx.py` sobre `IAvApService$Stub.onTransact`. Não cabe inteira aqui — se um dia precisar de todos, rodar o script contra o `.smali` deodexado.

### 5.5 Impacto para o nosso projeto

- **AutoOk v0.6.0 (hipotético)**: `setMute(false)` para desfazer um mute falso é possível, mas melhor é fazer **gate antes do tap**: ler `getMute(MAIN)` + `getCurrentSource()` + se `source == CARPLAY && mute == true` → **não tapar**. Elimina a classe de bug "tap em (400,350) acerta o botão de mute em contexto errado" (v0.4.0 §17.15).
- **Para apps nossos no futuro**: dá para ler `getCurrentSource`/`getCoverArt` para desenhar um cluster de música em cima do cluster secundário (estilo `alexpotv/Clusters`).
- **Risco baixo** porque é só leitura — os métodos `set*` precisam de permissão específica (a confirmar; provável que `android.uid.phone` seja requerido, ou seja, só app privilegiado).

---

## 6. Vídeo e câmera — `VideoManagerApService` (deodex de 2026-10-29)

Service `VideoManagerApService.apk` (`com.mitsubishielectric.ada.appservice.videomanager`), 30 classes. Interface `IVideoManagerApService` tem **12 métodos abstract** (service pequeno e focado). Permissões: `android.permission.CAMERA`, `android.permission.SYSTEM_ALERT_WINDOW`, `android.permission.INTERNAL_SYSTEM_WINDOW`, `android.permission.STATUS_BAR_SERVICE`, `com.mitsubishielectric.ada.permission.VEHICLE_RW`.

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

Padrão `register*Listener`/`unregister*Listener` + os `show*/hide*` em duas variantes (`Auto` e `Manual`) sugerem que a diferença é se o status change veio de uma trigger de hardware (câmera engatou, usuário no botão) ou de app controlando programaticamente.

### 6.2 🎯 Broadcasts dedicados pra câmera — rota NOVA pra Fase 9

**Achado principal:** o `VideoManagerApService` emite dois broadcasts dedicados para abertura/fechamento de câmera:

```
com.mitsubishielectric.ada.appservice.videomanager.CAMERA_START
com.mitsubishielectric.ada.appservice.videomanager.CAMERA_FINISH
```

(linha 531 do `VideoManagerApService.smali`; `sendBroadcast(Intent)` na linha 479 do mesmo arquivo).

**Isso abre uma rota muito mais simples que a Fase 9 originalmente planejada:**

| Rota | Mecanismo | Complexidade |
|---|---|---|
| Hoje (AutoOk v0.5.4) | Logcat polling procurando `am_create_activity` da câmera | Médio (polling, parsing de linha) |
| Fase 9 original | `bindService` + `transact` em `ICameraAPServiceReverseSignalListener` | Alto (Binder cru, descoberta de TX code) |
| **Fase 9 alternativa (via VideoManager)** | `BroadcastReceiver` com filter `CAMERA_START`/`CAMERA_FINISH` | **Mínimo (padrão Android, 15 linhas de código)** |
| Fase 9 alternativa 2 (via VehicleInfoManager) | `BcanListener` + `notifyBcanReceiveSetting(MICU_BCM/ICU)` | Médio (RE Camada 2 §3) |

A rota via `BroadcastReceiver` é a mais limpa. Também funciona para câmeras laterais e frontais (as outras Activities que apareceram no bytecode: `CornerCameraDisplayActivity`, `FrontCameraDisplayActivity`), não só a de ré.

### 6.3 Confirmação do issue #6 do ic1101

A issue #6 do `librick/ic1101` relatava que o `HondaHack` comercial faz bind no `IVideoManagerApService` (um dos 4 services que ele usa, junto com `IAvApService`, `IVehicleInfoManagerApService`, `ICameraAPService`). Agora sabemos **o que o HondaHack faz com esse bind**: provavelmente pergunta `isVideoOn()` + registra listener via `registVideoStatusListener` para saber quando a tela da câmera abre, pra sobrepor seu HUD por cima.

### 6.4 Impacto para o nosso projeto

- **Fase 9 fica fácil**: `AndroidManifest.xml` do nosso AutoOk ganha um `<receiver>` com `<intent-filter>` para as duas actions acima; o receiver dispara o mesmo caminho que o `am_create_activity` da câmera dispara hoje. O logcat polling do AutoOk pode permanecer como fallback.
- **App "cluster" nosso no futuro** (estilo `alexpotv/Clusters`) poderia usar `registVideoStatusListener` para saber quando pausar o overlay se a câmera abriu.

---

## 7. Próximos passos de RE (ainda sem carro)

- Decidir qual rota implementar na Fase 9 (polling logcat atual × `CAMERA_START`/`CAMERA_FINISH` do VideoManager × `MICU_BCM` do VehicleInfoManager × `ICameraAPServiceReverseSignalListener` do CameraAPService) — minha recomendação é a 2ª (BroadcastReceiver, mais simples).

Para a RE nativa (`daupdater`, `.so`): precisa primeiro dumpar o ramdisk do recovery e as libs de `/system/lib` + `/system/vendor/lib` (um OTA de `cp -L`/`dd` novo). Só então Ghidra.

**Resolvidos em 2026-10-29:**
- TX codes do `IAvApService` (213/214) mapeados do `onTransact` com `scratchpad/extract_tx.py`
- Estrutura do `KeyCommandData` + tabela parcial de `convertKeyType` (raw → tipo lógico). Falta só a correlação `tipo lógico ↔ nome simbólico`, que é 1 teste no carro
- Deodex do `AvApService` e `VideoManagerApService` (fechou §§5-6)
