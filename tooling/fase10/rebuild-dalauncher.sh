#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DUMP="$REPO_ROOT/tooling/apks-dumped/dump-0040"
APK_SRC="$DUMP/vendor-app/DaLauncher.apk"
ODEX_SRC="$DUMP/vendor-app/DaLauncher.odex"
PATCH_FILE="$REPO_ROOT/tooling/fase10/opening-divide-activity-skip-disclaimer.patch"
TARGET_SMALI="com/mitsubishielectric/ada/app/dalauncher/OpeningDivideActivity.smali"
BCP_DIRS="$DUMP/system-framework $DUMP/vendor-framework"
BAKSMALI_JAR="$REPO_ROOT/tooling/references/ic1101/apk-rebuilder/input/baksmali-2.5.2.jar"
SMALI_JAR="$REPO_ROOT/tooling/references/ic1101/apk-rebuilder/input/smali-2.5.2.jar"
TESTKEY_PK8="$REPO_ROOT/tooling/references/ic1101/ota-builder/input/keys/testkey.pk8"
TESTKEY_PEM="$REPO_ROOT/tooling/references/ic1101/ota-builder/input/keys/testkey.x509.pem"
ANDROID_BT="${ANDROID_BT:-$HOME/sdks/Android/build-tools/33.0.2}"
ZIPALIGN="$ANDROID_BT/zipalign"
APKSIGNER="$ANDROID_BT/apksigner"
EXPECTED_CERT_SHA256="a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc"
OUT_DIR="$REPO_ROOT/tooling/fase10/output"
OUT_APK="$OUT_DIR/DaLauncher-fase10.apk"
API_LEVEL=17

for f in "$APK_SRC" "$ODEX_SRC" "$PATCH_FILE" "$BAKSMALI_JAR" "$SMALI_JAR" "$TESTKEY_PK8" "$TESTKEY_PEM" "$ZIPALIGN" "$APKSIGNER"; do
    [ -e "$f" ] || { echo "erro: $f nao encontrado" >&2; exit 1; }
done

mkdir -p "$OUT_DIR"
WORK_DIR="$(mktemp -d -t dalauncher-fase10-XXXXXX)"
trap 'rm -rf "$WORK_DIR"' EXIT
mkdir -p "$WORK_DIR/bootclasspath" "$WORK_DIR/smali"

bcp=0
for dir in $BCP_DIRS; do
    [ -d "$dir" ] || continue
    for f in "$dir"/*.odex; do
        [ -f "$f" ] && { cp "$f" "$WORK_DIR/bootclasspath/"; bcp=$((bcp + 1)); }
    done
done
[ "$bcp" -gt 0 ] || { echo "erro: bootclasspath vazio ($BCP_DIRS)" >&2; exit 1; }

echo ">> baksmali deodex ($bcp jars no bootclasspath)"
java -jar "$BAKSMALI_JAR" deodex -a "$API_LEVEL" -d "$WORK_DIR/bootclasspath" -o "$WORK_DIR/smali" "$ODEX_SRC"

cp -r "$WORK_DIR/smali" "$WORK_DIR/smali-orig"

echo ">> aplica patch"
(cd "$WORK_DIR/smali" && git apply -p1 --recount "$PATCH_FILE")

echo ">> verifica patch aplicado"
if grep -q "if-nez v0, :cond_9" "$WORK_DIR/smali/$TARGET_SMALI"; then
    echo "erro: 'if-nez v0, :cond_9' ainda presente -- patch nao aplicou no lugar esperado" >&2
    exit 1
fi
grep -q "goto :cond_9" "$WORK_DIR/smali/$TARGET_SMALI" || { echo "erro: 'goto :cond_9' ausente apos patch" >&2; exit 1; }

echo ">> smali assemble (patcheado -> dex final)"
java -jar "$SMALI_JAR" assemble -a "$API_LEVEL" -o "$WORK_DIR/classes.dex" "$WORK_DIR/smali"

echo ">> prova: unica diferenca orig->patch no bytecode e OpeningDivideActivity"
java -jar "$SMALI_JAR" assemble -a "$API_LEVEL" -o "$WORK_DIR/classes-orig.dex" "$WORK_DIR/smali-orig"
java -jar "$BAKSMALI_JAR" disassemble -a "$API_LEVEL" -o "$WORK_DIR/dis-orig" "$WORK_DIR/classes-orig.dex"
java -jar "$BAKSMALI_JAR" disassemble -a "$API_LEVEL" -o "$WORK_DIR/dis-patch" "$WORK_DIR/classes.dex"
CHANGED="$({ LC_ALL=C diff -rq "$WORK_DIR/dis-orig" "$WORK_DIR/dis-patch" || true; } | awk '{print $2}' | xargs -r -n1 basename | sort -u)"
if [ "$CHANGED" != "OpeningDivideActivity.smali" ]; then
    echo "erro: diferenca orig->patch no bytecode nao se limita a OpeningDivideActivity.smali:" >&2
    echo "${CHANGED:-<nenhuma -- patch nao teve efeito>}" >&2
    exit 1
fi
echo "   confirmado: so OpeningDivideActivity mudou entre orig e patch"

echo ">> prepara APK unsigned (remove META-INF antigo + injeta classes.dex)"
cp "$APK_SRC" "$WORK_DIR/work.apk"
zip -q --delete "$WORK_DIR/work.apk" 'META-INF/*' || true
(cd "$WORK_DIR" && zip -q -j work.apk classes.dex)

echo ">> zipalign 4"
"$ZIPALIGN" -p -f 4 "$WORK_DIR/work.apk" "$WORK_DIR/aligned.apk"

echo ">> apksigner sign (testkey AOSP)"
"$APKSIGNER" sign --key "$TESTKEY_PK8" --cert "$TESTKEY_PEM" \
    --v1-signing-enabled true --v2-signing-enabled true \
    --out "$OUT_APK" "$WORK_DIR/aligned.apk" 2>&1 | grep -v '^WARNING' || true

echo ">> verifica assinatura == testkey AOSP"
CERT_SHA="$("$APKSIGNER" verify --print-certs "$OUT_APK" 2>/dev/null | grep -i 'SHA-256 digest' | head -1 | grep -oiE '[0-9a-f]{64}' || true)"
if [ "$CERT_SHA" != "$EXPECTED_CERT_SHA256" ]; then
    echo "erro: cert da assinatura ($CERT_SHA) != testkey AOSP esperado ($EXPECTED_CERT_SHA256)" >&2
    exit 1
fi

APK_SIZE="$(stat -c%s "$OUT_APK")"
APK_SHA="$(sha256sum "$OUT_APK" | awk '{print $1}')"
echo ""
echo "OK."
echo "  saida:  $OUT_APK"
echo "  size:   $APK_SIZE bytes"
echo "  cert:   $CERT_SHA (testkey AOSP)"
echo "  sha256: $APK_SHA"
