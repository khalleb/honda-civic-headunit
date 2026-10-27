#!/usr/bin/env python3
"""Pacote OTA de ROLLBACK.

Gera um SwUpdate.mdt que, se aplicado, monta /system rw e remove
/system/app/AutoOk.apk. Nada mais.

Rede de segurança: se o AutoOk.apk instalado causar instabilidade (crash do
launcher, boot loop do framework, aviso ficando preso), copia este pacote
pro pendrive FAT32, pluga e dispara reboot via combo AUDIO 5s. SystemUpdate
+ daupdater aplicam, APK sai.

NÃO copiar pro pendrive junto com o pacote de instalação — ou um ou outro.
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
OUT_DIR = HERE / "output-rollback"

sys.path.insert(0, str(OTA_BUILDER_SRC))
import main as upstream

BUSYBOX_SRC = HERE / "bin" / "busybox"
ROM_TYPE = "0040"


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
    (meta_dir / "updater-script").write_text(_updater_script(rom_type, meta, partitions))


def _updater_script(rom_type: str, meta, partitions) -> str:
    _ = meta, partitions
    BB = "/tmp/busybox"
    USB = "/mnt/usbdrive1"
    LOG = f"{USB}/rollback-{rom_type}.log"
    OKF = f"{USB}/AUTOOK-REMOVED.OK"
    FAILF = f"{USB}/AUTOOK-REMOVED.FAIL"

    def sh(cmd: str) -> str:
        esc = cmd.replace("\\", "\\\\").replace('"', '\\"')
        return f'run_program("{BB}", "sh", "-c", "{esc}");'

    out = [
        "show_progress(1.000000, 0);",
        "set_progress(0.000000);",
        'package_extract_file("busybox", "/tmp/busybox");',
        'set_perm(0, 0, 0755, "/tmp/busybox");',
        sh(f"{BB} echo === ROLLBACK START $({BB} date) === > {LOG} 2>&1"),
        sh(f"{BB} rm -f {OKF} {FAILF} 2>>{LOG}"),
        'mount("ext4", "EMMC", "/dev/block/platform/sdhci-tegra.3/by-name/APP", "/system");',
        sh(f"{BB} ls -la /system/app/AutoOk.apk /system/xbin/su >> {LOG} 2>&1"),
        sh(f"{BB} rm -f /system/app/AutoOk.apk /system/xbin/su >> {LOG} 2>&1; {BB} echo rm-done >> {LOG}"),
        # Gate no pendrive, igual ao restore do DaLauncher: .OK só se o /system
        # montou de verdade (build.prop presente) E os dois alvos sumiram. Sem o
        # teste do build.prop, um /system não montado daria "removido" falso,
        # porque os arquivos "não existem" num mount vazio.
        sh(
            f"if {BB} test -e /system/build.prop && {BB} test ! -e /system/app/AutoOk.apk && {BB} test ! -e /system/xbin/su; "
            f"then {BB} echo removed > {OKF}; {BB} echo rollback-verified-OK >> {LOG}; "
            f"else {BB} echo present-or-unmounted > {FAILF}; {BB} echo rollback-verify-FAILED >> {LOG}; fi"
        ),
        sh(f"{BB} sync"),
        'unmount("/system");',
        sh(f"{BB} echo === ROLLBACK END $({BB} date) === >> {LOG}; {BB} sync"),
        sh(f"{BB} mv {USB}/SwUpdate2.txt {USB}/SwUpdate2.txt.done 2>>{LOG}; {BB} echo mv-trigger-exit=$? >> {LOG}"),
        sh(f"{BB} rm -f /cache/.copy_complete 2>>{LOG}; {BB} echo rm-copy-complete-exit=$? >> {LOG}"),
        sh(f"{BB} sync"),
        f'package_extract_file("{upstream.SLEEP_PKG_PATH}", "/tmp/sleep");',
        'set_perm(0, 0, 0755, "/tmp/sleep");',
        "set_progress(1.000000);",
        'run_program("/tmp/sleep", "30");',
    ]
    return "\n".join(out) + "\n"


upstream.stage_tree = _patched_stage_tree


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger("civichmi-ota-rollback")

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
    logger.info("rollback mdt: %s", signed)
    print(f"OK: {build_dir}")


if __name__ == "__main__":
    main()
