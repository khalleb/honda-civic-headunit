#!/usr/bin/env bash
set -euo pipefail

INPUT="${1:-}"
if [ -z "$INPUT" ]; then
    echo "uso: $0 <caminho/da.apk>" >&2
    echo "o <caminho/da>.odex deve existir ao lado." >&2
    exit 1
fi

if [ ! -f "$INPUT" ]; then
    echo "erro: $INPUT nao existe" >&2
    exit 1
fi

APK_PATH="$(readlink -f "$INPUT")"
APK_DIR="$(dirname "$APK_PATH")"
APK_NAME="$(basename "$APK_PATH" .apk)"
ODEX_PATH="$APK_DIR/$APK_NAME.odex"

if [ ! -f "$ODEX_PATH" ]; then
    echo "erro: nao achei $ODEX_PATH" >&2
    echo "este script so trata APK com .odex ao lado (vendor-app/system-app)." >&2
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DUMP_DEFAULT="$REPO_ROOT/tooling/apks-dumped/dump-0040"
BOOTCLASSPATH_SRC_DIRS="${BOOTCLASSPATH_SRC_DIRS:-$DUMP_DEFAULT/system-framework:$DUMP_DEFAULT/vendor-framework}"
API_LEVEL="${API_LEVEL:-17}"
OUT_DIR="${OUT_DIR:-$REPO_ROOT/tooling/apks-decoded}"
BAKSMALI_JAR="${BAKSMALI_JAR:-$REPO_ROOT/tooling/references/ic1101/apk-rebuilder/input/baksmali-2.5.2.jar}"
SMALI_JAR="${SMALI_JAR:-$REPO_ROOT/tooling/references/ic1101/apk-rebuilder/input/smali-2.5.2.jar}"

for jar in "$BAKSMALI_JAR" "$SMALI_JAR"; do
    if [ ! -f "$jar" ]; then
        echo "erro: $jar nao encontrado." >&2
        echo "ajuste BAKSMALI_JAR / SMALI_JAR, ou rode MIGRATION/setup.sh pra clonar o ic1101." >&2
        exit 1
    fi
done

if ! command -v java >/dev/null; then
    echo "erro: java nao esta no PATH (precisa JDK 17+)" >&2
    exit 1
fi

if ! command -v zip >/dev/null; then
    echo "erro: zip nao esta no PATH" >&2
    exit 1
fi

WORK_DIR="$(mktemp -d -t deodex-"$APK_NAME"-XXXXXX)"
trap 'rm -rf "$WORK_DIR"' EXIT

mkdir -p "$WORK_DIR/bootclasspath" "$WORK_DIR/smali" "$OUT_DIR"

IFS=':' read -ra BCP_DIRS <<<"$BOOTCLASSPATH_SRC_DIRS"
BCP_FILES=0
for dir in "${BCP_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        for f in "$dir"/*.odex; do
            if [ -f "$f" ]; then
                cp "$f" "$WORK_DIR/bootclasspath/"
                BCP_FILES=$((BCP_FILES + 1))
            fi
        done
    fi
done

if [ "$BCP_FILES" -eq 0 ]; then
    echo "erro: nenhum .odex encontrado em BOOTCLASSPATH_SRC_DIRS=$BOOTCLASSPATH_SRC_DIRS" >&2
    exit 1
fi

echo ">> deodex $APK_NAME.odex  (api $API_LEVEL, bootclasspath com $BCP_FILES jars)"
java -jar "$BAKSMALI_JAR" deodex \
    -a "$API_LEVEL" \
    -d "$WORK_DIR/bootclasspath" \
    -o "$WORK_DIR/smali" \
    "$ODEX_PATH"

SMALI_COUNT="$(find "$WORK_DIR/smali" -name '*.smali' -type f | wc -l)"
if [ "$SMALI_COUNT" -eq 0 ]; then
    echo "erro: baksmali rodou mas nao gerou .smali" >&2
    exit 1
fi

echo ">> assemble -> classes.dex ($SMALI_COUNT smali)"
java -jar "$SMALI_JAR" assemble \
    -a "$API_LEVEL" \
    -o "$WORK_DIR/classes.dex" \
    "$WORK_DIR/smali"

OUT_APK="$OUT_DIR/$APK_NAME-deodexed.apk"
cp "$APK_PATH" "$OUT_APK"
(cd "$WORK_DIR" && zip -j -q "$OUT_APK" classes.dex)

DEX_SIZE="$(stat -c%s "$WORK_DIR/classes.dex")"

echo ""
echo "OK."
echo "  smali:        $SMALI_COUNT arquivos"
echo "  classes.dex:  $DEX_SIZE bytes"
echo "  saida:        $OUT_APK"
