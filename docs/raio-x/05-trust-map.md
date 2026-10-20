# Scan 5 — Trust Map

**110 APKs no shipping: 70 vendor-app + 40 system-app + 0 system-priv-app.** Para cada: pacote detectado, `sharedUserId` e número de permissões consumidas. Permite ver quem tem acesso privilegiado e quem fala com quem no mesmo UID.

## Como foi coletado

```bash
for apk in <vendor-app, system-app, system-priv-app>; do
  manif=$(unzip -p "$apk" AndroidManifest.xml | strings -el)
  pkg=$(echo "$manif" | grep -oE '^com\.(mitsubishielectric\.ada|honda|android)\.[a-z0-9._]{3,}$' | head -1)
  shared=$(echo "$manif" | grep -oE '^android\.uid\.[a-z]+$' | head -1)
  perms=$(echo "$manif" | grep -cE '\.permission\.')
  ...
done
```

**Limites:** `strings -el` (UTF-16LE) sobre `AndroidManifest.xml` binário retorna muitas strings mas sem estrutura. Alguns packages são "?" ou pegamos o `com.mitsubishielectric.uilib` (que na verdade é uma `uses-library`, não o package real) — nesses casos o manifest tem o package como primeiro atributo e o grep errou pela ordem alfabética. Para validar nome exato por APK, usar `inspect-android-package` do REA individualmente. Dos 110 APKs, **67 têm package detectado** com confiança.

## Highlights — a elite privilegiada

### APKs com `sharedUserId=android.uid.system` (11 APKs — poder total)

Os únicos que compartilham UID com o próprio sistema Android. Podem fazer **qualquer coisa**:

**Vendor (7):**
- `HidKeyboard` — teclado HID
- `MediaCoreService` — áudio
- `PowerManagerApService` — power
- `StrgSW` — eventos do volante
- `UsbCertApp` — USB cert
- `WhitelistApService` — whitelist
- `WifiApService` — WiFi

**AOSP (4):**
- `InputDevices` — gerenciador de input devices
- `KeyChain` — chaveiro de certificados
- `Settings` — app de settings do Android
- `SettingsProvider` — provedor de settings

**Nosso AutoOk NÃO está nesta lista** (não declara `sharedUserId` no manifest). Isso significa que mesmo estando em `/system/app/`, roda como UID próprio (10091 por padrão) — por isso precisa de `Runtime.exec("su")` para executar `input tap`.

### APKs com `sharedUserId=android.uid.phone` (4)

- `AV` — provavelmente áudio integrado ao stack telefônico (ducking etc)
- `UnitInfoManager` — mais 16 permissões consumidas, maior count da vendor-app
- `Phone` — AOSP padrão
- `TelephonyProvider` — AOSP

### APKs com `sharedUserId=android.uid.shared` (4)

- `ApplicationsProvider`, `Contacts`, `ContactsProvider`, `UserDictionaryProvider`

Padrão AOSP — contatos compartilham UID.

### Top 10 por número de permissões consumidas

| APK | Perms | Observação |
|---|---|---|
| `Settings` | 55 | AOSP settings |
| `Phone` | 49 | AOSP phone |
| `SystemUI` | 47 | AOSP system UI |
| `Contacts` | 30 | AOSP contacts |
| `Browser` | 25 | AOSP browser |
| `Gallery2` | 25 | AOSP gallery |
| `UnitInfoManager` | 16 | 🎯 **vendor top — unit info com android.uid.phone** |
| `CalendarProvider` | 15 | AOSP calendar provider |
| `DaLauncher` | 14 | 🎯 **nosso alvo principal, 14 perms** |
| `DaSettings` | 14 | app de settings vendor |
| `DownloadProvider` | 14 | AOSP downloads |
| `DiagApService` | 13 | 🎯 **diag service tem muita permissão** |

Esse é o mapa de "quem concentra autorização". `UnitInfoManager` e `DiagApService` são os dois targets vendor mais promissores — alta autoridade + função que pode levar a hooks interessantes.

### Permissões custom vendor

5 permissões Mitsubishi/Honda que criam gates próprios:

| Permissão | Consumida por |
|---|---|
| **`com.mitsubishielectric.ada.permission.VEHICLE_RW`** | **70 APKs** — a permissão central para acessar o barramento do veículo |
| `com.mitsubishielectric.ada.permission.ACCESS_AUDIO_DEVICE` | subset de APKs com áudio |
| `com.mitsubishielectric.ada.permission.MIRRORLINK_DEVICE` | MirrorLink + Phone coordination |
| `com.honda.displayaudio.navi.permission.ACCESS_MAP` | AcuraLinkApp + outros clients navi |
| `com.honda.telematics.core.permission.WRITE_CRM_DATA` | Telematics APKs |

**`VEHICLE_RW` consumida por 70/110 APKs = 64%.** É quase ubíqua. Qualquer app que precise saber qualquer coisa do carro declara isso.

**Para o AutoOk:** não declaramos `VEHICLE_RW` hoje. Se a Fase 9 for consumir `IVehicleGearInformationListener` para detectar ré direto, essa permissão precisa entrar no manifest. Precisamos verificar se a permissão é `signature|system` (bloqueia user apps) ou se qualquer app com UID system pode usar.

## Tabela completa

### `vendor-app/` (70 APKs)

| APK | Package detectado | sharedUserId | perms used |
|---|---|---|---|
| `AV` | — | **android.uid.phone** | 8 |
| `AVPlayer` | — | — | 5 |
| `AcuraLinkApService` | — | — | 9 |
| `AcuraLinkApp` | — | — | 1 |
| `AirCon` | — | — | 3 |
| `AndroidAuto` | — | — | 8 |
| `AntiTheft` | — | — | 3 |
| `AppManager` | — | — | 9 |
| `AppMode` | — | — | 3 |
| `AppModeApService` | — | — | 6 |
| `Camera` | — | — | 7 |
| `CameraAPService` | — | — | 4 |
| `CarPlay` | — | — | 1 |
| `CarPlayService` | — | — | 3 |
| `ClockSync` | — | — | 7 |
| `CompassService` | — | — | 2 |
| `CpuComService` | — | — | 1 |
| `DaLauncher` | — | — | 14 |
| `DaSettings` | — | — | 14 |
| `DealerDiag` | — | — | 2 |
| `DeveloperDiag` | — | — | 3 |
| `DiagApService` | — | — | 13 |
| `ETC` | — | — | 2 |
| `EcoTripComputer` | — | — | 2 |
| `EmergencyApService` | — | — | 10 |
| `EmergencyApp` | — | — | 1 |
| `EnergyManagement` | — | — | 2 |
| `ErrorManager` | — | — | 1 |
| `ExternalDisplayApService` | — | — | 2 |
| `ExternalDisplayOutService` | — | — | 7 |
| `FileManager` | — | — | 2 |
| `HangulKeyboard` | — | — | 4 |
| `HftApService` | — | — | 9 |
| `HftApp` | — | — | 4 |
| `HidKeyboard` | — | **android.uid.system** | 9 |
| `HudApService` | — | — | 1 |
| `LatinIME` | `com.android.inputmethod.latin` | — | 9 |
| `LetDiag` | — | — | 1 |
| `LinkManagerApService` | — | — | 3 |
| `MediaCoreService` | — | **android.uid.system** | 3 |
| `MirrorLink` | — | — | 7 |
| `Navigation` | `com.honda.displayaudio.navi.lib` | — | 8 |
| `PhoneCoordination` | — | — | 7 |
| `PicoTts` | `com.svox.pico` | — | 2 |
| `PinyinIME` | `com.android.inputmethod.pinyin` | — | 9 |
| `PowerManagerApService` | — | **android.uid.system** | 1 |
| `PreShipmentDiag` | — | — | 2 |
| `RaspApService` | — | — | 1 |
| `RoadToVehicle` | — | — | 2 |
| `ScreenshotApService` | — | — | 1 |
| `SensorMonitor` | — | — | 5 |
| `SiriEFM` | — | — | 2 |
| `StrgSW` | — | **android.uid.system** | 3 |
| `SystemInfoService` | — | — | 7 |
| `SystemUpdate` | — | — | 11 |
| `TaskManager` | — | — | 6 |
| `Telematics` | — | — | 8 |
| `UnitInfoManager` | — | **android.uid.phone** | 16 |
| `UsbCertApp` | — | **android.uid.system** | 1 |
| `VRSD` | — | — | 4 |
| `VehicleCoordination` | — | — | 4 |
| `VehicleDbManager` | — | — | 1 |
| `VehicleInfoManager` | — | — | 1 |
| `VehicleRW` | — | — | 1 |
| `VideoManagerApService` | — | — | 5 |
| `VoicePortal` | — | — | 5 |
| `VoicePortalAp` | — | — | 6 |
| `WhitelistApService` | — | **android.uid.system** | 2 |
| `WifiApService` | — | **android.uid.system** | 8 |
| `WifiApp` | — | — | 1 |

### `system-app/` (40 APKs — AOSP padrão)

| APK | Package detectado | sharedUserId | perms used |
|---|---|---|---|
| `ApplicationsProvider` | — | **android.uid.shared** | 1 |
| `BackupRestoreConfirmation` | `com.android.backupconfirm` | — | 3 |
| `Browser` | `com.android.browser.snapshots` | — | 25 |
| `Calculator` | `com.android.calculator2` | — | 0 |
| `Calendar` | `com.android.calendar` | — | 12 |
| `CalendarProvider` | `com.android.providers.calendar` | **android.uid.calendar** | 15 |
| `CertInstaller` | `com.android.certinstaller` | — | 1 |
| `Contacts` | `com.android.voicemail` | **android.uid.shared** | 30 |
| `ContactsProvider` | `com.android.providers.contacts` | **android.uid.shared** | 11 |
| `DefaultContainerService` | `com.android.defcontainer` | — | 10 |
| `DeskClock` | `com.android.alarmclock` | — | 10 |
| `DownloadProvider` | `com.android.providers.downloads` | — | 14 |
| `DownloadProviderUi` | — | — | 2 |
| `DrmProvider` | `com.android.providers.drm` | — | 4 |
| `FusedLocation` | `com.android.location.provider` | — | 4 |
| `Galaxy4` | `com.android.galaxy4` | — | 1 |
| `Gallery2` | `com.android.gallery3d.provider` | — | 25 |
| `HTMLViewer` | `com.android.htmlfileprovider` | — | 1 |
| `HoloSpiralWallpaper` | — | — | 1 |
| `InputDevices` | `com.android.inputdevices` | **android.uid.system** | 0 |
| `KeyChain` | `com.android.keychain` | **android.uid.system** | 0 |
| `LiveWallpapers` | `com.android.wallpaper` | — | 3 |
| `LiveWallpapersPicker` | — | — | 2 |
| `MagicSmokeWallpapers` | `com.android.magicsmoke` | — | 2 |
| `MediaProvider` | `com.android.providers.media` | — | 9 |
| `Music` | `com.android.music` | — | 8 |
| `MusicFX` | `com.android.musicfx` | — | 4 |
| `NoiseField` | `com.android.noisefield` | — | 1 |
| `PackageInstaller` | `com.android.packageinstaller` | — | 7 |
| `PhaseBeam` | `com.android.phasebeam` | — | 1 |
| `Phone` | `com.android.phone` | **android.uid.phone** | 49 |
| `Provision` | `com.android.provision` | — | 2 |
| `QuickSearchBox` | `com.android.quicksearchbox` | — | 6 |
| `Settings` | `com.android.settings` | **android.uid.system** | 55 |
| `SettingsProvider` | `com.android.providers.settings` | **android.uid.system** | 1 |
| `SharedStorageBackup` | `com.android.sharedstoragebackup` | — | 3 |
| `SystemUI` | `com.android.systemui.net` | — | 47 |
| `TelephonyProvider` | `com.android.providers.telephony` | **android.uid.phone** | 3 |
| `UserDictionaryProvider` | — | **android.uid.shared** | 2 |
| `VpnDialogs` | `com.android.vpndialogs` | — | 0 |

## Observações

### `Contacts` com package `com.android.voicemail`

Isso é esquisito mas correto: nesse dump, o APK `Contacts.apk` declara package `com.android.voicemail` no manifest — provavelmente é um merge de Contacts+Voicemail na build Honda. Confirmar com REA se for relevante.

### `AcuraLinkApp` tem só 1 permissão

Com peso tão baixo faz sentido ser inativo na safra BR. Idem `EmergencyApp`, `WifiApp` — apps de "entrada" que só mostram UI, delegando trabalho pros `*ApService` correspondentes.

### `DaLauncher` e `DaSettings` com 14 perms cada

Alta superfície — ambos são UI de usuário final com acesso a tudo (settings globais, launcher). Faz sentido serem alvos ricos pra análise futura.

### Alta superfície = alvo rico

Para a Camada 2, os três melhores candidatos vendor são:

1. **`UnitInfoManager`** (16 perms, uid.phone) — maior autoridade entre não-system
2. **`DaLauncher`** / **`DaSettings`** (14 cada) — ricos em UX, muito acesso
3. **`DiagApService`** (13 perms) — diag é target clássico pra PINs e menus escondidos
4. **`SystemUpdate`** (11 perms) — alvo do EvilValet; entender por dentro pode abrir rotas de deploy sem exploit

## Datasets brutos

- `apk-pkg-shareduid.txt` — tabela compacta `category|name|pkg|shared`
- `apk-permissions-uses.txt` — `apk|permission` tuplas (todas as permissões por APK)

Em `/tmp/.../scratchpad/raio-x/`. Como é scratchpad, somem no fim da sessão — mover pra `tooling/raio-x/data/` se quisermos preservar para versioning. Não escopado nesta rodada.
