# Scan 3 — ContentProviders

**27 authorities únicos, 52 URIs específicos.** São todos os pontos onde um app pode fazer `ContentResolver.query/openAssetFileDescriptor` para ler dados estruturados da plataforma.

## Como foi coletado

```bash
grep -rhoE 'const-string .*"content://[^"]+"' bulk-smali/*/ \
  | grep -oE '"content://[^"]+"' \
  | sort -u
```

Depois extração do authority (primeiro segmento após `content://`).

**Limites:** URIs construídos via `Uri.Builder` ou `Uri.withAppendedPath(baseUri, …)` não são capturados se o `baseUri` não é literal. Vale para a maior parte dos provedores AOSP de media (que fazem base + path).

## Authorities por categoria

### Vendor Mitsubishi/Honda (9 authorities — o que importa pra nós)

| Authority | APK provedor (inferido) | Função |
|---|---|---|
| **`com.honda.displayaudio.whitelist`** 🎯 | `com.honda.displayaudio.whitelist.apk` (/system/vendor/etc/honda/) | Entrega o ZIP com `whitelist-1.0.xml` para o `WhitelistApService`. Único URI documentado: `/1.0`. Ver [`whitelist-mitsubishi-2026-10-19.md`](../whitelist-mitsubishi-2026-10-19.md) |
| **`com.honda.displayaudio.system.telemainfo.telemainfoprovider`** | parte do stack telemainfo | Info de "tema" (telemática? modelo?); AIDL emparelhada é `ITelemaInfoService` |
| **`com.honda.telematics.core.crm`** | `com.honda.telematics.core.apk` | URI `/let_data` — Customer Relationship Management do dealer. Dados de contrato, visitas, histórico de manutenção. Protegido por permissão `com.honda.telematics.core.permission.WRITE_CRM_DATA` |
| **`com.honda.telematics.core.downloadpoiprovider`** | idem | URI `/downloadpoi` — download de pontos de interesse (POI). Alimenta o navegador com POIs vindos do telematics |
| **`com.mitsubishielectric.ada.app.dalauncher.settings`** | `DaLauncher.apk` | Settings persistentes do launcher: `/appWidgetReset`, `/favorites_hgw` (home-geral-widget?), `/favorites_ziba` (nome interno de outro tema do launcher). Com flag `?notify=true/false` controla broadcast de ChangeObserver |
| **`com.mitsubishielectric.ada.appservice.appmanagerservice.provider`** | `AppManager.apk` | DB de apps "oficiais". Provavelmente alimenta a UI de app manager com `IAppManagerService` (ver §01.`appmanagerservice`) |
| **`com.mitsubishielectric.ada.appservice.hft.localprovider`** | `HftApService.apk` | PhoneBook local: `/PhoneBook`. Cache de contatos do telefone pareado |
| **`com.mitsubishielectric.ada.appservice.hft.provider`** | idem | Fotos de contatos: `/HftPhotoData`. Separado do PhoneBook pra fotos grandes |
| **`com.clarion.linkmanager.linkprovider.LinkContentProvider`** | Clarion (link manager OEM) | Interface do subsistema Clarion LinkManager (ponto de integração entre AOSP e SW proprietário Clarion para linking externo) |

### AOSP (18 authorities)

Padrão Android padrão (não vendor-specific), listado para completeness:

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

## URIs completos (52)

### Vendor (destaque)

| URI | O que pede/escreve |
|---|---|
| `content://com.honda.displayaudio.whitelist/1.0` | AssetFileDescriptor → ZIP com `whitelist-1.0.xml` |
| `content://com.honda.displayaudio.system.telemainfo.telemainfoprovider` | sem path — provavelmente retorna o único row/dataset |
| `content://com.honda.telematics.core.crm/let_data` | Customer data |
| `content://com.honda.telematics.core.downloadpoiprovider/downloadpoi` | POI download queue/history |
| `content://com.mitsubishielectric.ada.app.dalauncher.settings/` | root — provavelmente lista as "tabelas" |
| `content://com.mitsubishielectric.ada.app.dalauncher.settings/appWidgetReset` | reseta posição de widgets do home |
| `content://com.mitsubishielectric.ada.app.dalauncher.settings/favorites_hgw?notify=false` | lista de favoritos do tema HGW, sem disparar observer |
| `content://com.mitsubishielectric.ada.app.dalauncher.settings/favorites_hgw?notify=true` | mesmo, mas dispara observer |
| `content://com.mitsubishielectric.ada.app.dalauncher.settings/favorites_ziba?notify=false` | favoritos do tema Ziba, silent |
| `content://com.mitsubishielectric.ada.app.dalauncher.settings/favorites_ziba?notify=true` | Ziba com notify |
| `content://com.mitsubishielectric.ada.appservice.appmanagerservice.provider` | root |
| `content://com.mitsubishielectric.ada.appservice.hft.localprovider/` | root |
| `content://com.mitsubishielectric.ada.appservice.hft.localprovider/PhoneBook` | contatos cacheados |
| `content://com.mitsubishielectric.ada.appservice.hft.provider/` | root |
| `content://com.mitsubishielectric.ada.appservice.hft.provider/HftPhotoData` | fotos de contatos |
| `content://com.clarion.linkmanager.linkprovider.LinkContentProvider` | root |

### AOSP (uso típico, documentado)

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

## Observações

### "Hgw" e "Ziba"

Dois nomes de temas visuais do launcher: `favorites_hgw` e `favorites_ziba`. Provavelmente temas da UI que podem ser alternados (ver tabela `favorites_*` do launcher settings). "Ziba" é inclusive referenciado em smali de animações no DaLauncher (ex: `home_pageupdown_blink_ziba.xml`, visto no scan 1 de resources do DaLauncher).

**Oportunidade:** se existe mais de um tema, deve haver um knob para trocar. Pode ser via `DaSettings.apk` ou direto via content URI de settings.

### HFT tem dois provedores separados

- `localprovider` — PhoneBook (texto, pequeno, bate rápido)
- `provider` — PhotoData (binário, grande, pode ser lento)

Boa separação pra permitir cache invalidation independente.

### A whitelist Honda tem versão no URI (`/1.0`)

Isso sugere planejamento futuro para versioning do schema. Hoje só existe `/1.0` — se virasse `/2.0`, provavelmente seria um breaking change compatível em paralelo.

### CRM e POI vêm do telematics (safra US/Acura)

`com.honda.telematics.core.*` são **safra US** (Acura Link). No BR provavelmente estão instalados mas inativos (sem contrato TCU). Vale confirmar — é um dataset grande e pode conter PII de teste.

## Próximos passos sugeridos

Dois alvos imediatos:

1. **`com.mitsubishielectric.ada.app.dalauncher.settings`** — se expõe schema de favoritos, dá para popular com atalho pro AutoOk sem passar pelo install padrão.
2. **`com.honda.displayaudio.whitelist/1.0`** — Rota B da análise anterior (ver [`whitelist-mitsubishi-2026-10-19.md`](../whitelist-mitsubishi-2026-10-19.md) §7.2). Para substituir o APK portador precisa saber a estrutura exata do ContentProvider dele — baixo custo via `dumpsys content provider com.honda.displayaudio.whitelist`.
