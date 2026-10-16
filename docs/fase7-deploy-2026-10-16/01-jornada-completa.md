# Jornada completa — 2026-10-15 à 2026-10-16

Narrativa cronológica da descoberta e do deploy. Documenta o processo de pesquisa + tentativa + erro + iteração que levou da hipótese "EvilValet talvez funcione na nossa safra" ao deploy funcional. Preserva as decisões, as hipóteses erradas, as surpresas e as correções, para quem retomar o projeto no futuro entender o porquê de cada escolha.

Formato: cronológico, marcadores de hora quando relevante, cada seção com "o que fizemos / o que achamos que ia acontecer / o que realmente aconteceu / o que aprendemos".

## Estado inicial — 2026-10-15 noite

Projeto estava em: APK auto-OK compilado com 3 constantes placeholder (`AVISO_ACTIVITY_NAME=""`, `BUTTON_OK_X=-1`, `BUTTON_OK_Y=-1`). Ambiente de build reprodutível no Fedora 44 (JDK 17 Temurin, Android SDK, Gradle 7.6.4). Setup Mitsubishi analisado (whitelist, Honda Installer). Combo correto do menu de serviço EXL BR confirmado. ~20 sinais B-CAN mapeados. 64 pacotes `com.mitsubishielectric.ada.*` catalogados.

Rota de ADB via passcord no Settings estava morta: na safra `1.F187.16` BR, a sequência `1-4-2-3` no editor de texto do Settings foi bloqueada por Honda/Mitsubishi em firmware update. Investigação do passcord ocupou 2 sessões anteriores no carro, encerradas em `docs/fase3-adb/passcord-pesquisa.md`.

Varredura ampla de rotas alternativas (fork de pesquisa de 2026-10-15) identificou 8 rotas, com **EvilValet** como a mais promissora (`docs/pesquisa-rotas-sem-adb-2026-10-15.md`). Resumo da varredura: Honda deixou a `testkey.x509.pem` pública do AOSP em `res/keys` da partição recovery, e a `verify_file` do recovery é essencialmente a do AOSP stock. Qualquer `update.zip` assinado com a `testkey.pk8` passa.

Fontes consultadas da vulnerabilidade:
- [juniperspring.org/posts/honda-evil-valet](https://juniperspring.org/posts/honda-evil-valet/) — post de anúncio do autor (librick / Eric McDonald), publicado 2026-06-13. É contexto do ataque + nomenclatura, não writeup técnico — o próprio autor explicitamente avisa que o post "is not intended as a technical writeup".
- [`tooling/references/ic1101/docs/updates.md`](../../tooling/references/ic1101/docs/updates.md) — **documento técnico operacional** do mesmo autor, com fluxo detalhado do `daupdater`, estrutura do pacote, checklist completa, risco de recovery loop. **Essa foi nossa fonte primária técnica real** — guiou todas as nossas decisões de design.

Confirmações públicas do EvilValet antes da nossa:
- Civic 2021 US (safra `1.F1A5.15`, rom_type `1115`) — pelo autor no próprio headunit dele.
- Update file EU `MRC_EU_SW_v12_4.zip` (`1.F197.70`, rom_type `2250`) — autor inspecionou assinatura via hex-dump, confirmou testkey. Não é o headunit dele.

Nossa safra `1.F187.16` BR nunca testada publicamente.

Objetivo da sessão: testar EvilValet na nossa safra.

## Primeira tentativa — rom_type range pequeno (2026-10-15 ~20h)

Construímos o primeiro pacote via `ic1101/ota-builder` (clonado em `tooling/references/ic1101/`), com rom_types `1110`, `1115`, `1118`, `1120`, `2250`. Justificativa:

- `1115` é o rom_type confirmado da safra 2021 US (ic1101 docs).
- `2250` é o rom_type de um update file EU capturado publicamente.
- `1110`, `1118`, `1120` foram palpites baseados em possível espaçamento linear de rom_types na família 11XX.

Pacote assinado com testkey AOSP (SHA-256 do cert: `A4:0D:A8:0A:59:D1:70:CA:A9:50:CF:15:C1:8C:45:4D:47:A3:9B:26:98:9D:8B:64:0E:CD:74:5B:A7:1B:F5:DC`). Pendrive formatado em FAT32 MSDOS (não superfloppy — recovery AOSP exige tabela de partição).

Levamos para o carro. Protocolo: pendrive na porta USB-A frontal, virar a chave em ACC, esperar.

**Resultado:** nada. Apareceu barra de progresso rápida sobre o logo Honda (não era do recovery — era boot normal) e depois a tela de Aviso normal. Clicamos OK manual, central voltou ao normal.

**O que aprendemos aqui — primeira surpresa:** virar a chave em ACC **não é cold boot**. A central Honda entra em sleep profundo quando o carro desliga, mas o kernel não reboota. Virar a chave só acorda do suspend. `daupdater` só roda em cold boot (via `startBootAnim` do `libsurfaceflinger.so`), então ele não escaneou o pendrive. Essa descoberta demoraria horas para ser confirmada.

**Nessa fase ainda achávamos:** "nenhum rom_type bateu".

## Segunda tentativa — range ampliado para 26 rom_types

Hipótese: o rom_type real está perto dos conhecidos mas não exatamente neles. Ampliamos para `1100, 1105, 1110-1125, 1130, 1135, 1140, 1150, 2250, 2251, 2252, 2260`.

Também adicionamos ao updater-script um dump: `/system/build.prop` e `/system/vendor/build.prop` para o pendrive, para que se qualquer rom_type batesse, voltássemos sabendo o valor real.

Testamos no carro. **Mesmo resultado:** barra rápida de boot, aviso normal, nada no pendrive.

Nessa altura ficou claro que algo estava sistematicamente errado. Possibilidades:
- Rom_type fora do range (improvável agora com 26 valores).
- Daupdater não existe/não roda na safra BR.
- Pre-mount do pendrive bloqueando daupdater (ele checa se outro serviço mountou primeiro).
- Algum outro bloqueio de nível framework.

## Terceira tentativa — range gigante + diagnóstico

Expandimos para **352 rom_types**: `1000-1250` + `2200-2300`. Pacote de 72MB total. Também mudamos o updater-script para dump de várias partições candidatas (SDA, SDA2, SDC, MITSU, LOG, UDA, CAC) além de `by-name/` listing e `getprop`.

Novo problema que surgiu: nada no pendrive de volta mesmo com 352 valores. **Novamente barra rápida sobre o logo, nada mais.**

Nessa altura: estava claro que ou (a) daupdater não roda, ou (b) nenhum rom_type bate numa faixa razoável.

Decidimos deixar overnight para forçar cold boot "natural" (carro desligado por longas horas talvez disparasse cold boot ao religar na manhã seguinte).

## Overnight (2026-10-15 noite → 2026-10-16 manhã)

Pendrive conectado na porta frontal, carro desligado, chave fora. Esperamos ~12h.

**Resultado na manhã seguinte:** ligamos o carro, nada. Barra padrão de boot sobre o logo, tela de Aviso, OK manual. Pendrive de volta no notebook: zero arquivos novos.

Já estávamos considerando que a safra BR tinha o daupdater **removido** do fluxo de boot.

## O break — Error History salvo pela central (2026-10-16 manhã, ~9h)

Antes de abandonar EvilValet, pedimos ao usuário para entrar no menu de serviço (`DAY/NIGHT + AUDIO + MENU` por 2s com áudio off) → `Error History` → clicar "Save". A central salvou **logcat completo + kmsgcat (kernel) + exception dumps + PowerLog** diretamente no pendrive. Primeira vez que vimos esse mecanismo em ação. Ouro.

Análise dos logs revelou dois pontos **críticos**:

1. **Kernel uptime quando o pendrive foi detectado:** `~9420 segundos` (~2h37min). O cold boot aconteceu muito antes do pendrive ser plugado. O pendrive entrou por hot-plug depois do daupdater já ter rodado.

2. **Nossa safra usa nomes de partição by-name DIFERENTES do ic1101 docs:** vimos `CAC, LOG, SDA, SDA2, SDC, UDA, MITSU` no kmsg. **`APP` e `CAP` não aparecem no e2fsck** porque são `ro,wait` (não precisa de check). Nessa altura hipotetizamos que a safra BR tinha renomeado as partições, perdido `APP`/`CAP`, trocado por outros nomes.

Isso explicava a terceira tentativa (overnight): a safra BR poderia ter mudado o layout da partição e nosso updater-script tentava montar partições que não existiam.

**Mas ainda não tínhamos entendido:** o problema real era "não houve cold boot", não "partição errada". O overnight sleep da central não é cold boot, é sleep profundo. Só reinicia o Android via `AUDIO 5s` ou puxar fusível.

## Combo AUDIO 5s descoberto por acaso (2026-10-16 ~10h)

Já desesperados por fazer cold boot, testamos uma série de combos físicos:
- `DAY/NIGHT + AUDIO + MENU` por 20-30s → só abre Service Mode (combo curto já conhecido)
- `AUDIO` sozinho por 5s → ← **"Quer reiniciar?" apareceu!** PROMPT real de reboot da central.
- Confirmamos → central reiniciou de verdade (cold boot).

Esse é o combo que estava faltando. Documentação do ic1101 (safra US 2021) não menciona esse combo. Pode ser safra-específico BR ou apenas não documentado.

A partir desse momento, EvilValet virou testável de verdade.

## Primeiro cold boot com pacote diag — descoberta do rom_type

Fizemos novo cold boot com o pendrive plugado (352 rom_types + updater diag). Pela primeira vez, kernel uptime baixo (49 segundos no save pós-boot).

Grep no logcat novo:

```
E daupdater: getNewDaVersion(228):Can't open /mnt/usbdrive1/0040/SwUpdate.mdt
E daupdater: getNewCustomRomType(383):Can't open /mnt/usbdrive1/0040/SwUpdate.mdt
```

**O rom_type real é `0040`.** Nosso range `1000-1250 + 2200-2300` nunca cobriu `0040` (3 ordens de grandeza off). Daupdater existe sim, roda sim, encontra sim o SwUpdate2.txt — só que foi procurar numa pasta `/mnt/usbdrive1/0040/` que não existia no pendrive.

Essa foi a primeira grande vitória da sessão. EvilValet aplica à nossa safra. Era só o rom_type que estava completamente off.

Também confirmamos:
- Partições by-name reais incluem `APP → mmcblk0p3` e `CAP → mmcblk0p2`. Elas EXISTEM na safra BR, só que o e2fsck as pulava porque são `ro,wait`.
- `MITSU → mmcblk0p5` é partição extra Mitsubishi, única da safra BR.

## Reconstrução cirúrgica com rom_type 0040

Novo pacote só com rom_type `0040` (mais 20 adjacentes por redundância, `0030-0050`). Updater-script com dump completo. Testamos.

**Resultado:** barra 100% apareceu, ficou por 30s (nosso sleep), reiniciou. Primeira vez que vimos o fluxo recovery completo funcionar.

Pendrive de volta no notebook: **`result.log` com dois `OK`**. Mas ZERO arquivos diag no pendrive.

Investigação revelou outro problema: **o recovery da nossa safra NÃO tem `/sbin/sh`.** Só `adbd, disp_com_cid, earlyrvc, logcat_recovery, logrotate_recovery, recovery, ueventd, watchdogd`. Nosso updater-script fazia `run_program("/sbin/sh", "-c", "...")` que falhava silenciosamente (edify segue adiante quando run_program retorna != 0). O updater-script completava com sucesso mas sem fazer nada útil.

## Busybox embarcado — unlock de todo o resto

Solução: embarcar um `busybox` ARM estático no pacote OTA, extraí-lo em `/tmp/busybox` com `package_extract_file`, usar como shell em `run_program("/tmp/busybox", "sh", "-c", ...)`.

Onde achar busybox ARM pré-compilado? **No próprio `HondaHack.apk`** (`tooling/apks-decoded/HondaHack/res/raw/busybox`, 1.1MB, ARM estático, com hush shell). Copiamos para `tooling/ota-build/bin/busybox` e integramos no build.

Durante a integração, descobrimos um bug no `build.py`: faltava a linha `upstream.stage_tree = _patched_stage_tree`. O monkey patch definia a função patched mas nunca a instalava no módulo upstream. Isso significava que **tentativas anteriores também não incluíam o busybox no pacote** — e a razão de nunca termos pegado isso antes era que o updater-script usava `/sbin/sh` (que não existia) então falha silenciosa dupla.

Correção simples, uma linha. Rebuild.

## Dump completo do /system

Com rom_type certo + busybox embarcado, construímos pacote de **dump total** (ler-only, não escreve nada no HU):

- Monta `APP` em `/system` via edify
- Monta `CAP` em `/tmp/ven` (vendor)
- `busybox cp -a /system/app/. /mnt/usbdrive1/dump-0040/system-app/`
- Idem para `priv-app`, `framework`, `vendor/app`, `etc`, `build.prop`

Teste no carro. Pendrive volta com **197MB de dados**:

- 40 APKs em `/system/app/`
- 125MB em `/system/vendor/app/` (todos os apps Mitsubishi — DaLauncher, DaSettings, CarPlay, Navigation, ~50 apps)
- 25MB de framework (parcial — symlinks como `honda-framework.jar` não copiaram, FAT32 não suporta)
- `/system/etc/` completo
- `/system/build.prop` e `/system/vendor/build.prop` em texto puro

**Pela primeira vez temos o `/system` da central no notebook, sem ADB.** Fase 4 do projeto original (análise estática de APKs do sistema) destravada.

## Localização da Activity do Aviso + coordenadas

Decompile do `DaLauncher.apk` via `apktool`:

```
res/anim/disclaimer_hide.xml
res/anim/disclaimer_show.xml
res/layout/mm_02_01_02.xml  ← layout do Aviso
res/values-pt/strings.xml:
    STR_MM_02_01_02_RES_01 = "OK"
    STR_MM_02_01_02_RES_04 = "O motorista é o responsável pela condução..."
    STR_MM_02_01_02_RES_05 = "Aviso"
```

Dentro do `mm_02_01_02.xml`:

```xml
<AbsoluteLayout>
  <com.mitsubishielectric.uilib.view.custom.AbsoluteLayoutExtState
      android:id="@id/btnOK"
      android:layout_width="354.0px" android:layout_height="44.0px"
      android:layout_x="223.0px" android:layout_y="328.0px">
    <AutoAdjustTextView android:text="@string/STR_MM_02_01_02_RES_01" .../>
  </AbsoluteLayoutExtState>
</AbsoluteLayout>
```

**Botão OK:** posição (223, 328), tamanho 354×44. Centro: **(400, 350)**. Resolução da central: 800×480 (confirmado no kmsg: `hwcomposer: Display 0 is 800 x 480`).

HondaHack.apk estava ofuscado com Tencent StubShell (anti-reverso chinês), inútil para análise de smali. Mas o `DaLauncher` original estava em claro.

Para descobrir qual Activity contém o `DisclaimerFragment`, deodex do `DaLauncher.odex` com `baksmali-2.5.2.jar` (do ic1101/apk-rebuilder/input/). Framework incompleto (symlinks honda-framework não copiados), mas 575 arquivos smali foram gerados mesmo com erros parciais. Grep:

```
new-instance Lcom/mitsubishielectric/ada/app/dalauncher/DisclaimerFragment;
```

Match único: `OpeningDivideActivity.smali` linha 640. Confirmado — a Activity que monta o `DisclaimerFragment` é `com.mitsubishielectric.ada.app.dalauncher.OpeningDivideActivity`.

Nome completo com `/.` no formato que o logcat usa:
```
com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity
```

## Build do APK auto-OK com needle correto

Preenchemos `AutoOkConfig.java`:
- `AVISO_ACTIVITY_NAME = "com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity"`
- `BUTTON_OK_X = 400`
- `BUTTON_OK_Y = 350`

**Primeiro bug encontrado durante build:** D8 (dexer) 4.0.52 do Android Gradle Plugin 7.4.2 crasha com NullPointerException ao processar `AutoOkService$1.class` e `LogcatWatcher$1.class`. Esses são as anonymous inner classes do Service (`new LogcatWatcher.OnDetected() { ... }` e `new Runnable() { ... }`).

Causa: bug conhecido do D8/R8 em certos padrões de anonymous inner. Workaround: converter para **named inner classes** (`AvisoCallback` em AutoOkService, `WatchRunnable` em LogcatWatcher). Build passou.

APK compilado 12794 bytes, assinado com debug keystore. SHA-1 do APK: `83c20d973fb3a6df44dffd6721f903e11fc46c5c` (depois disso teve o fix de persistência).

## Construção do pacote INSTALL definitivo

Updater-script final (para rom_type `0040`):

1. Extract `busybox` para `/tmp/busybox` + `set_perm 0,0,0755`
2. Edify `mount("ext4", "EMMC", "/dev/block/platform/sdhci-tegra.3/by-name/APP", "/system")`
3. Extract `AutoOk.apk` para `/system/app/AutoOk.apk` + `set_perm 0,0,0644`
4. `busybox mkdir -p /system/xbin` (idempotente)
5. Extract `su` (do root-honda, 133KB ARM estático) para `/system/xbin/su` + `set_perm 0,0,06755` (setuid+setgid+rx group/world)
6. Edify `unmount("/system")`
7. Sleep 30s para janela de retirada do pendrive

Pacote final: 1.6MB uncompressed, 211KB compressed (zip + testkey signature).

**Pacote ROLLBACK em paralelo:** mesma receita mas em vez de extract+set_perm, faz `busybox rm -f /system/app/AutoOk.apk /system/xbin/su`. Rede de segurança pronta no notebook.

## Deploy no carro + primeira execução + bug de persistência

Deploy OTA via pendrive. Fluxo "Software update → Copying" funcionou direto. Central reiniciou.

Logs pós-deploy:
```
10:42:57 PackageManager: /system/app/AutoOk.apk changed; collecting certs
10:43:28 am_proc_start: com.khalleb.civichmi.autook/.BootReceiver
10:43:28 AutoOk: watcher iniciado, aguardando com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity
10:43:37 AutoOk: tap 400,350 -> true     ← SUCESSO! aviso tappado automaticamente
```

Aviso sumiu rapidamente no primeiro boot pós-deploy. Mas usuário notou: ao desligar a chave e religar, aviso apareceu de novo e **não foi tappado**.

Diagnóstico via logs: `am_proc_start` do AutoOk só UMA vez em todos os logs. Causa: nosso `onAvisoDetected()` fazia `stopSelf()` depois do primeiro tap. Service morreu. Religar a chave não é cold boot (confirmado), então `BOOT_COMPLETED` não dispara, Service não re-inicia, Aviso aparece sem interceptação.

Correção simples: remover `stopSelf()`, adicionar `rearmWatcher()` que:
- Aguarda `REARM_DELAY_SECONDS = 10` após tap
- Reseta `handled = false`
- Mata o watcher antigo e cria novo

Service fica vivo pra sempre, pronto para múltiplas intercepções por boot.

Rebuild APK (SHA-1 final `e76d35741c5fafb8289f97f9565aaf8e1bff4f66`). Novo pacote OTA. Novo deploy no carro.

## Resultado final

Teste pós-deploy:
- Desliga a chave → central vai pra sleep profundo
- Liga a chave → central acorda, Aviso aparece
- ~10 segundos depois, aviso some sozinho
- Repete em todos os ciclos

Confirmado pelo usuário: "Agora deu certo! Espera uns 10 segundo e clica sobre o 'OK'".

Projeto encerrado. Fase 7 bem-sucedida.

## Lições aprendidas

1. **Virar a chave NÃO é cold boot** na central Honda. Precisa `AUDIO 5s` + "Quer reiniciar?" para forçar cold boot real. Sem cold boot, `BOOT_COMPLETED` não dispara em apps 3rd party instalados em `/system/app`.

2. **Rom_type pode estar muito fora do range "razoável"**. Nosso `0040` nunca teria sido palpite inicial — o range típico documentado (1115, 2250) nos levou a cobrir `1000-2300` que nem incluía `0040`. **Para safras novas, primeiro passo é SEMPRE forçar cold boot e grep `daupdater` nos logs** — o próprio daupdater loga `Can't open /mnt/usbdrive1/<rom>/SwUpdate.mdt` e aí você tem o valor exato.

3. **Recovery da safra BR não tem shell nativo (`/sbin/sh`)**. Precisa embarcar busybox ARM estático no pacote. O `busybox` do próprio `HondaHack.apk` serve.

4. **D8 4.0.52 tem bug com anonymous inner classes**. Workaround: usar named inner classes. É padrão de código melhor de qualquer forma.

5. **Edify `run_program` NÃO aborta quando o programa retorna != 0** — o script segue. Isso é bom pra permitir "best effort", mas significa que `result.log` pode mostrar `OK` mesmo que nada tenha executado. Sempre dumpar logs auxiliares para o pendrive para verificar execução real.

6. **FAT32 não suporta symlinks nem ownership**. `cp -a` em diretórios com symlinks (como `/system/framework/`) perde os links. Para dump completo com symlinks, precisaria de ext2 ou similar — mas aí recovery não monta sem driver específico. Alternativa: usar `cp -L` (follow symlinks) ou tar + copy do tar.

7. **O APK auto-OK precisa ser PERSISTENTE**. `stopSelf()` após o primeiro tap mata o Service. Em safras onde BOOT_COMPLETED só dispara em cold boot (como a nossa), Service morto não se recupera. Design correto: watcher sempre vivo, re-arma após cada tap.

8. **ADB NÃO É NECESSÁRIO para dump completo do /system**. Via OTA + busybox embarcado + partição montada em recovery, dá para ler e escrever qualquer coisa em `/system` sem precisar enumerar USB em modo dev. Isso é um ganho enorme pra safras BR onde dev mode é bloqueado.

9. **Honda deixa `testkey` AOSP em release-keys partition da safra BR também**. Confirmado. Mesmo risco de segurança do que a safra 2021 US publicada pelo juniperspring. Essa vulnerabilidade transcende safras (provavelmente é descuido sistêmico do pipeline de build Mitsubishi).

10. **PowerLog da central mostra ciclos reais**, não ciclos de "chave on/off". Diferencia cold boot de resume de suspend. Fonte: `Error History → Save` do menu de serviço. Ferramenta de debug poderosa e sub-documentada.
