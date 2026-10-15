# Compilar o `our-apk/` no Fedora

Setup prático de build para o AutoOk. Complementa o `../../our-apk/README.md` com o que é específico do Fedora 44.

## Estado do ambiente (verificado em 2026-10-15)

| Componente | Status | Observação |
|---|---|---|
| Java (JDK) | ⚠️ Instalado JDK 25, AGP 7.4.2 precisa 17 | Ver seção 2 |
| Gradle (sistema) | ❌ Não instalado | Vamos usar o gradlew do próprio projeto, não precisa de sistema |
| Android SDK | ❌ Não instalado | Ver seção 3 |
| ADB | ✅ `android-tools` do dnf, versão `1.0.41` | Já ok |
| apktool, jadx | ✅ Baixados em `tooling/bin/` pelo setup inicial | Já ok |

## 1. Por que não instalei automaticamente

Dois motivos para o setup ser **comando documentado para o usuário rodar**, não `dnf install -y` ou curl automatizado:

- **JDK 17 em paralelo com JDK 25** mexe no ambiente Java global (alternatives, JAVA_HOME). Risco de quebrar outras ferramentas que esperam Java 25.
- **Android SDK command-line tools** são ~500MB de download e autoinstalam componentes adicionais no primeiro `sdkmanager`. Ambos pedem aceite de licença EULA explícito.

Então segue o manual.

## 2. Instalar JDK 17

AGP 7.4.2 oficialmente suporta JDK 11-19; mesmo quase rodando com JDK 25, há regressões conhecidas (ex.: compiler plugins quebrados). Melhor manter JDK 17 só para esse projeto.

```bash
sudo dnf install -y java-17-openjdk-devel
```

Isso instala em `/usr/lib/jvm/java-17-openjdk*`. Não troca o default do sistema — o Java 25 segue no `java -version`.

Para apontar o Gradle do projeto para o JDK 17 **sem alterar o default global**, edite `~/.gradle/gradle.properties` (criar se não existir):

```properties
org.gradle.java.home=/usr/lib/jvm/java-17-openjdk
```

Alternativa menos invasiva (só para a sessão atual do shell):

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk
```

Para conferir:

```bash
cd our-apk
./gradlew --version 2>&1 | grep JVM
# deve dizer: JVM: 17.x.x (Red_Hat ...)
```

## 3. Instalar Android SDK (command-line tools)

Não precisa Android Studio inteiro — só o SDK com API 33 + build-tools 33.

### 3.1 Baixar command-line tools

```bash
mkdir -p ~/Android/Sdk/cmdline-tools
cd ~/Android/Sdk/cmdline-tools
curl -L -o cmdtools.zip \
  https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip -q cmdtools.zip
rm cmdtools.zip
mv cmdline-tools latest
```

### 3.2 Configurar `ANDROID_SDK_ROOT` + PATH

Edite `~/.bashrc` (ou `~/.profile`) e adicione:

```bash
export ANDROID_SDK_ROOT=$HOME/Android/Sdk
export PATH=$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools:$PATH
```

Carrega: `source ~/.bashrc`.

### 3.3 Aceitar licenças e instalar os componentes

```bash
yes | sdkmanager --licenses
sdkmanager "platform-tools" "platforms;android-33" "build-tools;33.0.2"
```

Download total: ~400 MB.

## 4. Compilar o `our-apk/`

Com JDK 17 ativo (seção 2) e SDK configurado (seção 3):

```bash
cd ~/repositorios/honda-civic-headunit/our-apk
./gradlew assembleRelease
```

Primeira execução baixa Gradle 7.6 do wrapper (~130 MB) e as libs do build. Depois disso é cache.

Saída esperada: `app/build/outputs/apk/release/app-release-unsigned.apk` (~30 KB — o APK é mínimo).

## 5. Assinar

Para instalação via Honda Installer ou `install_mitsubishi.sh`, qualquer signature serve. Para fins de teste:

```bash
# Chave debug padrão do Android (criada automaticamente se faltar)
~/.android/debug.keystore
```

Se não existir, cria uma na mão:

```bash
keytool -genkey -v -keystore ~/.android/debug.keystore \
    -alias androiddebugkey -storepass android -keypass android \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -dname "CN=Android Debug,O=Android,C=US"
```

Assinar:

```bash
cd our-apk
APK_IN=app/build/outputs/apk/release/app-release-unsigned.apk
APK_OUT=app/build/outputs/apk/release/AutoOk.apk

~/Android/Sdk/build-tools/33.0.2/apksigner sign \
    --ks ~/.android/debug.keystore \
    --ks-key-alias androiddebugkey \
    --ks-pass pass:android --key-pass pass:android \
    --out "$APK_OUT" "$APK_IN"
```

## 6. Extrair SHA-1 do certificado (para a whitelist)

A rota mais robusta é pedir pro próprio `apksigner`:

```bash
"$ANDROID_SDK_ROOT/build-tools/33.0.2/apksigner" verify --print-certs "$APK_OUT" \
  | grep "SHA-1 digest" | awk '{print $NF}'
```

Saída: 40 caracteres hex (ex.: `e3b14e2b697dcdf9245e9988cb0bae8b3b504860` para a debug keystore padrão). Essa string vira o terceiro argumento do `install_mitsubishi.sh` (seção "Opção B" do `our-apk/README.md`).

Alternativa manual (quando `apksigner` não está disponível): o APK v2+ assinado pelo `apksigner` tem o `.RSA` em `META-INF/` com nome dinâmico baseado no alias (ex.: `META-INF/ANDROIDD.RSA` para alias `androiddebugkey`), não `CERT.RSA` fixo. Para extrair direto do arquivo:

```bash
RSA_ENTRY=$(unzip -l "$APK_OUT" | awk '/META-INF\/.*\.RSA/ {print $NF}' | head -1)
unzip -p "$APK_OUT" "$RSA_ENTRY" | \
  openssl pkcs7 -inform DER -print_certs | \
  openssl x509 -fingerprint -noout -sha1 | \
  awk -F= '{print $2}' | tr -d :
```

## 7. Validação sem rodar o APK — o emulador API 17 não sobe mais

**O caminho de rodar num emulador Android 4.2.2 x86 não funciona em distro Linux recente** (testado em Fedora 44, kernel 7.2.8). O `qemu-system-i386` do pacote `emulator` 35.x segmenta logo depois de `Emulator is performing a full startup`, independente de GPU (`off`, `swiftshader`, `swiftshader_indirect`, `guest`) e aceleração (`-no-accel`). O crash é consistente com relatos públicos de incompatibilidade entre as imagens API 17 (de 2013) e o QEMU/Mesa modernos. API 21+ sobe normal, mas aí não é mais Android 4.2.2.

**Alternativa que preserva o que o emulador validaria** — análise estática do APK compilado:

### 7.1 Manifest após merge do AGP

```bash
BT=$ANDROID_SDK_ROOT/build-tools/33.0.2
APK=app/build/outputs/apk/release/AutoOk.apk
"$BT/aapt" dump xmltree "$APK" AndroidManifest.xml
```

O que conferir: `uses-sdk`, `uses-permission`, `<receiver>` com `<intent-filter><action name="android.intent.action.BOOT_COMPLETED"/></intent-filter>`, `<service>` registrado. Se qualquer um estiver faltando, o AGP comeu durante o merge.

### 7.2 Classes DEX e métodos compilados

```bash
"$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/apkanalyzer" dex packages "$APK" | grep com.khalleb
```

Confere nome das classes, campos (`F d`), métodos (`M d`), tamanho em bytes. Para o AutoOk, esperado:

- `AutoOkConfig` (constantes) — campos `AVISO_ACTIVITY_NAME`, `BUTTON_OK_X/Y`, etc.
- `BootReceiver` — `onReceive`
- `AutoOkService` — `onStartCommand`, `onBind`, `onDestroy`, `isConfigValid`, `onAvisoDetected`, `buildWatcher`, `sleepSeconds`, `stopWatcher`
- `LogcatWatcher` + `LogcatWatcher$1` (anon inner) + `LogcatWatcher$OnDetected` (interface)
- `Shell` — `suTap`, `suExec`

### 7.3 Lint focado em bugs reais

```bash
./gradlew :app:lintRelease
```

Isso roda só o lint, sem o build inteiro. Report em HTML em `app/build/reports/lint-results-release.html`. O que importa é zero erro — warnings de style podem ser ignorados.

### 7.4 Checar signature e permissões num comando só

```bash
"$BT/apksigner" verify --print-certs "$APK" | grep -E "SHA-1 digest|SHA-256 digest"
"$BT/aapt" dump permissions "$APK"
```

### 7.5 O que ainda só o carro consegue validar

A validação estática confirma que:

- O APK é parseável pelo `PackageManager` do Android 4.2.2.
- Permissões, componentes e flags estão como declaramos.
- O código Java compila sem erros e as classes estão todas lá.

**O que NÃO consegue validar sem a central:**

- Se `su` existe e o SuperSU/Magisk responde ao `exec("su")` do `LogcatWatcher`.
- Se o `logcat` filtra `ActivityManager:I *:S` como esperado (depende de versão exata do logd).
- Se a `AVISO_ACTIVITY_NAME` que a gente vai preencher aparece mesmo nas linhas que o filtro deixa passar.
- Se `input tap X Y` acerta o botão OK.

Esses quatro só pulam depois que ADB subir no carro.

## 8. Troubleshooting

| Sintoma | Causa provável | Fix |
|---|---|---|
| `./gradlew` erra `Unsupported class file major version 69` | JDK 25 ativo | Setar `org.gradle.java.home` para JDK 17 (seção 2) |
| `./gradlew` erra `SDK location not found` | `ANDROID_SDK_ROOT` não exportado | `source ~/.bashrc` ou criar `local.properties` com `sdk.dir=...` |
| `./gradlew` baixa Gradle lento | Primeira execução | Esperar; depois fica em cache em `~/.gradle/` |
| `apksigner` não achado | Build-tools 33 não instalado | `sdkmanager "build-tools;33.0.2"` |
| `./gradlew` erra `Could not resolve com.android.application` | Sem internet | Acesso à Maven Central e `dl.google.com` precisa estar livre |
