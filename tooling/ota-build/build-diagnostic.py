#!/usr/bin/env python3
"""Pacote OTA de DIAGNOSTICO focado - coleta so o que precisamos pra
tres investigacoes abertas e grava direto no pendrive, sem tar.

1. BUG DO MUDO (CarPlay BT muta sozinho em ligacao):
   - /data/data/com.khalleb.civichmi.autook/files/autook.log (+ .1)
   - A gente le pra ver se o AutoOk disparou tap no horario da ligacao.

2. REMOCAO DO AVISO DE VEZ:
   - /data/data/com.mitsubishielectric.ada.app.dalauncher/ inteiro
     (shared_prefs/ XML, databases/*.db, cache ignoravel).
   - /data/property/ - tudo que foi salvo como persist.*
   - Pra achar o gate que decide se mostra o disclaimer.

3. CONTEXTO:
   - Mount info, df do pendrive, lista de /data/data/ raiz.

Zero escrita em /system. Zero risco. Rapido (~3 min no carro).

Saida: /mnt/usbdrive1/diag-0040/<timestamp>/ com arvore navegavel.
"""
from __future__ import annotations

import logging
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
OTA_BUILDER_SRC = PROJECT / "tooling" / "references" / "ic1101" / "ota-builder" / "src"
INPUT_DIR = PROJECT / "tooling" / "references" / "ic1101" / "ota-builder" / "input"
OUT_DIR = HERE / "output-diagnostic"

sys.path.insert(0, str(OTA_BUILDER_SRC))
import main as upstream

BUSYBOX_SRC = HERE / "bin" / "busybox"
ROM_TYPE = "0040"

AUTOOK_PKG = "com.khalleb.civichmi.autook"
DALAUNCHER_PKG = "com.mitsubishielectric.ada.app.dalauncher"


def _patched_stage_tree(staging, overlay_paths, meta, rom_type, overlay_dir, update_binary, sleep_binary, partitions):
    _ = overlay_paths, overlay_dir
    (staging / "system" / "vendor").mkdir(parents=True, exist_ok=True)
    upstream.write_lf(
        staging / "system" / "build.prop",
        f"ro.build.id={upstream.NEW_DA_VERSION}\nro.build.tags={upstream.NEW_DA_BUILD_TAGS}\n",
    )
    upstream.write_lf(staging / "system" / "vendor" / "build.prop", f"custom_rom.type={rom_type}\n")

    sleep_dst = staging / upstream.SLEEP_PKG_PATH
    sleep_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(sleep_binary, sleep_dst)
    shutil.copy2(BUSYBOX_SRC, staging / "busybox")

    meta_dir = staging / "META-INF" / "com" / "google" / "android"
    meta_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(update_binary, meta_dir / "update-binary")
    (meta_dir / "updater-script").write_text(_updater_script(rom_type))


def _updater_script(rom_type: str) -> str:
    BB = "/tmp/busybox"
    USB = "/mnt/usbdrive1"
    STAMP = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    OUT = f"{USB}/diag-{rom_type}/{STAMP}"
    LOG = f"{OUT}/collect.log"

    def sh(cmd: str) -> str:
        esc = cmd.replace("\\", "\\\\").replace('"', '\\"')
        return f'run_program("{BB}", "sh", "-c", "{esc}");'

    def ts(label: str) -> list[str]:
        return [sh(f"{BB} echo === {label} === >> {LOG}"), sh(f"{BB} date >> {LOG}")]

    out = [
        "show_progress(1.000000, 0);",
        "set_progress(0.000000);",
        'package_extract_file("busybox", "/tmp/busybox");',
        'set_perm(0, 0, 0755, "/tmp/busybox");',
        sh(f"{BB} mkdir -p {OUT}/autook {OUT}/dalauncher {OUT}/properties {OUT}/context"),
    ]
    out.extend(ts("DIAG START"))
    out.extend([
        sh(f"{BB} echo rom_type={rom_type} >> {LOG}"),
        sh(f"{BB} df -h >> {LOG} 2>&1"),
        sh(f"{BB} cat /proc/mounts > {OUT}/context/mounts.txt 2>>{LOG}"),
        sh(f"{BB} ls -la /data/data/ > {OUT}/context/data-data-ls.txt 2>>{LOG}"),
        sh(f"{BB} ls -la /data/property/ > {OUT}/context/property-ls.txt 2>>{LOG}"),
    ])

    out.append("set_progress(0.200000);")
    out.extend(ts("COLLECT AUTOOK"))
    out.extend([
        sh(f"{BB} cp -rL /data/data/{AUTOOK_PKG}/files/ {OUT}/autook/files/ 2>>{LOG}; {BB} echo cp-autook-files-exit=$? >> {LOG}"),
        sh(f"{BB} ls -laR /data/data/{AUTOOK_PKG}/ > {OUT}/autook/tree.txt 2>>{LOG}"),
    ])

    out.append("set_progress(0.500000);")
    out.extend(ts("COLLECT DALAUNCHER"))
    out.extend([
        sh(f"{BB} cp -rL /data/data/{DALAUNCHER_PKG}/shared_prefs/ {OUT}/dalauncher/shared_prefs/ 2>>{LOG}; {BB} echo cp-prefs-exit=$? >> {LOG}"),
        sh(f"{BB} cp -rL /data/data/{DALAUNCHER_PKG}/databases/ {OUT}/dalauncher/databases/ 2>>{LOG}; {BB} echo cp-dbs-exit=$? >> {LOG}"),
        sh(f"{BB} cp -rL /data/data/{DALAUNCHER_PKG}/files/ {OUT}/dalauncher/files/ 2>>{LOG}; {BB} echo cp-files-exit=$? >> {LOG}"),
        sh(f"{BB} ls -laR /data/data/{DALAUNCHER_PKG}/ > {OUT}/dalauncher/tree.txt 2>>{LOG}"),
    ])

    out.append("set_progress(0.750000);")
    out.extend(ts("COLLECT PROPERTIES"))
    out.extend([
        sh(f"{BB} cp -rL /data/property/ {OUT}/properties/property/ 2>>{LOG}; {BB} echo cp-prop-exit=$? >> {LOG}"),
        sh(f"{BB} cp -L /data/system/packages.xml {OUT}/context/packages.xml 2>>{LOG}"),
    ])

    out.append("set_progress(0.900000);")
    out.extend(ts("DIAG END"))
    out.extend([
        sh(f"{BB} du -sh {OUT} >> {LOG} 2>&1"),
        sh(f"{BB} df -h {USB} >> {LOG} 2>&1"),
        sh(f"{BB} mv {USB}/SwUpdate2.txt {USB}/SwUpdate2.txt.done 2>>{LOG}; {BB} echo mv-trigger-exit=$? >> {LOG}"),
        sh(f"{BB} rm -f /cache/.copy_complete 2>>{LOG}; {BB} echo rm-copy-complete-exit=$? >> {LOG}"),
        sh(f"{BB} sync"),
        f'package_extract_file("{upstream.SLEEP_PKG_PATH}", "/tmp/sleep");',
        'set_perm(0, 0, 0755, "/tmp/sleep");',
        "set_progress(1.000000);",
        'run_program("/tmp/sleep", "60");',
    ])
    return "\n".join(out) + "\n"


upstream.stage_tree = _patched_stage_tree


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger("civichmi-ota-diagnostic")

    build_dir = OUT_DIR / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    build_dir.mkdir(parents=True, exist_ok=False)
    upstream.write_lf(build_dir / "SwUpdate2.txt", f"Ver:{upstream.NEW_COMMAND_VERSION}\n")

    signed = upstream.build_mdt(
        ROM_TYPE, [], {}, build_dir,
        overlay_dir=HERE / "overlay",
        update_binary=INPUT_DIR / "update-binary",
        sleep_binary=INPUT_DIR / "sleep" / "output" / "sleep",
        signapk_jar=INPUT_DIR / "signapk.jar",
        sign_cert=INPUT_DIR / "keys" / "testkey.x509.pem",
        sign_key=INPUT_DIR / "keys" / "testkey.pk8",
        partitions=upstream.PARTITIONS,
    )
    logger.info("diag mdt: %s", signed)
    print(f"OK: {build_dir}")


if __name__ == "__main__":
    main()
