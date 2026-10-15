# honda-civic-headunit

> Engenharia reversa e documentação da central multimídia do Honda Civic
> 10ª geração (2016–2021). Projeto pessoal, aprendizado de plataforma.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: WIP](https://img.shields.io/badge/status-work_in_progress-orange)]()
[![Platform](https://img.shields.io/badge/platform-Android_4.2.2_%7C_Tegra_3-blue)]()

## 🎯 Objetivo

Documentar e, se possível, modificar o firmware da central Honda Display Audio
7" (do Civic G10 brasileiro) para eliminar a tela de "Aviso" (OK) que aparece
toda vez que o carro é ligado — sem usar ferramentas pagas de terceiros.

## 📘 O que você vai encontrar aqui

- **`central-multimidia-civic-g10-kb.md`** — base de conhecimento técnica
  completa (hardware, software, mecanismo de root, análise de APK,
  menus ocultos, pinouts, CAN bus, etc.)
- **`MIGRATION/`** — scripts e docs para configurar o ambiente de desenvolvimento
  em qualquer máquina Linux
- **`CLAUDE.md`** — contexto automático para sessões do Claude Code
- **`DISCLAIMER.md`** — avisos de segurança, legais e técnicos
- **`our-apk/`** — nosso APK auto-OK em construção (ainda não iniciado)

## 🚀 Começando

### 1. Clone o repositório

```bash
git clone https://github.com/<seu-usuario>/honda-civic-headunit.git
cd honda-civic-headunit
```

### 2. Rode o setup (Linux)

```bash
cd MIGRATION
chmod +x setup.sh
./setup.sh
```

O script instala as dependências (Java, ADB, Git, curl, unzip), baixa
`apktool` e `jadx`, clona os repositórios de referência (`root-honda`,
`2016PilotOneClick`, `ic1101`) e descompila o `HondaHack.apk` incluído no
`root-honda` para estudo. Tudo em `~/honda-civic/`.

### 3. Leia a base de conhecimento

```bash
less ~/honda-civic/central-multimidia-civic-g10-kb.md
```

Esse arquivo é o coração do projeto — ler antes de qualquer coisa.

### 4. Siga as fases

O projeto tem 7 fases (ver `central-multimidia-civic-g10-kb.md`), da
preparação de ambiente até deploy e teste do APK auto-OK.

## 🔧 Plataforma estudada

| Campo | Valor |
|---|---|
| Carro | Honda Civic 10ª geração (2016–2021) |
| Central | Display Audio 7" |
| SoC | NVIDIA Tegra 3 (quad-core ARM Cortex-A9, ARMv7) |
| OS | Android 4.2.2 (Jelly Bean) |
| Framework HMI | Mitsubishi "Andromeda" |
| Namespace apps | `com.clarion.displayaudio.*` |
| Board NVIDIA | VCM30T30 |

## 📚 Referências de terceiros usadas

Esses repositórios são **clonados pelo `setup.sh`**, não incluídos aqui:

- [codeage/root-honda](https://github.com/codeage/root-honda) — ferramenta de
  root para Civic 2017 (dirtyCOW + SuperSU + whitelist bypass)
- [jersacct/2016PilotOneClick](https://github.com/jersacct/2016PilotOneClick) —
  projeto-mãe para Honda Pilot 2016
- [librick/ic1101](https://github.com/librick/ic1101) — RE profunda da
  plataforma por Eric McDonald (datasheets Tegra 3, imagens de boot/recovery,
  `ota-builder`)

## ⚠️ Avisos importantes

**Leia `DISCLAIMER.md` antes de executar qualquer coisa deste repositório.**

Resumo rápido dos riscos:
- Modificar a central pode causar **brick permanente** (R$1.000-2.000 para trocar)
- A tela da central é a **câmera de ré** — brick = sem ré
- Updates oficiais da concessionária podem reverter modificações
- Este projeto é para **uso pessoal, educativo e no próprio veículo**

## 🤝 Contribuindo

Projeto pessoal, mas issues e PRs com melhorias de documentação ou achados
técnicos relevantes são bem-vindos. Se você tem um Civic G10 brasileiro e quer
contribuir com dados específicos (versões de firmware, listagem de pacotes,
coordenadas de UI), abra uma issue.

**Não envie:**
- APKs do sistema Honda/Mitsubishi (proprietários)
- Firmware oficial da Honda
- Seus próprios dados pessoais (VIN, serial, dados de rede)

## 📄 Licença

MIT — ver [`LICENSE`](LICENSE). Trabalho próprio neste repositório é liberado
sob essa licença. Marcas e software proprietário referenciados pertencem a
seus respectivos donos.
