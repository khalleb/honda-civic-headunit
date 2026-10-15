# Briefing — Projeto Honda Civic G10 Head Unit

> **Para abrir uma nova sessão do Claude (Claude Code ou chat):** cole o texto
> abaixo como primeiro prompt. Ele contextualiza a sessão nova com todo o
> histórico técnico do projeto.

---

## 📋 PROMPT PRA COLAR NUMA NOVA SESSÃO DO CLAUDE

```
Oi. Estamos retomando um projeto de engenharia reversa da central multimídia
do meu Honda Civic 2017 (G10) brasileiro, feito ao longo de várias sessões
anteriores. O objetivo é eliminar a tela de "Aviso" (OK) que aparece na partida
do carro, construindo nosso próprio APK auto-OK (sem usar o Honda Hack pago).

Toda a documentação técnica consolidada está em:
    ~/repositorios/honda-civic/central-multimidia-civic-g10-kb.md

Por favor leia o KB inteiro antes de qualquer coisa — ele contém:
- Hardware (NVIDIA Tegra 3, Android 4.2.2, framework Mitsubishi "Andromeda")
- Pacotes do sistema (com.clarion.displayaudio.*)
- Mecanismo do Aviso (renderizado por APK local, não via CAN bus)
- Caminho de root (dirtyCOW CVE-2016-5195)
- Análise do HondaHack.apk (feature "auto_confirm_agreement" descoberta)
- Algoritmo inferido do auto-OK (BOOT_COMPLETED → readlogs → su -c "input tap X Y")
- Ferramentas instaladas (apktool, jadx, ADB)
- Repositórios de referência (root-honda, 2016PilotOneClick, ic1101)

Estamos atualmente entre a Fase 2 e Fase 3:
- Fase 0: ✅ Preparar ambiente de análise (feito)
- Fase 1: ⏳ Reconhecimento no carro (fotos Manual Diag + Build/Kernel) — pendente
- Fase 2: ⏳ Hardware — tenho um cabo USB-C↔USB-A que vou testar
- Fase 3: ⏳ ADB + pull /system/app
- Fase 4: ⏳ Analisar APKs → achar Activity e coords do Aviso
- Fase 5: ⏳ Escrever nosso APK auto-OK
- Fase 6: ⏳ Rootear a central
- Fase 7: ⏳ Deploy e teste

Quando estiver pronto, me diga que leu o KB e vamos continuar de onde paramos.
```

---

## 🗂 Estado do projeto no momento desta migração

- **Data:** 2026-10-15
- **Fase ativa:** Fase 2 (hardware)
- **Pendências pessoais:**
  - Testar cabo USB-C↔USB-A existente (teste do pendrive para confirmar que leva dados)
  - Pendrive FAT32 16GB+ vazio
  - Fotos do Manual Diag no carro (Fase 1, sem risco)

## 🧰 O que o `setup.sh` já faz pra você

- Instala dependências do apt: java, adb, git, curl, unzip
- Baixa apktool 2.11.1 e jadx 1.5.6
- Clona `root-honda`, `2016PilotOneClick`, `ic1101`
- Descompila `HondaHack.apk` (análise feita no PC Windows, só pra ter rápido)
- Copia o KB e este briefing pra `~/honda-civic/`

## 🎯 Objetivos do projeto (recapitulação)

1. **Primário:** eliminar a tela de "Aviso" que exige tocar OK na partida.
2. **Secundário (aprendizado):** entender a plataforma por dentro.
3. **Decisão:** fazer manual, sem Honda Hack pago; construir nosso APK.

## ⚠️ Riscos conhecidos e aceitos pelo dono

- Possibilidade de brick da central (R$1-2k pra trocar).
- A tela da central é a mesma da câmera de ré.
- Updates da concessionária reverteriam mods.
- Risco corporativo de usar notebook da empresa (EDR, políticas) — avisado.

## 🚦 Status das Fases (ver KB para detalhes)

| # | Fase | Status |
|---|------|--------|
| 0 | Preparar ambiente análise | ✅ Completa |
| 1 | Reconhecimento no carro (fotos) | ⏳ Pendente |
| 2 | Hardware (cabo + pendrive) | ⏳ Em andamento |
| 3 | ADB + extrair APKs | ⏳ Pendente |
| 4 | Análise APKs → achar Aviso | ⏳ Pendente |
| 5 | Escrever APK auto-OK | ⏳ Pendente |
| 6 | Root da central | ⏳ Pendente |
| 7 | Deploy + teste | ⏳ Pendente |
