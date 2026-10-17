# 00 — Overview

## The problem

Every time you turn on your Honda Civic G10 (Brazilian or international firmware), the head unit shows this screen:

> **"Warning — The driver is responsible for safe driving..."**

You have to tap OK before using CarPlay, radio, or anything else. Small pain. Daily. Multiplied by years of ownership = considerable annoyance.

Honda has **never** released a configuration to disable this screen — they treat it as legal liability.

## Existing options before this project

| Option | Cost | Problems |
|---|---|---|
| Honda Hack (`cn.autohack.hondahack`) | USD 25 | Closed source, obfuscated with Tencent StubShell, perpetual payment, author may disappear |
| Modify the launcher | — | High brick risk, requires existing root, very complex |
| Nothing | — | Tap OK every single day |

## What we did

Deployed our own APK to `/system/app/AutoOk.apk` + `su` setuid in `/system/xbin/`:

1. **Installation:** via OTA package (fake firmware update) signed with public AOSP testkey — using the **EvilValet** vulnerability discovered and documented by librick / Eric McDonald.
2. **Operation:** our APK monitors logcat; when the warning Activity starts, it fires `su -c "input tap 400 350"` — simulates an invisible tap on the OK button.
3. **Persistence:** APK runs as a Service that stays alive forever; every time the car turns on, it intercepts the warning.

## Result

- Warning appears and disappears on its own in ~5 seconds
- Zero manual interaction required
- CarPlay, Bluetooth, audio, navigation keep working
- Rollback available anytime via removal OTA package

## Who this is for

- **You:** owner of Brazilian Civic G10 (`1.F187.16`, EXL or similar). Tested and working.
- **Possibly others:** G10 2016-2021 US/EU/AU, Civic Avancier/URV, CR-V 2016-2021, Accord 2016+. **Not tested** — you'll need to adapt coords and rom_type. See [`03-finding-your-firmware.md`](03-finding-your-firmware.md).

## High-level flow

```
FAT32 pendrive with SwUpdate.mdt signed by testkey
      │
      ▼ (front USB-A port + AUDIO 5s + confirm reboot)
Head unit does cold boot
      │
      ▼
SystemUpdate.apk accepts the update (signature verifies)
      │
      ▼
daupdater validates rom_type (0040 for our firmware) + reboots into recovery
      │
      ▼
Recovery validates testkey signature + applies updater-script
      │
      ▼ (via embedded busybox + edify mount)
Installs /system/app/AutoOk.apk + /system/xbin/su
      │
      ▼
Normal boot. AutoOkService starts on BOOT_COMPLETED.
      │
      ▼ (every time the warning appears)
Logcat watcher detects Activity → su -c input tap 400 350 → warning disappears
```

Detailed diagram: [`../images/arquitetura.svg`](../images/arquitetura.svg).

## Why this approach is safer than alternatives

| Approach | Brick risk | Reversible? | Detectable by Honda? |
|---|---|---|---|
| **Ours (EvilValet + APK in /system/app)** | Low — we only add 2 new files, nothing modified | Yes — rollback OTA removes everything | No — APK sits in /system/app like any system app |
| Modify `DaLauncher.apk` | High — launcher brick = black screen | Yes but requires OTA | No |
| Xposed Framework | High — patches `/system/bin/app_process`, bootloop on failure | Yes but delicate | Possibly (fingerprint changes) |
| Honda Hack (paid) | Low | Yes | Possible (checksum) |

Our attack is **surgical**: we don't touch anything already in `/system`. If something goes wrong, remove the 2 new files and the HU returns to factory state.

## Original technical documentation

The final deploy session is in [`docs/fase7-deploy-2026-10-16/`](../fase7-deploy-2026-10-16/) — 7 docs with full narrative, detailed technical discoveries, build recipe, APK architecture, maintenance guide, and dump catalog. **Currently Portuguese** — translation welcome.

The docs in this folder (`docs/en/`) are the **accessible version** for people who want to use/adapt without reading the whole technical journey.

## Next steps

- To deploy on firmware `1.F187.16` BR: → [`QUICKSTART.md`](../../QUICKSTART.md) (currently Portuguese — commands are universal)
- For other firmware: → [`03-finding-your-firmware.md`](03-finding-your-firmware.md)
- For risk context: → [`../../DISCLAIMER.md`](../../DISCLAIMER.md)
