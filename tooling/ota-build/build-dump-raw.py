#!/usr/bin/env python3
"""Pacote OTA de BACKUP RAW das partições críticas.

Diferente do `build.py` (instala APK + su) e do `build-rollback.py` (remove
AutoOk + su), este faz **dump raw** das partições críticas (eMMC: APP, CAP,
MITSU, SDA, SDA2; MTD NOR: recovery, boot, whole_device) para imagens
bootáveis gzipadas no pendrive.

Uso: construir e deployar APENAS quando quiser ter backup "bootable" real
(único recurso que permite restaurar firmware em caso de brick total).
Deploy demora ~12-18 min no carro por causa do dd + gzip de ~1.5-2.5 GB.

Pendrive precisa de pelo menos 2.8 GB livres.

Pacote NÃO instala nada em /system — zero risco. Só lê e exporta.

Saída no pendrive após deploy:
- /dump-raw-0040/app.img.gz        (~100-120 MB gzipado — 512 MB raw)
- /dump-raw-0040/cap.img.gz        (~130 MB gzipado — 768 MB raw)
- /dump-raw-0040/mitsu.img.gz      (~40 MB gzipado — 1 GB raw)
- /dump-raw-0040/sda.img.gz        (~50-70 MB gzipado — 128 MB raw, /mnt/data1 com APKs do navi + libNaviApk.so)
- /dump-raw-0040/sda2.img.gz       (~50-70 MB gzipado — 128 MB raw, slot B do SDA)
- /dump-raw-0040/mtd-recovery.img.gz    (~3-5 MB gzipado — 8 MB raw, imagem do recovery com daupdater nativo + ramdisk)
- /dump-raw-0040/mtd-boot.img.gz        (~3-5 MB gzipado — 8 MB raw, kernel + ramdisk + init.rc do boot normal)
- /dump-raw-0040/mtd-whole_device.img.gz (~20-30 MB gzipado — 64 MB raw do NOR inteiro, redundante mas serve de referência de offsets)
- /dump-raw-0040/dump-raw.log      (log do processo + mapping do /proc/mtd)

Restaurar depois é via outro pacote OTA (não implementado — construir sob
demanda em caso de brick real) que faz dd reverso. Importante é TER o backup.
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
OUT_DIR = HERE / "output-dump-raw"

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
    DUMP = f"{USB}/dump-raw-{rom_type}"
    LOG = f"{DUMP}/dump-raw.log"

    def sh(cmd: str) -> str:
        esc = cmd.replace("\\", "\\\\").replace('"', '\\"')
        return f'run_program("{BB}", "sh", "-c", "{esc}");'

    def dump_partition(name: str, by_name: str, progress_after: float) -> list[str]:
        src = f"/dev/block/platform/sdhci-tegra.3/by-name/{by_name}"
        img = f"{DUMP}/{name}.img.gz"
        return [
            sh(f"{BB} echo === dumping {by_name} === >> {LOG} 2>&1"),
            sh(f"{BB} echo pre-dump $({BB} date) >> {LOG}"),
            # $? depois do pipe é do gzip, não do dd (busybox ash não tem
            # pipefail confiável). Para saber se o dd leu a partição inteira,
            # conferir os "records in/out" e os bytes que o dd escreve no LOG.
            sh(f"{BB} dd if={src} bs=4M 2>>{LOG} | {BB} gzip -c > {img} 2>>{LOG}; {BB} echo gzip-exit=$? >> {LOG}"),
            sh(f"{BB} ls -la {img} >> {LOG} 2>&1"),
            sh(f"{BB} echo post-dump $({BB} date) >> {LOG}"),
            sh(f"{BB} sync"),
            f"set_progress({progress_after:.6f});",
        ]

    def dump_mtd(name: str, progress_after: float) -> list[str]:
        # Resolve o índice pelo /proc/mtd (ex.: "mtd3: 00800000 00020000 \"boot\"")
        # em vez de assumir ordem fixa. Dumpa /dev/block/mtdblock<idx> — o block
        # device do MTD, que aceita dd igual ao eMMC. Se o nome não existe no
        # /proc/mtd, loga NOT FOUND e segue (nunca aborta).
        img = f"{DUMP}/mtd-{name}.img.gz"
        resolve = f"idx=$({BB} grep '\"{name}\"' /proc/mtd | {BB} sed 's/mtd\\([0-9]*\\):.*/\\1/')"
        return [
            sh(f"{BB} echo === dumping mtd:{name} === >> {LOG} 2>&1"),
            sh(f"{BB} echo pre-dump $({BB} date) >> {LOG}"),
            sh(
                f"{resolve}; "
                f"if [ -n \"$idx\" ] && [ -b /dev/block/mtdblock$idx ]; "
                f"then {BB} dd if=/dev/block/mtdblock$idx bs=4M 2>>{LOG} | {BB} gzip -c > {img} 2>>{LOG}; "
                f"{BB} echo mtd-{name}-idx=$idx gzip-exit=$? >> {LOG}; "
                f"else {BB} echo mtd-{name} NOT FOUND in /proc/mtd >> {LOG}; fi"
            ),
            sh(f"{BB} ls -la {img} >> {LOG} 2>&1"),
            sh(f"{BB} echo post-dump $({BB} date) >> {LOG}"),
            sh(f"{BB} sync"),
            f"set_progress({progress_after:.6f});",
        ]

    out = [
        "show_progress(1.000000, 0);",
        "set_progress(0.000000);",
        'package_extract_file("busybox", "/tmp/busybox");',
        'set_perm(0, 0, 0755, "/tmp/busybox");',
        "set_progress(0.050000);",
        sh(f"{BB} mkdir -p {DUMP}"),
        sh(f"{BB} echo === DUMP-RAW START $({BB} date) rom_type={rom_type} === > {LOG} 2>&1"),
        sh(f"{BB} df -h {USB} >> {LOG} 2>&1"),
        # Loga o /proc/mtd uma vez pro mapping nome↔índice ficar documentado,
        # mesmo que nenhum MTD seja encontrado no dumpar depois.
        sh(f"{BB} echo === /proc/mtd === >> {LOG} 2>&1; {BB} cat /proc/mtd >> {LOG} 2>&1"),
    ]

    # SDA e SDA2 (128 MB cada) são rápidas comparado a APP/CAP/MITSU, por isso
    # ficam no fim. SDA (/mnt/data1) tem o APK e as libs do navi reais; SDA2 é
    # o slot B equivalente — dumpar o par A/B deixa o backup bootable completo.
    out.extend(dump_partition("app", "APP", 0.48))
    out.extend(dump_partition("cap", "CAP", 0.68))
    out.extend(dump_partition("mitsu", "MITSU", 0.82))
    out.extend(dump_partition("sda", "SDA", 0.88))
    out.extend(dump_partition("sda2", "SDA2", 0.90))
    # MTD NOR (desbloqueia Ghidra no daupdater — recovery tem o binário nativo
    # + ramdisk; boot tem init.rc + kernel; whole_device é redundante mas serve
    # de referência pra conferir que os offsets batem).
    out.extend(dump_mtd("recovery", 0.93))
    out.extend(dump_mtd("boot", 0.95))
    out.extend(dump_mtd("whole_device", 0.97))

    out.extend([
        sh(f"{BB} df -h {USB} >> {LOG} 2>&1"),
        sh(f"{BB} ls -la {DUMP} >> {LOG} 2>&1"),
        sh(f"{BB} echo === DUMP-RAW END $({BB} date) === >> {LOG}"),

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
    logger = logging.getLogger("civichmi-ota-dump-raw")

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
    logger.info("dump-raw mdt: %s", signed)
    print(f"OK: {build_dir}")


if __name__ == "__main__":
    main()
