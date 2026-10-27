#!/usr/bin/env python3
"""Processa o scan.tar.gz do deep-scan e gera um RELATORIO.md.

Nao gera o docs/MAPA.md completo (que tem secoes humanas: hall of fame,
caminhos descartados, timeline). Gera um RELATORIO.md com as secoes
mecanicas (partitions, mounts, APKs instalados, bins disponiveis,
build.prop) que a IA pode usar pra sincronizar o MAPA.md manualmente.

Uso:
    # Extrai o scan.tar.gz mais recente do pendrive
    python3 tooling/scripts/gen-mapa.py

    # Ou passa o caminho especifico
    python3 tooling/scripts/gen-mapa.py /path/to/scan.tar.gz
    python3 tooling/scripts/gen-mapa.py /path/to/deep-scan-dir/

Saida:
    ~/backup-honda-civic-g10/deep-scan-YYYY-MM-DD/RELATORIO.md
    + extracao do tarball em ~/backup-honda-civic-g10/deep-scan-YYYY-MM-DD/
"""
from __future__ import annotations

import sys
import tarfile
from datetime import date
from pathlib import Path


HOME = Path.home()
BACKUP_ROOT = HOME / "backup-honda-civic-g10"
DEFAULT_PENDRIVE = Path("/run/media/khalleb/HONDA_OTA/deep-scan-0040/scan.tar.gz")


def resolve_source(argv: list[str]) -> Path:
    if len(argv) > 1:
        return Path(argv[1])
    if DEFAULT_PENDRIVE.exists():
        return DEFAULT_PENDRIVE
    raise SystemExit(
        f"ERRO: scan nao encontrado em {DEFAULT_PENDRIVE}. "
        "Passe o caminho como argumento."
    )


def extract(source: Path) -> Path:
    out_dir = BACKUP_ROOT / f"deep-scan-{date.today().isoformat()}"
    if source.is_dir():
        print(f"OK: usando dir ja extraido {source}")
        return source
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"OK: {out_dir} ja contem dados extraidos, pulando extracao")
        return out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Extraindo {source} em {out_dir}")
    with tarfile.open(source, "r:gz") as tf:
        # O tar vem do pendrive (gerado no recovery do carro): filter="data"
        # barra path traversal e symlink/device que escapariam de out_dir.
        tf.extractall(out_dir, filter="data")
    return out_dir


def read_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"<erro lendo {path.name}: {exc}>"


def section(title: str, body: str) -> str:
    return f"## {title}\n\n{body}\n\n"


def report_hardware(scan: Path) -> str:
    cpuinfo = read_text(scan / "proc" / "cpuinfo.txt")
    meminfo = read_text(scan / "proc" / "meminfo.txt")
    version = read_text(scan / "proc" / "version.txt")
    hw = next((l for l in cpuinfo.splitlines() if l.startswith("Hardware")), "?")
    mem = next((l for l in meminfo.splitlines() if l.startswith("MemTotal")), "?")
    cores = sum(1 for l in cpuinfo.splitlines() if l.startswith("processor"))
    return (
        f"- Hardware: `{hw}`\n"
        f"- Cores: {cores}\n"
        f"- {mem.strip()}\n"
        f"- Kernel: `{version.strip()}`\n"
    )


def report_build_prop(scan: Path) -> str:
    sys_prop = read_text(scan / "parts" / "APP" / "configs" / "build.prop")
    ven_prop = read_text(scan / "parts" / "CAP" / "configs" / "build.prop")
    keys = (
        "ro.build.id", "ro.build.version.release", "ro.build.version.sdk",
        "ro.product.model", "ro.product.device", "ro.product.name",
        "ro.product.manufacturer", "ro.build.fingerprint",
        "custom_rom.type", "custom_rom.id",
    )
    picked = {}
    for line in (sys_prop + "\n" + ven_prop).splitlines():
        for key in keys:
            if line.startswith(key + "="):
                picked[key] = line.split("=", 1)[1]
    lines = [f"- `{k}` = `{picked.get(k, '?')}`" for k in keys]
    return "\n".join(lines) + "\n"


def report_partitions(scan: Path) -> str:
    partitions = read_text(scan / "proc" / "partitions.txt")
    by_name = read_text(scan / "dev" / "by-name.txt")
    mounts = read_text(scan / "proc" / "mounts.txt")
    out = ["### /proc/partitions\n", "```", partitions.strip(), "```\n"]
    out.extend(["### by-name (symlinks)\n", "```", by_name.strip(), "```\n"])
    out.extend(["### /proc/mounts (recovery runtime)\n", "```", mounts.strip(), "```\n"])
    return "\n".join(out)


def report_apks(scan: Path) -> str:
    def pick(part: str) -> list[str]:
        paths = (scan / "parts" / part / "apks-paths.txt").read_text(errors="replace").splitlines()
        return sorted({p.rsplit("/", 1)[-1] for p in paths if p.strip()})

    app = pick("APP")
    cap = pick("CAP")
    sda = pick("SDA") if (scan / "parts" / "SDA" / "apks-paths.txt").exists() else []
    sda2 = pick("SDA2") if (scan / "parts" / "SDA2" / "apks-paths.txt").exists() else []

    out = [f"### /system/app ({len(app)} APKs)\n"]
    out.extend(f"- {a}" for a in app)
    out.append(f"\n### /system/vendor/app ({len(cap)} APKs)\n")
    out.extend(f"- {a}" for a in cap)
    out.append(f"\n### /mnt/data1 (SDA, {len(sda)} APKs)\n")
    out.extend(f"- {a}" for a in sda)
    out.append(f"\n### /mnt/data2 (SDA2, {len(sda2)} APKs)\n")
    out.extend(f"- {a}" for a in sda2)
    return "\n".join(out) + "\n"


def report_packages(scan: Path) -> str:
    pkgs_list = read_text(scan / "parts" / "UDA" / "configs" / "packages.list")
    lines = pkgs_list.strip().splitlines()
    out = [f"### packages.list ({len(lines)} apps instalados em runtime)\n"]
    out.append("| Package | UID | Data dir |")
    out.append("|---|---|---|")
    for line in sorted(lines):
        parts = line.split()
        if len(parts) >= 4:
            out.append(f"| `{parts[0]}` | {parts[1]} | `{parts[3]}` |")
    return "\n".join(out) + "\n"


def report_bins(scan: Path) -> str:
    bin_ls = read_text(scan / "parts" / "APP" / "configs" / "bin-ls.txt")
    xbin_ls = read_text(scan / "parts" / "APP" / "configs" / "xbin-ls.txt")
    out = ["### /system/xbin\n", "```", xbin_ls.strip(), "```\n"]
    key_bins = (
        "su", "logcat", "input", "am", "pm", "dumpsys",
        "getprop", "service", "settings", "screencap",
        "monkey", "sqlite3", "dexdump", "app_process",
    )
    found = []
    for line in bin_ls.splitlines():
        parts = line.split()
        if parts and parts[-1] in key_bins:
            found.append(line.strip())
    out.extend(["### /system/bin (binarios chave)\n", "```", "\n".join(found), "```\n"])
    return "\n".join(out)


def report_mounts_fstab(scan: Path) -> str:
    recovery_fstab = read_text(scan / "configs" / "recovery-fstab.txt")
    vold = read_text(scan / "parts" / "APP" / "configs" / "vold.fstab")
    return (
        "### recovery-fstab\n```\n"
        + recovery_fstab.strip()
        + "\n```\n\n### vold.fstab (runtime)\n```\n"
        + vold.strip()
        + "\n```\n"
    )


def report_autook(scan: Path) -> str:
    autook_trace = read_text(scan / "parts" / "UDA" / "configs" / "autook-trace.txt")
    pkgs_xml = read_text(scan / "parts" / "UDA" / "configs" / "packages.xml")
    autook_entry = next(
        (l for l in pkgs_xml.splitlines() if "khalleb" in l), "nao encontrado"
    )
    return (
        f"### Nosso APK (AutoOk)\n"
        f"- Trace: `{autook_trace.strip()}`\n"
        f"- Entrada no packages.xml:\n```\n{autook_entry}\n```\n"
    )


def main() -> None:
    source = resolve_source(sys.argv)
    scan_dir = extract(source)
    out_md = scan_dir / "RELATORIO.md"

    body = f"# Relatorio do deep-scan — {date.today().isoformat()}\n\n"
    body += f"Origem: `{source}`\n"
    body += f"Extraido em: `{scan_dir}`\n\n"

    failed = False
    try:
        body += section("Hardware", report_hardware(scan_dir))
        body += section("Build.prop", report_build_prop(scan_dir))
        body += section("Particoes", report_partitions(scan_dir))
        body += section("Mount config", report_mounts_fstab(scan_dir))
        body += section("APKs por particao", report_apks(scan_dir))
        body += section("Packages instalados", report_packages(scan_dir))
        body += section("Binarios /system/bin + xbin", report_bins(scan_dir))
        body += section("Nosso APK", report_autook(scan_dir))
    except Exception as exc:
        body += f"\n**ERRO durante geracao:** {exc}\n"
        failed = True

    out_md.write_text(body, encoding="utf-8")
    # Grava o relatorio parcial (ate util pra ver ate onde foi), mas sai !=0 pra
    # nao mascarar a falha quando rodado em pipeline ou com &&.
    if failed:
        raise SystemExit(f"geracao incompleta; relatorio parcial em {out_md}")
    print(f"OK: {out_md}")
    print()
    print("Proximos passos (IA):")
    print(f"  1. Ler {out_md}")
    print("  2. Comparar com docs/MAPA.md atual")
    print("  3. Atualizar MAPA secoes mecanicas (partitions, APKs, packages)")
    print("  4. Preservar secoes humanas (hall of fame, descartados, timeline)")


if __name__ == "__main__":
    main()
