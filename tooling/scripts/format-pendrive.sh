#!/usr/bin/env bash
# ============================================================
# format-pendrive.sh
# ============================================================
# Formata um pendrive em FAT32 com tabela de partição MSDOS.
# Recovery AOSP exige tabela de partição — pendrive em "superfloppy"
# (vfat direto no device sem partition table) NÃO funciona.
#
# ATENÇÃO: formatar DESTRÓI tudo no pendrive.
# Confirme o device duas vezes antes de rodar.
#
# Uso:
#   sudo ./tooling/scripts/format-pendrive.sh <device>
#
# Exemplo:
#   sudo ./tooling/scripts/format-pendrive.sh /dev/sda
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

# Guard de identidade — evita formatar o SSD por acidente
TRAN=$(lsblk -no TRAN "$DEV" | head -1 | xargs)
MODEL=$(lsblk -no MODEL "$DEV" | head -1 | xargs)
SIZE=$(lsblk -no SIZE "$DEV" | head -1 | xargs)
# Só o disco inteiro. Sem isso, /dev/sda1 passaria no teste de USB e o parted
# escreveria uma tabela de partição dentro da partição (igual à guarda do
# lib-pendrive.sh).
TYPE=$(lsblk -dno TYPE "$DEV" | head -1 | xargs)
if [ "$TYPE" != "disk" ]; then
  echo "ERRO: $DEV é '$TYPE'; passar o disco inteiro (ex: /dev/sda, não /dev/sda1)."
  exit 1
fi
if [ "$TRAN" != "usb" ]; then
  echo "ERRO: $DEV não é USB (tran=$TRAN). Abortando por segurança."
  echo "Confira com: lsblk"
  exit 1
fi

echo "=== Vai FORMATAR o seguinte device ==="
echo "  Device:  $DEV"
echo "  Modelo:  $MODEL"
echo "  Tamanho: $SIZE"
echo "  Interface: $TRAN"
echo ""
echo "TODO o conteúdo será perdido!"
read -p "Confirma? (digite 'yes' para prosseguir): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Abortado."
  exit 0
fi

# Desmonta qualquer partição montada
for p in "${DEV}"[0-9]*; do
  if [ -b "$p" ]; then
    mp=$(lsblk -no MOUNTPOINT "$p" | head -1)
    if [ -n "$mp" ]; then
      echo "Desmontando $p (de $mp)"
      umount "$p"
    fi
  fi
done

echo "=== Criando tabela MSDOS + partição FAT32 ==="
parted -s "$DEV" mklabel msdos
parted -s "$DEV" mkpart primary fat32 1MiB 100%
parted -s "$DEV" set 1 lba on
partprobe "$DEV" || true
sleep 1

echo "=== Formatando ${DEV}1 como FAT32 ==="
mkfs.vfat -F 32 -n HONDA_OTA "${DEV}1"

echo ""
echo "=== PRONTO ==="
echo "Pendrive $DEV formatado FAT32 MSDOS."
echo "Próximo passo: ./tooling/scripts/prepare-pendrive-install.sh $DEV"
