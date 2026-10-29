#!/usr/bin/env bash
# ============================================================
# prepare-pendrive-disable-adb.sh
# ============================================================
# Reversão do ENABLE-ADB — grava persist.sys.usb1_mode=host em
# /data/property/ do carro, pra o USB voltar ao modo Host (padrão de
# fábrica, enumera pendrive/celular). Mecanismo documentado em
# tooling/ota-build/build-enable-adb.py e MAPA §17.20.
#
# Zero modificação em /system. Deploy ~1 min no carro.
#
# Uso:
#   sudo ./tooling/scripts/prepare-pendrive-disable-adb.sh <device> [diretorio-de-build]
#
# Depois do deploy: ADB para de enumerar. Pra reabilitar, rodar o
# prepare-pendrive-enable-adb.sh de novo.
#
# Guardas, limpeza, cópia e conferência ficam em lib-pendrive.sh.
# ============================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib-pendrive.sh"

prepare_pendrive DISABLE-ADB "$OTA_BUILD_DIR/output-enable-adb" "python3 tooling/ota-build/build-enable-adb.py --mode host" 10 "$@"
echo "Protocolo: porta frontal + AUDIO 5s + confirmar reiniciar."
echo "ESPERAR ~1 min pelo fim."
echo ""
echo "Depois: USB volta ao modo Host (padrão de fábrica)."
echo "Pra reabilitar ADB: rodar prepare-pendrive-enable-adb.sh de novo."
