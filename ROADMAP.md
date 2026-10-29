# Roadmap

> O que já funciona, o que está em discussão para próximas fases, e o que foi descartado com motivo. Para o que **já descobrimos** (plataforma, protocolos, formato de dados), ver [`DISCOVERIES.md`](DISCOVERIES.md).

## Estado atual (2026-10-29)

- 🎯 **Fase 10 concluída (2026-10-29)** — aviso de abertura removido do fluxo de boot via patch smali no `DaLauncher.apk` (1 instrução). Tela intermediária Eco reduzida a ~1 s via segundo patch (Fase 10.1, mesma data). CarPlay projeta, navegação funciona, zero crash. Detalhes em [`docs/fase10-deploy-2026-10-29/README.md`](docs/fase10-deploy-2026-10-29/README.md). Pacote de rollback do DaLauncher validado no mesmo deploy.
- APK **AutoOk v0.5.4** mantido em `/system/app/` como safety net (recomendação: manter 1 semana estável pós-Fase 10.1 antes de remover). Suprime o aviso tanto em cold boot (AUDIO 5s) quanto em LP0 resume. Zero taps falsos, zero conflito com ligação CarPlay via BT.
- v0.5.4 fechou 4 iterações num mesmo dia (v0.5.0 → v0.5.4) resolvendo: bug do mudo em CarPlay (AlarmManager + needle frouxo do v0.4.0); regressão do EPERM (fix 17.9); duas Activities disparadas em LP0 resume (`PRECEDING_STARTUP` da tela de logo vs `NORMAL_STARTUP` do aviso real); formato errado do `-v brief`; bug do Android 4.2.2 que não combina `-b A -b B`.
- `su` setuid permanente em `/system/xbin/` — identificado como KingoSU (não SuperSU), broadcast no-op; troca pelo Chainfire SR1 pendente ([`docs/raio-x/08-github-landscape-2026-10-27.md §4`](docs/raio-x/08-github-landscape-2026-10-27.md))
- Deploy via pacote OTA EvilValet validado, com fix do loop infinito no `build.py` (renomeia `SwUpdate2.txt → .done`)
- Pacotes de rollback (AutoOk + DaLauncher) construídos e, no caso do DaLauncher, validados no carro em 2026-10-29

**O objetivo original do projeto está cumprido.** Nada do roadmap abaixo compromete a estabilidade do deploy atual. Tudo listado é opcional / exploratório.

## Em curto prazo (candidatos a próxima fase)

Em ordem de valor x custo. Nenhum está em execução — todos aguardam decisão de abrir fase nova.

### Fase 9 — Câmera de ré via API oficial

**Hoje:** o AutoOk detecta entrada/saída da ré via logcat polling (processo `logcat` como child de `su` que lê linhas). Funciona mas é frágil (o próprio bug corrigido no v0.4.0 era o logcat child morrer em LP0).

**Caminho oficial descoberto:** o Camera service da plataforma expõe `ICameraAPServiceReverseSignalListener` via AIDL binder, e o PowerManager emite `ACTION_RESUME_CAMERA` + `ACTION_RESUME_COMPLETED_CAMERA` como broadcasts dedicados. Também existe `com.mitsubishielectric.android.action.camera.EXIT_REAR_WIDE_CAMERA` para saída.

**O que precisa:** confirmar permissão exigida (provavelmente `VEHICLE_RW`), bind no `ICameraAPService`, registrar listener, remover polling do AutoOk. Risco baixo porque o fluxo atual continua funcionando como fallback.

→ [`docs/raio-x/01-apis-aidl.md § appservice.camera`](docs/raio-x/01-apis-aidl.md) · [`docs/raio-x/02-broadcasts.md`](docs/raio-x/02-broadcasts.md)

### Validar `DISCLAIMER_COMPLETE` como sinal canônico de "aviso dispensado"

A action `com.mitsubishielectric.ada.app.dalauncher.action.DISCLAIMER_COMPLETE` é emitida pelo launcher quando o `DisclaimerFragment` termina. Se o launcher emite o broadcast igualzinho quando é tap humano **e** tap programático nosso, abre caminho pra:

- Logs internos do AutoOk saberem que o tap deu certo sem precisar re-ver a tela
- Outros apps nossos reagirem ao evento sem polling

**O que precisa:** confirmar via logcat no veículo que o broadcast dispara em ambos os casos. Zero código, 1 teste no carro.

→ [`docs/raio-x/02-broadcasts.md § com.mitsubishielectric.ada.app.dalauncher.*`](docs/raio-x/02-broadcasts.md)

### Dumpar `com.honda.displayaudio.whitelist.apk` real

O APK portador do XML da whitelist deveria estar em `/system/vendor/etc/honda/com.honda.displayaudio.whitelist.apk` (14 KB conforme deep-scan textual), mas não foi trazido como bytes no dump raw atual. Precisa dumpar pra:

- Confirmar formato real do XML (hoje é inferido do parser)
- Testar Rota B da whitelist (substituir o APK portador por versão nossa com entry própria do AutoOk) se um dia quisermos nome amigável no AppManager

**O que precisa:** incluir `/system/vendor/etc/honda/*` no próximo deep-scan OTA. Baixo custo.

→ [`docs/whitelist-mitsubishi-2026-10-19.md § 2.3`](docs/whitelist-mitsubishi-2026-10-19.md)

### ~~Fase 10 — Remover o aviso de vez (patch smali no DaLauncher)~~ ✅ **CONCLUÍDA 2026-10-29**

Rota B escolhida (resign AOSP). Patches versionados em `tooling/fase10/*.patch`. Deploy §2.1 + §2.2 passaram todos os gates no carro, com md5 pós-deploy = `fc8e87f6…` confirmando o APK patcheado no lugar. Observação do deploy: a tela `EcoFragment` (caminho morto antes do patch, §17.19 do MAPA) acordou pela primeira vez e aparece por ~6 s. **Fase 10.1** preparada no mesmo dia reduz essa tela para ~1 s via segundo patch smali (`EcoFragment.smali:3094`, timer 5000 ms → 500 ms), mantendo as 4 chamadas pós-aviso (`DISCLAIMER_COMPLETE`, `setDisplayPermission`, `disclaimerDisappeared`, `setDisclaimerPassed`).

Pacotes finais:
- Install (v1 aplicada): `tooling/ota-build/output-dalauncher-fase10/20261027T020208Z/` SHA `4c31cb4d…`
- Install (Fase 10.1 pronta): `tooling/ota-build/output-dalauncher-fase10/20261029T134614Z/` SHA `f571af75…` md5 do APK `655c01a3…`
- Rollback: `tooling/ota-build/output-dalauncher-restore/20261027T020209Z/` SHA `6445ec80…`

Docs: [`docs/fase10-deploy-2026-10-29/README.md`](docs/fase10-deploy-2026-10-29/README.md), [`docs/MAPA.md`](docs/MAPA.md) §16.4, §17.19.

### Experimentar `persist.sys.keyoff_reboot=1`

Essa property controla se a central faz **cold boot** vs. **suspend/resume** no key-off. Hoje o default é suspend — por isso o combo `AUDIO 5s + confirmar` é necessário pra forçar cold boot. Se setarmos a prop pra `1`, teoricamente cada keyoff vira cold boot.

**Implicações potenciais:**
- Elimina a complexidade LP0 (cada partida é cold boot do zero)
- Carro liga mais devagar (3-5s de boot vs. instant)
- Consumo potencialmente maior em períodos parado

**O que precisa:** `su -c "setprop persist.sys.keyoff_reboot 1"` + testar com rollback preparado. Baixo custo, mas tem que ir no carro.

→ [`docs/raio-x/04-system-properties.md`](docs/raio-x/04-system-properties.md)

## Em médio prazo (bons alvos sem fase definida ainda)

### Diag APKs — menus escondidos / PINs

Os 4 APKs de diagnóstico (`DealerDiag`, `DeveloperDiag`, `PreShipmentDiag`, `LetDiag`) e o service `DiagApService.apk` tipicamente carregam PINs de dealer, modos de serviço e menus escondidos. Alto potencial de Easter egg, baixo risco de brick (são UIs). Descompilar via REA + ver strings de PIN, intents que abrem Activities privadas, etc.

→ [`docs/raio-x/05-trust-map.md`](docs/raio-x/05-trust-map.md)

### Steering wheel API

`IStrgSwApService` + 8 listeners cobrem eventos do volante (`IStrgSwRotaryKeyEventApServiceListener`, `IStrgSwMotionMenuApServiceListener`, etc). Mapeamento dos botões físicos vive aqui. Baixo custo pra hookar atalhos personalizados.

→ [`docs/raio-x/01-apis-aidl.md § appservice.strgsw`](docs/raio-x/01-apis-aidl.md)

### Vehicle info completa

`IVehicleInfoManagerApService` tem 37 listeners cobrindo marcha, velocidade, voltagem IG, ângulo do volante, VIN, FOB key atual (perfil por motorista!), sensores de ré, etc. Toda a telemetria do carro passa por aqui.

→ [`docs/raio-x/01-apis-aidl.md § appservice.vehicleinfomanager`](docs/raio-x/01-apis-aidl.md)

### Audio pipeline (bypass de ducking)

Nosso AutoOk hoje não interfere com áudio, mas outros apps nossos poderiam. `AV.apk` roda como `android.uid.phone` com acesso a `IAvApService` (14 interfaces callback). Entender o pipeline permite, por exemplo, publicar áudio sem o sistema baixar o volume.

→ [`docs/raio-x/01-apis-aidl.md § appservice.avapservice`](docs/raio-x/01-apis-aidl.md)

### Fluxo oficial de OTA (sem EvilValet)

`SystemUpdate.apk` é o alvo original do EvilValet. Entender por dentro como ele valida pacotes pode abrir caminho pra deploy sem exploit, se um dia a Honda fechar essa porta. Baixa prioridade enquanto EvilValet funcionar.

→ [`docs/raio-x/05-trust-map.md`](docs/raio-x/05-trust-map.md)

## Em longo prazo (alto custo / alto risco)

- **Ghidra em `/system/bin/daupdater`** — entender exatamente como o recovery valida pacotes OTA
- **Ghidra em `/system/vendor/lib/*.so`** — HALs de display, áudio, CAN. Modificar aqui tem risco real de brick de hardware.
- **Modificar bootloader** — recuperável só com acesso físico à eMMC. Fora de escopo prático.

Nenhum destes está sendo considerado hoje.

## Descartado (com motivo preservado)

Rotas que foram investigadas e descartadas. Documentar pra não re-descobrir:

| Rota | Motivo da descartação |
|---|---|
| Entrar na whitelist Mitsubishi pra remover v0.4.0 | Whitelist é UX-only. Não afeta LP0. V0.4.0 já é o padrão oficial. [`MAPA` §16.3](docs/MAPA.md) |
| SuperSU como mediator | Substituiria nosso `su` por um com prompt Activity → bloqueia `Runtime.exec("su")`. Quebra o AutoOk. [`MAPA` §16.1](docs/MAPA.md) |
| Xposed Framework | Alto risco de bootloop. Zero precedente em Andromeda. Recuperável só via rollback OTA. [`MAPA` §16.2](docs/MAPA.md) |
| ~~Modificar `DaLauncher.apk` via smali~~ | **Re-habilitada como Fase 10 em 2026-10-20** após descoberta do gate `sDisclamerFlg` + signature singular do DaLauncher. Ver seção "Em curto prazo" acima. [`docs/fase10-pre-planejamento-2026-10-20.md`](docs/fase10-pre-planejamento-2026-10-20.md) |

## Melhorias de ferramentas (não ligadas ao carro)

Mantido pra referência cruzada com `CONTRIBUTING.md`:

- Preencher `docs/pt-BR/01, 02, 04, 05, 06` (hoje são atalhos para fase7)
- Traduzir `docs/pt-BR/` completo para `docs/en/`
- GitHub Pages com MkDocs Material
- CI básico que valida `python3 tooling/ota-build/build.py`
- Social preview image + logo em versões (dark/light, favicon)

## Como ajudar com qualquer um dos itens acima

Ver [`CONTRIBUTING.md`](CONTRIBUTING.md). Issues com template "nova-safra" e "bug-report" prontos no repo.
