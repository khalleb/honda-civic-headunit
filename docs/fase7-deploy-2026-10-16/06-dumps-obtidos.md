# Dumps obtidos — catálogo completo

Durante a Fase 7, construímos pacote OTA de dump que copiou 197MB de `/system` da central para o pendrive, sem precisar de ADB. Esse dump é a fonte da verdade do estado da central Civic 2017 BR `1.F187.16` **pré nossa modificação** (sem APK auto-OK, sem su).

Guardar esse dump no projeto é essencial — qualquer análise futura, troubleshoot ou reversão depende dele. Se precisar comparar "estado atual vs estado original", é esse snapshot a referência.

## Local

```
tooling/apks-dumped/dump-0040/
```

Tamanho total: 197 MB. Caminho relativo ao projeto. Não está no `.gitignore` — considerar se o Git LFS seria apropriado se o repo crescer.

## Como foi coletado

Deploy OTA do pacote de "dump mode" (versão temporária do `build.py` da Fase 7, hoje substituída pelo build de instalação). Updater-script executava no recovery:

```sh
# Via busybox (extraído do pacote em /tmp/busybox)
mount -o ro /dev/block/platform/sdhci-tegra.3/by-name/APP /tmp/sys
mount -o ro /dev/block/platform/sdhci-tegra.3/by-name/CAP /tmp/ven

cp /tmp/sys/build.prop /mnt/usbdrive1/dump-0040/system-build.prop
cp /tmp/ven/build.prop /mnt/usbdrive1/dump-0040/vendor-build.prop

cp -a /tmp/sys/app/.         /mnt/usbdrive1/dump-0040/system-app/
cp -a /tmp/sys/priv-app/.    /mnt/usbdrive1/dump-0040/system-priv-app/
cp -a /tmp/sys/framework/.   /mnt/usbdrive1/dump-0040/system-framework/
cp -a /tmp/ven/app/.         /mnt/usbdrive1/dump-0040/vendor-app/
cp -a /tmp/sys/etc/.         /mnt/usbdrive1/dump-0040/system-etc/
```

Depois disso, FAT32 do pendrive foi montado no notebook e os arquivos copiados pro projeto via `rsync -a --no-perms --no-owner --no-group`.

**Perdas na cópia:**

- **Symlinks:** FAT32 não suporta. `cp -a` emite warnings mas copia o resto. Faltam no dump:
  - `/system/framework/HeaderService.jar + odex`
  - `/system/framework/HondaNavigationLib.jar + odex`
  - `/system/framework/HondaTelematicsLib.jar + odex`
  - `/system/framework/UiLib.jar + odex`
  - `/system/framework/WhitelistLib.jar + odex`
  - `/system/framework/honda-framework.jar + odex`
  - `/system/framework/framework-res.apk`
  - Alguns arquivos em `vendor/app/` (`com.aha.android.app.apk`, `com.honda.displayaudio.navi.apk`, etc.)
  - Alguns em `system/etc/` (`init.goldfish.sh`, `ppp/*`, etc.)

- **Ownership (uid/gid):** FAT32 não guarda. Tudo fica como `<user>:<user>` ao copiar pro notebook.
- **Mode bits:** FAT32 só tem rw via mask. Setuid, setgid, sticky bits perdidos.
- **Timestamps:** parcialmente preservados (mdate).

Para re-dumpar com symlinks resolvidos (`cp -L` segue symlinks em vez de copiá-los), seria necessário rebuildar pacote OTA de dump com `-L` no cp e redeployar. Não feito nesta sessão — o que temos é suficiente pra tudo que precisamos.

## Estrutura do dump

```
tooling/apks-dumped/dump-0040/
├── dump.log                              # log do updater-script no recovery
├── system-build.prop                     # /system/build.prop (1.9 KB)
├── vendor-build.prop                     # /system/vendor/build.prop (68 bytes)
├── system-ls.txt                         # ls -la do root de /system
├── system-app-ls.txt                     # ls -la de /system/app
├── system-priv-app-ls.txt                # ls -la (vazio na nossa safra)
├── vendor-ls.txt                         # ls -la de /system/vendor
├── system-app/                           # 40 APKs + odex (41 MB)
├── system-priv-app/                      # vazio (safra pré-4.3 não tem priv-app)
├── system-framework/                     # 48 JARs (25 MB, parcial)
├── system-etc/                           # 6.7 MB
└── vendor-app/                           # 50+ APKs (125 MB)
```

## `dump.log`

```
=== START Fri Oct 16 12:51:22 UTC 2026 ===
mounted APP in /tmp/sys exit=0
mounted CAP in /tmp/ven exit=0
copy-system-app exit=0
cp: can't stat '/tmp/sys/priv-app/.': No such file or directory
copy-system-priv-app exit=1
cp: can't create symlink '.../system-framework/./framework-res.apk': Operation not permitted
cp: can't create symlink '.../system-framework/./HeaderService.jar': Operation not permitted
cp: can't create symlink '.../system-framework/./HeaderService.odex': Operation not permitted
cp: can't create symlink '.../system-framework/./HondaNavigationLib.jar': Operation not permitted
cp: can't create symlink '.../system-framework/./HondaNavigationLib.odex': Operation not permitted
cp: can't create symlink '.../system-framework/./HondaTelematicsLib.jar': Operation not permitted
cp: can't create symlink '.../system-framework/./HondaTelematicsLib.odex': Operation not permitted
cp: can't create symlink '.../system-framework/./UiLib.jar': Operation not permitted
cp: can't create symlink '.../system-framework/./UiLib.odex': Operation not permitted
cp: can't create symlink '.../system-framework/./WhitelistLib.jar': Operation not permitted
cp: can't create symlink '.../system-framework/./WhitelistLib.odex': Operation not permitted
cp: can't create symlink '.../system-framework/./honda-framework.jar': Operation not permitted
cp: can't create symlink '.../system-framework/./honda-framework.odex': Operation not permitted
copy-system-framework exit=1
cp: can't create symlink '.../vendor-app/./com.aha.android.app.apk': Operation not permitted
cp: can't create symlink '.../vendor-app/./com.honda.displayaudio.navi.apk': Operation not permitted
cp: can't create symlink '.../vendor-app/./com.honda.displayaudio.whitelist.apk': Operation not permitted
cp: can't create symlink '.../vendor-app/./com.honda.telematics.core.apk': Operation not permitted
cp: can't create symlink '.../vendor-app/./com.yesway.ycarstore.acura.apk': Operation not permitted
cp: can't preserve ownership of '.../vendor-app/.': Operation not permitted
copy-vendor-app exit=1
cp: can't preserve ownership of '.../system-etc/./dbus.conf': Operation not permitted
cp: can't preserve ownership of '.../system-etc/./dhcpcd/dhcpcd-run-hooks': Operation not permitted
cp: can't preserve ownership of '.../system-etc/./init.goldfish.sh': Operation not permitted
cp: can't create symlink '.../system-etc/./ppp/peers/isp': Operation not permitted
cp: can't create symlink '.../system-etc/./ppp/ip-up': Operation not permitted
cp: can't create symlink '.../system-etc/./ppp/ip-down': Operation not permitted
cp: can't create symlink '.../system-etc/./ppp/pap-secrets': Operation not permitted
cp: can't create symlink '.../system-etc/./airplay.conf': Operation not permitted
copy-system-etc exit=1
=== END Fri Oct 16 12:52:06 UTC 2026 ===
```

Total: 44 segundos pra dumpar 197MB (incluindo mount + cp + unmount + sync).

## `system-app/` — 40 APKs do /system/app

Apps padrão Android (AOSP + Honda customizations em framework):

```
ApplicationsProvider.apk/odex       BackupRestoreConfirmation.apk/odex
Browser.apk/odex                    Calculator.apk/odex
Calendar.apk/odex                   CalendarProvider.apk/odex
CertInstaller.apk/odex              Contacts.apk/odex
ContactsProvider.apk/odex           DefaultContainerService.apk/odex
DeskClock.apk/odex                  DownloadProvider.apk/odex
DownloadProviderUi.apk/odex         DrmProvider.apk/odex
FusedLocation.apk/odex              Galaxy4.apk/odex
Gallery2.apk/odex                   HoloSpiralWallpaper.apk/odex
HTMLViewer.apk/odex                 InputDevices.apk/odex
KeyChain.apk/odex                   LiveWallpapers.apk/odex
LiveWallpapersPicker.apk/odex       MagicSmokeWallpapers.apk/odex
MediaProvider.apk/odex              ... (continua)
```

APKs AOSP padrão. Útil para:
- Comparar comportamento com Android stock.
- Verificar se Honda modificou algum (ex: KeyChain, DownloadProvider).
- Fonte de recursos reutilizáveis.

## `system-priv-app/` — vazio

Android 4.3+ introduziu `/system/priv-app` para apps "privilegiados" (grant permissions auto). Nossa safra 4.2.2 **não tem essa pasta** — todos os apps ficam em `/system/app`. Nosso updater-script tentou copiar e falhou com "No such file or directory" (esperado).

Nenhum código no projeto deve assumir que priv-app existe.

## `system-framework/` — 48 JARs (parcial)

AOSP framework completo + parte do Mitsubishi framework (parte faltando por symlinks).

Lista do que foi copiado:
```
am.jar/odex                         android.policy.jar/odex
android.test.runner.jar/odex        apache-xml.jar/odex
bmgr.jar/odex                       bouncycastle.jar/odex
bu.jar/odex                         com.android.location.provider.jar/odex
com.google.widevine.software.drm.jar/odex
content.jar/odex                    core.jar/odex
core-junit.jar/odex                 ext.jar/odex
framework.jar/odex                  ime.jar/odex
input.jar/odex                      javax.obex.jar/odex
mms-common.jar/odex                 monkey.jar/odex
pm.jar/odex                         requestsync.jar/odex
services.jar/odex                   settings.jar/odex
svc.jar/odex                        telephony-common.jar/odex
uiautomator.jar/odex
```

Faltam (symlinks que FAT32 não copiou):
- `HeaderService.jar/odex`
- `HondaNavigationLib.jar/odex`
- `HondaTelematicsLib.jar/odex`
- `UiLib.jar/odex` ← **framework de UI do Mitsubishi** (crítico para RE profundo)
- `WhitelistLib.jar/odex`
- `honda-framework.jar/odex` ← **framework principal Honda**
- `framework-res.apk`

Para re-dumpar os faltantes, modificar updater-script usando `cp -L` ou tar + untar.

## `vendor-app/` — 50+ APKs Mitsubishi (125 MB)

A camada de aplicação do framework Mitsubishi Andromeda. Catálogo completo em [02-descobertas-tecnicas.md § 3](02-descobertas-tecnicas.md#3-framework-mitsubishi-andromeda--apps-catalogados).

Apps mais críticos para análise futura:
- **DaLauncher.apk** (+ odex) — launcher, contém OpeningDivideActivity e DisclaimerFragment (nosso target)
- **DaSettings.apk** — configurações
- **SystemUpdate.apk** — gerencia OTAs (relevante pra EvilValet)
- **UnitInfoManager.apk** — pode ter info persistente útil
- **VehicleCoordination.apk** — coordenação de veículo (CAN?)
- **WhitelistApService.apk** — se tiver Whitelist decifrada, útil

## `system-etc/` — 6.7 MB

Configurações do /system/etc. Útil para entender:
- `dbus.conf` — D-Bus configuration
- `permissions/*.xml` — permission grants
- `init.*` — init scripts (parcial, alguns são symlinks)
- `dhcpcd/`, `ppp/`, `wifi/` — configs de rede
- `audio_policy.conf` — política de áudio

## APKs decodificados até agora

Além do dump bruto, decompilações feitas durante Fase 7:

```
tooling/apks-decoded/
├── HondaHack/                     # HondaHack.apk (do projeto antigo, obfuscado)
├── DaLauncher/                    # apktool decode do nosso DaLauncher
└── DaLauncher-deodexed/           # deodex via baksmali-2.5.2
    └── smali/com/mitsubishielectric/ada/app/dalauncher/
        ├── OpeningDivideActivity.smali       # Activity do Aviso
        ├── DisclaimerFragment.smali          # Fragment do Aviso
        ├── DisclaimerFragment$1.smali        # callbacks
        ├── DisclaimerFragment$2.smali
        ├── ... (5 inner anonymous classes)
        ├── DisclaimerFragment$GetRunOperationControlAsyncTask.smali
        └── DisclaimerFragment$StrgSwEventPriorityCallBackForDisclaimer.smali
```

Deodex do DaLauncher gerou 575 arquivos smali (pacote dalauncher completo, menos partes dependentes de UiLib que não temos).

## Como re-dumpar

Se precisar refazer o dump no futuro (depois de uma update Honda, por exemplo):

### 1. Modificar `build.py` temporariamente

Trocar o updater-script atual (que instala APK + su) pelo updater-script de dump (que só lê e copia). Código salvo em git history — commit da Fase 7 tem a versão original.

### 2. Rebuild + deploy

```bash
rm -rf tooling/ota-build/output/*
python3 tooling/ota-build/build.py
sudo bash ./tooling/scripts/prepare-pendrive-install.sh
# Deployar no carro via protocolo normal
```

### 3. Copiar pro projeto

Depois do deploy, pendrive volta cheio. Monta e copia:

```bash
MP=/run/media/<user>/HONDA_OTA
DEST=tooling/apks-dumped/dump-0040-new
mkdir -p $DEST
rsync -a --no-perms --no-owner --no-group "$MP/dump-0040/" "$DEST/"
```

### 4. Comparar com dump original

```bash
diff -r tooling/apks-dumped/dump-0040 tooling/apks-dumped/dump-0040-new
```

Mostra o que mudou. Se Honda atualizou alguma coisa, diff vai mostrar.

## Observações legais

Esses dumps são do firmware proprietário Mitsubishi/Honda. Guardá-los no repo privado do dono (que é esse) para uso pessoal + reverse engineering para "privacy, interop and research" é geralmente OK sob fair use e proteções do DMCA § 1201(f) para interoperability. **Não redistribuir publicamente.**

O repo é marcado como privado no GitHub. Mantê-lo privado.
