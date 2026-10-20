#!/usr/bin/env bash
# ============================================================
# prepare-pendrive-diagnostic.sh
# ============================================================
# Carrega o pacote OTA de DIAGNOSTICO que coleta:
#   - autook.log (log do AutoOk, pra bug do mudo em ligacao CarPlay)
#   - /data/data/com.mitsubishielectric.ada.app.dalauncher/ inteiro
#     (shared_prefs/, databases/, files/) - pra achar o gate do
#     disclaimer e tentar remover o aviso de vez
#   - /data/property/ - persist.* salvos
#
# Zero modificacao no /system. Deploy ~3 min no carro.
# Pendrive precisa de >= 50MB livres (coleta e pequena).
#
# Uso:
#   sudo ./tooling/scripts/prepare-pendrive-diagnostic.sh <device>
# ============================================================
set -euo pipefail

DEV="${1:-}"
if [ -z "$DEV" ]; then
  echo "ERRO: passar device do pendrive. Ex: sudo $0 /dev/sda"
  exit 1
fi

if [ ! -b "$DEV" ]; then
  echo "ERRO: $DEV nao e um block device"
  exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT_DIR="$PROJECT_ROOT/tooling/ota-build/output-diagnostic"

BUILD_TS=$(ls -1 "$OUTPUT_DIR" 2>/dev/null | sort | tail -1)
if [ -z "$BUILD_TS" ]; then
  echo "ERRO: nenhum build diagnostico encontrado em $OUTPUT_DIR"
  echo "Rode primeiro: python3 tooling/ota-build/build-diagnostic.py"
  exit 1
fi

SRC="$OUTPUT_DIR/$BUILD_TS"
echo "=== Usando build: $SRC ==="

TRAN=$(lsblk -no TRAN "$DEV" | head -1 | xargs)
if [ "$TRAN" != "usb" ]; then
  echo "ERRO: $DEV nao e USB (tran=$TRAN). Abortando por seguranca."
  exit 1
fi

mp=$(lsblk -no MOUNTPOINT "${DEV}1" | head -1)
if [ -z "$mp" ]; then
  MP=$(mktemp -d)
  mount "${DEV}1" "$MP"
  OWN_MOUNT=1
else
  MP="$mp"
  OWN_MOUNT=0
fi
echo "Pendrive em: $MP"

echo "=== Limpando pendrive ==="
find "$MP" -mindepth 1 -maxdepth 1 ! -name 'lost+found' -exec rm -rf {} +

echo "=== Copiando pacote DIAGNOSTICO ==="
cp -v "$SRC/SwUpdate2.txt" "$MP/"
cp -rv "$SRC/0040" "$MP/"
sync

echo ""
echo "=== Conteudo final ==="
ls -la "$MP"

if [ "$OWN_MOUNT" = "1" ]; then
  umount "$MP"
  rmdir "$MP"
fi

echo ""
echo "=== PRONTO ==="
echo "Pendrive em $DEV carregado com pacote DIAGNOSTICO."
echo "Protocolo: porta frontal + AUDIO 5s + confirmar reiniciar."
echo "ESPERAR ~3 min pelo fim."
echo ""
echo "Resultado vai pro pendrive em diag-0040/<timestamp>/:"
echo "  autook/      - logs do nosso APK"
echo "  dalauncher/  - prefs/dbs do launcher (acha gate do disclaimer)"
echo "  properties/  - persist.* salvos"
echo "  context/     - mounts, packages.xml, listas"
echo "  collect.log  - log do processo"
