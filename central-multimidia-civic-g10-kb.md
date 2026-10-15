# Base de Conhecimento — Central Multimídia Honda Civic G10 (2016–2017)

Documento vivo. Objetivo: virar especialista nessa central e avaliar, com base técnica, se dá pra
eliminar a tela de "Aviso" da partida sem depender do Honda Hack. Nada aqui foi executado no carro —
é pesquisa/engenharia reversa de leitura.

## Alvo (unidade estudada)

- Honda Civic 2017 **EXL**, fabricado no Brasil (VIN prefixo `93H...` = Brasil; 10º dígito = ano modelo).
- Central: Display Audio 7" (botões capacitivos laterais AUDIO/HOME/+VOL-/MENU/BACK; botão físico DAY/NIGHT acima da tela — **sem presets numerados 1-6 e sem knob giratório na central**, isso é da versão LX).
- **Confirmado via Settings → Sobre o dispositivo e menu de serviço (sessão de 2026-10-15, ver `docs/fase1-reconhecimento/achados-2026-10-15.md`):**
  - Model Number: **`MY16ADA`** (Model Year 2016, Android Display Audio)
  - Software (número da versão): **`1.F187.16`**
  - Android: **4.2.2** build `-55`
  - Kernel: `3.1.10+` build `jenkins@NDYWY3861584 #1 Thu Apr 7 18:50:54 JST 2016`
  - Bootloader **DBOOT**: `1.10_20160407183722` (mesma data do kernel — a central foi flashada numa única imagem)
  - Software loader: `1.F187.16` (bate com a versão de apps)
  - System µCom (microcontrolador): `H62F0N 71.55.13` (Renesas/Hitachi family)

> **Nota:** VIN completo, device serial e dados privados do veículo foram
> removidos desta documentação. Se você está adaptando pro seu próprio Civic,
> colete esses dados do seu veículo diretamente.
- Tem CarPlay/Android Auto com fio de fábrica. Dono usa dongle de CarPlay sem fio (emula iPhone).
- Dor: a tela "Aviso" (OK) na partida bloqueia o acesso ao CarPlay até tocar OK. Confirmado em teste:
  a tela some sozinha em ~30s para o relógio, mas qualquer toque volta ao Aviso; o CarPlay NÃO sobe
  sozinho — sempre exige o OK.

## 1. Hardware (confirmado via ic1101 — projeto RE do librick)

- **SoC: NVIDIA Tegra 3** (quad-core ARM Cortex-A9 ARMv7, ~2012)
- **Framework da HMI: Mitsubishi** (codinome "Andromeda")
- **Namespace Android: `com.clarion.displayaudio.*`** — a Mitsubishi comprou a Clarion em 2015, por
  isso o namespace Clarion no software Mitsubishi
- **Board NVIDIA: VCM30T30** (visto em fstab e init.rc da nossa unidade dumpada)
- Part numbers vistos para Civic 2016–2018 Display Audio: família `39101-TBA-A__` (ex.: `-A21-M1`,
  `-A31`). Part number exato da unidade BR ainda não confirmado.

### CORREÇÃO IMPORTANTE: Civic 2016–2021 usa A MESMA central

Entendimento inicial estava errado. A unidade do Civic G10 é a mesma em todo o período 2016–2021
(exceto trims mais baixos tipo 2021 LX). Isso inclui nossa unidade 2017 BR. Portanto:

- **Todo o trabalho de RE do ic1101 se aplica diretamente ao Civic 2017** ✅
- **Imagens de boot/recovery** disponíveis em `ic1101/headunit-files/` (mtd1-recovery.img, mtd2-boot.img)
- **init.rc, fstab, binaries** disponíveis em `ic1101/headunit-files/boot-ramdisk/`
- **Datasheets Tegra 3, eMMC, conectores** disponíveis em `ic1101/datasheets/`

### Diferenciar das OUTRAS centrais Honda (que NÃO são a nossa)
1. **Honda Connect (Europa, 2015 Civic/CR-V Tourer):** NVIDIA Tegra, Android 4.0.4. Outra plataforma.
2. **Trims baixos (2021 Civic LX):** central diferente, não aplicável.

## 2. Software / arquitetura

- **Android 4.2.2 (Jelly Bean, 2012/2013)** — confirmado em unidades Pilot/Ridgeline/Civic. Versão
  bastante antiga; muitos APKs modernos não rodam, por isso a comunidade caça builds velhos de apps.
- **Namespace de sistema:** no Civic 2017 EXL BR o namespace confirmado é
  **`com.mitsubishielectric.ada.*`**, não `com.clarion.displayaudio.*` como fontes mais antigas (unidade
  Civic 2016 NA e Ridgeline) indicavam. A Clarion foi comprada pela Mitsubishi em 2015, e a safra 2016
  parece ter sido o ponto de transição; nossa unidade (`1.F187.16`, Apr/2016) já saiu com namespace
  Mitsubishi puro. O **inventário completo** dos 64 pacotes `com.mitsubishielectric.ada.*` observados
  na central está em `docs/fase1-reconhecimento/achados-2026-10-15.md` (seções 5.3-5.5). Destaques
  relevantes para o nosso objetivo:
  - `com.mitsubishielectric.ada.app.dalauncher` — Launcher principal
  - `com.mitsubishielectric.ada.app.dasettings` — Settings (mostra "Sobre o dispositivo" e o toast "passcord")
  - `com.mitsubishielectric.ada.app.appmode` — Gerenciador de modos
  - `com.mitsubishielectric.ada.app.hidkeyboard` — **teclado escondido** (do passcord de serviço)
  - `com.mitsubishielectric.ada.app.developerdiag` — **Developer Diagnostic** (provável habilitador de ADB)
  - `com.mitsubishielectric.ada.app.dealerdiag` / `preshipmentdiag` / `letdiag` — apps de serviço do dealer
  - `com.mitsubishielectric.ada.app.systemupdate` — processo OTA
  - `com.mitsubishielectric.ada.appservice.whitelist` — service da whitelist (seção 4quater)
  - `com.mitsubishielectric.ada.appservice.screenshot` — **serviço nativo de screenshot** (vale ouro para medir X,Y do botão OK sem câmera)
  - `com.mitsubishielectric.ada.appservice.diag` — Diag core
  - Também presente: `com.honda.displayaudio.whitelist` — pacote Honda injetado sobre o firmware Mitsubishi
- **Candidatos ao Aviso de abertura** (seção 3) — pelo inventário real, os mais prováveis são
  `dalauncher`, `dasettings` e `appmode`. Ainda não confirmado qual exatamente; depende de dumpar
  os APKs via ADB e procurar a string do Aviso.
- **Whitelist:** o launcher checa o nome do pacote contra uma lista de apps homologados pela Honda
  (ex.: `com.honda.navigation`). Por isso só renomear um APK para um nome "da lista" funcionou em 2015
  mas falhou no modelo 2016 NA. É o mecanismo central que bloqueia apps de terceiros.
- Ícone **"App Installer"** existe na App List; a Honda diz que é para "apps futuros" (que nunca
  existiram) e desaconselha usar.
- **HondaLink App Launcher** é middleware do lado do celular, não o launcher da central.

### Modos de USB (detalhe arquitetural importante)
A porta USB da central tem dois modos: **host** (padrão — alimenta e lê o iPhone/pendrive = é como
CarPlay funciona) e **device** (central age como periférico de um PC). Trocar para `device` é o que
habilita ADB — mas corta a função CarPlay enquanto estiver nesse modo. Relato de dono: ao alternar
para ADB, a porta USB "ficou sem energia" (consistente com troca de modo). Isso explica por que
mexer com ADB impede uso normal da central no mesmo cabo.

## 3. A tela de "Aviso" — o alvo principal

O que já sabemos:

- É um aviso de segurança/legal mostrado no boot. Some sozinho em ~5–30s (varia por mercado); em várias
  unidades (inclusive a nossa BR) **exige OK para acessar menus/fontes**, inclusive CarPlay.
- **INVESTIGAÇÃO (direção 1) — o lead da "opção no menu dev" esfriou.** Aprofundando: os menus de
  engenharia/diagnóstico dessas unidades **resetam as configurações a cada ciclo de ignição, por
  design** (ex.: dono de Fit 2016 desligou uma trava no menu oculto e o restart desfez; unidade Civic
  de reposição volta à tela de diagnóstico a cada partida; combo de botão limpa só até reiniciar).
  Ninguém da comunidade achou um toggle rotulado de "desligar aviso de abertura" que **persista**.
- **Distinção técnica importante (isto é expertise):** o pessoal confunde DUAS coisas diferentes:
  - **(a) Aviso de abertura** — nosso alvo; disclaimer mostrado uma vez no boot.
  - **(b) Trava "distracted driver" / DD VSS** — bloqueia vídeo/navegação com o carro em movimento.
  Os toggles que a comunidade encontrou nos menus ocultos (e que resetam) são da trava **(b)**. É isso
  que o "vídeo em movimento" do Honda Hack ataca. Para o nosso Aviso **(a)** **não há toggle
  persistente documentado** em nenhum fórum (Civic, CR-V, Pilot, Fit).
- Até o **Honda Hack Pro** falha às vezes nisto: há relato de que o aviso de boot **ainda precisou de
  OK após reiniciar a central**. Ou seja, nem a ferramenta paga remove de forma confiável — ela
  auto-pressiona o OK (e às vezes nem isso).
- Um recall de 2024 menciona **DAY/NIGHT + HOME** para pular o disclaimer *durante aquele procedimento*
  (atalho de serviço, não ajuste permanente).

Conclusão da direção 1: **não existe caminho por "configuração" para remover o Aviso.** A camada de
settings/menu-oculto é não-persistente de propósito, e não há flag de disclaimer de boot que "cole".
Sobram só dois alvos, ambos nível-root e nível-Honda-Hack: **(i)** patchear/re-assinar o app da HMI
que mostra o Aviso (muito invasivo, assinatura é checada, nada documentado para nossa unidade
Mitsubishi), ou **(ii)** script no boot que auto-pressiona o OK — que é exatamente o que o Honda Hack
já faz (de forma incerta). Não há ganho novo em reinventar isso.

## 4. Menus ocultos e acesso (procedimentos documentados pela Honda em TSBs — leitura segura)

Esses são atalhos de serviço que a Honda publica em boletins técnicos (TSBs) para seus próprios
técnicos. Não são exploits — é como um mecânico Honda abre o diagnóstico. Totalmente seguros de
abrir no seu carro parado, só *não mexer* nos ajustes que afetem direção/segurança.

### 4.1 Manual Diag (o principal, 7" — CONFIRMADO para Civic 2016–2017 LX)
Fonte: manual de serviço Honda, replicado no fórum.

1. Dar partida no carro (modo ON, motor rodando ou pelo menos em ON).
2. **Desligar o áudio** pressionando o botão POWER.
3. **Segurar simultaneamente**: `PRESET 1` + `PRESET 6` + knob `VOLUME/POWER`.
   ⚠️ Importante: não pressionar `PRESET 1` e `PRESET 6` *antes* de incluir o knob — tem que ser os
   três juntos.
4. A tela vai para **Manual Diag**.
5. Submenus (um por preset): `1 = System` · `2 = Audio` · `3 = Display` · `4 = Camera`
   · `5 = Connection` · `6 = Vehicle Info`.
6. Sair: girar/pressionar o knob `VOLUME/POWER`, ou desligar o carro.

### 4.1a Self-Diagnosis Mode (EXL BR — CONFIRMADO em `1.F187.16`, 2026-10-15)
A versão EXL brasileira **não tem presets físicos 1-6 nem knob giratório na central** — o combo da
seção 4.1 não serve. Em compensação ela tem o botão físico **DAY/NIGHT** (sol+lua, acima da tela) e
os capacitivos **AUDIO/HOME/+VOL-/MENU/BACK** à esquerda da tela. O combo que funciona é o oficial
do TSB Honda 17-049 (seção 4.3):

1. Carro em **ON**, áudio **off** (botão POWER capacitivo até a tela ficar sem fonte).
2. **Segurar simultaneamente por ~2s:** `DAY/NIGHT` (físico) + `AUDIO` (capacitivo) + `MENU` (capacitivo).
   Técnica: um dedo em cada capacitivo + outra mão no DAY/NIGHT físico. Encostar firme nos capacitivos
   sem deslizar.
3. Abre a tela **Self-Diagnosis Mode** com duas opções:
   - `Self-Diagnosis Mode` — roda teste automático (não usar fora de serviço)
   - `Detail Information & Setting` — é por aqui que a gente navega

Estrutura mapeada do `Detail Information & Setting`:

```
Detail Information & Setting
├─ Monitor Check · Unit Check · Audio Check · Guideline Setup
├─ Functional Setup
│  ├─ Backup Data Clear  ⚠️  Anti-Theft Skip  ⚠️  AMP Repro  ⚠️⚠️  Display Repro  ⚠️⚠️⚠️
│  ├─ Save User's Memory · LaneWatch · Phone Picture
│  └─ Other
│     ├─ Operation Restriction  ← é a trava (b) "DD VSS" (vídeo em movimento), não o Aviso (a)
│     └─ Smartphone Information (ON/OFF do Android Auto e do Car Play — não mexer, derruba CarPlay)
├─ B-CAN · F-CAN                 ← monitor ao vivo dos barramentos (seção 4bis)
├─ Version                        ← inventário completo de pacotes + versões DBOOT/loader/µCom
├─ Vehicle status · GPS Information
```

**Achado importante:** o **Functional Setup do EXL BR não expõe dev mode / ADB** (ao contrário do
que a seção 4.4 reporta para outras unidades Honda). Essa rota está fechada aqui — ver 4.4 abaixo.

Sair: botão `Return` no canto superior direito, até voltar à tela normal.

### 4.2 Combinação alternativa — Civic 2016 Touring (tela 7" "upgraded")
Reportada em fórum, menos confirmada: segurar `AUDIO` + `BRIGHTNESS` + `MENU` por 4s.
Variante vista: `HOME` + `BRIGHTNESS` + `MENU`.

### 4.3 Procedimento oficial Honda (TSB 17-049) para update de software 2016 Civic EX/EX-L/Touring
Para a atualização de software, a Honda documenta: carro em ON → segurar
`DAY/NIGHT` + `AUDIO POWER` + `MENU` → navegar `Detail Information & Setting` → `Unit Check` →
`Center display`. Esse é o caminho oficial — útil para olhar versões sem risco.

### 4.4 Modo desenvolvedor (Android dev options)
Tocar várias vezes (relatos de 7–8 vezes) no número do build dentro das configurações. O caminho
exato muda entre firmware 2016–2017 e 2018+ (olhar a data ao lado de "Kernel Version"). Em CR-V 2016
sem navegação: dev mode via "Functional setup" dentro do Manual Diag.

**Civic 2017 EXL BR (`1.F187.16`) — reality check 2026-10-15:**

- 7 toques no "Número da versão" abrem um toast curto `Please enter a passcord` (sic, com typo —
  é string única, boa para `grep` nos APKs quando a gente tiver pull). Nenhum teclado aparece junto;
  é só o toast, mesmo clicando novamente.
- Sequência XDA 2017 (`Modelo → Kernel → Android → Baseband`, ordem 1-4-2-3) **não funciona** nessa
  safra — só repete o toast. Mesmo sintoma relatado para 2018 Civic Si (XDA / CivicX).
- Rota alternativa "via Functional Setup" (seção 4.4 original) **também não funciona no EXL BR**: o
  Functional Setup só tem Backup Data Clear, Save User's Memory, LaneWatch, Phone Picture, Anti-Theft
  Skip, Other, AMP Repro, Display Repro (ver 4.1a). Dentro de "Other" tem apenas Operation Restriction
  e Smartphone Information. Zero opção explícita de dev mode / ADB.
- **Hipótese nova:** o passcord **não destrava o dev mode do Android** — destrava os apps
  `com.mitsubishielectric.ada.app.{dealerdiag,developerdiag,preshipmentdiag,letdiag}` listados em
  Version (ver seção 2). Pistas: existe pacote dedicado `com.mitsubishielectric.ada.app.hidkeyboard`
  (teclado escondido) só para o fluxo de serviço; os relatos XDA que mencionam "após o passcord,
  segurar MENU para abrir outro menu" descrevem na verdade a entrada no `DeveloperDiag`, não no dev
  mode do Settings do Android.
- **Rotas abertas a avaliar:** descobrir o passcord correto para safra 2016-04; invocar `developerdiag`
  via `am start -n ...` (circular — precisa ADB); explorar `systemupdate` como shell OTA; procurar
  atalho não documentado para habilitar `ScreenshotApService`. Detalhes em
  `docs/fase1-reconhecimento/achados-2026-10-15.md` seção 4.

### 4.5 Reboot do áudio
Segurar `HOME` por ~5s reinicia a central (atalho oficial Honda).

### 4.6 ADB (restrições reais)
- A opção pode vir **acinzentada** em algumas unidades.
- Pareamento ADB em Android 4.2.2 pode exigir aprovação na primeira conexão.
- Trocar para modo device **desliga a função normal do USB** (ver seção 2).
- Especulação da comunidade: ADB sobre rede pode depender das chaves vendor da Honda (a central só
  aceitaria conexão ADB autenticada por certificado não público).

### 4.7 Volatilidade — a razão técnica do "reseta no reboot"
Os toggles do menu de engenharia são **flags de sessão** mantidas em memória do processo da HMI, não
em `/data` ou propriedades persistentes do sistema. Quando o processo reinicia (toda ignição off/on),
os defaults do APK são reaplicados. **Não é bug — é design.** Qualquer solução "clean" de persistência
precisaria mudar o APK que define esses defaults, não só flipar o toggle.

## 4bis. CAN bus — como a central conversa com o resto do carro

Nossa unidade **não é uma ilha**: ela publica/consome mensagens em dois barramentos CAN. Entender isso
é entender a arquitetura elétrica do carro, e é o motivo pelo qual mexer na central tem implicações
além da própria central.

### Topologia (Civic G10)
- **F-CAN** (fast / powertrain): mais rápido, com tráfego de direção, freios, ACC, câmera LKAS, etc.
  Dividido em F-CAN-A e F-CAN-B por um gateway sob o volante *se* o carro tiver câmera LKAS; sem a
  câmera, o F-CAN-B vai direto ao OBD2.
- **B-CAN** (body): mais lento, com portas, instrumentos, HVAC, iluminação, etc. É nele que a central
  mais fala/escuta.
- **Gateway master = cluster de instrumentos** (encaminha entre buses). Seção 41 do manual de serviço
  Honda documenta isso.
- Ambos os buses (F-CAN e B-CAN) chegam fisicamente nos conectores da central.

### Pinouts úteis
- **OBD2** (padrão Honda): pino 6 = CAN High, pino 14 = CAN Low; pino 16 = +12V, pinos 4/5 = GND.
  ⚠️ Pino 13 da Honda carrega VTM-4/imobilizador — **não encostar sonda nesse pino**.
- **Conector A do rádio (24 pinos, variante com amplificador):** B-CAN High = A14, B-CAN Low = A24,
  K-line em A12. Diferenças US/CA vs México nas notas de rodapé. O PDF original está no GitHub do
  projeto `librick/ic1101` (seção 9), mesmo não sendo da nossa unidade exata.

### O que a comunidade já mapeou — e o que FALTA
- **comma.ai / opendbc** (`github.com/commaai/opendbc`): tem DBC do Honda Civic 10ª gen, usada pelo
  **OpenPilot** para direção assistida. Cobre bem **mensagens de ADAS/powertrain**, pouco de
  infotainment/interior.
- Thread **CivicX "decoding the can bus" (94513)** é a referência de RE do interior (HVAC, instrumentos,
  rádio). Posts individuais estão por trás do paywall de bot (tollbit), mas é onde o pessoal publica
  descobertas específicas do G10.
- **Lacuna documental:** não há lista pública de IDs CAN do infotainment do G10 (rádio, status, pop-ups).
  Isso é RE que teria que ser feita por sniffing — mas aí a conclusão é importante: **a tela de Aviso
  é renderizada LOCALMENTE pela HMI, não vem do CAN.** Então mesmo mapeando o CAN inteiro, não há
  "mensagem de aviso" para interceptar. É UI do próprio APK.

### Bitrate
- F-CAN: 500 kbit/s (padrão Honda moderno).
- B-CAN: 125 kbit/s (segundo o projeto da comunidade).

### Para experimentar (futuramente, e sempre em modo leitura)
Hardware básico (US$30–40): adaptador CAN tipo CANable/MCP2515 + software **SavvyCAN** ou **Cabana**
(da comma.ai). Capturar com ignição ON, mexer em um controle de cada vez (abrir porta, ligar farol,
mudar fonte do rádio) e ver quais IDs mudam. **Nunca** transmitir (`TX`) num bus com tráfego vivo —
injetar frames num barramento ativo pode causar falhas de segurança.

## 4ter. APKs do sistema — como obter e analisar

Dumps dos APKs do sistema do Civic 2016/17 **não circulam** na web aberta. Pacotes OTA chegam na
concessionária em pendrives criptografados. O caminho confiável é **extrair da própria unidade via
ADB** (precisa cabo USB A-A + ADB habilitado + modo device no USB).

Após ter os APKs em mãos (`/system/app/` e `/system/priv-app/`), o fluxo de análise é:

1. `apktool d <nome>.apk -o <saida>/` → decode de resources + smali.
2. `grep` recursivo nos XML/strings pelo texto do Aviso ("O motorista é o responsável", "disclaimer").
3. Ler o `AndroidManifest.xml` do APK candidato → mapear activities/receivers.
4. Analisar com `jadx-gui` o fluxo da activity para localizar flag/método/coordenada do botão OK.

**Candidatos prováveis pra o Aviso** (todos sob `com.clarion.displayaudio.*`):
`.extframework` · `.apps.generalsettings` · algum `.launcher`/`.boot` ainda não listado.

**Ferramentas prontas no PC:** `C:\repositorios\honda-civic\tooling\bin\` tem `apktool.jar` (2.11.1) e
`jadx\` (1.5.6). ADB já instalado via winget.

## 4quater. Análise do HondaHack.apk (feita no PC, 2026-10-15) — jackpot

O repositório `root-honda` inclui `packages/HondaHack.apk` (3.7 MB, pacote `cn.autohack.hondahack`).
Mesmo o código Java estando protegido com **Tencent Legu packer** (libs `libshella-*.so` e
`libshellx-*.so`, loader dex `mix.dex`/`mixz.dex`), **as strings de resource NÃO são ofuscadas** e
revelaram a feature e o algoritmo do auto-OK.

### Strings-chave extraídas
```
auto_confirm_agreement_title:    "Automatically click the OK button at startup"
auto_confirm_agreement_summary:  "Avoid clicking the button manually each time you restart..."
auto_confirm_agreement_delay_title: "Delay a few seconds before clicking the button"
auto_confirm_agreement_delay_summary: "Set the delay before clicking the OK button (1~10 seconds)."
```

### Algoritmo inferido (do Manifest + permissões + strings)
1. **`BOOT_COMPLETED` BroadcastReceiver** (`MyBroadcastReceiver`) → ativa quando central liga.
2. **`MyService`** em background → monitora logcat (perm `READ_LOGS` ✅ declarada).
3. Detecta a Activity do Aviso aparecer no topo da UI.
4. Aguarda delay configurado (1-10s).
5. Executa `su -c "input tap <X> <Y>"` com as coordenadas do botão OK (perm `ACCESS_SUPERUSER` ✅).

### Permissões relevantes do manifest
`ACCESS_SUPERUSER` · `READ_LOGS` · `MOUNT_UNMOUNT_FILESYSTEMS` · `SYSTEM_ALERT_WINDOW` ·
`RECEIVE_BOOT_COMPLETED` · `GET_TASKS` · `KILL_BACKGROUND_PROCESSES` · `RESTART_PACKAGES`

### Dica útil tirada do HondaHack
Reboot da central no Civic: **"long press AUDIO 5s → select reboot"** — atalho oficial Honda.

### Outras features do HondaHack (contexto, não todas interessam ao nosso projeto)
`auto_start_app` (auto-abre app no boot) · `fix_driving_video` (bypass parking brake) ·
`fix_sdcard` (write em USB) · `install_to_system` (APK como system app) ·
`enable_sdcard_fast_mount` · navigator settings.

### Mecanismo de whitelist (do `root-honda/install.sh`)
A central tem `/data/data/whitelist-1.0.xml` listando pacotes autorizados com hash de assinatura.
Instalar APK terceiro = (a) extrair signature do APK com `GetAndroidSig.jar`, (b) adicionar
`<application><property><package>` + `<keyStore>` ao XML, (c) copiar como system, (d) `pm install`.
Precisa root pra escrever no whitelist.

**Atualização 2026-10-15 — análise estática do `install_mitsubishi.sh` do HondaHack**
(detalhes em `docs/fase4-analise-estatica/hondahack-mitsubishi.md`):

- Caminho exato na central Mitsubishi: `/data/data/whitelist-1.0.xml` (confirmado).
- Permissões: `0666`, dono `system:system`.
- Schema do `<application>` para injetar inclui `<property>`, `<keyStoreLists>` com `<keyStore>` por
  assinatura, e `<controlData>` com `withAudio`, `audioStreamType`, `regulation`, `revert`.
- **O HondaHack instala como user app** (`pm install -r`), **não** copia para `/system/app/`. Isso é
  importante — nosso APK auto-OK pode seguir o mesmo caminho (menos invasivo, reversível) desde que
  a signature entre na whitelist. Investigar em runtime quando ADB subir.
- Diff com Clarion: Clarion usa `/data/system/whitelist.xml` (sem versão) e já tem `cn.autohack.hondahack`
  pré-aprovado. Mitsubishi precisa adicionar na hora.

### Base do root (fluxo do `root-honda/root.sh`)
1. Push `dirtycow` (binário ARMv7) via ADB para `/data/local/tmp/dcow`.
2. `dcow` substitui `/system/bin/run-as` por um `run-as` modificado (CVE-2016-5195).
3. Push de `nefarious.sh` + `su` + `SuperSU-v2.78.apk` para `/data/local/tmp/rootme/`.
4. Executa `nefarious.sh` com `run-as` pivotando pra root.
5. `nefarious.sh` monta `/system` RW, copia `su` para `/system/xbin/` (SUID 6777), copia SuperSU.apk.

**Takeaway crítico:** **temos tudo que precisamos pra escrever nosso auto-OK sem decifrar o código
ofuscado do HondaHack.** O algoritmo está claro, as permissões necessárias estão identificadas, o
caminho de root está documentado. Faltam só:
(a) coordenada X,Y do botão OK na tela (do APK da HMI, extração depois do ADB), e
(b) nome da Activity do Aviso (do APK da HMI, mesma extração).

## 5. Ferramentas instaladas no PC (`C:\repositorios\honda-civic\tooling\`)

```
tooling\
├── bin\
│   ├── apktool.jar      (2.11.1 — descompilação de APK)
│   ├── apktool.bat      (wrapper Windows)
│   └── jadx\            (1.5.6 — jadx CLI e jadx-gui)
├── references\
│   ├── root-honda\      (ferramenta de root pro Civic 2017; inclui HondaHack.apk)
│   ├── 2016PilotOneClick\ (projeto base, dirtyCOW + whitelist bypass)
│   └── ic1101\          (RE do librick, SoC Tegra 3, boot/recovery images, datasheets)
├── apks-dumped\         (vazio; destino do pull do /system/app via ADB)
├── apks-decoded\
│   └── HondaHack\       (HondaHack descompilado com apktool)
└── our-apk\             (projeto do nosso APK auto-OK, a construir)
```

Além disso o PC tem: Java 17 ✅ · Python 3.13 ✅ · Git 2.55 ✅ · ADB 1.0.41 ✅ · 7-Zip ✅ · tar ✅.

## 5. Acesso de escrita (root) — entendimento conceitual

Para persistir qualquer mudança no sistema (incluindo fazer uma config do Aviso "colar"), precisa
ganhar privilégios de escrita no sistema de arquivos — o que em Android se chama *root*. Entender
POR QUE é difícil é mais útil do que a receita (que fica nas fontes da seção 9).

### Por que a central resiste a mudanças persistentes
- `/system` é montado read-only no boot. É aí que vivem os APKs do launcher e configurações default
  da HMI (inclusive, provavelmente, a flag que ativa o Aviso).
- Mesmo tendo ADB habilitado, por padrão **ADB não é root** — você entra como usuário sem permissão
  pra remontar `/system` ou substituir APKs.
- Para elevar permissões, precisaria de uma falha de kernel. O Android 4.2.2 nessa central roda em
  kernel pré-2016 — vulnerável à família de bugs do tipo **CVE-2016-5195 (dirtyCOW)**, que foi o
  caminho usado pelos projetos do Pilot e por derivados Civic (ferramentas como o Honda Hack
  empacotam isso num processo "clica-clica"). O patch do kernel que fecha isso nunca chegou nessa
  unidade — ela é um sistema congelado em 2012/2013.

### O que mudar persistentemente envolveria, conceitualmente
1. Entrar na central com shell de usuário.
2. Elevar para root via exploit de kernel.
3. Remontar `/system` como gravável.
4. Modificar o APK alvo (patch de smali ou de resource) — e **re-assinar**, porque mesmo rooteado o
   Android checa a assinatura em instalação. APKs de sistema podem ser substituídos pelo arquivo em
   `/system/app` sem reinstalar, mas quebrar a signatura compartilhada pode quebrar comunicação com
   outros serviços que compartilham `android:sharedUserId`.
5. Reiniciar e torcer.

### Por que a comunidade basicamente desistiu dessa rota pra remover o Aviso
Mesmo com root (do Honda Hack ou manual), **ninguém publicou qual APK/flag controla o Aviso**. É RE
original. E o Honda Hack, com root já funcionando, não removeu — apenas **auto-pressiona o OK**. Isso
sugere fortemente que a comunidade tentou achar e desistiu, optando pelo workaround mais barato.

### Riscos arquiteturais (importantes de saber)
- **A central tem acesso ao CAN bus do carro.** Isso não é teoria: ela precisa falar com o veículo
  pra mostrar status, câmera de ré, climatização. Software comprometido na central potencialmente
  alcança outros sistemas. Isso eleva o peso de "não quebrar nada".
- **A tela da central é a tela da câmera de ré.** Brick = sem ré.
- **Updates de concessionária reinstalam `/system` e desfazem mods** (e podem retornar o Aviso).

## 6. Riscos (reais e recorrentes)

- **Brick / reboot-loop / tela preta** são relatados com frequência nesse processo (há threads inteiras
  de "head unit possibly bricked").
- A **câmera de ré usa a mesma tela** — central morta = sem câmera de ré.
- **Atualização da concessionária reverte** mods (e pode retrazer o aviso).
- Antivírus acusa as ferramentas de root (esperado, mas exige cuidado com a procedência dos arquivos).
- Pode afetar garantia (no nosso caso, garantia Honda BR de 3 anos já expirou ~2020).

## 7. Perguntas em aberto / roadmap de pesquisa

Atualizado em 2026-10-15 após sessão de reconhecimento no carro.

1. ✅ **Resolvida** — Pacotes da unidade Mitsubishi do Civic BR: são **`com.mitsubishielectric.ada.*`**
   (64 pacotes mapeados). Lista completa em `docs/fase1-reconhecimento/achados-2026-10-15.md`.
2. **Qual activity do `dalauncher`/`dasettings`/`appmode` renderiza o Aviso?** Só respondemos depois
   de pullar os APKs via ADB e procurar a string. Candidatos reduzidos aos 3 pacotes acima.
3. **Qual é o passcord do serviço na safra `1.F187.16`?** Não chutar. Procurar em fóruns BR/XDA
   específicos dessa safra, ou extrair do APK `com.mitsubishielectric.ada.app.dasettings` quando
   tivermos pull. **Prioridade alta — destrava `DeveloperDiag` que provavelmente destrava ADB.**
4. ✅ **Resolvida** — Part number + build da nossa unidade: `MY16ADA` + `1.F187.16` + DBOOT
   `1.10_20160407183722`.
5. **Fórum BR** (civicx.club "Honda Hack para Civic 2017"): alguém já achou o passcord ou outra
   rota de dev mode na safra BR? Buscar.
6. **O `ScreenshotApService 1.0` que vimos existir pode ser disparado por atalho?** Em caso positivo,
   dispensa a câmera na hora de medir X,Y do botão OK — valor alto.
7. **Caminho de persistência pós-root:** se rooteado, dá pra (a) tornar a config persistente,
   (b) script no boot que reaplica, ou (c) patch no app/HMI que reativa o aviso? Qual é menos
   arriscado?
8. **A whitelist Honda (`com.honda.displayaudio.whitelist`) vive junto da Mitsubishi
   (`com.mitsubishielectric.ada.appservice.whitelist`)** — qual tem prioridade? Pode haver ponto
   de alavanca na Honda, não na Mitsubishi.

## 8. Veredito atual (honesto)

Depois de esgotar a direção 1 (settings/menu): **não há caminho limpo para remover o Aviso.** A camada
de configuração reseta por design e não existe flag persistente de disclaimer de boot. Os únicos alvos
restantes (patch da HMI re-assinada; ou script de boot que auto-pressiona o OK) são nível-root,
nível-Honda-Hack, sem nada documentado para a unidade Mitsubishi, por um ganho de **um toque** — e com
risco de brick (a mesma tela é a câmera de ré).

Conclusão prática: as opções reais continuam sendo **(a) conviver com o toque único** (recomendado) ou
**(b) o auto-OK do Honda Hack** (incerto, arriscado, e que o dono já descartou). A engenharia reversa
confirmou *por que* não há mágica aqui — isso é a expertise que ganhamos. Vale seguir só se for pelo
aprendizado, não pelo resultado.

## 9. Fontes

- XDA — central Android do Civic 2016 (NA): https://xdaforums.com/t/2016-honda-civic-android-based-headunit-north-american-version.3416177/
- CivicX — "is there a guide for how to hack the headunit": https://www.civicx.com/forum/threads/is-there-a-guide-for-how-to-hack-the-headunit.5827/
- Hondata — instalar Hondata Mobile (root 10ª gen): https://hondata.mobi/forum/viewtopic.php?p=100674
- CR-V Owners — "can I get rid of the NOTICE...": https://www.crvownersclub.com/threads/can-i-get-rid-of-the-notice-that-comes-up-on-the-display-every-time-i-start-the-car.170937/
- Ridgeline — erro `com.clarion.displayaudio.extframework`: https://www.ridgelineownersclub.com/threads/unfortunately-com-clarion-displayaudio-extframework-has-stopped.234562/
- RE da unidade 2021 (NÃO é a nossa) — librick/ic1101: https://github.com/librick/ic1101 · artigos: https://juniperspring.org/posts/honda-reverse-engineering/
- Gitee `root-honda` (ferramenta não verificada): https://gitee.com/ylcplus/root-honda
- Honda/NVIDIA (unidade europeia Tegra, contexto): https://www.droid-life.com/2014/10/02/nvidia-and-honda-debut-tegra-powered-android-infotainment-system/

### Fontes adicionadas na sessão de 2026-10-15

- Pastebin — `pm list packages` de outro Honda Civic (fonte principal dos nomes `com.mitsubishielectric.ada.*`): https://pastebin.com/B9Edr2fv
- XDA — "How to enter developer mode on 2017 Honda Civic" (sequência 1-4-2-3 após o passcord): https://xdaforums.com/t/guide-how-to-enter-developer-mode-on-2017-honda-civic-and-now-root-install-apps.3621582/
- CivicX — "In case anyone is wondering passcord for 2018 models" (confirma que o passcord muda por safra): https://www.civicx.com/forum/threads/in-case-anyone-is-wondering-passcord-for-2018-models-developer-mode.26840/
- CivicX — "2017 Lx Secret Menu" (combo PRESET 1+6+VOL para LX): https://www.civicx.com/forum/threads/2017-lx-secret-menu.39126/
- civinfo — "Diagnostic or hidden menu Honda CRV EX 2016" (combo POWER + MENU + BRIGHTNESS para 7"): https://www.civinfo.com/threads/diagnostic-or-hidden-menu-honda-crv-ex-2016.290529/
- Relato interno da Fase 1 (unidade real `1.F187.16` EXL BR): `docs/fase1-reconhecimento/achados-2026-10-15.md`
