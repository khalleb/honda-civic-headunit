# AutoOk — APK auto-OK do Aviso de abertura

APK próprio para dispensar a tela de "Aviso" na partida do Civic G10. Implementa o algoritmo descrito na seção 4quater do KB (`../central-multimidia-civic-g10-kb.md`) sem usar o Honda Hack. Pacote: `com.khalleb.civichmi.autook`.

## Estado

Esqueleto compilável. Falta preencher 3 constantes em `app/src/main/java/com/khalleb/civichmi/autook/AutoOkConfig.java` com dados que só saem do pull via ADB da central (Fase 3). Enquanto não forem preenchidas, o `AutoOkService` loga `config pendente...` e encerra — fail-fast de propósito.

| Constante | Valor hoje | Como obter |
|---|---|---|
| `AVISO_ACTIVITY_NAME` | `""` | Rodar `logcat ActivityManager:I *:S` na central logo após ligar, até ver o Aviso. A linha de `am_resume_activity` ou `START u0 {cmp=...}` traz o pacote/Activity. |
| `BUTTON_OK_X` | `-1` | Coord X do botão OK em pixel. Ativar "Pointer location" nas dev options (ou tirar screenshot via `screencap` + abrir no PC) com o Aviso na tela. |
| `BUTTON_OK_Y` | `-1` | Idem para Y. |

Opcional:

| Constante | Default | Observação |
|---|---|---|
| `DELAY_SECONDS_AFTER_DETECT` | `2` | Espera depois que a Activity do Aviso é vista no logcat, antes de disparar o tap. HondaHack permite 1–10s. |
| `BOOT_INITIAL_WAIT_MS` | `5000` | Espera inicial depois do `BOOT_COMPLETED` antes de começar a observar o logcat. |

## Como funciona

1. `BootReceiver` escuta `BOOT_COMPLETED` e sobe o `AutoOkService`.
2. `AutoOkService` valida a config; se faltar coisa, aborta.
3. `LogcatWatcher` roda `logcat -v brief ActivityManager:I *:S` numa thread e lê linha a linha procurando `AVISO_ACTIVITY_NAME` como substring.
4. Ao achar, chama de volta o service, que espera `DELAY_SECONDS_AFTER_DETECT` e dispara `su -c "input tap X Y"` via `Shell`.
5. Executado com sucesso ou não, encerra o watcher e o service (one-shot por ignição).

Perms declaradas: `RECEIVE_BOOT_COMPLETED`, `READ_LOGS`, `ACCESS_SUPERUSER`. `READ_LOGS` em API 17 é `signature|system` — por isso o APK só vai funcionar instalado como **system app**, não como user app.

## Compilar

Pré-requisitos: Android SDK (API 33 para compile; build-tools 33). Com `ANDROID_SDK_ROOT` apontado:

```bash
cd our-apk
./gradlew assembleRelease
```

Saída: `app/build/outputs/apk/release/app-release-unsigned.apk`. Para instalar como system app, o APK precisa ser alinhado e assinado (ou copiado direto para `/system/app/AutoOk/AutoOk.apk` com root — nesse caso a assinatura system pode ser dispensada em algumas configurações; na nossa central Mitsubishi ainda é incógnita, ver seção de whitelist no KB).

## Instalar como system app (fluxo esperado, não executado ainda)

Pré-condição: central já rooteada seguindo a doc do `root-honda` (fase 6). Backup de `/system` antes.

```bash
adb push app-release-unsigned.apk /sdcard/AutoOk.apk
adb shell
su
mount -o remount,rw /system
mkdir -p /system/app/AutoOk
cp /sdcard/AutoOk.apk /system/app/AutoOk/AutoOk.apk
chmod 644 /system/app/AutoOk/AutoOk.apk
```

Depois, pela regra de whitelist descrita no KB (seção 4quater), editar `/data/data/whitelist-1.0.xml` adicionando o pacote `com.khalleb.civichmi.autook` com a signature do APK (`GetAndroidSig.jar`). Reboot da central (`long press AUDIO 5s → reboot`).

## Ver logs

```bash
adb logcat -s AutoOk:*
```

Mensagens relevantes:

- `watcher iniciado, aguardando <Activity>` — subiu.
- `config pendente de preenchimento em AutoOkConfig` — constantes vazias/`-1`.
- `tap X,Y -> true` — comando `su input tap` saiu com exit 0.
- `logcat watch falhou: ...` — erro ao abrir o processo logcat (sem READ_LOGS?).
- `su exec IOException: ...` — `su` não disponível ou negou.

## Estrutura do módulo

```
our-apk/
├── build.gradle               (plugin AGP 7.4.2, apply false)
├── settings.gradle
├── gradle.properties
├── README.md
└── app/
    ├── build.gradle           (minSdk/targetSdk 17, compileSdk 33)
    ├── proguard-rules.pro
    └── src/main/
        ├── AndroidManifest.xml
        ├── res/values/strings.xml
        └── java/com/khalleb/civichmi/autook/
            ├── AutoOkConfig.java     (constantes a preencher)
            ├── BootReceiver.java     (BOOT_COMPLETED -> service)
            ├── AutoOkService.java    (orquestra: valida, observa, tap, encerra)
            ├── LogcatWatcher.java    (tail do logcat em thread própria)
            └── Shell.java            (su -c "input tap X Y")
```
