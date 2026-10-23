# Fase 10 — Checklist de execução (deploy day)

> Prep concluída em 2026-10-23. Alvo de deploy: **2026-10-27** (quando fecha a
> janela de "v0.5.4 estável por 1 semana"). Este doc é o roteiro minuto a
> minuto pro dia de ir no carro.

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
- [ ] **Pendrives preparados**:
  ```bash
  sudo tooling/scripts/prepare-pendrive-install.sh /dev/sdX tooling/ota-build/output-dalauncher-fase10/<ts>
  sudo tooling/scripts/prepare-pendrive-rollback.sh /dev/sdY tooling/ota-build/output-dalauncher-restore/<ts>
  ```
  (Se os scripts não aceitarem path arbitrário, copiar manualmente: `cp .../SwUpdate.mdt /dev/sdX1/0040/SwUpdate.mdt` + `cp .../SwUpdate2.txt /dev/sdX1/SwUpdate2.txt`.)
- [ ] **Checklist de validação dos pendrives**:
  ```bash
  diff <(sha256sum /path/to/output/<ts>/0040/SwUpdate.mdt | awk '{print $1}') <(sha256sum /mnt/usbA/0040/SwUpdate.mdt | awk '{print $1}')
  ```
  Deve dar vazio nos dois pendrives.
- [ ] **Celular carregado** — pra fotografar logs do pendrive se precisar
- [ ] **PC com acesso ao backup externo** — pra copiar logs e, se der ruim, usar `~/backup-honda-civic-g10/dump-raw-2026-10-17/*.img.gz`

## 1. Materiais pra levar

- Pendrive A (ROLLBACK) — rótulo claro, cabo USB-A → USB-A frontal
- Pendrive B (INSTALL) — rótulo claro
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
7. **Primeiro boot pós-deploy será lento** — ~10-30s a mais que o normal, porque Dalvik vai `dexopt` o `classes.dex` novo embutido no APK
8. Observar:
   - Tela liga normal? ✅
   - **Aviso NÃO aparece**? ✅ (meta da Fase 10)
   - Launcher aparece (possivelmente com configs default — wallpaper padrão, ícones em posição inicial — **se** o PackageManager tomar o caminho "new install"; ver hipótese em `fase10-decisao-rotas-2026-10-23.md`)

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

Melhor: aproveitar que o AutoOk v0.5.4 está em prod e já grava log em `/data/data/com.khalleb.civichmi.autook/files/autook.log`. Mesmo com Fase 10 bem sucedida, AutoOk vai detectar que a Activity do aviso **nunca aparece** — isso em si é um indicador.

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
2. Combo AUDIO + OK → sempre funciona porque é um input de hardware que entra no bootloader
3. Rollback

Se nada disso resolver: `~/backup-honda-civic-g10/dump-raw-2026-10-17/*.img.gz` tem backup raw do /system inteiro. Precisa de ferramenta externa pra re-flashar.

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

## 5. Pacotes OTA prontos nesta sessão

Build fresco rodado em 2026-10-23:

| Pacote | Path | SHA-256 (parcial) |
|---|---|---|
| Install | `tooling/ota-build/output-dalauncher-fase10/<ts>/0040/SwUpdate.mdt` | APK embutido: `1774136cfad10919...` |
| Rollback | `tooling/ota-build/output-dalauncher-restore/<ts>/0040/SwUpdate.mdt` | APK dentro: `1d8bd729ad309240...` (SHA do original) |

O APK patcheado é reconstruído por `tooling/fase10/rebuild-dalauncher.sh`, que deodexa o `.odex` original fresh, aplica `tooling/fase10/opening-divide-activity-skip-disclaimer.patch` (versionado), e **prova** que a única diferença de bytecode orig→patch é a classe `OpeningDivideActivity` (assemble + disassemble de ambos os lados, diff). O `build-dalauncher-fase10.py` recusa empacotar um APK que não esteja assinado com o testkey AOSP.

**Importante:** se este doc for seguido em outra data (ex: 2026-11-02), rebuildar os dois pacotes pra ter timestamps frescos e caminhos novos — o conteúdo é determinístico (o SHA do APK só muda se o patch ou o pipeline mudarem) mas a convenção OUT_DIR com timestamp evita confusão sobre qual pacote é o atual.

## 6. Referências cruzadas

- [`fase10-pre-planejamento-2026-10-20.md`](fase10-pre-planejamento-2026-10-20.md) — briefing técnico original
- [`fase10-decisao-rotas-2026-10-23.md`](fase10-decisao-rotas-2026-10-23.md) — por que Rota B
- [`MAPA.md`](MAPA.md) — atlas da central
- `../tooling/fase10/rebuild-dalauncher.sh` — rebuild do APK patcheado
- `../tooling/ota-build/build-dalauncher-fase10.py` — pacote de install
- `../tooling/ota-build/build-dalauncher-restore.py` — pacote de rollback
