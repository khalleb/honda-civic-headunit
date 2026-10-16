# 🇺🇸 English Documentation

> ⚠️ **Translation in progress.** Full documentation is currently in Portuguese
> at [`docs/pt-BR/`](../pt-BR/) and in [`docs/fase7-deploy-2026-10-16/`](../fase7-deploy-2026-10-16/).
> Translation PRs welcome! See [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Quick overview

This project automatically dismisses the "Driver Responsibility" disclaimer screen that appears on
every boot of Honda Civic G10 head units (Mitsubishi Andromeda, Android 4.2.2, Tegra 3). Works
by installing a custom APK + `su` setuid binary into `/system/` via the **EvilValet** vulnerability
(testkey AOSP accepted by HU recovery).

## Started here

- **Just want to deploy?** → [`QUICKSTART.md`](../../QUICKSTART.md) (Portuguese, but commands are universal)
- **Different firmware than ours?** → [`../pt-BR/03-descobrindo-sua-safra.md`](../pt-BR/03-descobrindo-sua-safra.md) (Portuguese — translate help wanted!)
- **How it works technically?** → [`../fase7-deploy-2026-10-16/`](../fase7-deploy-2026-10-16/) (Portuguese)
- **Need rollback?** → [`../pt-BR/07-rollback.md`](../pt-BR/07-rollback.md) (Portuguese)

## Tested firmware

- **Honda Civic 2017 EXL Brazil**, DA version `1.F187.16`, rom_type `0040`. ✅ Working.

## Likely compatible (not tested)

- Civic G10 2016-2021 US/EU/AU (same framework)
- CR-V 2016-2021 (some firmware)
- Accord 2016+ with Display Audio
- Civic Avancier, Civic URV

For other firmware, see [`../pt-BR/03-descobrindo-sua-safra.md`](../pt-BR/03-descobrindo-sua-safra.md) — the procedure to find your `custom_rom.type` via a diagnostic OTA package.

## Report your firmware

If you have a different Honda G10 variant, please report via the [issue template](../../.github/ISSUE_TEMPLATE/nova-safra.md). The template is bilingual (PT-BR + EN) — fill in English works.

Even if you don't deploy, just the technical fields help build the compatibility matrix.

## Credits

See main [README.en.md](../../README.en.md).

## License

Code: MIT. Documentation: CC BY 4.0.

Honda/Mitsubishi proprietary software referenced is owned by respective holders. This repo does
NOT distribute proprietary firmware — you must dump from your own HU.
