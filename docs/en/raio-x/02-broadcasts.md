# Scan 2 — Broadcasts (`com.mitsubishielectric.*` / `com.honda.*` actions)

**445 distinct actions across 48 prefixes.** Enumerated by greppig `"com.(mitsubishielectric|honda).*"` literals in the smali bytecode of 160 projects.

## How it was collected

```bash
grep -rhE 'const-string .*"com\.(mitsubishielectric|honda)[^"]*"' bulk-smali/*/ \
  | grep -oE '"com\.(mitsubishielectric|honda)[^"]+"' \
  | sort -u
```

Then a final filter keeping only strings ending in `.ACTION_FOO` or `.FOO_BAR_BAZ` (uppercase snake), dropping class names (`.StubProxy`, `.MainActivity`, etc.). 1109 vendor strings boiled down to 445 real actions.

**Limits:** actions assembled at runtime via `StringBuilder` don't show up. Strings inside XML resources also don't (resources aren't in the scan yet).

## Highlights — findings worth calling out

### Reverse: we have a dedicated broadcast ⭐

Three findings critical for Phase 9 of AutoOk (replace logcat polling):

1. **`com.mitsubishielectric.ada.appservice.powermanager.ACTION_RESUME_CAMERA`** — PowerManager announces the camera is back. It's the counterpart of the `sendResumeCameraIntent()` we had already seen in the PowerManagerBroadcastSender scan.
2. **`com.mitsubishielectric.ada.appservice.powermanager.ACTION_RESUME_COMPLETED_CAMERA`** — camera fully loaded.
3. **`com.mitsubishielectric.android.action.camera.EXIT_REAR_WIDE_CAMERA`** — **the reverse camera exit** (there are also `EXIT_FRONT_CAMERA`, `EXIT_LANEWATCH`, `EXIT_MVC`, `EXIT_CORNER_CAMERA`).

With the three, you can build a precise camera state machine in AutoOk without polling.

### PowerManager stop is **versioned by phases** (A-J)

```
ACTION_HMI_SERVICE_STOP
ACTION_HMI_SERVICE_STOP_A/B/C/D/E/F/G/H/I/J
ACTION_HMI_SERVICE_STOP_COMPLETE
ACTION_HMI_SERVICE_STOP_COMPLETE_A/B/C/D/E/F/G/H/I/J
```

21 broadcasts just for shutdown. That's why the transition is heavy — each "stop phase" fires a broadcast that serializes the exit of every HMI service in a controlled order. **Confirms the complexity** of the flow that v0.4.0 handles with a generic `forceRestartWatcher`.

### "Shoulder tap" is a real action

**`com.honda.displayaudio.system.action.SHOULDER_TAP`** — not a joke. Probably a "tap" notification (passenger signaling something?) or something more mundane. Worth looking at in the future.

### Human operator / personal assistance

- `com.honda.displayaudio.system.action.OPERATOR_CALL` — call operator (Honda Link / dealer concierge)
- `com.honda.displayaudio.system.action.ROADSIDEASSISTANCE_DIAL` — 24h roadside assistance via telematics
- `com.honda.telematics.core.action.EXECUTE_DIAG` + `RESPONSE_DIAG` — remote diag over the network

This is US/Acura firmware — probably **not active in BR** (no registered TCU/CDMA), but the code is there.

### Navigation is intent-based RPC

40 `com.honda.displayaudio.navi.action.*` actions paired as `REQ_*` / `RES_*` + `GET_*` / `RETURN_*`. That's a **broadcast-based RPC system** on top of the binder (which also exists in `appservice.navigation` with 25 interfaces). Two paths to the same thing.

For an app to look up the current location, send a route, list favorites, etc., just send an intent with `REQ_*` and listen for the paired `RES_*`.

### HFT (hands-free telephony) is its own universe

53 actions in total: 34 `extra.*` + 19 `action.*`. All related to Bluetooth pairing/discovery, calls, messages, pairing deny/accept. If we want our own telephony UI, the contract is here.

### Launcher exposes internal hooks

`com.mitsubishielectric.ada.app.dalauncher.action.*`:
- `NORMAL_STARTUP` and `PRECEDING_STARTUP` — distinguish boot phase
- `DISCLAIMER_COMPLETE` — announces the warning was accepted (our golden question!)
- `ANTITHEFT_RELEASE` — passed anti-theft
- `ECO_START` — eco screen started
- `INFO_TOP_ANIME`, `INFO_TOP_SCREEN_DISP/NO_DISP`, `INFO_MENU`, `INFO_CLOCK` — info screen events

**For AutoOk**: `DISCLAIMER_COMPLETE` is potentially the canonical signal that the warning has been dismissed. Worth validating whether it's also emitted when WE issue the tap (not just when the user does).

### Diag has dedicated actions

- `com.mitsubishielectric.ada.appservice.diag.ACTION_HMI_LET_DIAG_STATE_CHANGED`
- `ACTION_HMI_INPUTHISTORY_BACKUP_COMPLETE` (+ local backup variant)
- `com.mitsubishielectric.android.action.diag.EXIT_USER_OPERATION_ACTIVITY` + other `EXIT_*`

Hints for how to open dealer menus.

## Prefixes with 5+ actions (27 prefixes, 403 actions)

### `com.honda.displayaudio.navi.action.*` (40 actions)

`DESTINATION_ENTRY_STATUS` · `GET_MAP_UPDATE_STATUS` · `GET_MINIMAP_IMAGE` · `GET_ROUTE_INFO` · `MAP_UPDATE_STATUS_CHANGED` · `REQUEST_MAP_INFO` · `REQUEST_POIX_INFO` · `REQUEST_TRAFFIC_INFO` · `REQ_ADD_NEW_FAVORITE` · `REQ_DELETE_ROUTE` · `REQ_DESTINATION_HISTORY` · `REQ_FAVORITE_LIST` · `REQ_NEARBY_SEARCH` · `REQ_ROUTE_PREFERENCE_CHANGE` · `RES_ADD_NEW_FAVORITE` · `RES_DELETE_ROUTE` · `RES_DESTINATION_HISTORY` · `RES_FAVORITE_LIST` · `RES_GO_HOME` · `RES_MAP_UPDATE_STATUS` · `RES_MARKER` · `RES_MINIMAP_IMAGE` · `RES_NEARBY_SEARCH` · `RES_REQUEST_POIX_INFO` · `RES_ROUTE` · `RES_ROUTE_INFO` · `RES_ROUTE_PREFERENCE_CHANGE` · `RETURN_MAP_INFO` · `RETURN_TRAFFIC_INFO` · `ROUTE_PREFERENCE_SETTING` · `SET_GO_HOME` · `SET_MARKER` · `SET_ROUTE` · `START_CURRENT_MAP` · `START_MAP` · `START_NAVI_MAIN` · `START_NAVI_SETTING` · `START_PARKING` · `START_TRAFFIC_INFO` · `START_VR`

### `com.mitsubishielectric.ada.appservice.powermanager.*` (38 actions)

`ACTION_CHANGE_BOOT_CAUSE` · `ACTION_COLDBOOT_CAMERA_END` · `ACTION_COMPLETED_ANIMATION` · `ACTION_EMERGENCY` · `ACTION_HMI_SERVICE_PRE_STOP` · `ACTION_HMI_SERVICE_RESTART` · `ACTION_HMI_SERVICE_START` · `ACTION_HMI_SERVICE_STOP` · `ACTION_HMI_SERVICE_STOP_A..J` (10 variants) · `ACTION_HMI_SERVICE_STOP_COMPLETE` + `COMPLETE_A..J` (11 variants) · `ACTION_HOME_APP_START` · `ACTION_KEYOFF_LIMIT_NOTICE` · `ACTION_RESUME_CAMERA` · `ACTION_RESUME_COMPLETED_CAMERA` · `ACTION_SET_VBUS_REQ` · `ACTION_SET_VBUS_RES` · `ACTION_START_ANIMATION` · `ACTION_SYSCOM_RESET` · `ACTION_VBUS_OFF`

### `com.mitsubishielectric.ada.extra.hft.*` (34 extras)

Payloads associated with HFT actions: `EXTRA_BLUETOOTH_BOND_STATE`, `EXTRA_BLUETOOTH_CONNECTION_STATE`, `EXTRA_BLUETOOTH_DEVICE`, `EXTRA_BLUETOOTH_DISCONNECT_REASON`, `EXTRA_BLUETOOTH_PAIRING_DENIED_REASON`, `EXTRA_BLUETOOTH_PAIRING_KEY`, `EXTRA_BLUETOOTH_PAIRING_VARIANT`, `EXTRA_BLUETOOTH_SCAN_MODE`, `EXTRA_BLUETOOTH_STATE`, `EXTRA_CALL_PRIMARY_STATE`, `EXTRA_CALL_SECONDARY_STATE`, `EXTRA_HFT_BLUETOOTH_AUTO_CONNECT_LAPS`, `EXTRA_HFT_BLUETOOTH_CONNECTION_RESULT`, `EXTRA_HFT_BLUETOOTH_CONNECTION_TYPE`, `EXTRA_HFT_BLUETOOTH_PROFILE`, `EXTRA_HFT_NEW_MESSAGE`, `EXTRA_HFT_NEW_MESSAGE_NOTIFICATION`, and 17 more.

### `com.honda.displayaudio.navi.extra.*` (33 extras)

`ADD_NEW_FAVORITE` · `CATEGORY` · `CURRENT_PREFERENCE_ID` · `CURRENT_ROUTE` · `DATUM` · `ENTRY_STATUS` · `ERROR_STATUS` · `FAVORITE` · `FAVORITE_DISPLAYNAME` · `HISTORY` · `HISTORY_DISPLAYNAME` · `HOME` · `HOME_DISPLAYNAME` · `IS_DISPLAYED` · `LATITUDE` · `LIST_MAX` · `LONGITUDE` · `MAP_DATA` · `MAP_UPDATING` · `NEARBY` · `PARAMS` · `PKG_NAME` · `PREFERENCE_ID` · `PREFERENCE_ID_LIST` · `PREFERENCE_LIST` · `RADIUS` · `RESULT` · `RESULT_MESSAGE` · `ROUTE_DELETE_DISPLAYNAME` · `ROUTE_PREFERENCE_SETTING_DISPLAYNAME` · `SCREEN_CHANGE` · `STATUS` · `TRAFFIC_DATA`

### `com.honda.displayaudio.system.action.*` (24 actions)

`ADA_STARTED` · `ADA_STOP` · `DIALUP_CURRENT_UPDATE` · `DIALUP_SERVER_UPDATE` · `DRIVE_RANGE_INFO` · `FCD_UPLOAD_STATUS_CHANGED` · `GUI_COLOR_CHANGED` · `HFT_STATUS` · `LOCATION_UPLOAD_STATUS_CHANGED` · `LPA_CONNECTION` · `OPERATOR_CALL` · `PROVISIONING_CHANGED` · `PROVISIONING_STORED` · `REQ_CANCEL_ROUTE` · `REQ_DRIVE_RANGE` · `RES_CANCEL_ROUTE` · `ROADSIDEASSISTANCE_DIAL` · `SHOULDER_TAP` · `TCU_CDMA_MEID` · `TCU_HW_INFORMATION_CHANGED` · `TCU_MANUFACTURER_ID` · `TCU_PRODUCT_SERIAL` · `TCU_SW_INFORMATION` · `VIEW_PHONE_MENU`

### `com.honda.displayaudio.system.extra.*` (24 extras)

`CDMA_MEID` · `DISPLAY` · `DRIVE_RANGE_EV` · `DRIVE_RANGE_PET` · `DRIVE_RANGE_TOTAL` · `MANUFACTURER_ID` · `PRODUCT_SERIAL` · `REQUEST` · `RESULT` · `SETTING` · `SOCKET_NAME` · `STATUS` · `SW_VERSION_BUILD` · `SW_VERSION_MAJOR` · `SW_VERSION_MINOR` · `TCU_CONNECTION` · `TCU_ERROR_STATUS` · `TCU_MIN` · `TCU_MODE` · `TCU_PHONE_NUMBER` · `TYPE` · `UNIT` · `URL1` · `URL2`

### `com.mitsubishielectric.ada.appservice.appmanagerservice.*` (20)

`ACTION_DISPLAY_ACTIVITY_LAYOUT_NOTIFICATION` · `FINISH_CONDITION` · `action.ACTION_ALL_TASKS_FINISHED` · `action.ACTION_ALL_TASKS_FINISHED_FOREGROUND` · `action.ACTION_ALL_TASKS_FINISHED_PARTIAL` · `action.ACTION_FINISH_ACTIVITIES` · `action.ACTION_FINISH_ACTIVITIES_COMPLETED` · `action.ACTION_FINISH_ALL_RUNNING_TASKS` · `action.ACTION_FINISH_ALL_RUNNING_TASKS_FOREGROUND` · `action.ACTION_FINISH_ALL_RUNNING_TASKS_PARTIAL` · `action.ACTION_THIRDPARTY_AUDIO_APP_DISPLAYED` · `action.DIAG_DISPLAY_CHANGED` · `action.JUDGED_LAUNCH_OBJECT_CHANGED` · `action.THIRDPARTY_APP_DISPLAY_CHANGED` · `action.TOP_DISPLAY_PRIORITY_CHANGED` · `extra.DISPLAYING_DIAG_STATE` · `extra.EXTRA_THIRDPARTY_AUDIO_APP_COMP_NAME` · `extra.INTERRUPT_OBJECT_CATEGORY` · `extra.THIRDPARTY_APP_STATE` · `extra.TRANSITION_TRIGER` [sic, "Triger"]

### `com.mitsubishielectric.ada.action.hft.*` (19)

19 Bluetooth/call actions: `ACTION_HFT_ACL_DISCONNECTED` · `ACTION_HFT_BLUETOOTH_AUTO_CONNECT_STATE_CHANGED` · `ACTION_HFT_BLUETOOTH_BOND_STATE_CHANGED` · `ACTION_HFT_BLUETOOTH_CONNECTION_RESULT` · `ACTION_HFT_BLUETOOTH_CONNECTION_STATE_CHANGED` · `ACTION_HFT_BLUETOOTH_DISCOVERY_FINISHED` · `ACTION_HFT_BLUETOOTH_DISCOVERY_STARTED` · `ACTION_HFT_BLUETOOTH_FOUND` · `ACTION_HFT_BLUETOOTH_NAME_CHANGED` · `ACTION_HFT_BLUETOOTH_PAIRING_CANCEL` · `ACTION_HFT_BLUETOOTH_PAIRING_DENIED` · `ACTION_HFT_BLUETOOTH_PAIRING_REQUEST` · `ACTION_HFT_BLUETOOTH_SCAN_MODE_CHANGED` · `ACTION_HFT_BLUETOOTH_STATE_CHANGE` · `ACTION_HFT_BLUETOOTH_UUID` · `ACTION_HFT_CALL_STATE_CHANGE` · `ACTION_HFT_DELETE_BLUETOOTH_DEVICE_FINISHED` · `ACTION_HFT_NEW_MESSAGE_NOTIFY` · `ACTION_SERVICE_CONNECTION_STATE_CHANGED`

### `com.mitsubishielectric.ada.appservice.phonecoordination.*` (16)

Actions: `ACTION_ANDROIDAUTO_BLUETOOTH_AUTO_CONNECT_DETERRENCE`, `ACTION_ANDROIDAUTO_DELETE`, `ACTION_CARPLAY_CANCEL_DISPLAY_NOTIFY`, `ACTION_CARPLAY_DISCLAIMER_DISPLAY_NOTIFY` (+ `BUTTON` and `TYPE` variants), `ACTION_NOTIFY_PHONE_STATE`, `ACTION_NOTIFY_TCU_MODE`. Extras: `EXTRA_BLUETOOTH_AUTO_CONNECT_DETERRENCE_TYPE`, `EXTRA_PHONE_BT_INFO`, `EXTRA_PHONE_DISCONNECT_REASON`, `EXTRA_PHONE_EXT_INFO`, `EXTRA_PHONE_STATE`, `EXTRA_PHONE_STATE_FRX`, `EXTRA_PHONE_TYPE`, `EXTRA_TCU_MODE`.

### `com.mitsubishielectric.ada.appservice.voiceportalap.*` (14)

Voice recognition extras: `EXTRA_RECG_AUDIO_NAME`, `EXTRA_RECG_CALLHISTORY_DATE/NAME/TYPE`, `EXTRA_RECG_DISP`, `EXTRA_RECG_DISP_INDEX`, `EXTRA_RECG_LISTNUM`, `EXTRA_RECG_PHONETYPE_CATEGORY/NUMBER`, `EXTRA_RECG_PHONE_CATEGORIES`, `EXTRA_RECG_PHONE_CONTACT`, `EXTRA_RECG_STATE`, `EXTRA_RECG_WORD`, `GRAMMAR_KEY`.

### `com.mitsubishielectric.android.action.camera.*` (14) 🎯

`ACTION_MVC_CTM` · `DISP_LANEWATCH_CAUTION` · `EXIT_CORNER_CAMERA` · `EXIT_CORNER_CAMERA_SET` · `EXIT_DISPLAY_SET` · `EXIT_FRONT_CAMERA` · `EXIT_LANEWATCH` · `EXIT_LANEWATCH_CAUTION` · `EXIT_LANEWATCH_SET` · `EXIT_MVC` · `EXIT_MVC_SET` · **`EXIT_REAR_WIDE_CAMERA`** · `NOTIFY_COMMAND_RESULT_FROM_PSI` · `PAUSE_MVC`

### `com.mitsubishielectric.ada.app.dalauncher.*` (13)

`INFO_MENU` · `WallpaperChooserDialogFragment.EMBEDDED_KEY` · `action.ADD_APP` · `action.ANTITHEFT_RELEASE` · **`action.DISCLAIMER_COMPLETE`** · `action.ECO_START` · `action.INFO_CLOCK` · `action.INFO_MENU` · `action.INFO_TOP_ANIME` · `action.INFO_TOP_SCREEN_DISP` · `action.INFO_TOP_SCREEN_NO_DISP` · `action.NORMAL_STARTUP` · `action.PRECEDING_STARTUP`

### `com.mitsubishielectric.ada.app.headerservice.*` (12)

Header UI (top bar in the car): `ACTION_DISPLAY_NOTIFICATION`, `ACTION_HIDE_INTERRUPT_FAN_CLIMATE`, `ACTION_INTERRUPT_FAN_CLIMATE`, `ACTION_INTERRUPT_FILTER_ENTER/EXIT`, `ACTION_LAYOUT_CHANGED`, `ACTION_OVERWRITE_INTERRUPT_FAN_CLIMATE`, `ACTION_SCENE_ADVICE`, `ACTION_TOUCHES_VR`, `ACTION_VR_CALLBACK` (+ `_VALUE`), `CLOCK_ADJUST_CHANGED`.

### `com.mitsubishielectric.ada.app.CarPlay.*` (9)

`CarPlayModeActivity.FINISH` · `MainActivity.AUDIOSOURCE` · `MainActivity.CAUTIONSEL` · `MainActivity.CONNECTSTATUS` · `MainActivity.DEVICENAME` · `MainActivity.SERIALNUM` · `MainActivity.STARTFACTOR` · `MainActivity.STARTTYPE` · `MainActivity.URL`

### `com.mitsubishielectric.ada.app.avplayer.*` (9)

`AUDIO_SETTING` · `CHANGE_AUDIO_POWER` · `FINISH_AUDIO_SETTING` · `FINISH_SOUND_SETTING` · `FUNCTION_TOP` · `SHOW_SHORTCUT` · `SOUND_SETTING` · `SOURCE_POPUP` · `START_SERVICE`

### `com.mitsubishielectric.ada.app.dasettings.*` (9)

`CLOCK_SETTING` · `GROUND_SETTING_MESSAGE` · `MENU_AUDIO` · `MENU_INFO` · `MENU_PHONE` · `SETTINGS_TOP_ANIME` · `TEMP_SETTING` · `VR_SETTING` · `action.DISCLAIMER`

### `com.mitsubishielectric.ada.appservice.avapservice.*` (9)

`AUDIO_POWER_OFF` · `voiceportal.MUSIC_IPOD_INFO` · `voiceportal.MUSIC_TYPE` · `voiceportal.MUSIC_USB_INFO` · `voiceportal.REPLACE_INFO` · `voiceportal.STATION_SEARCH_RESULT` · `voiceportal.SXM_SEARCH_RESULT` · `voiceportalGET.MUSIC_BUNDLE_INFO` · `voiceportalSET.MUSIC_BUNDLE_INFO`

### `com.mitsubishielectric.ada.appservice.emergency.*` (9)

`ACTION_CHANGE_STATE_HELPNET` · `ACTION_COMMUNICATION_EXIT_REQUEST` · `EXTRA_KEY_E911_SETTING_START_TYPE` · `EXTRA_KEY_IS_CONTRACT` · `EXTRA_KEY_IS_SUPPORT` · `EXTRA_KEY_SETTING_TYPE` · `EXTRA_KEY_START_TYPE` · `EXTRA_KEY_STATE` · `EXTRA_KEY_TYPE`

### `com.mitsubishielectric.ada.app.androidauto.*` (8)

`ACTION_CUSTOM_DRIVING_OPERATION_INFO` · `ACTION_STATE_CHANGED` · `ACTION_VIDEO_FOCUS_NATIVE` · `EXTRA_ERROR` · `EXTRA_OLD_STATE` · `EXTRA_STATE` · `ui.ACTION_USB_DEVICE_ATTACHED` · `ui.ACTION_USB_DEVICE_PERMISSION`

### `com.mitsubishielectric.ada.app.hft.*` (8)

`ACTION_NOTIFY_PHONE_STATE_DELAYED` · `EXTRA_PHONE_MENU_ORIGIN` · `HFT_EXTRA_KEY_BT_SERVICE_REQUEST_ID` · `HFT_EXTRA_KEY_PAIRING_TYPE` · `HFT_EXTRA_KEY_TARGET_PROFILE` · `HftSettingHelpActivity.EXTRA_SETTING_MENU_ID` · `HftSettingHelpActivity.EXTRA_SETTING_MENU_NAME` · `HftSettingHelpActivity.EXTRA_SETTING_MENU_POS`

### `com.mitsubishielectric.ada.framework.speech.*` (7)

`EXTRA_BEGIN_OF_SPEECH_TIME_MILLS` · `EXTRA_END_OF_SPEECH_TIME_MILLS` · `EXTRA_RESULTS_USER_IDS` · `EXTRA_RESULTS_WORDS` · `EXTRA_RESULTS_WORD_ID` · `EXTRA_SPEECH_INPUT_LEADING_SILENCE_TIMEOUT_MILLIS` · `tts.TTS_USER_DICTIONARIES`

### `com.honda.displayaudio.navi.intent.*` (6)

`extra.ADDRESSINFO` · `extra.DATUM` · `extra.IDENTIFIER` · `extra.LAT` · `extra.LON` · `extra.NAME`

### `com.mitsubishielectric.ada.app.ecotripcomputer.*` (6)

`action.CURRENT_DRIVE_TAB_DISP` · `action.INFO_MENU_SCREEN_DISP` · `action.INFO_TOP_SCREEN_DISP` · `action.INFO_TOP_SCREEN_NO_DISP` · `action.INFO_TOP_SETTING_DISP` · `action.TRIPA_TAB_DISP`

### `com.mitsubishielectric.ada.appservice.acuralink.*` (6)

`ACTION_ACURALINK_START` · `ACTION_TCU_SYNC_COMPLETED` · `EXTRA_KEY_ACTIVITY_TYPE` · `EXTRA_KEY_CONTRACT` · `EXTRA_KEY_PHONE_NUMBER` · `EXTRA_KEY_STATE`

### `com.mitsubishielectric.ada.appservice.carplayapservice.*` (6)

`KEY_CALL_PRIMARY_CR/EMERGENCY_MODE/STATE` · `KEY_CALL_SECONDARY_CR/EMERGENCY_MODE/STATE`

### `com.honda.telematics.core.action.*` (5)

`EXECUTE_DIAG` · `EXECUTE_DOWNLOAD_POI` · `EXECUTE_LOCATION_UPLOAD_DISCLAIMER` · `EXECUTE_VR` · `RESPONSE_DIAG`

### `com.mitsubishielectric.ada.appservice.diag.*` (5)

`ACTION_HMI_INPUTHISTORY_BACKUP_COMPLETE` · `ACTION_HMI_INPUTHISTORY_LOCAL_BACKUP_COMPLETE` · `ACTION_HMI_LET_DIAG_STATE_CHANGED` · `EXTRA_FROM` · `EXTRA_HMI_LET_DIAG`

## Prefixes with <5 actions (21 prefixes, 42 actions)

- **`com.mitsubishielectric.ada.app.energymanagement.*`** (4): `action.INFO_MENU_SCREEN_DISP`, `action.INFO_TOP_SCREEN_DISP`, `action.INFO_TOP_SCREEN_NO_DISP`, `action.INFO_TOP_SETTING_DISP`
- **`com.mitsubishielectric.android.action.diag.*`** (4): `EXIT_CAMERA_SOURCE_ACTIVITY`, `EXIT_COLOR_BAR_ACTIVITY`, `EXIT_USER_OPERATION_ACTIVITY`, `NOTIFY_COMMAND_RESULT_FROM_PSI`
- **`com.mitsubishielectric.ada.action.voiceportal.*`** (3): `ACTION_CLOSE_ALL_VOICE_HELP_SCREEN`, `ACTION_VR_FINISH`, `ACTION_VR_MODE_NOTIFY`
- **`com.mitsubishielectric.ada.app.systeminfoservice.*`** (3): `ACTION_BRIGHTNESSBAR_DISMISS`, `ACTION_BRIGHTNESSBAR_SHOW`, `its.ETC_ACTION_PERIOD_OVER`
- **`com.mitsubishielectric.ada.app.systemupdate.*`** (3): `ACTION_SWUPDATE_COMPLETE_NOTIFY`, `ACTION_SYSTEM_UPDATE_DA_START`, `EXTRA_RESULT`
- **`com.mitsubishielectric.ada.appservice.hft.*`** (3): `Constants.ACTION_HFT_BLUETOOTH_DISCOVERY_FINISHED`, `Constants.ACTION_HFT_BLUETOOTH_DISCOVERY_STARTED`, `Constants.ACTION_HFT_BLUETOOTH_UUID`
- **`com.honda.telematics.core.extra.*`** (2): `PARAMS`, `RES_PARAMS`
- **`com.mitsubishielectric.ada.app.appmode.*`** (2): `AppModeMainActivity.STARTFACTOR`, `AppModeMainActivity.URL`
- **`com.mitsubishielectric.ada.appservice.clocksync.*`** (2): `ACTION_CLOCK_ADJUSTED`, `ACTION_CLOCK_UNADJUSTED`
- **`com.mitsubishielectric.ada.appservice.compassservice.*`** (2): `ACTION_COMPASS_LOG_START`, `ACTION_COMPASS_LOG_STOP`
- **`com.mitsubishielectric.ada.appservice.siriefm.*`** (2): `EXTRA_HMI_SIRIEFM_STATE`, `action.ACTIVITY_FINISH`
- **`com.mitsubishielectric.ada.appservice.unitinfomanager.*`** (2): `ACTION_HMI_FUNCTION_LIST_INIT`, `ACTION_ZIBA_FUNCTION_LIST_INIT`
- **`com.mitsubishielectric.ada.appservice.videomanager.*`** (2): `CAMERA_FINISH`, `CAMERA_START`
- **`com.mitsubishielectric. ada.app.avplayer.*`** (1): `REQUEST_AUDIO_FUNCTION` *(space in the prefix — likely a bug in the shipping build)*
- **`com.mitsubishielectric.ada.action.app.*`** (1): `dalauncher.CAMERA_STATUS_CHANGED`
- **`com.mitsubishielectric.ada.action.carplayapservice.*`** (1): `ACTION_CARPLAY_CALL_STATE_CHANGE`
- **`com.mitsubishielectric.ada.app.mirrorlink.*`** (1): `action.ADD_APP`
- **`com.mitsubishielectric.ada.app.usbcert.*`** (1): `action.USB_PERMISSION`
- **`com.mitsubishielectric.ada.appservice.sieriefm.*`** (1): `ACTION_HMI_SIRIEFM_STATE_CHANGED` *(note: "sieriefm" typo — coexists with `siriefm` above; two distinct prefixes)*
- **`com.mitsubishielectric.ada.header.UPDATE.*`** (1): action with no suffix
- **`com.mitsubishielectric.android.displayaudio.app.*`** (1): `aircon.extra.AIRCON_STATUS`

## Notes / rabbit holes

### Typos in the shipping build

They coexist side by side: `siriefm` and `sieriefm`, `Listner` and `Listener`, `Moniter` and `Monitor`, `Triger` and `Trigger`. For a safe bind, both must be considered.

### REQ/RES vs. push pattern

In `navi.action` there are three patterns:
- `REQ_*` / `RES_*` — call and response over broadcast (RPC)
- `GET_*` / `RETURN_*` — same, with query semantics
- `SET_*` — one-way
- `START_*` — activity launcher (opens the screen)
- `*_CHANGED` — push notification

### 1109 strings became 445 actions

The 664 filtered strings were class names with the vendor prefix. Raw dataset preserved in `/tmp/.../scratchpad/raio-x/all-mitsu-honda-strings.txt`.

## Suggested next steps

1. **AutoOk v0.5.0** — swap logcat polling for a listener of `com.mitsubishielectric.android.action.camera.EXIT_REAR_WIDE_CAMERA` + `com.mitsubishielectric.ada.appservice.powermanager.ACTION_RESUME_CAMERA`.
2. **Validate the canonicity of `DISCLAIMER_COMPLETE`** — decompile `DaLauncher.OpeningDivideActivity.onBackPressed` and `onBackFromDisclaimer` to see whether it's also emitted on a programmatic tap.
3. **Catalog the extras** of each action — today we only have the name. Decompile the receiver to extract the extras in use — that's Layer 2.
