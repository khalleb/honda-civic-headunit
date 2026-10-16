#!/usr/bin/env bash
# ============================================================
# verificar-backups.sh
# ============================================================
# Lista o estado dos backups do projeto. Aponta o que está
# presente, SHA-1 dos arquivos críticos, e alerta se faltar.
#
# Uso:
#   ./tooling/scripts/verificar-backups.sh
# ============================================================
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

ok() { echo "  ✓ $*"; }
warn() { echo "  ⚠ $*"; }
fail() { echo "  ✗ $*"; }
sep() { echo ""; echo "=== $* ==="; }

MISSING=0

sep "1. APK compilado"
APK="our-apk/app/build/outputs/apk/release/AutoOk.apk"
if [ -f "$APK" ]; then
  ok "$APK ($(stat -c%s "$APK") bytes, SHA-1 $(sha1sum "$APK" | cut -d' ' -f1))"
else
  fail "APK não compilado — rode: cd our-apk && ./gradlew assembleRelease && apksigner sign ..."
  MISSING=$((MISSING+1))
fi

sep "2. Overlay do pacote OTA"
OVERLAY="tooling/ota-build/overlay/system/app/AutoOk.apk"
if [ -f "$OVERLAY" ]; then
  ok "$OVERLAY (SHA-1 $(sha1sum "$OVERLAY" | cut -d' ' -f1))"
  if [ -f "$APK" ] && [ "$(sha1sum "$APK" | cut -d' ' -f1)" != "$(sha1sum "$OVERLAY" | cut -d' ' -f1)" ]; then
    warn "SHA-1 do overlay difere do APK compilado — overlay pode estar desatualizado"
  fi
else
  fail "Overlay vazio — cp our-apk/app/build/outputs/apk/release/AutoOk.apk $OVERLAY"
  MISSING=$((MISSING+1))
fi

sep "3. Binários de terceiros (busybox + su)"
for bin in busybox su; do
  P="tooling/ota-build/bin/$bin"
  if [ -f "$P" ]; then
    ok "$P ($(stat -c%s "$P") bytes)"
  else
    fail "$P ausente — ver instruções em QUICKSTART.md § 2"
    MISSING=$((MISSING+1))
  fi
done

sep "4. Pacote OTA INSTALL"
INSTALL_LATEST=$(ls -1 tooling/ota-build/output 2>/dev/null | sort | tail -1)
if [ -n "$INSTALL_LATEST" ]; then
  MDT="tooling/ota-build/output/$INSTALL_LATEST/0040/SwUpdate.mdt"
  if [ -f "$MDT" ]; then
    ok "$MDT ($(stat -c%s "$MDT") bytes, SHA-1 $(sha1sum "$MDT" | cut -d' ' -f1))"
    ok "Timestamp: $INSTALL_LATEST"
  else
    fail "Diretório $INSTALL_LATEST existe mas SwUpdate.mdt dentro não"
    MISSING=$((MISSING+1))
  fi
else
  fail "Nenhum pacote INSTALL — rode: python3 tooling/ota-build/build.py"
  MISSING=$((MISSING+1))
fi

sep "5. Pacote OTA ROLLBACK"
ROLLBACK_LATEST=$(ls -1 tooling/ota-build/output-rollback 2>/dev/null | sort | tail -1)
if [ -n "$ROLLBACK_LATEST" ]; then
  MDT="tooling/ota-build/output-rollback/$ROLLBACK_LATEST/0040/SwUpdate.mdt"
  if [ -f "$MDT" ]; then
    ok "$MDT ($(stat -c%s "$MDT") bytes, SHA-1 $(sha1sum "$MDT" | cut -d' ' -f1))"
    ok "Timestamp: $ROLLBACK_LATEST"
  else
    fail "Diretório $ROLLBACK_LATEST existe mas SwUpdate.mdt dentro não"
    MISSING=$((MISSING+1))
  fi
else
  fail "Nenhum pacote ROLLBACK — rode: python3 tooling/ota-build/build-rollback.py"
  MISSING=$((MISSING+1))
fi

sep "6. Dump do /system pré-deploy (opcional, bom pra inspeção)"
DUMP="tooling/apks-dumped/dump-0040"
if [ -d "$DUMP" ]; then
  ok "$DUMP ($(du -sh "$DUMP" | cut -f1))"
  for sub in system-build.prop vendor-build.prop system-app vendor-app; do
    if [ -e "$DUMP/$sub" ]; then
      ok "  $sub presente"
    else
      warn "  $sub ausente (não bloqueador, mas dump parcial)"
    fi
  done
else
  warn "Sem dump do /system — para inspeção/comparação, dumpe via pacote de dump (ver docs)"
fi

sep "7. Pendrive conectado?"
if [ -b /dev/sda ]; then
  TRAN=$(lsblk -no TRAN /dev/sda | head -1 | xargs)
  MODEL=$(lsblk -no MODEL /dev/sda | head -1 | xargs)
  SIZE=$(lsblk -no SIZE /dev/sda | head -1 | xargs)
  if [ "$TRAN" = "usb" ]; then
    ok "/dev/sda: $MODEL $SIZE (USB)"
    mp=$(lsblk -no MOUNTPOINT /dev/sda1 2>/dev/null | head -1)
    if [ -n "$mp" ]; then
      ok "  montado em $mp"
      if [ -f "$mp/SwUpdate2.txt" ] && [ -d "$mp/0040" ]; then
        PENDRIVE_MDT="$mp/0040/SwUpdate.mdt"
        if [ -f "$PENDRIVE_MDT" ]; then
          ok "  pendrive carregado — SwUpdate.mdt SHA-1: $(sha1sum "$PENDRIVE_MDT" | cut -d' ' -f1)"
        fi
      else
        warn "  pendrive sem pacote OTA (vazio ou outro conteúdo)"
      fi
    else
      warn "  não montado"
    fi
  else
    warn "/dev/sda não é USB (tran=$TRAN) — pode não ser o pendrive"
  fi
else
  warn "/dev/sda não existe — pendrive não conectado"
fi

sep "Resumo"
if [ $MISSING -eq 0 ]; then
  echo "✅ Todos os artefatos críticos presentes."
  echo ""
  echo "Pronto para:"
  echo "  - sudo ./tooling/scripts/prepare-pendrive-install.sh /dev/sdX"
  echo "  - sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sdX"
else
  echo "⚠ $MISSING artefato(s) ausente(s). Veja mensagens acima."
  exit 1
fi
