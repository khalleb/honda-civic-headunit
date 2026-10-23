# Fase 10 — Decisão de rota: Rota B (resign AOSP)

> Decisão tomada em 2026-10-23 após análise do `AndroidManifest.xml` do DaLauncher
> e do `/system/etc/permissions/com.mitsubishielectric.ada.util.vehiclerw.lib.xml`.
> Rota A (odex patch) foi descartada por complexidade adicional sem ganho real.

## Objetivo

Escolher entre as duas rotas de deploy pré-planejadas em
[`fase10-pre-planejamento-2026-10-20.md`](fase10-pre-planejamento-2026-10-20.md)
para aplicar o patch smali que desabilita o aviso de partida.

- **Rota A:** odex-level patch, APK fica intocado com assinatura Mitsubishi original.
- **Rota B:** resign com testkey AOSP, DaLauncher vira "new install".

## Análise do manifesto do DaLauncher

Fonte: `tooling/apks-decoded/DaLauncher/AndroidManifest.xml` (deodex local via
`tooling/deodex/deodex-apk.sh`).

### Pontos verificados

| Checagem | Resultado |
|---|---|
| `android:sharedUserId` | **ausente** — não há UID compartilhado a quebrar |
| `android:process` da `<application>` | padrão (próprio processo do pacote) |
| 18× `uses-library` Mitsubishi | não dependem de signature matching |
| Permissions declaradas pelo próprio APK | privileged, dangerous, normal (nenhuma signature-pura usada por terceiros) |

### Permissions requeridas (uses-permission)

| Permission | Nível | Comportamento sob testkey AOSP |
|---|---|---|
| `com.mitsubishielectric.ada.permission.VEHICLE_RW` | **GID-only** (`<group gid="vehicle_rw"/>`, sem `protectionLevel`) | ✅ Grant por declaração, não por signature |
| `android.permission.CALL_PHONE` | dangerous | ✅ Grant automático em /system |
| `android.permission.SET_WALLPAPER`, `SET_WALLPAPER_HINTS` | normal | ✅ |
| `android.permission.VIBRATE` | normal | ✅ |
| `android.permission.BIND_APPWIDGET` | `signature\|system` | ✅ `\|system` cobre (APK em /system/vendor/app) |
| `android.permission.GET_ACCOUNTS` | normal | ✅ |
| `android.permission.ACCESS_FINE_LOCATION` | dangerous | ✅ |
| `android.permission.GET_TASKS` | `normal` em API 17 | ✅ |
| Launcher permissions próprias (`READ_SETTINGS`, etc.) | normal/dangerous | ✅ |

### Achado crítico: VEHICLE_RW não é signature-level

A permission mais sensível do DaLauncher é a Mitsubishi `VEHICLE_RW`. O arquivo
`/system/etc/permissions/com.mitsubishielectric.ada.util.vehiclerw.lib.xml`
declara ela **sem `protectionLevel`**, apenas associando ao grupo UNIX
`vehicle_rw`:

```xml
<permission name="com.mitsubishielectric.ada.permission.VEHICLE_RW">
    <group gid="vehicle_rw" />
</permission>
<library name="com.mitsubishielectric.ada.util.vehiclerw.lib" file="/vendor/framework/VehicleRW.jar"/>
```

Esse padrão (do `platform.xml` do AOSP) é usado para permissions que mapeiam
diretamente para GIDs UNIX. O APK recebe o grupo `vehicle_rw` no processo pelo
simples fato de declarar `uses-permission`. **Signature não entra no gating.**

## Risco secundário (hipótese a confirmar no deploy — não-bloqueador)

Resign com testkey AOSP faz `checkSignaturesLP` falhar no PackageManager:

1. `packages.xml` tem a signature Mitsubishi original (`93:14:CE:...:05:AD`)
2. APK novo tem signature testkey AOSP (`A4:0D:A8:...:F5:DC`)
3. Mismatch esperado no primeiro boot pós-deploy

**O que o PackageManager faz a seguir é hipótese, não fato verificado nesta safra
Mitsubishi 4.2.2.** O caminho padrão do AOSP 4.2 para system app com signature
divergente é `deletePackageLI` + `scanPackageLI`/`SCAN_NEW_INSTALL` — aceita o APK
novo, re-registra a signature e apaga `/data/data`. Mas existe o caminho alternativo
`INSTALL_FAILED_UPDATE_INCOMPATIBLE`, que desabilitaria o launcher. Qual dos dois esta
recovery toma **só se confirma no carro** — por isso o rollback é obrigatório e o
deploy é gated.

Impacto operacional **se** o caminho for o esperado:

- **Perdem-se os dados em `/data/data/com.mitsubishielectric.ada.app.dalauncher/*`** — SharedPreferences (wallpaper configurado, ícones reorganizados), bancos de dados internos, caches. Launcher recria defaults no primeiro boot pós-deploy.
- **Primeiro boot ~10-30s mais lento** — Dalvik precisa `dexopt` do `classes.dex` novo (que vem embutido no APK rebuildado, não mais no `.odex` sibling).

Nenhum dos dois efeitos é bloqueador no nosso contexto (sem wallpaper custom
nem reorganização de ícones).

Nota: o APK do AutoOk em produção é assinado com a **debug.keystore** do dev
(`CN=Android Debug`, SHA `95:05:DE:...:CF:02`), **não** com o testkey AOSP. O testkey
AOSP (`A4:0D:A8:...:F5:DC`) é o que assina os pacotes OTA (`SwUpdate.mdt`) e passa a
assinar também o DaLauncher patcheado.

## Decisão

**Rota B.** Rota A traz complexidade real (re-odex em host, sem ferramenta
oficial AOSP para Dalvik 4.2.2 ARM) sem ganho concreto. Rota B:

- Reutiliza o tooling de build já validado (apksigner, pacote OTA EvilValet assinado com testkey AOSP, `build.py` style)
- Não quebra permission alguma (análise acima)
- Risco limitado a `/data/data` do launcher — recuperável automaticamente

## Requisitos operacionais do pacote OTA de instalação (`build-dalauncher-fase10.py`)

O pacote OTA que entregar o DaLauncher patcheado precisa:

1. **Substituir `/system/vendor/app/DaLauncher.apk`** pela versão rebuildada+assinada com testkey AOSP (inclui `classes.dex` modificado). O `build-dalauncher-fase10.py` verifica, antes de empacotar, que o APK está assinado com o testkey AOSP esperado (`apksigner verify`) — aborta se não.
2. **Deletar `/system/vendor/app/DaLauncher.odex`** antes do primeiro boot pós-deploy. Se mantiver, o Dalvik pode carregar bytecode antigo com fingerprint do APK novo e crashar. A remoção **não pode ser mascarada**: o updater-script faz `rm` + `test ! -e` e grava no pendrive `FASE10-ODEX-REMOVED.OK` (sucesso) ou `FASE10-ODEX-REMOVED.FAIL` (o `.odex` persistiu). Não aborta o script (senão travaria o loop do loop-break), mas deixa o resultado inequívoco — o deploy day é gated nesse flag.
3. **Montar `/system` + `/system/vendor`** (DaLauncher mora em `CAP`, não `APP`).
4. **Loop break obrigatório** — `mv SwUpdate2.txt .done` + `rm /cache/.copy_complete` antes do sleep final, senão `daupdater` reaplica em loop.
5. **Logar md5 do APK** no pendrive para auditoria.

## Rollback pronto antes de executar

[`tooling/ota-build/build-dalauncher-restore.py`](../tooling/ota-build/build-dalauncher-restore.py)
restaura os bytes originais vindos do dump textual de 2026-10-17
(`tooling/apks-dumped/dump-0040/vendor-app/DaLauncher.{apk,odex}`), validados
por sha256 na hora do build:

- `DaLauncher.apk`: `1d8bd729ad309240bc77c6c2d5f9a93c07940cc355d4adbed9930ee6d9cee019`
- `DaLauncher.odex`: `1497dc8497799faf8e86fe8f90fede54dd98502472f1c3e03b82b4542eb57db7`

Rollback **tem que ser construído e aplicado no carro antes do deploy do pacote
patcheado**. Aplicar o rollback sobre o DaLauncher original esperado é no-op
(mesmos bytes sendo escritos sobre eles mesmos) — isso valida que o rollback
funciona antes de precisar dele de verdade.

## Referências cruzadas

- [`fase10-pre-planejamento-2026-10-20.md`](fase10-pre-planejamento-2026-10-20.md) — briefing técnico original
- [`MAPA.md § 11.1.1`](MAPA.md) — OpeningDivideActivity internals
- [`MAPA.md § 17.16`](MAPA.md) — gate do disclaimer descoberto
- [`raio-x/05-trust-map.md`](raio-x/05-trust-map.md) — permissões do DaLauncher
- [`../tooling/apks-decoded/DaLauncher-deodexed/`](../tooling/apks-decoded/) — smali local
- [`../tooling/ota-build/build-dalauncher-restore.py`](../tooling/ota-build/build-dalauncher-restore.py) — pacote de rollback
