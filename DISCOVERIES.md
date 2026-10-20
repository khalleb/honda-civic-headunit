# Descobertas técnicas

> Índice navegável dos achados sobre a central Mitsubishi Andromeda / Honda Civic G10, feitos ao longo das fases do projeto. Cada item linka pro doc denso onde a evidência está.
>
> Isto não é tutorial. Pra deployar na sua central, [`QUICKSTART.md`](QUICKSTART.md). Pra entender o estado atual + próximos passos, [`ROADMAP.md`](ROADMAP.md). Pra ver o atlas completo da central (partições, APKs, services, pipeline), [`docs/MAPA.md`](docs/MAPA.md).

## Plataforma (como ela funciona por dentro)

Mapeamento estático completo feito via REA + JADX sobre 160 APKs/libs do dump 0040. Os datasets são reutilizáveis pra qualquer central Mitsubishi Andromeda com mesmo framework.

| O que | Quantidade | Doc |
|---|---|---|
| Interfaces AIDL (binder internas) | 364 em 63 domínios | [`docs/raio-x/01-apis-aidl.md`](docs/raio-x/01-apis-aidl.md) |
| Broadcasts `com.mitsubishielectric.*` / `com.honda.*` | 445 em 48 prefixos | [`docs/raio-x/02-broadcasts.md`](docs/raio-x/02-broadcasts.md) |
| ContentProviders (authorities) | 27 (9 vendor + 18 AOSP) | [`docs/raio-x/03-content-providers.md`](docs/raio-x/03-content-providers.md) |
| System properties referenciadas | 48 | [`docs/raio-x/04-system-properties.md`](docs/raio-x/04-system-properties.md) |
| APKs do shipping (vendor + system) | 110 (11 com `android.uid.system`) | [`docs/raio-x/05-trust-map.md`](docs/raio-x/05-trust-map.md) |

## PowerManager — como a central realmente se recupera de LP0

O PowerManager Mitsubishi **não mantém lista** de serviços HMI. Ele é pub/sub puro: emite 16 broadcasts em pontos chave do ciclo de power, qualquer app com receiver registrado participa.

- **16 broadcasts do `PowerManagerBroadcastSender`** mapeados (start, stop, pre-stop, restart + 10 variantes de parada por fase + resume camera + animation + VBUS)
- **33 APKs do shipping** escutam `ACTION_HMI_SERVICE_START` — é o contrato universal
- **Causas conhecidas de startup**: `"ColdBoot"`, `"ExitLP0"`, `"AccOnRestart"`
- **Nossa v0.4.0 do AutoOk** usa esse pattern (`HmiServiceReceiver`) — é o jeito oficial, não workaround

→ [`docs/MAPA.md` §11.6](docs/MAPA.md), [`docs/whitelist-mitsubishi-2026-10-19.md` §6](docs/whitelist-mitsubishi-2026-10-19.md)

## Whitelist Mitsubishi — fluxo completo

A "whitelist Mitsubishi" aparece em várias análises de projetos vizinhos (ex: `codeage/root-honda`) como mecanismo de controle, mas **ela é só UX de instalação de apps**. Só `AppManager.apk` (gerenciador oficial) e `FileManager.apk` consomem via binder. Nenhum HMI service, nenhum PowerManager a consulta.

Mapeado em detalhe:
- APK shell: `com.mitsubishielectric.ada.appservice.whitelist` (roda como `android.uid.system`)
- Lógica real: `WhitelistLib.jar` em `vendor-framework/` (15 classes)
- APK portador do XML: `com.honda.displayaudio.whitelist.apk` (14 KB, em `/system/vendor/etc/honda/`)
- XML em runtime: `/data/data/whitelist-1.0.xml`
- Interface AIDL com 7 métodos: `checkInstallPackage`, `getPackageNames`, `getApplicationName`, `getAudioInfo`, `getAudioStreamType`, `getRegulation`, `getRevert`
- Formato do XML (`<package>`, `<keyStore>`, `<versionCode>`, `<regulation>`, `<revert>`, `<audioStreamType>`, `<withAudio>`) totalmente mapeado

→ [`docs/whitelist-mitsubishi-2026-10-19.md`](docs/whitelist-mitsubishi-2026-10-19.md)

## Fluxo do aviso (`OpeningDivideActivity`) por dentro

O aviso que o projeto suprime é lançado por `com.mitsubishielectric.ada.app.dalauncher.Launcher$HMIServiceReceiver.onReceive()` ao receber o broadcast `ACTION_HMI_SERVICE_START` do PowerManager.

- Activity principal: `com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity` (extends `HomeBaseActivity`)
- Layout: `R.layout.opening_divide`
- 14 classes referenciam a Activity (confirmado via `trace-android-references`)
- 19 fields, 37 métodos públicos mapeados (incluindo `startNextActivity`, `createDisclaimerOnHomeIntent`, `antiTheftUnlockScreenTransition`)
- `onCreate` decompilado — a lógica de "aceitou/não aceitou" vive em `DisclaimerFragment`

→ [`docs/MAPA.md` §11.1.1](docs/MAPA.md)

## Hall of fame de bugs resolvidos

14 bugs com causa raiz identificada e fix documentado — valioso pra quem está começando em RE Mitsubishi ou pra outros projetos adjacentes.

Destaques:
- **Needle do logcat com `.` vs `/`** — Activity Manager imprime `pkg/.ClassName`, não `pkg.ClassName`
- **APK morre após 1º tap** — `stopSelf()` após o tap matava o Service; precisa `rearmWatcher()`
- **Rom_type `0040` descoberto por trial-and-error** — 352 pacotes gerados até acertar
- **Recovery BR sem `/sbin/sh`** — precisa embarcar busybox ARM estático
- **D8 dexer NullPointerException** — anonymous inner classes crasham, precisa named inner classes
- **EPERM em `Process.destroy()` do logcat** — user app não pode matar processo root; fix no v0.3.0
- **APK fica inoperante após LP0** — Watcher thread zumbi após sistema matar o logcat child; fix no v0.4.0 com receiver

→ [`docs/MAPA.md` §17](docs/MAPA.md)

## Caminhos descartados (com motivo)

Rotas investigadas, descartadas e preservadas pra não re-descobrir:

| Rota | Por que descartada |
|---|---|
| **Entrar na whitelist Mitsubishi** pra remover workaround v0.4.0 | Whitelist é UX-only. Não afeta LP0. V0.4.0 já é o padrão oficial da plataforma. |
| **SuperSU como mediator** | Nosso `su` é setuid simples. SuperSU substitui por um com prompt Activity → bloqueia nosso `Runtime.exec("su")` esperando toque humano = quebra o AutoOk. |
| **Xposed Framework** | Patch de `/system/bin/app_process` é destrutivo. Zero precedente público em Mitsubishi Andromeda. Alto risco de bootloop recuperável só via OTA de rollback. |
| **Modificar `DaLauncher.apk` via smali** | Benefício: aviso sumir de vez. Risco: brick do launcher = tela preta no boot = sem câmera de ré. Custo-benefício não compensa dado que v0.4.0 funciona. |

→ [`docs/MAPA.md` §16](docs/MAPA.md)

## Ferramentas e processos reusáveis

Além dos achados específicos deste carro, o projeto produziu infraestrutura reusável:

- **`tooling/deodex/deodex-apk.sh`** — automatiza odex → `classes.dex` → APK pra qualquer APK Mitsubishi (toda a vendor-app é pre-dexed). Validado em 160 APKs.
- **Fluxo REA + MCP** — integração do [REA](https://github.com/morluto/rea) como MCP server. `~/.local/share/rea/android/jadx-headless-mcp-0.7.1-all.jar` + env var `REA_JADX_MCP_JAR` + skill `reverse-engineer-anything`. Qualquer dump Android pode ser analisado.
- **EvilValet OTA com testkey AOSP** — pacote OTA assinado com testkey AOSP pública, aceito pela recovery (fundamentos em [juniperspring.org](https://juniperspring.org/posts/honda-evil-valet/)). Nossa adaptação pra safra BR + inclusão de busybox no pacote funciona pra outras safras do mesmo recovery.
- **Pacote OTA de deep-scan** — dumpa `/system`, `/data/system/packages.xml`, `/proc/*`, árvore de partições em uma passada no carro. Gera `scan.tar.gz` 897 KB → alimenta `docs/MAPA.md`.
- **Hall of fame com fix** — cada bug tem receita no `MAPA` §17; aplicável a outros projetos de RE Mitsubishi.

→ Processo de deodex: [`tooling/deodex/README.md`](tooling/deodex/README.md) · Comando frequente REA: [`docs/MAPA.md` §20.8](docs/MAPA.md)

## Oportunidades identificadas (próximas fases)

Resumo dos achados que apontam pra próximas melhorias concretas — detalhes e priorização em [`ROADMAP.md`](ROADMAP.md).

- **`ICameraAPServiceReverseSignalListener`** (AIDL do Camera service) permite detectar entrada/saída da ré via callback direto, sem o logcat polling atual
- **`com.mitsubishielectric.ada.appservice.powermanager.ACTION_RESUME_CAMERA`** é broadcast dedicado à retomada da câmera
- **`com.mitsubishielectric.ada.app.dalauncher.action.DISCLAIMER_COMPLETE`** pode ser o sinal canônico de "aviso dispensado" — vale validar se dispara em tap programático
- **`persist.sys.keyoff_reboot=1`** teoricamente força cold boot a cada keyoff — resolveria a complexidade LP0 toda (teste pendente)
- **Vehicle info completa** — `IVehicleInfoManagerApService` tem 37 listeners cobrindo marcha, velocidade, voltagem IG, ângulo do volante, VIN, FOB key atual. Abre caminho pra features reais ligadas ao estado do carro.

→ [`ROADMAP.md`](ROADMAP.md)
