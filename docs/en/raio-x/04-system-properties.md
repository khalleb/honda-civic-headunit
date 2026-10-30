# Scan 4 — System Properties

**48 `ro.*`/`persist.*`/`sys.*`/`net.*` properties referenced in bytecode.** List of what the shipping build reads or writes via `SystemProperties.get()`/`.set()`.

## How it was collected

```bash
grep -rhE 'const-string .*"(sys\.|ro\.|persist\.|init\.|dev\.|net\.)' bulk-smali/*/ \
  | grep -oE '"(sys\.|ro\.|persist\.|init\.|dev\.|net\.)[^"]+"' \
  | sort -u
```

**Limits:** props whose name is concatenated via `StringBuilder` (e.g. `"sys.hmi_" + state`) escape. Looking at the output, there's no evidence of any such case in this ROM — every setter/getter uses a direct literal.

## By prefix

### `sys.*` (8) — volatile car state 🎯

| Prop | Inferred meaning | Who uses it |
|---|---|---|
| **`sys.hmi_service_started`** | Flag the PowerManager sets when the HMI services are alive | mostly `PowerManagerApService` |
| **`sys.hmi_service_start_cause`** | Textual cause of the last start: `ColdBoot`, `ExitLP0`, `AccOnRestart` | same |
| **`sys.hmi_service_keyoff`** | Key-off-in-progress flag | same |
| **`sys.hmi_reboot_reservation`** | Reboot reservation (reboot pending after key-off) | same |
| `sys.lowbat_stat` | Low-battery status | diag/power |
| `sys.settings_global_version` | SettingsProvider.Global version | AOSP |
| `sys.settings_secure_version` | SettingsProvider.Secure version | AOSP |
| `sys.settings_system_version` | SettingsProvider.System version | AOSP |

**For AutoOk:** `sys.hmi_service_started` + `sys.hmi_service_start_cause` are already used indirectly by our `HmiServiceReceiver` (via broadcast). Reading them directly with `SystemProperties.get()` would be redundant — the broadcast arrives with the same data.

### `persist.*` (13) — persisted across reboots

Props that survive a reboot (written to `/data/property/persist.*`):

| Prop | What it does |
|---|---|
| **`persist.sys.keyoff_reboot`** 🎯 | **0 = no reboot on key-off; 1 = reboot**. Worth testing — flipping this may force cold boot when turning the car off, useful to avoid the "warning persists" state |
| `persist.sys.hdcp_checking` | HDCP (HDMI content protection) on/off |
| `persist.sys.strictmode.visual` | Debug: visual strict mode |
| `persist.sys.ui.hw` | Hardware UI rendering on/off |
| `persist.sys.` | "nu" prefix (likely a StringBuilder artifact) |
| `persist.radio.imsallowmtsms` | IMS mobile-terminated SMS |
| `persist.radio.imsregrequired` | IMS registration required |
| `persist.radio.otaspdial` | OTASP dial enabled |
| `persist.radio.ramdump` | Radio stack ramdump |

Strings like `persist.sys.keyoff_reboot is 0`, `persist.sys.keyoff_reboot set 1` also appear — those are **log messages** with the prop name embedded, not props themselves. They left a trace on grep because the filter only looks at the prefix.

### `ro.*` (18) — read-only, immutable after boot

| Prop | What it reports |
|---|---|
| `ro.build.id` | DA version — our value is `1.F187.16` |
| `ro.build.selinux` | SELinux build-time status |
| `ro.cdma.ecmexittimer` | CDMA emergency callback mode timer |
| `ro.com.android.dataroaming` | Default roaming |
| `ro.com.android.mobiledata` | Default mobile data |
| `ro.com.android.wifi-watchlist` | Wi-Fi watchlist |
| `ro.config.license_path` | Path to the license file |
| **`ro.debuggable`** | **0 in prod, 1 in debug**. Ours is probably 0 — worth confirming |
| `ro.kernel.qemu` | Is this an emulator? |
| `ro.lockscreen.disable.default` | Default lockscreen (disabled in the car) |
| `ro.ril.fccid` | Radio FCC ID |
| `ro.allow.mock.location` | Mock location allowed |
| `ro.screenreader.market` | Screenreader market |
| **`ro.serialno`** | Device serial number — already known (`androidboot.serialno` in the kernel cmdline) |
| `ro.setupwizard.mode` | Setup wizard mode |
| `ro.telephony.default_network` | Default network (RIL) |
| `ro.url.safetylegal` | Legal URL |

### `net.*` (9) — networking

| Prop | What it does |
|---|---|
| `net.gsm.attempt-gprs`, `net.gsm.succeed-gprs` | GPRS counters |
| `net.gsm.radio-reset` | Radio reset flag |
| `net.ppp0.dns1`, `net.ppp0.dns2` | PPP DNS (TCU dial-up) |
| `net.ppp.reset-by-timeout` | PPP reset on timeout |
| `net.tcp.buffersize.wifi` | TCP buffer over Wi-Fi |
| `net.tethering.noprovisioning` | Tethering without provisioning |
| `net.wimax.mac.address` | WiMAX MAC |

All cellular/Wi-Fi related — US/Acura firmware included (there's a registered TCU/CDMA even though not active in BR).

## Highlights

### HMI properties (the 4 that matter)

The only vendor-specific properties on the platform are the 4 `sys.hmi_*` flags. They give the current state without needing to listen for broadcasts:

```java
boolean started = "1".equals(SystemProperties.get("sys.hmi_service_started"));
String cause    = SystemProperties.get("sys.hmi_service_start_cause");   // "ColdBoot" | "ExitLP0" | "AccOnRestart"
boolean keyoff  = "1".equals(SystemProperties.get("sys.hmi_service_keyoff"));
boolean reboot  = "1".equals(SystemProperties.get("sys.hmi_reboot_reservation"));
```

**For AutoOk**, two possible uses:
1. **On boot**, before starting the watcher: read `sys.hmi_service_start_cause`. If `ColdBoot`, use a long delay (whole system coming up). If `ExitLP0`, short delay (fast comeback). Saves battery/CPU in the common case.
2. **In the watchdog**, check whether `sys.hmi_service_started == "0"` means "system about to sleep" and reduce activity preemptively.

### `persist.sys.keyoff_reboot`

This is the property that decides whether the car does **cold boot on key-off** vs. **suspend/resume**. Today our firmware defaults to suspend — the `AUDIO 5s + confirm reboot` combo is what forces cold boot.

**If we set `persist.sys.keyoff_reboot=1`**, every key-off theoretically becomes a cold boot. That has three potential implications:

1. **It might solve everything v0.4.0 handles** — if every "ignition on" is a cold boot, the warning appears from scratch without the weird LP0.
2. **UX impact**: the Honda powers on more slowly (3-5 s boot vs. instant suspend).
3. **Power impact**: cold boot uses more energy than resume — may drain the battery in days of idle.

Worth researching without committing. Low cost: `su -c "setprop persist.sys.keyoff_reboot 1"` + test + revert with `0`.

### `ro.debuggable`

If `ro.debuggable=1` by some vendor-config magic, it would open **adb shell with unrestricted access** without needing EvilValet. Worth checking via `getprop ro.debuggable` in the car — read-only, zero cost.

## Methodological notes

- **"False-positive" entries**: `persist.sys.keyoff_reboot is 0`, `persist.sys.keyoff_reboot set 1`, etc., are **log strings** with the prop name embedded. They left fingerprints on grep. For a future script, filter strings without spaces.
- **Honda-specific props are rare**: the platform mainly uses **broadcasts and binder** for communication. SysProps are reserved for persisted state or for things read by native binaries (e.g. `init.rc` consulting `sys.hmi_service_started` to decide whether to start something).

## Suggested next steps

1. **Full `getprop` dump** in the car — next time with access, run `su -c getprop | tee /sdcard/getprop-full.txt`. That will also catch props read by native binaries (not only what's in Java bytecode).
2. **Test `persist.sys.keyoff_reboot=1`** as an experiment with rollback ready. More risky — leave it as a Phase 9 follow-up.
