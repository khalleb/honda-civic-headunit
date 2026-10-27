#!/usr/bin/env bash
# ============================================================
# lib-pendrive.sh
# ============================================================
# Sequência comum dos prepare-pendrive-*.sh: confere o pendrive,
# escolhe o build, pede "yes" antes de limpar, copia o pacote OTA,
# confere a cópia lendo do próprio pendrive e desmonta.
#
# Não roda sozinho. Cada prepare-pendrive-*.sh faz `source` deste
# arquivo e chama:
#
#   prepare_pendrive <rótulo> <dir-padrão> <comando-de-build> <capacidade-mín-MB> <device> [dir-de-build]
#
# As etapas ficam em funções separadas para serem testadas sem
# pendrive nem root: tooling/ota-build/tests/test_prepare_pendrive.py
# ============================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OTA_BUILD_DIR="$PROJECT_ROOT/tooling/ota-build"

# custom_rom.type da nossa safra. O daupdater só procura
# /mnt/usbdrive1/<rom_type>/SwUpdate.mdt, então só esse diretório vai pro pendrive.
ROM_TYPE="0040"

PART=""
MP=""
TEMP_MP=""
MOUNTED_HERE=0

die() {
  echo "ERRO: $*" >&2
  exit 1
}

# Recebe um build exato (pasta com $ROM_TYPE/SwUpdate.mdt) ou um diretório de
# builds; nesse caso usa o mais novo. Os builds são pastas YYYYMMDDTHHMMSSZ,
# então a ordem alfabética é a cronológica. Imprime o caminho escolhido.
#
# Se o mais novo estiver incompleto (build que falhou no meio), recusa em vez de
# cair no anterior: pacote velho no pendrive sem ninguém perceber é pior que erro.
resolve_build_dir() {
  local output_dir="$1" build_hint="$2" src newest
  if [ -f "$output_dir/$ROM_TYPE/SwUpdate.mdt" ]; then
    src="$output_dir"
  else
    newest=$(ls -1 "$output_dir" 2>/dev/null | sort | tail -1) || true
    [ -n "$newest" ] || die "nenhum build encontrado em $output_dir (rode primeiro: $build_hint)"
    src="$output_dir/$newest"
  fi
  if [ ! -f "$src/SwUpdate2.txt" ] || [ ! -f "$src/$ROM_TYPE/SwUpdate.mdt" ]; then
    die "$src não tem SwUpdate2.txt e $ROM_TYPE/SwUpdate.mdt"
  fi
  echo "$src"
}

# Só aceita o disco inteiro de um pendrive USB: é a guarda contra apagar o SSD.
# O lsblk mostra TRAN=usb também na partição, então sem a checagem de TYPE um
# /dev/sdb1 passaria e a montagem falharia adiante em /dev/sdb11.
check_device() {
  local dev="$1" type tran
  [ -n "$dev" ] || die "passar device do pendrive. Ex: sudo $0 /dev/sda [diretorio-de-build]"
  [ -b "$dev" ] || die "$dev não é um block device"
  type=$(lsblk -dno TYPE "$dev" | xargs)
  [ "$type" = "disk" ] || die "$dev é '$type'; passar o disco inteiro (ex: /dev/sda, não /dev/sda1)"
  tran=$(lsblk -dno TRAN "$dev" | xargs)
  [ "$tran" = "usb" ] || die "$dev não é USB (tran=$tran). Abortando por segurança."
}

# O checklist do daupdater no ic1101 (docs/updates.md) pede tabela MSDOS e uma
# partição vfat. Sem tabela ("superfloppy") o pendrive aparece como sda em vez de
# sda1 e o daupdater não acha o pacote. Melhor recusar aqui do que descobrir no carro.
check_pendrive_format() {
  local dev="$1" pttype fstype
  pttype=$(lsblk -dno PTTYPE "$dev" | xargs)
  [ "$pttype" = "dos" ] || die "$dev tem tabela '${pttype:-nenhuma}', mas o daupdater exige MSDOS. Formatar com: sudo tooling/scripts/format-pendrive.sh $dev"
  PART=$(lsblk -lnpo NAME,TYPE "$dev" | awk '$2 == "part" { print $1; exit }')
  [ -n "$PART" ] || die "$dev não tem partição. Formatar com: sudo tooling/scripts/format-pendrive.sh $dev"
  fstype=$(lsblk -dno FSTYPE "$PART" | xargs)
  [ "$fstype" = "vfat" ] || die "$PART é '${fstype:-sem filesystem}', mas o daupdater exige vfat. Formatar com: sudo tooling/scripts/format-pendrive.sh $dev"
}

require_root() {
  [ "$(id -u)" = "0" ] || die "rodar com sudo"
}

# Reaproveita a montagem do desktop, se houver. Senão monta numa pasta temporária,
# que o cleanup desmonta e apaga, inclusive quando o script morre no meio.
mount_pendrive() {
  local part="$1" existing
  existing=$(lsblk -no MOUNTPOINT "$part" | head -1)
  if [ -n "$existing" ]; then
    MP="$existing"
  else
    TEMP_MP=$(mktemp -d)
    MP="$TEMP_MP"
    mount "$part" "$MP"
    MOUNTED_HERE=1
  fi
  echo "Pendrive em: $MP"
}

cleanup() {
  if [ "$MOUNTED_HERE" = "1" ]; then
    umount "$MP"
    MOUNTED_HERE=0
  fi
  if [ -n "$TEMP_MP" ]; then
    rmdir "$TEMP_MP"
    TEMP_MP=""
  fi
}

# deep-scan, diagnostic e dump-raw gravam o resultado no próprio pendrive. Como o
# pendrive é limpo antes da cópia, o que importa é a capacidade total, não o
# espaço livre que ele tem agora.
check_capacity() {
  local min_mb="$1" size_mb confirm
  [ "$min_mb" -gt 0 ] || return 0
  size_mb=$(df -BM --output=size "$MP" | tail -1 | tr -d 'M ')
  [ "$size_mb" -ge "$min_mb" ] && return 0
  echo "AVISO: pendrive de ${size_mb}MB; este pacote grava até ~${min_mb}MB de resultado."
  read -r -p "Prosseguir mesmo assim? (yes/no): " confirm
  [ "$confirm" = "yes" ] || { echo "Abortado."; exit 0; }
}

# As guardas acima conferem que é um pendrive no formato certo, mas não qual: com
# os dois pendrives da Fase 10 plugados, o device trocado apaga o outro. Mostra o
# que vai ser apagado e só segue com "yes", como o format-pendrive.sh.
confirm_wipe() {
  local dev="$1" pkg="$2" content confirm
  content=$(ls -A "$MP" | tr '\n' ' ')
  echo "=== Vai APAGAR o conteúdo deste pendrive ==="
  echo "  Device:   $dev ($(lsblk -dno MODEL,SIZE "$dev" | xargs))"
  echo "  Rótulo:   $(lsblk -dno LABEL "$PART" | xargs)"
  echo "  Montado:  $MP"
  echo "  Conteúdo: ${content:-(vazio)}"
  read -r -p "Apagar e gravar o pacote $pkg? (yes/no): " confirm || confirm=""
  [ "$confirm" = "yes" ] || { echo "Abortado. Nada foi apagado."; exit 0; }
}

# Limpa a raiz do pendrive (menos lost+found) para não sobrar log, gate .OK/.FAIL
# ou SwUpdate2.txt.done de uma rodada anterior misturado com o resultado da próxima.
wipe_pendrive() {
  find "$1" -mindepth 1 -maxdepth 1 ! -name 'lost+found' -exec rm -rf {} +
}

copy_package() {
  local src="$1" dest="$2"
  cp -v "$src/SwUpdate2.txt" "$dest/"
  cp -rv "$src/$ROM_TYPE" "$dest/"
  sync
}

# Depois do sync, o page cache ainda guarda o que acabou de ser escrito, e o
# sha256sum leria dali. Descartar o cache força a leitura do próprio pendrive.
drop_page_cache() {
  sync
  echo 3 > /proc/sys/vm/drop_caches
}

# Uma linha OK/ERRO por arquivo do pacote. Retorna 1 se algum diferir ou faltar.
verify_copy() {
  local src="$1" dest="$2" f expected on_drive status=0
  for f in SwUpdate2.txt "$ROM_TYPE/SwUpdate.mdt"; do
    expected=$(sha256sum "$src/$f" | cut -d' ' -f1)
    on_drive=$(sha256sum "$dest/$f" 2>/dev/null | cut -d' ' -f1) || true
    if [ -n "$on_drive" ] && [ "$expected" = "$on_drive" ]; then
      echo "OK   $f  $on_drive"
    else
      echo "ERRO $f  build=$expected pendrive=${on_drive:-ausente}"
      status=1
    fi
  done
  return "$status"
}

# Desmonta também quando a montagem era do desktop: o checklist manda puxar o
# pendrive logo depois do PRONTO, e o vfat só marca o volume como limpo no umount.
unmount_pendrive() {
  umount "$MP" || die "a cópia está conferida, mas $MP não desmontou (pasta aberta em algum programa?). Ejetar pelo desktop antes de puxar o pendrive."
  MOUNTED_HERE=0
}

prepare_pendrive() {
  local label="$1" default_dir="$2" build_hint="$3" min_mb="$4"
  shift 4
  local dev="${1:-}" output_dir="${2:-$default_dir}" src

  check_device "$dev"
  src=$(resolve_build_dir "$output_dir" "$build_hint")
  echo "=== Usando build: $src ==="

  require_root
  check_pendrive_format "$dev"
  trap cleanup EXIT
  mount_pendrive "$PART"

  # Trava antes do rm -rf: o alvo tem que ser um ponto de montagem de verdade,
  # nunca uma pasta comum do notebook.
  mountpoint -q "$MP" || die "$MP não é ponto de montagem; não vou limpar"
  check_capacity "$min_mb"
  confirm_wipe "$dev" "$label"

  echo "=== Limpando pendrive ==="
  wipe_pendrive "$MP"

  echo "=== Copiando pacote $label ==="
  copy_package "$src" "$MP"

  echo "=== Conferindo a cópia (SHA-256 lido do pendrive, sem cache) ==="
  drop_page_cache
  verify_copy "$src" "$MP" || die "o conteúdo do pendrive não bate com o build. Não levar este pendrive ao carro."

  echo ""
  echo "=== Conteúdo final ==="
  ls -la "$MP"

  unmount_pendrive
  cleanup
  echo ""
  echo "=== PRONTO ==="
  echo "Pendrive em $dev carregado com pacote $label de $src."
  echo "Já está desmontado: pode puxar."
}
