#!/usr/bin/env bash
# ============================================================
# prepare-pendrive-deep-scan.sh
# ============================================================
# Carrega o pacote OTA de DEEP SCAN que coleta estrutura inteira
# da central (todas as particoes, build.prop, init.rc,
# packages.xml, /proc/*, etc) e empacota em scan.tar.gz.
#
# Zero modificacao no /system. Deploy ~5-15 min no carro.
# Pendrive precisa de >= 500MB livres.
#
# Uso:
#   sudo ./tooling/scripts/prepare-pendrive-deep-scan.sh <device>
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
OUTPUT_DIR="$PROJECT_ROOT/tooling/ota-build/output-deep-scan"

BUILD_TS=$(ls -1 "$OUTPUT_DIR" 2>/dev/null | sort | tail -1)
if [ -z "$BUILD_TS" ]; then
  echo "ERRO: nenhum build deep-scan encontrado em $OUTPUT_DIR"
  echo "Rode primeiro: python3 tooling/ota-build/build-deep-scan.py"
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

AVAIL=$(df -BM --output=avail "$MP" | tail -1 | tr -d 'M ')
if [ "$AVAIL" -lt 512 ]; then
  echo "AVISO: pendrive tem so ${AVAIL}MB livres. Scan precisa de ~500MB."
  read -p "Prosseguir mesmo assim? (yes/no): " CONFIRM
  if [ "$CONFIRM" != "yes" ]; then
    [ "$OWN_MOUNT" = "1" ] && { umount "$MP"; rmdir "$MP"; }
    exit 0
  fi
fi

echo "=== Limpando pendrive ==="
find "$MP" -mindepth 1 -maxdepth 1 ! -name 'lost+found' -exec rm -rf {} +

echo "=== Copiando pacote DEEP SCAN ==="
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
echo "Pendrive em $DEV carregado com pacote DEEP SCAN."
echo "Protocolo: porta frontal + AUDIO 5s + confirmar reiniciar."
echo "ESPERAR ~5-15 min pelo fim."
echo ""
echo "Resultado vai pro pendrive em deep-scan-0040/:"
echo "  scan.tar.gz   - estrutura completa compactada"
echo "  scan.log      - log do processo"
