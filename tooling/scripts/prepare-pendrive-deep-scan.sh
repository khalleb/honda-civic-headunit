#!/usr/bin/env bash
# ============================================================
# prepare-pendrive-deep-scan.sh
# ============================================================
# Carrega o pacote OTA de DEEP SCAN que coleta estrutura inteira
# da central (todas as particoes, build.prop, init.rc,
# packages.xml, /proc/*, etc) e empacota em scan.tar.gz.
#
# Zero modificacao no /system. Deploy ~5-15 min no carro.
# Pendrive precisa de >= 512MB (o script confere a capacidade).
#
# Uso:
#   sudo ./tooling/scripts/prepare-pendrive-deep-scan.sh <device> [diretorio-de-build]
#
# Guardas, limpeza, cópia e conferência ficam em lib-pendrive.sh.
# ============================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib-pendrive.sh"

prepare_pendrive "DEEP SCAN" "$OTA_BUILD_DIR/output-deep-scan" "python3 tooling/ota-build/build-deep-scan.py" 512 "$@"
echo "Protocolo: porta frontal + AUDIO 5s + confirmar reiniciar."
echo "ESPERAR ~5-15 min pelo fim."
echo ""
echo "Resultado vai pro pendrive em deep-scan-0040/:"
echo "  scan.tar.gz   - estrutura completa compactada"
echo "  scan.log      - log do processo"
