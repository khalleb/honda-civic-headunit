<div align="center">

<img src="docs/images/logo.svg" alt="Honda Civic G10 Skip Disclaimer" width="180"/>

# Honda Civic G10 — Skip Disclaimer

**Elimine automaticamente a tela de "Aviso" que aparece sempre que você liga seu Honda Civic**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-conclu%C3%ADdo-brightgreen)](docs/fase10-deploy-2026-10-29/README.md)
[![Platform](https://img.shields.io/badge/platform-Android_4.2.2_%7C_Tegra_3-blue)]()
[![Safra](https://img.shields.io/badge/safra_testada-1.F187.16_BR-orange)]()
[![Fase 10](https://img.shields.io/badge/Fase_10-aviso_removido_2026--10--29-success)](docs/fase10-deploy-2026-10-29/README.md)
[![AutoOk](https://img.shields.io/badge/AutoOk-v0.5.4_safety_net-informational)]()
[![CI](https://github.com/khalleb/honda-civic-headunit/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/khalleb/honda-civic-headunit/actions/workflows/ci.yml)

🇧🇷 **Português** · [🇺🇸 English](README.en.md)

</div>

---

## 🎬 Antes e depois

<div align="center">

<img src="docs/images/antes-depois.gif" alt="Antes: aviso aparece. Depois: aviso nao aparece mais" width="640"/>

**Toda vez que você liga o carro, a central mostrava o Aviso.** Antes era clicar manualmente. Hoje **o aviso nem aparece mais** — o fluxo pula direto para o launcher (Fase 10, 29/10/2026).

</div>

---

## 🎯 O problema

<div align="center">
<img src="docs/images/foto-aviso-painel.jpg" alt="Tela de Aviso na central multimídia do Honda Civic G10" width="640"/>
</div>

Cada vez que você liga o carro, a central mostra:

> **"Aviso — O motorista é o responsável pela condução segura deste veículo..."**

E você tem que clicar **OK**. Toda. Vez. Até o CarPlay subir. Toda ligada do carro, 365 dias por ano, por anos.

A Honda **nunca** liberou uma configuração pra desabilitar isso.

## ✨ A solução — em duas camadas

Tudo é entregue via **EvilValet** (descoberta por [juniperspring.org](https://juniperspring.org/posts/honda-evil-valet/)) — um pacote OTA "falso" assinado com a testkey AOSP pública, que o `daupdater` do carro aceita como se fosse update oficial.

### Camada 1 — AutoOk (safety net automático)

APK + `su` setuid instalados em `/system/`. O APK monitora o logcat, detecta a Activity do aviso aparecer e dispara um `input tap` simulado em (400, 350). Aviso aparecia por ~3 s e sumia sozinho. Rede de segurança: se o patch da Camada 2 falhar por qualquer motivo, essa rota continua tapando.

### Camada 2 — Fase 10 (patch smali no DaLauncher — a solução definitiva)

Patch de **uma instrução no bytecode** do `DaLauncher.apk` (`OpeningDivideActivity.smali:671`): `if-nez v0, :cond_9` → `goto :cond_9`. Força o fluxo de boot a pular o `DisclaimerFragment` e cair direto no caminho que já carregava CarPlay, navegação e tudo mais. **Aviso simplesmente não existe mais no fluxo**, para sempre.

Um segundo patch (Fase 10.1) reduz uma tela intermediária de ecoscore de ~6 s para ~1 s.

**Resultado observado no carro (29/10/2026):** aviso removido, CarPlay projeta, navegação funciona, câmera de ré funciona, zero crash. Detalhes em [`docs/fase10-deploy-2026-10-29/README.md`](docs/fase10-deploy-2026-10-29/README.md).

**Rede de segurança preservada:** o AutoOk (Camada 1) permanece em `/system/app/` como fallback automático na primeira semana. Pode ser removido depois da janela estável via `tooling/ota-build/output-rollback/` sem afetar o patch.

---

## 🏗️ Como funciona (visão de 60 segundos)

<div align="center">
<img src="docs/images/arquitetura.svg" alt="Pipeline: PC → pacote OTA → pendrive → cold boot → recovery → /system" width="900"/>
</div>

**No PC** (uma vez, ~15 min):
1. Compila o APK AutoOk (`gradlew assembleRelease`) **ou** rebuilda o `DaLauncher.apk` patcheado (`bash tooling/fase10/rebuild-dalauncher.sh`)
2. Assina com testkey AOSP (`apksigner`)
3. Monta pacote OTA assinado com testkey AOSP (`python3 build.py` para AutoOk; `python3 build-dalauncher-fase10.py` para Fase 10)
4. Grava num pendrive FAT32 (`prepare-pendrive-install.sh`)

**No carro** (uma vez por deploy, ~10 min):
1. Pendrive na porta USB-A frontal
2. Segura `AUDIO` por 5s → confirma "Quer reiniciar?"
3. Central reinicia, recovery aplica o pacote
4. APK em `/system/` — permanente

**Em operação** (automático, pra sempre):
- Com só a Camada 1 (AutoOk): a cada boot, APK dispensa o aviso em ~3 s
- Com a Camada 2 (Fase 10): o aviso **nem chega a aparecer**
- Zero manutenção. Zero interação.

---

## 🚗 Compatibilidade

### ✅ Confirmado funcionando

| Carro | DA Version | Mercado | Rom type | Status |
|---|---|---|---|---|
| Honda Civic 2017 EXL | `1.F187.16` | 🇧🇷 Brasil | `0040` | ✅ AutoOk deployado 2026-10-16 · Fase 10 deployada 2026-10-29 |

### 🤷 Potencialmente compatível (não testado)

Mesmo framework Mitsubishi Andromeda — provável que funcione com adaptação de 2 valores:
- **Civic G10 2016-2021** (US, EU, AU, outras BR)
- **Civic Avancier, Civic URV**
- **CR-V 2016-2021** (algumas safras)
- **Accord 2016+** com Display Audio

Se você tem outra safra, [ajude a comunidade](#-contribuindo) — bastam 2 informações pra confirmar: o `custom_rom.type` e a resolução da tela.

👉 Como adaptar pra outra safra: [`docs/pt-BR/03-descobrindo-sua-safra.md`](docs/pt-BR/03-descobrindo-sua-safra.md)

---

## 🚀 Quick Start

**Dono de Civic 2017 EXL BR?** Deploy em ~20 minutos:

👉 **[QUICKSTART.md](QUICKSTART.md)** — passo a passo completo

Resumo:
```bash
git clone https://github.com/khalleb/honda-civic-headunit.git
cd honda-civic-headunit
./MIGRATION/setup.sh                     # clona dependências
cd our-apk && ./gradlew assembleRelease  # compila APK
# ... assina + copia pro overlay ...
python3 tooling/ota-build/build.py       # pacote OTA
sudo ./tooling/scripts/prepare-pendrive-install.sh /dev/sda
# No carro: AUDIO 5s + confirmar reiniciar
```

**Outra safra?** Primeiro adapte seguindo [`docs/pt-BR/03-descobrindo-sua-safra.md`](docs/pt-BR/03-descobrindo-sua-safra.md).

---

## ⚠️ Avisos importantes

- 🧱 **Pode causar brick permanente** da central se feito errado. Troca custa R$ 1.000-2.000.
- 📷 **A tela também é a câmera de ré** — brick = sem ré até trocar.
- 🔄 **OTAs oficiais da Honda podem reverter** a modificação. Precisa redeployar.
- ✅ **CarPlay, Bluetooth, áudio, navegação continuam funcionando** — nossa modificação é cirúrgica.
- 🔒 **Zero backdoor pra Honda detectar.** APK fica como qualquer app do /system/.

**Leia o [DISCLAIMER.md](DISCLAIMER.md) completo antes de executar qualquer coisa.**

---

## 🔬 O que descobrimos no caminho

Além do APK que resolve o aviso, mapeamos muito da plataforma Mitsubishi Andromeda. Útil pra quem quer adaptar pra outra safra, construir outros apps no mesmo HU, ou entender o fluxo real de power da central (LP0, câmera de ré, HMI service start).

Resumo com links pros docs densos: [`DISCOVERIES.md`](DISCOVERIES.md).

Alguns highlights:

- **16 broadcasts do PowerManager** mapeados, com causas conhecidas (`ColdBoot`, `ExitLP0`, `AccOnRestart`). 33 APKs do shipping escutam `ACTION_HMI_SERVICE_START` — é o contrato oficial de recovery pós-LP0, não workaround.
- **364 interfaces AIDL** em 63 domínios. `appservice.vehicleinfomanager` sozinho tem 37 listeners cobrindo marcha, velocidade, VIN, FOB key atual, ângulo do volante.
- **445 broadcasts vendor** em 48 prefixos (navi, HFT, câmera, launcher, PowerManager, diag).
- **27 ContentProvider authorities** (9 vendor, incluindo o fluxo real da whitelist Mitsubishi — que, surpresa, é UX-only e não afeta LP0).
- **Hall of fame de 14 bugs** resolvidos com causa raiz documentada — útil pra outros projetos de RE Mitsubishi.

## 🧰 Ferramentas reusáveis

Infraestrutura que vive junto do projeto e serve pra outros HUs com mesmo stack:

- [`tooling/deodex/deodex-apk.sh`](tooling/deodex/deodex-apk.sh) — automatiza odex → APK pra qualquer APK Mitsubishi (toda a vendor-app é pre-dexed). Validado em 160 APKs do dump.
- Pacote OTA EvilValet com `busybox` ARM embarcado — nossa safra precisa porque o recovery BR não tem `/sbin/sh`. Serve pra outras safras do mesmo recovery.
- Pacote OTA de deep-scan — dumpa `/system`, `/data/system/packages.xml`, árvore de partições + `/proc/*` numa passada só. Alimenta o atlas da central.
- Fluxo [REA](https://github.com/morluto/rea) + MCP já configurado em [`tooling/deodex/`](tooling/deodex/) — análise estática de qualquer APK Android pelo agente.

## 🗺️ Para onde isso vai

Objetivo original cumprido em 2026-10-29. O que fica abaixo é exploratório; detalhes em [`ROADMAP.md`](ROADMAP.md).

- **Fase 9 — câmera de ré via API oficial.** Trocar o logcat polling atual por bind no `ICameraAPServiceReverseSignalListener`, com `ACTION_RESUME_CAMERA` como fallback. Hoje já temos TX codes do `IVehicleInfoManagerApService` mapeados (via `alexpotv/Clusters`), inclusive o sinal `MICU_BCM`/`MICU_ICU` que carrega a luz de ré.
- Dumpar `com.honda.displayaudio.whitelist.apk` real pra confirmar formato do XML (hoje é inferido do parser).
- Testar `persist.sys.keyoff_reboot=1` — teoricamente força cold boot a cada keyoff e elimina a complexidade LP0.
- Trocar o `/system/xbin/su` por SuperSU oficial — o atual é KingoSU (achado da varredura do GitHub de 2026-10-27).

---

## 📚 Documentação

### 🇧🇷 Em português

| Doc | Descrição |
|---|---|
| [`QUICKSTART.md`](QUICKSTART.md) | Deploy em 20 min |
| [`docs/pt-BR/00-visao-geral.md`](docs/pt-BR/00-visao-geral.md) | O que foi feito e por quê |
| [`docs/pt-BR/01-arquitetura-ataque.md`](docs/pt-BR/01-arquitetura-ataque.md) | Como EvilValet funciona |
| [`docs/pt-BR/02-pre-requisitos.md`](docs/pt-BR/02-pre-requisitos.md) | Hardware, software, keystore |
| [`docs/pt-BR/03-descobrindo-sua-safra.md`](docs/pt-BR/03-descobrindo-sua-safra.md) | Adaptar pra outras safras |
| [`docs/pt-BR/04-build-do-pacote.md`](docs/pt-BR/04-build-do-pacote.md) | Compilar o pacote OTA |
| [`docs/pt-BR/05-deploy-no-carro.md`](docs/pt-BR/05-deploy-no-carro.md) | Protocolo no carro |
| [`docs/pt-BR/06-troubleshooting.md`](docs/pt-BR/06-troubleshooting.md) | Debug quando algo não funciona |
| [`docs/pt-BR/07-rollback.md`](docs/pt-BR/07-rollback.md) | Reverter tudo |
| [`docs/pt-BR/08-backups-e-rollback.md`](docs/pt-BR/08-backups-e-rollback.md) | Catálogo de backups |

### 🇺🇸 In English

| Doc | Description |
|---|---|
| [`README.en.md`](README.en.md) | README |
| [`docs/en/00-overview.md`](docs/en/00-overview.md) | What the project does and why |
| [`docs/en/01-attack-architecture.md`](docs/en/01-attack-architecture.md) | How the EvilValet attack works |
| [`docs/en/02-prerequisites.md`](docs/en/02-prerequisites.md) | Hardware, software, keystore |
| [`docs/en/03-finding-your-firmware.md`](docs/en/03-finding-your-firmware.md) | Adapt for other firmware |
| [`docs/en/04-building-the-package.md`](docs/en/04-building-the-package.md) | Build the OTA package step by step |
| [`docs/en/05-deploying-in-car.md`](docs/en/05-deploying-in-car.md) | Deploy protocol in the car |
| [`docs/en/06-troubleshooting.md`](docs/en/06-troubleshooting.md) | Decision tree when something fails |
| [`docs/en/07-rollback.md`](docs/en/07-rollback.md) | Revert everything |
| [`docs/en/08-backups.md`](docs/en/08-backups.md) | Full backup catalog |

### 🔬 Deep technical dive

- [`DISCOVERIES.md`](DISCOVERIES.md) — Índice navegável dos achados técnicos
- [`ROADMAP.md`](ROADMAP.md) — Próximos passos, descartados com motivo
- [`docs/MAPA.md`](docs/MAPA.md) — **Atlas navegável da central** (partições, APKs, services, pipeline)
- [`docs/fase7-deploy-2026-10-16/`](docs/fase7-deploy-2026-10-16/) — Camada 1 (AutoOk): jornada, descobertas, receitas, dumps, arquitetura
- [`docs/fase10-deploy-2026-10-29/`](docs/fase10-deploy-2026-10-29/) — **Camada 2 (patch smali)**: timeline do deploy, Fase 10.1, logs do carro
- [`docs/raio-x/`](docs/raio-x/) — Scan estático da plataforma: 364 AIDLs, 445 broadcasts, 27 providers, 48 sysprops, trust map de 110 APKs + RE Camada 2 das services (volante, OTA oficial, veículo, áudio) + varredura de 33 projetos adjacentes no GitHub
- [`docs/whitelist-mitsubishi-2026-10-19.md`](docs/whitelist-mitsubishi-2026-10-19.md) — Fluxo completo da whitelist Mitsubishi + mapeamento do recovery pós-LP0

---

## 🙏 Créditos

Este projeto não existiria sem o trabalho de:

- **[librick / Eric McDonald](https://juniperspring.org/)** — descoberta e documentação técnica da vulnerabilidade **EvilValet**, `ota-builder`, `apk-rebuilder` ([ic1101](https://github.com/librick/ic1101))
- **[@codeage](https://github.com/codeage/root-honda)** — ferramenta de root com `su` ARM estático, SuperSU, análise da whitelist Mitsubishi
- **[@jersacct](https://github.com/jersacct/2016PilotOneClick)** — projeto-mãe para rooting de Honda via DirtyCOW

**Nossa contribuição** é a adaptação para a safra brasileira `1.F187.16` (rom type `0040`, combo `AUDIO 5s` para cold boot, descoberta de que o recovery BR não tem `/sbin/sh` e precisa de busybox embarcado, APK persistente que re-arma após cada tap, pipeline de deep-scan pra sincronizar o atlas da central) **e a Fase 10** (descoberta do gate `OpeningDivideActivity.sDisclamerFlg` como static boolean em memória, dois patches smali de uma instrução cada, pipeline de rebuild auto-contido com prova de bytecode `orig → patch`).

Detalhes técnicos: [`docs/fase7-deploy-2026-10-16/02-descobertas-tecnicas.md § 0`](docs/fase7-deploy-2026-10-16/02-descobertas-tecnicas.md#0-contribuições-novas-deste-projeto).

---

## 🤝 Contribuindo

Encorajamos:

1. **Tem outra safra Honda G10?** Abra uma issue com o template [`nova-safra.md`](.github/ISSUE_TEMPLATE/nova-safra.md). Informe VIN prefix, DA version, `custom_rom.type`, resolução. Juntamos matriz de compatibilidade.
2. **Encontrou bug ou melhoria?** Issues + PRs bem-vindos.
3. **Quer traduzir pra outro idioma?** Fork + PR com nova pasta `docs/<lang>/`. Prioridade: completar tradução EN dos docs 01, 02, 04, 05, 06.
4. **Testou em outro carro e funcionou?** Reporta via issue — vira linha na tabela de compatibilidade.

Veja [`CONTRIBUTING.md`](CONTRIBUTING.md) pra detalhes.

---

## 📄 Licença

Código: [MIT](LICENSE). Documentação: CC BY 4.0.

Software proprietário Honda/Mitsubishi referenciado é propriedade de seus respectivos donos. **Este repo NÃO distribui firmware proprietário** — você precisa dumpar do seu próprio HU (ver [`docs/pt-BR/03-descobrindo-sua-safra.md`](docs/pt-BR/03-descobrindo-sua-safra.md)).

---

<div align="center">

**Feito pela comunidade Civic G10, pra comunidade Civic G10.**

🇧🇷 **Português** · [🇺🇸 English](README.en.md)

</div>
