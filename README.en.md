<div align="center">

<img src="docs/images/logo.svg" alt="Honda Civic G10 Skip Disclaimer" width="200"/>

# Honda Civic G10 — Skip Disclaimer

**Automatically dismiss the "Warning" disclaimer screen that appears every time you turn on your Honda Civic G10**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Done](https://img.shields.io/badge/status-done-brightgreen)]()
[![Platform](https://img.shields.io/badge/platform-Android_4.2.2_%7C_Tegra_3-blue)]()
[![Build](https://img.shields.io/badge/tested_firmware-1.F187.16_BR-orange)]()

[🇧🇷 Português](README.md) · 🇺🇸 **English**

</div>

---

## 🎯 What this project does

Every time you turn the car on, the head unit shows a disclaimer screen:

> **"The driver is responsible for safe driving..."**

And you have to tap OK. Every. Single. Time. Before CarPlay starts.

This project **automatically dismisses that warning** — you turn on the car, warning appears, and ~2 seconds later it disappears on its own. No tapping.

## ✨ How it works

1. An OTA package (fake firmware update, signed with the AOSP testkey via the **EvilValet** vulnerability discovered by [juniperspring.org](https://juniperspring.org/posts/honda-evil-valet/)) installs:
   - **`AutoOk.apk`** in `/system/app/` — monitors logcat, detects when the warning screen appears.
   - **`su`** setuid binary in `/system/xbin/` — permanent root.
2. On car boot, the APK receives `BOOT_COMPLETED` and starts a logcat watcher.
3. When the warning screen appears, the APK waits 2s and fires `su -c "input tap 400 350"` — simulates a tap on the OK button.
4. Warning disappears. You barely noticed.

## 🚗 Tested on

**Only confirmed firmware:**

| Car | DA Version | Market | Rom type | Status |
|---|---|---|---|---|
| Honda Civic 2017 EXL | `1.F187.16` | 🇧🇷 Brazil | `0040` | ✅ Working |

**Likely compatible** (same Mitsubishi Andromeda framework) — not tested:

- Civic G10 2016–2021 (US, EU, AU, other BR variants)
- Civic Avancier, Civic URV
- CR-V 2016–2021 (some firmware)
- Accord 2016+ with Display Audio

**If you have a different firmware**, [help the community](#-contributing) — just 2 pieces of info to confirm compatibility: your `custom_rom.type` and screen resolution.

## 🚀 Quick Start

If you own a 2017 Civic EXL BR and want to deploy today:

👉 **[Follow the QUICKSTART.md](QUICKSTART.md)** (currently Portuguese only — translation welcome!) — step-by-step in 10 minutes (laptop) + 10 minutes (car).

For different firmware, before deploying you need to:
1. Find your `custom_rom.type` → [`docs/pt-BR/03-descobrindo-sua-safra.md`](docs/pt-BR/03-descobrindo-sua-safra.md) (Portuguese, translation welcome)
2. Confirm OK button coordinates (may be (400, 350) or different)
3. Rebuild the package with correct values

## ⚠️ Important warnings

- **Can cause permanent brick** of the head unit if done wrong. Replacement is R$ 1,000-2,000 (~USD 200-400).
- **The HU display is also the backup camera** — brick = no backup camera until replacement.
- **Official Honda OTA updates may revert** the modification. You'll need to redeploy.
- **CarPlay, Bluetooth, audio, navigation remain functional** — our modification is surgical.
- **Zero backdoor for Honda to detect.** APK sits in /system/app like any system app.

**Read the full [DISCLAIMER.md](DISCLAIMER.md) before executing anything.**

## 📚 Full documentation

- 🇧🇷 Portuguese: [`docs/pt-BR/`](docs/pt-BR/) — complete
- 🇺🇸 English: [`docs/en/`](docs/en/) — summary (translations welcome!)

**Deep technical dive** (for researchers):

- [`docs/fase7-deploy-2026-10-16/`](docs/fase7-deploy-2026-10-16/) — 7 docs covering journey, discoveries, recipes, dumps, APK architecture, maintenance (currently Portuguese, but technical identifiers are universal)
- [`docs/images/flow-evilvalet.md`](docs/images/flow-evilvalet.md) — Mermaid diagrams of the deploy flow

## 🙏 Credits

This project wouldn't exist without:

- **librick / Eric McDonald** ([juniperspring.org](https://juniperspring.org/), [ic1101](https://github.com/librick/ic1101)) — discovery and technical documentation of the EvilValet vulnerability, `ota-builder`, `apk-rebuilder`.
- **@codeage** ([root-honda](https://github.com/codeage/root-honda)) — root tool with static ARM `su`, SuperSU, Mitsubishi whitelist analysis.
- **@jersacct** ([2016PilotOneClick](https://github.com/jersacct/2016PilotOneClick)) — mother project for Honda rooting based on DirtyCOW.

**Our contribution is the adaptation to the Brazilian firmware `1.F187.16`** (rom type `0040`, `AUDIO 5s` combo for cold boot, discovery that BR firmware recovery doesn't ship `/sbin/sh` and needs embedded busybox, persistent APK that re-arms after each tap). See [`docs/fase7-deploy-2026-10-16/02-descobertas-tecnicas.md § 0`](docs/fase7-deploy-2026-10-16/02-descobertas-tecnicas.md#0-contribuições-novas-deste-projeto) for details.

## 🤝 Contributing

We welcome:

1. **Have another Honda G10 firmware?** Open an issue using the [`nova-safra.md`](.github/ISSUE_TEMPLATE/nova-safra.md) template with: VIN prefix, DA version, `custom_rom.type` (how to find it is in the docs), screen resolution. We'll build a compatibility matrix.
2. **Found a bug or improvement?** Issues + PRs welcome.
3. **Want to translate to another language?** Fork + PR with new `docs/<lang>/` folder. Priority: full English translation of `docs/pt-BR/`.

## 📄 License

Code: [MIT](LICENSE). Documentation: CC BY 4.0.

Honda/Mitsubishi proprietary software referenced is owned by respective holders. **This repo does not distribute proprietary firmware** — you must dump from your own HU (see `docs/pt-BR/03-descobrindo-sua-safra.md`).

---

<div align="center">

**Made for the Honda Civic G10 community.**

</div>
