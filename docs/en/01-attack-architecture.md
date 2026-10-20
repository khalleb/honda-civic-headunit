# 01 — Attack architecture

How we installed new code in `/system/` **without ADB, without an unlocked bootloader, and without Honda's signature** — using just a flash drive and the AUDIO button.

This doc explains **why it works**. For the build recipe, see [`04-building-the-package.md`](04-building-the-package.md). For the in-car protocol, see [`05-deploying-in-car.md`](05-deploying-in-car.md).

---

## The weak point: EvilValet

The head unit has a firmware update flow that works like this:

1. Owner plugs a FAT32 flash drive with a `/<rom_type>/SwUpdate.mdt` folder (the OTA package).
2. On **cold boot**, a service called `daupdater` scans the flash drive.
3. If it finds `SwUpdate.mdt` that:
   - sits in a folder whose name matches the head unit's `custom_rom.type` (e.g. `0040`), **and**
   - is signed with a key the AOSP recovery accepts,
4. ...the recovery applies the package as if it were a legitimate Honda update.

**The bug:** the recovery on the Mitsubishi Andromeda firmware accepts the **public AOSP testkey** — the same key Google uses in Android test builds. That key lives in AOSP source and anyone can sign a `SwUpdate.mdt` with it.

This vulnerability was discovered and documented by **Eric McDonald (librick)** at [juniperspring.org](https://juniperspring.org/posts/honda-evil-valet/) and named **EvilValet** — "any valet with a flash drive can plant firmware in your car".

### Why the name EvilValet

The original hypothetical: you hand the car keys to the parking valet. While you're eating, they plug a flash drive and apply a package that plants spyware in `/system/`. Zero visible signal.

For us, this is a feature, not a bug. It lets the owner apply modifications **with their own consent**, without needing an unlocked bootloader or expensive tools.

---

## Full pipeline

![Deploy pipeline](../images/arquitetura.svg)

In text:

```
┌─────────────────────────────────────────────────────────────────────┐
│ ON THE PC (prep)                                                    │
│                                                                      │
│  gradlew assembleRelease      →  AutoOk.apk (our APK bytecode)      │
│  apksigner --ks debug.keystore →  AutoOk.apk signed w/ debug key    │
│  python3 build.py             →  SwUpdate.mdt signed w/ testkey     │
│  prepare-pendrive-install.sh  →  FAT32 flash drive with /0040/*.mdt │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (flash drive in front USB-A port)
┌─────────────────────────────────────────────────────────────────────┐
│ IN THE CAR (deploy)                                                 │
│                                                                      │
│  Owner holds AUDIO for 5s                                           │
│   └─ Head unit shows "Reboot?" dialog                               │
│      └─ Owner confirms → SHUTDOWN + COLD BOOT                       │
│         │                                                            │
│         ▼                                                            │
│      Cold boot → daupdater scans /mnt/usbdrive1/                    │
│         └─ Finds /0040/SwUpdate.mdt                                 │
│            └─ Validates signature against testkey ✓                 │
│               └─ Transfers to /cache + reboots into recovery        │
│                  └─ AOSP recovery applies updater-script            │
│                     ├─ mounts /system via edify                     │
│                     ├─ package_extract: AutoOk.apk, su, busybox     │
│                     ├─ set_perm: AutoOk.apk 0644, su 06755          │
│                     └─ umount + reboot                              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (head unit returns to normal)
┌─────────────────────────────────────────────────────────────────────┐
│ IN OPERATION (every car ignition)                                   │
│                                                                      │
│  BOOT_COMPLETED → BootReceiver → AutoOkService                      │
│   └─ LogcatWatcher thread reads `logcat ActivityManager:I *:S` via  │
│      su                                                              │
│      └─ Looks for the string "...dalauncher/.OpeningDivideActivity" │
│         └─ Once found:                                               │
│            ├─ sleep 1s (let UI render)                              │
│            ├─ su -c "input tap 400 350"  (OK button coords)         │
│            └─ sleep 10s + reset flag → ready for next appearance    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## The 4 pieces

### Piece 1 — OTA package (`SwUpdate.mdt`)

A zip signed with the AOSP testkey. Contents:
- `META-INF/com/google/android/update-binary` — AOSP edify binary
- `META-INF/com/google/android/updater-script` — commands (mount, package_extract_file, set_perm, etc.)
- `system/app/AutoOk.apk` — our APK
- `system/xbin/su` — setuid root binary
- `busybox` — static ARM toolkit (needed because the BR recovery doesn't ship `/sbin/sh`)
- `META-INF/MANIFEST.MF`, `CERT.SF`, `CERT.RSA` — signature

Built by `tooling/ota-build/build.py` (our wrapper on top of ic1101's `ota-builder`).

### Piece 2 — Trigger flash drive

FAT32 MSDOS. Two files:
- `SwUpdate2.txt` — 28-byte file containing `Ver:1\n` (trigger file)
- `<rom_type>/SwUpdate.mdt` — the package

The daupdater looks for exactly this structure. If the folder name doesn't match the `custom_rom.type`, the package is silently ignored.

### Piece 3 — `AutoOk.apk` + `su`

Installed under `/system/`:
- **`/system/app/AutoOk.apk`** (16 KB) — persistent service that monitors logcat
- **`/system/xbin/su`** (133 KB, mode `06755`) — plain setuid root (from root-honda)

After installation, on every cold boot:
1. Android comes up → `BOOT_COMPLETED` broadcast
2. Our `BootReceiver` catches it → starts `AutoOkService`
3. Service spawns `su` → `logcat` → observes Activity transitions

### Piece 4 — The simulated tap

When the APK detects the warning in logcat, it runs:
```
su -c "input tap 400 350"
```

`input` is a stock Android binary in `/system/bin/` that simulates touch events. `(400, 350)` is the center of the OK button on our firmware's 800×480 screen.

Visually: the warning screen appears → ~2 seconds later an invisible pointer "clicks" OK → warning disappears.

---

## Why this is safer than alternatives

| Approach | Brick risk | Reversible? | Detectable by Honda? |
|---|---|---|---|
| **Ours (EvilValet + APK in /system/app)** | Low — we only add 2 new files, nothing modified | Yes — rollback OTA removes everything | No — APK sits in /system/app like any system app |
| Modify `DaLauncher.apk` | High — launcher brick = black screen | Yes but requires OTA | No |
| Xposed Framework | High — patches `/system/bin/app_process`, bootloop on failure | Yes but delicate | Possibly (fingerprint changes) |
| Honda Hack (paid) | Low | Yes | Possible (checksum) |

Our attack is **surgical**: we don't touch anything already in `/system`. If something goes wrong, remove the 2 new files and the head unit returns to factory state.

---

## How it works in operation (persistence)

Once installed, the APK has to **survive every car usage cycle**. Here's how:

### Cold boot (key off → key on, full boot)

1. Kernel + init + Zygote + system services
2. Android fires `android.intent.action.BOOT_COMPLETED`
3. Our `BootReceiver` listens → `startService(AutoOkService)`
4. Service starts the LogcatWatcher thread
5. Logcat emits Activity transitions
6. Watcher sees the `OpeningDivideActivity` string → callback fires the tap

### Resume from suspend (turning the key when the car was already "sleeping")

**Caveat here:** `BOOT_COMPLETED` **only fires on real cold boot**. Resume from suspend doesn't fire. But the Service with `START_STICKY` stays alive between resumes.

So after the first cold boot of the day, the Service is already running and will intercept the warning on every subsequent ignition.

### Multiple warning appearances in the same session

The `OpeningDivideActivity` can come back if the owner enters diagnostic mode and exits, for example. The APK handles that with a rearm system:

- After firing the tap, the `handled = true` flag stays for 10s (avoids double-tap)
- After 10s, the flag resets to `false` → next appearance fires another tap
- The `logcat` process stays alive between taps (not recreated) — zero overhead

### Watchdog

An extra thread checks every 30s if the LogcatWatcher is still alive. If it died (crash, external kill), it recreates it. Resilient under adverse conditions.

**Important fix in v0.4.0:** after certain LP0 transitions (backup camera, door changes), the PowerManager was killing the `logcat` child process. The watcher thread would stay blocked in `readLine()` on a dead FD and the watchdog's `isAlive()` would return true (blocked thread is "alive"). Fix: a new `HmiServiceReceiver` listens for `com.mitsubishielectric.ada.appservice.powermanager.ACTION_HMI_SERVICE_START` (emitted by the PowerManager on `ExitLP0`) and force-restarts the watcher. See [`../MAPA.md` §11.6](../MAPA.md) and [`../whitelist-mitsubishi-2026-10-19.md` §6](../whitelist-mitsubishi-2026-10-19.md).

---

## Deep technical paths

- **OTA package recipe**: [`../fase7-deploy-2026-10-16/03-build-ota-receita.md`](../fase7-deploy-2026-10-16/03-build-ota-receita.md) (Portuguese)
- **APK architecture (code line by line)**: [`../fase7-deploy-2026-10-16/04-apk-autook-detalhes.md`](../fase7-deploy-2026-10-16/04-apk-autook-detalhes.md) (Portuguese)
- **Firmware-specific findings (Brazilian)**: [`../fase7-deploy-2026-10-16/02-descobertas-tecnicas.md`](../fase7-deploy-2026-10-16/02-descobertas-tecnicas.md) (Portuguese)
- **Filesystem map of the head unit**: [`../MAPA.md`](../MAPA.md)

## Technical credits

- **EvilValet** discovered and documented by [Eric McDonald (librick)](https://juniperspring.org/) — [juniperspring.org/posts/honda-evil-valet](https://juniperspring.org/posts/honda-evil-valet/)
- **ota-builder** (base of our `build.py`): [github.com/librick/ic1101](https://github.com/librick/ic1101)
- **su setuid** (our `/system/xbin/su`): [github.com/codeage/root-honda](https://github.com/codeage/root-honda)
- **static ARM busybox**: shipped with the HondaHack APK, extracted and redistributed

None of this would be possible without those three projects.
