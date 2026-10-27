# Fase 10 — Checklist de execução (deploy day)

> Prep concluída em 2026-10-23. Alvo de deploy: **2026-10-27** (quando fecha a
> janela de "v0.5.4 estável por 1 semana"). Este doc é o roteiro minuto a
> minuto pro dia de ir no carro.
>
> Revisado em 2026-10-26: pacotes regerados sem `assert` de device e sem
> `set_perm` em `/system`, e scripts de pendrive recebendo o diretório do build
> (ver MAPA §16.4).

## 0. Precondições antes de sair de casa

Checar nessa ordem. Cada item precisa estar OK, senão **adiar o deploy**.

- [ ] **v0.5.4 do AutoOk ainda estável** — nenhum tap falso ou LP0 bug reportado desde 2026-10-20
- [ ] **Dois pendrives FAT32 distintos**, rotulados fisicamente:
  - Pendrive A — **ROLLBACK** (contém `tooling/ota-build/output-dalauncher-restore/<ts>/0040/SwUpdate.mdt`)
  - Pendrive B — **INSTALL** (contém `tooling/ota-build/output-dalauncher-fase10/<ts>/0040/SwUpdate.mdt`)
- [ ] **Build fresco de ambos** (se o APK patcheado foi modificado, rodar o fluxo todo):
  ```bash
  bash tooling/fase10/rebuild-dalauncher.sh
  python3 tooling/ota-build/build-dalauncher-fase10.py
  python3 tooling/ota-build/build-dalauncher-restore.py
  ```
- [ ] **Pendrives preparados** — passar o diretório é obrigatório; sem ele, os scripts gravam os pacotes do AutoOk:
  ```bash
  sudo tooling/scripts/prepare-pendrive-install.sh /dev/sdX tooling/ota-build/output-dalauncher-fase10
  sudo tooling/scripts/prepare-pendrive-rollback.sh /dev/sdY tooling/ota-build/output-dalauncher-restore
  ```
  Cada script usa o build mais novo do diretório (ou o build exato, se receber `.../<ts>`). Antes de apagar, mostra modelo, rótulo e conteúdo do pendrive e só segue com `yes`; os dois pendrives formatados pelo `format-pendrive.sh` têm o rótulo HONDA_OTA, então o mais seguro é preparar um de cada vez, só com ele plugado. Depois copia, confere o SHA-256 lido do pendrive contra o build e desmonta. Se o SHA-256 não bater, termina com erro e o pendrive não vai pro carro. Também recusa partição no lugar do disco (`/dev/sdX1`), tabela que não seja MSDOS e partição que não seja vfat; nesses casos, formatar com `sudo tooling/scripts/format-pendrive.sh /dev/sdX`.
- [ ] **Validação dos pendrives**, na saída de cada script:
  - `=== Usando build: ...` aponta para `output-dalauncher-fase10/<ts>` (Pendrive B) e `output-dalauncher-restore/<ts>` (Pendrive A), nunca para `output/` ou `output-rollback/`
  - duas linhas `OK` na conferência, e o SHA-256 do `0040/SwUpdate.mdt` igual ao da tabela do §5
- [ ] **Celular carregado** — pra fotografar logs do pendrive se precisar
- [ ] **PC com acesso ao backup externo** — pra copiar logs e, se der ruim, usar `~/backup-honda-civic-g10/dump-raw-2026-10-17/*.img.gz`

## 1. Materiais pra levar

- Pendrive A (ROLLBACK) — rótulo claro, cabo USB-A → USB-A frontal
- Pendrive B (INSTALL) — rótulo claro
- (Opcional) Pendrive C — install do AutoOk v0.5.4 (`tooling/ota-build/output/20261020T181124Z`, já aplicado no carro), saída alternativa de recovery loop (§3.6)
- Celular carregado
- Chave do carro
- (Opcional) Laptop com os backups se precisar de rollback via dump raw

## 2. Sequência no carro

### 2.1. Validação do rollback (no-op intencional)

**Objetivo:** garantir que o pacote de rollback funciona ANTES de precisar dele. Como o DaLauncher atual no carro = DaLauncher original esperado pelo rollback, aplicar rollback agora é no-op (bytes iguais sendo escritos sobre eles mesmos). Mas valida: mount, extract, perms, loop break, unmount.

Passos:

1. Carro no acostamento ou garagem, chave em "ON" (não "START"), central ligada e boot completo
2. Plugar **Pendrive A (ROLLBACK)** na porta USB-A frontal
3. Segurar **AUDIO 5s** → diálogo "Reiniciar?" → **OK**
4. Esperar ~2 min (central reboota, aplica OTA, reboota mais uma vez)
5. **Puxar o pendrive assim que a tela acender a terceira vez** (janela de 30s do sleep final)
6. **Gate primário (sem abrir log):** plugar o pendrive no PC e confirmar que existe o arquivo `ROLLBACK-RESTORED.OK` e que **não** existe `ROLLBACK-RESTORED.FAIL`. O updater-script grava `.OK` só se o md5 do apk e do odex pós-restore baterem com os originais da safra.
7. Confirmação detalhada no log `dalauncher-restore-0040.log`:
   - `restore-verified-OK` presente
   - `rm-copy-complete-exit=0` e `mv-trigger-exit=0` (loop break OK)
   - `chown-exit=0 chmod-exit=0` nas duas linhas `perm` (APK e odex). É a primeira vez que o `chown`/`chmod` do busybox roda no carro; o install do §2.2 usa o mesmo comando

Se faltar o `.OK`, ou existir o `.FAIL`, ou o log não confirmar: **abortar deploy**, investigar.

> Ressalva: esta validação exercita mount / extract / perms / md5 / loop-break do rollback, mas **não** o caminho de recuperação de signature-mismatch (aqui a assinatura ainda é a Mitsubishi original). Esse caminho só é exercido num rollback real pós-Fase 10 — por isso o dump raw de 2026-10-17 segue como rede final.

### 2.2. Deploy do pacote Fase 10

Só prosseguir se §2.1 passou.

1. Pendrive A pode ficar dentro do carro mas **não plugado**
2. Plugar **Pendrive B (INSTALL)** na porta USB-A frontal
3. Segurar **AUDIO 5s** → diálogo "Reiniciar?" → **OK**
4. Esperar ~2 min
5. **Puxar o pendrive B** quando a tela ligar pela terceira vez
6. **Gate do `.odex` (antes de confiar no boot):** plugar o pendrive B no PC e confirmar que existe `FASE10-ODEX-REMOVED.OK` e que **não** existe `FASE10-ODEX-REMOVED.FAIL`. Se existir o `.FAIL`, o `.odex` velho não saiu → risco de crash do launcher → aplicar rollback (§3) e investigar antes de qualquer coisa.
   - No `dalauncher-fase10-0040.log`, conferir também `chown-exit=0 chmod-exit=0` na linha `perm /system/vendor/app/DaLauncher.apk`. Com exit diferente de 0, o provável é o CAP não ter montado e o APK não ter sido extraído (ver a saída do `mount` no começo do log). Nesse caso o `.OK` do `.odex` também não prova nada, porque o `test ! -e` passa com o CAP desmontado: não repetir o deploy antes de entender o log
   - Prova positiva de que o APK novo está no lugar (fecha o falso `.OK` acima): na linha de md5 antes de `post-deploy-md5-apk`, o md5 de `/system/vendor/app/DaLauncher.apk` tem que ser `fc8e87f6bba2713c0703f6b9d37a29cf` (o md5 do APK dentro do pacote de hoje). Qualquer outro valor — ou a linha ausente — quer dizer que o APK não foi gravado (CAP não montou), e aí o `.odex` também não saiu
7. **Primeiro boot pós-deploy será lento** — ~10-30s a mais que o normal, porque Dalvik vai `dexopt` o `classes.dex` novo embutido no APK
8. Observar:
   - Tela liga normal? ✅
   - **Aviso NÃO aparece**? ✅ (meta da Fase 10)
   - Launcher aparece (possivelmente com configs default — wallpaper padrão, ícones em posição inicial — **se** o PackageManager tomar o caminho "new install"; ver hipótese em `fase10-decisao-rotas-2026-10-23.md`)
   - Câmera de ré, navegação e projeção do CarPlay funcionam. O patch troca o aviso pelo `EcoFragment`, que precisa refazer `DISCLAIMER_COMPLETE`, `disclaimerDisappeared` e `setDisplayPermission` (MAPA §11.1.1). No logcat do carro de 2026-10-20, o CarPlay só recebe `setDisplayPermission(status=true)` depois do aviso; se ele não projetar, é o caminho Eco que não refez essa chamada. Se algum falhar, tratar como §3.3

### 2.3. Boot de LP0 (desligar e religar a chave)

1. Desligar o carro (chave off)
2. Esperar ~30s
3. Ligar o carro (chave on)
4. Observar:
   - Central acorda rápido (LP0 resume) ✅
   - **Aviso NÃO aparece** ✅
   - Launcher operando normal ✅

### 2.4. Cold boot fresh (segunda validação)

1. Segurar **AUDIO 5s** → diálogo "Reiniciar?" → **OK**
2. Após boot:
   - **Aviso NÃO aparece** ✅
   - AutoOk v0.5.4 continua rodando como safety net (log no `autook.log`)

### 2.5. Coletar logs

1. Plugar Pendrive A (ou B, qualquer FAT32)
2. No ADB se estiver ativo, OU via comando pelo AutoOk se tiver, OU via próximo deploy de diagnóstico

Melhor: aproveitar que o AutoOk v0.5.4 está em prod e já grava log em `/data/data/com.khalleb.civichmi.autook/files/autook.log`.

**Atenção ao ler esse log:** mesmo com a Fase 10 bem sucedida, o AutoOk vai continuar logando `aviso detectado` + `tap ok=true` a cada boot — isso **não** é sinal de que o patch falhou. O needle casa a abertura da `OpeningDivideActivity` com `NORMAL_STARTUP` (`AvisoMatcher.matches`), e quem dispara essa Activity é `Launcher.startOpeningDividActivity()`, que o patch não toca. O patch só pula o disclaimer **dentro** da Activity e põe o `EcoFragment` no lugar. Ou seja, o tap programático em (400,350) continua caindo ~1s depois no fundo da tela Eco (onde só há imagem de fundo, nada clicável nos dois layouts `mm_07_04_06`/`_ziba`). O veredito da Fase 10 vem **da tela** (aviso não aparece, launcher opera, CarPlay projeta) e do logcat do DaLauncher (`ECO_START`, `DISCLAIMER_COMPLETE`), não do `autook.log`. Se algo abrir ou piscar sozinho ~1s depois do boot, o primeiro suspeito é esse tap.

## 3. Falhas esperadas e como abortar

### 3.1. Launcher não aparece (tela preta ou tela do reboot em loop)

Causa provável: signature mismatch mais severo do que o esperado, ou .odex residual causando conflito no Dalvik.

**Abort imediato:**
1. Plugar **Pendrive A (ROLLBACK)**
2. **AUDIO 5s** → OK → aguardar 2 min → puxar pendrive na terceira tela
3. Depois: boot normal volta porque DaLauncher.apk + .odex originais são restaurados
4. Em casa: ler log `dalauncher-restore-0040.log`, investigar o que deu errado

### 3.2. Launcher aparece mas aviso ainda aparece

Causa provável: patch smali não cobriu algum caminho, OU `.odex` foi regenerado antes do primeiro boot (improvável), OU algum erro de assembly.

**Não é crítico** (AutoOk v0.5.4 ainda está lá dispensando o aviso). Mas Fase 10 falhou. Opções:
1. Deixar como está, aviso dispensado pelo AutoOk (volta ao estado pré-Fase 10)
2. Rollback (opcional): aplicar Pendrive A pra restaurar DaLauncher original "limpo"
3. Investigar o smali — pode faltar patchear outro caminho

### 3.3. Launcher aparece normal mas algum feature quebrou

Exemplo: wallpaper some, ícones em ordem errada, menus específicos crasham.

Causa: PackageManager apagou `/data/data/...dalauncher/*` por causa do signature mismatch. **Esperado**. Launcher recria defaults e volta ao normal com o uso.

Se quebrou algo **crítico** (ex: funções do volante, câmera de ré pelo launcher):
- Rollback (Pendrive A)
- Investigar permissions perdidas

### 3.4. Boot loop verdadeiro (central reboota continuamente)

Causa provável: APK corrompido ou Dalvik não consegue parsear classes.dex novo.

**Abort via pendrive na porta frontal:**
1. Pendrive A plugado antes do keyon
2. Carro liga normalmente
3. Combo AUDIO 5s + OK → entra no fluxo OTA → rollback aplica
4. Se **nem com rollback** o boot loop para: fallback para dump raw via `tooling/ota-build/build-dump-raw.py` ou escalation a ferramenta externa

### 3.5. Tela preta persistente (não vai pra lugar nenhum)

Última linha de defesa:
1. Pendrive A plugado
2. Combo AUDIO 5s + confirmar "Reiniciar?" → entra no fluxo OTA → rollback aplica
3. Rollback

**O combo não é garantido.** O diálogo "Reiniciar?" é desenhado pelo Android (não é input direto no bootloader) e o `daupdater` só escaneia o pendrive num boot completo (MAPA §13.1, §13.3; `ic1101/docs/updates.md`). Se a central estiver em tela preta de verdade, o diálogo pode não aparecer. Nesse caso, forçar o desligamento completo pela energia:

- **Puxar o fusível do rádio por 15-20 min** (fuse box interno), com o Pendrive A já plugado. Religar o fusível, ligar o carro, tentar o combo de novo. É o mesmo procedimento de `docs/pt-BR/06-troubleshooting.md` quando o diálogo não aparece.

Se nem assim: `~/backup-honda-civic-g10/dump-raw-2026-10-17/*.img.gz` tem backup raw do /system inteiro. Precisa de ferramenta externa pra re-flashar.

### 3.6. Recovery loop (a central volta sempre para o recovery)

Causa: o recovery falhou ao aplicar o pacote e não apagou o comando estagiado em `/cache/recovery/command` (CAUTION do `ic1101/docs/updates.md`). Tirar o pendrive ou a bateria não resolve.

O comando aponta para `/mnt/usbdrive1/0040/SwUpdate.mdt`. A saída é plugar na porta frontal um pendrive com outro pacote que o recovery consiga aplicar:

1. **Pendrive A (ROLLBACK)** — o recovery aplica o restore e apaga o comando
2. Se não sair, **Pendrive C** — o install do AutoOk v0.5.4, que já rodou no carro

Os pacotes da Fase 10 não têm nada que aborte o `updater-script`: nem `assert`/`abort`, nem `set_perm` fora de `/tmp` (testes `test_nao_tem_assert_nem_abort_que_prenderiam_o_recovery_em_loop` e `test_set_perm_so_em_tmp_porque_aborta_quando_o_arquivo_falta`). O assert de device dos builds de 2026-10-23 e o `set_perm` em `/system` dos builds anteriores eram os riscos conhecidos deste cenário (MAPA §17.18).

## 4. Pós-deploy — manter safety net

### 4.1. Semana 1 pós-deploy

- **NÃO remover o AutoOk v0.5.4 do /system/app/**. Deixar como safety net.
- Observar comportamento normal do carro: boot, LP0 resume, câmera de ré, CarPlay, chamadas BT, volume, etc.
- Qualquer regressão → rollback do DaLauncher (Pendrive A)

### 4.2. Após 1 semana estável (alvo 2026-11-03)

- Remover AutoOk via rollback do próprio AutoOk: `tooling/ota-build/output-rollback/<ts>/0040/SwUpdate.mdt`
- Esse rollback dropa `/system/app/AutoOk.apk` + `/system/xbin/su` (reset total do nosso trabalho)
- Resta no sistema: só o DaLauncher patcheado

### 4.3. Documentar o deploy

- Atualizar `docs/MAPA.md`:
  - §10 (nossas modificações) — adicionar DaLauncher patcheado
  - §17 (hall of fame bugs) — se houve algum durante deploy
  - §18 (timeline) — data do deploy + resultado
- Criar `docs/fase10-deploy-2026-10-27/README.md` com resultado real
- Atualizar `ROADMAP.md` — marcar Fase 10 como concluída

## 5. Pacotes OTA prontos

Regerados em 2026-10-26 (o nome da pasta tem o horário em UTC), sem o assert de device e sem `set_perm` em `/system` (§3.6). Em relação aos builds de 2026-10-23, só mudam essas linhas do `updater-script` e a assinatura refeita; APK, odex, busybox e `update-binary` são os mesmos bytes. A assinatura whole-file dos dois foi conferida contra o testkey AOSP (RSA 2048, e=3, SHA-1), com controle positivo (install do v0.5.4, aceito pelo carro) e negativo (cópia adulterada em 1 byte).

| Pacote | Path | SHA-256 do `SwUpdate.mdt` | Conteúdo |
|---|---|---|---|
| Install | `tooling/ota-build/output-dalauncher-fase10/20261027T020208Z/0040/SwUpdate.mdt` | `4c31cb4d018afbfcf7fc8a48c0d10d95d489fd929e3e4d4eaf98ffbb1bc02fb0` | APK patcheado `1774136cfad10919...` |
| Rollback | `tooling/ota-build/output-dalauncher-restore/20261027T020209Z/0040/SwUpdate.mdt` | `6445ec80302705300a98a0a5adc993ada8ff580b8d657ee35c4c93a2237bbd3d` | APK original `1d8bd729ad309240...` + odex `1497dc8497799faf...` |

Os builds anteriores (os de 2026-10-23 e os `20261026T214450Z`/`20261026T214451Z`) continuam nos mesmos diretórios e **não devem ir pro pendrive**: todos têm `set_perm` em `/system`, os de 2026-10-23 têm também o assert, e os de `...210720Z`/`...210007Z` nem gravam `.OK`/`.FAIL`. Os scripts de pendrive pegam o build mais novo; basta não passar um `<ts>` antigo.

O SHA-256 do `SwUpdate.mdt` muda a cada build (data das entradas do zip e assinatura). Se rebuildar, vale o SHA que o script de pendrive imprimir.

O APK patcheado é reconstruído por `tooling/fase10/rebuild-dalauncher.sh`, que deodexa o `.odex` original fresh, aplica `tooling/fase10/opening-divide-activity-skip-disclaimer.patch` (versionado), e **prova** que a única diferença de bytecode orig→patch é a classe `OpeningDivideActivity` (assemble + disassemble de ambos os lados, diff). O `build-dalauncher-fase10.py` recusa empacotar um APK que não esteja assinado com o testkey AOSP.

**Importante:** se este doc for seguido em outra data (ex: 2026-11-02), rebuildar os dois pacotes pra ter timestamps frescos e caminhos novos — o conteúdo é determinístico (o SHA do APK só muda se o patch ou o pipeline mudarem) mas a convenção OUT_DIR com timestamp evita confusão sobre qual pacote é o atual.

## 6. Referências cruzadas

- [`fase10-pre-planejamento-2026-10-20.md`](fase10-pre-planejamento-2026-10-20.md) — briefing técnico original
- [`fase10-decisao-rotas-2026-10-23.md`](fase10-decisao-rotas-2026-10-23.md) — por que Rota B
- [`MAPA.md`](MAPA.md) — atlas da central
- `../tooling/fase10/rebuild-dalauncher.sh` — rebuild do APK patcheado
- `../tooling/ota-build/build-dalauncher-fase10.py` — pacote de install
- `../tooling/ota-build/build-dalauncher-restore.py` — pacote de rollback
