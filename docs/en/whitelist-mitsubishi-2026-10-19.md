# Mitsubishi Whitelist — full static analysis

**Date:** 2026-10-19
**Tooling:** REA (`morluto/rea` v6.7.0) + JADX headless 0.7.1 + baksmali/smali 2.5.2
**Starting question:** if the PowerManager isn't restarting our Service after LP0, could it be because we're not on the "Mitsubishi whitelist"? Would adding our APK to the whitelist drop the v0.4.0 workaround?
**Short answer:** **no.** The Mitsubishi whitelist is an install-UX mechanism, consulted only by `AppManager.apk` and `FileManager.apk`. The PowerManager uses a pure pub/sub pattern over broadcasts — any app that registers the right receiver participates. Our v0.4.0 already follows that pattern.

This document preserves the complete whitelist and post-LP0 recovery flow even though the "get on the whitelist" route doesn't fix our workaround — because understanding this subsystem opens other opportunities (e.g. friendly metadata in AppManager, use of other PowerManager broadcasts).

---

## Executive summary

| Question | Answer | Evidence |
|---|---|---|
| Who defines the whitelist? | The APK `com.honda.displayaudio.whitelist` (14 KB in `/system/vendor/etc/honda/`, not dumped), via a ContentProvider that serves a ZIP containing `whitelist-1.0.xml` | `WhitelistContentResolver.getWhitelistZip()` (below) |
| Where does the XML live at runtime? | `/data/data/whitelist-1.0.xml` (literal, straight at the root of `/data/data/` — `WhitelistApService` runs as `android.uid.system`) | `WhitelistUtil.WHITELIST_FILE_REGEX`, `WhitelistFileManager.WHITELIST_DIRECTORY` |
| How does it get updated? | Boot: `WhitelistApService.onCreate` → queries the content provider → if the new `contentVersion` > current, replaces the local file. Runtime: `PACKAGE_REPLACED` on `com.honda.displayaudio.whitelist` fires `WhitelistUpdateService` which does the same | `WhitelistContentResolver.updateWhitelist()`, `WhitelistContentReceiver.onReceive()` |
| XML format? | `<whiteList><contentVersion/><controlData><application>…</application>…</controlData></whiteList>` with `<package>`, `<versionCode>`, `<keyStore>`, `<audioStreamType>`, `<withAudio>`, `<regulation>`, `<revert>` | `WhitelistXmlParser` literal fields in the smali |
| Who consults the whitelist? | UI only: `AppManager.apk` (manager) calls `getApplicationName`, `getAudioInfo`, `getRegulation`, `getRevert`. `FileManager.apk` (USB install screens). **No HMI service, no PowerManager, no launcher.** | grep over 120 deodexed APKs — only 3 consumers |
| Does getting on the whitelist fix LP0? | **No.** PowerManager doesn't consult the whitelist. Post-LP0 restart happens via `ACTION_HMI_SERVICE_START` broadcast which any app can listen to without permission | `PowerManagerBroadcastSender`, 33 APK listeners |

---

## 1. How we analyzed

### 1.1 Preparation

All of Mitsubishi's vendor-app is **odex-only** (pre-dexed). For JADX/REA to open any APK, we need:

1. `tooling/deodex/deodex-apk.sh <APK>` — assembles a bootclasspath with `system-framework/*.odex` + `vendor-framework/*.odex`, runs `baksmali deodex`, `smali assemble`, injects `classes.dex` into a copy of the APK.
2. For libraries (`vendor-framework/*.jar`), REA rejects a bare `.jar` — so we build an "APK wrapper" by copying the manifest from an empty APK (the `WhitelistApService` itself) and swapping the `classes.dex`. Simple hack, works.

### 1.2 Bulk deodex

For this analysis we had to deodex all 120 APKs in `vendor-app/` + `vendor-framework/` in one shot to grep globally. The workspace in `/tmp/.../scratchpad/bulk-smali/by-apk/<Name>/com/mitsubishielectric/.../` was ready in ~2 min.

### 1.3 Reproduce

```bash
export REA_JADX_MCP_JAR=~/.local/share/rea/android/jadx-headless-mcp-0.7.1-all.jar

./tooling/deodex/deodex-apk.sh tooling/apks-dumped/dump-0040/vendor-app/WhitelistApService.apk

APK=tooling/apks-decoded/WhitelistApService-deodexed.apk
npx -y rea-agents@latest inspect-android-package   "$APK" --json
npx -y rea-agents@latest search-android-classes    "$APK" "" --json
npx -y rea-agents@latest inspect-android-class     "$APK" com.mitsubishielectric.ada.appservice.whitelist.WhitelistApService --json
npx -y rea-agents@latest inspect-android-method    "$APK" com.mitsubishielectric.ada.appservice.whitelist.WhitelistContentResolver updateWhitelist --json
```

For the lib: deodex `vendor-framework/WhitelistLib.odex` manually, inject the `classes.dex` into a copy of `WhitelistApService-deodexed.apk`, and REA takes it as an APK.

---

## 2. The three entities

```
                    ┌──────────────────────────────────────────────┐
                    │  Other apps (AppManager, FileManager, …)     │
                    │  bindService(action=IWhiteListApService) ────┼─────┐
                    └──────────────────────────────────────────────┘     │
                                                                          ▼
┌──────────────────────────────────┐   uses-library   ┌──────────────────────────────┐
│ WhitelistApService.apk (vendor)  │ ───────────────▶ │ WhitelistLib.jar             │
│  — 5 shell classes:              │                  │   (vendor-framework)         │
│   WhitelistApService (binder)    │                  │ — 15 real classes:           │
│   WhitelistContentReceiver       │                  │   IWhitelistApService (AIDL) │
│   WhitelistContentResolver       │                  │   IWhitelistApService$Stub   │
│   WhitelistUpdateService         │                  │   WhitelistFileManager       │
│   R                              │                  │   WhitelistXmlParser         │
│  — sharedUserId=android.uid.system│                 │   WhitelistModel             │
│  — permission VEHICLE_RW         │                  │   WhitelistCriteria          │
└──────────────────────────────────┘                  │   WhitelistUtil              │
            │ onCreate                                │   WhitelistConst             │
            │ updateWhitelist()                       │   enums.{Audio,Regulation,   │
            ▼                                         │     Revert,Stream,Symbol}   │
┌──────────────────────────────────┐                  └──────────────────────────────┘
│ WhitelistContentResolver         │
│  openAssetFileDescriptor(        │
│   "content://com.honda.           │   ContentProvider
│    displayaudio.whitelist/1.0")  │ ───────────────────┐
└──────────────────────────────────┘                    │
                                                        ▼
                            ┌──────────────────────────────────────────┐
                            │ APK com.honda.displayaudio.whitelist.apk │
                            │  — carrier of the ZIP with whitelist-1.0.xml │
                            │  — path: /system/vendor/etc/honda/       │
                            │  — ~14 KB (per MAPA §7)                  │
                            │  — NOT IN CURRENT DUMP (gap scan)        │
                            └──────────────────────────────────────────┘
```

### 2.1 WhitelistApService.apk (`com.mitsubishielectric.ada.appservice.whitelist`)

- **Manifest key points:**
  - `android:sharedUserId="android.uid.system"` — runs under the system UID.
  - `uses-permission com.mitsubishielectric.ada.permission.VEHICLE_RW`
  - `uses-permission android.permission.WRITE_EXTERNAL_STORAGE`
  - 3 `uses-library`: `explog.lib`, `constext.lib`, `whitelist.lib`.
  - 2 services:
    - `.WhitelistApService` with `intent-filter action=com.mitsubishielectric.ada.appservice.whitelist.IWhiteListApService` (⚠️ note `WhiteList` with uppercase L in this action — the rest of the codebase uses `IWhitelistApService` with lowercase l).
    - `.WhitelistUpdateService` protected by `com.mitsubishielectric.ada.permission.VEHICLE_RW`.
  - 1 receiver: `.WhitelistContentReceiver` listening to `android.intent.action.PACKAGE_REPLACED` with `data scheme=package`.

- **Classes (5):** `R`, `WhitelistApService`, `WhitelistContentReceiver`, `WhitelistContentResolver`, `WhitelistUpdateService`. Zero logic — all the real work is delegated to the lib.

### 2.2 WhitelistLib.jar (`vendor-framework/WhitelistLib.{jar,odex}`)

15 classes loaded via `<uses-library>`. The relevant ones:

| Class | Role |
|---|---|
| `IWhitelistApService` (AIDL interface) | 7 public methods (listed below) |
| `IWhitelistApService$Stub` | binder base implementation |
| `WhitelistFileManager` | reads/writes `/data/data/whitelist-1.0.xml` + `TEMP_whitelist-1.0.xml` |
| `WhitelistXmlParser` | XmlPullParser consuming the tags |
| `WhitelistModel` | POJO holding the parsed content |
| `WhitelistCriteria` + `WhitelistCriteriaProtocol` | rule parsers (comma-delimited) |
| `WhitelistUtil` | `isWhitelistXMLFile`, `compareWhitelistContentVersion`, `getContentVersion`, `isExternalPath`, `checkHondaApplication` |
| `WhitelistConst` | 24 constants (regulation, revert, stream, symbol) |
| `enums.*` | typed enums of the integer values |

### 2.3 XML carrier APK — `com.honda.displayaudio.whitelist.apk`

**It is mentioned in MAPA §7 as living at `/system/vendor/etc/honda/com.honda.displayaudio.whitelist.apk` (~14 KB), but the 0040 deep-scan didn't bring this file in.** The directory `system-etc/honda/` doesn't even exist in the dump — gap in the deep-scan: the next round should include `/system/vendor/etc/honda/*`.

From what the code implies, this APK:
- Is a regular package (doesn't need Java code — can be just a manifest + a ContentProvider that reads an asset).
- Publishes a `ContentProvider` with `authority="com.honda.displayaudio.whitelist"`.
- The `/1.0` path of the URI exposes an `AssetFileDescriptor` pointing to a ZIP (asset of the APK).
- The ZIP contains **one entry named `whitelist-1.0.xml`** (exact name — the comparison in `WhitelistUtil.isWhitelistXMLFile` is `filename.equals("whitelist-1.0.xml")`).

---

## 3. Public interface (AIDL `IWhitelistApService`)

7 methods exposed via Binder. Any app that calls `bindService` with `action = "com.mitsubishielectric.ada.appservice.whitelist.IWhiteListApService"` can call them (**no permission required** in the intent-filter):

| Method | Purpose |
|---|---|
| `boolean checkInstallPackage(String pkg)` | ⭐ "is this package authorized?" — **BUT NEVER called from any shipped APK** |
| `List<String> getPackageNames(String ???, boolean withAudio)` | enumerate packages with/without audio |
| `String getApplicationName(String pkg, int versionCode)` | friendly app name (e.g. "Android Auto") |
| `int getAudioInfo(String pkg, int versionCode)` | 0=no audio, 1=has audio |
| `int getAudioStreamType(String pkg, int versionCode)` | 0=NULL, 1=SYSTEM, 2=ADA_GUIDE_HIGH, 3=VOICE_RECOGNITION, 4=ADA_GUIDE, 5=ADA_GUIDE_LOW, 6=MUSIC |
| `int getRegulation(String pkg, int versionCode)` | 0=NULL, 1=PARKTRIGGER (parked only), 2=SPEEDTRIGGER (moving only), 3=PARKSPEEDTRIGGER (both) |
| `int getRevert(String pkg, int versionCode)` | 0=NO, 1=YES |

### Who actually calls (`invoke-interface` on `IWhitelistApService` across 120 deodexed APKs)

**3 consumers, all UI:**

1. **`AppManager.apk` → `WhiteListAdapter.smali` + `WhiteListAdapter$1.smali`**
   Calls: `getApplicationName`, `getAudioInfo`, `getRegulation`, `getRevert`.
   Purpose: populate the application list in the built-in app manager (friendly name + usage condition).

2. **`FileManager.apk` → `FileManagerActivity.smali`, `TelopInstallPopup.smali`, `commonservice/CommonServiceConnection.smali`, `FileManagerActivity$6.smali`**
   Purpose: validate/show metadata when the user connects a pendrive with APKs and tries to install something.

3. **`WhitelistLib` + `WhitelistApService` themselves** (don't count — that's the service itself).

**`checkInstallPackage` never appears as `invoke-interface` anywhere in the shipping image.** It exists in the AIDL, but in practice nobody calls it.

**No HMI service, no launcher, no PowerManager, no boot component consults the whitelist.**

---

## 4. XML format

### 4.1 Tags (from `WhitelistXmlParser.smali`, literal fields)

```xml
<whiteList>
  <formatVersion>1.0</formatVersion>
  <contentVersion>N</contentVersion>
  <controlData>
    <application>
      <name>Friendly Name</name>
      <package>com.example.app</package>
      <versionCode>1</versionCode>
      <keyStore>SHA-256_of_signing_certificate_in_hex</keyStore>
      <audioStreamType>0</audioStreamType>
      <withAudio>false</withAudio>
      <regulation>0</regulation>
      <revert>0</revert>
    </application>
    <application>…</application>
  </controlData>
</whiteList>
```

- Encoding: UTF-8.
- `<keyStore>` is probably the hex SHA-256 of the signing certificate — our debug key has a known hash:
  `A40DA80A59D170CAA950CF15C18C454D47A39B26989D8B640ECD745BA71BF5DC` (CLAUDE.md).

### 4.2 Filesystem paths (from `WhitelistConst.smali` and `WhitelistUtil.smali`)

| Constant | Value |
|---|---|
| `WHITELIST_FILE_REGEX` (despite the name, it's a literal string) | `whitelist-1.0.xml` |
| `WHITELIST_DIRECTORY` | `/data/data/` |
| `WHITELIST_TEMP_NAMEADITION` | `TEMP_` (prefix during update) |
| `WHITELIST_USB_DIRECTORY` | `/data/data/usbtmp` |
| `WHITELIST_FORMAT_VERSION_FLOATING` | `1.0` |
| `MNT_USBDRIVE1` / `MNT_USBDRIVE2` | `/mnt/usbdrive1` / `/mnt/usbdrive2` |
| `PACKAG_MITSUBISH` | `mitsubishielectric` (substring used in `checkHondaApplication`) |

### 4.3 Enums (from `WhitelistConst.smali`)

```
WHITELIST_AUDIO_WITH          = 1
WHITELIST_AUDIO_WITHOUT       = 0

WHITELIST_REGULATION_NULL             = 0
WHITELIST_REGULATION_PARKTRIGGER      = 1
WHITELIST_REGULATION_SPEEDTRIGGER     = 2
WHITELIST_REGULATION_PARKSPEEDTRIGGER = 3

WHITELIST_REVERT_NO  = 0
WHITELIST_REVERT_YES = 1

WHITELIST_STREAM_NULL                   = 0
WHITELIST_STREAM_SYSTEM                 = 1
WHITELIST_STREAM_ADA_GUIDE_HIGH         = 2
WHITELIST_STREAM_ADA_VOICE_RECOGNITION  = 3
WHITELIST_STREAM_ADA_GUIDE              = 4
WHITELIST_STREAM_ADA_GUIDE_LOW          = 5
WHITELIST_STREAM_MUSIC                  = 6

WHITELIST_SYMBOL_AUDIO      = 1
WHITELIST_SYMBOL_STREAM     = 2
WHITELIST_SYMBOL_REGULATION = 3
WHITELIST_SYMBOL_REVERT     = 4

WHITELIST_NOT_EXIST       = -1  (sentinel return)
WHITELIST_NOT_DEFINITION  = -2
```

---

## 5. Flows

### 5.1 Boot — initial ingestion

`WhitelistApService.onCreate()`:

```java
public void onCreate() {
    super.onCreate();
    ExpLog.setTag("WhitelistApService");
    ExpLog.trace("onCreate service!");
    WhitelistFileManager.createUsbtemp();       // mkdir /data/data/usbtmp
    this.mFileManager = new WhitelistFileManager();
    updateWhitelist();                           // see 5.2
}
```

### 5.2 Update (boot or PACKAGE_REPLACED)

`WhitelistApService.updateWhitelist()`:

```java
private void updateWhitelist() {
    WhitelistContentResolver resolver = new WhitelistContentResolver(this);
    if (resolver.updateWhitelist()) {           // true if overwritten
        this.mWhitelistXmlFileName = this.mFileManager.getWhitelistInDirectory();
        if (this.mWhitelistXmlFileName != null) {
            sWhitelistXml = this.mFileManager.getWhitelistModel(this.mWhitelistXmlFileName);
        }
    }
}
```

`WhitelistContentResolver.updateWhitelist()` (simplified — JADX decompile came out ugly with duplicated try/catch):

```
1. checkDescriptor = resolver.openAssetFileDescriptor(
     Uri.parse("content://com.honda.displayaudio.whitelist/1.0"), null);
2. targetDescriptor = same (two independent streams)
3. checkZis = ZipInputStream(checkDescriptor.createInputStream())
4. newZipEntry = getWhitelistInZip(checkZis)   // finds the entry named "whitelist-1.0.xml"
5. targetZis = ZipInputStream(targetDescriptor.createInputStream())
6. seekZipStream("whitelist-1.0.xml", targetZis)   // positions
7. mFileManager.updateNewWhitelistInDirectory(targetZis, newZipEntry)
```

`WhitelistFileManager.updateNewWhitelistInDirectory`:

```java
public boolean updateNewWhitelistInDirectory(ZipInputStream zis, ZipEntry newEntry) {
    boolean res = saveFile(zis, newEntry);     // writes /data/data/TEMP_whitelist-1.0.xml
    if (getWhitelistInDirectory() == null) {   // first time — no existing XML
        res = renameFile(newEntry);            // TEMP_ → whitelist-1.0.xml
    } else {
        String tempfilename = "TEMP_" + newEntry.getName();
        String filename = newEntry.getName();
        if (WhitelistUtil.compareWhitelistContentVersion(tempfilename, filename) > 0) {
            res = renameFile(newEntry);        // replaces only if temp.contentVersion > current
        }
        deleteFile(createFilePath(tempfilename));
    }
    return res;
}
```

**Critical rule:** `<contentVersion>` must be **strictly greater** to replace. Any XML modification has to come with an incremented `<contentVersion>`.

### 5.3 PACKAGE_REPLACED — runtime update

`WhitelistContentReceiver.onReceive`:

```java
public void onReceive(Context context, Intent intent) {
    if (intent == null) return;
    String action = intent.getAction();
    String packageName = intent.getDataString();
    if (!"android.intent.action.PACKAGE_REPLACED".equals(action)
        || !"package:com.honda.displayaudio.whitelist".equals(packageName)) {
        return;    // only reacts if the whitelist package changed
    }
    Intent updateIntent = new Intent();
    updateIntent.setClassName(UPDATE_SERVICE_PACKAGE, UPDATE_SERVICE_CLASS);
    context.startService(updateIntent);        // calls WhitelistUpdateService
}
```

`WhitelistUpdateService` runs on a thread (`mUpdateThread`), calls the same `WhitelistContentResolver.updateWhitelist()` as boot.

### 5.4 Querying (how it's used — binder pattern)

```java
Intent i = new Intent("com.mitsubishielectric.ada.appservice.whitelist.IWhiteListApService");
context.bindService(i, serviceConnection, Context.BIND_AUTO_CREATE);
// serviceConnection.onServiceConnected receives the IBinder:
IWhitelistApService svc = IWhitelistApService.Stub.asInterface(binder);
String name = svc.getApplicationName("com.example.app", 1);
int regulation = svc.getRegulation("com.example.app", 1);
```

That's what `AppManager/WhiteListAdapter` does. Not even a permission check — any app can query.

---

## 6. Post-LP0 recovery — how it actually works

### 6.1 PowerManager is pure pub/sub

`com.mitsubishielectric.ada.appservice.powermanager.PowerManagerApService` **does not keep a list of services to restart**. It fires broadcasts at key points of the power cycle. Each app that wants to participate in the HMI flow registers receivers in the manifest.

### 6.2 Broadcasts emitted (from `PowerManagerBroadcastSender`, 16 methods)

| Method | When | Action sent |
|---|---|---|
| `sendHMIServiceStartIntent(ctx, cause)` | Exiting LP0 or ACC-on-restart | `ACTION_HMI_SERVICE_START` with extra `state` = cause (e.g. `"ExitLP0"`, `"AccOnRestart"`, `"ColdBoot"`) |
| `sendHMIServiceStopIntent(ctx, cause)` | Entering LP0 or shutdown | `ACTION_HMI_SERVICE_STOP` |
| `sendHMIServicePreStopIntent(ctx, cause)` | Preparing for LP0 | `ACTION_HMI_SERVICE_PRE_STOP` |
| `sendHMIServiceRestartIntent(ctx, cause)` | ACC-on during a transition | `ACTION_HMI_SERVICE_RESTART` |
| `sendHMIServiceStopIntentSplit(ctx, cause, extra)` | Variant with split info | same stop |
| `sendFinishAllRunnningTaskForegroundIntent` | Kills foreground before LP0 | `ACTION_FINISH_ALL_RUNNING_TASKS_FOREGROUND` |
| `sendFinishAllRunnningTaskIntent` / `Partial` | Kills processes (variants) | two similar actions |
| `sendResumeCameraIntent(ctx)` | ⭐ Rear camera resume | dedicated action — **opportunity**: today AutoOk polls logcat; this broadcast is clean |
| `sendStartAnimationIntent(ctx)` | Boot animation | — |
| `sendChangeStartCauseNoticeIntent(ctx, cause)` | Startup reason change | — |
| `sendKeyOffLimitNoticeIntent(ctx, cause)` | Key-off timer expiring | — |
| `sendSetVbusResIntent(ctx, cause, res)` | VBUS result | — |
| `sendSyscomResetStartNoticeIntent(ctx)` | SysCom reset | — |
| `sendVbusOffNoticeIntent(ctx)` | VBUS turned off | — |

### 6.3 Confirmed listeners in the shipping image

Bytecode grep across 120 APKs: **33 reference `ACTION_HMI_SERVICE_START`.** Full list:

```
AcuraLinkApService        AndroidAuto           AppManager
AppModeApService          AV                    Camera
CameraAPService           CarPlayService        ClockSync
CompassService            DaLauncher            DiagApService
EmergencyApService        ErrorManager          ExternalDisplayApService
ExternalDisplayOutService HftApp                HftApService
MirrorLink                Navigation            PhoneCoordination
PowerManagerApService     PowerManagerApServiceLib
ScreenshotApService       SensorMonitor         StrgSW
SystemUpdate              Telematics            UnitInfoManager
VehicleCoordination       VehicleInfoManager    VoicePortalAp
WifiApService
```

Top 5 by occurrence count: `DaLauncher` (4), `Camera` (4), `AV` (4), `AppManager` (4), `EmergencyApService` (3). The `DaLauncher.Launcher$HMIServiceReceiver` is actually what launches the `OpeningDivideActivity` that AutoOk v0.4.0 dismisses.

### 6.4 Our v0.4.0 already follows the pattern

`AutoOk/HmiServiceReceiver` listens to `ACTION_HMI_SERVICE_START` and re-starts the watcher. Same pattern as the 33 system services.

**There is no way to "jump the queue" by joining a list — the list does not exist.**

---

## 7. Discarded routes

### 7.1 Route A — write `/data/data/whitelist-1.0.xml` directly

**Discarded.** Even if it works technically (we have root), the only effect would be:
- Our APK showing up in the car's `AppManager` with a friendly name.
- Our APK showing up in the `FileManager` UI if we try to install via pendrive.

Doesn't affect LP0. Doesn't remove any v0.4.0 code.

### 7.2 Route B — modify `com.honda.displayaudio.whitelist.apk`

**Discarded for the same reason**, with the extra difficulty that the APK isn't in the 0040 dump (deep-scan gap — the next round needs to include `/system/vendor/etc/honda/*`). Cleaner than Route A because it survives a later `updateWhitelist()`, but the win is still cosmetic.

### 7.3 Original hypothesis was wrong

Our hunch was that PowerManager keeps a list of "HMI services" based on the whitelist and therefore doesn't restart our Service after LP0. **It's wrong.** PowerManager is whitelist-agnostic; the restart depends solely on the receiver registered in the manifest. Our v0.4.0 `HmiServiceReceiver` **is** the correct mechanism.

---

## 8. Bonus opportunities uncovered

### 8.1 Join the whitelist for cosmetic value

If one day we want AutoOk to show up in the car's official "App Manager" with a friendly name ("AutoOk — warning suppressor") + a configured regulation (e.g. `0` = no restriction), Route A is viable. Low priority.

### 8.2 Listen to `ACTION_HMI_SERVICE_STOP` and `_PRE_STOP`

Today AutoOk v0.4.0 only reacts to **resume**. Reacting to `_PRE_STOP` would allow saving state before LP0 (e.g. the last-known-log-position offset), to resume exactly where we left off. Today we lose that state.

### 8.3 ⭐ `sendResumeCameraIntent` as a reverse-camera trigger

Today AutoOk learns the rear camera came back / went away via **logcat polling** (see §13 of MAPA). That's fragile and expensive. PowerManager fires a dedicated broadcast — `sendResumeCameraIntent` — which would be a much cleaner trigger.

Worth a Phase 9: swap camera detection for a receiver registered on that action. First we need to confirm the exact action string (not in the visible constants — probably in `PowerManagerConstants.smali` or hardcoded inside the method).

### 8.4 Full broadcast list as a debug contract

The 16 broadcasts in `PowerManagerBroadcastSender` form the public power-management contract of the platform. Registering listeners for all of them in an instrumentation app (doesn't have to be AutoOk — can be a separate APK) would give a detailed timeline of the vehicle's power state. Useful for diagnosing weird behaviors.

---

## 9. APKs decoded in this analysis

Now under `tooling/apks-decoded/`:

- `WhitelistApService-deodexed.apk` (6 smali, 12 KB classes.dex)
- `WhitelistLib-asapk.apk` (20 smali, 47 KB — APK wrapper with the lib's classes.dex)
- `PowerManagerApService-deodexed.apk` (40 smali, 184 KB)
- `AppManagerServiceLib-asapk.apk` (41 smali, 128 KB — APK wrapper)
- `DaLauncher-deodexed.apk` (579 smali, 1.2 MB — from the earlier OpeningDivideActivity analysis)

Under `/tmp/.../scratchpad/bulk-smali/by-apk/<Name>/` there were **120 complete smali projects** (vendor-app + vendor-framework) — temporary, wiped at the end of the session.

---

## 10. Open question

**What's the exact action for `sendResumeCameraIntent`?** Worth 10 minutes on the `PowerManagerBroadcastSender.sendResumeCameraIntent` pseudocode or on `PowerManagerConstants.smali` — kept as a follow-up when/if we decide to open Phase 9.

---

**Evidence IDs (REA):** `ev_37e5ff64…`, `ev_742e311a…`, `ev_132387ab…`, `ev_805e74e4…`, `ev_357179c9…`, `ev_4c114516…`, `ev_7af9ae97…`, `ev_f6b0aa1a…`, `ev_fbd80713…`, `ev_08123e7b…`, `ev_13418a33…`, `ev_f83f62bd…`, `ev_2d83999a…`, `ev_60eb9f9a…`, `ev_a50a86d2…`, `ev_e7649556…`, `ev_645101a2…`, `ev_115cbd7c…`. Any query is reproducible via REA/CLI against the APKs in `tooling/apks-decoded/`.
