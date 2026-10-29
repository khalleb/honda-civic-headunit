# 09 — Fase 10: remover o aviso de vez (patch no DaLauncher)

Este guia é pra quem quer aplicar a **Camada 2** da solução — o patch smali no `DaLauncher.apk` que faz o aviso **não aparecer mais** no fluxo de boot. Já aplicada com sucesso no Civic 2017 EXL BR em 2026-10-29 (ver [`../fase10-deploy-2026-10-29/README.md`](../fase10-deploy-2026-10-29/README.md)).

**Pré-requisito obrigatório:** Camada 1 (AutoOk) já deployada e estável por pelo menos uma semana. A Fase 10 **substitui** o aviso por uma tela curta de ecoscore (~1 s) e precisa das 4 chamadas pós-aviso que o AutoOk também desencadeava, então ter os dois ativos é a configuração mais segura durante a transição.

## Por que fazer

| Com | Experiência | Risco |
|---|---|---|
| Só Camada 1 (AutoOk) | Aviso aparece e some em ~3 s | Mínimo |
| **Camadas 1 + 2 (Fase 10)** | **Aviso não aparece.** Tela de ecoscore por ~1 s | Médio (patch no launcher principal, rede = pacote de restore do DaLauncher) |

A Camada 2 vale a pena se o ruído visual do aviso em cada boot incomoda você. Senão, pode parar na Camada 1.

## O que o patch faz

Dentro de `com.mitsubishielectric.ada.app.dalauncher.OpeningDivideActivity` (a Activity do aviso), uma linha do bytecode decide entre dois destinos:

- `sDisclamerFlg == false` → `DisclaimerFragment` (o aviso que você conhece)
- `sDisclamerFlg == true`  → `EcoFragment` (caminho que estava morto porque o flag sempre começa `false`)

Nosso patch 1 ignora o flag:

```diff
     sget-boolean v0, Lcom/mitsubishielectric/ada/app/dalauncher/OpeningDivideActivity;->sDisclamerFlg:Z

-    if-nez v0, :cond_9
+    goto :cond_9

     invoke-direct {p0}, Lcom/mitsubishielectric/ada/app/dalauncher/OpeningDivideActivity;->createDisclaimerOnHomeIntent()Landroid/content/Intent;
```

Resultado: sempre vai pro `EcoFragment`, que dispara em `startNextActivity()` **as 4 chamadas que CarPlay/Navegação/SystemDisplay esperam** depois do aviso ser passado — então nada quebra.

Patch 2 (Fase 10.1) reduz o timer do EcoFragment:

```diff
     iget-object v0, p0, ...->mNoOperationTimer:Lcom/mitsubishielectric/ada/app/dalauncher/CommonTimer;

-    const/16 v1, 0x1388        # 5000 ms
+    const/16 v1, 0x1f4         # 500 ms

     invoke-virtual {v0, v1, v2}, ...CommonTimer;->start(ILcom/mitsubishielectric/ada/app/dalauncher/CommonTimer$TimerCallBack;)V
```

Tela Eco fica visível por ~1 s em vez de ~6 s. Deixar 500 ms (não 0 ms) é necessário porque o AutoOk v0.5.4 continua tapando `(400, 350)` ~1 s depois do boot — com 500 ms o tap ainda cai no fundo seguro do EcoFragment (sem botão clicável nos layouts `mm_07_04_06`/`_ziba`).

## Pré-requisitos

### Hardware
- Civic G10 BR com Camada 1 (AutoOk v0.5.4) já aplicada e estável
- **2 pendrives FAT32** (ou 1 pendrive e preparar duas vezes — veja §0 do checklist detalhado)
- PC Linux

### Software no PC
- JDK 17 (`~/sdks/jdk-17/bin/java` ou `/usr/lib/jvm/java-17-openjdk-devel`)
- Android SDK build-tools 33.0.2 (pro `apksigner` e `zipalign`)
- Python 3.12 com stdlib (sem extras)
- Dump do `/system/vendor/app/DaLauncher.apk` + `DaLauncher.odex` da sua safra em `tooling/apks-dumped/dump-0040/vendor-app/` — vem do processo de descoberta da safra, ver [`03-descobrindo-sua-safra.md`](03-descobrindo-sua-safra.md)

### Verificar invariante
```bash
python3 -m unittest discover -s tooling/ota-build/tests
# Esperado: 42 testes OK
```

## Passo 1 — Construir o APK patcheado

```bash
cd honda-civic-headunit
export PATH="$HOME/sdks/jdk-17/bin:$PATH"
bash tooling/fase10/rebuild-dalauncher.sh
```

O script:
1. Deodexa fresh o `DaLauncher.odex` com baksmali
2. Aplica os dois patches versionados (`opening-divide-activity-skip-disclaimer.patch` + `eco-fragment-reduce-timer.patch`)
3. Verifica que cada patch caiu no lugar certo
4. Monta o `classes.dex` novo com smali
5. **Prova** que a diferença orig→patch no bytecode é **exatamente** `EcoFragment.smali` + `OpeningDivideActivity.smali` (falha senão)
6. Reempacota o APK, remove META-INF antigo, injeta `classes.dex`
7. Zipaligna 4
8. Assina com testkey AOSP
9. Verifica que o cert é o testkey AOSP esperado

Saída:
```
OK.
  saida:  tooling/fase10/output/DaLauncher-fase10.apk
  size:   17798948 bytes
  cert:   a40da80a... (testkey AOSP)
  sha256: 65481d45acd01ad67359b1174b57150eecb959377bde3379a30e2eb17a8d4a4c
```

## Passo 2 — Construir os pacotes OTA

```bash
# Install da Fase 10 (vai aplicar o APK patcheado)
python3 tooling/ota-build/build-dalauncher-fase10.py

# Restore do DaLauncher original (rede de segurança — use para abortar)
python3 tooling/ota-build/build-dalauncher-restore.py
```

Resultado: dois pacotes em `tooling/ota-build/output-dalauncher-{fase10,restore}/<timestamp>/0040/SwUpdate.mdt`. Guarde os SHA-256 impressos pra conferir depois.

## Passo 3 — Preparar os pendrives

```bash
# Pendrive A — ROLLBACK (rede de segurança, aplica PRIMEIRO para validar o caminho)
sudo tooling/scripts/prepare-pendrive-rollback.sh /dev/sdX tooling/ota-build/output-dalauncher-restore

# (depois do §4 validado, repita o processo com Pendrive B)
# Pendrive B — INSTALL (aplica o patch de verdade)
sudo tooling/scripts/prepare-pendrive-install.sh /dev/sdY tooling/ota-build/output-dalauncher-fase10
```

O script pede `yes` antes de limpar o pendrive, mostra modelo+rótulo+conteúdo, grava, confere o SHA-256 lido do pendrive contra o build e desmonta. **Se o SHA não bater, termina com erro e o pendrive não vai pro carro.**

## Passo 4 — Validação do rollback no carro (NO-OP intencional)

**Antes de instalar nada novo**, aplique o pacote de rollback. Como o DaLauncher no seu carro atual = DaLauncher original esperado pelo rollback, isso é um **no-op bytes idênticos**: valida mount + extract + perms + md5 + loop break + unmount sem risco real.

1. Pendrive A na porta USB-A frontal
2. Chave em ON (não START)
3. **AUDIO 5 s** → "Reiniciar?" → **OK**
4. Esperar ~2 min, puxar o pendrive quando a tela acender a terceira vez
5. **No PC**, plugar o Pendrive A e conferir:
   - Existe `ROLLBACK-RESTORED.OK` (e **não** existe `.FAIL`)
   - No `dalauncher-restore-0040.log`:
     - `restore-verified-OK`
     - `mv-trigger-exit=0`, `rm-copy-complete-exit=0`
     - `chown-exit=0 chmod-exit=0` nas duas linhas `perm` (APK e odex)

Se qualquer gate falhar: **não prossiga para o passo 5.** Investigue antes.

## Passo 5 — Deploy da Fase 10

Só prosseguir se §4 passou tudo.

1. Pendrive B na porta USB-A frontal
2. Chave em ON
3. **AUDIO 5 s** → "Reiniciar?" → **OK**
4. Esperar ~2 min, puxar o pendrive na terceira tela
5. **Primeiro boot pós-deploy será lento** (~10-30 s a mais — Dalvik vai `dexopt` o `classes.dex` novo)
6. **No PC**, plugar o Pendrive B e conferir:
   - Existe `FASE10-ODEX-REMOVED.OK` (e **não** existe `.FAIL`)
   - No `dalauncher-fase10-0040.log`:
     - `chown-exit=0 chmod-exit=0` na linha `perm /system/vendor/app/DaLauncher.apk`
     - md5 pós-deploy do APK bate com o SHA que o `rebuild-dalauncher.sh` imprimiu (prova positiva: é o APK patcheado no lugar, não um restore silencioso)

## Passo 6 — Validar no uso real

Dê a volta no quarteirão. Confira:
- Aviso **não aparece**
- Tela "-eco-" aparece por ~1 s em cada ligar do carro
- CarPlay projeta normalmente
- Navegação funciona
- Câmera de ré funciona
- Chamadas Bluetooth funcionam
- Botões do volante funcionam

Monitore por 1 semana. Se tudo OK, você pode (opcional) rodar o rollback do próprio AutoOk pra liberar o `/system`:

```bash
sudo tooling/scripts/prepare-pendrive-rollback.sh /dev/sdX tooling/ota-build/output-rollback
```

Isso remove `/system/app/AutoOk.apk` + `/system/xbin/su`. O patch da Fase 10 continua ativo porque está no `DaLauncher.apk` em si.

## Se der errado

| Sintoma | Ação |
|---|---|
| Launcher não aparece (tela preta ou boot loop) | Aplique o Pendrive A (rollback). Boot normal volta porque o DaLauncher original é restaurado. |
| Launcher aparece mas aviso ainda aparece | Patch pode não ter sido aplicado. Confira o md5 do APK no `dalauncher-fase10-0040.log`. |
| CarPlay não projeta | O caminho Eco pode não ter emitido o `setDisplayPermission`. Investigue o `logcat.txt` do pendrive. |
| Boot loop verdadeiro (central reboota continuamente) | Pendrive A antes do keyon + AUDIO 5 s. Se nem assim resolver: `~/backup-honda-civic-g10/dump-raw-*.img.gz` + ferramenta externa. |

Decision tree completa: [`06-troubleshooting.md`](06-troubleshooting.md). Checklist detalhado minuto-a-minuto: [`../fase10-execucao-2026-10-27.md`](../fase10-execucao-2026-10-27.md).

## Entendendo o que acontece por dentro

Veja [`DISCOVERIES.md`](../../DISCOVERIES.md) para os detalhes técnicos:
- Como o `sDisclamerFlg` é um `static boolean` em memória que reseta `false` a cada boot
- Por que o caminho Eco (`createEcoIntent()`) existia mas nunca rodava antes do patch
- Quais são as 4 chamadas que o `EcoFragment` dispara que mantêm o resto do sistema funcionando

Timeline completo do deploy real em [`../fase10-deploy-2026-10-29/README.md`](../fase10-deploy-2026-10-29/README.md).

Discussão da decisão de rota (resign com testkey AOSP vs. odex-level patch): [`../fase10-decisao-rotas-2026-10-23.md`](../fase10-decisao-rotas-2026-10-23.md).
