# Próxima sessão — ponto de partida

Documento operacional, não teórico. Para abrir no início da próxima sessão de trabalho (seja no carro, no PC ou em pesquisa online). O KB principal (`../central-multimidia-civic-g10-kb.md`) tem o conhecimento acumulado; aqui está só o que precisa ser feito a seguir.

Última atualização: 2026-10-15, após as duas sessões no carro **e** da varredura ampla documentada em `pesquisa-rotas-sem-adb-2026-10-15.md`.

## 1. Resumo do estado em uma frase

**Rota de ADB via passcord no Settings do Android está morta** para a safra `1.F187.16` BR. Mas a varredura de 2026-10-15 identificou a rota **EvilValet** (`testkey` AOSP + `update.zip` via USB) como **substituta direta do ADB** — se funcionar, pula Fase 3 e Fase 6 inteiras. Precisa validar com experimento zero-risco em laboratório antes de descer para o carro.

**📄 Leia `pesquisa-rotas-sem-adb-2026-10-15.md` antes de continuar** — ele cataloga 8 rotas alternativas e justifica a priorização.

## 2. O que já está pronto e NÃO precisa refazer

- APK auto-OK compilado, assinado e validado estaticamente (`our-apk/app/build/outputs/apk/release/AutoOk.apk`, 12,8 KB, SHA-1 `e3b14e2b697dcdf9245e9988cb0bae8b3b504860`). Só três constantes placeholder dependendo do pull do `/system/app` para preencher.
- Ambiente de build reprodutível (JDK 17 Temurin em `~/sdks/jdk-17`, Android SDK em `~/sdks/Android`, Gradle 7.6.4 pinned via wrapper).
- Setup Mitsubishi decifrado: schema completo da whitelist, fluxo `install_mitsubishi.sh`, Honda Installer analisado (sem telemetria, sem backdoor). Nosso APK deve ir como user app via Honda Installer.
- Combo correto do menu de serviço EXL BR: `DAY/NIGHT + AUDIO + MENU` por 2s com áudio off.
- Estrutura completa do Self-Diagnosis Mode mapeada (ver `fase1-reconhecimento/achados-2026-10-15-sessao2.md`).
- Lista de ~20 sinais B-CAN com nome semântico (ver mesma referência).
- `com.mitsubishielectric.ada.*` — 64 pacotes com nome exato catalogados.

## 3. Pendência mais barata — teste do cabo novo em casa (1 min)

Antes de descer para o carro, falsifica a ressalva da ida anterior. **No notebook, com o cabo novo:**

1. Pluga um pendrive FAT32 no notebook via o cabo novo (pendrive do lado USB-A, notebook do lado USB-C).
2. Roda:

   ```
   lsusb
   journalctl -k -n 20 --no-pager
   ls /run/media/$USER/ 2>/dev/null
   ```

3. **Se aparecer o pendrive montado:** cabo tem data lines, está certo para a sessão no carro. Segue para a seção 4.
4. **Se nada aparecer:** cabo também é "só carrega". Troca por outro antes de descer.

## 4. Checklist antes de descer para o carro

- [ ] Teste do cabo novo com pendrive passou (seção 3).
- [ ] Notebook carregado (precisa durar ~30 min a 1 h).
- [ ] Celular com câmera carregada.
- [ ] Pendrive FAT32 vazio na mão (pode servir no carro — ver seção 5.3).
- [ ] Esse documento aberto num aparelho que você levar para o carro.

## 5. Plano no carro — ordem recomendada

**O que NÃO fazer na próxima sessão:** repetir tentativa de passcord via Settings. Está encerrado. Ciclo de cooldown de ~24h+ também. Zero valor.

### 5.1 Pré-condições sempre

- Carro em **ACC** (1 toque no start/stop sem freio) ou **ON** (2 toques sem freio). Motor desligado.
- Combo `DAY/NIGHT + AUDIO + MENU` por 2s com áudio off abre o menu de serviço quando precisar.

### 5.2 Primeiro teste — conectar o cabo novo na central em modo normal (zero risco)

1. Central ligada em modo normal (uso cotidiano, com relógio aparecendo).
2. Pluga o cabo entre PC e central (USB-A na central).
3. Espera 10 s. No PC:

   ```
   lsusb
   journalctl -k -n 40 --no-pager
   adb devices
   ```

4. **Se nada aparecer** no `lsusb` nem no `journalctl`: confirma de vez a conclusão da sessão anterior. Significa que sem dev mode a central engole o cabo mesmo com data lines.
5. **Se aparecer algo** (qualquer linha nova no `lsusb`, ou `usb X-Y: new ...` no `journalctl`): me manda tudo que apareceu. Mesmo que seja `unauthorized` no `adb devices`, é informação nova.

### 5.3 Segundo teste — procurar modo "USB storage" por combo físico

Alguns relatos antigos (não confirmados) dizem que centrais Honda têm modo de "USB mass storage" acessível por combo físico fora do Settings. Vale testar com cabo plugado:

- Combo A: `HOME` segurado por 5 s (atalho oficial Honda — reinicia o áudio; se abrir algo diferente, foto).
- Combo B: `AUDIO + HOME` por 5 s.
- Combo C: `AUDIO + BACK` por 5 s.
- Combo D: `AUDIO + MENU + BACK` por 5 s (3 capacitivos simultâneos).

Após cada combo, roda `lsusb` e `journalctl -k -n 10` no PC. Se qualquer um fizer o PC ver a central, me manda saída.

Esses combos não têm risco documentado. Se mesmo assim aparecer alerta na tela ou abrir algo estranho, para e me manda foto.

### 5.4 Terceiro teste — pendrive na central (se cabo não funcionou)

Pluga **o pendrive FAT32 vazio** direto na central (sem o cabo). Pode acontecer uma destas:

- Central reconhece como fonte USB (música), aparece "USB" como fonte. Esperado — zero valor.
- Central pede para "atualizar sistema" ou "escanear OTA". Se isso acontecer, para imediatamente e tira foto — pode ser rota de entrada OTA que a gente ainda não mapeou.
- Central mostra o Installer de app pedindo APK. Improvável mas documentar.

### 5.5 Quarto teste — Unit Check → USB (dentro do menu de serviço)

Na sessão 2 a gente viu `USB` como componente dentro de Unit Check e **não entrou** por precaução. Vale entrar agora e fotografar o que o teste de USB mostra. Pode render dado útil sobre VID/PID da porta ou status.

Combo `DAY/NIGHT + AUDIO + MENU` → Detail Information & Setting → Unit Check → **USB**. Foto. Return sem tocar em nada mais.

### 5.6 Quinto teste — Error History

Mesmo caminho acima, mas em vez de USB entra em `Error History`. Pode listar erros persistentes que ajudem a entender o estado do sistema. Foto. Return.

## 6. Rotas de pesquisa offline (se nada do carro render)

Ordenadas por chance de dar resultado real.

### 6.1 Thread civicx.club BR

Procurar manualmente (abrir no navegador — a WebFetch bloqueia por tollbit) por relatos de dono BR da safra `1.F187` ou `MY16ADA` que conseguiu dev mode. Não existe garantia que exista; vale 20 min de busca.

### 6.2 Analisar o kernel 3.1.10 por vulns conhecidas

Kernel 3.1.10 é de 2011/2012, pré-dirtyCOW. Além da CVE-2016-5195 (dirtyCOW, que o `root-honda` usa quando ADB está disponível), ele é vulnerável a outros LPE conhecidos (CVE-2013-2094 perf_event_open, CVE-2012-0056 /proc/pid/mem, etc.). Nenhum desses sozinho dá ADB — todos precisam de um shell local primeiro. Então não resolve o nosso problema de "não ter nem shell", mas vale catalogar para a fase 6 (root após ADB).

### 6.3 Procurar OTA pública da Honda

A `com.mitsubishielectric.ada.app.systemupdate` indica que a central aceita atualização. Se encontrarmos uma OTA zip (talvez em site de dealer, torrent de carro, github issues), dá para desempacotar e extrair os APKs sem precisar de ADB. Isso resolveria o problema do pull de `/system/app` e desbloquearia o preenchimento das 3 constantes do nosso APK. Prioridade alta.

### 6.4 Procurar binário `honda_installer.apk` de versão mais nova

A nossa cópia é de 2018 (`versionName 2.1`, `@codeage`). Se houver versão mais nova que tenha logica diferente para safras pós-patch (talvez o `@codeage` tenha atualizado sem publicar), vale.

### 6.5 Avaliar CAN bus como ponto de alavanca

Agora que a gente conhece ~20 sinais B-CAN semânticos, dá para imaginar vetores: injetar um sinal específico via OBD2 que faça a central alterar flag interna. Isso é RE pesada e especulativa. Fica como última opção.

## 7. O que NÃO vale a próxima sessão

Para evitar perder tempo:

- Repetir passcord — morreu.
- Rodar o emulador API 17 — não sobe no Fedora 44.
- Comprar o serviço do `@codeage` (US$ 25) — regra do dono.
- Instalar APKs modernos esperando que rodem em Android 4.2.2 — não roda sem backports.

## 8. Cenário de sucesso da próxima sessão

Se qualquer coisa das seções 5 ou 6 render ADB funcionando, a sequência é:

1. `adb pull /system/app` e `adb pull /system/priv-app` para `tooling/apks-dumped/`.
2. `apktool d` nos pacotes `com.mitsubishielectric.ada.app.dalauncher`, `.dasettings` e `.appmode`.
3. `grep -r "O motorista é o responsável"` ou `grep -r "disclaimer"` ou `grep -r "aviso"` nos XML/smali resultantes.
4. Nome da Activity do Aviso → vai para `AVISO_ACTIVITY_NAME` em `our-apk/app/src/main/java/com/khalleb/civichmi/autook/AutoOkConfig.java`.
5. Habilitar Pointer Location nas dev options da central, ligar o carro, bater o OK — anotar X,Y.
6. Preencher `BUTTON_OK_X` e `BUTTON_OK_Y`.
7. `./gradlew assembleRelease` no `our-apk/` (cache quente, segundos).
8. Assinar + extrair SHA-1 (comandos no `fase5-apk/compilar.md` seção 5-6).
9. Instalar via Honda Installer (opção A do README do `our-apk/`) ou via `install_mitsubishi.sh` manual (opção B). Precisa central já rooteada — ver 10 abaixo.

### 8.1 Nota sobre root

A fase 6 (root da central via `root-honda` com dirtyCOW) é a mais arriscada do projeto inteiro. **Não deve ser feita na mesma visita que gerou o ADB**. Deveria ter sessão própria com:

- Backup completo de `/system` antes.
- Carro em local ventilado, em caso de o carro precisar ficar ligado por tempo prolongado.
- Decisão consciente de aceitar o risco de brick (sem ré, troca R$ 1k-2k).

Essa sessão fica para depois do pull do `/system/app` ser feito e nós termos tempo para preparar com calma.

## 9. Resumo de 3 linhas para abrir na próxima sessão

- **Prioridade 1 (laboratório, sem risco):** construir `update.zip` com `AutoOk.apk` + testkey AOSP e validar formato — ver `pesquisa-rotas-sem-adb-2026-10-15.md` seção 4.3.
- **Prioridade 2 (laboratório):** ler `tooling/references/ic1101/docs/rooting.md` localmente (clonado pelo setup.sh) buscando método alternativo não documentado aqui.
- **Prioridade 3 (no carro):** combos físicos (5.3) + plugar o `signed.zip` em pendrive e observar o prompt (sem instalar) — rotas B e D da varredura.
