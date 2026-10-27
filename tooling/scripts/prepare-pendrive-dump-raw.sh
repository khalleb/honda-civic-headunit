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
# Pendrive precisa de pelo menos 2GB. Se o dump não couber, o gzip
# falha em silêncio no carro; o script confere a capacidade antes.
#
# Uso:
#   sudo ./tooling/scripts/prepare-pendrive-dump-raw.sh <device> [diretorio-de-build]
#
# Guardas, limpeza, cópia e conferência ficam em lib-pendrive.sh.
# ============================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib-pendrive.sh"

prepare_pendrive DUMP-RAW "$OTA_BUILD_DIR/output-dump-raw" "python3 tooling/ota-build/build-dump-raw.py" 2048 "$@"
echo "Protocolo: porta frontal + AUDIO 5s + confirmar reiniciar."
echo "ESPERAR ~10-15 min pelo fim (dd + gzip de ~2GB)."
echo "Depois: pluga pendrive no notebook, copia dump-raw-0040/ pro notebook,"
echo "guarda em local seguro (NÃO vai pro git — está no .gitignore)."
