#!/usr/bin/env bash
# ============================================================
# prepare-pendrive-rollback.sh
# ============================================================
# PACOTE DE EMERGÊNCIA — ROLLBACK.
# Carrega pacote que REMOVE AutoOk.apk + su do /system do HU.
# Use se o APK causou problema após deploy, ou para reverter
# ao estado original.
#
# Uso:
#   sudo ./tooling/scripts/prepare-pendrive-rollback.sh <device>
#
# Exemplo:
#   sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sda
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
OUTPUT_DIR="$PROJECT_ROOT/tooling/ota-build/output-rollback"

BUILD_TS=$(ls -1 "$OUTPUT_DIR" 2>/dev/null | sort | tail -1)
if [ -z "$BUILD_TS" ]; then
  echo "ERRO: nenhum build de rollback encontrado em $OUTPUT_DIR"
  echo "Rode primeiro: python3 tooling/ota-build/build-rollback.py"
  exit 1
fi

SRC="$OUTPUT_DIR/$BUILD_TS"
echo "=== Usando rollback build: $SRC ==="

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

echo "=== Limpando pendrive ==="
find "$MP" -mindepth 1 -maxdepth 1 ! -name 'lost+found' -exec rm -rf {} +

echo "=== Copiando pacote ROLLBACK ==="
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
echo "Pendrive em $DEV carregado com pacote ROLLBACK."
echo "Protocolo: puxar pendrive, levar ao carro, AUDIO 5s, confirmar reiniciar."
echo "APK e su serão removidos de /system no próximo boot."
