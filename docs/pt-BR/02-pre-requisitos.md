# 02 — Pré-requisitos

Tudo que você precisa ter antes de executar o deploy.

**Tempo total pra setup:** ~30 minutos no notebook (uma vez). Depois disso, build + deploy roda em ~20 minutos cada vez.

---

## Hardware

| Item | Especificação | Obrigatório |
|---|---|---|
| **Honda Civic G10** | 2017 EXL BR com DA version `1.F187.16` (confirmado) ou safra adjacente que você vai adaptar | Sim |
| **Notebook/PC** | Linux (Fedora, Ubuntu, Debian, Arch — qualquer distribuição com `glibc` moderna) | Sim |
| **Pendrive USB-A** | ≥ 100 MB livre para pacote INSTALL. ≥ 2 GB se for fazer dump raw bootable | Sim |
| **Pendrive USB-A extra** | Opcional — carregado com pacote ROLLBACK, deixado no porta-luvas por garantia | Recomendado |
| **Acesso físico ao carro** | Pra inserir pendrive, segurar AUDIO 5s, observar barra de progresso | Sim |

**Nota sobre o pendrive:**
- Precisa ser **USB-A** (não USB-C) — a porta frontal do Civic é A.
- FAT32 MSDOS formatação (nosso script formata se preciso).
- Sem partições múltiplas — uma só primária FAT32.
- Pendrives muito grandes (>128GB) podem ter problemas de reconhecimento em alguns BIOS automotivos. Prefira 8-32GB.

---

## Software

### Dependências de sistema

**Fedora:**
```bash
sudo dnf install -y java-17-openjdk-devel android-tools git curl unzip \
                    parted dosfstools python3 zip imagemagick
```

**Ubuntu / Debian:**
```bash
sudo apt install -y openjdk-17-jdk android-tools-adb git curl unzip \
                    parted dosfstools python3 zip imagemagick
```

**Arch:**
```bash
sudo pacman -S jdk17-openjdk android-tools git curl unzip parted dosfstools \
               python zip imagemagick
```

### Android SDK (para `apksigner`)

```bash
# Baixar command-line tools
mkdir -p ~/sdks/Android/cmdline-tools
cd ~/sdks/Android/cmdline-tools
curl -L -o cmdtools.zip \
  https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip cmdtools.zip && rm cmdtools.zip && mv cmdline-tools latest

# Exportar paths
export ANDROID_SDK_ROOT=~/sdks/Android
export PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin

# Aceitar licenças
yes | sdkmanager --licenses

# Instalar build-tools 33 (requer o apksigner v2+)
sdkmanager "build-tools;33.0.2"
```

Depois, pra persistir:
```bash
echo 'export ANDROID_SDK_ROOT=~/sdks/Android' >> ~/.bashrc
echo 'export PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin' >> ~/.bashrc
```

### JDK 17 (não 21+, não 11-)

**Importante:** AGP 7.4.2 (nosso build.gradle) **não suporta JDK 21+**. Precisa ser JDK 17 Temurin ou OpenJDK.

Verificar versão:
```bash
java -version
# Esperado: openjdk version "17.0.X" ou "17.X.X"
```

Se o sistema tiver JDK mais novo como padrão, instala o 17 em paralelo e usa só nele:

```bash
# Fedora
sudo dnf install java-17-openjdk-devel

# Rodar build com JDK 17 específico:
JAVA_HOME=/usr/lib/jvm/java-17-openjdk ./gradlew assembleRelease
```

### Python 3.9+

Nosso `build.py` usa `datetime.UTC` (Python 3.11+ puro). Python 3.9/3.10 funciona com minor ajuste. Testado em 3.13 e 3.14.

### Keystore do Android (debug keystore padrão)

O Android gera automaticamente um `~/.android/debug.keystore` quando você roda `gradle` ou outras ferramentas Android pela primeira vez. Verifica se já existe:

```bash
ls ~/.android/debug.keystore
```

Se não existe, gera forçando um build qualquer OU manualmente:
```bash
mkdir -p ~/.android
keytool -genkey -v -keystore ~/.android/debug.keystore \
  -alias androiddebugkey -keyalg RSA -keysize 2048 \
  -validity 10000 \
  -dname "CN=Android Debug,O=Android,C=US" \
  -storepass android -keypass android
```

**IMPORTANTE:** se você modificar o APK depois (versão v0.3 → v0.4), **precisa assinar com a MESMA keystore** — Android recusa upgrade de APK com signature diferente. Faz backup logo:

```bash
mkdir -p ~/backup-honda-civic-g10
cp ~/.android/debug.keystore ~/backup-honda-civic-g10/debug.keystore.bak
```

---

## Projetos de referência (clonar na pasta `tooling/references/`)

Os projetos que o nosso usa como base. Nenhum deles redistribuído — você clona na hora:

```bash
cd /caminho/do/honda-civic-headunit
mkdir -p tooling/references

# ic1101 — ota-builder (nosso build.py envelopa isso)
git clone https://github.com/librick/ic1101.git tooling/references/ic1101

# root-honda — su setuid + whitelist Mitsubishi
git clone https://github.com/codeage/root-honda.git tooling/references/root-honda
```

Alternativamente, `MIGRATION/setup.sh` do nosso repo faz isso automaticamente:
```bash
./MIGRATION/setup.sh
```

---

## Binários (busybox + su + sleep)

Estão em projetos de terceiros clonados acima. Script helper copia pros lugares certos:

```bash
mkdir -p tooling/ota-build/bin

# busybox ARM estático (do HondaHack APK que vem no root-honda)
unzip -o tooling/references/root-honda/packages/HondaHack.apk -d /tmp/hondahack
cp /tmp/hondahack/res/raw/busybox tooling/ota-build/bin/busybox

# su setuid (do root-honda direto)
cp tooling/references/root-honda/su tooling/ota-build/bin/su

# sleep (do ic1101 — compilado)
# Já vem como parte do ic1101/ota-builder/input/sleep/output/sleep
```

---

## Verificar que tudo está pronto

Script helper verifica se tudo foi instalado:

```bash
./tooling/scripts/verificar-backups.sh
```

Além disso, teste manual rápido:

```bash
# JDK 17
java -version 2>&1 | grep "17\."

# Python
python3 --version

# apksigner
$ANDROID_SDK_ROOT/build-tools/33.0.2/apksigner --version

# gradlew do projeto
cd our-apk && ./gradlew --version

# Binários
ls -la tooling/ota-build/bin/{busybox,su}

# References
ls tooling/references/ic1101 tooling/references/root-honda
```

Tudo verde = pronto pra build.

---

## O que você NÃO precisa

- ❌ Bootloader destravado
- ❌ ADB funcional na central (nosso ataque dispensa totalmente)
- ❌ Assinatura ou aprovação da Honda
- ❌ Honda Hack pago (US$ 25) — este projeto substitui
- ❌ JTAG / cabo serial / hardware especial
- ❌ Carro de outra pessoa pra testar — você aprende no seu próprio

---

## Checklist final antes de fazer o build

- [ ] JDK 17 instalado e `java -version` mostra `17.X`
- [ ] Android SDK + build-tools 33.0.2 instalado
- [ ] Python 3.11+ (ou 3.9+ com ajuste no build.py)
- [ ] `~/.android/debug.keystore` existe e tem backup externo
- [ ] Projeto clonado em `honda-civic-headunit/`
- [ ] `tooling/references/ic1101/` e `tooling/references/root-honda/` existem
- [ ] `tooling/ota-build/bin/busybox` e `tooling/ota-build/bin/su` existem
- [ ] Pendrive USB-A disponível

Tudo check? → [`04-build-do-pacote.md`](04-build-do-pacote.md).
