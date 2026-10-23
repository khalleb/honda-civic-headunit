#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import logging
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
OTA_BUILDER_SRC = PROJECT / "tooling" / "references" / "ic1101" / "ota-builder" / "src"
INPUT_DIR = PROJECT / "tooling" / "references" / "ic1101" / "ota-builder" / "input"
OUT_DIR = HERE / "output-dalauncher-fase10"

DALAUNCHER_PATCHED_APK = PROJECT / "tooling" / "fase10" / "output" / "DaLauncher-fase10.apk"
ANDROID_BT = Path(os.environ.get("ANDROID_BT", str(Path.home() / "sdks" / "Android" / "build-tools" / "33.0.2")))
EXPECTED_CERT_SHA256 = "a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc"

sys.path.insert(0, str(OTA_BUILDER_SRC))
import main as upstream

BUSYBOX_SRC = HERE / "bin" / "busybox"
ROM_TYPE = "0040"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_source() -> str:
    if not DALAUNCHER_PATCHED_APK.is_file():
        raise SystemExit(
            f"APK patcheado ausente: {DALAUNCHER_PATCHED_APK}\n"
            f"rode tooling/fase10/rebuild-dalauncher.sh primeiro"
        )
    apksigner = ANDROID_BT / "apksigner"
    if not apksigner.is_file():
        raise SystemExit(f"apksigner nao encontrado: {apksigner} (ajuste ANDROID_BT)")
    res = subprocess.run(
        [str(apksigner), "verify", "--print-certs", str(DALAUNCHER_PATCHED_APK)],
        capture_output=True,
        text=True,
    )
    if EXPECTED_CERT_SHA256 not in res.stdout.lower():
        raise SystemExit(
            f"APK nao esta assinado com o testkey AOSP esperado ({EXPECTED_CERT_SHA256}).\n"
            f"saida do apksigner:\n{res.stdout}\n"
            f"rode tooling/fase10/rebuild-dalauncher.sh"
        )
    return _sha256(DALAUNCHER_PATCHED_APK)


def _patched_stage_tree(staging, overlay_paths, meta, rom_type, overlay_dir, update_binary, sleep_binary, partitions):
    _ = overlay_paths, meta, overlay_dir

    dst = staging / "system/vendor/app/DaLauncher.apk"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DALAUNCHER_PATCHED_APK, dst)

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
    (meta_dir / "updater-script").write_text(_updater_script(rom_type, partitions))


def _updater_script(rom_type: str, partitions) -> str:
    _ = partitions
    BB = "/tmp/busybox"
    USB = "/mnt/usbdrive1"
    LOG = f"{USB}/dalauncher-fase10-{rom_type}.log"
    ODEX = "/system/vendor/app/DaLauncher.odex"
    OKF = f"{USB}/FASE10-ODEX-REMOVED.OK"
    FAILF = f"{USB}/FASE10-ODEX-REMOVED.FAIL"

    def sh(cmd: str) -> str:
        esc = cmd.replace("\\", "\\\\").replace('"', '\\"')
        return f'run_program("{BB}", "sh", "-c", "{esc}");'

    out = [
        'assert(getprop("ro.product.device") == "vcm30t30" || getprop("ro.build.product") == "vcm30t30");',
        "show_progress(1.000000, 0);",
        "set_progress(0.000000);",
        'package_extract_file("busybox", "/tmp/busybox");',
        'set_perm(0, 0, 0755, "/tmp/busybox");',
        sh(f"{BB} echo === DALAUNCHER-FASE10 START $({BB} date) rom_type={rom_type} === > {LOG} 2>&1"),
        sh(f"{BB} rm -f {OKF} {FAILF} 2>>{LOG}"),
        'mount("ext4", "EMMC", "/dev/block/platform/sdhci-tegra.3/by-name/APP", "/system");',
        'mount("ext4", "EMMC", "/dev/block/platform/sdhci-tegra.3/by-name/CAP", "/system/vendor");',
        sh(f"{BB} mount >> {LOG} 2>&1; {BB} echo mount-done >> {LOG}"),
        sh(f"{BB} ls -la /system/vendor/app/DaLauncher.apk {ODEX} >> {LOG} 2>&1; {BB} echo pre-deploy-ls >> {LOG}"),
        'package_extract_file("system/vendor/app/DaLauncher.apk", "/system/vendor/app/DaLauncher.apk");',
        'set_perm(0, 0, 0644, "/system/vendor/app/DaLauncher.apk");',
        sh(
            f"{BB} rm -f {ODEX} >> {LOG} 2>&1; "
            f"if {BB} test ! -e {ODEX}; then {BB} echo removed > {OKF}; {BB} echo odex-removed-OK >> {LOG}; "
            f"else {BB} echo present > {FAILF}; {BB} echo odex-remove-FAILED >> {LOG}; fi"
        ),
        sh(f"{BB} md5sum /system/vendor/app/DaLauncher.apk >> {LOG} 2>&1; {BB} echo post-deploy-md5-apk >> {LOG}"),
        sh(f"{BB} sync"),
        'unmount("/system/vendor");',
        'unmount("/system");',
        sh(f"{BB} echo === DALAUNCHER-FASE10 END $({BB} date) === >> {LOG}; {BB} sync"),
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
    logger = logging.getLogger("civichmi-ota-dalauncher-fase10")

    apk_sha = _verify_source()
    logger.info("APK patcheado verificado (testkey AOSP), sha256: %s", apk_sha)

    build_dir = OUT_DIR / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    build_dir.mkdir(parents=True, exist_ok=False)
    upstream.write_lf(build_dir / "SwUpdate2.txt", f"Ver:{upstream.NEW_COMMAND_VERSION}\n")

    overlay_paths = ["system/vendor/app/DaLauncher.apk"]
    overlay_meta = {"system/vendor/app/DaLauncher.apk": upstream.FileMeta(0, 0, 0o644)}

    signed = upstream.build_mdt(
        ROM_TYPE,
        overlay_paths,
        overlay_meta,
        build_dir,
        overlay_dir=HERE / "overlay",
        update_binary=INPUT_DIR / "update-binary",
        sleep_binary=INPUT_DIR / "sleep" / "output" / "sleep",
        signapk_jar=INPUT_DIR / "signapk.jar",
        sign_cert=INPUT_DIR / "keys" / "testkey.x509.pem",
        sign_key=INPUT_DIR / "keys" / "testkey.pk8",
        partitions=upstream.PARTITIONS,
    )
    logger.info("dalauncher-fase10 mdt: %s", signed)
    print(f"OK: {build_dir}")


if __name__ == "__main__":
    main()
