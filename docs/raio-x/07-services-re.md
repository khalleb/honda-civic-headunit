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

**Teclas (nomes simbólicos, valor numérico a resolver no `Const` do cpucomservice):**
`C_TALK` (voz), `C_PICKUP` (atender), `C_HANGUP_BACK` (desligar/voltar), `C_VOLUME` / `C_VOLUME_TOUCH`, e o controlador 4-way `C_FOURWAY_ENTER/LEFT/RIGHT/UPPER/LOWER`, rotação `C_FOURWAY_CLOCKWISE_ROTATE`/`ANTICLOCKWISE`, e swipes (`C_FOURWAY_SWIPE_LTOR` etc.). Grupos `SW_GEN` e `SW_PAD`.

**Como um app nosso usaria:** registrar um callback no Binder `IStrgSwApService` (bind no service `StrgSW`) implementando a interface de evento de tecla. Precisa da permissão do service (a confirmar — provável GID vehicle, como o resto). Isso dá os botões do volante sem polling de logcat — útil para substituir o AutoOk por um listener de verdade, ou para a Fase 9.

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

Service grande (440 classes). **O mute de áudio em si não mora aqui** — é feito via `IAvApService.setMute(boolean)` / `IAvApService.getMute()`, ou seja, no `AvApService` (ainda não deodexado). O `SystemInfoService` chama essa API e cuida da camada de cima:
- `VstMute` (+ `VstMuteListener`, `VstMuteTouchMonitorView`) — o mute "Vst" e seu toque na tela
- `VolumeOperationController` (+ `VolumeBar*`) — operação de volume e long-push da tecla de volume
- `EXCLUSIVE_STATUS_SOUND_BAR_DISPLAY_MUTE`
- Sistema de "interrupt header" (telops): `ACTION_INTERRUPT_FAN_CLIMATE`, `hideHeaderInterrupt`, e um ramo `"Disclaimer not Passed and CLIMATE_INTERRUPT_TYPE0"` que amarra com o gate do disclaimer

**Relação com o bug do mudo (v0.4.0):** o tap falso do AutoOk acertava um botão de mute cuja ação final é `IAvApService.setMute`. Para entender o ducking de verdade (abaixar vs. mutar, foco transiente) o próximo passo é deodexar o `AvApService` e seguir `setMute`/`getMute` + a lista de mix (`Can not get MixPlayList`). Com o v0.5.4 o bug já não acontece (o needle não casa mais o contexto errado), então isto é investigação de fundo, não correção pendente.

**TX codes do `IAvApService`** resolvidos pelo Clusters (varredura 2026-10-27):

| TX | Método |
|----|--------|
| 22 | `getVolume(int type)` — type `MAIN = 0` |
| 24 | `getMute()` |
| 72 | `getSource()` |
| 160 | `getVolumeMax()` |

**Para um AutoOk v0.6.0:** `getMute` + `getSource` + um dedup por fonte de áudio removeria o restante do risco do bug do mudo que o v0.5.4 ainda carrega como "ausência comprovada no v0.5.4" em vez de "impossível por construção".

---

## 5. Próximos passos de RE (ainda sem carro)

- Deodexar `AvApService` e mapear `setMute`/`getMute` + o mix de áudio (fecha o item 4).
- Resolver os valores numéricos das teclas do volante (classe `Const` do `cpucomservice`) e montar a tabela código→tecla.
- Comparar o sinal de ré por `VehicleInfoManager` (`CVT_SHFT_IN_REVERSE`) com o `ICameraAPServiceReverseSignalListener` para decidir a Fase 9.

Para a RE nativa (`daupdater`, `.so`): precisa primeiro dumpar o ramdisk do recovery e as libs de `/system/lib` + `/system/vendor/lib` (um OTA de `cp -L`/`dd` novo). Só então Ghidra.
