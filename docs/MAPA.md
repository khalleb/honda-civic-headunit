# MAPA — Atlas da Central Honda Civic G10 BR

**Reflexo navegável do estado real da central multimídia (Honda Display Audio 7", Mitsubishi Andromeda, Tegra 3, Android 4.2.2).**

Última sincronização: `2026-10-19` (REA integrado + fluxo de deodex automatizado + validação da `OpeningDivideActivity` + análise completa da whitelist Mitsubishi + mapeamento do recovery pós-LP0 via `PowerManagerBroadcastSender` + **raio-x de superfície completo** da plataforma: 364 AIDLs, 445 broadcasts, 27 content authorities, 48 sysprops, 110 APKs mapeados).

---

## 0. Como usar este arquivo

**Para IA:** este é o **primeiro arquivo a ler** no início de qualquer sessão. Ele contém o reflexo navegável da central. Antes de pesquisar documentação, código ou tentar comandos: **consulte aqui primeiro**.

### 🔴 REGRA DE OURO — SALVAR TUDO IMPORTANTE AQUI

**Tudo que for descoberto, decidido ou aprendido sobre a central vai para este arquivo. Sem exceção. Antes de encerrar qualquer análise/mudança, atualizar o MAPA é obrigatório.**

Isso inclui, mas não se limita a:

| Tipo de descoberta | Onde registrar no MAPA |
|---|---|
| Novo nome de Activity, Service, Receiver, BroadcastAction | §11 (serviços + activities) |
| Nova partição ou mount point descoberto | §3 (partições) + §4 (mounts) |
| Novo arquivo relevante em alguma partição | §5 (filesystem map) |
| Novo binário / comando em /system/bin ou xbin | §9 (comandos) |
| Nova modificação feita por nós (APK, config, su) | §10 (nossas modificações) + §18 (timeline) |
| Novo cenário operacional (ex: câmera de ré, suspend, resume) | §11 ou §12 (pipeline) + §13 (fluxos) |
| Novo bug corrigido com causa raiz identificada | §17 (hall of fame) |
| Caminho avaliado e descartado | §16 (descartados) com motivo |
| Novo backup, dump ou artefato local | §15 (credenciais → backups essenciais) |
| Nova rota de deploy ou re-sincronização | §20 (comandos frequentes) |

**O MAPA deve ser mais fiel que a memória**. Se tiver dúvida entre "vale a pena salvar?" vs "é trivial", salve. Linhas a mais no MAPA são baratas; informação perdida é cara.

### Regras operacionais

- Quando **descobrir fato novo** sobre a central → atualizar aqui.
- Quando **modificar algo real** (APK, su, config) → atualizar aqui + timeline (§18).
- Quando **descartar/adiar algo** → registrar em §16 com motivo.
- Quando **resolver um bug chato** → registrar em §17 (causa raiz + fix).
- Quando **mudar um comportamento do APK** → atualizar §10 + §12 (pipeline).

**Como re-sincronizar:**
Rodar o pacote OTA de deep-scan no carro + script no PC:
```bash
# 1. Build + pendrive
python3 tooling/ota-build/build-deep-scan.py
sudo ./tooling/scripts/prepare-pendrive-deep-scan.sh /dev/sda
# 2. Carro: AUDIO 5s + confirmar reiniciar + aguardar ~10s
# 3. De volta ao PC:
python3 tooling/scripts/gen-mapa.py
```

**Legenda de status (usada em todas as tabelas):**
| Flag | Significado |
|---|---|
| ✓ | Analisado e documentado |
| 🔍 | Dumpado mas não analisado em profundidade |
| ✗ | Não dumpado / não investigado |
| 🔧 | Modificado por nós |
| ⏸ | Investigado e intencionalmente ignorado |
| ❓ | Desconhecido / incerto |
| 🎯 | Importante / próximo alvo |

---

## 1. Hardware

| Campo | Valor |
|---|---|
| Device code | `vcm30t30` |
| SoC | NVIDIA Tegra 3 (T30) |
| CPU | ARMv7 Cortex-A9, 4 cores, ~1.8GHz (BogoMIPS 1799.32) |
| CPU rev | ARMv7 Processor rev 9 (v7l), implementer 0x41, part 0xc09 |
| RAM | 988 MB (`MemTotal`) |
| Tela | 800×480 (deduzido pelas coords dos botões) |
| eMMC primária | mmcblk0 — 7.4 GB (7372800 blocos de 1KB) |
| eMMC secundária | mmcblk1 — 15.8 GB (❓ não investigada) |
| USB host | tegra-ehci.0 (porta frontal, usada pro pendrive OTA) |
| Serial do veículo | redactado — está em `/proc/cmdline` como `androidboot.serialno=` |
| Hardware signature | `vcm30t30` (`/proc/cpuinfo` Hardware) |
| Revision | 58c800 |

---

## 2. Firmware

| Campo | Valor | Fonte |
|---|---|---|
| Android version | 4.2.2 (API 17, Jelly Bean MR1) | `ro.build.version.release` |
| SDK | 17 | `ro.build.version.sdk` |
| Kernel | Linux 3.1.10+ #1 SMP PREEMPT Thu Apr 7 19:50:54 JST 2016 | `/proc/version` |
| Bootloader | `1.10_20160407183722` | kernel cmdline |
| DA version | **`1.F187.16`** | `ro.build.id` |
| Build incremental | 55 | `ro.build.version.incremental` |
| Build type | user, release-keys | `ro.build.type`, `ro.build.tags` |
| Build date | 2016-04-07 19:33:13 JST | `ro.build.date` |
| **rom_type** (EvilValet key) | **`0040`** | `/system/vendor/build.prop` (`custom_rom.type`) |
| custom_rom.id | `039726af3d8671c3855d21a9832e5214` | `/system/vendor/build.prop` |
| Fingerprint | `Honda/Andromeda/vcm30t30:4.2.2/1.F187.16/55:user/release-keys` | `ro.build.fingerprint` |
| Model | `MY16ADA` | `ro.product.model` |
| Device/board | `vcm30t30` / `Andromeda` | `ro.product.device` / `ro.product.board` |
| Manufacturer | `MITSUBISHI ELECTRIC` | `ro.product.manufacturer` |
| Brand | `Honda` | `ro.product.brand` |
| CPU ABI | `armeabi-v7a` + `armeabi` fallback | `ro.product.cpu.abi` |
| Characteristics | `tablet,nosdcard` | `ro.build.characteristics` |
| Locale default | en-US | `ro.product.locale.*` |
| OpenGL | 131072 (= OpenGL ES 2.0) | `ro.opengles.version` |
| WiFi | `wifi-only`, `wlan0` | `ro.carrier`, `wifi.interface` |
| Dalvik heap | start 5m, growth 48m, max 256m | `dalvik.vm.heap*` |
| da.car_model | `TBAA` | kernel cmdline |
| da.hwversion | `0xb` | kernel cmdline |

**Combo de cold boot (manual):**
Virar a chave do carro **NÃO** faz cold boot (sai do suspend). Para cold boot:
1. Segurar botão **AUDIO** por **5 segundos**
2. Diálogo "Quer reiniciar?" aparece → confirmar OK
3. Central reboota de verdade e `BOOT_COMPLETED` dispara + daupdater escaneia pendrive

---

## 3. Partições

### 3.1 eMMC primária — mmcblk0 (~7.2 GB)

| By-name | Block | Tamanho | FS | Mount runtime | Mount recovery | Status |
|---|---|---|---|---|---|---|
| CAC | mmcblk0p1 | 1024 MB | ext4 | `/cache` | `/cache` | 🔍 scan |
| CAP | mmcblk0p2 | 768 MB | ext4 | `/system/vendor` | `/system/vendor` | ✓ raw+scan+KB |
| APP | mmcblk0p3 | 512 MB | ext4 | `/system` | `/system` | ✓ raw+scan+KB |
| LOG | mmcblk0p4 | 128 MB | ext4 | `/log` | — | 🔍 scan |
| MITSU | mmcblk0p5 | 1024 MB | ext4 | `/data/MitsubishiElectric` | — | ✓ raw+scan |
| **SDA** | mmcblk0p6 | 128 MB | ext4 | **`/mnt/data1`** 🎯 | `/mnt/data1` | 🔍 scan — APKs pendente raw |
| SDA2 | mmcblk0p7 | 128 MB | ext4 | `/mnt/data2` | `/mnt/data2` | 🔍 scan (duplicata SDA) |
| SDC | mmcblk0p8 | 1024 MB | ext4 | `/mnt/media` | `/mnt/media` | 🔍 scan |
| UDA | mmcblk0p9 | 2432 MB | ext4 | `/data` | `/data` | 🔍 scan — contém packages.xml, autook.log |

**Fonte:** `recovery-fstab`, `/proc/partitions`, `/dev/block/platform/sdhci-tegra.3/by-name/`

### 3.2 eMMC secundária — mmcblk1 (~15 GB)

❓ Não investigada. Conhecida só pela listagem de `/proc/partitions` (15826944 blocos). Candidato: SD card interno pra conteúdo multimedia (música, etc.).

### 3.3 MTD (NOR flash, 64 MB total)

Fonte: `kernel cmdline` `mtdparts=tegra-nor:...`

| Partição | Offset | Tamanho | Mount recovery | Função |
|---|---|---|---|---|
| whole_device | 0K | 64 MB | — | Acesso total ao NOR |
| recovery | 4864K | 8 MB | `/recovery` | Imagem do recovery mode |
| boot | 13056K | 8 MB | `/boot` | **Contém ramdisk + init.rc + kernel** 🎯 |
| USP | 21504K | 2 MB | `/USP` | ❓ |
| app_datas | 23552K | 2 MB | `/app_datas` | ❓ |
| app_datas_ex | 25600K | 256 KB | `/app_datas_ex` | ❓ |
| kpanic | 61440K | 3 MB | `/kpanic` | Kernel panic log |
| misc | 59392K | 2 MB | `/misc` | Flags boot/recovery |

**IMPORTANTE:** `init.rc` **NÃO está em `/system/etc/init.rc`** (ao contrário do Android padrão). Ele mora no **ramdisk da partição `/boot` (MTD)**. Para extrair: dumpar MTD /boot via `dd if=/dev/mtd/mtd2` ou similar.

### 3.4 USB

| Device | Block | Mount recovery | Mount runtime | Função |
|---|---|---|---|---|
| sda | sda1 (vfat) | `/mnt/usbdrive1` | `/mnt/usbdrive1` | Pendrive OTA (porta frontal) |

Vold.fstab tem 3 slots de pendrive (`usbdrive1`, `usbdrive2`, `usbdrive3`) para portas diferentes do carro.

---

## 4. Mount points — runtime completo

| Mount point | Device | FS | Flags | Fonte |
|---|---|---|---|---|
| `/` | rootfs | rootfs | rw | boot |
| `/dev` | tmpfs | tmpfs | rw,nosuid,relatime,mode=755 | — |
| `/dev/pts` | devpts | devpts | rw,relatime,mode=600 | — |
| `/proc` | proc | proc | rw,relatime | — |
| `/sys` | sysfs | sysfs | rw,relatime | — |
| `/system` | APP (mmcblk0p3) | ext4 | rw,nodev,noatime,nodiratime,user_xattr,barrier=1,data=ordered | recovery-fstab |
| `/system/vendor` | CAP (mmcblk0p2) | ext4 | — | recovery-fstab |
| `/data` | UDA (mmcblk0p9) | ext4 | rw,nosuid,nodev,noatime,user_xattr,barrier=1,data=ordered | recovery-fstab |
| `/cache` | CAC (mmcblk0p1) | ext4 | rw,nosuid,nodev,noatime,user_xattr,barrier=1,data=ordered | recovery-fstab |
| `/log` | LOG (mmcblk0p4) | ext4 | — | recovery-fstab |
| `/data/MitsubishiElectric` | MITSU (mmcblk0p5) | ext4 | — | recovery-fstab |
| `/mnt/data1` | SDA (mmcblk0p6) | ext4 | — | recovery-fstab |
| `/mnt/data2` | SDA2 (mmcblk0p7) | ext4 | — | recovery-fstab |
| `/mnt/media` | SDC (mmcblk0p8) | ext4 | — | recovery-fstab |
| `/mnt/usbdrive1` | sda1 | vfat | rw,relatime,fmask=0077,dmask=0077,shortname=mixed,errors=remount-ro | vold.fstab + daupdater |
| `/storage/sdcard1` | mmc2/auto | — | — | vold.fstab |
| `/sdcard` | mmcblk1 (?) | vfat | — | recovery-fstab |

---

## 5. Filesystem map

### 5.1 `/system/` (APP, 512 MB)

```
/system/
├── bin/              — Comandos nativos (~250 arquivos). Ver §9.
├── xbin/             — su (NOSSO), dexdump, rfcomm, sqlite3. Só 4 arquivos.
├── lib/              — Libs .so do Android base
├── fonts/            — Fontes do sistema
├── framework/        — jars do Android AOSP (am.jar, framework.jar, etc.)
├── vendor/           — SYMLINK ou mount? É mount (CAP). Ver §5.2.
├── app/              — 42 APKs (ver §6)
├── media/            — Boot animation, sounds
├── usr/              — i18n data, keychars, keylayouts
├── etc/
│   ├── permissions/            — platform.xml, com.*.lib.xml (API routing)
│   ├── security/               — Certificates (otacerts.zip, cacerts/)
│   ├── init.goldfish.sh        — Script init (não init.rc!)
│   ├── install-recovery.sh     — Instala recovery no boot
│   ├── vold.fstab              — Config dinâmica de mounts (USB, SD)
│   ├── dbus.conf               — D-Bus system config
│   ├── fallback_fonts.xml      — Fallback fonts
│   ├── media_codecs.xml        — Codec availability
│   ├── media_profiles.xml      — Media profiles
│   ├── audio_effects.conf      — Audio effects config
│   ├── audio_policy.conf       — Audio policy routing
│   ├── bluetooth/              — Bluetooth config
│   ├── dhcpcd/                 — DHCP client config
│   ├── firmware/               — Firmware blobs (NFC, GPS, etc.)
│   ├── gnss/                   — GPS/GLONASS config
│   ├── nvcamera.conf           — NVIDIA camera config
│   ├── nvaudio_conf.xml        — NVIDIA audio
│   ├── airplay.conf            — AirPlay
│   ├── asound.conf             — ALSA
│   ├── mkshrc                  — Shell rc
│   ├── system_fonts.xml        — System fonts
│   └── wifi/                   — WiFi config
├── build.prop                  — ✓ Properties do sistema
├── recovery-from-boot.p        — Patch do recovery
└── custom                      — ❓ (3864 bytes)
```

### 5.2 `/system/vendor/` (CAP, 768 MB)

```
/system/vendor/
├── app/              — 78 APKs Mitsubishi+Honda (ver §7)
├── framework/        — 104 jars/odex libs Honda/Mitsubishi (ver §8)
│                       Inclui UiLib, honda-framework, HondaNavigationLib, 
│                       HondaTelematicsLib, HeaderService, WhitelistLib, 
│                       framework-res.apk (39MB)
├── bin/              — Binaries vendor-specific
├── lib/              — Libraries .so vendor
├── etc/
│   └── honda/        — Marcadores de APKs: com.honda.*.apk, .ver, .dst
│                       (telematics core apk real está aqui, 4.5MB)
├── media/            — Vendor media
└── build.prop        — ✓ custom_rom.type=0040
```

### 5.3 `/data/` (UDA, 2.4 GB)

```
/data/
├── app-lib/                                  — Native libs dos apps instalados
│   ├── AutoOk/                               — 🔧 Nosso APK
│   ├── com.honda.displayaudio.navi/
│   └── com.honda.displayaudio.whitelist/
├── data/                                     — 98 pastas, uma por package
│   ├── com.khalleb.civichmi.autook/          — 🔧 Nosso APK runtime data
│   │   └── files/
│   │       ├── autook.log                    — 🔧 Nosso log persistente
│   │       └── autook.log.1                  — 🔧 Rotação (sessão anterior)
│   ├── com.mitsubishielectric.ada.app.dalauncher/
│   │   └── shared_prefs/com.mitsubishielectric.ada.app.dalauncher.prefs.xml
│   └── com.* (todos os apps instalados)
├── system/
│   ├── packages.xml                          — ✓ Registro de todos os packages (74 KB)
│   ├── packages.list                         — ✓ uid/path (98 linhas)
│   ├── users/                                — User system info
│   └── ...
├── anr/
│   └── traces.txt                            — ✓ Crashes/ANRs recentes (579 KB)
├── local/tmp/                                — Vazio (dir shell:shell, 0771)
├── MitsubishiElectric/                       — Mount de MITSU (mmcblk0p5)
└── ...
```

### 5.4 `/mnt/data1/` (SDA, 128 MB) 🎯

```
/mnt/data1/
├── com.honda/
│   ├── com.honda.displayaudio.navi.apk       — ✓ 14.8 MB (APK real)
│   ├── com.honda.displayaudio.navi/
│   │   └── libNaviApk.so                     — 39.5 MB (biblioteca nativa)
│   ├── com.honda.displayaudio.whitelist.apk  — SYMLINK → /vendor/etc/honda/
│   ├── com.honda.displayaudio.whitelist/
│   └── com.honda.displayaudio.whitelist.ver
├── com.mitsubishielectric.ada.appservice.camera/   — User data
├── com.mitsubishielectric.ada.appservice.navigation/
├── com.mitsubishielectric.ada.appservice.unitinfomanager/
├── com.mitsubishielectric.ada.framework.vehicledbmanager/
├── Aginglog.log                              — 59 bytes
├── edid.txt                                  — Monitor EDID
└── lost+found/
```

**Nota:** `com.aha.android.app.apk`, `com.honda.telematics.core.apk`, `com.yesway.ycarstore.acura.apk` **são symlinks em CAP** pra `/mnt/data1/com.honda/<nome>.apk` mas o arquivo real **não existe** aqui. Esses APKs não estão instalados nessa safra BR (safras US/Acura).

### 5.5 `/mnt/data2/` (SDA2, 128 MB)

Duplicata quase idêntica de SDA. Mesmas pastas `com.honda/`, mesmas de serviço. Função provável: slot A/B pra OTA de updates do navi.

### 5.6 `/mnt/media/` (SDC, 1 GB)

Pasta `/0/Download/` com um `YouTube_v14.42.54_apkpure.com.apk` esquecido lá (não instalado, provavelmente teste do dono anterior).

### 5.7 `/data/MitsubishiElectric/` (MITSU, 1 GB)

```
/data/MitsubishiElectric/
├── ada/                                      — Dados Mitsubishi (Andromeda) 
│   ├── automotive-fw/
│   └── VoicePortal/
├── artwork-1.jpg                             — ❓
└── ...
```

Partição exclusiva da safra BR (não aparece em safras US).

---

## 6. APKs do `/system/app/` (42 total)

42 APKs — AOSP padrão + **nosso AutoOk.apk**.

| APK | Package | Função |
|---|---|---|
| **AutoOk.apk** | **com.khalleb.civichmi.autook** 🔧 | **Nosso APK — dispensa aviso automaticamente** |
| ApplicationsProvider.apk | com.android.providers.applications | Provider de lista de apps |
| BackupRestoreConfirmation.apk | com.android.backupconfirm | Backup/restore UI |
| Browser.apk | com.android.browser | Browser web |
| Calculator.apk | com.android.calculator2 | Calculadora |
| Calendar.apk | com.android.calendar | Calendário |
| CalendarProvider.apk | com.android.providers.calendar | Provider calendário |
| CertInstaller.apk | com.android.certinstaller | Instalador de certificados |
| Contacts.apk | com.android.contacts | Contatos |
| ContactsProvider.apk | com.android.providers.contacts | Provider contatos |
| DefaultContainerService.apk | com.android.defcontainer | Instalação de APKs |
| DeskClock.apk | com.android.deskclock | Relógio |
| DownloadProvider.apk | com.android.providers.downloads | Provider downloads |
| DownloadProviderUi.apk | com.android.providers.downloads.ui | UI downloads |
| DrmProvider.apk | com.android.providers.drm | DRM provider |
| framework-res.apk | android | Resources base do framework |
| FusedLocation.apk | com.android.location.fused | Localização fusionada |
| Galaxy4.apk | com.android.galaxy4 | Live wallpaper |
| Gallery2.apk | com.android.gallery3d | Galeria de fotos |
| HoloSpiralWallpaper.apk | com.android.wallpaper.holospiral | Live wallpaper |
| HTMLViewer.apk | com.android.htmlviewer | Viewer HTML |
| InputDevices.apk | com.android.inputdevices | Input devices |
| KeyChain.apk | com.android.keychain | KeyChain |
| LiveWallpapers.apk | com.android.wallpaper | Live wallpapers |
| LiveWallpapersPicker.apk | com.android.wallpaper.livepicker | Picker |
| MagicSmokeWallpapers.apk | com.android.magicsmoke | Live wallpaper |
| MediaProvider.apk | com.android.providers.media | Provider mídia |
| Music.apk | com.android.music | Música |
| MusicFX.apk | com.android.musicfx | Equalizer |
| NoiseField.apk | com.android.noisefield | Live wallpaper |
| PackageInstaller.apk | com.android.packageinstaller | Instalador |
| PhaseBeam.apk | com.android.phasebeam | Live wallpaper |
| Phone.apk | com.android.phone | Phone app |
| Provision.apk | com.android.provision | First-boot setup |
| QuickSearchBox.apk | com.android.quicksearchbox | Search |
| Settings.apk | com.android.settings | Settings |
| SettingsProvider.apk | com.android.providers.settings | Settings provider |
| SharedStorageBackup.apk | com.android.sharedstoragebackup | Backup |
| SystemUI.apk | com.android.systemui | Status bar, notifications |
| TelephonyProvider.apk | com.android.providers.telephony | Telefonia provider |
| UserDictionaryProvider.apk | com.android.providers.userdictionary | Dicionário |
| VpnDialogs.apk | com.android.vpndialogs | VPN dialogs |

---

## 7. APKs do `/system/vendor/app/` (78 total)

> ⚠️ **Toda a vendor-app é odex-only (pre-dexed).** Cada APK aqui vem **sem `classes.dex`** — o bytecode está no `.odex` ao lado (ex: `DaLauncher.apk` + `DaLauncher.odex`). JADX/apktool/REA só enxergam o manifest e os resources até esse `.odex` ser transformado em `classes.dex` e re-injetado no APK. Pipeline automatizado em [`tooling/deodex/deodex-apk.sh`](../tooling/deodex/deodex-apk.sh) (ver §20.8). O mesmo vale para `/system/app/`.

| APK | Package | Função |
|---|---|---|
| **DaLauncher.apk** 🎯 | com.mitsubishielectric.ada.app.dalauncher | **Launcher principal + OpeningDivideActivity (aviso)** |
| AcuraLinkApp.apk | com.mitsubishielectric.ada.app.acuralink | Acura Link (safra US, inativo aqui) |
| AcuraLinkApService.apk | com.mitsubishielectric.ada.appservice.acuralink | Service AcuraLink |
| AirCon.apk | com.mitsubishielectric.ada.app.aircon | Ar condicionado |
| AndroidAuto.apk | com.mitsubishielectric.ada.app.androidauto | Android Auto UI |
| AntiTheft.apk | com.mitsubishielectric.ada.app.antitheft | Antifurto |
| AppManager.apk | - | Gerenciador de apps |
| AppMode.apk | com.mitsubishielectric.ada.app.appmode | App mode selector |
| AppModeApService.apk | com.mitsubishielectric.ada.appservice.appmodeapservice | Service app mode |
| AV.apk | — | Áudio/Vídeo |
| AVPlayer.apk | com.mitsubishielectric.ada.app.avplayer | Reprodutor A/V |
| Camera.apk | com.mitsubishielectric.ada.app.camera | Câmera de ré |
| CameraAPService.apk | com.mitsubishielectric.ada.appservice.camera | Service câmera |
| **CarPlay.apk** | com.mitsubishielectric.ada.app.carplay | **CarPlay app** |
| CarPlayService.apk | com.mitsubishielectric.ada.appservice.carplayapservice | Service CarPlay |
| ClockSync.apk | com.mitsubishielectric.ada.appservice.clocksync | Sincronização de relógio |
| CompassService.apk | com.mitsubishielectric.ada.appservice.compassservice | Bússola |
| CpuComService.apk | com.mitsubishielectric.ada.framework.cpucomservice | CPU communication |
| DaSettings.apk | com.mitsubishielectric.ada.app.dasettings | Configurações |
| DealerDiag.apk | com.mitsubishielectric.ada.app.dealerdiag | Diagnóstico (Error History!) |
| DeveloperDiag.apk | com.mitsubishielectric.ada.app.developerdiag | Diag developer |
| DiagApService.apk | com.mitsubishielectric.ada.appservice.diag | Diag service |
| EcoTripComputer.apk | com.mitsubishielectric.ada.app.ecotripcomputer | Eco trip |
| EmergencyApp.apk | com.mitsubishielectric.ada.app.emergency | Emergência |
| EmergencyApService.apk | com.mitsubishielectric.ada.appservice.emergency | Service emergência |
| EnergyManagement.apk | com.mitsubishielectric.ada.app.energymanagement | Gestão de energia |
| ErrorManager.apk | com.mitsubishielectric.ada.appservice.errormanager | Error manager |
| ETC.apk | com.mitsubishielectric.ada.app.etc | ETC |
| ExternalDisplayApService.apk | com.mitsubishielectric.ada.appservice.externaldisplay | Display externo |
| ExternalDisplayOutService.apk | — | Display out |
| FileManager.apk | com.mitsubishielectric.ada.app.filemanager | File manager |
| framework-res.apk | — | Resources vendor framework |
| HangulKeyboard.apk | org.kandroid.app.hangulkeyboard | Teclado Hangul (coreano) |
| HftApp.apk | com.mitsubishielectric.ada.app.hft | Hands-free telephony |
| HftApService.apk | com.mitsubishielectric.ada.appservice.hft | Service HFT |
| HidKeyboard.apk | com.mitsubishielectric.ada.app.hidkeyboard | Teclado HID |
| HudApService.apk | com.mitsubishielectric.ada.appservice.hudapservice | HUD service |
| LatinIME.apk | com.android.inputmethod.latin | IME Latin |
| LetDiag.apk | com.mitsubishielectric.ada.app.letdiag | Diag |
| LinkManagerApService.apk | com.mitsubishielectric.ada.appservice.linkmanager | Link manager |
| MediaCoreService.apk | com.mitsubishielectric.ada.framework.mcservice | Media core |
| MirrorLink.apk | com.mitsubishielectric.ada.app.mirrorlink | MirrorLink |
| Navigation.apk | com.mitsubishielectric.ada.appservice.navigation | Navegação |
| PhoneCoordination.apk | com.mitsubishielectric.ada.appservice.phonecoordination | Phone coord |
| PicoTts.apk | com.svox.pico | Text-to-speech |
| PinyinIME.apk | com.android.inputmethod.pinyin | IME Pinyin (chinês) |
| PowerManagerApService.apk | com.mitsubishielectric.ada.appservice.powermanager | Power |
| PreShipmentDiag.apk | com.mitsubishielectric.ada.app.preshipmentdiag | Pre-shipment diag |
| RaspApService.apk | com.mitsubishielectric.ada.appservice.raspapservice | ❓ |
| RoadToVehicle.apk | com.mitsubishielectric.ada.appservice.roadtovehicle | Road-to-vehicle |
| ScreenshotApService.apk | com.mitsubishielectric.ada.appservice.screenshot | Screenshots |
| SensorMonitor.apk | com.mitsubishielectric.ada.appservice.sensormonitor | Sensors |
| SiriEFM.apk | com.mitsubishielectric.ada.appservice.siriefm | Siri Eyes Free Mode |
| StrgSW.apk | com.mitsubishielectric.ada.appservice.strgsw | Steering wheel switches |
| SystemInfoService.apk | com.mitsubishielectric.ada.app.systeminfoservice | System info |
| **SystemUpdate.apk** | com.mitsubishielectric.ada.app.systemupdate | **Fluxo OTA (EvilValet target)** |
| **WhitelistApService.apk** 🎯 | com.mitsubishielectric.ada.appservice.whitelist | **Whitelist Mitsubishi — UX de instalação de apps, NÃO afeta LP0.** Detalhes completos em [`docs/whitelist-mitsubishi-2026-10-19.md`](whitelist-mitsubishi-2026-10-19.md) e §11.7 abaixo. |
| TaskManager.apk | com.mitsubishielectric.ada.app.taskmanager | Task manager |
| Telematics.apk | com.mitsubishielectric.ada.appservice.telematics | Telematics |
| UnitInfoManager.apk | com.mitsubishielectric.ada.appservice.unitinfomanager | Unit info |
| UsbCertApp.apk | com.mitsubishielectric.ada.app.usbcert | USB cert |
| VehicleCoordination.apk | com.mitsubishielectric.ada.appservice.vehiclecoordination | Vehicle coord |
| VehicleDbManager.apk | com.mitsubishielectric.ada.framework.vehicledbmanager | Vehicle DB |
| VehicleInfoManager.apk | com.mitsubishielectric.ada.appservice.vehicleinfomanager | Vehicle info |
| VehicleRW.apk | com.mitsubishielectric.ada.util.vehiclerw | Vehicle RW |
| VideoManagerApService.apk | com.mitsubishielectric.ada.appservice.videomanager | Video manager |
| VoicePortal.apk | com.mitsubishielectric.ada.app.voiceportal | Voice portal |
| VoicePortalAp.apk | com.mitsubishielectric.ada.appservice.voiceportalap | Voice service |
| VRSD.apk | com.mitsubishielectric.ada.framework.speech.vrsd | Voice recognition |
| WifiApp.apk | com.mitsubishielectric.ada.app.wifi | WiFi settings |
| WifiApService.apk | com.mitsubishielectric.ada.appservice.wifi | WiFi service |

**APKs com nome `com.*.apk` (symlinks pra /mnt/data1):**
- com.aha.android.app.apk → **symlink quebrado** (não existe, safra US)
- com.honda.displayaudio.navi.apk → /mnt/data1/com.honda/com.honda.displayaudio.navi.apk (14.8 MB ✓)
- com.honda.displayaudio.whitelist.apk → /system/vendor/etc/honda/com.honda.displayaudio.whitelist.apk (14 KB ✓)
- com.honda.telematics.core.apk → /system/vendor/etc/honda/com.honda.telematics.core.apk (4.5 MB ✓)
- com.yesway.ycarstore.acura.apk → **symlink quebrado** (safra Acura)

---

## 8. Vendor framework libraries — `/system/vendor/framework/` (104 arquivos, 44 MB)

Libs Honda/Mitsubishi — **esqueleto do framework proprietário**.

**Dumpadas localmente em** `tooling/apks-dumped/dump-0040/vendor-framework/` (via debugfs do cap.img).

Libs chave:
- **honda-framework.jar/.odex** — API Honda principal
- **HondaNavigationLib.jar/.odex** — API navegação
- **HondaNavigationNaviLib.jar/.odex** — Navi mais específico
- **HondaTelematicsLib.jar/.odex** — Telematics
- **HeaderService.jar/.odex** — Header de serviços
- **UiLib.jar/.odex** — UI widgets Mitsubishi
- **WhitelistLib.jar/.odex** — API whitelist
- **framework-res.apk** (39 MB) — Resources vendor framework
- **AppManagerServiceLib** — Automotive activity manager (!)
- **AcuraLinkApServiceLib**, **CarPlayApServiceApiLib**, **DiagServiceLib**, **TelematicsLib**, **VehicleCoordinationLib**, etc. — libs dos services

52 pares `.jar + .odex`.

---

## 9. Comandos binários disponíveis

### 9.1 `/system/bin/` (~250 binários, Android AOSP)

Comandos **relevantes pra deploy, debug, e scripting** (todos presentes ✓):

| Comando | Caminho | Função | Nosso uso |
|---|---|---|---|
| **su** | `/system/xbin/su` 🔧 | Setuid root (nosso) | Pipeline AutoOk |
| **logcat** | `/system/bin/logcat` | Logs do sistema | LogcatWatcher.consume |
| **input** | `/system/bin/input` | Simular toques | `input tap X Y` do AutoOk |
| **am** | `/system/bin/am` | Activity manager (start/stop/broadcast) | Debug |
| **pm** | `/system/bin/pm` | Package manager (list, install, uninstall) | Debug |
| **dumpsys** | `/system/bin/dumpsys` | Dump de services | Debug profundo |
| **getprop** | `/system/bin/getprop` | Ler system properties | Debug |
| **settings** | `/system/bin/settings` | Settings DB (system/secure/global) | Debug |
| **service** | `/system/bin/service` | Chama binder services | Avançado |
| **screencap** | `/system/bin/screencap` | Screenshot | Debug UI |
| **monkey** | `/system/bin/monkey` | Fuzzing | — |
| **toolbox** | `/system/bin/toolbox` | Multi-command (cat, chmod, cp, ls, etc.) | — |
| **adb** | `/system/bin/adb` | adbd daemon (não cliente adb!) | Potencial debug |
| **app_process** | `/system/bin/app_process` | Zygote (target do Xposed) | ⏸ |
| **bootanimation** | `/system/bin/bootanimation` | Boot animation | — |
| **dalvikvm** | `/system/bin/dalvikvm` | Dalvik VM standalone | — |
| **sqlite3** | `/system/xbin/sqlite3` | SQLite CLI | Debug databases |
| **dexdump** | `/system/xbin/dexdump` | Dump de DEX | RE profundo |

### 9.2 Toolbox symlinks

Vários comandos `/system/bin/*` são symlinks pra `/system/bin/toolbox`:
cat, chmod, chown, cmp, cp, date, getprop, ...

---

## 10. Nossas modificações (🔧)

### 10.1 `/system/app/AutoOk.apk` 🔧

Nosso APK — dispensa automaticamente o aviso de abertura.

| Campo | Valor |
|---|---|
| Package | `com.khalleb.civichmi.autook` |
| Instalado em | `/system/app/AutoOk.apk` |
| Versão atual | **9** (v0.5.4) ✓ validado no carro 2026-10-20 (mudo CarPlay + LP0 resume; baseline estável, ver §17.15) |
| Tamanho | ~17 KB |
| User ID | 10091 |
| Native lib dir | `/data/app-lib/AutoOk/` |
| Data dir | `/data/data/com.khalleb.civichmi.autook/` |
| Log persistente | `/data/data/com.khalleb.civichmi.autook/files/autook.log` ✓ existe |
| Log rotation | `.log.1` por sessão de boot ✓ existe |
| Signing | debug keystore (Android Debug cert, SHA-256 `9505deb0b0d8c53178eaade253eee94e1a31f0e6a1dde2b809752914b644cf02`) |
| Source | `our-apk/` do repositório |

**Classes:**
- `BootReceiver` — ouve `BOOT_COMPLETED`, inicia `AutoOkService`
- `HmiServiceReceiver` — ouve `com.mitsubishielectric.ada.appservice.powermanager.ACTION_HMI_SERVICE_START`, dispara `ACTION_FORCE_RESTART` no Service. Fundamental em cada exit de LP0 (câmera de ré, abertura de porta, acordar do suspend).
- `AutoOkService` — Service persistente (START_STICKY). Monta watcher, watchdog, rearm. `forceRestartWatcher()` mata/recria o watcher (quebra thread bloqueado em `readLine()` após LP0), mas **reusa o watcher se ainda estiver vivo** (lição 17.9: recriar à toa trazia EPERM de volta).
- `LogcatWatcher` — Thread que lê `logcat -b events -v threadtime am_create_activity:I am_new_intent:I *:S` via `su`, procura needle. Roda em loop infinito desde v0.3.0 (não é destruído entre taps; sem `logcat -c`, por isso relê o buffer `events` ao recriar).
- `AvisoMatcher` — lógica pura do match (needle + `NORMAL_STARTUP` + `am_create_activity`/`am_new_intent`), testada em JVM.
- `TapDeduper` — lógica pura do dedup temporal (janela de 3s), testada em JVM.
- `Shell` — Wrapper de `Runtime.exec("su")` + `suTapWithFallback`
- `FileLogger` — Grava `/data/data/.../files/autook.log` com rotação por sessão

> **v0.5.0 removeu o `AlarmManager`/`AlarmReceiver`** que a v0.4.0 tinha como fallback de 60s (ver §17.15). A permissão `WAKE_LOCK` continua declarada no manifesto, mas sem uso ativo depois disso.

**Permissions declaradas:**
- `RECEIVE_BOOT_COMPLETED` (boot)
- `WAKE_LOCK` (declarada desde v0.4.0; sem uso ativo depois que a v0.5.0 tirou o AlarmManager)

**Config atual** (`AutoOkConfig.java`, v0.5.4):
```java
AVISO_ACTIVITY_NAME = "com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity"
BUTTON_OK_X = 400, BUTTON_OK_Y = 350
TAP_FALLBACK_COORDS = {(400,350), (400,340), (400,360)}
TAP_FALLBACK_INTERVAL_MS = 200
DELAY_SECONDS_AFTER_DETECT = 1
REARM_DELAY_SECONDS = 2
BOOT_INITIAL_WAIT_MS = 500
WATCHDOG_INTERVAL_SECONDS = 30
TAP_DEDUP_SECONDS = 3
HMI_SERVICE_START_ACTION = "com.mitsubishielectric.ada.appservice.powermanager.ACTION_HMI_SERVICE_START"
ACTION_FORCE_RESTART = "com.khalleb.civichmi.autook.FORCE_RESTART"
// Needle: am_create_activity (cold boot) OU am_new_intent (LP0 resume) + OpeningDivideActivity + NORMAL_STARTUP
```

### 10.2 `/system/xbin/su` 🔧

Setuid root ARM. Vindo do `codeage/root-honda`.

| Campo | Valor |
|---|---|
| Caminho | `/system/xbin/su` |
| Tamanho | 133472 bytes |
| SHA-256 | `4f399ccd4c53bf1a12cbcc7f1b2bd23354491111358937c2da51d3355333fa84` |
| Modo | `06755` (`-rwsr-sr-x`) |
| Owner | root:root |
| Comportamento | Sem prompt — qualquer app que chamar vira root direto |

**⚠ O binário é KingoSU, não SuperSU** (descoberto em 2026-10-27 via auditoria externa [`joshfng/root-honda` AUDIT.md](https://github.com/joshfng/root-honda/blob/main/AUDIT.md)). Confirmado em `tooling/ota-build/bin/su`: strings `--- KingoSU notice ---`, `KingoSU v%d.%s%d Copyright (C) 2012-2015 - KingoSu`, paths em `/data/data/com.kingouser.com/`. A cada chamada de `su`, dispara `am broadcast -a com.kingouser.com.NativeAccess -n com.kingouser.com/.NativeAccessReceiver` com UID/comando. O manager `com.kingouser.com` **não** está instalado, então o broadcast é no-op público — mas aparece no `logcat.events`. Impacto operacional em prod é zero (o AutoOk v0.5.4 roda estável). Substituição pelo `su` Chainfire SR1 (SHA `67e4d251…`) pendente para o próximo rebuild do AutoOk. Detalhes em [`raio-x/08-github-landscape-2026-10-27.md §4`](raio-x/08-github-landscape-2026-10-27.md).

### 10.3 `/system/vendor/app/DaLauncher.apk` 🔧 (patcheado — Fase 10, 2026-10-29)

Substituído pelo APK rebuildado em `tooling/fase10/output/DaLauncher-fase10.apk`, deployado via `tooling/ota-build/output-dalauncher-fase10/`. **Única mudança em arquivo preexistente de /system no projeto.**

| Campo | Fase 10 v1 (deployada 2026-10-29) | Fase 10.1 (preparada 2026-10-29) |
|---|---|---|
| APK SHA-256 | `1774136cfad10919eb03698badc259179521e5fe7e69b82fc349029aaceb1807` | `65481d45acd01ad67359b1174b57150eecb959377bde3379a30e2eb17a8d4a4c` |
| md5 (gate §2.2) | `fc8e87f6bba2713c0703f6b9d37a29cf` | `655c01a3b17fe20b23c70114e1e0dae7` |
| `.odex` original | **removido** (deploy força `test ! -e DaLauncher.odex`, grava `FASE10-ODEX-REMOVED.OK`) | idem |
| Assinatura | testkey AOSP (`a40da80a…`), **não** a Mitsubishi `Melco Honda16MY` original | idem |
| Patch(es) smali | `OpeningDivideActivity.smali:671` (pula o `DisclaimerFragment`) | 2 patches: o anterior + `EcoFragment.smali:3094` (timer 5000ms → 500ms) |

**Patches versionados:**
- `tooling/fase10/opening-divide-activity-skip-disclaimer.patch`
- `tooling/fase10/eco-fragment-reduce-timer.patch`

**Rebuild:** `tooling/fase10/rebuild-dalauncher.sh` deodexa o `.odex` original fresh, aplica os dois patches, prova que só `EcoFragment.smali` + `OpeningDivideActivity.smali` mudam no DEX, zipaligna e assina com testkey AOSP. Falha se qualquer outra classe aparecer na diff do bytecode orig→patch.

**Rollback (restaura o DaLauncher original):** `tooling/ota-build/output-dalauncher-restore/20261027T020209Z/` (SHA `6445ec80…`). O APK e o `.odex` do dump original (`tooling/apks-dumped/dump-0040/vendor-app/DaLauncher.{apk,odex}`) são escritos de volta com md5 verificado pós-restore.

Comportamento esperado: aviso de abertura **não aparece**, tela "-eco-" aparece por ~1 s (Fase 10.1) ou ~6 s (v1), launcher sobe normal, CarPlay projeta, navegação funciona. Detalhes em §16.4 e §17.19.

### 10.4 Deploy — EvilValet OTA

Caminho pra qualquer modificação adicional: pacote OTA assinado com testkey AOSP, aceito pelo daupdater via pendrive.

Pacotes OTA do repositório:
- `tooling/ota-build/build.py` — install AutoOk.apk + su
- `tooling/ota-build/build-rollback.py` — remove AutoOk.apk + su (volta ao estado inicial)
- `tooling/ota-build/build-dump-raw.py` — dump raw bootable de APP, CAP, MITSU
- `tooling/ota-build/build-deep-scan.py` — scan textual de todas as partições + /proc/*

---

## 11. Services + Activities monitoradas

### 11.1 OpeningDivideActivity (aviso) 🎯

| Campo | Valor |
|---|---|
| Package | `com.mitsubishielectric.ada.app.dalauncher` |
| Component | `/.OpeningDivideActivity` |
| Needle completo | `com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity` |
| Fragment interno | `DisclaimerFragment` |
| Layout botão OK | `mm_02_01_02.xml` |
| Coord botão OK | X=400, Y=350 (tela 800×480) |
| Timing aparição | ~2-3s após `BOOT_COMPLETED` |
| Comportamento sem AutoOk | Aguarda tap humano no "OK" para liberar launcher |
| Comportamento com AutoOk v0.3.0 | Tap automático em ~2.5s após detect, aviso some |

### 11.1.1 Internals da `OpeningDivideActivity` (confirmado via REA + jadx, 2026-10-19)

Após deodex do `DaLauncher.apk` (ver §20.8), o REA (`inspect-android-class` + `trace-android-references` + `inspect-android-method`) devolveu:

- Herda de `HomeBaseActivity`.
- Layout: `R.layout.opening_divide` (não `mm_02_01_02.xml` — este é só o botão interno do `DisclaimerFragment`).
- 19 fields e 37 métodos. Os reveladores: `createOpeningIntent`, `createCSFIntent`, `createDisclaimerOnHomeIntent`, `createDisclaimerOrEcoIntent`, `createEcoIntent`, `createAntiTheftIntent`, `startNextActivity`, `antiTheftUnlockScreenTransition`, `onHMIServiceReceive`.
- 6 inner classes (5 anônimas + `HMIServiceReceiver`).

**`onCreate` (decompilação JADX):**
```java
protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    ExpLog.enter("");
    ExpLog.callApi("onCreate");
    getWindow().addFlags(1024);
    setDaThemeTranslucent(true);
    setDaContentView(R.layout.opening_divide);
    findViewById(R.id.absoluteBaseLayout);
    ExpLog.exit("");
}
```

**14 classes a referenciam** (`trace-android-references`). O lançador real do aviso no boot é **`com.mitsubishielectric.ada.app.dalauncher.Launcher.HMIServiceReceiver`**: ao receber `ACTION_HMI_SERVICE_START` do PowerManager (§11.6), ele dispara a Activity. As demais referências são colaterais: `CSFFragment`, `DisclaimerFragment` (+ 3 inners), `EcoFragment` (+ 2 inners), `HomeBaseFragment`, `HmiBroadcastReceiver`, `OpeningActivity`, e a própria `OpeningDivideActivity.HMIServiceReceiver`.

**Sequência pós-aviso e `DISCLAIMER_COMPLETE` (smali do DaLauncher deodexado, 2026-10-26).** A action `com.mitsubishielectric.ada.app.dalauncher.action.DISCLAIMER_COMPLETE` é enviada em quatro métodos: `DisclaimerFragment.finishDisclaimer(Z)` (o OK do aviso), `OpeningDivideActivity.onFinishFragment()` (quando o fragment atual é `EcoFragment`), `OpeningDivideActivity.startNextActivity()` e `EcoFragment.startNextActivity()`. O `createEcoIntent()` manda `ECO_START` e coloca um `EcoFragment` na tela. O `EcoFragment.startNextActivity()` tem as mesmas chamadas que rodam depois do OK: `setDisclaimerPassed`, o broadcast `DISCLAIMER_COMPLETE`, `INavigationApService.disclaimerDisappeared()` e `IPhoneCoordinationApService.setDisplayPermission()`. Fora do DaLauncher, a string da action aparece em quatro `.odex`: `CameraAPService`, `SystemInfoService`, `VehicleCoordination` e `AcuraLinkApService` (prováveis receivers; o código deles não foi lido). O impacto disso na Fase 10 está em §16.4.

**Confirmado no carro (logcat que a central gravou no pendrive em 2026-10-20, com o v0.5.4; backup em `~/backup-honda-civic-g10/pendrive-honda-ota-2026-10-20/`).** O tap do AutoOk dispara a sequência inteira do fabricante, no cold boot e no resume de LP0. Até ~220 ms depois de `AutoOk: tap ok=true` aparecem `NavigationApService.disclaimerDisappeared`, `DisclaimerFragment.finishDisclaimer` (`DisclaimerComplete!`), `SystemDisplayApService$ActionDisclaimerCompleteReceiver.onReceive` com `act=com.mitsubishielectric.ada.app.dalauncher.action.DISCLAIMER_COMPLETE` e `CarPlayApService.setDisplayPermission(status=true)`. Então o `DISCLAIMER_COMPLETE` dispara com tap programático, o `SystemInfoService` é receiver de verdade, e o CarPlay só ganha permissão de tela depois do aviso. Nesses logs `ECO_START` não aparece nenhuma vez: depois do patch da Fase 10, o caminho Eco vai rodar pela primeira vez neste carro.

### 11.2 Launcher principal

| Campo | Valor |
|---|---|
| Package | `com.mitsubishielectric.ada.app.dalauncher` |
| Activity principal | `.Launcher` (depois do dismiss do aviso) |
| TaskId | 3 (observado) |
| Lançador do aviso | `.Launcher$HMIServiceReceiver.onReceive` (confirmado via REA, §11.1.1) |

### 11.3 Services críticos do boot

Visíveis em logcat quando o boot acontece:
- `AppManagerServiceApplication` — Automotive activity manager (controla transições)
- `AutomotiveActivityManager` — Dentro de AMS
- `SystemDisplayApService` — Controla display state
- `AVPlayer` — A/V player
- `am_proc_start`, `am_new_intent`, `am_resume_activity` — ActivityManager padrão Android

### 11.4 Câmera de ré 🆕

| Campo | Valor |
|---|---|
| Package | `com.mitsubishielectric.ada.app.camera` |
| Activity | `.activity.RearWideCameraDisplayActivity` |
| Needle completo | `com.mitsubishielectric.ada.app.camera/.activity.RearWideCameraDisplayActivity` |
| Trigger | Marcha ré engatada |
| Comportamento | Sobe sobre qualquer Activity ativa (incluindo o aviso). Quando saí da ré, Activity anterior volta ao topo. |
| Pacote OTA | `/system/vendor/app/Camera.apk` + `/system/vendor/app/CameraAPService.apk` |
| Impacto no AutoOk v0.3.0 | APK tentava tapar enquanto câmera estava ativa (tap caía na UI da câmera, no vazio) |
| Impacto no AutoOk v0.4.0 | HmiServiceReceiver re-inicia o watcher após exit de LP0 que acompanha a mudança de ré, cobre o cenário corretamente |

### 11.5 InfoClockOpeningActivity 🆕

Activity do launcher que aparece brevemente em algumas transições pós-LP0:

| Campo | Valor |
|---|---|
| Needle | `com.mitsubishielectric.ada.app.dalauncher/.InfoClockOpeningActivity` |
| Observado em | am_pause_activity logo antes do am_resume_activity do OpeningDivideActivity depois de voltar da câmera |
| Função provável | Tela de boas vindas/relógio que aparece brevemente antes do aviso em alguns resumos |
| Não interfere com nosso APK (não é needle do watcher) | — |

### 11.6 Power Management (LP0) 🆕 — CRÍTICO

A central Mitsubishi faz **transições frequentes de power** entre dois estados principais:

- **LP0 (Low Power 0)** — sleep profundo. Processadores desligados, apenas RAM mantida.
- **Normal operation** — tudo rodando.

Essas transições acontecem **o tempo todo**: ao mudar de ré, abrir/fechar porta, pressionar pedal, qualquer coisa que o PowerManager considere "mudança de estado operacional". **Cada transição afeta processos do Android inteiro**.

| Package | Função |
|---|---|
| `com.mitsubishielectric.ada.appservice.powermanager` | PowerManagerApService |
| Classe chave | `PowerManagerEnterLP0`, `PowerManagerStartUp`, `PowerManagerStateMachine` |

**Broadcasts emitidos pelo PowerManager** (CRÍTICOS pro nosso APK):

| Action | Extra `state` | Emitido quando | Reação do AutoOk v0.4.0 |
|---|---|---|---|
| `com.mitsubishielectric.ada.appservice.powermanager.ACTION_HMI_SERVICE_START` | `ExitLP0` | Sistema saiu de LP0 (acordou do sleep) | HmiServiceReceiver → forceRestartWatcher |
| `com.mitsubishielectric.ada.appservice.powermanager.ACTION_HMI_SERVICE_START` | `AccOnRestart` | ACC foi ligado interrompendo transição LP0 em curso | HmiServiceReceiver → forceRestartWatcher |
| `com.mitsubishielectric.ada.appservice.powermanager.ACTION_HMI_SERVICE_PRE_STOP` | — | Sistema vai entrar em LP0 | (não escutamos — poderia ser usado pra salvar estado) |
| `com.mitsubishielectric.ada.appservice.powermanager.ACTION_HMI_SERVICE_RESTART` | `AccOnRestart` | HMI services vão ser reiniciados | (equivalente a HMI_SERVICE_START) |
| `com.mitsubishielectric.ada.appservice.powermanager.ACTION_FINISH_ALL_RUNNING_TASKS_FOREGROUND` | — | PowerManager mata tasks foreground (power off) | — |
| `com.mitsubishielectric.ada.appservice.powermanager.ACTION_FINISH_ALL_RUNNING_TASKS_PARTIAL` | — | PowerManager mata tasks parciais (preparando LP0) | — |

**Comportamento ligado a nós:**
Nosso APK não é tratado como "HMI service" pelo PowerManager, então o PowerManager **não re-inicia nosso Service** após LP0. Antes da v0.4.0, isso causava o APK ficar silencioso após qualquer LP0.

**Pattern real descoberto 2026-10-19 (REA, ver [whitelist-mitsubishi-2026-10-19.md](whitelist-mitsubishi-2026-10-19.md) §6):** o PowerManager **não mantém lista** de serviços. Ele é **pub/sub puro** — `PowerManagerBroadcastSender` envia 16 broadcasts, qualquer app com receiver registrado no manifest participa, sem gating de whitelist nem permissão. 33 APKs do shipping referenciam `ACTION_HMI_SERVICE_START` — é o contrato universal. Nossa `HmiServiceReceiver` da v0.4.0 segue esse mesmo pattern.

**Lista dos 16 broadcasts do `PowerManagerBroadcastSender`:**

| Broadcast | Momento |
|---|---|
| **`sendHMIServiceStartIntent`** 🎯 | ExitLP0 / AccOnRestart (nós escutamos) |
| `sendHMIServiceStopIntent` | entrando em LP0 |
| `sendHMIServicePreStopIntent` | prepare pra LP0 |
| `sendHMIServiceRestartIntent` | ACC-on durante transição |
| `sendHMIServiceStopIntentSplit` | variante do stop |
| `sendFinishAllRunnningTaskForegroundIntent` | mata foreground antes de LP0 |
| `sendFinishAllRunnningTaskIntent` | mata processos genéricos |
| `sendFinishAllRunnningTaskPartialIntent` | mata processos parciais |
| ⭐ `sendResumeCameraIntent` | **retomada da câmera de ré — oportunidade pro AutoOk** (hoje usamos logcat polling) |
| `sendStartAnimationIntent` | animação de boot |
| `sendChangeStartCauseNoticeIntent` | mudança de razão de startup |
| `sendKeyOffLimitNoticeIntent` | timer de key-off expirando |
| `sendSetVbusResIntent` | VBUS result |
| `sendSyscomResetStartNoticeIntent` | SysCom reset |
| `sendVbusOffNoticeIntent` | VBUS desligou |

Causas de startup conhecidas (strings extra em `ACTION_HMI_SERVICE_START`): `"ExitLP0"`, `"AccOnRestart"`, `"ColdBoot"`.

### 11.7 Whitelist Mitsubishi (UX de instalação de apps, não gating de boot) 🆕

Análise estática completa via REA + JADX em 2026-10-19. Documento denso em [`docs/whitelist-mitsubishi-2026-10-19.md`](whitelist-mitsubishi-2026-10-19.md). Resumo:

| Campo | Valor |
|---|---|
| APK shell | `com.mitsubishielectric.ada.appservice.whitelist` (`vendor-app/WhitelistApService.apk`) — 5 classes, roda como `android.uid.system` |
| Biblioteca com a lógica | `vendor-framework/WhitelistLib.jar` — 15 classes (interface AIDL, parser XML, FileManager, Util) |
| APK portador do XML | `com.honda.displayaudio.whitelist.apk` em `/system/vendor/etc/honda/` (14 KB — **NÃO está no dump 0040**, gap) |
| XML em runtime | `/data/data/whitelist-1.0.xml` (literal, direto no root de `/data/data/`) |
| Arquivo temporário durante update | `/data/data/TEMP_whitelist-1.0.xml` |
| Content URI do provider | `content://com.honda.displayaudio.whitelist/1.0` → AssetFileDescriptor de um ZIP contendo `whitelist-1.0.xml` |
| Trigger de reload | Boot + `android.intent.action.PACKAGE_REPLACED` com `data=package:com.honda.displayaudio.whitelist` |
| Regra de substituição | Só se `<contentVersion>` novo > atual (`WhitelistUtil.compareWhitelistContentVersion`) |
| Interface AIDL | `com.mitsubishielectric.ada.appservice.whitelist.IWhiteListApService` (**action** usa `WhiteList` com L maiúsculo; o resto do código usa `IWhitelistApService`) |
| Métodos públicos | `checkInstallPackage` (nunca é chamado no shipping), `getPackageNames`, `getApplicationName`, `getAudioInfo`, `getAudioStreamType`, `getRegulation`, `getRevert` |

**Quem consulta a whitelist (grep em 120 odex deodexados):**
- `AppManager.apk` (gerenciador de apps UI) — `getApplicationName`, `getAudioInfo`, `getRegulation`, `getRevert`.
- `FileManager.apk` (telas de instalação do USB).

**Ninguém mais.** Nenhum HMI service, nenhum launcher, nenhum PowerManager. Entrar na whitelist tem **efeito cosmético** (nome amigável no AppManager) — não afeta LP0, não remove código da v0.4.0. Ver §16.3.

**Formato do XML:**
```xml
<whiteList>
  <formatVersion>1.0</formatVersion>
  <contentVersion>N</contentVersion>
  <controlData>
    <application>
      <name>...</name>
      <package>...</package>
      <versionCode>...</versionCode>
      <keyStore>SHA-256_hex_do_certificado</keyStore>
      <audioStreamType>0..6</audioStreamType>
      <withAudio>true|false</withAudio>
      <regulation>0..3</regulation>  <!-- NULL/PARK/SPEED/PARKSPEED -->
      <revert>0|1</revert>
    </application>
  </controlData>
</whiteList>
```

---

## 12. Pipeline do APK AutoOk (v0.5.4)

```
BOOT_COMPLETED (cold boot via AUDIO 5s)
      │
      ▼
BootReceiver.onReceive()
      │
      ▼
context.startService(AutoOkService)
      │
      ▼
AutoOkService.onStartCommand(START_STICKY, action=null)
      │
      ├─ FileLogger.init(this)
      ├─ FileLogger.startSessionOnce()   ← rotation .log → .log.1
      ├─ Validate config
      ├─ synchronized(watcherLock) {
      │     watcher = buildWatcher()
      │     watcher.start()              ← Thread "AutoOk-LogcatWatcher"
      │  }
      └─ startWatchdog()                 ← Thread "AutoOk-Watchdog" (30s loop)
         (v0.5.0 tirou o scheduleAlarm()/AlarmManager que a v0.4.0 tinha)

OU: Em resposta a HMI_SERVICE_START:

HmiServiceReceiver.onReceive()         ← dispara em cada ExitLP0/AccOnRestart
      │
      ▼
startService(AutoOkService, action=ACTION_FORCE_RESTART)
      │
      ▼
AutoOkService.onStartCommand(action=ACTION_FORCE_RESTART)
      │
      └─ forceRestartWatcher()         ← recria o watcher só se morto; se vivo,
                                         só reseta handled (lição 17.9: EPERM)
      
LogcatWatcher thread:
      │
      ├─ sleep(BOOT_INITIAL_WAIT_MS=500)
      ├─ Runtime.exec("su") → stdin: "exec logcat -b events -v threadtime am_create_activity:I am_new_intent:I *:S"
      ├─ while (running && readLine()):
      │     if (line.contains(NEEDLE)):
      │        callback.onDetected()     ← NÃO retorna! Loop infinito desde v0.3.0
      │
AutoOkService.onAvisoDetected() (chamada pelo watcher):
      │
      ├─ if (handled) return
      ├─ if (TapDeduper.shouldSuppress(now, lastTapAtMs, 3s)) return  ← dedup temporal
      ├─ handled = true
      ├─ FileLogger.log("aviso detectado (NORMAL_STARTUP match)")
      ├─ sleep(DELAY_SECONDS_AFTER_DETECT=1)
      ├─ Shell.suTapWithFallback(coords, intervalMs)
      │     ├─ tap (400,350) → se exit 0, return true
      │     ├─ sleep 200ms
      │     ├─ tap (400,340) → se exit 0, return true
      │     ├─ sleep 200ms
      │     └─ tap (400,360)
      ├─ FileLogger.log("tap ok=... coords=...")
      └─ rearmWatcher()
      
AutoOkService.rearmWatcher():
      │
      ├─ sleep(REARM_DELAY_SECONDS=2)
      ├─ handled = false                ← só reseta flag, NÃO recria watcher (v0.3.0 fix)
      └─ FileLogger.log("rearmed (watcher reusado)")
      
Watchdog thread (a cada 30s):
      │
      ├─ sleep(30s)
      ├─ synchronized(watcherLock) {
      │     if (handled) return
      │     if (watcher.isAlive()) return
      │     // só recria se morto de verdade
      │     watcher.stop()
      │     watcher = buildWatcher()
      │     watcher.start()
      │     FileLogger.log("watchdog: watcher recriado")
      │  }
      └─ loop
```

**Delays reais medidos (v0.3.0):**
- Session start → tap (cold boot): ~5.1s
- Detect → tap: ~2.5s
- Rearm → próximo detect: instantâneo (reuso)

---

## 13. Fluxos

### 13.1 Cold boot (combo AUDIO 5s)

```
Chave off
   │
   │ Dono segura botão AUDIO por 5s
   ▼
Diálogo "Quer reiniciar?" aparece
   │
   │ Dono confirma OK
   ▼
Shutdown real + reboot cold
   │
   ├─ Bootloader (1.10_20160407183722)
   ├─ Kernel Linux 3.1.10+ (do /boot MTD)
   ├─ init.rc (do ramdisk /boot MTD)
   ├─ Zygote + Dalvik VM
   ├─ Android services → BOOT_COMPLETED
   │
   ▼
Daupdater (bg) escaneia pendrive → se achar SwUpdate.mdt, aplica
Launcher → OpeningDivideActivity → aguarda tap no OK
   │
   │ ← AutoOk Service dispara tap em ~5s
   ▼
Launcher principal (Launcher.class)
```

### 13.2 Resume do suspend (virar a chave)

```
Chave on (do suspend)
   │
   ▼
Kernel wake
   ├─ Services restauram estado
   ├─ Última Activity resume
   │
   ▼
Launcher principal (sem OpeningDivideActivity, sem BOOT_COMPLETED)
```

**Importante:** Nesse fluxo **não dispara BOOT_COMPLETED**, logo AutoOk Service permanece com o estado anterior (watcher ativo da sessão passada, se não morreu). O watchdog recria se necessário.

### 13.3 Deploy OTA EvilValet

```
PC: python3 tooling/ota-build/build.py (ou build-rollback / build-dump-* / build-deep-scan)
   └─ Gera SwUpdate.mdt assinado com testkey AOSP
   
PC: sudo ./tooling/scripts/prepare-pendrive-install.sh /dev/sda
   └─ Limpa pendrive VFAT + copia 0040/SwUpdate.mdt + SwUpdate2.txt
   
Carro: Pendrive na porta frontal USB
   
Carro: AUDIO 5s + "Quer reiniciar?" → confirmar
   │
   ▼
Reboot cold → Recovery Mode (daupdater scaneia pendrive)
   │
   ├─ daupdater lê /mnt/usbdrive1/<rom_type>/SwUpdate.mdt
   ├─ Verifica signature contra testkey (whitelist)
   ├─ Executa updater-script (edify):
   │     ├─ mount /system
   │     ├─ package_extract_dir/file (nosso overlay)
   │     ├─ set_perm/set_perm_recursive
   │     └─ sleep final (2 min, pra garantir sync)
   │
   ▼
Resultado em /mnt/usbdrive1/result.log + install-0040.log
Reinicia central
```

### 13.4 Rearm do AutoOk (dentro de uma sessão)

```
Detecta OpeningDivideActivity (ex: usuário entra/sai do DealerDiag)
   │
   ▼ consume() do logcat watcher dispara callback
onAvisoDetected() → handled=true → sleep 1s → tap sweep → FileLogger.log("tap ok=...")
   │
   ▼ handled continua true por 10s
rearmWatcher() → sleep 10s → handled=false → log "rearmed"
   │
   ▼ consume() continua rodando (reuso)
Próxima aparição do needle → dispara callback de novo
```

### 13.5 Recovery após LP0 (v0.4.0) 🆕

```
Sistema em LP0 (sleep profundo)
   │
   ▼ Usuário coloca em ré (ou abre porta, ou qualquer wake event)
PowerManagerApService detecta → inicia saída de LP0
   │
   ▼
Emite broadcast: ACTION_HMI_SERVICE_START com state=ExitLP0
   │
   ▼ (HMI services reiniciados, mas nosso APK não é "HMI service")
   │ Durante LP0, nosso processo logcat (filho do su) foi matado.
   │ Thread do watcher ficou bloqueado em readLine() num FD morto.
   │ isAlive() retornava true (falso positivo).
   │
   ▼ BroadcastReceiver v0.4.0:
HmiServiceReceiver.onReceive() → startService(ACTION_FORCE_RESTART)
   │
   ▼
AutoOkService.forceRestartWatcher()
   ├─ stopWatcher()                    ← mata watcher antigo (interrompe readLine)
   ├─ handled = false
   └─ buildWatcher() + start()         ← novo logcat process via novo su
   │
   ▼
Watcher novo captura o am_resume_activity de OpeningDivideActivity que
estava "represado" no logcat buffer durante o LP0 (ou qualquer aparição
subsequente) → dismiss normal.
```

**Fallback (safety net):**
Se por algum motivo o `HMI_SERVICE_START` broadcast não chegar, AlarmManager
dispara `ACTION_ALARM_HEALTHCHECK` a cada 60s → mesmo efeito (forceRestart).

---

## 14. Pendrive OTA — layout esperado pelo daupdater

```
/mnt/usbdrive1/ (pendrive VFAT formatado)
├── SwUpdate2.txt                — Ver:X.Y (trigger file)
├── <rom_type>/                  — Pasta nomeada pelo rom_type (nossa safra: 0040)
│   └── SwUpdate.mdt             — Pacote OTA assinado (zip)
└── [após deploy]
    ├── SwUpdate2.txt.done       — Renomeado pelo updater-script (sinaliza "não re-aplicar")
    ├── result.log               — "YYYY/MM/DD HH:MM:SS : OK"
    ├── install-<rom_type>.log   — Log do updater-script (nosso)
    ├── logcat.txt (+.1)         — Logcat do boot pós-OTA (daupdater salva)
    └── kmsgcat.txt              — Kernel log
```

---

## 15. Credenciais técnicas (resumo)

| Campo | Valor |
|---|---|
| DA version | `1.F187.16` |
| rom_type (EvilValet) | `0040` |
| Model | MY16ADA |
| Device | vcm30t30 |
| Android | 4.2.2 (API 17) |
| Kernel | Linux 3.1.10+ #1 SMP PREEMPT (Apr 7 2016) |
| Combo cold boot | **AUDIO 5s + confirmar reiniciar** |
| Botão OK do Aviso | X=400, Y=350 (800×480) |
| Needle do Aviso | `com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity` |
| Package do AutoOk | `com.khalleb.civichmi.autook` |
| User ID do AutoOk | 10091 |
| Versão atual AutoOk | **9** (v0.5.4 — mudo CarPlay + LP0 resume; baseline estável) |
| Signing key | debug keystore (Android Debug cert) |
| Testkey SHA-256 | `A4:0D:A8:0A:59:D1:70:CA:A9:50:CF:15:C1:8C:45:4D:47:A3:9B:26:98:9D:8B:64:0E:CD:74:5B:A7:1B:F5:DC` |
| Debug cert SHA-256 | `9505deb0b0d8c53178eaade253eee94e1a31f0e6a1dde2b809752914b644cf02` |
| Broadcast crítico (recovery após LP0) | `com.mitsubishielectric.ada.appservice.powermanager.ACTION_HMI_SERVICE_START` com `state=ExitLP0` |
| Activity da câmera de ré | `com.mitsubishielectric.ada.app.camera/.activity.RearWideCameraDisplayActivity` |

**Backups essenciais:**
| Item | Caminho local |
|---|---|
| debug.keystore | `~/backup-honda-civic-g10/debug.keystore.bak` |
| dump raw APP/CAP/MITSU | `~/backup-honda-civic-g10/dump-raw-2026-10-17/*.img.gz` |
| deep-scan 2026-10-17 | `~/backup-honda-civic-g10/deep-scan-2026-10-17/` |
| vendor framework extraído | `tooling/apks-dumped/dump-0040/vendor-framework/` |
| Externo (Google Drive privado) | `honda-civic-g10-backup-2026-10-17.tar.gz` (269 MB, sha256 `3dbc1994...`) |
| Error History do bug LP0 (câmera de ré) | `~/backup-honda-civic-g10/error-history-2026-10-17-camera-ride-bug/` (4.5 MB) |
| Pendrive HONDA_OTA de 2026-10-20 (logcat/kmsg/exception da central depois do v0.5.4 + logs do install) | `~/backup-honda-civic-g10/pendrive-honda-ota-2026-10-20/` (3.6 MB, `SHA256SUMS`) |

---

## 16. Caminhos descartados (⏸)

### 16.1 ⏸ SuperSU como mediator (descartado 2026-10-17)

**Motivo:** nosso `/system/xbin/su` já é o mesmo binário setuid simples que o SuperSU-adjacent. SuperSU "completo" substituiria por um com **prompt via Activity** → `Runtime.exec("su")` do AutoOk ficaria bloqueado esperando toque humano = **quebra o AutoOk**. Pre-populate do database SQLite é frágil (UID muda, corrupção). APK é único consumidor de root; UI inútil aqui.

**Veredito:** não vale. Marcar como "não voltar a considerar".

### 16.2 ⏸ Xposed Framework (adiado 2026-10-17)

**Motivo:** Xposed v54 é a última compatível com Android 4.2.2 (API 17). Patch do `/system/bin/app_process` é destrutivo (binário crítico do boot). Qualquer problema = **bootloop permanente**, só recuperável via rollback OTA (10+ min por tentativa). **Zero precedente público** de Xposed em Mitsubishi Andromeda — Zygote customizado deles pode causar incompatibilidade.

**Veredito:** reconsiderar só se tiver central de testes dedicada, OU após 6+ meses rodando APK atual sem problema. Alternativa menos invasiva: smali-patch no DaLauncher (surface menor).

### 16.3 ⏸ Adicionar nosso APK à whitelist Mitsubishi (descartado 2026-10-19) 🆕

**Hipótese inicial:** se o PowerManager não reinicia nosso Service após LP0 porque não estamos na whitelist, entrar na whitelist eliminaria o workaround da v0.4.0.

**Investigação (REA + JADX, bulk-deodex de 120 odex):** 100% errada. Dos 120 APKs da vendor, só 2 consomem `IWhitelistApService` — `AppManager` (UI do gerenciador) e `FileManager` (telas de instalação por USB). PowerManager e todos os HMI services são agnósticos à whitelist. Recovery pós-LP0 é pub/sub via `ACTION_HMI_SERVICE_START` — qualquer app com receiver registrado participa, sem lista. Ver [`docs/whitelist-mitsubishi-2026-10-19.md`](whitelist-mitsubishi-2026-10-19.md) §7.

**Veredito:** entrar na whitelist tem **efeito cosmético** (nome amigável no AppManager, metadata de regulação). Não remove código da v0.4.0. Fica no backlog só pra UX futura. Reconsiderar apenas se abrirmos a Fase 9 "AutoOk oficial com nome bonito no gerenciador".

### 16.4 ✅ Modificar DaLauncher.apk via smali — CONCLUÍDA (Fase 10, deployada 2026-10-29)

**Deploy executado 2026-10-29.** §2.1 (validação do rollback) e §2.2 (install) passaram todos os gates e todas as 4 chamadas pós-aviso dispararam no carro (`disclaimerDisappeared`, `setDisclaimerPassed(true)`, `setDisplayPermission(true)` do CarPlay, broadcast `DISCLAIMER_COMPLETE`). Aviso de abertura removido do fluxo de boot. Observação do deploy: a tela `EcoFragment` passou a aparecer por ~6 s em cada boot (nunca tinha sido vista neste carro — era caminho morto antes do patch, §17.19 e §11.1.1). Resolvida no mesmo dia pela **Fase 10.1** com um segundo patch smali que reduz o timer do `EcoFragment` para 500 ms, mantendo as 4 chamadas pós-aviso intactas. Pacotes abaixo. Deploy e resultado completo em [`fase10-deploy-2026-10-29/README.md`](fase10-deploy-2026-10-29/README.md).

### 16.4-histórico Modificar DaLauncher.apk via smali — preparação (Fase 10, deploy 2026-10-27→29)

**Reaberto 2026-10-20** após descoberta do gate `sDisclamerFlg` (ver §17.16). **Rota B escolhida 2026-10-23** após análise do `AndroidManifest.xml` do DaLauncher: nenhuma permission signature-pura, `VEHICLE_RW` é GID-only. Doc da decisão: [`fase10-decisao-rotas-2026-10-23.md`](fase10-decisao-rotas-2026-10-23.md).

**Patch:** `OpeningDivideActivity.smali:671` `if-nez v0, :cond_9` → `goto :cond_9` (força rota pra `createEcoIntent()`, flag `sDisclamerFlg` nunca mais é lido).

**Validação:** segundo caller de `createDisclaimerOnHomeIntent` (linha 1754, em `notifyDisclaimerDestroy`) é código morto pós-patch — único caller indireto é `DisclaimerFragment:1741`, e o fragment nunca é instanciado.

**Patch versionado:** `tooling/fase10/opening-divide-activity-skip-disclaimer.patch` (1 hunk, 1 instrução). O `rebuild-dalauncher.sh` deodexa o `.odex` original fresh, aplica o patch, e **prova** que a única diferença de bytecode orig→patch é a classe `OpeningDivideActivity` (assemble+disassemble dos dois lados, diff). Não depende mais da árvore pré-patcheada local.

**Pacotes prontos (regerados em 2026-10-26, sem assert de device e sem `set_perm` em `/system`; o nome da pasta tem o horário em UTC):**
- Install: `tooling/ota-build/output-dalauncher-fase10/20261027T020208Z/0040/SwUpdate.mdt` (SHA-256 `4c31cb4d...`; APK rebuildado 17.8MB `1774136c...`, signado com testkey AOSP; o builder recusa APK não assinado com o testkey). Deleta o `.odex` velho e grava `FASE10-ODEX-REMOVED.OK`/`.FAIL` no pendrive (gate inequívoco, não trava o loop).
- Rollback: `tooling/ota-build/output-dalauncher-restore/20261027T020209Z/0040/SwUpdate.mdt` (SHA-256 `6445ec80...`; APK + odex originais; verifica md5 pós-restore e grava `ROLLBACK-RESTORED.OK`/`.FAIL`)
- Rebuild script: `tooling/fase10/rebuild-dalauncher.sh`
- Execução passo-a-passo: [`fase10-execucao-2026-10-27.md`](fase10-execucao-2026-10-27.md)

**Risco secundário (hipótese a confirmar no deploy):** espera-se que o PackageManager trate o signature mismatch como "new install" (apaga `/data/data/.../dalauncher/*` — wallpaper, ícones; launcher recria defaults). O caminho alternativo `INSTALL_FAILED_UPDATE_INCOMPATIBLE` desabilitaria o launcher — só se confirma no carro, por isso o rollback é gated. Detalhe em [`fase10-decisao-rotas-2026-10-23.md`](fase10-decisao-rotas-2026-10-23.md).

**Revisão pré-deploy (2026-10-26):**

- **O caminho Eco refaz a sequência pós-aviso.** Depois do patch, `createDisclaimerOrEcoIntent()` sempre devolve `createEcoIntent()`, e o `EcoFragment` faz as chamadas que o OK do aviso faria, inclusive o broadcast `DISCLAIMER_COMPLETE` que aparece em `CameraAPService`, `SystemInfoService`, `VehicleCoordination` e `AcuraLinkApService` (§11.1.1). A análise estática não diz qual branch roda. No carro, depois do deploy, conferir câmera de ré, navegação e projeção do CarPlay.
- **Resolvido: assert de device removido dos dois pacotes.** Os builds de 2026-10-23 geravam `assert(getprop("ro.product.device") == "vcm30t30" || getprop("ro.build.product") == "vcm30t30")`, que nenhum dos 18 pacotes anteriores (install, rollback, dump-raw, deep-scan, diagnostic) tinha. O `build.py` tira esse assert de propósito: se ele falha dentro do recovery, o comando `--update_package=/mnt/usbdrive1/0040/SwUpdate.mdt` fica em `/cache/recovery/command` e a central entra em recovery loop. Pelo CAUTION do `ic1101/docs/updates.md`, tirar o pendrive ou a bateria não sai do loop; sai plugando na porta frontal um pendrive com um pacote que o recovery consiga aplicar. O `/system/build.prop` do dump tem os dois valores iguais a `vcm30t30`, mas no recovery o `getprop` lê as props do ramdisk do recovery, cuja imagem (MTD `recovery`, §3.3) nunca foi dumpada, e o rollback tinha o mesmo assert. Os builders não geram mais a linha, e dois testes mantêm `assert(`/`abort(` fora dos 7 geradores. Os pacotes regerados diferem dos anteriores só nessa linha e na assinatura. A assinatura whole-file foi conferida contra o testkey (RSA 2048, e=3, SHA-1), com controle positivo (install do v0.5.4, aceito pelo carro) e negativo (cópia adulterada em 1 byte).
- **Resolvido: `set_perm` em `/system` trocado por `chown`/`chmod` do busybox.** O `set_perm` também aborta: no `update-binary` empacotado, ele aborta com `some changes failed` quando o chown/chmod falha, por exemplo se o CAP não montou e o arquivo não foi extraído (§17.18). Os dois pacotes agora acertam dono e modo do APK (e do odex, no rollback) com o busybox via `run_program`, que não aborta e grava no log `perm <arquivo> chown-exit=N chmod-exit=N`. O `set_perm` ficou só em `/tmp`, com teste. Os pacotes regerados diferem dos `20261026T214450Z`/`20261026T214451Z` só nessas linhas do `updater-script` e na assinatura, conferida contra o testkey com os mesmos controles; APK, odex, busybox e `update-binary` são os mesmos bytes. O busybox tem os applets `chown` e `chmod` (tabela de applets do binário), mas eles nunca rodaram no carro: o §2.1 do checklist os exercita no rollback antes do install.
- **Resolvido: scripts de pendrive aceitam o diretório do build.** `prepare-pendrive-install.sh` e `prepare-pendrive-rollback.sh` ignoravam o 2º argumento e sempre copiavam o build mais novo de `output/` e `output-rollback/` (pacotes do AutoOk); seguindo o checklist como estava, o §2.1 removeria `AutoOk.apk` + `su` do carro. Agora o 2º argumento é um diretório de builds (usa o mais novo) ou um build exato. O script valida `SwUpdate2.txt` + `0040/SwUpdate.mdt` antes de limpar o pendrive e, no fim, confere o SHA-256 lido do pendrive contra o build, depois de `drop_caches` para ler do dispositivo e não do cache. Sem o 2º argumento, o comportamento é o de antes. A sequência dos 5 `prepare-pendrive-*.sh` fica em `tooling/scripts/lib-pendrive.sh` (testada em `tooling/ota-build/tests/test_prepare_pendrive.py`, inclusive a sequência inteira, com stub no lugar do que exige root), que também recusa partição no lugar do disco, tabela que não seja MSDOS e partição que não seja vfat, mostra modelo, rótulo e conteúdo do pendrive e só limpa com `yes`, e no fim desmonta, inclusive quando a montagem era do desktop. As guardas e a confirmação foram conferidas, sem apagar nada, no pendrive HONDA_OTA real (`/dev/sda`, Cruzer Fit 29 GB).
- **Builds velhos no mesmo diretório.** Os de 2026-10-23 e os `20261026T214450Z`/`20261026T214451Z` continuam em `output-dalauncher-fase10/` e `output-dalauncher-restore/` e não devem ir pro pendrive: todos têm `set_perm` em `/system`, os de 2026-10-23 têm também o assert, e `...210720Z`/`...210007Z` nem gravam `.OK`/`.FAIL`. Os scripts pegam o build mais novo.

**Fase 10.1 (preparada 2026-10-29, pós-deploy da v1):** segundo patch smali em `EcoFragment.startNoOperationTimer`, trocando `const/16 v1, 0x1388` (5000 ms) por `const/16 v1, 0x1f4` (500 ms). Reduz a tela Eco de ~6 s para ~1 s mantendo intacto o `onServiceListComplete` + o callback que dispara `startEndAnimeAndNextActivity → startNextActivity → DISCLAIMER_COMPLETE + setDisplayPermission + disclaimerDisappeared + setDisclaimerPassed`. Patch versionado: `tooling/fase10/eco-fragment-reduce-timer.patch`. O `rebuild-dalauncher.sh` passou a aplicar os dois patches e exige que a diferença orig→patch no DEX seja **exatamente** `EcoFragment.smali` + `OpeningDivideActivity.smali`. 500 ms é o mínimo seguro porque o AutoOk v0.5.4 continua tapando `(400,350)` ~1 s depois do `am_create_activity` da `OpeningDivideActivity`; com 500 ms o tap ainda cai dentro do fundo do `EcoFragment` (os dois layouts `mm_07_04_06`/`_ziba` só têm `ImageView` em `(400,350)`, nada clicável — ver `raio-x/07-services-re.md`). Pacote novo: `output-dalauncher-fase10/20261029T134614Z/0040/SwUpdate.mdt` (SHA-256 `f571af751dc9be6619cf33e7eb5d11268dd3f004b1c93587dd47f05d6cf3f453`; APK `65481d45...`; md5 pós-deploy do APK = `655c01a3b17fe20b23c70114e1e0dae7`). Updater-script bit-por-bit idêntico ao da v1 (md5 `2cca09a3...`): único byte diferente dentro do `.mdt` é o APK. Rollback (`output-dalauncher-restore/20261027T020209Z/`) continua valendo sem rebuild — restaura o DaLauncher original.

---

## 17. Hall of fame de bugs

### 17.1 ✓ Needle do logcat sem `/.` — não detectava aviso

**Sintoma:** APK v0.1 nunca dispensava aviso.
**Causa:** needle configurada como `com.mitsubishielectric.ada.app.dalauncher.OpeningDivideActivity` (com `.`) — logcat do ActivityManager imprime `pkg/.ClassName` (com `/`), nunca batia.
**Fix:** `com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity`.

### 17.2 ✓ APK morre após 1º tap — Service com `stopSelf()`

**Sintoma:** APK v0.1 funcionava só na 1ª chave do dia.
**Causa:** `onAvisoDetected()` chamava `stopSelf()` após tap. BOOT_COMPLETED só dispara em cold boot, não resume do suspend, logo APK não voltava.
**Fix:** `rearmWatcher()` que sleep 10s e re-arma. Service nunca morre.

### 17.3 ✓ Boot != resume — virar a chave não dispara BOOT_COMPLETED

**Sintoma:** APK configurado mas nunca disparava.
**Causa:** central Honda **não faz cold boot** ao virar a chave. Sai do suspend. BOOT_COMPLETED só com cold boot.
**Fix:** combo AUDIO 5s + confirmar reiniciar.

### 17.4 ✓ Rom_type via log de erro do daupdater

**Sintoma:** Pacote OTA aplicava mas daupdater não achava.
**Causa:** rom_type default `0040` só descoberto após gerar 352 pacotes com valores diferentes e ler Error History da central.
**Fix:** rom_type `0040` confirmado via trial-and-error documentado.

### 17.5 ✓ Recovery sem `/sbin/sh` — `run_program("sh", ...)` falhava

**Sintoma:** `run_program("/sbin/sh", "-c", ...)` silenciosamente falhava no edify.
**Causa:** safra BR do recovery não tem `/sbin/sh` embarcado.
**Fix:** embarcar `busybox` ARM estático (do HondaHack APK) no pacote OTA via `package_extract_file` + `/tmp/busybox sh -c "..."`.

### 17.6 ✓ D8 dexer NullPointerException com anonymous inner classes

**Sintoma:** `./gradlew assembleRelease` crashava em `dexBuilder`.
**Causa:** D8 bug 4.0.52 com anonymous inner classes (lambda-like) em Service.
**Fix:** converter todas pra **named inner classes** (`AvisoCallback`, `WatchRunnable`, `WatchdogRunnable`).

### 17.7 ✓ Monkey-patch `stage_tree` não aplicado

**Sintoma:** pacote OTA não incluía busybox/su no overlay apesar do código Python.
**Causa:** faltou linha `upstream.stage_tree = _patched_stage_tree` no final do script Python.
**Fix:** adicionar linha + sempre validar diff do overlay.

### 17.8 ✓ Pendrive VFAT não suporta symlinks

**Sintoma:** dump adb via `cp -r` falhava com "can't create symlink: Operation not permitted" para 13 arquivos de framework + 5 APKs vendor.
**Causa:** VFAT não suporta symlinks.
**Fix descoberto 2026-10-17:** usar `cp -L` (follow symlinks). Também: extrair direto do raw dump do cap.img via `debugfs rdump` — não precisa ida ao carro.

### 17.9 ✓ EPERM em `Process.destroy()` do logcat (v0.2.0 → v0.3.0)

**Sintoma:** APK v0.2.0 funcionava mas log mostrava stacktrace de EPERM a cada rearm.
**Causa:** APK roda como uid 10091 (user app). `Runtime.exec("su") → logcat` cria processo como root. `Process.destroy()` do Java chama `kill()` que falha com EPERM (user não pode matar processo root).
**Fix v0.3.0:** `rearmWatcher()` não destrói mais o watcher — só reseta flag `handled`. Processo logcat segue vivo entre taps. `consume()` virou loop infinito. `destroy()` só roda em `onDestroy` do Service (sessão terminando, EPERM silenciado com try/catch).

### 17.10 ✓ tar sem gzip no recovery

**Sintoma:** `tar czf out.tar.gz dir/` gerava arquivo de 0 bytes.
**Causa:** busybox tar tenta fork+exec `gzip` externo que não existe no PATH do recovery.
**Fix:** pipe explícito `tar cf - -C dir . | gzip -c > out.tar.gz` com busybox explícito nos dois comandos.

### 17.11 ✓ UDA/CAC "Device or resource busy" no mount

**Sintoma:** `mount /dev/.../UDA /tmp/mnt/UDA` falhava.
**Causa:** o próprio recovery já monta UDA em `/data` e CAC em `/cache` (recovery-fstab).
**Fix:** usar os mount points existentes `/data` e `/cache` em vez de re-montar.

### 17.12 ✓ `/system/system/packages.xml` não existe

**Sintoma:** `cp /system/system/packages.xml` falhava.
**Causa:** `packages.xml` está em `/data/system/packages.xml` (dentro de UDA = /data), não dentro de APP (= /system).
**Fix:** paths corretos — tabela de localização validada contra dump raw local antes de deploy.

### 17.13 ✓ APK fica inoperante após LP0 (v0.3.0 → v0.4.0) 🆕

**Sintoma reportado pelo dono:** liga carro → aviso aparece → coloca em ré → câmera aparece → tira da ré → **aviso persiste e precisa toque manual**.

**Causa raiz** (descoberta analisando `Error History` do carro, 2026-10-17):

1. Mitsubishi faz transições frequentes de power (LP0 ↔ ativo) em QUALQUER mudança de estado operacional (ré, porta, pedal, etc.)
2. Em cada entrada de LP0, PowerManager emite `FinishAllRunningTasksPartialIntent` que mata processos de baixa prioridade
3. Nosso processo `logcat` (filho de `su`) morre durante a transição
4. Nosso APK (processo 2586) **continua vivo em memória**, mas o thread `LogcatWatcher` fica bloqueado em `readLine()` lendo de um FD morto
5. `watcher.isAlive()` retorna **true** (thread em espera é "vivo"), então o watchdog não detecta e não re-cria
6. APK fica silencioso até o próximo cold boot

**Diagnóstico via logs:**
- Último log do APK antes do travamento: `rearmed (watcher reusado)` (14:30:08)
- Depois, 1 minuto completo de silêncio enquanto câmera e aviso aconteciam
- Sistema emitiu `am_resume_activity` do OpeningDivideActivity, mas APK não logou "aviso detectado"
- `am_proc_died` do khalleb nunca apareceu (processo não morreu, só o thread ficou zumbi)

**Fix v0.4.0:**
Novo `HmiServiceReceiver` escuta `com.mitsubishielectric.ada.appservice.powermanager.ACTION_HMI_SERVICE_START` que o PowerManager emite em cada `ExitLP0`. Quando recebe, chama `AutoOkService` com `ACTION_FORCE_RESTART` → `forceRestartWatcher()` mata watcher antigo (interrompe o `readLine()` bloqueado) e cria novo. Além disso, `AlarmManager` dispara o mesmo caminho a cada 60s como fallback. Nova permissão `WAKE_LOCK` necessária.

**Validado no carro 2026-10-17:** cenário câmera de ré → aviso persiste **não acontece mais**.

**Logs do bug preservados em:** `~/backup-honda-civic-g10/error-history-2026-10-17-camera-ride-bug/`

### 17.14 ✓ Mapeamento do recovery pós-LP0 confirma v0.4.0 (REA 2026-10-19) 🆕

**Pergunta de pesquisa:** por que o PowerManager não re-inicia nosso Service após LP0? É porque não estamos na whitelist Mitsubishi?

**Investigação:** deodex de 120 APKs vendor + grep global por `IWhitelistApService` e `ACTION_HMI_SERVICE_START`. Decompilação de `WhitelistApService`, `WhitelistLib`, `PowerManagerApService`, `AppManagerServiceLib` via REA/JADX.

**Causa raiz da nossa confusão inicial:** interpretamos "não ser HMI service" como "não estar na whitelist". Errado em dois níveis:
1. A whitelist Mitsubishi é consultada só por UI (`AppManager` + `FileManager`) — não é gate de boot.
2. O PowerManager é pub/sub puro: envia `ACTION_HMI_SERVICE_START` e qualquer app com receiver registrado participa. Não há lista.

**Confirmação da v0.4.0:** nossa `HmiServiceReceiver` + manifest com `intent-filter action=ACTION_HMI_SERVICE_START` é **exatamente o pattern que os 33 APKs do shipping usam** (de `AndroidAuto` a `WifiApService`). Não é workaround — é o jeito oficial.

**Oportunidade descoberta de bônus:** `PowerManagerBroadcastSender.sendResumeCameraIntent` é um broadcast dedicado à retomada da ré. Hoje o AutoOk detecta ré via logcat polling. Pode virar Fase 9 (ver [`docs/whitelist-mitsubishi-2026-10-19.md`](whitelist-mitsubishi-2026-10-19.md) §8.3).

**Documento denso:** [`docs/whitelist-mitsubishi-2026-10-19.md`](whitelist-mitsubishi-2026-10-19.md).

### 17.15 ✓ Bug do mudo em ligação CarPlay via BT + jornada v0.4.0 → v0.5.4 🆕

**Sintoma inicial:** com APK v0.4.0 e CarPlay via BT, ligações recebidas ficavam em mudo sozinhas poucos segundos depois de atendidas. Reproduzível.

**Investigação (2026-10-20):** pacote OTA novo `build-diagnostic.py` coletou `/data/data/com.khalleb.civichmi.autook/files/autook.log` + SharedPrefs do DaLauncher + persist props + logcat/kmsg do próprio HU.

**Evidência do autook.log v0.4.0:**

```
09:24:57 FORCE_RESTART source=alarm_60s cause=null
09:24:59 FORCE_RESTART source=hmi_broadcast cause=ExitLP0
09:24:59 tap ok=true coords=3
09:25:01 aviso detectado    ← match "falso"
09:25:05 tap ok=true coords=3
...
```

Janelas de 10-15 minutos com um tap a cada ~12s, totalizando centenas de taps por dia. Taps em `(400, 350)` acertam o botão de mudo quando a tela de ligação do CarPlay está sobreposta.

**Causa raiz do v0.4.0 — 3 bugs compostos:**

1. `AutoOkConfig.ALARM_HEALTHCHECK_INTERVAL_SECONDS = 60` agenda AlarmManager que chama `FORCE_RESTART` a cada 60s
2. `forceRestartWatcher()` recria o `LogcatWatcher` e reseta `handled = false`
3. O watcher novo lê o buffer do logcat que ainda tem linhas antigas mencionando `OpeningDivideActivity` (eventos `am_destroy_activity`, `onActivityPauseComplete`, `onStop`). O match `line.contains(activityNeedle)` casa com qualquer uma — inclusive destruída

**Jornada de fix em 4 iterações no mesmo dia:**

| Versão | Mudanças | Regressão | Validada no carro |
|---|---|---|---|
| **v0.5.0** | AlarmManager removido, needle `am_create_activity`/`START u0` com buffer `main` em `-v brief`, pre-check `isActivityOnTop`, dedup 30s, rearm 10s, `logcat -c`, `BOOT_INITIAL_WAIT_MS=2000` | Needle no formato errado (`-v brief` cuspia `I/TAG(PID):` sem `: START`); pre-check nunca casava; `logcat -c` zerava buffer antes do watcher ler. Zero taps | Sim, aviso parou de ser tapado |
| **v0.5.1** | Removido `logcat -c` e pre-check; `forceRestartWatcher()` passa a reusar watcher vivo em vez de recriar (regressão do fix 17.9 — EPERM voltou em v0.5.0) | Needle ainda com formato errado | Sim, aviso continuou aparecendo |
| **v0.5.2** | `-v brief` → `-v threadtime`; `-b main -b events`; `BOOT_INITIAL_WAIT_MS=500` | Em LP0 resume, central dispara `PRECEDING_STARTUP` (tela de logo) ANTES do `NORMAL_STARTUP` (o aviso real). v0.5.2 tapava no primeiro e bloqueava o segundo com `handled=true` | Parcial: pegava cold boot mas não LP0 resume |
| **v0.5.3** | Needle exige `NORMAL_STARTUP` + `START u0`; rearm 10s → 2s; dedup 30s → 3s | Buffer errado: Android 4.2.2 ignora `-b main` quando `-b events` vem depois, lia só events. Needle `ActivityManager: START u0` é tag do buffer `main` → nunca casava | Sim, aviso continuou |
| **v0.5.4** | `-b events` sozinho + needle casa `am_create_activity` (cold boot) OU `am_new_intent` (LP0 resume) + `OpeningDivideActivity` + `NORMAL_STARTUP` | — | **Sim: cold boot ✓, LP0 resume ✓, zero taps falsos, mudo CarPlay OK** |

**Config final em v0.5.4:**

- `REARM_DELAY_SECONDS = 2`
- `TAP_DEDUP_SECONDS = 3`
- `BOOT_INITIAL_WAIT_MS = 500`
- `WATCHDOG_INTERVAL_SECONDS = 30`
- Logcat: `-b events -v threadtime am_create_activity:I am_new_intent:I *:S`
- Needle: casa `am_create_activity` OU `am_new_intent` + `OpeningDivideActivity` + `dalauncher.action.NORMAL_STARTUP`
- `forceRestartWatcher`: reusa watcher vivo (só reseta `handled`), recria só se morto

**Lições técnicas:**

1. `logcat -v brief` cuspe `I/TAG(PID): msg` — needle `"TAG: msg"` não casa. Use `-v threadtime` que gera `date pid tid I TAG: msg` padrão.
2. Android 4.2.2 `logcat -b A -b B` **não** combina buffers — o segundo sobrescreve. Pra ler múltiplos buffers precisa de duas instâncias.
3. `am_create_activity`, `am_resume_activity`, `am_new_intent` vivem no buffer `events`. `ActivityManager: START u0` vive em `main`. **Buffers diferentes.**
4. LP0 resume reutiliza Activity com `SINGLE_TOP` flag → não dispara `am_create_activity`, só `am_new_intent`. Needle de LP0 resume precisa casar `am_new_intent`.
5. Central dispara 2 Activities no LP0 resume: `PRECEDING_STARTUP` (tela de logo, não é o aviso) e `NORMAL_STARTUP` (o aviso). Precisa filtrar pelo action.
6. Logs do próprio HU vão pro pendrive automaticamente quando ele está plugado (`logcat.txt`, `kmsgcat.txt`, `*.dat`). Diagnóstico ad-hoc sem OTA custom.

### 17.16 ✓ Gate do disclaimer é static `sDisclamerFlg` em memória (2026-10-20) 🆕

**Pergunta de pesquisa:** dá pra remover o aviso de vez (sem tap, sem watcher)? Onde o DaLauncher persiste a aceitação do disclaimer?

**Investigação:** diagnóstico (`build-diagnostic.py`) copiou SharedPrefs + databases + persist props do DaLauncher. Nenhum gate persistido encontrado:

- `com.mitsubishielectric.ada.app.dalauncher.prefs.xml`: só `apps.new.list` / `apps.new.page`
- `HMI_SERVICE_START_SHARED_PREF.xml`: `HMI_SERVICE_START_IS_CALLED=false`
- `HMI_SERVICE_STATUS.xml` + `SP_LAST_SCREEN_NAME.xml`: vazios
- `launcher.preferences`: só locale `en_US`
- `/data/property/*`: nenhum `persist.*` relacionado a disclaimer

Grep no smali deodex local (`tooling/apks-decoded/DaLauncher-deodexed/`) revelou:

```
OpeningDivideActivity.smali:17   .field public static sDisclamerFlg:Z
OpeningDivideActivity.smali:669  sget-boolean v0, ...sDisclamerFlg:Z
OpeningDivideActivity.smali:671  if-nez v0, :cond_9    ← SE true, pula o aviso
```

**O gate é static boolean em memória**, não persistido em disco. Explica por que o aviso aparece em todo boot: static reseta pra `false` no reload da classe. `DisclaimerFragment.smali:4363` seta `true` depois do tap OK, `HmiBroadcastReceiver.smali:492` e `:636` resetam `false` em certos eventos HMI.

**Patch mínimo** em `OpeningDivideActivity.smali:671`:

```
Antes:   if-nez v0, :cond_9
Depois:  goto :cond_9
```

Pula sempre pro `createEcoIntent()`, ignorando o flag. Aviso nunca aparece.

**Signature do DaLauncher**: `CN=Melco Honda16MY, Mitsubishi Electric, Japan` — SHA-256 `93:14:CE:...:05:AD`. **Não é AOSP testkey**. Outros vendor-apps usam chave Mitsubishi distinta (`A2:09:0F:...:EF:65`). DaLauncher é singular, provavelmente sem `sharedUserId` compartilhado.

Resign com nossa testkey AOSP = PackageManager detecta mismatch no boot, trata como "new install" perdendo permissões `/system/*`. Pode funcionar OU travar — risco médio.

**Rota recomendada = odex-level patch** (preserva signature). Fase 10 planejada em [`docs/fase10-pre-planejamento-2026-10-20.md`](fase10-pre-planejamento-2026-10-20.md).

**Pré-requisito pra Fase 10:** v0.5.0 do AutoOk estável por 1 semana primeiro.

### 17.17 ✓ Install OTA entrava em loop infinito sem renomear `SwUpdate2.txt` (2026-10-20) 🆕

**Sintoma:** depois de deployar o v0.5.0 e v0.5.1 do AutoOk, a central aplicava o OTA, chegava a 100%, ficava segundos com tela preta, e **começava a aplicar o OTA de novo**. Único workaround manual: puxar o pendrive durante a janela de tela preta.

**Causa raiz:** o `daupdater` em cada boot escaneia o pendrive montado em `/mnt/usbdrive1` procurando pelo trigger `SwUpdate2.txt`. Se encontra, aplica o OTA que está em `0040/SwUpdate.mdt`. Como o updater-script do `build.py` **não renomeava** esse trigger após instalar, no reboot pós-OTA o daupdater via o trigger de novo e re-aplicava — loop infinito.

**Por que só o install tinha o bug?** Os builders mais recentes (`build-deep-scan.py`, `build-dump-raw.py`, `build-diagnostic.py`) já tinham o fix. O `build.py` original (de 2026-10-16) foi feito antes dessa lição aparecer e nunca foi atualizado. `build-rollback.py` tinha o mesmo problema por omissão análoga.

**Mitigação:** adicionar nos dois builders antes do sleep final:

```python
out.append(sh(f"{BB} mv {USB}/SwUpdate2.txt {USB}/SwUpdate2.txt.done 2>>{LOG}; {BB} echo mv-trigger-exit=$? >> {LOG}"))
out.append(sh(f"{BB} rm -f /cache/.copy_complete 2>>{LOG}; {BB} echo rm-copy-complete-exit=$? >> {LOG}"))
out.append(sh(f"{BB} sync"))
```

O `.done` evita re-match. O `rm /cache/.copy_complete` cobre um flag secundário que o daupdater também consulta — e que o `SystemUpdateApService` (fluxo OTA oficial, app-level) é quem escreve ao encenar o comando em `/cache/recovery/` (confirmado na RE de 2026-10-27, [`raio-x/07-services-re.md`](raio-x/07-services-re.md) §2).

**Regra arquitetural permanente:** todo `build-*.py` novo em `tooling/ota-build/` **PRECISA** incluir esses dois comandos imediatamente antes do `run_program("/tmp/sleep", N)` final. Sem exceção. Documentado em memória pessoal ([[ota-script-sempre-quebra-loop]]) pra garantir que não vai esquecer de novo.

### 17.18 ✓ `set_perm` em `/system` abortaria o updater-script (latente, 2026-10-26) 🆕

**Sintoma:** nenhum no carro. Achado no review pré-deploy da Fase 10, antes de algum pacote falhar por isso.

**Causa raiz:** o `update-binary` dos nossos pacotes (`ic1101/ota-builder/input/update-binary`) tem o `set_perm` do AOSP JB: se o `chown` ou o `chmod` falha, ele imprime `chown of %s to %d %d failed` e aborta com `%s: some changes failed` (as strings estão no binário). O `mount` e o `package_extract_file` não abortam quando falham, então um CAP que não montou deixa o arquivo sem extrair e o `set_perm` seguinte aborta. O abort deixa o comando estagiado em `/cache/recovery/command`: recovery loop (§3.6 do checklist da Fase 10).

**Mitigação:** em todos os geradores, dono e modo em `/system` saem do `chown`/`chmod` do busybox via `run_program`, que não aborta, e o resultado vai para o log (`perm <arquivo> chown-exit=N chmod-exit=N`). O `set_perm` fica só em `/tmp` (busybox e sleep que o próprio pacote extrai), com teste em `test_dalauncher_ota.py` e `test_ota_generators.py` (sem exceção — vale para os 5 geradores).

**Resolvido também no `build.py` (2026-10-27):** o install do AutoOk era o último com `set_perm` em `/system` (no `AutoOk.apk` 0644 e no `su` 06755). Trocado por `chown`/`chmod` do busybox, com um detalhe a mais: `su` precisa do bit setuid, e `su` sem setuid = AutoOk sem root. Por isso o updater-script grava `AUTOOK-INSTALLED.OK`/`.FAIL` no pendrive conferindo `test -u /system/xbin/su` (setuid de fato presente) além do APK no lugar. O pacote estável já aplicado no carro (`output/20261020T181124Z`) não muda — isto vale a partir do próximo rebuild do AutoOk. O `chmod` setuid do busybox ainda não rodou no carro; o gate `.OK`/`.FAIL` é justamente a prova no primeiro deploy que usar este `build.py`.

### 17.19 ✓ Tela Eco (`createEcoIntent`) aparece 5 s pela primeira vez neste carro, pós-Fase 10 (2026-10-29) 🆕

**Sintoma observado após o deploy Fase 10:** aviso desapareceu, mas em cada boot aparece por ~6 s uma tela com título **-eco-** e três barras de folhinhas (ecoscore) antes do launcher principal. O dono do carro nunca tinha visto essa tela — nem antes do nosso projeto.

**Causa raiz:** o fluxo original dentro de `OpeningDivideActivity.createDisclaimerOrEcoIntent()` testava `sDisclamerFlg` (static boolean em memória, §17.16) e tinha dois destinos — `DisclaimerFragment` (aviso, sempre caía aqui porque o flag sempre começa `false`) ou `EcoFragment` (nunca alcançado em uso real). Nosso patch (`if-nez v0, :cond_9` → `goto :cond_9`) ignora o flag e sempre vai pro `createEcoIntent()`. Resultado: a tela Eco acordou pela primeira vez neste carro, como o §11.1.1 previa. Timing confirmado no `logcat.txt` do pendrive: 5000 ms de `startNoOperationTimer` + ~770 ms de `startEndAnimeAndNextActivity` + render ≈ 6 s totais.

**Mitigação — Fase 10.1 (2026-10-29):** segundo patch smali em `EcoFragment.startNoOperationTimer`, de uma instrução: `const/16 v1, 0x1388` → `const/16 v1, 0x1f4` (5000 ms → 500 ms). Mantém intacto o `onServiceListComplete` + o callback que dispara `startEndAnimeAndNextActivity → startNextActivity → DISCLAIMER_COMPLETE + setDisplayPermission + disclaimerDisappeared + setDisclaimerPassed` (as 4 chamadas pós-aviso que CarPlay/Navegação precisam). Resultado esperado: ~1 s de tela Eco (500 ms de timer + animação). Patch versionado: `tooling/fase10/eco-fragment-reduce-timer.patch`. Detalhes em §16.4 e [`fase10-deploy-2026-10-29/README.md`](fase10-deploy-2026-10-29/README.md).

**Por que não 0 ms:** o AutoOk v0.5.4 continua no sistema como safety net (§4.1 do checklist) e tapa `(400,350)` ~1 s depois do `am_create_activity` da `OpeningDivideActivity`. Com 500 ms o tap ainda cai no fundo do `EcoFragment` (ambos layouts `mm_07_04_06`/`_ziba` têm só `ImageView` em `(400,350)`, nada clicável). Com 0 ms o tap cairia no `CarPlayMainActivity` ou no `Launcher` → risco de clicar em algo real.

---

## 18. Timeline de modificações feitas por nós

| Data | Mudança | Resultado | Commit |
|---|---|---|---|
| 2026-10-16 | Deploy inicial AutoOk.apk v0.1 + su via EvilValet OTA | Funcionou — aviso dispensado em ~10s por boot | — (sessão exploratória) |
| 2026-10-16 | Release público bilíngue no GitHub | Repo khalleb/honda-civic-headunit público | `70a26a7` |
| 2026-10-16 | Documentação Fase 7 (7 docs) + logo SVG + diagramas Mermaid | Documentação de deploy final | parte de `70a26a7` |
| 2026-10-17 | Backup debug.keystore + dump raw bootable APP/CAP/MITSU | Rede de segurança externa (Google Drive, 269 MB) | `f60d447`, `ea5f742` |
| 2026-10-17 | Rodada 1 — APK v0.2.0 (delay reduzido, logs persistentes, watchdog, multi-coord) | Delay session start → tap: 10s → 5s | partial `4a1206d` |
| 2026-10-17 | Rodada 1 Hotfix — APK v0.3.0 (fix EPERM via reuso do watcher) | Zero stacktraces de EPERM | `4a1206d` |
| 2026-10-17 | Rodada 2 — framework extraído de cap.img via debugfs (sem ida ao carro) | 104 arquivos em `vendor-framework/` | — (apks-dumped está no .gitignore) |
| 2026-10-17 | Fase 8A — deep-scan OTA com todas as partições + packages.xml + /proc/* | scan.tar.gz 897 KB extraído → gera este MAPA | `46a99aa` |
| 2026-10-17 | Documentação GitHub: README bilíngue, GIF animado real do carro, mockups SVG EN, 5 docs pt-BR + 4 EN preenchidos | Repo visualmente pronto para público internacional | `0f5b3cc` + `c55470d` + `d8a2d56` + `7dabe22` |
| 2026-10-17 | APK v0.4.0 — fix do bug "aviso persiste após câmera de ré" | HmiServiceReceiver + AlarmReceiver + forceRestartWatcher. Resolve inoperância após LP0. Validado no carro. | pendente |
| 2026-10-19 | REA (`morluto/rea`) integrado como ferramenta de análise estática | MCP server `rea` registrado em `~/.claude.json` com `REA_JADX_MCP_JAR` apontando pro JADX headless. Skill `reverse-engineer-anything` instalado em `~/.claude/skills/`. Script `tooling/deodex/deodex-apk.sh` automatiza o fluxo odex→dex→APK. Primeira validação: `OpeningDivideActivity` do `DaLauncher` (ver §11.1.1). | pendente |
| 2026-10-19 | Análise estática completa da whitelist Mitsubishi + mapeamento do recovery pós-LP0 | Deodex de 120 APKs vendor. Confirmado que whitelist é UI-only (ver §11.7, §16.3). PowerManager é pub/sub puro com 16 broadcasts (ver §11.6). V0.4.0 segue o pattern correto, nada a mudar. Documento denso em [`docs/whitelist-mitsubishi-2026-10-19.md`](whitelist-mitsubishi-2026-10-19.md). | pendente |
| 2026-10-19 | Raio-X Camada 1: scan de superfície completo da plataforma | Deodex de 160 APKs/libs (vendor-app + vendor-framework + system-app). 5 scans: 364 interfaces AIDL, 445 broadcasts, 27 content authorities, 48 sysprops, trust map de 110 APKs. Achado-chave: `ICameraAPServiceReverseSignalListener` + `EXIT_REAR_WIDE_CAMERA` + `ACTION_RESUME_CAMERA` abrem caminho pra Fase 9 (ré sem logcat polling). Documentos em [`docs/raio-x/`](raio-x/). | pendente |
| 2026-10-20 | APK v0.5.0 — primeira tentativa de fix do bug do mudo em CarPlay | Diagnóstico via `build-diagnostic.py` novo (coletou autook.log + prefs/dbs do DaLauncher + persist props). AlarmManager removido, needle tentou `-v brief`+`main`, pre-check, dedup 30s, rearm 10s. **Regrediu**: zero taps + EPERM voltou (§17.9 regressão). Validado no carro. (ver §17.15) | pendente |
| 2026-10-20 | APK v0.5.1 — fix EPERM | `forceRestartWatcher()` reusa watcher vivo (lição 17.9). Removido `logcat -c` + pre-check. Needle ainda errado pro formato brief. Zero taps. | pendente |
| 2026-10-20 | APK v0.5.2 — threadtime + buffers | `-v threadtime`, `-b main -b events`, `BOOT_INITIAL_WAIT_MS=500`. Cold boot ✓, LP0 resume ✗ (tapa `PRECEDING_STARTUP` em vez de `NORMAL_STARTUP`). | pendente |
| 2026-10-20 | APK v0.5.3 — needle NORMAL_STARTUP | Needle exige `NORMAL_STARTUP`; rearm 2s; dedup 3s. **Regrediu**: Android 4.2.2 `-b main -b events` falha silenciosa, só lê events. `ActivityManager: START u0` nunca casa. | pendente |
| 2026-10-20 | APK v0.5.4 — baseline estável | `-b events` sozinho; needle casa `am_create_activity` (cold boot) ou `am_new_intent` (LP0 resume, Activity SINGLE_TOP) + `NORMAL_STARTUP`. **Validado no carro: cold boot ✓, LP0 resume ✓, mudo CarPlay ✓, zero taps falsos**. (ver §17.15) | pendente |
| 2026-10-20 | Fix do loop OTA infinito em `build.py` + `build-rollback.py` | Updater-script agora renomeia `SwUpdate2.txt` → `.done` + remove `/cache/.copy_complete` antes do sleep final. Antes o pendrive precisava ser puxado manualmente durante a tela preta. Regra arquitetural permanente: todo `build-*.py` novo precisa dos dois comandos. (ver §17.17, memória `ota-script-sempre-quebra-loop`) | pendente |
| 2026-10-20 | Fase 10 pré-planejada — gate do disclaimer descoberto | `OpeningDivideActivity.sDisclamerFlg` é static boolean em memória (não persistido). Patch mínimo de 1 instrução no smali remove o aviso de vez. DaLauncher assinado com key Mitsubishi `Melco Honda16MY` (não AOSP testkey) — deploy requer odex-level patch pra preservar signature, ou resign aceitando risco de "new install". Fase 10 bloqueada até v0.5.4 estável. (ver §17.16, doc denso em [`docs/fase10-pre-planejamento-2026-10-20.md`](fase10-pre-planejamento-2026-10-20.md)) | pendente |
| 2026-10-23 | Fase 10 preparada offline — Rota B escolhida + 2 pacotes OTA construídos | Análise do manifesto do DaLauncher confirmou que `VEHICLE_RW` é GID-only e não há `sharedUserId` → Rota B (resign AOSP) é viável. Patch versionado em `tooling/fase10/opening-divide-activity-skip-disclaimer.patch`; `rebuild-dalauncher.sh` deodexa fresh + aplica o patch + prova que só `OpeningDivideActivity` muda no bytecode + verifica cert testkey AOSP (classes.dex 1.25MB, zipalign + apksigner). Pacotes install (APK `1774136c...`) e rollback construídos e smoke-tested, ambos com gate de status-file no pendrive (`FASE10-ODEX-REMOVED.OK` / `ROLLBACK-RESTORED.OK`). Deploy no carro agendado 2026-10-27 (fecha janela de v0.5.4 estável por 1 semana). Checklist em [`fase10-execucao-2026-10-27.md`](fase10-execucao-2026-10-27.md). (ver §16.4) | pendente |
| 2026-10-24 | Análise RE dos Diag APKs (Camada 2) | 5 apps (`DealerDiag`, `DeveloperDiag`, `PreShipmentDiag`, `LetDiag`) + backend AIDL `DiagApService`. **Sem PIN**: as 91 telas do DealerDiag são `exported=false` sem gate interno (sem checagem de permission/UID/senha). Acesso normal via ferramenta LET ou triggers de arquivo em `/data/data/inlinediag/rcv_{dealer,let}_launch`; nossa rota é `su -c "am start -n ...dealerdiag/.DealerDiagActivity"` (root bypassa exported, a validar no carro). 91 telas classificadas leitura/teste/escrita — escrita perigosa: `DisplayReprogram` (StartRepro), `BackupDataCleat` (DealerClearAll), `factoryResetSettings` (AIDL). O "unlock code" (`getUnLockCode`) é licenciamento de mapa Garmin (ESN + `GarminUnlock*.csv`), **não** senha de menu. Doc: [`raio-x/06-diag-apks.md`](raio-x/06-diag-apks.md). | pendente (validar am start no carro) |
| 2026-10-26 | Revisão pré-deploy da Fase 10 | Assert de device removido de `build-dalauncher-fase10.py` e `build-dalauncher-restore.py` (nenhum pacote aplicado no carro tinha; falha dele no recovery vira recovery loop), e o `set_perm` em `/system` desses dois trocado por `chown`/`chmod` do busybox, porque também aborta (§17.18). Testes mantêm `assert(`/`abort(` fora dos 7 geradores e `set_perm` só em `/tmp` (menos no `build.py`, §17.18). `prepare-pendrive-install.sh`/`-rollback.sh` passam a aceitar o diretório do build e conferem o SHA-256 lido do pendrive. Pacotes regerados (`20261027T020208Z`/`20261027T020209Z`, horário UTC), assinatura whole-file conferida contra o testkey. Sequência dos 5 scripts de pendrive extraída para `lib-pendrive.sh`, com guardas de disco/MSDOS/vfat, `yes` antes de limpar, umount no fim e teste da sequência inteira; o CI ganhou o job `unit-tests`. Caminho Eco do DaLauncher patcheado mapeado, e o logcat do carro de 2026-10-20 confirma que `DISCLAIMER_COMPLETE` dispara com o tap do AutoOk (§11.1.1). (ver §16.4) | pendente |
| 2026-10-27 | Revisão do projeto inteiro + fix do `set_perm` no `build.py` | Revisão de APK/geradores/scripts/CI/docs, tudo na `main` (CI com 4 jobs, verde: tooling + JUnit do AutoOk). Último `set_perm` em `/system` (install do AutoOk) trocado por `chown`/`chmod` do busybox com gate `AUTOOK-INSTALLED.OK`/`.FAIL` que confere o setuid do `su` (`test -u`) — §17.18 resolvido para os 5 geradores. Sincronização do MAPA/CLAUDE com a v0.5.4, correções de logs de exit, código morto e guardas de script. Deploy da Fase 10 adiado para 2026-10-28 (só disponibilidade do carro). RE Camada 2 das services (`StrgSW`, `SystemUpdate`, `VehicleInfoManager`, `SystemInfoService`) em [`raio-x/07-services-re.md`](raio-x/07-services-re.md): OTA oficial pelo `SystemUpdateApService` escreve o `/cache/.copy_complete` (§17.17); sinal de ré por B-CAN `CVT_SHFT_IN_REVERSE` no `VehicleInfoManager` (candidato pra Fase 9); API de eventos do volante no `StrgSwApService`; mute via `IAvApService.setMute`. RE nativa (daupdater/.so) bloqueada — não dumpados. | pendente |
| 2026-10-27 | Varredura do GitHub (33 repos) + achado KingoSU no nosso `su` | [`raio-x/08-github-landscape-2026-10-27.md`](raio-x/08-github-landscape-2026-10-27.md). O `/system/xbin/su` instalado é **KingoSU**, não SuperSU — confirmado por `strings` e pelo SHA bater com o AUDIT do [`joshfng/root-honda`](https://github.com/joshfng/root-honda). Dispara broadcast `com.kingouser.com/.NativeAccessReceiver` a cada chamada (no-op, mas público). Troca pelo `su` Chainfire SR1 pendente para o próximo rebuild do AutoOk (§10.2). TX codes + IDs B-CAN do Mitsubishi resolvidos via [`alexpotv/Clusters`](https://github.com/alexpotv/Clusters) — fecha a lacuna da RE §3/§4. Issue #29 do ic1101 confirma CR-V China (`1.F198.60`) como mesma família. `commaai/opendbc` tem o Civic Touring 2016 / Hatchback EX 2017 como fonte canônica de CAN (mesma base que o Clusters usa). | pendente |
| 2026-10-29 | 🎯 **Fase 10 deployada no carro — aviso removido para sempre.** | §2.1 (validação do rollback, no-op bytes idênticos) e §2.2 (install Fase 10) passaram todos os gates. Logs no `~/backup-honda-civic-g10/pendrive-fase10-{restore,install}-2026-10-29/`. Aviso de abertura não aparece mais. CarPlay projeta, navegação funciona, zero crash. **Caminho Eco acordado pela 1ª vez neste carro** (§17.19) — tela "-eco-" por ~6 s em cada boot. Mesma sessão: Fase 10.1 preparada — segundo patch smali reduzindo `startNoOperationTimer` de 5000 ms para 500 ms. Pacote `output-dalauncher-fase10/20261029T134614Z/` (SHA `f571af75…`, APK `65481d45…`, md5 pós-deploy = `655c01a3b17fe20b23c70114e1e0dae7`). Updater-script bit-por-bit igual ao da v1; só o APK mudou. Doc completo em [`fase10-deploy-2026-10-29/README.md`](fase10-deploy-2026-10-29/README.md). | pendente (Fase 10.1 a aplicar) |

---

## 19. Pontos de entrada (links)

### 19.1 Documentação do projeto

- [`CLAUDE.md`](../CLAUDE.md) — Contexto automático pro Claude Code
- [`README.md`](../README.md) — README PT-BR
- [`README.en.md`](../README.en.md) — README EN (stub)
- [`QUICKSTART.md`](../QUICKSTART.md) — Deploy em 20 min
- [`CONTRIBUTING.md`](../CONTRIBUTING.md)
- [`DISCLAIMER.md`](../DISCLAIMER.md)
- [`central-multimidia-civic-g10-kb.md`](../central-multimidia-civic-g10-kb.md) — KB histórico (narrativa de descoberta)
- [`docs/proxima-sessao.md`](proxima-sessao.md) — Pontos de entrada por tipo de pergunta
- [`docs/pesquisa-rotas-sem-adb-2026-10-15.md`](pesquisa-rotas-sem-adb-2026-10-15.md) — Pesquisa das 8 rotas sem-ADB
- [`docs/whitelist-mitsubishi-2026-10-19.md`](whitelist-mitsubishi-2026-10-19.md) — Análise estática da whitelist Mitsubishi + recovery pós-LP0 (REA + JADX)
- [`docs/fase10-pre-planejamento-2026-10-20.md`](fase10-pre-planejamento-2026-10-20.md) — Fase 10 (remover aviso de vez): gate smali descoberto, rotas de deploy, rede de segurança requerida
- [`docs/raio-x/`](raio-x/) — Raio-X Camada 1 (5 scans do shipping):
  - [01-apis-aidl.md](raio-x/01-apis-aidl.md) — 364 binder interfaces em 63 domínios
  - [02-broadcasts.md](raio-x/02-broadcasts.md) — 445 actions em 48 prefixos
  - [03-content-providers.md](raio-x/03-content-providers.md) — 27 authorities / 52 URIs
  - [04-system-properties.md](raio-x/04-system-properties.md) — 48 sysprops
  - [05-trust-map.md](raio-x/05-trust-map.md) — 110 APKs com sharedUserId e perms
  - [06-diag-apks.md](raio-x/06-diag-apks.md) — RE dos Diag APKs (sem PIN)
  - [07-services-re.md](raio-x/07-services-re.md) — RE das services (volante, OTA oficial, veículo, áudio)
  - [08-github-landscape-2026-10-27.md](raio-x/08-github-landscape-2026-10-27.md) — varredura do GitHub (33 repos; achado KingoSU no nosso `su`; TX codes do Mitsubishi via Clusters)
  - [README.md](raio-x/README.md) — índice + metodologia

### 19.2 Fase 7 (deploy final)

- [`docs/fase7-deploy-2026-10-16/README.md`](fase7-deploy-2026-10-16/README.md) — Resumo + navegação
- [`docs/fase7-deploy-2026-10-16/01-jornada-completa.md`](fase7-deploy-2026-10-16/01-jornada-completa.md) — Narrativa cronológica
- [`docs/fase7-deploy-2026-10-16/02-descobertas-tecnicas.md`](fase7-deploy-2026-10-16/02-descobertas-tecnicas.md) — Descobertas
- [`docs/fase7-deploy-2026-10-16/03-build-ota-receita.md`](fase7-deploy-2026-10-16/03-build-ota-receita.md) — Receita de build OTA
- [`docs/fase7-deploy-2026-10-16/04-apk-autook-detalhes.md`](fase7-deploy-2026-10-16/04-apk-autook-detalhes.md) — Detalhes do APK
- [`docs/fase7-deploy-2026-10-16/05-manutencao-e-futuro.md`](fase7-deploy-2026-10-16/05-manutencao-e-futuro.md) — Manutenção
- [`docs/fase7-deploy-2026-10-16/06-dumps-obtidos.md`](fase7-deploy-2026-10-16/06-dumps-obtidos.md) — Dumps

### 19.3 Documentação pt-BR

- [`docs/pt-BR/00-visao-geral.md`](pt-BR/00-visao-geral.md) — Visão geral
- [`docs/pt-BR/03-descobrindo-sua-safra.md`](pt-BR/03-descobrindo-sua-safra.md) — Como descobrir rom_type
- [`docs/pt-BR/07-rollback.md`](pt-BR/07-rollback.md) — Rollback
- [`docs/pt-BR/08-backups-e-rollback.md`](pt-BR/08-backups-e-rollback.md) — Backups
- [`docs/pt-BR/README.md`](pt-BR/README.md) — Índice

### 19.4 Local (não commitado — fora do repo)

- `~/backup-honda-civic-g10/debug.keystore.bak` — Keystore de assinatura
- `~/backup-honda-civic-g10/dump-raw-2026-10-17/` — Raw bootable APP+CAP+MITSU
- `~/backup-honda-civic-g10/deep-scan-2026-10-17/` — Deep scan extraído
- `~/honda-civic-g10-backup-2026-10-17.tar.gz` — Backup externo compactado
- `PENDENCIAS.md` — Lista de pendências (não commitada, no .gitignore)

### 19.5 Dumps/decoded (apks-dumped, no .gitignore)

- `tooling/apks-dumped/dump-0040/system-app/` — APKs do /system/app
- `tooling/apks-dumped/dump-0040/system-framework/` — framework/ parcial (sem symlinks resolvidos)
- `tooling/apks-dumped/dump-0040/vendor-framework/` — 104 jars/odex de /system/vendor/framework (extraído do raw)
- `tooling/apks-dumped/dump-0040/vendor-app/` — APKs do /system/vendor/app
- `tooling/apks-decoded/` — APKs já desodexados, prontos pra análise com REA/JADX:
  - `DaLauncher-deodexed.apk` (579 smali, 1.2 MB classes.dex) — launcher incluindo `OpeningDivideActivity`
  - `WhitelistApService-deodexed.apk` (6 smali) — shell binder da whitelist
  - `WhitelistLib-asapk.apk` (20 smali, APK wrapper) — biblioteca da whitelist (lógica real)
  - `PowerManagerApService-deodexed.apk` (40 smali, 184 KB classes.dex) — power manager da Mitsubishi
  - `AppManagerServiceLib-asapk.apk` (41 smali, APK wrapper) — framework de automotive activities

### 19.6 Referências de terceiros

- https://github.com/codeage/root-honda — su setuid + SuperSU + whitelist Mitsubishi
- https://github.com/jersacct/2016PilotOneClick — rooteador de Honda Pilot 2016
- https://github.com/librick/ic1101 — pesquisa RE completa + ota-builder (base do nosso build); também fornece `baksmali-2.5.2.jar` + `smali-2.5.2.jar` em `tooling/references/ic1101/apk-rebuilder/input/` (usados pelo script de deodex)
- https://juniperspring.org — artigo original Eric McDonald sobre EvilValet
- https://github.com/morluto/rea — ferramenta de reverse engineering com MCP para APK/nativo/firmware. **Como está instalada aqui:** JADX JAR em `~/.local/share/rea/android/jadx-headless-mcp-0.7.1-all.jar`, MCP registrado em `~/.claude.json` (`mcpServers.rea`), skill em `~/.claude/skills/reverse-engineer-anything/`

### 19.7 Nosso tooling (scripts locais)

- [`tooling/deodex/deodex-apk.sh`](../tooling/deodex/deodex-apk.sh) + [`tooling/deodex/README.md`](../tooling/deodex/README.md) — Converte APK odex-only em APK com `classes.dex` injetado (pré-requisito pra JADX/REA funcionarem na vendor-app)
- `tooling/scripts/` — Scripts de pendrive, deep-scan, dump raw, rollback (ver §20)
- `tooling/scripts/lib-pendrive.sh` — Sequência comum dos `prepare-pendrive-*.sh`: guardas (USB, disco inteiro, MSDOS, vfat), escolha do build, `yes` antes de limpar, limpeza, cópia, conferência de SHA-256 lida do pendrive e umount no fim. Testes em `tooling/ota-build/tests/test_prepare_pendrive.py`
- `tooling/ota-build/` — Build do pacote OTA EvilValet

---

## 20. Comandos frequentes

### 20.1 Build + deploy do APK

```bash
# Rebuild APK
cd our-apk
JAVA_HOME=/home/khalleb/sdks/jdk-17 PATH=/home/khalleb/sdks/jdk-17/bin:$PATH \
  ./gradlew clean assembleRelease

# Sign com debug keystore
APKSIGNER=/home/khalleb/sdks/Android/build-tools/33.0.2/apksigner
$APKSIGNER sign --ks ~/.android/debug.keystore --ks-pass pass:android \
  --out app/build/outputs/apk/release/AutoOk.apk \
  app/build/outputs/apk/release/app-release-unsigned.apk

# Copiar pro overlay OTA
cp our-apk/app/build/outputs/apk/release/AutoOk.apk \
   tooling/ota-build/overlay/system/app/AutoOk.apk

# Build pacote OTA
python3 tooling/ota-build/build.py

# Preparar pendrive
sudo ./tooling/scripts/prepare-pendrive-install.sh /dev/sda
```

### 20.2 Rollback

```bash
python3 tooling/ota-build/build-rollback.py
sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sda
# Deploy no carro: AUDIO 5s + confirmar
```

### 20.3 Dump raw bootable

```bash
python3 tooling/ota-build/build-dump-raw.py
sudo ./tooling/scripts/prepare-pendrive-dump-raw.sh /dev/sda
# Deploy: ~18 min no carro
```

### 20.4 Deep scan (sincroniza este MAPA)

```bash
python3 tooling/ota-build/build-deep-scan.py
sudo ./tooling/scripts/prepare-pendrive-deep-scan.sh /dev/sda
# Deploy: ~10s no carro
# De volta: 
mkdir -p ~/backup-honda-civic-g10/deep-scan-$(date +%Y-%m-%d)
tar xzf /run/media/khalleb/HONDA_OTA/deep-scan-0040/scan.tar.gz \
  -C ~/backup-honda-civic-g10/deep-scan-$(date +%Y-%m-%d)/
```

### 20.5 Inspecionar dumps raw via debugfs

```bash
# Montar app.img sem precisar sudo nem mount loop
gunzip -c ~/backup-honda-civic-g10/dump-raw-2026-10-17/app.img.gz > /tmp/app.img
debugfs -R "ls /" /tmp/app.img
debugfs -R "rdump /framework ~/extract/" /tmp/app.img
rm /tmp/app.img

# Mesmo com cap.img, mitsu.img
```

### 20.6 Verificar integridade dos backups

```bash
./tooling/scripts/verificar-backups.sh
```

### 20.7 Ler logs do APK no HU (precisa acesso via adb/su)

```bash
# No HU com adb habilitado:
adb shell su -c "cat /data/data/com.khalleb.civichmi.autook/files/autook.log"

# Sessão anterior:
adb shell su -c "cat /data/data/com.khalleb.civichmi.autook/files/autook.log.1"
```

### 20.8 Análise estática de APK via REA (odex → dex → REA)

APK em `/system/vendor/app/` e `/system/app/` é odex-only. Pipeline:

```bash
./tooling/deodex/deodex-apk.sh tooling/apks-dumped/dump-0040/vendor-app/DaLauncher.apk
```
A APK sai em `tooling/apks-decoded/DaLauncher-deodexed.apk`.

Via CLI (independente do MCP):
```bash
APK=tooling/apks-decoded/DaLauncher-deodexed.apk
export REA_JADX_MCP_JAR=~/.local/share/rea/android/jadx-headless-mcp-0.7.1-all.jar

npx -y rea-agents@latest inspect-android-package  "$APK" --json
npx -y rea-agents@latest search-android-classes   "$APK" OpeningDivideActivity --json
npx -y rea-agents@latest inspect-android-class    "$APK" com.mitsubishielectric.ada.app.dalauncher.OpeningDivideActivity --json
npx -y rea-agents@latest inspect-android-method   "$APK" com.mitsubishielectric.ada.app.dalauncher.OpeningDivideActivity onCreate --json
npx -y rea-agents@latest trace-android-references "$APK" com.mitsubishielectric.ada.app.dalauncher.OpeningDivideActivity --json
```

Via MCP (dentro do Claude Code, após restart): o skill `reverse-engineer-anything` carrega sozinho; é só pedir ao agente para inspecionar a APK.

Re-rodar o setup do MCP após atualizar o REA:
```bash
npx -y rea-agents@latest setup --client claude_code --yes
```
Depois conferir que `env.REA_JADX_MCP_JAR` segue dentro de `mcpServers.rea` no `~/.claude.json` (se o setup limpar, reinjetar com Python/jq).

### 20.9 Fase 10 — rebuild do DaLauncher patcheado + pacotes OTA

Rota B (ver §16.4). Precisa dos originais em `tooling/apks-dumped/dump-0040/vendor-app/` (dump, gitignored) e do patch versionado `tooling/fase10/opening-divide-activity-skip-disclaimer.patch`. Não depende mais da árvore smali pré-patcheada local.

```bash
# Rebuilda: deodex fresh + aplica patch versionado + prova (so OpeningDivideActivity muda) + zipalign + apksigner testkey AOSP
bash tooling/fase10/rebuild-dalauncher.sh
# Saída: tooling/fase10/output/DaLauncher-fase10.apk

# Pacote OTA de install (deploya o APK rebuildado + remove .odex antigo + gate FASE10-ODEX-REMOVED.OK)
python3 tooling/ota-build/build-dalauncher-fase10.py

# Pacote OTA de rollback (restaura APK + .odex originais + verifica md5 -> ROLLBACK-RESTORED.OK)
python3 tooling/ota-build/build-dalauncher-restore.py
```

Pendrives: aqui o 2º argumento é obrigatório; sem ele, os scripts gravam os pacotes do AutoOk. Cada script usa o build mais novo do diretório, pede `yes` antes de apagar, confere o SHA-256 lido do pendrive e desmonta no fim.

```bash
sudo tooling/scripts/prepare-pendrive-install.sh /dev/sdX tooling/ota-build/output-dalauncher-fase10
sudo tooling/scripts/prepare-pendrive-rollback.sh /dev/sdY tooling/ota-build/output-dalauncher-restore
```

---

**Fim do MAPA. Última atualização: 2026-10-26 (revisão pré-deploy da Fase 10).**
