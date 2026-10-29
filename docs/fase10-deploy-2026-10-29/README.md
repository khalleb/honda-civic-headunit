# Fase 10 — Resultado do deploy (2026-10-29)

Deploy executado em 2026-10-29 (adiado de 2026-10-27 por disponibilidade do carro). Este documento é o registro final do que aconteceu, baseado no gate `.OK/.FAIL`, nos logs do updater-script e nos `logcat.txt`/`kmsgcat.txt` que a central gravou no pendrive em cada passo. Checklist seguido na íntegra: [`docs/fase10-execucao-2026-10-27.md`](../fase10-execucao-2026-10-27.md).

## Resultado em uma linha

**O aviso de abertura desapareceu permanentemente.** O patch smali no `DaLauncher.apk` (1 instrução) força o fluxo a pular o `DisclaimerFragment` e cair direto no `EcoFragment`, que depois cede pro `CarPlayMainActivity`. CarPlay projetando, navegação funcionando, zero crash em qualquer boot. Uma Fase 10.1 preparada no mesmo dia reduz a tela Eco de ~6 s para ~1 s via segundo patch smali de 1 instrução.

## Timeline

### §2.1 — Validação do pacote de rollback (10:00 BRT)

**Objetivo:** garantir que a rede de segurança funciona antes de arriscar o install. Como o DaLauncher no carro era igual ao original esperado pelo rollback, o resultado tinha que ser no-op (bytes idênticos sobre eles mesmos).

Pacote: `tooling/ota-build/output-dalauncher-restore/20261027T020209Z/0040/SwUpdate.mdt` (SHA-256 `6445ec80…`).

Resultado:
- Gate `ROLLBACK-RESTORED.OK` presente, conteúdo `OK`
- `ROLLBACK-RESTORED.FAIL` ausente
- `restore-verified-OK` no `dalauncher-restore-0040.log`
- `mv-trigger-exit=0`, `rm-copy-complete-exit=0` (loop break confirmado)
- `chown-exit=0 chmod-exit=0` nas duas linhas `perm` (APK e odex) — **primeira vez que o `chown`/`chmod` do busybox roda neste carro** (§17.18)
- md5 pré-restore == md5 pós-restore em APK e odex → no-op bytes idênticos como previsto
- Duração do updater-script: 6 s (`12:56:47 → 12:56:53 UTC`)
- CAP montado como ext4 (sem o CAP, o `.OK` do odex seria falso — §17.18)

Logs preservados em `~/backup-honda-civic-g10/pendrive-fase10-restore-2026-10-29/`.

### §2.2 — Deploy da Fase 10 (10:10 BRT)

Pacote: `tooling/ota-build/output-dalauncher-fase10/20261027T020208Z/0040/SwUpdate.mdt` (SHA-256 `4c31cb4d…`, APK `1774136c…`, md5 `fc8e87f6…`).

Resultado do updater-script:
- Gate `FASE10-ODEX-REMOVED.OK` presente, conteúdo `removed`
- `.FAIL` ausente
- `odex-removed-OK` no log
- `chown-exit=0 chmod-exit=0` na linha `perm /system/vendor/app/DaLauncher.apk`
- md5 pós-deploy do APK = `fc8e87f6bba2713c0703f6b9d37a29cf` ← **prova positiva** (fecha o falso `.OK` do §17.18: é o APK patcheado no lugar, não um restore silencioso)
- Loop break OK, duração 5 s (`13:11:44 → 13:11:49 UTC`)
- `result.log` do daupdater presente com `OK` (não tinha no §2.1)

**No carro, com o patch já ativo (boot subsequente, 13:13 UTC):**

```
13:13:12.503 — ActivityManager inicia OpeningDivideActivity (NORMAL_STARTUP)
13:13:13.103 — OpeningDivideActivity.onCreate (classe patcheada)
13:13:13.673 — OpeningDivideActivity.createEcoIntent():EcoStart!  ← primeira vez no veículo
13:13:13.763 — EcoFragment.onCreateView                           ← tela "-eco-" aparece
13:13:14.053 — EcoFragment.onResume / onServiceListComplete
… 6 s de tela Eco …
13:13:19.823 — EcoFragment.startNextActivity → CarPlayMainActivity
13:13:19.833 — NavigationApService.disclaimerDisappeared
13:13:19.863 — AppManagerService.setDisclaimerPassed(true)
13:13:19.863 — CarPlayApService.setDisplayPermission(status=true)  ← CarPlay liberado
13:13:19.873 — broadcast DISCLAIMER_COMPLETE disparado
13:13:19.933 — EcoFragment.onPause / onDestroy
13:13:21.503 — reafirma setDisclaimerPassed + setDisplayPermission
13:13:35.763 — reafirma uma 3ª vez (boot final)
13:13:31+   — NavigationApService ativo (TBT, RDS-TMC, NMEA)
```

Zero stacktraces no `logcat`, zero erros no `kmsg`. Logs em `~/backup-honda-civic-g10/pendrive-fase10-install-2026-10-29/`.

### Observação: a tela "-eco-" (10:20 BRT)

Após o deploy, a central passou a mostrar por ~6 s uma tela com o título **-eco-** e três barras de folhinhas (ecoscore) antes de ir pro launcher principal. **Essa tela nunca tinha sido vista pelo dono do carro** — nem mesmo antes do nosso projeto. Explicação:

O fluxo original dentro de `OpeningDivideActivity` testava `sDisclamerFlg` (`static boolean` em memória, §17.16) e tinha dois destinos:
- `sDisclamerFlg == false` → `createDisclaimerOnHomeIntent()` → `DisclaimerFragment` (o aviso)
- `sDisclamerFlg == true`  → `createEcoIntent()` → `EcoFragment` (nunca alcançado)

Como `sDisclamerFlg` **reseta `false` a cada boot da classe**, o `EcoFragment` era caminho morto em uso real. O patch (`if-nez v0, :cond_9` → `goto :cond_9`) ignora o flag e manda sempre pro `createEcoIntent()`. Resultado: a tela Eco acordou pela primeira vez neste carro, como o MAPA §11.1.1 previu.

**Decisão:** o caminho Eco não foi escolhido à toa — é o `EcoFragment.startNextActivity()` quem dispara as 4 chamadas que o CarPlay / Navegação / SystemDisplayApService esperam (`disclaimerDisappeared`, `setDisclaimerPassed(true)`, `setDisplayPermission(true)`, broadcast `DISCLAIMER_COMPLETE`). Pular o Eco sem reimplementar essas chamadas quebraria CarPlay. Mas reduzir o tempo do `EcoFragment` para quase zero preserva as 4 chamadas e visualmente faz a tela "piscar". Esse é o patch da Fase 10.1.

## Fase 10.1 — reduz a tela Eco

Segundo patch smali, de uma instrução, no `EcoFragment.startNoOperationTimer()`:

```diff
     iget-object v0, p0, ...->mNoOperationTimer:Lcom/mitsubishielectric/ada/app/dalauncher/CommonTimer;

-    const/16 v1, 0x1388
+    const/16 v1, 0x1f4

     iget-object v2, p0, ...->mNoOperationTimerCallBack:...
     invoke-virtual {v0, v1, v2}, ...CommonTimer;->start(ILcom/mitsubishielectric/ada/app/dalauncher/CommonTimer$TimerCallBack;)V
```

- `0x1388` = 5000 ms (padrão de fábrica, confirmado nos logs de hoje = 5 s de timer + ~770 ms de animação = os 6 s observados)
- `0x1f4` = 500 ms
- **Resultado esperado:** tela Eco visível por ~1 s (500 ms de timer + animação)
- **Mantido intacto:** `onServiceListComplete`, o callback que dispara `startEndAnimeAndNextActivity → startNextActivity → DISCLAIMER_COMPLETE + setDisplayPermission + disclaimerDisappeared + setDisclaimerPassed`. Só o atraso entre o `onServiceListComplete` e o `onTimerComplete` encurta.
- **Não tocado:** o `displayOffTimerStart()` do EcoFragment (screensaver interno do fragment, também com `0x1388`, mas sem relação com o nosso fluxo).

### Por que 500 ms e não 0 ms

Pela timeline de hoje, o AutoOk v0.5.4 continua ativo no sistema (safety net do §4.1) e tapa `(400, 350)` **~1 s depois** do `am_create_activity` da `OpeningDivideActivity`. Com o patch Fase 10:

- `13:13:13.103` — AutoOk detecta o `am_create_activity`
- `13:13:14.103` — AutoOk tapa (DELAY_SECONDS_AFTER_DETECT = 1 s)

Com a tela Eco em 500 ms:
- `13:13:13.763` — `EcoFragment.onCreateView`
- `13:13:14.263` — `onTimerComplete` dispara `startEndAnimeAndNextActivity`
- `13:13:14.103` — AutoOk tapa → **cai dentro do fundo do EcoFragment** (confirmado seguro: nos dois layouts `mm_07_04_06`/`_ziba`, `(400, 350)` só tem `ImageView` de fundo, nada clicável — ver [`../raio-x/07-services-re.md`](../raio-x/07-services-re.md) e análise em `cysin/honda_hacking_analysis` sobre layouts do Eco)

Com timer de 0 ms o fluxo acabaria em < 500 ms e o tap do AutoOk cairia no `CarPlayMainActivity` ou no `Launcher`, que **têm** elementos clicáveis — risco de ligar/pausar música, clicar num ícone, etc. 500 ms resolve isso sem precisar deployar junto um novo AutoOk ou aumentar `BOOT_INITIAL_WAIT_MS`.

### Verificação da prova de bytecode

O `tooling/fase10/rebuild-dalauncher.sh` passou a aplicar os dois patches e exige que a diferença orig→patch no DEX seja **exatamente** `EcoFragment.smali` + `OpeningDivideActivity.smali`. Qualquer outra classe mudar na diff aborta o rebuild. Confirmado nesta execução:

```
confirmado: so EcoFragment e OpeningDivideActivity mudaram entre orig e patch
```

### Pacote pronto

| Campo | Fase 10 (2026-10-29 10:10 BRT) | **Fase 10.1 (preparada 2026-10-29 10:46)** |
|---|---|---|
| Pasta OTA | `output-dalauncher-fase10/20261027T020208Z` | `output-dalauncher-fase10/20261029T134614Z` |
| SHA-256 do `SwUpdate.mdt` | `4c31cb4d018afbfcf7fc8a48c0d10d95d489fd929e3e4d4eaf98ffbb1bc02fb0` | `f571af751dc9be6619cf33e7eb5d11268dd3f004b1c93587dd47f05d6cf3f453` |
| SHA-256 do APK | `1774136cfad10919eb03698badc259179521e5fe7e69b82fc349029aaceb1807` | `65481d45acd01ad67359b1174b57150eecb959377bde3379a30e2eb17a8d4a4c` |
| md5 do APK (gate §2.2) | `fc8e87f6bba2713c0703f6b9d37a29cf` | **`655c01a3b17fe20b23c70114e1e0dae7`** |
| Updater-script | — | **bit-por-bit idêntico à v1 (md5 `2cca09a3…`)**: único byte diferente dentro do `.mdt` é o APK |

O rollback (`output-dalauncher-restore/20261027T020209Z/`, SHA `6445ec80…`) **não precisa ser rebuildado** — ele continua restaurando o DaLauncher original esperado.

## Como aplicar a Fase 10.1

Segue o mesmo roteiro do §2.2 do checklist, só mudando o SHA esperado e o md5.

```bash
# No PC (sudo)
sudo tooling/scripts/prepare-pendrive-install.sh /dev/sda tooling/ota-build/output-dalauncher-fase10
```

O script pega o build mais novo do diretório (= `20261029T134614Z`), pede `yes`, grava, confere o SHA-256 contra o pacote. Esperado:

```
OK   SwUpdate2.txt       <sha>
OK   0040/SwUpdate.mdt   f571af751dc9be6619cf33e7eb5d11268dd3f004b1c93587dd47f05d6cf3f453
```

**No carro:**
1. Pendrive na porta USB-A frontal, chave em ON
2. AUDIO 5 s → "Reiniciar?" → OK
3. Esperar ~2 min, puxar o pendrive na terceira tela
4. Primeiro boot pós-deploy será lento (~10-30 s a mais, `dexopt` do classes.dex novo)

**No PC (gate §2.2 adaptado para Fase 10.1):**
- `FASE10-ODEX-REMOVED.OK` presente, `.FAIL` ausente
- No `dalauncher-fase10-0040.log`:
  - `chown-exit=0 chmod-exit=0` no APK
  - md5 pós-deploy do APK = **`655c01a3b17fe20b23c70114e1e0dae7`** (**novo** — não é mais `fc8e87f6…`)

**Observar na tela:**
- Aviso **não** aparece
- Tela "-eco-" aparece por **~1 s** (não mais 6 s)
- Launcher principal / CarPlay sobem normalmente
- CarPlay projeta, navegação funciona, câmera de ré funciona

## Fase 10 encerrada

Com a Fase 10.1 aplicada, o objetivo original do projeto está cumprido:

- Aviso removido do fluxo de boot via patch de 1 instrução no bytecode (`OpeningDivideActivity.smali:671`)
- Tela intermediária Eco reduzida a ~1 s via segundo patch de 1 instrução (`EcoFragment.smali:3094`)
- CarPlay / Navegação / SystemDisplay recebem as 4 chamadas que precisavam (`DISCLAIMER_COMPLETE`, `setDisplayPermission`, `disclaimerDisappeared`, `setDisclaimerPassed`)
- Rede de segurança testada e funcional (`output-dalauncher-restore`)
- Zero `assert`/`abort` nos pacotes, `chown`/`chmod` do busybox em vez de `set_perm` em `/system` (§17.18)
- Pacotes assinados com testkey AOSP, aceitos pelo `daupdater` do nosso carro

### Pós-deploy — manter safety net

Mantido o §4.1 do checklist original: AutoOk v0.5.4 continua em `/system/app/` como rede. Ele vai continuar logando `aviso detectado` + `tap ok=true` em cada boot — **não é falha** (o needle casa o `am_create_activity` da `OpeningDivideActivity`, que o patch não toca; só o conteúdo dela mudou).

Semana estável a partir do deploy Fase 10.1 → pode-se considerar remover o AutoOk via rollback do próprio AutoOk (`tooling/ota-build/output-rollback/`). Isso é opcional e tem o único benefício de deixar o `/system` 100% limpo.

### O que fica aberto

- Documentação atualizada em MAPA (§10.3 novo + §18 novo item), ROADMAP (Fase 10 encerrada), CLAUDE.md (versão atual AutoOk continua v0.5.4), e aqui.
- `tooling/fase10/opening-divide-activity-skip-disclaimer.patch` e `eco-fragment-reduce-timer.patch` são os dois patches versionados no repo (fontes de verdade).
- `tooling/fase10/rebuild-dalauncher.sh` passou a aplicar os dois patches e exige a prova de bytecode "só EcoFragment e OpeningDivideActivity mudaram". Rodou OK em 2026-10-29.

## Referências cruzadas

- [`../fase10-pre-planejamento-2026-10-20.md`](../fase10-pre-planejamento-2026-10-20.md) — briefing técnico original
- [`../fase10-decisao-rotas-2026-10-23.md`](../fase10-decisao-rotas-2026-10-23.md) — Rota B escolhida (resign AOSP)
- [`../fase10-execucao-2026-10-27.md`](../fase10-execucao-2026-10-27.md) — checklist de execução (seguido na íntegra)
- [`../MAPA.md`](../MAPA.md) §11.1.1 (internals), §16.4 (pacotes), §17.16 (gate `sDisclamerFlg`), §17.18 (`set_perm` em `/system`)
- [`../raio-x/07-services-re.md`](../raio-x/07-services-re.md) — RE das services que recebem `DISCLAIMER_COMPLETE`
