# Raio-X da Central Mitsubishi/Honda — Camada 1 (Scan de Superfície)

**Data:** 2026-10-19
**Metodologia:** deodex com baksmali 2.5.2 → grep bytecode + parsing de `AndroidManifest.xml` binário (`strings -el`) → consolidação em tabelas → verificação por amostragem via REA (JADX 0.7.1).
**Alvo:** dump raw `0040` (safra BR `1.F187.16`): `vendor-app/` (78), `system-app/` (42), `system-priv-app/` (0), `vendor-framework/` (104 jars/odex). Total: **160 projetos smali** gerados em bloco.

Este raio-x é o "schema" da plataforma: lista o que **existe**, não o que **cada coisa faz**. Os aprofundamentos (Camada 2) consultam estes documentos como ponto de partida.

## Os 5 scans

| # | Arquivo | O que mapeia | Contagem |
|---|---|---|---|
| 1 | [`01-apis-aidl.md`](01-apis-aidl.md) | Interfaces binder internas (contratos IPC) | **364 interfaces únicas** |
| 2 | [`02-broadcasts.md`](02-broadcasts.md) | Actions com prefixo `com.mitsubishielectric.*` / `com.honda.*` referenciadas em bytecode | **445 actions distintas em 48 prefixos** |
| 3 | [`03-content-providers.md`](03-content-providers.md) | ContentProvider authorities e URIs | **27 authorities, 52 URIs** (9 vendor) |
| 4 | [`04-system-properties.md`](04-system-properties.md) | SystemProperties lidas/escritas no shipping | **48 propriedades em 4 prefixos** |
| 5 | [`05-trust-map.md`](05-trust-map.md) | Mapa de confiança: `sharedUserId`, package, permissões por APK | **110 APKs, 11 com `android.uid.system`** |

## Alto nível — o que o raio-x revela

### A plataforma é majoritariamente IPC

Os 364 binder interfaces (muitos com `*Listener`/`*Callback` espelhando async) mostram que a arquitetura é **mediator-based**: cada capability do carro (navegação, audio, câmera, HFT, voice, telematics, strg sw, vehicle info, etc) tem um `ApService` próprio com AIDL público. Qualquer app que roda com UID adequado pode fazer bind e consumir.

**Implicação pra nós:** adicionar features ao AutoOk pelo caminho oficial é "escolher a AIDL certa, fazer bind, consumir". É muito mais limpo do que `logcat polling` + `input tap` que usamos hoje — contudo exige que entendamos cada AIDL individualmente (próximas fases).

### Os 445 broadcasts são o fluxo de controle principal

33 APKs já conhecidos escutam `ACTION_HMI_SERVICE_START`. Mas tem muito mais contrato pub/sub: 38 actions só do PowerManager, 40 só do Honda navi, 34 do HFT, 24 do system Honda. O MAPA já tinha o essencial do PowerManager; agora temos a planilha inteira.

### Só 11 APKs rodam como `android.uid.system`

A whitelist implícita de "quem pode fazer tudo" é curta — e já conhecemos todos os nomes (ver §05). Isso valida que `/system/app/` tem baixo custo de inclusão para apps nossos, mas que para capabilities privilegiadas precisa escolher receiver/intent certo (não há "virar system" por mágica — é o manifest + sharedUserId no build).

### Dados estruturados do veículo moram em 9 ContentProviders

Além da já mapeada whitelist (`com.honda.displayaudio.whitelist`), existem providers de **telematics CRM** (`com.honda.telematics.core.crm`), **download POI** (`com.honda.telematics.core.downloadpoiprovider`), **telema info** (`com.honda.displayaudio.system.telemainfo.telemainfoprovider`), **launcher favorites** (duas tabelas), **HFT phonebook/photo** (duas tabelas), e o adapter da **Clarion LinkManager**.

### A superfície de system properties é pequena e nomeada

Só 48 props são referenciadas em bytecode, destas as HMI-específicas são 4: `sys.hmi_service_started`, `sys.hmi_service_start_cause`, `sys.hmi_service_keyoff`, `sys.hmi_reboot_reservation`. Resto é AOSP padrão (`ro.build.*`, `net.*`, `persist.radio.*`).

## Como foi coletado (reprodutível)

```bash
BULK=/tmp/.../scratchpad/bulk-smali   # dir temporário desta sessão
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

Depois os greps/awks de cada scan sobre `$BULK/**/*.smali` + `unzip -p AndroidManifest.xml | strings -el` sobre os APKs. Tempo total ~5 min no hardware atual.

**Os datasets brutos** (listas completas, não cabem nos docs) ficaram em `/tmp/.../scratchpad/raio-x/`: `aidl-unique.txt`, `actions-vendor.txt`, `content-uris.txt`, `sysprops-clean.txt`, `apk-permissions-uses.txt`, `apk-pkg-shareduid.txt`. Como é scratchpad, somem no fim da sessão — se quisermos manter no repo, o próximo passo é copiar pra `tooling/raio-x/data/` (não feito nesta rodada).

## Limites conhecidos

- **`strings -el` sobre AXML binário** detecta ~67/110 packages. Nos 43 restantes, o nome do pacote fica embaraçado com `com.mitsubishielectric.uilib` (uses-library) ou é "?" por limitação do strings/AXML. Para análise definitiva por APK, usar REA `inspect-android-package` individual — ver §01 do MAPA §20.8.
- **Reflexão / dynamic class loading** não é capturado. Alguns `SystemProperties.get(...)` com nome montado por `StringBuilder` ficam fora do scan 4.
- **Prefixos de actions não são 100% canônicos** — `com.mitsubishielectric.android.action.camera.*` e `com.mitsubishielectric.ada.*` convivem; o scan agrupa pelo prefix bruto, não normaliza.
- **`system-priv-app/` estava vazio no dump** — se existir no futuro, re-executar o pipeline cobre.

## Para onde isso aponta (Camada 2, candidatos)

Hierarquizados por valor imediato pro projeto:

1. **Camera** — a AIDL `IRearWideCameraDisplay` + actions `com.mitsubishielectric.android.action.camera.*` são o caminho correto pra substituir o logcat-polling de ré no AutoOk v0.4.0. Fase 9 natural.
2. **Diag** (DealerDiag, DeveloperDiag, PreShipmentDiag, LetDiag) — tipicamente carregam PINs, modos de serviço, menus escondidos. Alto potencial de Easter egg.
3. **Vehicle** (VehicleRW, VehicleInfoManager, VehicleDbManager — 55 interfaces AIDL) — lá mora a leitura/escrita de CAN. Fase 10+, risco alto se escrever.
4. **StrgSW** — mapeamento dos botões físicos do volante. Baixo custo, útil pra hooks diretos.
5. **AV + MediaCoreService** — pipeline de áudio, roteamento. Potencial de bypass de ducking (áudio nosso não baixar com voz Honda).

Nenhum destes está escopado para esta sessão.
