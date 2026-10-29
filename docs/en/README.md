# 🇺🇸 English Documentation

Practical documentation to use/adapt the project. For those who just want to deploy on their own HU.

## Index

| Doc | Description |
|---|---|
| [`00-overview.md`](00-overview.md) | What the project does and why |
| [`01-attack-architecture.md`](01-attack-architecture.md) | How the EvilValet attack works |
| [`02-prerequisites.md`](02-prerequisites.md) | Hardware, software, keystore |
| [`03-finding-your-firmware.md`](03-finding-your-firmware.md) | How to adapt for other firmware |
| [`04-building-the-package.md`](04-building-the-package.md) | Compile the OTA package step by step |
| [`05-deploying-in-car.md`](05-deploying-in-car.md) | Protocol in the car |
| [`06-troubleshooting.md`](06-troubleshooting.md) | Decision tree when something fails |
| [`07-rollback.md`](07-rollback.md) | Reverting everything |
| [`08-backups.md`](08-backups.md) | Complete backup catalog |
| [`09-fase10-remove-warning.md`](09-fase10-remove-warning.md) | 🎯 Phase 10 — remove the warning for good via DaLauncher patch |

## Recommended path

### If this is your first contact with the project

1. [`00-overview.md`](00-overview.md) — context
2. [`../../DISCLAIMER.md`](../../DISCLAIMER.md) — read the risks
3. If firmware `1.F187.16` BR: follow [`../../QUICKSTART.md`](../../QUICKSTART.md) (Portuguese — commands are universal) or walk through [`04-building-the-package.md`](04-building-the-package.md) + [`05-deploying-in-car.md`](05-deploying-in-car.md)
4. If other firmware: [`03-finding-your-firmware.md`](03-finding-your-firmware.md)

### If you already deployed and something went wrong

1. [`06-troubleshooting.md`](06-troubleshooting.md) — complete decision tree
2. If nothing helps: [`07-rollback.md`](07-rollback.md) — revert everything
3. Open an [issue](../../.github/ISSUE_TEMPLATE/) with APK log + deploy logs

### If you're a researcher / want to understand deeply

1. [`00-overview.md`](00-overview.md) — summary
2. [`../MAPA.md`](../MAPA.md) — navigable atlas of the HU (partitions, APKs, binaries) — mostly Portuguese labels but structure is clear
3. [`../fase7-deploy-2026-10-16/`](../fase7-deploy-2026-10-16/) — 7 technical docs with discovery narrative, technical findings, deep dives (Portuguese)

## Tested firmware

- **Honda Civic 2017 EXL Brazil**, DA version `1.F187.16`, rom_type `0040`. ✅ Working.

## Likely compatible (not tested)

- Civic G10 2016-2021 US/EU/AU (same framework)
- CR-V 2016-2021 (some firmware)
- Accord 2016+ with Display Audio
- Civic Avancier, Civic URV

For other firmware, see [`03-finding-your-firmware.md`](03-finding-your-firmware.md) — the procedure to find your `custom_rom.type` via a diagnostic OTA package.

## Report your firmware

If you have a different Honda G10 variant, please report via the [issue template](../../.github/ISSUE_TEMPLATE/nova-safra.md). Both Portuguese and English accepted.

Even if you don't deploy, just the technical fields help build the compatibility matrix.

## Translation help wanted

The main user-facing docs (00-08) are translated. Still Portuguese-only:

- All of `../fase7-deploy-2026-10-16/` — technical journey, APK architecture, deploy recipe (narrative)
- `../MAPA.md` → `docs/en/MAP.md` — navigable atlas of the head unit
- `../whitelist-mitsubishi-2026-10-19.md` — Mitsubishi whitelist analysis
- `../raio-x/` — platform scan (364 AIDLs, 445 broadcasts, trust map)

Fork + PR welcome. See [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md).

## Credits

See main [README.en.md](../../README.en.md).

## License

Code: MIT. Documentation: CC BY 4.0.

Honda/Mitsubishi proprietary software referenced is owned by respective holders. This repo does
NOT distribute proprietary firmware — you must dump from your own HU.
