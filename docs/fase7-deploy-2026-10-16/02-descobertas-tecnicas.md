# Ficha técnica da safra `1.F187.16` BR

Dados técnicos consolidados da central Civic 2017 EXL BR, Display Audio Mitsubishi Andromeda. Base de referência para qualquer trabalho futuro na mesma central ou em safras adjacentes.

Fonte primária: dumps obtidos no deploy 2026-10-16 em `tooling/apks-dumped/dump-0040/` e logs via `Error History → Save`. Veja [06-dumps-obtidos.md](06-dumps-obtidos.md) para catálogo dos dumps.

## 0. Contribuições novas deste projeto

Este projeto é o **primeiro deploy público confirmado de EvilValet em safra brasileira** (`1.F187.16` BR, deploy 2026-10-16). Além da confirmação em si, estas descobertas específicas da safra BR não aparecem em nenhuma fonte pública anterior (nem no post juniperspring, nem no `ic1101/docs/updates.md`):

| Descoberta | Impacto | Seção |
|---|---|---|
| Rom type `0040` para safra `1.F187.16` BR | Chave do EvilValet nessa safra; sem isso não há deploy | [§ 2.2](#22-buildprop-do-systemvendor-mmcblk0p2--partition-cap) |
| Combo **`AUDIO 5s`** para forçar cold boot | Sem esse combo, `daupdater` nunca roda (porque "virar a chave" não é cold boot nessa safra) | [§ 6](#6-combos-físicos-conhecidos) |
| Recovery dessa safra **não tem `/sbin/sh`** | Updater-script precisa de busybox embarcado para shell ops | [§ 8](#8-recovery-da-nossa-safra) |
| `SystemUpdate` da safra BR **aceita `NEW_DA_VERSION` sem prefix `1.F1`** | Permite usar `"IC1101"` sem precisar fingir número de versão. Diferente da safra 2021 US documentada no `ic1101/updates.md` | [§ 7.2](#72-fluxo-systemupdate-app-based-com-ui-software-update--copying) |
| Partição `MITSU` extra (`mmcblk0p5`) exclusiva da safra BR | Safra 2021 US não tem. Função exata não determinada. | [§ 2.6](#26-partition-map-emmc-mmcblk0) |
| BOOT_COMPLETED não dispara em suspend wake | APK auto-OK precisa ser persistente (nunca `stopSelf()`) | [04-apk-autook-detalhes.md](04-apk-autook-detalhes.md) |

Essas descobertas são contribuição desta sessão para a base de conhecimento comum (podem alimentar PR futuro ao `ic1101/docs/updates.md`).

**Fontes primárias que usamos** (atribuição correta):

- Para **o fluxo do daupdater, formato do pacote OTA, mecanismo de version check, risco de recovery loop**: `tooling/references/ic1101/docs/updates.md` (de librick / Eric McDonald). Esse é o documento técnico operacional.
- Para **o contexto da vulnerabilidade EvilValet e nomenclatura**: [juniperspring.org/posts/honda-evil-valet](https://juniperspring.org/posts/honda-evil-valet/) (mesmo autor, post de 2026-06-13). O autor explicitamente diz que o post **não é technical writeup** — é anúncio.
- Para **`su` ARM estático e SuperSU opcional**: `tooling/references/root-honda/` (de codeage).
- Para **tudo mais** (safra específica, combos, fluxo real, debugging): este projeto.

## 1. Identificação do veículo e central

| Campo | Valor | Fonte |
|---|---|---|
| Marca/modelo | Honda Civic EXL | — |
| Ano | 2017 | — |
| Mercado | Brasil | — |
| Central | Honda Display Audio 7" (Mitsubishi Andromeda) | — |
| Processador | NVIDIA Tegra 3 (ARM Cortex-A9 quad-core) | `kmsgcat.txt` |
| RAM | 1021 MB | kernel cmdline: `mem=1021M@2048M` |
| eMMC | 7.03 GiB (chip VM010B) | kernel: `mmcblk0: mmc0:0001 VM010B 7.03 GiB` |
| Secondary flash | 15.0 GiB (chip RP16G em mmcblk1) | kernel: `mmcblk1: mmc2:cc7d RP16G 15.0 GiB` |
| NOR flash | ~64 MB (recovery/boot/misc) | kernel cmdline: `mtdparts=tegra-nor:...` |
| Display | 800×480, LVDS | kmsg: `hwcomposer: Display 0 is 800 x 480` |

## 2. Software

### 2.1 Build.prop do /system (`mmcblk0p3` = partition `APP`)

Arquivo completo em `tooling/apks-dumped/dump-0040/system-build.prop`. Resumo:

```properties
ro.build.id=1.F187.16
ro.build.display.id=1.F187.16
ro.build.version.incremental=55
ro.build.version.sdk=17
ro.build.version.codename=REL
ro.build.version.release=4.2.2
ro.build.date=2016年 4月 7日 木曜日 19:33:13 JST
ro.build.date.utc=1460025193
ro.build.type=user
ro.build.user=MitsubishiElectric
ro.build.host=BUILD_PC
ro.build.tags=release-keys
ro.product.model=MY16ADA
ro.product.brand=Honda
ro.product.name=Andromeda
ro.product.device=vcm30t30
ro.product.board=Andromeda
ro.product.cpu.abi=armeabi-v7a
ro.product.cpu.abi2=armeabi
ro.product.manufacturer=MITSUBISHI ELECTRIC
ro.product.locale.language=en
ro.product.locale.region=US
ro.wifi.channels=
ro.board.platform=tegra
ro.build.product=vcm30t30
ro.build.description=vcm30t30-user 4.2.2 1.F187.16 55 release-keys
ro.build.fingerprint=Honda/Andromeda/vcm30t30:4.2.2/1.F187.16/55:user/release-keys
ro.build.characteristics=tablet,nosdcard
ro.opengles.version=131072
wifi.interface=wlan0
rild.libpath=/system/lib/libril-icera.so
rild.libargs=-e rmnet0
persist.tegra.nvmmlite=1
ro.sf.override_null_lcd_density=1
keyguard.no_require_sim=true
debug.nfc.fw_download=false
debug.nfc.se=false
ro.ril.wake_lock_timeout=200000
ro.streaming.video.drs=true
persist.sys.usb1_mode=host
persist.tegra.un_premult_alpha=1
ro.carrier=wifi-only
drm.service.enabled=true
dalvik.vm.heapstartsize=5m
dalvik.vm.heapgrowthlimit=48m
dalvik.vm.heapsize=256m
dalvik.vm.heaptargetutilization=0.75
dalvik.vm.heapminfree=512k
dalvik.vm.heapmaxfree=2m
dalvik.vm.dexopt-flags=m=y
net.bt.name=Android
dalvik.vm.stack-trace-file=/data/anr/traces.txt
tf.enable=y
```

Observações:
- `ro.product.locale` é `en`/`US` mesmo sendo safra BR — o idioma português é selecionado por app, não pelo locale do Android.
- `rild.libpath=/system/lib/libril-icera.so` — Icera é um modem baseband (NVIDIA comprou ICERA em 2011). Pode ser que a central tenha hardware modem GSM dormindo que nunca é ativado.
- `ro.carrier=wifi-only` — confirma que não há plano cellular ativo.
- `dalvik.vm.heapsize=256m` — heap grande para a época (Android 4.2.2 default era 48MB-128MB em celulares).

### 2.2 Build.prop do /system/vendor (`mmcblk0p2` = partition `CAP`)

Arquivo completo em `tooling/apks-dumped/dump-0040/vendor-build.prop`. Conteúdo:

```properties
custom_rom.type=0040
custom_rom.id=039726af3d8671c3855d21a9832e5214
```

Apenas 2 linhas. **O `custom_rom.type=0040` é a chave do EvilValet** — é o valor que o `daupdater` compara com o nome da pasta `/mnt/usbdrive1/<rom_type>/SwUpdate.mdt` no pendrive. Match exato (strcmp), case-sensitive.

O `custom_rom.id` é um hash MD5 (32 chars hex). Finalidade exata desconhecida — provavelmente identificador único da combinação de safra + customizações.

### 2.3 Hardware version e firmware versions (do logcat)

Vindo de `PhoneCoordinationApService.registerCallback`:

```
hardware version: 10.110
softwareVersion: 1.F187.16
serialNumber: <serial-redactado>
```

Vindo de `SystemUpdateApService.create_syscom_version_file`:

```
Program Version = CPU0x0171.55.13;H62F0N
```

`CPU0x0171.55.13;H62F0N` — versão do subsystem CPU (provavelmente o microcontrolador syscon que gerencia power management + comunicação com veículo).

### 2.4 Kernel

Do `kmsgcat.txt`:

```
Linux version 3.1.10+ (jenkins@NDYWY3861584) (gcc version 4.6.x-google 20120106 (prerelease) (GCC) ) #1 SMP PREEMPT Thu Apr 7 18:50:54 JST 2016
CPU: ARMv7 Processor [412fc099] revision 9 (ARMv7), cr=10c5387d
CPU: VIPT nonaliasing data cache, VIPT aliasing instruction cache
Machine: vcm30t30
```

- Kernel compilado em **7 abril 2016 18:50:54 JST** (Japão horário local).
- Compilador: GCC 4.6.x Google 20120106 prerelease. Toolchain antiga.
- Build host: `jenkins@NDYWY3861584` (CI do Mitsubishi).
- Machine code: `vcm30t30` (plataforma NVIDIA Tegra 3 do fornecedor VCM — Vehicle Computing Module Rev 30 T30).

### 2.5 Kernel command line

```
tegraid=30.1.3.0.0 mem=1021M@2048M video=tegrafb debug_uartport=lsport,1
usbcore.old_scheme_first=1 lp0_vec=8192@0x84008140 core_edp_mv=1300
nvsku=699-61855-1002-000 SkuVer=AB ProdInfo=000-00000-0000-000 ProdVer=
no_console_suspend=1 android.kerneltype=normal
androidboot.bootloader=1.10_20160407183722 commchip_id=0
console=ttyS0,115200n8 androidboot.serialno=<serial-redactado>
androidboot.hardware=vcm30t30 androidboot.console=ttyS0
mtdparts=tegra-nor:2M@21504K(USP),8M@4864K(recovery),8M@13056K(boot),
         2M@23552K(app_datas),256K@25600K(app_datas_ex),2M@59392K(misc),
         3M@61440K(kpanic),65536K@0K(whole_device)
quiet lpj=8996624 vmalloc=256m nr_cpus=4
da.hwversion=0xb da.camera_mode=2 da.clr.rgb_d=2229,1971,0,0,0
da.clr.rgb_n=1365,1091,0,0,0 da.clr.yuv_d=2371,1971,0,0,0,0,0
da.clr.yuv_n=1091,1091,0,0,0,0,0 da.tilt_step=771 da.car_model=TBAA
da.mvc_connect=0 da.vol_knob=2791,2791 da.cd_slot=21,5,0 da.navi=0
da.reboot=0 da.ill=0
```

Observações importantes:

- **`da.car_model=TBAA`** — código Honda interno para a família Civic sedan 10th gen. Fontes externas (catálogos de peças Honda, forums) sugerem chassis FC. "TBAA" especificamente pode indicar sub-variante regional, mas sem confirmação pública clara.
- **`androidboot.serialno=<serial-redactado>`** — número de série da central. Usar em qualquer suporte Honda ou identificação futura.
- **`androidboot.bootloader=1.10_20160407183722`** — bootloader versão 1.10, datado também de 2016-04-07 (mesmo dia do kernel).
- **`nvsku=699-61855-1002-000 SkuVer=AB`** — SKU NVIDIA do módulo Tegra 3.
- **`mtdparts`**: NOR flash dividido em 8 partições (USP, recovery, boot, app_datas, app_datas_ex, misc, kpanic, whole_device). Total 64MB. `recovery` tem 8MB (nossa fonte da verdade para o updater).
- `da.navi=0` — safra EXL BR não tem Navi nativo (confirmado — é a safra "sem GPS", DA Audio-only).
- `da.hwversion=0xb` — revisão de hardware 11.

### 2.6 Partition map (eMMC `mmcblk0`)

Partition device-mapper by-name links (confirmado via dump do próprio recovery):

| By-name | Device | Mount point | Filesystem | Mode | Função |
|---|---|---|---|---|---|
| `APP` | `mmcblk0p3` | `/system` | ext4 | ro | Sistema Android |
| `CAC` | `mmcblk0p1` | `/cache` | ext4 | rw | Cache do Android (OTA stage, dalvik cache) |
| `CAP` | `mmcblk0p2` | `/system/vendor` | ext4 | ro | Framework Mitsubishi/Honda |
| `LOG` | `mmcblk0p4` | `/log` | ext4 | rw | Logs da central (persistentes) |
| `MITSU` | `mmcblk0p5` | ? | ext4 | rw | Específica Mitsubishi (safra BR tem, 2021 US não) |
| `SDA` | `mmcblk0p6` | `/mnt/data1` (safra US) | ext4 | rw | Dados usuário 1 |
| `SDA2` | `mmcblk0p7` | `/mnt/data2` (safra US) | ext4 | rw | Dados usuário 2 |
| `SDC` | `mmcblk0p8` | `/mnt/media` (safra US) | ext4 | rw | Media/arquivos |
| `UDA` | `mmcblk0p9` | `/data` | ext4 | rw | User data (dados de apps, Dalvik cache) |

**Diferença crítica vs safra 2021 US:**
- Nossa safra BR tem `MITSU` extra (`mmcblk0p5`).
- Mount point e função exata de `MITSU` não confirmados (dump não revelou — content não foi inspecionado).

### 2.7 Partição NOR flash (`mtd-tegra-nor`)

Do kernel cmdline:

| Nome | Offset | Tamanho | Função |
|---|---|---|---|
| `USP` | 21504K | 2M | ? |
| `recovery` | 4864K | 8M | Imagem do recovery |
| `boot` | 13056K | 8M | Imagem do boot |
| `app_datas` | 23552K | 2M | Dados de app persistentes |
| `app_datas_ex` | 25600K | 256K | Extended app_datas |
| `misc` | 59392K | 2M | Misc partition (boot flags) |
| `kpanic` | 61440K | 3M | Kernel panic log |
| `whole_device` | 0K | 65536K | Device inteiro (bypass partition) |

## 3. Framework Mitsubishi Andromeda — apps catalogados

Catálogo completo dos APKs em `/system/vendor/app/` (dump em `tooling/apks-dumped/dump-0040/vendor-app/`):

### 3.1 Launcher e UI

- `DaLauncher.apk` — Launcher principal (home screen, tela de aviso)
- `DaSettings.apk` — Configurações
- `AppManager.apk` — Gerenciador de apps
- `AppMode.apk` / `AppModeApService.apk` — Modos do carro
- `TaskManager.apk` — Gerenciador de tarefas
- `FileManager.apk` — Gerenciador de arquivos

### 3.2 Áudio e multimídia

- `AV.apk` — Áudio/Vídeo
- `AVPlayer.apk` — Player
- `MediaCoreService.apk` — Serviço de media

### 3.3 Conectividade telefônica

- `HftApp.apk` / `HftApService.apk` — Hands-Free Telephony (Bluetooth phone)
- `PhoneCoordination.apk` — Coordenação de telefone
- `WifiApp.apk` / `WifiApService.apk` — Wi-Fi

### 3.4 Smartphone mirroring

- `CarPlay.apk` / `CarPlayService.apk` — Apple CarPlay
- `AndroidAuto.apk` — Android Auto
- `MirrorLink.apk` — MirrorLink
- `SiriEFM.apk` — Siri EFM (Siri Eyes Free Mode)
- `VoicePortal.apk` / `VoicePortalAp.apk` — Portal de voz
- `VRSD.apk` — Voice Recognition Steering wheel Device

### 3.5 Navegação (safra EXL BR não tem Navi nativo, mas o APK existe)

- `Navigation.apk` — Navegação

### 3.6 Veículo e diagnóstico

- `VehicleCoordination.apk` — Coordenação de veículo
- `VehicleDbManager.apk` — DB Manager
- `VehicleInfoManager.apk` — Info do veículo
- `VehicleRW.apk` — Vehicle Read/Write (CAN bus?)
- `UnitInfoManager.apk` — Info da central
- `CompassService.apk` — Bússola
- `SensorMonitor.apk` — Monitor de sensores
- `SystemInfoService.apk` — Info do sistema

### 3.7 Diagnóstico profissional

- `DealerDiag.apk` — Diagnóstico de concessionária
- `DeveloperDiag.apk` — Diagnóstico de desenvolvedor
- `DiagApService.apk` — Service de diagnóstico
- `LetDiag.apk` — ? (versão simplificada?)
- `PreShipmentDiag.apk` — Diagnóstico pré-envio
- `ErrorManager.apk` — Gerenciador de erros (que gera o Error History!)

### 3.8 Honda-específicos

- `AcuraLinkApp.apk` / `AcuraLinkApService.apk` — AcuraLink (safra tem AcuraLink desabilitado em BR)
- `Telematics.apk` — Telemática
- `AntiTheft.apk` — Antifurto
- `EmergencyApp.apk` / `EmergencyApService.apk` — Emergência

### 3.9 Automotivo e UI especializada

- `AirCon.apk` — Ar condicionado
- `CameraAPService.apk` / `Camera.apk` — Câmera (ré, 360?)
- `ClockSync.apk` — Sincronização de relógio (via GPS/CAN)
- `CpuComService.apk` — Comunicação com CPU/syscon
- `EcoTripComputer.apk` — Computador de bordo eco
- `EnergyManagement.apk` — Gerenciamento de energia (bateria)
- `ETC.apk` — ETC (pedágio automático, japonês)
- `ExternalDisplayApService.apk` / `ExternalDisplayOutService.apk` — Display externo
- `HudApService.apk` — Head-Up Display
- `LinkManagerApService.apk` — Link Manager
- `PowerManagerApService.apk` — Power Manager
- `RaspApService.apk` — ? (Raspberry? Rear Audio Subsystem?)
- `RoadToVehicle.apk` — Road-to-Vehicle (comunicação externa?)
- `ScreenshotApService.apk` — Screenshot
- `StrgSW.apk` — Steering Wheel buttons
- `UsbCertApp.apk` — Certificação USB
- `VideoManagerApService.apk` — Video Manager
- `WhitelistApService.apk` — Whitelist do framework Mitsubishi

### 3.10 IME (teclados virtuais)

- `HangulKeyboard.apk` — Teclado coreano
- `HidKeyboard.apk` — Teclado HID (externo)
- `LatinIME.apk` — Teclado latino
- `PicoTts.apk` — Text-to-Speech
- `PinyinIME.apk` — Teclado chinês

### 3.11 SystemUpdate (crítico para EvilValet)

- `SystemUpdate.apk` — Gerencia atualizações via USB. Mostra a UI "Software update → Current Ver 1.F187.16 → New Ver IC1101 → Copying..." que vimos nas fotos do deploy.

## 4. Framework (/system/framework/)

Dump parcial em `tooling/apks-dumped/dump-0040/system-framework/` — 25MB. 48 arquivos .jar/.odex copiados. **Falta a parte Honda-específica** (symlinks que FAT32 não suporta):

- `HeaderService.jar/odex`
- `HondaNavigationLib.jar/odex`
- `HondaTelematicsLib.jar/odex`
- `UiLib.jar/odex` ← framework de UI do Mitsubishi, muito importante
- `WhitelistLib.jar/odex`
- `honda-framework.jar/odex` ← framework principal Honda
- `framework-res.apk` ← resources do framework

Para re-dumpar com symlinks resolvidos, modificar `build.py` para usar `busybox cp -L` (follow symlinks) ou copiar via `tar` dentro do updater-script.

### Framework JARs copiados (AOSP + Mitsubishi parcial)

```
am.jar, android.policy.jar, android.test.runner.jar, apache-xml.jar,
bmgr.jar, bouncycastle.jar, bu.jar, com.android.location.provider.jar,
com.google.widevine.software.drm.jar, content.jar, core.jar, core-junit.jar,
ext.jar, framework.jar, ime.jar, input.jar, javax.obex.jar, mms-common.jar,
monkey.jar, pm.jar, requestsync.jar, services.jar, settings.jar, svc.jar,
telephony-common.jar, uiautomator.jar
```

## 5. DaLauncher — detalhes importantes

### 5.1 Activities declaradas (via AndroidManifest.xml)

- `com.mitsubishielectric.ada.app.dalauncher.Launcher` — home screen principal
- `com.mitsubishielectric.ada.app.dalauncher.WallpaperChooser` — escolha de wallpaper
- `com.mitsubishielectric.ada.app.dalauncher.InfoClockActivity` — relógio info
- `com.mitsubishielectric.ada.app.dalauncher.InfoClockOpeningActivity` — abertura do relógio info
- `com.mitsubishielectric.ada.app.dalauncher.OpeningActivity` — abertura
- `com.mitsubishielectric.ada.app.dalauncher.InfoMenuActivity` — menu de info
- **`com.mitsubishielectric.ada.app.dalauncher.OpeningDivideActivity`** ← **monta o DisclaimerFragment (nosso alvo)**
- `com.mitsubishielectric.ada.app.dalauncher.ZibaInfoTopActivity` — Ziba Info Top

### 5.2 Layout do Aviso (`res/layout/mm_02_01_02.xml`)

Resolução: 800×480 (tela da central).

```xml
<AbsoluteLayout id="absoluteBaseLayout">
  <ImageView id="imageBgNoticeBlack"
             width="778" height="338" x="11" y="71" />  <!-- fundo preto -->

  <AbsoluteLayoutExtState id="btnChangeLanguage"
                          width="254" height="44" x="273" y="429" />  <!-- botão lingua (gone) -->

  <AbsoluteLayoutExtState id="btnOK"
                          width="354" height="44" x="223" y="328">
    <AutoAdjustTextView id="textOK"
                        width="288" height="38" x="33" y="3"
                        text="@string/STR_MM_02_01_02_RES_01" />  <!-- "OK" -->
  </AbsoluteLayoutExtState>

  <RelativeLayout width="672" height="165" x="64" y="148">
    <AutoAdjustTextView id="textMsgCenter"
                        text="@string/STR_MM_02_01_02_RES_04" />  <!-- texto do aviso -->
    <AutoAdjustTextView id="textMsgDefault"
                        text="@string/STR_MM_02_01_02_RES_04" />
  </RelativeLayout>

  <AutoAdjustTextView id="textWarningWording"
                      width="256" height="38" x="272" y="88"
                      text="@string/STR_MM_02_01_02_RES_05" />  <!-- "Aviso" título -->
</AbsoluteLayout>
```

**Botão OK:** retângulo com cantos superior esquerdo em (223, 328), tamanho 354×44.
- Canto superior esquerdo: (223, 328)
- Canto superior direito: (577, 328)
- Canto inferior esquerdo: (223, 372)
- Canto inferior direito: (577, 372)
- **Centro: (400, 350)**

Qualquer coordenada dentro desse retângulo deveria aceitar o tap. Escolhemos o centro para margem de erro máxima.

### 5.3 Strings do Aviso (res/values-pt/strings.xml)

```xml
<string name="STR_MM_02_01_02_RES_01">OK</string>
<string name="STR_MM_02_01_02_RES_04">"O motorista é o responsável pela condução ...</string>
<string name="STR_MM_02_01_02_RES_05">Aviso</string>
```

String RES_04 completa (truncada no grep) — texto principal do disclaimer "O motorista é o responsável pela condução..."

### 5.4 Idiomas suportados pelo DaLauncher

Pastas `res/values-<lang>/` encontradas:
`values, values-ar, values-bg, values-cs, values-da, values-de, values-el, values-en-rGB, values-en-rUS, values-es, values-es-rUS, values-fi, values-fr, values-fr-rCA, values-hr, values-hu, values-in, values-it, values-iw, values-ja, values-ko, values-land, values-lt, values-lv, values-ms, values-nb, values-nl, values-pl, values-pt, values-pt-rPT, values-ro, values-ru, values-sk, values-sl, values-sr, values-sv, values-th, values-tr, values-zh-rCN, values-zh-rTW`

Observação: `values-pt` (sem `-rBR`) é o idioma usado em Brasil. Mitsubishi não distingue PT-BR de PT genérico. `values-pt-rPT` é Portugal especificamente.

### 5.5 DisclaimerFragment internals

Classe: `com.mitsubishielectric.ada.app.dalauncher.DisclaimerFragment` (herda de `HomeBaseFragment`).

Inner classes:
- `DisclaimerFragment$1`, `$2`, `$3`, `$4`, `$5` — handlers/callbacks
- `DisclaimerFragment$StrgSwEventPriorityCallBackForDisclaimer` — callback de eventos do steering wheel
- `DisclaimerFragment$GetRunOperationControlAsyncTask` — AsyncTask que consulta `UnitInformationManagerApService.getRunOperationControl()` em background

Campos importantes:
- `mOkButton` — botão OK
- `mRunOperation` — Integer do run operation control (muda comportamento do fragment baseado em estado do veículo)
- `mChangeLanguageButton` — botão de troca de idioma

Interage com:
- `NavigationApService.disclaimerDisappeared()` — notifica navegação quando aviso some
- `SystemDisplayApService` — callbacks de brightness bar, off screen, touch events
- `AvApService` — callbacks pro diagnóstico

**Não há flag persistente para "disclaimer accepted"**. A decisão de mostrar ou não é dinâmica, baseada em estado do veículo + algum outro state que não identificamos.

## 6. Combos físicos conhecidos

| Combo | Duração | Resultado |
|---|---|---|
| `DAY/NIGHT + AUDIO + MENU` | 2s (áudio off) | Abre Service Mode Mitsubishi |
| **`AUDIO`** | **5s** | **"Quer reiniciar?" (cold boot forçado) ← CRÍTICO para EvilValet** |
| `HOME` sozinho | 10s | Sem efeito observado |
| Knob volume (clique longo) | 10-15s | Sem efeito observado |
| `AUDIO + MENU` | 5s | Sem efeito (só service mode se incluir DAY/NIGHT) |
| `AUDIO + BACK` | 5s | Sem efeito observado |
| `AUDIO + HOME` | 5s | Sem efeito observado |

**Virar a chave em ACC/ON ≠ cold boot.** Só acorda a central do suspend. BOOT_COMPLETED não dispara em apps 3rd party instalados em /system/app.

## 7. Fluxos de atualização descobertos

### 7.1 Fluxo `daupdater` (silencioso, aceita qualquer version string)

1. Boot da central (cold boot).
2. `libsurfaceflinger.so` executa `property_set("ctl.start", "daupdater")` no `startBootAnim`.
3. `/sbin/daupdater` inicia como serviço `oneshot`.
4. Verifica dev USB em `/sys/devices/platform/tegra-ehci.{0,1,2}/usb{3,1,2}/<n>-1`.
5. Checa `bInterfaceClass` == USB mass storage.
6. Checa `/dev/block/sda1` existe (até 15 tentativas, 1s sleep).
7. Monta `/dev/block/sda1` em `/mnt/usbdrive1` (vfat).
8. Procura `SwUpdate2.txt` (preferência) ou `SwUpdate.txt`.
9. Lê `cur_rom` de `/system/vendor/build.prop` (`custom_rom.type=`).
10. Procura `/mnt/usbdrive1/<cur_rom>/SwUpdate.mdt`.
11. Se encontra: valida version strings (`ro.build.id` do pacote vs HU), estaga `/cache/recovery/command` com `--update_package=...`, grava `/cache/recovery/version` com `<cur_da><new_da>`, reinicia para recovery.
12. Recovery valida assinatura (contra `/res/keys` que inclui testkey AOSP), executa `META-INF/com/google/android/update-binary` → updater-script.
13. Reboot normal.

### 7.2 Fluxo `SystemUpdate` (app-based, com UI "Software update → Copying")

1. Boot normal.
2. `SystemUpdateApService` detecta pendrive via `UnitInformationManagerApService`.
3. Lê `SwUpdate2.txt` do pendrive.
4. Mostra UI "Software update": Current Ver + New Ver + barra "Copying...".
5. Copia `SwUpdate.mdt` para `/data/.../copy/` interno + atualiza `/cache/.copy_complete`.
6. Dispara `ACTION_SWUPDATE_COMPLETE_NOTIFY` broadcast.
7. Agenda reboot (sem interação).
8. Reboot → daupdater pega o pacote do `/cache` interno → aplica como fluxo 7.1.

**Surpresa descoberta na safra BR:** `SystemUpdate` **aceita `NEW_DA_VERSION` sem prefix `1.F1`**. Nosso pacote usa `IC1101` (herdado do ic1101) e passou. Documentação do ic1101 (para safra 2021 US) dizia que SystemUpdate exigia `1.F1<X><YYY><Z>` strict. Isso parece ser difference BR vs US.

## 8. Recovery da nossa safra

Binários em `/sbin/` do recovery (confirmado via dump via logo processo):
- `adbd` — ADB daemon (não ativo, mas presente)
- `disp_com_cid` — Display Comms (vendor Honda)
- `earlyrvc` — Early Rear View Camera (câmera de ré antes do boot completo)
- `logcat_recovery` — logcat do recovery
- `logrotate_recovery` — rotacionador de logs
- `recovery` — binary principal
- `ueventd` — ueventd (link para /init)
- `watchdogd` — watchdog (link para /init)

**NÃO tem `/sbin/sh`, `/sbin/busybox`, `/sbin/toybox`.** Shell operations no recovery exigem embarcar busybox no pacote OTA (fazemos isso).

## 9. Hardware físico e sensores

### 9.1 Portas USB

- Porta frontal (dash) — a que o daupdater escaneia. Usar para OTA.
- Porta console central — não escaneada pelo daupdater (segundo docs ic1101).
- Porta embaixo do dash — pode existir para ADB/service. Não testamos.

### 9.2 Sinais B-CAN mapeados (de sessões anteriores — ver `docs/fase1-reconhecimento/`)

Lista de ~20 sinais semanticamente nomeados do CAN body (B-CAN) via Unit Check → CAN. Não vou duplicar aqui — ver `docs/fase1-reconhecimento/achados-2026-10-15-sessao2.md`.

### 9.3 Erros de hardware observados nos dumps

```
E DispComDMeter: disp_com_send_command_to_driver(314):serializer i2c ioctl error. errno = 121
```

I2C error no driver `disp_com_meter` — provavelmente erro de comunicação com algum componente (meter? painel?). Preexistente, não causado por nós.

```
E InputDispatcher: channel 'XXXX com.mitsubishielectric.ada.app.carplay/...' ~ Channel is unrecoverably broken
```

CarPlay channel crashes periódicos — comportamento preexistente da safra, provavelmente bug Mitsubishi conhecido. Não afeta funcionamento.

## 10. GPS/Localização

Via dumps:
- `GNSS` module: `TI` (Texas Instruments) based (`/3rdparty/ti/gnss/`).
- NMEA sentences processadas em `/dev/log_cycle/` com rotation.
- Capturamos coordenadas em `kmsgcat`: `<coords-redactadas>` → <cidade-redactada>. Confirmação da região <região-redactada>.

## 11. Sumário executivo

Para um dev chegar nessa central no futuro e ter que trabalhar:

1. **Rota de deploy sem brick:** EvilValet via pendrive + rom_type `0040` + updater-script com busybox embarcado + mount APP em /system via edify.
2. **Nome exato das pastas no pendrive:** `SwUpdate2.txt` + `0040/SwUpdate.mdt`.
3. **Combo pra forçar cold boot:** `AUDIO 5s` + confirmar "Reiniciar?".
4. **Resolução display:** 800×480.
5. **Botão OK do Aviso:** centro em (400, 350).
6. **Activity do Aviso:** `com.mitsubishielectric.ada.app.dalauncher.OpeningDivideActivity` (padrão logcat: `.../.OpeningDivideActivity`).
7. **Arquivo que persiste o rom_type:** `/system/vendor/build.prop` (`custom_rom.type=0040`).
8. **Partição `/system`:** `/dev/block/platform/sdhci-tegra.3/by-name/APP` (= mmcblk0p3). Monta `ro` no boot normal, pode remontar `rw` no recovery.
9. **Testkey AOSP aceita:** sim, confirmado. Fingerprint: `A4:0D:A8:0A:59:D1:70:CA:A9:50:CF:15:C1:8C:45:4D:47:A3:9B:26:98:9D:8B:64:0E:CD:74:5B:A7:1B:F5:DC`.
