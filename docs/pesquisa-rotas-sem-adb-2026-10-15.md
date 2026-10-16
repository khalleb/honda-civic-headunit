# Varredura — rotas de deploy do nosso APK sem ADB

Documento operacional da sessão 2026-10-15 (Windows PC). O passcord via Settings foi descartado em sessão anterior (ver `fase3-adb/passcord-pesquisa.md`). Este documento é o resultado de uma varredura ampla em fóruns, GitHub, HN e write-ups técnicos para encontrar **rotas alternativas que não dependam de ADB** para colocar o `our-apk/AutoOk.apk` no `/system/app/` da central `1.F187.16` BR.

Nove buscas extensas foram feitas; o compilado abaixo lista cada rota, custo, risco, e o experimento zero-risco que decide se vale descer para o carro.

## 1. Resumo em uma linha

> A rota mais nova e promissora é **EvilValet** (divulgada em jun/2026): assinar um `update.zip` com a `testkey` pública do AOSP e deixar o recovery da própria central instalar. Confirmada em Civic 2021; precisa validar na nossa safra 1.F187.16 BR com um experimento zero-risco antes de descer para o carro.

## 2. Problema é conhecido globalmente — e tem só uma solução comercial

A tela "Aviso" é relatada em mercados US, EU, LATAM com nomes diferentes ("driver responsibility warning", "safe-driving notice", "startup OK"). A Honda **nunca liberou switch de UI para desligar** — tratado como responsabilidade legal.

Comportamento regional:

- **US**: fade out automático em 5-10 s.
- **EU/BR**: fica fixo até o toque no OK.

Única solução comercial confirmada: **Honda Hack** (`cn.autohack.hondahack`), tier Pro US$25. Tem feature `auto_confirm_agreement` exatamente para isso. Projeto do dono exclui essa opção.

Nenhum fork open-source do HondaHack com auto-OK foi encontrado — repos existentes (`librick/ic1101`, `codeage/root-honda`, `jersacct/2016PilotOneClick`) cobrem rooting, não a feature auto-OK propriamente. Nosso `our-apk/` já é essa reimplementação.

## 3. Rotas identificadas — tabela de triagem

| # | Rota | Precisa ADB? | Confirmação pública | Risco físico | Viabilidade 1.F187.16 BR |
|---|---|---|---|---|---|
| A | Passcord 1-4-2-3 via Settings | — | Sim (até 2017) | Nenhum | ❌ Encerrado (fase 3) |
| B | EvilValet / `testkey` AOSP via update.zip USB | **Não** | Sim (jun/2026, 2021 Civic) | Baixo (controlado) | ⚠️ A validar com experimento |
| C | OTA pública Honda com dump do `/system/app` | Não | Nenhuma pública BR | Nenhum | ❌ Zero evidência de dump BR |
| D | Combo físico de botões para `DeveloperDiag` | Não | Nenhuma | Nenhum | ⚠️ Discovery nossa |
| E | Browser nativo + payload (@codeage style) | Não | Sim (pago) | Médio | ❌ Payload é privado |
| F | KingoRoot via USB | **Sim** (ADB primeiro) | Parcial (2018 Si) | Médio | ❌ Depende de A |
| G | Dealer Firmware Downloader (TSB + VIN) | Não | Oficial | Nenhum | ⚠️ Precisa concessionária |
| H | Honda Hack Cracker (pirataria) | — | Sim | — | ❌ Fora do escopo ético |

As rotas abaixo são detalhadas por utilidade pra nossa safra.

## 4. Rota B — EvilValet (prioritária, nova, pode destravar tudo)

### 4.1 O que é

Publicada em 14 de junho de 2026 por **E. McDonald** (`juniperspring.org`). Em dois achados centrais:

1. A central Honda **mantém o certificado público AOSP `testkey.x509.pem`** em `res/keys` da partição recovery.
2. A rotina `verify_file` do recovery é **essencialmente idêntica à do AOSP stock** — apesar da customização Mitsubishi, o `signapk.jar -w` para OTA zips passa pela verificação.

**Consequência:** qualquer pessoa pode construir um `update.zip` com o payload que quiser, assinar com a `testkey.pk8` + `testkey.x509.pem` disponíveis publicamente no AOSP, colocar num pendrive FAT32, plugar na porta USB frontal da central (energizada), e o recovery aceita e aplica.

Isso é **substituto completo da rota ADB**: não precisa de dev mode, de passcord, de cabo USB-A/A, de dirtyCOW. Só pendrive + update.zip assinado.

### 4.2 Status de confirmação

- Confirmado em **Civic 2021** (safra US) pelo autor.
- Um comentário em HN relata que uma OTA oficial EU, inspecionada por hex-dump, tem a mesma signature do test key — reforço indireto de que o problema é sistêmico Mitsubishi, não só do 2021.
- **Não confirmado em 1.F187.16 BR** — o nosso trabalho é validar.

### 4.3 Experimento zero-risco (recomendado antes de descer pro carro)

Montar o `update.zip` em laboratório e simular a verificação de assinatura **sem plugar na central**:

1. Baixar `testkey.pk8` e `testkey.x509.pem` de `aosp-mirror/platform_build/target/product/security/`.
2. Construir um `update.zip` mínimo com: `META-INF/com/google/android/update-binary` (dummy script) + nosso `AutoOk.apk` em `/system/app/AutoOk.apk`.
3. Rodar `java -jar signapk.jar -w testkey.x509.pem testkey.pk8 unsigned.zip signed.zip`.
4. Comparar o header de `signed.zip` com headers de OTA Honda **reais** (de fóruns públicos — tem OTA EU 1.F197.00 descrito em civicx.com).
5. Se os campos de magic/version/signature algorithm batem, a chance de o recovery aceitar é alta.

**Custo:** 1-2 h no PC, zero toque na central.

### 4.4 Teste no carro (depois do experimento zero-risco)

**Correção importante (2026-10-15 noite):** a redação anterior desta seção dizia "observar prompt sem instalar". Isso **estava errado** — foi extrapolação do fluxo do app `SystemUpdate`, que o nosso pacote evita de propósito (usa `NEW_DA_VERSION="IC1101"`, sem prefixo `1.F1`). Fluxo real do `daupdater` segundo `tooling/references/ic1101/docs/updates.md`:

- `daupdater` roda silenciosamente a cada boot — não existe UI de confirmação.
- Pendrive FAT32 MSDOS (com tabela de partição; superfloppy sem tabela não funciona).
- Pendrive precisa ter `SwUpdate2.txt` na raiz **e** `<cur_rom>/SwUpdate.mdt`, onde `<cur_rom>` é o valor exato de `custom_rom.type` em `/system/vendor/build.prop` do HU. Como esse valor não é conhecido para `1.F187.16` BR, o build atual (`tooling/ota-build/output/20261015T234310Z/`) cobre cinco: `1110`, `1115`, `1118`, `1120`, `2250`. `daupdater` ignora silenciosamente as pastas que não batem.
- Processo: plugar pendrive na porta USB-A frontal (não a do console central), reboot forçado (power/volume), aguardar `daupdater` detectar/estagar/reiniciar para recovery, recovery aplicar, updater-script fazer `set_progress(1.000000)` + sleep 30s, **retirar o pendrive durante esses 30s** (ver seção `Appendix: Boot loops with a valid update` do updates.md para detalhes).

**Isso significa que não existe "testar sem aplicar".** Qualquer passagem do pendrive na central com `daupdater` ativo é uma tentativa real de aplicação. Risco de brick é aceito por decisão (sem ré, troca R$ 1-2k).

**Mitigações no pacote reconstruído:**
- Sem `assert(ro.product.device == "vcm30t30" || ...)` no updater-script, para evitar recovery loop permanente em safras BR que possam ter sufixo (`vcm30t30br`?). Perda de proteção é irrelevante — pendrive só vai nessa central.
- 5 rom types em paralelo cobrem a maior incerteza.
- `release-keys` nas tags do `build.prop` embarcado (exigência do recovery, cf. recovery checklist).

### 4.5 Risco

- Zero se abortar no prompt (sem instalar).
- Médio-alto se instalar sem backup: a central pode entrar em recovery loop; proxima-sessao.md seção 8.1 já cita isso.
- O `ota-builder` do `librick/ic1101` já suporta esse workflow — vale ler quando entrarmos na próxima sessão Linux.

### 4.6 Dependência

- Nenhuma — pode começar hoje.

## 5. Rota C — OTA pública Honda (dump `/system/app` sem ADB)

### 5.1 Realidade

- `usb.honda.com` **exige VIN + data file gerado pela central** antes de permitir download.
- Para a safra brasileira `1.F187` não há evidência de OTA publicada em canal independente.
- Nenhum dump do `/system/app` dessa safra encontrado em MediaFire, GitHub, archives, nem fóruns BR.

Pacotes US de safras próximas foram publicados por donos em civicx.com (ex.: `1.F196.39` para 2017 sedan, `1.F197.00` para 2016 hatchback 5p). Esses pacotes vêm como ZIP com `SwUpdate.mdt` dentro de `1110/` (~470 MB). Reportagens de dumping dizem que o arquivo tem jeito de "Windows CE / mix" segundo hex-dump — ou seja, não é um `.img` AOSP padrão.

### 5.2 O que isso resolveria se achar

Com um ZIP de uma safra qualquer da nossa família (`com.mitsubishielectric.ada.*`), dá para desempacotar, extrair os APKs, achar o Activity do Aviso e as coordenadas do OK — exatamente o que falta para preencher as 3 constantes do `our-apk/AutoOkConfig.java`.

### 5.3 Caminhos ainda abertos

1. **Pedir a um proprietário US de 2016 Civic EX-T** (safra `1.F187.14` relatada em civicx.com post 1-6) para compartilhar o pacote OTA. Risco: comunidade pode ser rígida sobre compartilhamento.
2. **Concessionária Honda Brasil** com VIN — pode gerar um ZIP para flasheamento. Requer visita, requer que haja TSB aberto para essa safra. Baixa probabilidade mas vale pedido formal.
3. **Buscar `honda_installer.apk` versão > 2.1** no GitHub (atual é 2018). Nenhuma versão nova encontrada; `@codeage` provavelmente parou — última release pública mencionada é mar/2021.

### 5.4 Veredicto

Rota não encerrada, mas sem avanço imediato possível daqui. Fica como fallback se a rota B falhar.

## 6. Rota D — Combo físico escondido para `DeveloperDiag`

### 6.1 Hipótese

A sessão 2 mapeou que o pacote `com.mitsubishielectric.ada.app.developerdiag` **está instalado**. Se existir um combo físico (long-press, sequência de PRESET + VOL etc.) que invoque essa Activity direto, a gente pula o passcord inteiro.

Combos já conhecidos (do KB):
- `DAY/NIGHT + AUDIO + MENU` por 2s com áudio off → menu de serviço Mitsubishi.
- `AUDIO` por 5s → reboot.

Combos documentados como seguros pela comunidade mas **NÃO testados** na sessão 2:
- `HOME` por 5s.
- `AUDIO + HOME` por 5s.
- `AUDIO + BACK` por 5s.
- `AUDIO + MENU + BACK` por 5s (3 capacitivos simultâneos).

### 6.2 Expectativa

Baixa chance de dar certo. Combos físicos para menus escondidos geralmente foram abertos em safras pré-patch e **removidos nas versões BR**, que são mais travadas. Mas o custo é zero (ninguém testou ainda) e um achado desses destrava tudo.

### 6.3 Veredicto

Rota 2ª prioridade — já estava planejada em `proxima-sessao.md` seção 5.3, continua válida.

## 7. Rota E — Browser nativo + payload custom

### 7.1 O que o `@codeage` faz

- Usuário entra no site da `@codeage` **pelo browser nativo da central** (Android 4.2.2 Browser-55 ancestral do Chrome 18).
- Site entrega um payload binário (`.so` nativo + script); o Browser carrega + executa pelo mecanismo pago (US$25).
- Payload faz tudo: enable dev options, write em `/system`, install `honda_installer.apk`.

### 7.2 Por que a gente não consegue replicar

- O payload é privado — nunca foi liberado em código.
- Precisamos encontrar o CVE que o Browser 4.2.2-55 usa para escapar da sandbox e virar root. Candidatos públicos:
  - **CVE-2016-2060** — libQSEEComAPI (não aplicável, só Qualcomm).
  - **CVE-2016-5195 (dirtyCOW)** — kernel 3.1.10 é vulnerável, mas precisa de shell local primeiro.
  - **CVE-2013-2094 (perf_event_open)** — kernel 3.1.10 é vulnerável, LPE confirmado, usável de dentro do browser via JS → native via WebGL? Pouco documentado.
  - **CVE-2015-1805 (iovyroot)** — kernel 3.1.10 é vulnerável, usado em outros root-tools.

Qualquer um desses, uma vez com shell local, pode escrever em `/system`. Mas **chamar o CVE de dentro do Browser** sem code injection prévio exige RCE no Browser primeiro — e CVEs públicos de RCE para WebView 4.2.2 são caros.

### 7.3 Veredicto

Rota técnica, mas distante do estado atual do projeto. Fica catalogada para fase 6+ se as outras rotas falharem.

## 8. Rota G — Dealer Firmware Downloader

### 8.1 Como funciona

- Técnico com acesso dealer → `techinfo.honda.com` → informa VIN + TSB.
- Site gera um ZIP específico para aquele VIN + aquele TSB.
- Técnico pluga em pendrive e aplica.

### 8.2 Útil para nós

Não para instalar o nosso APK, **mas pode render o dump do `/system/app`** se o técnico aceitar entregar o ZIP (ou se ele deixar o pendrive na mesa por 5 min).

Em civicx.com relatos de donos conseguindo:
- Comprar o pendrive-TSB oficial (SB 18-001, ~$30 nos US).
- Dealer rodando grátis em cortesia.

No Brasil é mais fechado — concessionárias Honda BR não liberam o pendrive, e a ferramenta de dealer é controlada pela Honda Brasil Automóveis (não é a mesma do dealer US).

### 8.3 Veredicto

Baixa probabilidade de dar certo no BR, mas vale um telefonema para concessionária consultando TSB para "safra 1.F187.16". Zero custo.

## 9. Plano consolidado — ordem recomendada

### 9.1 Para fazer **agora**, no PC Windows ou Linux (zero toque no carro)

1. ⏳ **Experimento Rota B zero-risco** — construir `update.zip` com testkey AOSP e nosso `AutoOk.apk`. Precisa Linux ou WSL (signapk.jar não roda em Windows nativo bem). Custo: 2 h. Resultado: um arquivo `.zip` que **se o recovery da central aceitar, resolve o projeto todo**. Nenhum risco físico.
2. ⏳ **Ler `ic1101/docs/rooting.md` localmente** (clonado pelo `setup.sh` em `tooling/references/ic1101/docs/rooting.md`). Pode conter método alternativo à dirtyCOW que ainda não documentamos.
3. ⏳ **Mapear precisamente o layout do `signed.zip`** — comparar com um pacote OTA real da família (civicx tem posts com file-listing de 1.F197.00). Confirmar paths e script format.
4. ⏳ **Procurar na comunidade BR** — Olx, grupos Honda Civic BR no Facebook, forums.autoentusiastas, HondaForum.com.br — alguém que fez root em MY16/17ADA BR. Baixa chance mas sem custo.

### 9.2 Para fazer na **próxima ida ao carro**

1. ✅ Testar combos físicos da Rota D (seção 6) — 5 combos distintos, 10 min total. Já estava planejado.
2. ⏳ Se o experimento 9.1.1 completou com `signed.zip` válido: **plugar o pendrive e observar o prompt** (sem instalar).

### 9.3 Para fase 6 (se tudo acima falhar)

1. Estudo profundo das CVE candidatas em kernel 3.1.10.
2. Reverter o payload do `@codeage` por análise de tráfego HTTP (ele é HTTP, não HTTPS — ver `honda-installer.md` seção 10) — captura MITM num ponto Wi-Fi local.
3. Contactar E. McDonald (autor do EvilValet) via GitHub com dado da nossa safra — pode haver interesse acadêmico em expandir a lista "Known Versions".

## 10. Fontes consultadas (varredura)

Prioritárias:
- [juniperspring.org — Honda Civics and the Evil Valet](https://juniperspring.org/posts/honda-evil-valet/)
- [juniperspring.org — Honda Civic Reverse Engineering](https://juniperspring.org/posts/honda-reverse-engineering/)
- [GitHub — librick/ic1101](https://github.com/librick/ic1101)
- [GitHub — librick/ic1101/ota-builder](https://github.com/librick/ic1101/tree/main/ota-builder)
- [GitHub — librick/ic1101/docs/rooting.md](https://github.com/librick/ic1101/blob/main/docs/rooting.md)
- [GitHub — codeage/root-honda](https://github.com/codeage/root-honda)
- [GitHub — jersacct/2016PilotOneClick](https://github.com/jersacct/2016PilotOneClick)
- [GitHub — aosp-mirror/platform_build (testkey)](https://github.com/aosp-mirror/platform_build/tree/master/target/product/security)
- [Hacker News — Show HN Infotainment RE](https://news.ycombinator.com/item?id=36052753)
- [Hacker News — EvilValet discussion](https://news.ycombinator.com/item?id=48523080)

Secundárias (fóruns e write-ups):
- [Hackaday — Honda Civics And Installing Software With Android Test Keys](https://hackaday.com/2026/06/16/honda-civics-and-installing-software-with-android-test-keys/)
- [Hackaday — Honda Headunit Reverse Engineering](https://hackaday.com/2023/06/27/honda-headunit-reverse-engineering-and-the-dismal-state-of-infotainment-systems/)
- [Tom's Hardware — 2021 Civic jailbreak via USB](https://www.tomshardware.com/tech-industry/cyber-security/2021-honda-civic-infotainment-system-can-be-jailbroken-via-usb-flaw-uses-public-android-test-keys-to-install-unauthorized-apps-enables-for-evilvalet-attacks)
- [GIGAZINE — EvilValet detail (EN)](https://gigazine.net/gsc_news/en/20260617-honda-civic-evil-valet)
- [CivicX — Turn off annoying "OK" on startup](https://www.civicx.com/forum/threads/turn-off-annoying-%E2%80%9Cok%E2%80%9D-on-startup.84663/)
- [CivicX — How to deactivate annoying warning advice](https://www.civicx.com/forum/threads/how-to-deactivate-annoying-warning-advice-at-every-start-of-head-unit.42810/)
- [CivicX — Remove Warning / Notice Banner](https://www.civicx.com/forum/threads/remove-warning-notice-banner.1878/)
- [CivicX — Warning screen when starting car up](https://www.civicx.com/forum/threads/warning-screen-when-starting-car-up-drivers-responsible.2367/)
- [CivicX — DO NOT change locale if haven't disabled warning](https://www.civicx.com/forum/threads/do-not-change-the-locale-if-you-havent-have-the-start-up-notice-disabled.56205/)
- [CivicX — Infotainment screen warning](https://www.civicx.com/forum/threads/infotainment-screen-warning.20719/)
- [CivicX — Honda Head Unit Hack Without A Laptop](https://www.civicx.com/forum/threads/honda-head-unit-hack-without-a-laptop.23336/)
- [CivicX — The head unit was rooted](https://www.civicx.com/forum/threads/the-head-unit-was-rooted-and-app-installation-is-possible-now.12711/)
- [CivicX — How to Establish an ADB Connection (US Models)](https://www.civicx.com/forum/threads/how-to-establish-an-adb-connection-us-models.12479/)
- [CivicX — Firmware for Head unit](https://www.civicx.com/forum/threads/firmware-for-head-unit.67989/)
- [CivicX — Install American firmware on European head unit](https://www.civicx.com/forum/threads/install-american-firmware-on-european-head-unit.78015/)
- [CivicX — Civic 2016 EX/EX-T/Touring Firmware Upgrade Guide](https://www.civicx.com/forum/threads/civic-2016-ex-ex-t-and-touring-firmware-upgrade-guide.65967/)
- [Civinfo — Disabling the driver responsibility warning](https://www.civinfo.com/threads/disabling-the-driver-responsibility-warning.418726/)
- [XDA — How to enter developer mode on 2017 Honda Civic](https://xdaforums.com/t/guide-how-to-enter-developer-mode-on-2017-honda-civic-and-now-root-install-apps.3621582/)
- [XDA — Honda Connect Android System](https://xdaforums.com/t/honda-connect-android-system.3179549/)
- [XDA — 2018 Honda Civic HU root](https://xdaforums.com/t/2018-honda-civic-hu-root.3776900/)
- [Softstribe — How to enter developer mode in Honda Civic 2017](https://softstribe.com/android/how-to-enter-developer-mode-in-honda-civic-2017/)
- [Hive13 — Honda Navigation Hacking (older)](https://wiki.hive13.org/view/Honda_Navigation_Hacking)
- [X — Jeff Garzik on Insure Honda headunits (EvilValet)](https://x.com/jgarzik/status/2066055486395281513)

Oficiais Honda (contexto):
- [usb.honda.com — OTA USB portal](https://usb.honda.com/)
- [techinfo.honda.com — System Updates](https://techinfo.honda.com/rjanisis/pubs/om/ah/at202222iom/enu/details/131229047-293358.html)

Repos secundários (não serviram diretamente mas úteis):
- [GitHub — bouletmarc/HondaReflashTool](https://github.com/bouletmarc/HondaReflashTool)
- [GitHub — jpancotti/rwd-xray](https://github.com/jpancotti/rwd-xray)
- [GitHub — csouers/hondasnet](https://github.com/csouers/hondasnet)
- [GitHub — hondabase/files-archive](https://github.com/hondabase/files-archive)
- [GitHub — hondabase/manuals-archive](https://github.com/hondabase/manuals-archive)
- [GitHub — tipaktapak/HFP_Updates](https://github.com/tipaktapak/HFP_Updates)

## 11. Impacto no plano de fases do KB

A rota B muda o roteiro: **se funcionar**, a Fase 3 (ADB) deixa de ser pré-requisito da Fase 6 (root/deploy). Novo roteiro possível:

- Fase 0 ✅
- Fase 1 ✅
- Fase 2 (comprar cabo) → **adiada** até rota B falhar
- Fase 3 (ADB) → **substituída pela rota B** até prova em contrário
- Fase 4 (análise APKs) → ainda precisa do `/system/app` dump, mas **pode vir de dentro do próprio recovery** via script `update-binary` que lista e copia APKs para pendrive **antes** de instalar o auto-OK — reconhecimento + deploy no mesmo update.zip.
- Fase 5 ✅
- Fase 6 (root dirtyCOW) → **só necessária se EvilValet falhar**
- Fase 7 → inalterada

Esse replano é bastante positivo. Vale discutir com o dono antes de implementar.
