#!/usr/bin/env bash
# ============================================================
# prepare-pendrive-rollback.sh
# ============================================================
# PACOTE DE EMERGÊNCIA — ROLLBACK.
#
# Sem diretório, carrega o rollback do AutoOk, que REMOVE
# AutoOk.apk + su do /system do HU. Com
# tooling/ota-build/output-dalauncher-restore, carrega o restore
# do DaLauncher original (Fase 10).
#
# Uso:
#   sudo ./tooling/scripts/prepare-pendrive-rollback.sh <device> [diretorio-de-build]
#
# Exemplos:
#   sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sda
#   sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sda tooling/ota-build/output-dalauncher-restore
#
# Guardas, limpeza, cópia e conferência ficam em lib-pendrive.sh.
# ============================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib-pendrive.sh"

prepare_pendrive ROLLBACK "$OTA_BUILD_DIR/output-rollback" "python3 tooling/ota-build/build-rollback.py" 0 "$@"
echo "Protocolo: puxar pendrive, levar ao carro, AUDIO 5s, confirmar reiniciar."
