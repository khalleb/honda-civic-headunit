# X-ray of the Mitsubishi/Honda head unit — Layer 1 (surface scan)

**Date:** 2026-10-19
**Methodology:** deodex with baksmali 2.5.2 → bytecode grep + binary `AndroidManifest.xml` parsing (`strings -el`) → consolidation into tables → sampling verification via REA (JADX 0.7.1).
**Target:** raw dump `0040` (Brazilian firmware `1.F187.16`): `vendor-app/` (78), `system-app/` (42), `system-priv-app/` (0), `vendor-framework/` (104 jars/odex). Total: **160 smali projects** generated in bulk.

This x-ray is the platform's "schema": lists what **exists**, not what **each thing does**. The deeper dives (Layer 2) use these documents as a starting point.

## The 5 scans

| # | File | What it maps | Count |
|---|---|---|---|
| 1 | [`01-apis-aidl.md`](01-apis-aidl.md) | Internal binder interfaces (IPC contracts) | **364 unique interfaces** |
| 2 | [`02-broadcasts.md`](02-broadcasts.md) | Actions with `com.mitsubishielectric.*` / `com.honda.*` prefix referenced in bytecode | **445 distinct actions across 48 prefixes** |
| 3 | [`03-content-providers.md`](03-content-providers.md) | ContentProvider authorities and URIs | **27 authorities, 52 URIs** (9 vendor) |
| 4 | [`04-system-properties.md`](04-system-properties.md) | SystemProperties read/written in the shipping build | **48 properties across 4 prefixes** |
| 5 | [`05-trust-map.md`](05-trust-map.md) | Trust map: `sharedUserId`, package, permissions by APK | **110 APKs, 11 with `android.uid.system`** |
| 6 | [`06-diag-apks.md`](06-diag-apks.md) | RE of the Diag APKs (DealerDiag et al.) and `DiagApService` | **91 DealerDiag screens, no PIN** |
| 7 | [`07-services-re.md`](07-services-re.md) | RE of services: steering wheel, official OTA, vehicle, audio | **StrgSW, SystemUpdate, VehicleInfoManager, SystemInfoService** |
| 8 | [`08-github-landscape-2026-10-27.md`](08-github-landscape-2026-10-27.md) | GitHub landscape: 33 repos, KingoSU found in our `su`, Mitsubishi TX codes mapped by Clusters | **KingoSU in `/system/xbin/su`**, Clusters, opendbc, CR-V China |

## High level — what the x-ray reveals

### The platform is mostly IPC

The 364 binder interfaces (many with `*Listener`/`*Callback` mirroring async) show the architecture is **mediator-based**: every car capability (navigation, audio, camera, HFT, voice, telematics, strg sw, vehicle info, etc.) has its own `ApService` with a public AIDL. Any app running with the right UID can bind and consume.

**Implication for us:** adding features to AutoOk via the official path is "pick the right AIDL, bind, consume". Much cleaner than the `logcat polling` + `input tap` we use today — but it requires understanding each AIDL individually (upcoming phases).

### The 445 broadcasts are the main control flow

33 already-known APKs listen for `ACTION_HMI_SERVICE_START`. But there's a lot more pub/sub contract: 38 actions just from PowerManager, 40 from Honda navi, 34 from HFT, 24 from Honda system. MAPA already had the essential PowerManager bits; now we have the full spreadsheet.

### Only 11 APKs run as `android.uid.system`

The implicit whitelist of "who can do anything" is short — and we already know all the names (see §05). This confirms `/system/app/` has low inclusion cost for our apps, but privileged capabilities require picking the right receiver/intent (there's no "becoming system" by magic — it's manifest + sharedUserId at build time).

### Vehicle structured data lives in 9 ContentProviders

Beyond the already-mapped whitelist (`com.honda.displayaudio.whitelist`), there are providers for **telematics CRM** (`com.honda.telematics.core.crm`), **POI download** (`com.honda.telematics.core.downloadpoiprovider`), **telema info** (`com.honda.displayaudio.system.telemainfo.telemainfoprovider`), **launcher favorites** (two tables), **HFT phonebook/photo** (two tables), and the Clarion LinkManager adapter.

### The system properties surface is small and named

Only 48 props are referenced in bytecode; of those, 4 are HMI-specific: `sys.hmi_service_started`, `sys.hmi_service_start_cause`, `sys.hmi_service_keyoff`, `sys.hmi_reboot_reservation`. The rest are AOSP standard (`ro.build.*`, `net.*`, `persist.radio.*`).

## How it was collected (reproducible)

```bash
BULK=/tmp/.../scratchpad/bulk-smali   # temp dir of this session
BAK=tooling/references/ic1101/apk-rebuilder/input/baksmali-2.5.2.jar
DUMP=tooling/apks-dumped/dump-0040

mkdir -p "$BULK/bootclasspath"
cp "$DUMP/system-framework/"*.odex  "$BULK/bootclasspath/"
cp "$DUMP/vendor-framework/"*.odex  "$BULK/bootclasspath/"

for dir in vendor-app vendor-framework system-app system-priv-app; do
  for odex in "$DUMP/$dir/"*.odex; do
    name=$(basename "$odex" .odex)
    java -jar "$BAK" deodex -a 17 \
      -d "$BULK/bootclasspath" \
      -o "$BULK/by-apk/$name" "$odex"
  done
done
```

Then the greps/awks of each scan run over `$BULK/**/*.smali` + `unzip -p AndroidManifest.xml | strings -el` over the APKs. Total time ~5 min on current hardware.

**The raw datasets** (full lists, which don't fit in the docs) landed in `/tmp/.../scratchpad/raio-x/`: `aidl-unique.txt`, `actions-vendor.txt`, `content-uris.txt`, `sysprops-clean.txt`, `apk-permissions-uses.txt`, `apk-pkg-shareduid.txt`. Since it's the scratchpad, they vanish at session end — if we want to keep them in the repo, the next step is copying to `tooling/raio-x/data/` (not done in this round).

## Known limits

- **`strings -el` over binary AXML** detects ~67/110 packages. In the remaining 43, the package name is tangled with `com.mitsubishielectric.uilib` (uses-library) or shows "?" due to strings/AXML limits. For a definitive per-APK analysis, use REA `inspect-android-package` individually — see §01 of MAPA §20.8.
- **Reflection / dynamic class loading** is not captured. Some `SystemProperties.get(...)` with names built via `StringBuilder` fall outside scan 4.
- **Action prefixes are not 100% canonical** — `com.mitsubishielectric.android.action.camera.*` and `com.mitsubishielectric.ada.*` coexist; the scan groups by raw prefix, no normalization.
- **`system-priv-app/` was empty in the dump** — if it exists in the future, re-running the pipeline covers it.

## Where this points (Layer 2 candidates)

Ranked by immediate value to the project:

1. **Camera** — the `IRearWideCameraDisplay` AIDL + actions `com.mitsubishielectric.android.action.camera.*` are the correct path to replace the AutoOk v0.4.0 logcat polling for reverse. Natural Phase 9.
2. **Diag** (DealerDiag, DeveloperDiag, PreShipmentDiag, LetDiag) — typically carry PINs, service modes, hidden menus. **→ deep-dived in [`06-diag-apks.md`](06-diag-apks.md) (2026-10-24):** there's no PIN (screens are `exported=false` with no internal gate; root opens them via `am start`); 91 DealerDiag screens classified into read / hardware test / write; the "unlock code" is Garmin map licensing, not a password.
3. **Vehicle** (VehicleRW, VehicleInfoManager, VehicleDbManager — 55 AIDL interfaces) — this is where CAN read/write lives. Phase 10+, high risk if writing.
4. **StrgSW** — mapping of the physical steering wheel buttons. Low cost, useful for direct hooks.
5. **AV + MediaCoreService** — audio pipeline, routing. Ducking bypass potential (our audio not getting lowered by Honda voice).

None of these are in scope for this session.
