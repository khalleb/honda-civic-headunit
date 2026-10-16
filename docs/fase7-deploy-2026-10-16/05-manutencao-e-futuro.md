# Manutenção, troubleshooting e roadmap futuro

Guia operacional pra quem precisa mexer no projeto depois. Como atualizar o APK, como fazer rollback, o que fazer se algo quebrar, ideias de evolução.

## Rebuild + redeploy do APK

Cenário: fez mudança no código Java ou mudou alguma constante do `AutoOkConfig.java`.

### Passo a passo

```bash
cd /home/khalleb/repositorios/honda-civic-headunit

# 1. Rebuild do APK
cd our-apk
./gradlew clean assembleRelease

# 2. Assinar
APKSIGNER=/home/khalleb/sdks/Android/build-tools/33.0.2/apksigner
$APKSIGNER sign \
  --ks ~/.android/debug.keystore \
  --ks-pass pass:android \
  --out app/build/outputs/apk/release/AutoOk.apk \
  app/build/outputs/apk/release/app-release-unsigned.apk

# 3. Copiar pro overlay
cd ..
cp our-apk/app/build/outputs/apk/release/AutoOk.apk \
   tooling/ota-build/overlay/system/app/AutoOk.apk

# 4. Verificar SHA-1 bate
sha1sum our-apk/app/build/outputs/apk/release/AutoOk.apk \
        tooling/ota-build/overlay/system/app/AutoOk.apk

# 5. Rebuild pacote OTA de instalação
rm -rf tooling/ota-build/output/*
python3 tooling/ota-build/build.py

# 6. Rebuild pacote de rollback (sempre bom manter atualizado)
rm -rf tooling/ota-build/output-rollback/*
python3 tooling/ota-build/build-rollback.py

# Scripts em tooling/scripts/ pegam automaticamente o build mais recente
# (Script pega automaticamente o build mais recente)
NEW_TS=$(ls tooling/ota-build/output/)
echo "Novo timestamp: $NEW_TS"
# Editar manualmente SRC= no script

# 8. Carregar pendrive
sudo ./tooling/scripts/prepare-pendrive-install.sh /dev/sdX
```

### Deploy no carro

Mesmo protocolo do deploy inicial:

1. Pendrive na porta USB-A frontal.
2. `AUDIO 5s` → "Quer reiniciar?" → confirma.
3. Fluxo "Software update → Copying..." → reboot → recovery → reboot normal.
4. Puxa o pendrive quando central estabilizar.
5. **Teste:** desliga/liga a chave → Aviso deve aparecer e sumir sozinho em ~10s.

### Importante: APK já existe em `/system/app`

O OTA vai **sobrescrever** o APK existente. Package name é o mesmo, Android trata como update. Caminhos a ter em mente:

- Se mudou `versionCode`: Android reconhece como update, re-dexopt. ✓
- Se não mudou `versionCode`: Android pode cachear o APK antigo. Mudar versionCode em `app/build.gradle` quando fizer mudança significativa.
- Se mudou signing cert: Android **recusa** o update (signature mismatch) — mas em `/system/app` pode funcionar porque Android trata system apps diferente. Em caso de dúvida, mantenha o mesmo keystore (debug).

## Rollback completo

Cenário: APK está causando problema, quer remover tudo (APK + su).

### Pacote de rollback

Já construído em `tooling/ota-build/output-rollback/<timestamp>/0040/SwUpdate.mdt`. Se não existir, construir:

```bash
cd /home/khalleb/repositorios/honda-civic-headunit
python3 tooling/ota-build/build-rollback.py
```

### Carregar pendrive e deployar

```bash
# Script pega automaticamente o build mais recente de output-rollback/
sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sdX
```

### Deploy no carro

Mesmo protocolo. Após deploy:
- `/system/app/AutoOk.apk` removido.
- `/system/xbin/su` removido.
- Central volta ao estado pré-nossa modificação.
- Aviso volta a aparecer normalmente, precisa clicar OK manual.

### Verificar que removeu

Depois do deploy, puxa pendrive, cola no notebook. Ler `rollback-0040.log`:

```
=== ROLLBACK START Fri Oct XX ... ===
-rw-r--r-- ... AutoOk.apk           # confirma que existia
-rwsr-sr-x ... su                   # confirma que existia
rm-done
removal-confirmed                   # confirma que foi removido
=== ROLLBACK END ... ===
```

Se o log não tem `removal-confirmed`, algo falhou. Investigar.

## Troubleshooting

### "APK deployado mas Aviso não some automaticamente"

Possíveis causas:

1. **`su` não está em `/system/xbin/`** — install.log do deploy mostra que foi gravado?

   Verificação: puxar logs do Error History pós-boot, grep por `AutoOk`:
   ```
   grep "AutoOk" logcat*
   ```
   Se houver `watcher iniciado` mas nunca `tap X,Y -> true`, problema é no logcat match ou no `su`.

2. **Needle da Activity está errado** — logcat emite com formato diferente?

   Verificação: grep por `OpeningDivideActivity` no logcat salvo. Se aparece com `.OpeningDivideActivity` (não `/.OpeningDivideActivity`), o needle precisa mudar.

3. **Coordenadas estão erradas** — layout mudou em algum update Mitsubishi?

   Verificação: entrar nos dumps mais recentes do `/system/vendor/app/DaLauncher.apk`, decompile, abrir `res/layout/mm_02_01_02.xml`, pegar coord atualizada do `btnOK`.

4. **Service morreu** — algum crash?

   Verificação: grep por `AutoOk` + stack trace no logcat. Tombstones em `/data/tombstones/`.

### "APK deployado mas central não boota"

Rollback de emergência:

1. Pega o pendrive de rollback.
2. Pluga na porta frontal.
3. `AUDIO 5s` → confirma reboot.
4. Fluxo rollback executa.
5. Central deve bootar normal.

Se nem o rollback funcionar (central em recovery loop permanente, boot loop sem fim), aí a situação é crítica. Opções:

- **Puxar fusível do radio** (fuse box interno) por 15-20 min → central fica totalmente desligada → ao religar pode tentar cold boot limpo.
- **Overnight sem bateria do pendrive** — não ajuda se já está em loop.
- **Trocar central** — última opção, R$ 1-2k. Backup da bateria do carro é tirar negativo por 15 min pra evitar surpresas.

### "APK funciona mas Aviso aparece por muito tempo antes de sumir"

Reduzir `BOOT_INITIAL_WAIT_MS` + `DELAY_SECONDS_AFTER_DETECT` em `AutoOkConfig.java`:

```java
public static final int DELAY_SECONDS_AFTER_DETECT = 1;    // era 2
public static final int BOOT_INITIAL_WAIT_MS = 2000;        // era 5000
```

Rebuild + redeploy. Testar — se o tap virar inconsistente (às vezes falha), aumentar de novo. 2+1 é o mínimo seguro observado.

### "CarPlay/Bluetooth parou de funcionar depois do deploy"

Improvável, nosso deploy só adiciona 2 arquivos novos sem modificar nada. Mas se acontecer:

1. Rollback imediato.
2. Verificar `dumps-obtidos.md` para comparar estado de `/system/vendor/app/CarPlay.apk` e `HftApService.apk` (nossos dumps são a referência pré-deploy).
3. Se os APKs estão intactos no HU (comparar SHA-1 via novo dump), problema é de outra ordem.

### "Após atualização OTA Honda, APK sumiu"

Se Honda liberar uma atualização OTA do firmware (improvável mas possível), a atualização vai:

1. Substituir `/system/app/*` inteiro — nosso APK será removido.
2. Possivelmente mudar o `custom_rom.type` do HU — nosso rom_type `0040` pode não ser mais o correto.
3. Possivelmente mudar o layout do Aviso — coordenadas podem mudar.

Procedimento de recuperação:

1. Forçar cold boot pós-atualização (`AUDIO 5s`).
2. Salvar logs via Error History.
3. Grep logs por `daupdater` para pegar o novo `cur_rom`:
   ```
   grep "daupdater" logcat* | grep "Can't open"
   ```
4. Atualizar `ROM_TYPES = ["<novo>"]` em `tooling/ota-build/build.py`.
5. Re-dumpar `/system/vendor/app/DaLauncher.apk` (via novo pacote de dump).
6. Verificar coord novo em `mm_02_01_02.xml`.
7. Atualizar coord em `AutoOkConfig.java` se necessário.
8. Rebuild + redeploy.

Esse processo foi exatamente o que fizemos pela primeira vez e documentamos aqui.

### "Após atualização OTA Honda, central foi para rom_type diferente, nossa OTA não aplica"

Se o deploy acima falhar porque `daupdater` não encontra `0040/SwUpdate.mdt` (porque o cur_rom mudou), precisa descobrir o novo:

1. Pacote OTA de **diagnóstico puro** (não instala nada, só salva info no pendrive). Script skeleton:
   ```python
   # Em build.py, trocar ROM_TYPES para range largo:
   ROM_TYPES = [f"{n:04d}" for n in range(0, 10000, 10)]  # 1000 pacotes
   # E updater-script apenas dumpa info, não escreve em /system
   ```
2. Deploy pendrive, cold boot → logs vão revelar o novo valor.
3. Rebuild com rom_type certo.

## Após atualização OTA Honda

Honda historicamente tem publicado OTAs via sitio oficial (`usb.honda.com`) + concessionária. Nosso projeto não detecta se Honda vai lançar OTA pra safra `1.F187.16` BR especificamente (improvável — safra tem 10 anos quando é 2026).

Mas se acontecer:

1. **A atualização apaga nosso APK?** Depende. Se a OTA substituir `/system/app` inteiro: sim. Se só atualizar arquivos específicos: nosso APK pode sobreviver.
2. **A atualização apaga o `su`?** Idem. Se tocar em `/system/xbin`, sim.
3. **A atualização corrige a vulnerabilidade do testkey?** Possivelmente. Se Honda trocar o keystore do recovery, EvilValet morre e precisamos de outro caminho (dirtyCOW via ADB — mas aí precisa de dev mode, que não temos sem passcord).

Mitigação: **antes de aplicar qualquer OTA Honda, fazer rollback dos nossos arquivos**. Deploy do rollback → OTA Honda → ver se continua tudo funcionando normal. Se sim, pode decidir se vale redeployar nossa modificação.

## Roadmap futuro

### Melhorias de baixo risco

1. **Reduzir delay de tap** — ajustar `BOOT_INITIAL_WAIT_MS` para 2000ms e `DELAY_SECONDS_AFTER_DETECT` para 1s. Risco: tap pode falhar se Fragment não renderizou ainda. Mitigação: feedback de `ok` boolean do `suTap` + retry.
2. **Logs persistentes do APK** — escrever para `/sdcard/` ou `/data/local/tmp/` arquivo com histórico de taps. Permite debug sem precisar coletar logcat.
3. **Watchdog self-check** — Service periodicamente verifica se LogcatWatcher ainda está vivo. Se não, re-cria.
4. **Multi-coord fallback** — tentar coord primária (400,350), se não funcionar em X segundos, tentar coord secundária (ex: 400,340 ou 450,350). Robusto a mudanças sutis de layout.

### Melhorias médio risco

5. **Modificar DaLauncher.apk** para pular `DisclaimerFragment` por completo. Decompile → smali edit → recompile → sign com testkey → OTA deploy. Risco: quebrar launcher = tela preta. Benefício: aviso realmente não aparece, zero delay.
6. **SuperSU opcional** — instalar SuperSU.apk como mediator do `su`. Benefício: gerenciamento de permissions bonito, pode auto-grant pra nosso APK, outros apps que peçam su mostram prompt. Risco: SuperSU v2.78 é de 2016, pode ter bugs em Android 4.2.2.
7. **Xposed Framework** — instalar Xposed e usar módulo pra hook `DisclaimerFragment.onCreate` e retornar sem renderizar. Risco: Xposed em Android 4.2.2 pode ser instável, requer ART ou Dalvik específico.

### Melhorias alto risco

8. **Modificar `UnitInformationManagerApService`** para fingir estado de aceite permanente do disclaimer. Nível framework, pode quebrar outras features.
9. **Flashear firmware mod customizado** — construir uma versão modificada do firmware Honda com Aviso removido no source. Requer total RE do pipeline Mitsubishi. Projeto de meses.

### Features bônus (zero risco, agregam valor)

10. **Script de setup zero-config pra outra pessoa com Civic 2017 BR** — bundle do pendrive INSTALL + instruções passo a passo. Permite comunidade usar sem precisar entender nada.
11. **Interface web pra configurar o APK** — rodar servidor local no notebook, usuário clica "deploy", script gera pacote + prepara pendrive.
12. **Rollback automatizado via botão físico** — hook num combo de teclas específico que, se pressionado durante boot, dispara rollback.
13. **Modo diagnóstico persistente** — permitir que o APK, ao receber um broadcast específico, dumpe logs e state atual pro pendrive sem precisar de novo OTA.

## Pontos de contato em caso de dúvida

- **ic1101 repo** (`tooling/references/ic1101/`): referência oficial pra EvilValet + ota-builder. Docs em `tooling/references/ic1101/docs/`.
- **root-honda repo** (`tooling/references/root-honda/`): referência pra `su` + SuperSU + whitelist Mitsubishi.
- **Juniperspring posts**: `tooling/references/ic1101/README.md` tem links.
- **Nossos dumps** (`tooling/apks-dumped/dump-0040/`): fonte da verdade do estado da central pré-nossa modificação.

## Boas práticas de contribuição futura

- **Nunca editar código em `tooling/references/*` diretamente.** São submodulos clonados. Usar monkey patch em `tooling/ota-build/` ao invés.
- **Sempre construir pacote rollback junto com install.** Rede de segurança.
- **Testar rollback pelo menos uma vez** em algum momento. Não dá para "confiar que vai funcionar quando precisar" sem ter testado.
- **Documentar qualquer mudança significativa** em `docs/fase7-deploy-2026-10-16/` ou criar `fase8-...` se mudança for grande.
- **Backup do estado atual via dump** antes de qualquer modificação significativa. 197MB cabe em qualquer pendrive.
