#!/usr/bin/env python3
"""Pacote OTA de ENABLE-ADB — habilita ADB via USB sem combo físico.

Objetivo: deixar a central em USB Device mode persistente, pra o cabo USB-A
conectado no PC enumerar como dispositivo ADB (não como host). Hoje o único
caminho é o combo físico 'Brightness + Phone + Volume/Power → Phone → Home'
no menu secreto (ic1101 issue #20). Com AutoOk + su já instalados, o pacote
OTA pode gravar a propriedade persistente que o `usbdetectd` lê no boot.

O que o pacote faz:
1. Monta /data (geralmente já está montado no recovery, mas garantimos).
2. Escreve `/data/property/persist.sys.usb1_mode` com conteúdo "device".
   É o padrão Android: `persist.*` sysprops ficam em /data/property/<nome>
   como arquivos de texto. No boot normal subsequente, `usbdetectd` lê a
   prop e configura `tegra-otg` para enable_device + soft_connect.
3. Também mexe direto no sysfs durante o recovery (vale pra sessão atual
   se o recovery mantivesse a configuração — não vai manter, mas registra).
4. Gate ENABLE-ADB.OK/.FAIL no pendrive. Sem assert nem set_perm em /system.

Depois do deploy e primeiro boot, o cabo USB-A → USB-A entre central e PC
já enumera como ADB (precisa `adb kill-server && adb start-server` no PC).

Reversível: para voltar ao modo Host, rodar o mesmo pacote mudando
"device" por "host" em USB1_MODE, ou apagar o arquivo `/data/property/persist.sys.usb1_mode`.
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
OUT_DIR = HERE / "output-enable-adb"

sys.path.insert(0, str(OTA_BUILDER_SRC))
import main as upstream

BUSYBOX_SRC = HERE / "bin" / "busybox"
ROM_TYPE = "0040"

# Valor da propriedade — "device" ativa ADB sobre USB. Alternativa seria "host"
# para voltar ao modo original.
USB1_MODE = "device"


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
    LOG = f"{USB}/enable-adb-{rom_type}.log"
    OKF = f"{USB}/ENABLE-ADB.OK"
    FAILF = f"{USB}/ENABLE-ADB.FAIL"
    PROP_FILE = "/data/property/persist.sys.usb1_mode"

    def sh(cmd: str) -> str:
        esc = cmd.replace("\\", "\\\\").replace('"', '\\"')
        return f'run_program("{BB}", "sh", "-c", "{esc}");'

    # Nada aqui pode abortar o updater-script: sem assert() nem abort(), e
    # set_perm só em /tmp. Se o recovery falha no meio, o comando estagiado em
    # /cache/recovery/command fica lá e a central entra em recovery loop
    # (MAPA §17.17). Por isso a etapa crítica grava .OK/.FAIL no pendrive em
    # vez de abortar.
    out = [
        "show_progress(1.000000, 0);",
        "set_progress(0.000000);",
        'package_extract_file("busybox", "/tmp/busybox");',
        'set_perm(0, 0, 0755, "/tmp/busybox");',
        sh(f"{BB} echo === ENABLE-ADB START $({BB} date) rom_type={rom_type} === > {LOG} 2>&1"),
        sh(f"{BB} rm -f {OKF} {FAILF} 2>>{LOG}"),
        sh(f"{BB} mount >> {LOG} 2>&1; {BB} echo mount-done >> {LOG}"),
        # Garante /data/property/ existe. UDA já é montada pelo recovery (§13.3).
        sh(f"{BB} mkdir -p /data/property 2>>{LOG}; {BB} echo mkdir-prop-exit=$? >> {LOG}"),
        # Grava a propriedade persistente. 0:0 = root:root durante recovery; no
        # boot normal o init corrige para system:system ao reler.
        sh(f"{BB} echo -n '{USB1_MODE}' > {PROP_FILE} 2>>{LOG}; {BB} echo write-prop-exit=$? >> {LOG}"),
        sh(f"{BB} chmod 0600 {PROP_FILE} 2>>{LOG}; {BB} echo chmod-prop-exit=$? >> {LOG}"),
        sh(f"{BB} ls -la {PROP_FILE} >> {LOG} 2>&1"),
        sh(f"{BB} cat {PROP_FILE} >> {LOG} 2>&1; {BB} echo >> {LOG}"),
        # Tenta sysfs direto (não persiste, mas registra no log se funciona).
        sh(f"{BB} echo 0 > /sys/devices/platform/tegra-otg/enable_host 2>>{LOG}; {BB} echo sysfs-enable_host-exit=$? >> {LOG}"),
        sh(f"{BB} echo 1 > /sys/devices/platform/tegra-otg/enable_device 2>>{LOG}; {BB} echo sysfs-enable_device-exit=$? >> {LOG}"),
        sh(f"{BB} echo connect > /sys/devices/platform/tegra-udc.0/udc/tegra-udc.0/soft_connect 2>>{LOG}; {BB} echo sysfs-soft_connect-exit=$? >> {LOG}"),
        # Gate: .OK só se o arquivo da prop está presente e tem o valor certo.
        # No boot subsequente, usbdetectd vai ler a prop e configurar o USB.
        sh(
            f"if {BB} test -e {PROP_FILE} && {BB} grep -q '^{USB1_MODE}$' {PROP_FILE}; "
            f"then {BB} echo enabled > {OKF}; {BB} echo enable-adb-verified-OK >> {LOG}; "
            f"else {BB} echo missing-or-wrong-value > {FAILF}; {BB} echo enable-adb-verify-FAILED >> {LOG}; fi"
        ),
        sh(f"{BB} sync"),
        sh(f"{BB} echo === ENABLE-ADB END $({BB} date) === >> {LOG}; {BB} sync"),
        # Quebra o loop do daupdater: sem renomear o gatilho e apagar o
        # .copy_complete, ele reaplica o pacote a cada boot (MAPA §17.17).
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
    logger = logging.getLogger("civichmi-ota-enable-adb")

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
    logger.info("enable-adb mdt: %s", signed)
    print(f"OK: {build_dir}")


if __name__ == "__main__":
    main()
