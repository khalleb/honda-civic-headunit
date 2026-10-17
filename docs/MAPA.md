# MAPA — Atlas da Central Honda Civic G10 BR

**Reflexo navegável do estado real da central multimídia (Honda Display Audio 7", Mitsubishi Andromeda, Tegra 3, Android 4.2.2).**

Última sincronização: `2026-10-17` (APK v0.4.0 + fix do bug de LP0).

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
| WhitelistApService.apk | com.mitsubishielectric.ada.appservice.whitelist | **Whitelist Mitsubishi (bypass signing)** |
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
| Versão atual | **4** (v0.4.0) ✓ confirmado via teste no carro 2026-10-17 (corrige bug de LP0) |
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
- `HmiServiceReceiver` 🆕 v0.4.0 — ouve `com.mitsubishielectric.ada.appservice.powermanager.ACTION_HMI_SERVICE_START`, dispara `ACTION_FORCE_RESTART` no Service. Fundamental em cada exit de LP0 (câmera de ré, abertura de porta, acordar do suspend).
- `AlarmReceiver` 🆕 v0.4.0 — recebe alarm periódico de 60s do `AlarmManager`, dispara `ACTION_FORCE_RESTART` como fallback.
- `AutoOkService` — Service persistente (START_STICKY). Monta watcher, watchdog, rearm. **v0.4.0:** novo `forceRestartWatcher()` que mata e recria watcher (quebra thread bloqueado em `readLine()` após LP0). `scheduleAlarm()` via AlarmManager a cada 60s.
- `LogcatWatcher` — Thread que lê `logcat -v brief ActivityManager:I *:S` via `su`, procura needle. Em v0.3.0+ roda em loop infinito (não é destruído entre taps).
- `Shell` — Wrapper de `Runtime.exec("su")` + `suTapWithFallback`
- `FileLogger` — Grava `/data/data/.../files/autook.log` com rotação por sessão

**Permissions declaradas:**
- `RECEIVE_BOOT_COMPLETED` (boot)
- `WAKE_LOCK` 🆕 v0.4.0 (AlarmManager fallback)

**Config atual** (`AutoOkConfig.java`):
```java
AVISO_ACTIVITY_NAME = "com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity"
BUTTON_OK_X = 400, BUTTON_OK_Y = 350
TAP_FALLBACK_COORDS = {(400,350), (400,340), (400,360)}
TAP_FALLBACK_INTERVAL_MS = 200
DELAY_SECONDS_AFTER_DETECT = 1
REARM_DELAY_SECONDS = 10
BOOT_INITIAL_WAIT_MS = 2000
WATCHDOG_INTERVAL_SECONDS = 30
// Novos em v0.4.0:
HMI_SERVICE_START_ACTION = "com.mitsubishielectric.ada.appservice.powermanager.ACTION_HMI_SERVICE_START"
ACTION_FORCE_RESTART = "com.khalleb.civichmi.autook.FORCE_RESTART"
ACTION_ALARM_HEALTHCHECK = "com.khalleb.civichmi.autook.ALARM_HEALTHCHECK"
ALARM_HEALTHCHECK_INTERVAL_SECONDS = 60
```

### 10.2 `/system/xbin/su` 🔧

Setuid root ARM. Vindo do `codeage/root-honda` (versão SuperSU-adjacent 2.78 simples).

| Campo | Valor |
|---|---|
| Caminho | `/system/xbin/su` |
| Tamanho | 133472 bytes |
| Modo | `06755` (`-rwsr-sr-x`) |
| Owner | root:root |
| Comportamento | Sem prompt — qualquer app que chamar vira root direto |

### 10.3 Deploy — EvilValet OTA

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

### 11.2 Launcher principal

| Campo | Valor |
|---|---|
| Package | `com.mitsubishielectric.ada.app.dalauncher` |
| Activity principal | `.Launcher` (depois do dismiss do aviso) |
| TaskId | 3 (observado) |

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
Nosso APK não é tratado como "HMI service" pelo PowerManager (está em /system/app mas não é reconhecido pela whitelist Mitsubishi), então o PowerManager **não re-inicia nosso Service** após LP0. Antes da v0.4.0, isso causava o APK ficar silencioso após qualquer LP0.

---

## 12. Pipeline do APK AutoOk (v0.4.0)

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
      ├─ startWatchdog()                 ← Thread "AutoOk-Watchdog" (30s loop)
      └─ scheduleAlarm()  🆕 v0.4.0      ← AlarmManager repete a cada 60s

OU (v0.4.0): Em resposta a HMI_SERVICE_START ou alarm:

HmiServiceReceiver.onReceive()         ← dispara em cada ExitLP0/AccOnRestart
   OU
AlarmReceiver.onReceive()              ← dispara a cada 60s (fallback)
      │
      ▼
startService(AutoOkService, action=ACTION_FORCE_RESTART)
      │
      ▼
AutoOkService.onStartCommand(action=ACTION_FORCE_RESTART)
      │
      └─ forceRestartWatcher()         ← mata watcher antigo + cria novo
                                         (quebra readLine() bloqueado)
      
LogcatWatcher thread:
      │
      ├─ sleep(BOOT_INITIAL_WAIT_MS=2000)
      ├─ Runtime.exec("su") → stdin: "exec logcat -v brief ActivityManager:I *:S"
      ├─ while (running && readLine()):
      │     if (line.contains(NEEDLE)):
      │        callback.onDetected()     ← NÃO retorna! Loop infinito desde v0.3.0
      │
AutoOkService.onAvisoDetected() (chamada pelo watcher):
      │
      ├─ if (handled) return
      ├─ handled = true
      ├─ FileLogger.log("aviso detectado")
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
      ├─ sleep(REARM_DELAY_SECONDS=10)
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
| Versão atual AutoOk | **4** (v0.4.0 — fix do bug de LP0) |
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

---

## 16. Caminhos descartados (⏸)

### 16.1 ⏸ SuperSU como mediator (descartado 2026-10-17)

**Motivo:** nosso `/system/xbin/su` já é o mesmo binário setuid simples que o SuperSU-adjacent. SuperSU "completo" substituiria por um com **prompt via Activity** → `Runtime.exec("su")` do AutoOk ficaria bloqueado esperando toque humano = **quebra o AutoOk**. Pre-populate do database SQLite é frágil (UID muda, corrupção). APK é único consumidor de root; UI inútil aqui.

**Veredito:** não vale. Marcar como "não voltar a considerar".

### 16.2 ⏸ Xposed Framework (adiado 2026-10-17)

**Motivo:** Xposed v54 é a última compatível com Android 4.2.2 (API 17). Patch do `/system/bin/app_process` é destrutivo (binário crítico do boot). Qualquer problema = **bootloop permanente**, só recuperável via rollback OTA (10+ min por tentativa). **Zero precedente público** de Xposed em Mitsubishi Andromeda — Zygote customizado deles pode causar incompatibilidade.

**Veredito:** reconsiderar só se tiver central de testes dedicada, OU após 6+ meses rodando APK atual sem problema. Alternativa menos invasiva: smali-patch no DaLauncher (surface menor).

### 16.3 ✗ Modificar DaLauncher.apk via smali (não feito)

**Motivo:** benefício seria aviso realmente nunca aparecer. Risco: brick do launcher = tela preta no boot = precisa rollback OTA de emergência. Rede de segurança existe (dump raw bootable + rollback OTA pronto), mas custo-benefício não compensa dado que AutoOk v0.3.0 funciona em ~5s.

**Status:** parado no backlog; só fazer se Xposed-equivalente for necessário (zero delay real).

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

### 19.6 Referências de terceiros

- https://github.com/codeage/root-honda — su setuid + SuperSU + whitelist Mitsubishi
- https://github.com/jersacct/2016PilotOneClick — rooteador de Honda Pilot 2016
- https://github.com/librick/ic1101 — pesquisa RE completa + ota-builder (base do nosso build)
- https://juniperspring.org — artigo original Eric McDonald sobre EvilValet

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

---

**Fim do MAPA. Última atualização: 2026-10-17 após deep-scan v2.**
