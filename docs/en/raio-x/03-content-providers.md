# Scan 3 — ContentProviders

**27 unique authorities, 52 specific URIs.** These are every point where an app can call `ContentResolver.query/openAssetFileDescriptor` to read structured data from the platform.

## How it was collected

```bash
grep -rhoE 'const-string .*"content://[^"]+"' bulk-smali/*/ \
  | grep -oE '"content://[^"]+"' \
  | sort -u
```

Then extract the authority (first segment after `content://`).

**Limits:** URIs built via `Uri.Builder` or `Uri.withAppendedPath(baseUri, …)` are not captured if `baseUri` isn't a literal. Applies to most AOSP media providers (which do base + path).

## Authorities by category

### Vendor Mitsubishi/Honda (9 authorities — what matters to us)

| Authority | Provider APK (inferred) | Role |
|---|---|---|
| **`com.honda.displayaudio.whitelist`** 🎯 | `com.honda.displayaudio.whitelist.apk` (/system/vendor/etc/honda/) | Delivers the ZIP containing `whitelist-1.0.xml` to the `WhitelistApService`. Only documented URI: `/1.0`. See [`whitelist-mitsubishi-2026-10-19.md`](../whitelist-mitsubishi-2026-10-19.md) |
| **`com.honda.displayaudio.system.telemainfo.telemainfoprovider`** | part of the telemainfo stack | "Thema" info (telematics? model?); paired AIDL is `ITelemaInfoService` |
| **`com.honda.telematics.core.crm`** | `com.honda.telematics.core.apk` | URI `/let_data` — dealer Customer Relationship Management. Contract data, visits, maintenance history. Protected by permission `com.honda.telematics.core.permission.WRITE_CRM_DATA` |
| **`com.honda.telematics.core.downloadpoiprovider`** | same | URI `/downloadpoi` — point-of-interest (POI) download. Feeds the navigator with POIs coming from telematics |
| **`com.mitsubishielectric.ada.app.dalauncher.settings`** | `DaLauncher.apk` | Persistent launcher settings: `/appWidgetReset`, `/favorites_hgw` (home-general-widget?), `/favorites_ziba` (internal name for another launcher theme). With `?notify=true/false` flag controls the ChangeObserver broadcast |
| **`com.mitsubishielectric.ada.appservice.appmanagerservice.provider`** | `AppManager.apk` | DB of "official" apps. Probably feeds the app-manager UI with `IAppManagerService` (see §01.`appmanagerservice`) |
| **`com.mitsubishielectric.ada.appservice.hft.localprovider`** | `HftApService.apk` | Local PhoneBook: `/PhoneBook`. Cache of contacts from the paired phone |
| **`com.mitsubishielectric.ada.appservice.hft.provider`** | same | Contact photos: `/HftPhotoData`. Separate from PhoneBook for large photos |
| **`com.clarion.linkmanager.linkprovider.LinkContentProvider`** | Clarion (OEM link manager) | Interface of the Clarion LinkManager subsystem (integration point between AOSP and Clarion proprietary SW for external linking) |

### AOSP (18 authorities)

Standard Android (non-vendor-specific), listed for completeness:

```
com.android.browser.home              com.android.browser.snapshots
com.android.calendar                  com.android.contacts
com.android.contacts.dumpfile         com.android.deskclock
com.android.gallery3d.filtershow.provider.SharedImageProvider
com.android.gallery3d.provider        com.android.htmlfileprovider
com.google.android.partnersetup.rlzappprovider
com.google.settings
contacts        icc        media        mms-sms        settings        sms
telephony
```

## Full URIs (52)

### Vendor (highlights)

| URI | What it reads/writes |
|---|---|
| `content://com.honda.displayaudio.whitelist/1.0` | AssetFileDescriptor → ZIP with `whitelist-1.0.xml` |
| `content://com.honda.displayaudio.system.telemainfo.telemainfoprovider` | no path — probably returns the single row/dataset |
| `content://com.honda.telematics.core.crm/let_data` | Customer data |
| `content://com.honda.telematics.core.downloadpoiprovider/downloadpoi` | POI download queue/history |
| `content://com.mitsubishielectric.ada.app.dalauncher.settings/` | root — probably lists the "tables" |
| `content://com.mitsubishielectric.ada.app.dalauncher.settings/appWidgetReset` | resets widget positions on the home screen |
| `content://com.mitsubishielectric.ada.app.dalauncher.settings/favorites_hgw?notify=false` | favorites list for the HGW theme, without firing an observer |
| `content://com.mitsubishielectric.ada.app.dalauncher.settings/favorites_hgw?notify=true` | same, but fires an observer |
| `content://com.mitsubishielectric.ada.app.dalauncher.settings/favorites_ziba?notify=false` | Ziba theme favorites, silent |
| `content://com.mitsubishielectric.ada.app.dalauncher.settings/favorites_ziba?notify=true` | Ziba with notify |
| `content://com.mitsubishielectric.ada.appservice.appmanagerservice.provider` | root |
| `content://com.mitsubishielectric.ada.appservice.hft.localprovider/` | root |
| `content://com.mitsubishielectric.ada.appservice.hft.localprovider/PhoneBook` | cached contacts |
| `content://com.mitsubishielectric.ada.appservice.hft.provider/` | root |
| `content://com.mitsubishielectric.ada.appservice.hft.provider/HftPhotoData` | contact photos |
| `content://com.clarion.linkmanager.linkprovider.LinkContentProvider` | root |

### AOSP (typical, documented use)

```
content://com.android.browser.home/
content://com.android.browser.home/res/raw/
content://com.android.browser.snapshots
content://com.android.calendar/events
content://com.android.calendar/time/
content://com.android.contacts/contacts/lookup/
content://com.android.contacts.dumpfile
content://com.android.deskclock/alarm
content://com.android.gallery3d.filtershow.provider.SharedImageProvider/image
content://com.android.gallery3d.provider
content://com.android.htmlfileprovider
content://com.google.android.partnersetup.rlzappprovider/
content://com.google.settings/partner
content://contacts/groups
content://contacts/people
content://contacts/people/
content://icc/adn
content://icc/fdn
content://icc/sdn
content://media
content://media/
content://media/external
content://media/external/audio/albumart
content://media/external/audio/albums/
content://media/external/audio/artists/
content://media/external/audio/media/
content://media/external/audio/search/fancy/
content://media/external/fs_id
content://media/external/video/media
content://media/none/mtp_connected
content://mms-sms/conversations/
content://settings/old_favorites?notify=true
content://sms
content://sms/icc
content://telephony/carriers/preferapn
content://telephony/carriers/restore
```

## Notes

### "Hgw" and "Ziba"

Two launcher visual theme names: `favorites_hgw` and `favorites_ziba`. Probably UI themes that can be swapped (see the `favorites_*` table in the launcher settings). "Ziba" is in fact referenced in DaLauncher animation smali (e.g. `home_pageupdown_blink_ziba.xml`, seen in the DaLauncher resources scan 1).

**Opportunity:** if there's more than one theme, there must be a knob to switch it. It could be via `DaSettings.apk` or straight through a settings content URI.

### HFT has two separate providers

- `localprovider` — PhoneBook (text, small, fast)
- `provider` — PhotoData (binary, large, can be slow)

Good separation to allow independent cache invalidation.

### The Honda whitelist carries a version in the URI (`/1.0`)

Suggests planning ahead for schema versioning. Today only `/1.0` exists — if a `/2.0` ever appears, it would most likely be a parallel compatible break.

### CRM and POI come from telematics (US/Acura firmware)

`com.honda.telematics.core.*` are **US firmware** (Acura Link). On BR they are probably installed but inactive (no TCU contract). Worth confirming — it is a large dataset and may contain test PII.

## Suggested next steps

Two immediate targets:

1. **`com.mitsubishielectric.ada.app.dalauncher.settings`** — if it exposes a favorites schema, we could populate it with a shortcut to AutoOk without going through the standard install.
2. **`com.honda.displayaudio.whitelist/1.0`** — Route B from the earlier analysis (see [`whitelist-mitsubishi-2026-10-19.md`](../whitelist-mitsubishi-2026-10-19.md) §7.2). To replace the carrier APK we need to know the exact ContentProvider schema — low cost via `dumpsys content provider com.honda.displayaudio.whitelist`.
