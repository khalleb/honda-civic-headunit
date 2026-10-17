#!/usr/bin/env bash
# ============================================================
# prepare-pendrive-dump-raw.sh
# ============================================================
# Carrega o pacote OTA de DUMP RAW das partições (APP + CAP + MITSU)
# para um pendrive FAT32. Esse pacote NÃO instala nada no HU —
# só exporta imagens bootáveis das partições para o pendrive.
#
# Use UMA vez para ter backup "bootable" real das partições críticas.
# Deploy demora ~10-15 min no carro (dd + gzip de ~1-2GB).
#
# Pendrive precisa de pelo menos 2GB livres.
#
# Uso:
#   sudo ./tooling/scripts/prepare-pendrive-dump-raw.sh <device>
# ============================================================
set -euo pipefail

DEV="${1:-}"
if [ -z "$DEV" ]; then
  echo "ERRO: passar device do pendrive. Ex: sudo $0 /dev/sda"
  exit 1
fi

if [ ! -b "$DEV" ]; then
  echo "ERRO: $DEV não é um block device"
  exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT_DIR="$PROJECT_ROOT/tooling/ota-build/output-dump-raw"

BUILD_TS=$(ls -1 "$OUTPUT_DIR" 2>/dev/null | sort | tail -1)
if [ -z "$BUILD_TS" ]; then
  echo "ERRO: nenhum build dump-raw encontrado em $OUTPUT_DIR"
  echo "Rode primeiro: python3 tooling/ota-build/build-dump-raw.py"
  exit 1
fi

SRC="$OUTPUT_DIR/$BUILD_TS"
echo "=== Usando build: $SRC ==="

TRAN=$(lsblk -no TRAN "$DEV" | head -1 | xargs)
if [ "$TRAN" != "usb" ]; then
  echo "ERRO: $DEV não é USB (tran=$TRAN). Abortando por segurança."
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

AVAIL=$(df -BM --output=avail "$MP" | tail -1 | tr -d 'M ')
if [ "$AVAIL" -lt 2048 ]; then
  echo "AVISO: pendrive tem só ${AVAIL}MB livres. Pacote de dump pode precisar de 1-2GB."
  echo "Se o dump não couber, falha silenciosa no gzip."
  read -p "Prosseguir mesmo assim? (yes/no): " CONFIRM
  if [ "$CONFIRM" != "yes" ]; then
    [ "$OWN_MOUNT" = "1" ] && { umount "$MP"; rmdir "$MP"; }
    exit 0
  fi
fi

echo "=== Limpando pendrive ==="
find "$MP" -mindepth 1 -maxdepth 1 ! -name 'lost+found' -exec rm -rf {} +

echo "=== Copiando pacote DUMP-RAW ==="
cp -v "$SRC/SwUpdate2.txt" "$MP/"
cp -rv "$SRC/0040" "$MP/"
sync

echo ""
echo "=== Conteúdo final ==="
ls -la "$MP"

if [ "$OWN_MOUNT" = "1" ]; then
  umount "$MP"
  rmdir "$MP"
fi

echo ""
echo "=== PRONTO ==="
echo "Pendrive em $DEV com pacote DUMP-RAW."
echo "Protocolo: porta frontal + AUDIO 5s + confirmar reiniciar."
echo "ESPERAR ~10-15 min pelo fim (dd + gzip de ~2GB)."
echo "Depois: pluga pendrive no notebook, copia dump-raw-0040/ pro notebook,"
echo "guarda em local seguro (NÃO vai pro git — está no .gitignore)."
