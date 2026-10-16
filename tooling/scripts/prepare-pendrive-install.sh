#!/usr/bin/env bash
# ============================================================
# prepare-pendrive-install.sh
# ============================================================
# Carrega o pacote OTA de instalação (AutoOk.apk + su setuid)
# para um pendrive FAT32 pronto para ser plugado na porta
# USB-A frontal da central Honda Civic G10.
#
# Pré-requisitos:
#   - Pendrive já formatado como FAT32 com tabela MSDOS
#     (ver prepare-pendrive-format.sh)
#   - Build do pacote OTA já feito via `python3 tooling/ota-build/build.py`
#   - Rodar como root (sudo)
#
# Uso:
#   sudo ./tooling/scripts/prepare-pendrive-install.sh <device>
#
# Exemplo:
#   sudo ./tooling/scripts/prepare-pendrive-install.sh /dev/sda
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

# Diretório raiz do projeto (dois níveis acima de scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT_DIR="$PROJECT_ROOT/tooling/ota-build/output"

# Pega o build mais recente
BUILD_TS=$(ls -1 "$OUTPUT_DIR" 2>/dev/null | sort | tail -1)
if [ -z "$BUILD_TS" ]; then
  echo "ERRO: nenhum build encontrado em $OUTPUT_DIR"
  echo "Rode primeiro: python3 tooling/ota-build/build.py"
  exit 1
fi

SRC="$OUTPUT_DIR/$BUILD_TS"
echo "=== Usando build: $SRC ==="

# Guard de identidade do pendrive — evita formatar o SSD por acidente
TRAN=$(lsblk -no TRAN "$DEV" | head -1 | xargs)
if [ "$TRAN" != "usb" ]; then
  echo "ERRO: $DEV não é USB (tran=$TRAN). Abortando por segurança."
  exit 1
fi

# Monta o pendrive (ou usa mount existente)
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

# Limpa conteúdo anterior
echo "=== Limpando pendrive ==="
find "$MP" -mindepth 1 -maxdepth 1 ! -name 'lost+found' -exec rm -rf {} +

# Copia o pacote de instalação
echo "=== Copiando pacote INSTALL ==="
cp -v "$SRC/SwUpdate2.txt" "$MP/"
cp -rv "$SRC/0040" "$MP/"
sync

echo ""
echo "=== Conteúdo final ==="
ls -la "$MP"
MDT_COUNT=$(find "$MP" -name 'SwUpdate.mdt' | wc -l)
echo "Pacotes .mdt: $MDT_COUNT"

if [ "$OWN_MOUNT" = "1" ]; then
  umount "$MP"
  rmdir "$MP"
fi

echo ""
echo "=== PRONTO ==="
echo "Pendrive em $DEV carregado com pacote INSTALL."
echo "Agora: puxar pendrive, levar ao carro, protocolo em docs/pt-BR/05-deploy-no-carro.md"
