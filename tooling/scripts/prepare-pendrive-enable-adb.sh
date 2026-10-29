#!/usr/bin/env bash
# ============================================================
# prepare-pendrive-enable-adb.sh
# ============================================================
# Carrega o pacote OTA de ENABLE-ADB — grava persist.sys.usb1_mode=device
# em /data/property/ do carro, pra no próximo boot o USB enumerar como
# dispositivo ADB (não como host). Documentação da cadeia USB mode em
# tooling/ota-build/build-enable-adb.py e MAPA §17.20.
#
# Zero modificação em /system. Deploy ~1 min no carro.
#
# Pré-requisito: AutoOk e su já instalados (Fase 7). Se o carro ainda está
# no estado zero, aplique primeiro o pacote INSTALL do AutoOk.
#
# Uso:
#   sudo ./tooling/scripts/prepare-pendrive-enable-adb.sh <device> [diretorio-de-build]
#
# Depois do deploy: cabo USB-A → USB-A entre central e PC, no PC rode
#   adb kill-server && adb start-server && adb devices
# A central deve aparecer como dispositivo não autorizado — autorize no
# diálogo que aparece na tela do carro.
#
# Guardas, limpeza, cópia e conferência ficam em lib-pendrive.sh.
# ============================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib-pendrive.sh"

prepare_pendrive ENABLE-ADB "$OTA_BUILD_DIR/output-enable-adb" "python3 tooling/ota-build/build-enable-adb.py" 10 "$@"
echo "Protocolo: porta frontal + AUDIO 5s + confirmar reiniciar."
echo "ESPERAR ~1 min pelo fim."
echo ""
echo "Depois no PC:"
echo "  adb kill-server && adb start-server"
echo "  adb devices    # central deve aparecer; autorizar na tela do carro"
echo ""
echo "Para reverter: regerar o builder trocando USB1_MODE='device' por 'host' e redeployar."
