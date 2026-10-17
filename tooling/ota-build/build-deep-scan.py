#!/usr/bin/env python3
"""Pacote OTA de DEEP SCAN - varre tudo que o recovery consegue.

Objetivo: coletar dados suficientes para que a IA gere automaticamente
o `docs/MAPA.md` (atlas da central). Roda em recovery (sem Android),
monta todas as particoes acessiveis em modo read-only, lista estrutura
inteira, copia arquivos-chave (build.prop, packages.xml, vold.fstab),
dumpa /proc/*, e compacta tudo em tar.gz pro pendrive.

Zero modificacao em /system. Zero risco. ~5-15 min no carro.

Pendrive precisa de pelo menos 500MB livres.

Saida: /mnt/usbdrive1/deep-scan-0040/scan.tar.gz (~5-20MB comprimido)
       + /mnt/usbdrive1/deep-scan-0040/scan.log

Lecoes de iteracoes anteriores:
- UDA e CAC ja vem montadas pelo recovery em /data e /cache. Usar
  esses mount points existentes em vez de re-montar.
- `init.rc` fica no ramdisk do boot, nao em /system/etc.
- `packages.xml` fica em /data/system (nao /system/system).
- busybox tar nao fork+exec gzip externo; precisa pipe explicito:
  `tar cf - | gzip -c > out.tar.gz`.
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
OUT_DIR = HERE / "output-deep-scan"

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
    OUT_FINAL = f"{USB}/deep-scan-{rom_type}"
    STAGE = "/tmp/scan"
    LOG = f"{OUT_FINAL}/scan.log"
    MNT = "/tmp/mnt"
    BY_NAME = "/dev/block/platform/sdhci-tegra.3/by-name"

    def sh(cmd: str) -> str:
        esc = cmd.replace("\\", "\\\\").replace('"', '\\"')
        return f'run_program("{BB}", "sh", "-c", "{esc}");'

    def ts(label: str) -> list[str]:
        return [sh(f"{BB} echo === {label} === >> {LOG}"), sh(f"{BB} date >> {LOG}")]

    def mount_and_scan(name: str, by_name: str) -> list[str]:
        src = f"{BY_NAME}/{by_name}"
        mp = f"{MNT}/{name}"
        out = f"{STAGE}/parts/{name}"
        return [
            sh(f"{BB} mkdir -p {mp} {out}"),
            sh(f"{BB} mount -o ro -t ext4 {src} {mp} 2>>{LOG}; {BB} echo mount-{name}-exit=$? >> {LOG}"),
            sh(f"{BB} ls -laR {mp} > {out}/tree.txt 2>>{LOG}"),
            sh(f"{BB} du -shx {mp}/* > {out}/dusize.txt 2>>{LOG}"),
            sh(f"{BB} find {mp} -maxdepth 6 -name '*.apk' > {out}/apks-paths.txt 2>>{LOG}"),
            sh(f"{BB} find {mp} -maxdepth 6 -name '*.jar' > {out}/jars-paths.txt 2>>{LOG}"),
            sh(f"{BB} find {mp} -maxdepth 8 \\( -name 'com.honda*' -o -name 'com.mitsub*' -o -name 'data1' -o -name 'com.aha*' -o -name 'com.yesway*' \\) > {out}/honda-paths.txt 2>>{LOG}"),
        ]

    def copy_app_configs() -> list[str]:
        mp = f"{MNT}/APP"
        out = f"{STAGE}/parts/APP/configs"
        return [
            sh(f"{BB} mkdir -p {out}"),
            sh(f"{BB} cp -L {mp}/build.prop {out}/build.prop 2>>{LOG}"),
            sh(f"{BB} cp -L {mp}/etc/vold.fstab {out}/vold.fstab 2>>{LOG}"),
            sh(f"{BB} cp -L {mp}/etc/install-recovery.sh {out}/install-recovery.sh 2>>{LOG}"),
            sh(f"{BB} cp -L {mp}/etc/dbus.conf {out}/dbus.conf 2>>{LOG}"),
            sh(f"{BB} cp -L {mp}/etc/init.goldfish.sh {out}/init.goldfish.sh 2>>{LOG}"),
            sh(f"{BB} cp -rL {mp}/etc/permissions/ {out}/permissions/ 2>>{LOG}"),
            sh(f"{BB} cp -rL {mp}/etc/security/ {out}/security/ 2>>{LOG}"),
            sh(f"{BB} ls -la {mp}/xbin/ > {out}/xbin-ls.txt 2>>{LOG}"),
            sh(f"{BB} ls -la {mp}/bin/ > {out}/bin-ls.txt 2>>{LOG}"),
        ]

    def copy_cap_configs() -> list[str]:
        mp = f"{MNT}/CAP"
        out = f"{STAGE}/parts/CAP/configs"
        return [
            sh(f"{BB} mkdir -p {out}"),
            sh(f"{BB} cp -L {mp}/build.prop {out}/build.prop 2>>{LOG}"),
            sh(f"{BB} ls -la {mp}/ > {out}/root-ls.txt 2>>{LOG}"),
            sh(f"{BB} ls -la {mp}/bin/ > {out}/bin-ls.txt 2>>{LOG}"),
            sh(f"{BB} ls -la {mp}/etc/ > {out}/etc-ls.txt 2>>{LOG}"),
            sh(f"{BB} ls -la {mp}/lib/ > {out}/lib-ls.txt 2>>{LOG}"),
        ]

    def scan_premounted(name: str, mp: str) -> list[str]:
        out = f"{STAGE}/parts/{name}"
        return [
            sh(f"{BB} mkdir -p {out} {out}/configs"),
            sh(f"{BB} echo premounted at {mp} > {out}/mount-info.txt"),
            sh(f"{BB} ls -laR {mp} > {out}/tree.txt 2>>{LOG}"),
            sh(f"{BB} du -shx {mp}/* > {out}/dusize.txt 2>>{LOG}"),
            sh(f"{BB} find {mp} -maxdepth 6 -name '*.apk' > {out}/apks-paths.txt 2>>{LOG}"),
            sh(f"{BB} find {mp} -maxdepth 6 -name '*.jar' > {out}/jars-paths.txt 2>>{LOG}"),
            sh(f"{BB} find {mp} -maxdepth 8 \\( -name 'com.honda*' -o -name 'com.mitsub*' -o -name 'data1' -o -name 'com.aha*' -o -name 'com.yesway*' \\) > {out}/honda-paths.txt 2>>{LOG}"),
        ]

    def copy_uda_configs() -> list[str]:
        out = f"{STAGE}/parts/UDA/configs"
        return [
            sh(f"{BB} mkdir -p {out}"),
            sh(f"{BB} cp -L /data/system/packages.xml {out}/packages.xml 2>>{LOG}"),
            sh(f"{BB} cp -L /data/system/packages.list {out}/packages.list 2>>{LOG}"),
            sh(f"{BB} cp -rL /data/system/users/ {out}/users/ 2>>{LOG}"),
            sh(f"{BB} cp -rL /data/anr/ {out}/anr/ 2>>{LOG}"),
            sh(f"{BB} ls -laR /data/data/ > {out}/data-data-tree.txt 2>>{LOG}"),
            sh(f"{BB} ls -la /data/local/tmp/ > {out}/local-tmp-ls.txt 2>>{LOG}"),
            sh(f"{BB} find /data -maxdepth 4 -name 'autook*' > {out}/autook-trace.txt 2>>{LOG}"),
        ]

    def umount(name: str) -> list[str]:
        mp = f"{MNT}/{name}"
        return [
            sh(f"{BB} umount {mp} 2>>{LOG}; {BB} echo umount-{name}-exit=$? >> {LOG}"),
            sh(f"{BB} sync"),
        ]

    out = [
        "show_progress(1.000000, 0);",
        "set_progress(0.000000);",
        'package_extract_file("busybox", "/tmp/busybox");',
        'set_perm(0, 0, 0755, "/tmp/busybox");',
        "set_progress(0.030000);",
        sh(f"{BB} mkdir -p {OUT_FINAL} {STAGE}/proc {STAGE}/dev {STAGE}/configs {STAGE}/parts {MNT}"),
    ]
    out.extend(ts("DEEP SCAN START"))
    out.extend([
        sh(f"{BB} echo rom_type={rom_type} >> {LOG}"),
        sh(f"{BB} df -h >> {LOG} 2>&1"),
        sh(f"{BB} cat /proc/mounts > {STAGE}/proc/mounts.txt"),
        sh(f"{BB} cat /proc/partitions > {STAGE}/proc/partitions.txt"),
        sh(f"{BB} cat /proc/cpuinfo > {STAGE}/proc/cpuinfo.txt"),
        sh(f"{BB} cat /proc/meminfo > {STAGE}/proc/meminfo.txt"),
        sh(f"{BB} cat /proc/version > {STAGE}/proc/version.txt"),
        sh(f"{BB} cat /proc/last_kmsg > {STAGE}/proc/last_kmsg.txt 2>>{LOG}"),
        sh(f"{BB} dmesg > {STAGE}/proc/dmesg.txt 2>>{LOG}"),
        sh(f"{BB} ls -la {BY_NAME}/ > {STAGE}/dev/by-name.txt 2>>{LOG}"),
        sh(f"{BB} ls -la /dev/block/ > {STAGE}/dev/block-ls.txt 2>>{LOG}"),
        sh(f"{BB} cat /etc/fstab > {STAGE}/configs/fstab-recovery.txt 2>>{LOG}"),
        sh(f"{BB} cat /etc/recovery.fstab > {STAGE}/configs/recovery-fstab.txt 2>>{LOG}"),
        sh(f"{BB} ls -la /sbin/ > {STAGE}/configs/sbin-ls.txt 2>>{LOG}"),
        sh(f"{BB} ls -la /system/ > {STAGE}/configs/sysroot-ls.txt 2>>{LOG}"),
    ])

    out.append("set_progress(0.100000);")
    out.extend(ts("SCAN APP"))
    out.extend(mount_and_scan("APP", "APP"))
    out.extend(copy_app_configs())
    out.extend(umount("APP"))

    out.append("set_progress(0.250000);")
    out.extend(ts("SCAN CAP"))
    out.extend(mount_and_scan("CAP", "CAP"))
    out.extend(copy_cap_configs())
    out.extend(umount("CAP"))

    out.append("set_progress(0.400000);")
    out.extend(ts("SCAN MITSU"))
    out.extend(mount_and_scan("MITSU", "MITSU"))
    out.extend(umount("MITSU"))

    out.append("set_progress(0.500000);")
    out.extend(ts("SCAN UDA (premounted /data)"))
    out.extend(scan_premounted("UDA", "/data"))
    out.extend(copy_uda_configs())

    out.append("set_progress(0.650000);")
    out.extend(ts("SCAN CAC (premounted /cache)"))
    out.extend(scan_premounted("CAC", "/cache"))

    out.append("set_progress(0.700000);")
    out.extend(ts("SCAN SDA"))
    out.extend(mount_and_scan("SDA", "SDA"))
    out.extend(umount("SDA"))

    out.append("set_progress(0.800000);")
    out.extend(ts("SCAN SDA2"))
    out.extend(mount_and_scan("SDA2", "SDA2"))
    out.extend(umount("SDA2"))

    out.append("set_progress(0.880000);")
    out.extend(ts("SCAN SDC"))
    out.extend(mount_and_scan("SDC", "SDC"))
    out.extend(umount("SDC"))

    out.append("set_progress(0.920000);")
    out.extend(ts("SCAN LOG"))
    out.extend(mount_and_scan("LOG", "LOG"))
    out.extend(umount("LOG"))

    out.append("set_progress(0.950000);")
    out.extend(ts("BUILDING TARBALL"))
    out.extend([
        sh(f"{BB} du -sh {STAGE} >> {LOG} 2>&1"),
        sh(f"{BB} tar cf - -C {STAGE} . 2>>{LOG} | {BB} gzip -c > {OUT_FINAL}/scan.tar.gz 2>>{LOG}"),
        sh(f"{BB} echo tar-pipe-exit=$? >> {LOG}"),
        sh(f"{BB} ls -la {OUT_FINAL}/scan.tar.gz >> {LOG} 2>&1"),
        sh(f"{BB} df -h {USB} >> {LOG} 2>&1"),
    ])
    out.extend(ts("DEEP SCAN END"))

    out.extend([
        sh(f"{BB} mv {USB}/SwUpdate2.txt {USB}/SwUpdate2.txt.done 2>>{LOG}; {BB} echo mv-trigger-exit=$? >> {LOG}"),
        sh(f"{BB} rm -f /cache/.copy_complete 2>>{LOG}; {BB} echo rm-copy-complete-exit=$? >> {LOG}"),
        sh(f"{BB} sync"),
        f'package_extract_file("{upstream.SLEEP_PKG_PATH}", "/tmp/sleep");',
        'set_perm(0, 0, 0755, "/tmp/sleep");',
        "set_progress(1.000000);",
        'run_program("/tmp/sleep", "120");',
    ])
    return "\n".join(out) + "\n"


upstream.stage_tree = _patched_stage_tree


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger("civichmi-ota-deep-scan")

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
    logger.info("deep-scan mdt: %s", signed)
    print(f"OK: {build_dir}")


if __name__ == "__main__":
    main()
