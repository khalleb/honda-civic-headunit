#!/usr/bin/env bash
# =============================================================================
# Setup — Projeto Honda Civic G10 Head Unit (Linux)
# =============================================================================
# Fluxo esperado:
#   mkdir -p ~/repositorios
#   cd ~/repositorios
#   git clone <este-repo> honda-civic
#   cd honda-civic/MIGRATION
#   chmod +x setup.sh
#   ./setup.sh
#
# O que faz:
#   1. Instala dependências do sistema (Java, ADB, Git, curl, unzip)
#   2. Baixa apktool e jadx para ./tooling/bin/
#   3. Clona repositórios de referência em ./tooling/references/
#   4. Descompila o HondaHack.apk incluído no root-honda
# =============================================================================

set -e

# Detecta a raiz do projeto (um nível acima do MIGRATION/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TOOLING="$PROJECT_ROOT/tooling"
BIN="$TOOLING/bin"
REFS="$TOOLING/references"

echo "============================================================"
echo "Setup — Projeto Honda Civic G10"
echo "Projeto detectado em: $PROJECT_ROOT"
echo "============================================================"
read -p "Pressione ENTER para continuar, Ctrl+C para cancelar..."

# -----------------------------------------------------------------------------
# 1. Dependências do sistema
# -----------------------------------------------------------------------------
echo ""
echo "[1/4] Verificando dependências do sistema..."

NEED_INSTALL=""
command -v java  >/dev/null 2>&1 || NEED_INSTALL="$NEED_INSTALL default-jre"
command -v adb   >/dev/null 2>&1 || NEED_INSTALL="$NEED_INSTALL android-tools-adb"
command -v git   >/dev/null 2>&1 || NEED_INSTALL="$NEED_INSTALL git"
command -v curl  >/dev/null 2>&1 || NEED_INSTALL="$NEED_INSTALL curl"
command -v unzip >/dev/null 2>&1 || NEED_INSTALL="$NEED_INSTALL unzip"

if [ -n "$NEED_INSTALL" ]; then
  echo "   Falta instalar:$NEED_INSTALL"
  echo "   Rodando: sudo apt install -y$NEED_INSTALL"
  sudo apt update
  sudo apt install -y $NEED_INSTALL
else
  echo "   ✅ Todas as dependências já instaladas"
fi

echo ""
echo "   Java: $(java -version 2>&1 | head -1)"
echo "   ADB:  $(adb --version | head -1)"
echo "   Git:  $(git --version)"

# -----------------------------------------------------------------------------
# 2. Estrutura de diretórios de trabalho
# -----------------------------------------------------------------------------
echo ""
echo "[2/4] Garantindo estrutura de diretórios..."
mkdir -p "$BIN" "$REFS" "$TOOLING/apks-dumped" "$TOOLING/apks-decoded" "$PROJECT_ROOT/our-apk"
echo "   ✅ OK"

# -----------------------------------------------------------------------------
# 3. Baixar apktool e jadx em tooling/bin/
# -----------------------------------------------------------------------------
echo ""
echo "[3/4] Baixando apktool 2.11.1..."
if [ ! -f "$BIN/apktool.jar" ]; then
  curl -L -o "$BIN/apktool.jar" \
    "https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.11.1.jar"
  curl -L -o "$BIN/apktool" \
    "https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool"
  chmod +x "$BIN/apktool"
  echo "   ✅ apktool baixado"
else
  echo "   ✅ apktool já existe"
fi

echo ""
echo "       Baixando jadx 1.5.6..."
if [ ! -d "$BIN/jadx" ]; then
  curl -L -o "$BIN/jadx.zip" \
    "https://github.com/skylot/jadx/releases/download/v1.5.6/jadx-1.5.6.zip"
  unzip -q "$BIN/jadx.zip" -d "$BIN/jadx"
  rm "$BIN/jadx.zip"
  chmod +x "$BIN/jadx/bin/jadx" "$BIN/jadx/bin/jadx-gui"
  echo "   ✅ jadx baixado e extraído"
else
  echo "   ✅ jadx já existe"
fi

# -----------------------------------------------------------------------------
# 4. Clonar repositórios de referência em tooling/references/
# -----------------------------------------------------------------------------
echo ""
echo "[4/4] Clonando repositórios de referência..."
cd "$REFS"

if [ ! -d "root-honda" ]; then
  echo "   Clonando root-honda..."
  git clone --depth 1 https://github.com/codeage/root-honda.git || \
  git clone --depth 1 https://gitee.com/ylcplus/root-honda.git
else
  echo "   ✅ root-honda já existe"
fi

if [ ! -d "2016PilotOneClick" ]; then
  echo "   Clonando 2016PilotOneClick..."
  git clone --depth 1 https://github.com/jersacct/2016PilotOneClick.git || \
  git clone --depth 1 https://gitee.com/toddhan/2016PilotOneClick.git
else
  echo "   ✅ 2016PilotOneClick já existe"
fi

if [ ! -d "ic1101" ]; then
  echo "   Clonando ic1101..."
  git clone --depth 1 https://github.com/librick/ic1101.git
else
  echo "   ✅ ic1101 já existe"
fi

# Descompilar HondaHack.apk (análise rápida)
echo ""
echo "       Descompilando HondaHack.apk..."
HONDAHACK_APK="$REFS/root-honda/packages/HondaHack.apk"
HONDAHACK_OUT="$TOOLING/apks-decoded/HondaHack"
if [ -f "$HONDAHACK_APK" ] && [ ! -d "$HONDAHACK_OUT" ]; then
  java -jar "$BIN/apktool.jar" d "$HONDAHACK_APK" -o "$HONDAHACK_OUT" --force
  echo "   ✅ HondaHack descompilado em tooling/apks-decoded/HondaHack/"
elif [ -d "$HONDAHACK_OUT" ]; then
  echo "   ✅ HondaHack já descompilado"
else
  echo "   ⚠️  HondaHack.apk não encontrado"
fi

# -----------------------------------------------------------------------------
# FIM
# -----------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "✅ SETUP COMPLETO"
echo "============================================================"
echo ""
echo "Estrutura final em: $PROJECT_ROOT"
echo "  ├── central-multimidia-civic-g10-kb.md  (base de conhecimento)"
echo "  ├── CLAUDE.md                           (contexto auto p/ Claude Code)"
echo "  ├── tooling/"
echo "  │   ├── bin/                            (apktool.jar, jadx/)"
echo "  │   ├── references/                     (root-honda, 2016PilotOneClick, ic1101)"
echo "  │   ├── apks-dumped/                    (vazio; destino do pull via ADB)"
echo "  │   └── apks-decoded/HondaHack/         (descompilado)"
echo "  └── our-apk/                            (vazio; nosso APK a construir)"
echo ""
echo "Verificação rápida:"
echo "  java -jar $BIN/apktool.jar --version"
echo "  $BIN/jadx/bin/jadx --version"
echo "  adb --version"
echo ""
echo "Próximo passo:"
echo "  cd $PROJECT_ROOT"
echo "  claude   # (se tiver Claude Code — CLAUDE.md é auto-carregado)"
echo ""
