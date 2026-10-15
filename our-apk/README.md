# AutoOk — APK auto-OK do Aviso de abertura

APK próprio para dispensar a tela de "Aviso" na partida do Civic G10 EXL BR. Implementa o algoritmo descrito na seção 4quater do KB (`../central-multimidia-civic-g10-kb.md`) sem usar o Honda Hack pago. Pacote: `com.khalleb.civichmi.autook`.

## Estado

Esqueleto compilável. Falta preencher 3 constantes em `app/src/main/java/com/khalleb/civichmi/autook/AutoOkConfig.java` com dados que só saem do pull via ADB da central (fase 3 do roadmap). Enquanto não forem preenchidas, o `AutoOkService` loga `config pendente...` e encerra.

| Constante | Valor hoje | Como obter |
|---|---|---|
| `AVISO_ACTIVITY_NAME` | `""` | `adb shell "su -c 'logcat -v brief ActivityManager:I *:S'"` com a central ligando, até ver a linha `am_resume_activity` ou `START u0 {cmp=...}` do Aviso. Candidatos (seção 2 do KB): `com.mitsubishielectric.ada.app.dalauncher`, `.dasettings`, `.appmode`. |
| `BUTTON_OK_X` | `-1` | Dev options → Pointer location + bater o OK; ou `screencap -p /sdcard/aviso.png` + `adb pull` + abrir no PC e medir. |
| `BUTTON_OK_Y` | `-1` | Idem. |

Opcionais:

| Constante | Default | Observação |
|---|---|---|
| `DELAY_SECONDS_AFTER_DETECT` | `2` | Espera depois que a Activity do Aviso é vista no logcat, antes de disparar o tap. HondaHack permite 1-10s. |
| `BOOT_INITIAL_WAIT_MS` | `5000` | Espera inicial depois do `BOOT_COMPLETED` antes de observar o logcat. |

## Como funciona

1. `BootReceiver` escuta `BOOT_COMPLETED` e sobe o `AutoOkService`.
2. `AutoOkService` valida a config; se faltar coisa, aborta via `Log.e` sem efeitos colaterais.
3. `LogcatWatcher` executa `su -c "logcat -v brief ActivityManager:I *:S"` numa thread e lê linha a linha procurando `AVISO_ACTIVITY_NAME` como substring. **Rodar o logcat via `su` dispensa a permissão `READ_LOGS` que normalmente é `signature|system`** — mesmo caminho que o HondaHack usa (ver `../docs/fase4-analise-estatica/honda-installer.md`).
4. Ao achar, chama de volta o service, que espera `DELAY_SECONDS_AFTER_DETECT` e dispara `su -c "input tap X Y"` via `Shell`.
5. Executado o tap, encerra watcher e service (one-shot por ignição).

Permissões declaradas no manifest: `RECEIVE_BOOT_COMPLETED`, `READ_LOGS`, `ACCESS_SUPERUSER`. `READ_LOGS` fica como best-effort — se por qualquer motivo o APK virar system app, continua funcionando sem `su`; se for user app comum (fluxo recomendado), cai no `su` do passo 3. `ACCESS_SUPERUSER` é consumido pelo SuperSU instalado via `root-honda` (fase 6).

## Compilar

Pré-requisitos: Android SDK (API 33 para compile; build-tools 33), `ANDROID_SDK_ROOT` apontado. **Para setup no Fedora** (instalação do JDK 17, SDK command-line tools, troubleshooting), ver `../docs/fase5-apk/compilar.md`.

```bash
cd our-apk
./gradlew assembleRelease
```

Saída: `app/build/outputs/apk/release/app-release-unsigned.apk`. Assinar com qualquer keystore (debug serve para testes; release para distribuição):

```bash
# Chave debug (desenvolvimento)
apksigner sign --ks ~/.android/debug.keystore \
  --ks-key-alias androiddebugkey \
  --ks-pass pass:android --key-pass pass:android \
  --out AutoOk-signed.apk app-release-unsigned.apk
```

Qualquer signature serve para a whitelist Mitsubishi — ela aceita `null` como `keyStore` ou qualquer hash SHA do CERT.RSA. Ver `../docs/fase4-analise-estatica/hondahack-mitsubishi.md` seção 5.

## Instalar como user app (fluxo recomendado)

Pré-requisitos acumulados: central já rooteada (fase 6) **e** com o Honda Installer instalado em `/system/app/` (seguir `root-honda/` + copiar `honda_installer.apk` para a central). A partir daí nosso APK é tratado como qualquer app terceiro:

### Opção A — Pelo Honda Installer (mais simples)

1. `adb push AutoOk-signed.apk /sdcard/Download/AutoOk.apk`.
2. Na central: abrir "Honda Installer" → "Install an app" → escolher `AutoOk.apk`.
3. O Installer extrai signature, edita `/data/data/whitelist-1.0.xml` via `install_mitsubishi.sh`, pede reboot.
4. Após reboot: `pm install -r` roda automaticamente ao reabrir o Installer; AutoOk fica instalado como user app.

### Opção B — Direto via ADB (sem Honda Installer)

Se por qualquer motivo o Installer não estiver na central, o fluxo manual replica o que ele faria. Pré-condição: central rooteada.

1. `adb push AutoOk-signed.apk /sdcard/Download/AutoOk.apk`
2. `adb push install_mitsubishi.sh /data/local/tmp/` (copiar o script de `tooling/apks-decoded/HondaHack/res/raw/`)
3. `adb shell`, depois `su`, depois:
   ```sh
   chmod 755 /data/local/tmp/install_mitsubishi.sh
   /data/local/tmp/install_mitsubishi.sh \
       /sdcard/Download/AutoOk.apk \
       com.khalleb.civichmi.autook \
       "<SHA-1 do CERT.RSA do nosso APK>" \
       no \
       no
   ```
4. Reboot da central (`long press AUDIO 5s → reboot`).

Para extrair a SHA-1 do certificado do APK assinado, no PC — rota robusta via `apksigner`:

```bash
"$ANDROID_SDK_ROOT/build-tools/33.0.2/apksigner" verify --print-certs AutoOk-signed.apk \
  | grep "SHA-1 digest" | awk '{print $NF}'
```

A rota pelo `META-INF/*.RSA` funciona, mas o apksigner v2+ nomeia o entry dinamicamente a partir do alias do keystore (ex.: `META-INF/ANDROIDD.RSA` quando o alias é `androiddebugkey`), **não** `CERT.RSA` fixo. Ver `../docs/fase5-apk/compilar.md` seção 6 para a versão robusta.

### O que NÃO precisa (ao contrário do que o README anterior dizia)

- ❌ Copiar o APK para `/system/app/`
- ❌ `mount -o remount,rw /system`
- ❌ Resetar `android:sharedUserId` para `android.uid.system`
- ❌ Nada em `/system/`

Isso é consequência da análise estática do `honda_installer.apk` (ver `../docs/fase4-analise-estatica/honda-installer.md` seção 9) — ele mostra que o único componente que precisa viver em `/system/app/` é o próprio Installer. User apps rodam normal depois da whitelist.

## Ver logs

```bash
adb logcat -s AutoOk:*
```

Mensagens relevantes:

- `watcher iniciado, aguardando <Activity>` — serviço subiu, config válida.
- `config pendente de preenchimento em AutoOkConfig` — constantes placeholder.
- `tap X,Y -> true` — `su -c "input tap"` saiu com exit 0.
- `tap X,Y -> false` — `su` negou ou o tap deu erro.
- `logcat watch falhou: <mensagem>` — a thread do watcher parou (central sem `su`? processo logcat morreu?).
- `su exec IOException: ...` — binário `su` indisponível (central não rooteada).

## Riscos operacionais

Nenhum dos fluxos acima mexe em `/system/`, então **o risco de brick é baixíssimo**. Pior cenário realista: o AutoOk fica em loop tentando o tap em coordenada errada e consome bateria enquanto o carro está em acessório. Para desarmar: `adb shell pm disable com.khalleb.civichmi.autook` (reversível) ou `adb shell pm uninstall com.khalleb.civichmi.autook` (remove de vez).

O que **PODE** gerar brick:
- A fase de root (dirtyCOW), que é anterior a este APK.
- Copiar o `honda_installer.apk` para `/system/app/` manualmente errado — mas isso também é anterior.

Depois que a central está rooteada e com o Installer, nosso APK em si é totalmente reversível.

## Estrutura do módulo

```
our-apk/
├── build.gradle               (plugin AGP 7.4.2, apply false)
├── settings.gradle
├── gradle.properties
├── README.md                   (este arquivo)
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
            ├── LogcatWatcher.java    (su -c "logcat ..." em thread própria)
            └── Shell.java            (su -c "input tap X Y")
```
