# 🇺🇸 English Documentation

Practical documentation to use/adapt the project. For those who just want to deploy on their own HU.

## Index

| Doc | Description |
|---|---|
| [`00-overview.md`](00-overview.md) | What the project does and why |
| [`03-finding-your-firmware.md`](03-finding-your-firmware.md) | How to adapt for other firmware |
| [`07-rollback.md`](07-rollback.md) | Reverting everything |
| [`08-backups.md`](08-backups.md) | Complete backup catalog |

**Portuguese-only (translation welcome!):**

| Doc | Description |
|---|---|
| [`../pt-BR/01-arquitetura-ataque.md`](../pt-BR/01-arquitetura-ataque.md) | How the EvilValet attack works |
| [`../pt-BR/02-pre-requisitos.md`](../pt-BR/02-pre-requisitos.md) | Hardware, software, keystore |
| [`../pt-BR/04-build-do-pacote.md`](../pt-BR/04-build-do-pacote.md) | Compile the OTA package step by step |
| [`../pt-BR/05-deploy-no-carro.md`](../pt-BR/05-deploy-no-carro.md) | Protocol in the car |
| [`../pt-BR/06-troubleshooting.md`](../pt-BR/06-troubleshooting.md) | Decision tree when something fails |

## Recommended path

### If this is your first contact with the project

1. [`00-overview.md`](00-overview.md) — context
2. [`../../DISCLAIMER.md`](../../DISCLAIMER.md) — read the risks
3. If firmware `1.F187.16` BR: follow [`../../QUICKSTART.md`](../../QUICKSTART.md) (Portuguese — commands are universal)
4. If other firmware: [`03-finding-your-firmware.md`](03-finding-your-firmware.md)

### If you already deployed and something went wrong

1. [`../pt-BR/06-troubleshooting.md`](../pt-BR/06-troubleshooting.md) — complete decision tree (Portuguese)
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

The following Portuguese docs still need English translation:

- `../pt-BR/01-arquitetura-ataque.md` → `docs/en/01-attack-architecture.md`
- `../pt-BR/02-pre-requisitos.md` → `docs/en/02-prerequisites.md`
- `../pt-BR/04-build-do-pacote.md` → `docs/en/04-building-the-package.md`
- `../pt-BR/05-deploy-no-carro.md` → `docs/en/05-deploying-in-car.md`
- `../pt-BR/06-troubleshooting.md` → `docs/en/06-troubleshooting.md`
- All of `../fase7-deploy-2026-10-16/`
- `../MAPA.md` → `docs/en/MAP.md`

Fork + PR welcome. See [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md).

## Credits

See main [README.en.md](../../README.en.md).

## License

Code: MIT. Documentation: CC BY 4.0.

Honda/Mitsubishi proprietary software referenced is owned by respective holders. This repo does
NOT distribute proprietary firmware — you must dump from your own HU.
