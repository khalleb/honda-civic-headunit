#!/usr/bin/env bash
# ============================================================
# prepare-pendrive-diagnostic.sh
# ============================================================
# Carrega o pacote OTA de DIAGNOSTICO que coleta:
#   - autook.log (log do AutoOk, pra bug do mudo em ligacao CarPlay)
#   - /data/data/com.mitsubishielectric.ada.app.dalauncher/ inteiro
#     (shared_prefs/, databases/, files/) - pra achar o gate do
#     disclaimer e tentar remover o aviso de vez
#   - /data/property/ - persist.* salvos
#
# Zero modificacao no /system. Deploy ~3 min no carro.
# Pendrive precisa de >= 50MB (coleta e pequena; o script confere).
#
# Uso:
#   sudo ./tooling/scripts/prepare-pendrive-diagnostic.sh <device> [diretorio-de-build]
#
# Guardas, limpeza, cópia e conferência ficam em lib-pendrive.sh.
# ============================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib-pendrive.sh"

prepare_pendrive DIAGNOSTICO "$OTA_BUILD_DIR/output-diagnostic" "python3 tooling/ota-build/build-diagnostic.py" 50 "$@"
echo "Protocolo: porta frontal + AUDIO 5s + confirmar reiniciar."
echo "ESPERAR ~3 min pelo fim."
echo ""
echo "Resultado vai pro pendrive em diag-0040/<timestamp>/:"
echo "  autook/      - logs do nosso APK"
echo "  dalauncher/  - prefs/dbs do launcher (acha gate do disclaimer)"
echo "  properties/  - persist.* salvos"
echo "  context/     - mounts, packages.xml, listas"
echo "  collect.log  - log do processo"
