<div align="center">

<img src="docs/images/logo.svg" alt="Honda Civic G10 Skip Disclaimer" width="200"/>

# Honda Civic G10 — Skip Disclaimer

**Elimine automaticamente a tela de "Aviso" que aparece sempre que você liga seu Honda Civic G10 BR**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Done](https://img.shields.io/badge/status-done-brightgreen)]()
[![Platform](https://img.shields.io/badge/platform-Android_4.2.2_%7C_Tegra_3-blue)]()
[![Safra](https://img.shields.io/badge/safra_testada-1.F187.16_BR-orange)]()

🇧🇷 **Português** · [🇺🇸 English](README.en.md)

</div>

---

## 🎯 O que esse projeto faz

Cada vez que você liga o carro, a tela da central mostra o Aviso:

> **"O motorista é o responsável pela condução segura..."**

E você tem que clicar OK. Toda. Vez. Até o CarPlay subir.

Esse projeto **suprime esse aviso automaticamente** — você liga o carro, aparece o aviso, e em ~2 segundos ele some sozinho. Sem clicar em nada.

## ✨ Como funciona

1. Um pacote OTA (atualização de firmware falsa, assinada com testkey AOSP via vulnerabilidade **EvilValet** descoberta por [juniperspring.org](https://juniperspring.org/posts/honda-evil-valet/)) instala:
   - **`AutoOk.apk`** em `/system/app/` — monitora logcat, detecta quando a tela do Aviso aparece.
   - **`su`** setuid em `/system/xbin/` — root permanente.
2. No boot do carro, o APK recebe `BOOT_COMPLETED` e inicia o watcher.
3. Quando a tela de Aviso aparece, o APK espera 2s e dispara `su -c "input tap 400 350"` — simula o toque no botão OK.
4. Aviso some. Você nem percebeu.

## 🚗 Testado em

**Única safra confirmada:**

| Carro | DA Version | Mercado | Rom type | Status |
|---|---|---|---|---|
| Honda Civic 2017 EXL | `1.F187.16` | 🇧🇷 Brasil | `0040` | ✅ Funciona |

**Potencialmente compatível** (framework Mitsubishi Andromeda igual) — não testado:

- Civic G10 2016–2021 (US, EU, AU, outros mercados BR)
- Civic Avancier, Civic URV
- CR-V 2016–2021 (algumas safras)
- Accord 2016+ com Display Audio

**Se você tem outra safra**, [ajude a comunidade](#-contribuindo) — bastam 2 informações pra confirmar se funciona na sua: o `custom_rom.type` e a resolução da tela.

## 🚀 Quick Start

Se você é dono de Civic 2017 EXL BR e quer deployar hoje:

👉 **[Siga o QUICKSTART.md](QUICKSTART.md)** — passo a passo em 10 minutos (notebook) + 10 minutos (carro).

Para safras diferentes, antes do deploy você precisa:
1. Descobrir seu `custom_rom.type` → [`docs/pt-BR/03-descobrindo-sua-safra.md`](docs/pt-BR/03-descobrindo-sua-safra.md)
2. Confirmar coordenadas do botão OK (pode ser (400, 350) ou outras)
3. Rebuild do pacote com valores corretos

## ⚠️ Avisos importantes

- **Pode causar brick permanente** da central se feito errado. Troca custa R$ 1.000-2.000.
- **A tela da central também é a câmera de ré** — brick = sem ré até trocar.
- **Updates oficiais da Honda podem reverter** a modificação. Precisará redeployar.
- **CarPlay, Bluetooth, áudio, navegação continuam funcionando** — nossa modificação é cirúrgica.
- **Zero backdoor pra Honda detectar.** APK fica como se fosse um app do sistema.

**Leia o [DISCLAIMER.md](DISCLAIMER.md) completo antes de executar qualquer coisa.**

## 📚 Documentação completa

- 🇧🇷 Português: [`docs/pt-BR/`](docs/pt-BR/)
- 🇺🇸 English: [`docs/en/`](docs/en/)

| Documento | Descrição |
|---|---|
| [`QUICKSTART.md`](QUICKSTART.md) | Deploy em 20 minutos |
| [`docs/pt-BR/00-visao-geral.md`](docs/pt-BR/00-visao-geral.md) | O que foi feito e por quê |
| [`docs/pt-BR/01-arquitetura-ataque.md`](docs/pt-BR/01-arquitetura-ataque.md) | Como EvilValet funciona |
| [`docs/pt-BR/02-pre-requisitos.md`](docs/pt-BR/02-pre-requisitos.md) | Ferramentas, hardware, software |
| [`docs/pt-BR/03-descobrindo-sua-safra.md`](docs/pt-BR/03-descobrindo-sua-safra.md) | Como adaptar pra sua central |
| [`docs/pt-BR/04-build-do-pacote.md`](docs/pt-BR/04-build-do-pacote.md) | Compilar o pacote OTA |
| [`docs/pt-BR/05-deploy-no-carro.md`](docs/pt-BR/05-deploy-no-carro.md) | Protocolo no carro |
| [`docs/pt-BR/06-troubleshooting.md`](docs/pt-BR/06-troubleshooting.md) | Debug quando algo não funciona |
| [`docs/pt-BR/07-rollback.md`](docs/pt-BR/07-rollback.md) | Reverter tudo |

**Deep dive técnico** (para pesquisadores):

- [`docs/fase7-deploy-2026-10-16/`](docs/fase7-deploy-2026-10-16/) — 7 docs com jornada, descobertas, receitas, dumps, arquitetura do APK, manutenção
- [`docs/images/flow-evilvalet.md`](docs/images/flow-evilvalet.md) — diagramas Mermaid do fluxo

## 🙏 Créditos

Este projeto não existiria sem o trabalho de:

- **librick / Eric McDonald** ([juniperspring.org](https://juniperspring.org/), [ic1101](https://github.com/librick/ic1101)) — descoberta e documentação técnica da vulnerabilidade EvilValet, `ota-builder`, `apk-rebuilder`.
- **@codeage** ([root-honda](https://github.com/codeage/root-honda)) — ferramenta de root com `su` ARM estático, SuperSU, análise da whitelist Mitsubishi.
- **@jersacct** ([2016PilotOneClick](https://github.com/jersacct/2016PilotOneClick)) — projeto-mãe para rooting de Honda baseado em DirtyCOW.

**Nossa contribuição é a adaptação para a safra brasileira `1.F187.16`** (rom type `0040`, combo `AUDIO 5s` para cold boot, descoberta de que o recovery da safra BR não tem `/sbin/sh` e precisa de busybox embarcado, APK persistente que re-arma depois de cada tap). Veja [`docs/fase7-deploy-2026-10-16/02-descobertas-tecnicas.md § 0`](docs/fase7-deploy-2026-10-16/02-descobertas-tecnicas.md#0-contribuições-novas-deste-projeto) para detalhes.

## 🤝 Contribuindo

Encorajamos contribuições:

1. **Tem outra safra Honda G10?** Abra uma issue usando o template [`nova-safra.md`](.github/ISSUE_TEMPLATE/nova-safra.md) com: VIN prefix, DA version, `custom_rom.type` (como descobrir no doc), resolução da tela. Juntamos uma matriz de compatibilidade.
2. **Encontrou bug ou melhoria?** Issues + PRs bem-vindos.
3. **Quer traduzir pra outro idioma?** Fork + PR com nova pasta em `docs/<lang>/`.

## 📄 Licença

Código: [MIT](LICENSE). Documentação: CC BY 4.0.

Software proprietário Honda/Mitsubishi referenciado é propriedade de seus respectivos donos. **Este repo não distribui firmware proprietário** — você precisa dumpar do seu próprio HU (ver `docs/pt-BR/03-descobrindo-sua-safra.md`).

---

<div align="center">

**Made for the Honda Civic G10 community.**
**Feito pela comunidade, para a comunidade.**

</div>
