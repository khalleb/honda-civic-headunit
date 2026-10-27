#!/usr/bin/env bash
# ============================================================
# prepare-pendrive-install.sh
# ============================================================
# Carrega um pacote OTA de instalação para um pendrive FAT32
# pronto para ser plugado na porta USB-A frontal da central
# Honda Civic G10.
#
# Sem diretório, usa o build mais novo de tooling/ota-build/output
# (AutoOk.apk + su setuid). Com diretório, usa o build mais novo
# dele, ou o build exato se o caminho já for um <timestamp>.
#
# Pré-requisitos:
#   - Pendrive FAT32 com tabela MSDOS (ver format-pendrive.sh)
#   - Build do pacote OTA já feito
#   - Rodar como root (sudo)
#
# Uso:
#   sudo ./tooling/scripts/prepare-pendrive-install.sh <device> [diretorio-de-build]
#
# Exemplos:
#   sudo ./tooling/scripts/prepare-pendrive-install.sh /dev/sda
#   sudo ./tooling/scripts/prepare-pendrive-install.sh /dev/sda tooling/ota-build/output-dalauncher-fase10
#
# Guardas, limpeza, cópia e conferência ficam em lib-pendrive.sh.
# ============================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib-pendrive.sh"

prepare_pendrive INSTALL "$OTA_BUILD_DIR/output" "python3 tooling/ota-build/build.py" 0 "$@"
echo "Agora: puxar o pendrive e seguir o protocolo do pacote"
echo "  AutoOk:  docs/pt-BR/05-deploy-no-carro.md"
echo "  Fase 10: docs/fase10-execucao-2026-10-27.md"
