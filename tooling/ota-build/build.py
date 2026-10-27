#!/usr/bin/env python3
"""Wrapper em cima do ic1101/ota-builder.

Instala o AutoOk.apk + su setuid em /system. Diferenças do nosso build para o
main.py do upstream:

1. Gera só o rom_type da nossa safra (`0040`, em ROM_TYPES). O `daupdater`
   escolhe o diretório que bate com o `cur_rom` do HU; gerar só o nosso basta.
2. Remove o `assert(ro.product.device == "vcm30t30" || ro.build.product ==
   "vcm30t30")` do updater-script. Se a safra BR tiver sufixo (vcm30t30br,
   vcm30t30lat, ...), o assert falha depois do `daupdater` já ter estagado o
   command em `/cache/recovery/command` e isso vira recovery loop permanente
   (ver `tooling/references/ic1101/docs/updates.md` seção "recovery checklist"
   caution). A proteção perdida é irrelevante no nosso contexto — o pendrive
   só vai na nossa central, e qualquer tentativa de aplicar em outro device
   que não Tegra 3 Mitsubishi quebra depois no mount do bloco APP, não aqui.

Mantém:
- NEW_DA_VERSION="IC1101" (evita o fluxo SystemUpdate app-based, cf. seção
  "SystemUpdateApService" do updates.md).
- NEW_DA_BUILD_TAGS="release-keys" (recovery exige se o HU tiver tags
  release-keys, cf. recovery checklist).
- Janela de 30s via sleep estático ARM — é o design cuidadoso do ic1101 para
  dar tempo de retirar o pendrive durante o boot loop controlado.
"""
from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
OTA_BUILDER_SRC = PROJECT / "tooling" / "references" / "ic1101" / "ota-builder" / "src"
INPUT_DIR = PROJECT / "tooling" / "references" / "ic1101" / "ota-builder" / "input"
OVERLAY_DIR = HERE / "overlay"
OUT_DIR = HERE / "output"

sys.path.insert(0, str(OTA_BUILDER_SRC))
import main as upstream

ROM_TYPES = ["0040"]


CURRENT_ROM_TYPE: str = ""

BUSYBOX_PKG_PATH = "busybox"
BUSYBOX_SRC = HERE / "bin" / "busybox"
SU_PKG_PATH = "su"
SU_SRC = HERE / "bin" / "su"


_orig_stage_tree = upstream.stage_tree


def _patched_stage_tree(staging, overlay_paths, meta, rom_type, overlay_dir, update_binary, sleep_binary, partitions):
    _orig_stage_tree(staging, overlay_paths, meta, rom_type, overlay_dir, update_binary, sleep_binary, partitions)
    if not BUSYBOX_SRC.is_file():
        raise SystemExit(f"missing busybox at {BUSYBOX_SRC}")
    if not SU_SRC.is_file():
        raise SystemExit(f"missing su at {SU_SRC}")
    import shutil as _sh
    _sh.copy2(BUSYBOX_SRC, staging / BUSYBOX_PKG_PATH)
    _sh.copy2(SU_SRC, staging / SU_PKG_PATH)


upstream.stage_tree = _patched_stage_tree


def our_create_updater_script(overlay_paths, meta, partitions):
    """Updater-script de INSTALL do AutoOk. Monta /system (bloco APP), extrai
    AutoOk.apk para /system/app e o su setuid (06755) para /system/xbin, loga
    um ls antes/depois no pendrive, desmonta e quebra o loop do daupdater.

    Sem assert/abort (não prende o recovery em loop se falhar no meio). Este é o
    único gerador que ainda usa set_perm em /system (no AutoOk.apk e no su): é o
    pacote já aplicado no carro, exceção conhecida no MAPA §17.18, fora do teste
    test_set_perm_so_em_tmp. A conferência real do install fica nos ls do pendrive.
    """
    _ = overlay_paths, meta, partitions
    rt = CURRENT_ROM_TYPE
    out = ["show_progress(1.000000, 0);", "set_progress(0.000000);"]

    out.append(f'package_extract_file("{BUSYBOX_PKG_PATH}", "/tmp/busybox");')
    out.append('set_perm(0, 0, 0755, "/tmp/busybox");')

    BB = "/tmp/busybox"
    USB = "/mnt/usbdrive1"
    LOG = f"{USB}/install-{rt}.log"

    def sh(cmd: str) -> str:
        esc = cmd.replace("\\", "\\\\").replace('"', '\\"')
        return f'run_program("{BB}", "sh", "-c", "{esc}");'

    out.append(sh(f"{BB} echo === INSTALL START $({BB} date) rom_type={rt} === > {LOG} 2>&1"))

    out.append('mount("ext4", "EMMC", "/dev/block/platform/sdhci-tegra.3/by-name/APP", "/system");')
    out.append(sh(f"{BB} mount >> {LOG} 2>&1; {BB} echo mount-APP-via-edify-done >> {LOG}"))
    out.append(sh(f"{BB} ls -la /system/app/AutoOk.apk /system/xbin/su >> {LOG} 2>&1; {BB} echo pre-install-check >> {LOG}"))

    out.append('package_extract_file("system/app/AutoOk.apk", "/system/app/AutoOk.apk");')
    out.append('set_perm(0, 0, 0644, "/system/app/AutoOk.apk");')

    out.append(sh(f"{BB} mkdir -p /system/xbin >> {LOG} 2>&1"))
    out.append(f'package_extract_file("{SU_PKG_PATH}", "/system/xbin/su");')
    out.append('set_perm(0, 0, 06755, "/system/xbin/su");')

    out.append(sh(f"{BB} ls -la /system/app/AutoOk.apk /system/xbin/su >> {LOG} 2>&1; {BB} echo post-install-check >> {LOG}"))
    out.append(sh(f"{BB} sync"))
    out.append('unmount("/system");')
    out.append(sh(f"{BB} echo === INSTALL END $({BB} date) === >> {LOG}; {BB} sync"))

    out.append(sh(f"{BB} mv {USB}/SwUpdate2.txt {USB}/SwUpdate2.txt.done 2>>{LOG}; {BB} echo mv-trigger-exit=$? >> {LOG}"))
    out.append(sh(f"{BB} rm -f /cache/.copy_complete 2>>{LOG}; {BB} echo rm-copy-complete-exit=$? >> {LOG}"))
    out.append(sh(f"{BB} sync"))

    out.append(f'package_extract_file("{upstream.SLEEP_PKG_PATH}", "/tmp/sleep");')
    out.append('set_perm(0, 0, 0755, "/tmp/sleep");')
    out.append("set_progress(1.000000);")
    out.append('run_program("/tmp/sleep", "30");')
    return "\n".join(out) + "\n"


upstream.create_updater_script = our_create_updater_script

_orig_build_mdt = upstream.build_mdt


def _tagged_build_mdt(rom_type, *args, **kwargs):
    global CURRENT_ROM_TYPE
    CURRENT_ROM_TYPE = rom_type
    return _orig_build_mdt(rom_type, *args, **kwargs)


upstream.build_mdt = _tagged_build_mdt


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger("civichmi-ota-build")

    overlay_paths = upstream.collect_overlay(OVERLAY_DIR)
    upstream.check_banned(overlay_paths)
    upstream.check_partitions(overlay_paths, upstream.PARTITIONS)
    if not overlay_paths:
        raise SystemExit("overlay vazio em " + str(OVERLAY_DIR))
    meta = upstream.load_meta(INPUT_DIR / "overlay-meta.txt")

    build_dir = OUT_DIR / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    build_dir.mkdir(parents=True, exist_ok=False)
    upstream.write_lf(build_dir / "SwUpdate2.txt", f"Ver:{upstream.NEW_COMMAND_VERSION}\n")

    for overlay_path in overlay_paths:
        m = meta.get(overlay_path, upstream.DEFAULT_META)
        logger.info(
            "deploy: /%s owner=%d:%d mode=0%o",
            overlay_path, m.uid, m.gid, m.mode,
        )

    for rt in ROM_TYPES:
        signed = upstream.build_mdt(
            rt, overlay_paths, meta, build_dir,
            overlay_dir=OVERLAY_DIR,
            update_binary=INPUT_DIR / "update-binary",
            sleep_binary=INPUT_DIR / "sleep" / "output" / "sleep",
            signapk_jar=INPUT_DIR / "signapk.jar",
            sign_cert=INPUT_DIR / "keys" / "testkey.x509.pem",
            sign_key=INPUT_DIR / "keys" / "testkey.pk8",
            partitions=upstream.PARTITIONS,
        )
        logger.info("rom_type=%s -> %s", rt, signed)

    print(f"OK: {build_dir}")


if __name__ == "__main__":
    main()
