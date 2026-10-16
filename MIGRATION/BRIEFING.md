# Briefing — Projeto Honda Civic G10 Head Unit

> **🎉 PROJETO CONCLUÍDO EM 2026-10-16.** Objetivo primário atingido: Aviso de partida é suprimido
> automaticamente em cada ligar do carro. Zero interação manual.
>
> Este briefing serve para contextualizar uma sessão nova do Claude sobre o estado final e os pontos
> de entrada caso você precise mexer de novo no projeto.

---

## 📋 PROMPT PRA COLAR NUMA NOVA SESSÃO DO CLAUDE

```
Oi. Estou retomando um projeto de engenharia reversa da central multimídia do meu
Honda Civic 2017 (G10) EXL brasileiro. O projeto foi CONCLUÍDO com sucesso em
2026-10-16: a tela de "Aviso" da partida é suprimida automaticamente em cada
boot da central, via APK auto-OK instalado em /system/app + binário `su` setuid
em /system/xbin.

Toda a documentação da fase final está em:
    ~/repositorios/honda-civic/docs/fase7-deploy-2026-10-16/

Comece por:
    ~/repositorios/honda-civic/docs/fase7-deploy-2026-10-16/README.md

Credenciais técnicas rápidas:
- Central: 1.F187.16, Mitsubishi Andromeda, Android 4.2.2, Tegra 3 vcm30t30
- Rom type (chave do EvilValet): 0040
- Combo pra cold boot: AUDIO 5s + confirmar reiniciar
- Botão OK do Aviso: centro em (400, 350), tela 800×480
- Activity do Aviso: com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity
- Partição /system: /dev/block/platform/sdhci-tegra.3/by-name/APP (= mmcblk0p3)
- APK em /system/app/AutoOk.apk (SHA-1 e76d35741c5fafb8289f97f9565aaf8e1bff4f66)
- su em /system/xbin/su mode 06755 setuid

O que fizemos de origem até concluir:
- Rota de ADB via passcord no Settings: BLOQUEADA na safra BR, abandonada.
- Rota EvilValet (testkey AOSP + pendrive OTA): FUNCIONOU. Precisava descobrir
  o rom_type 0040 (safra BR não documentada publicamente antes de nós).
- Pacote OTA instala APK + su numa única passagem.
- APK monitora logcat, detecta Activity do Aviso, tapa (400,350) via `su -c
  "input tap"`. É persistente (re-arma depois de cada tap).

Me diga o que você precisa fazer — provavelmente é uma dessas:
(a) atualizar o APK (mudar coord, mudar delay, mudar lógica)
(b) rollback (remover tudo que foi instalado)
(c) re-dumpar o /system para análise atualizada
(d) troubleshoot (algo parou de funcionar)
(e) explorar melhoria futura
```

---

## 🗂 Estado final do projeto

- **Data de conclusão:** 2026-10-16 ~10:55 BRT
- **Resultado:** 100% funcional em teste real (confirmado pelo dono em múltiplos ciclos de desligar/ligar a chave)
- **Rota usada:** EvilValet (CVE sistemática do Mitsubishi Andromeda) via pendrive OTA
- **Risco de brick realizado:** zero. Nenhum arquivo preexistente foi modificado. Apenas 2 arquivos novos adicionados (`AutoOk.apk` + `su`).

## 🧰 O que o `setup.sh` já faz pra você

- Instala dependências do apt: java, adb, git, curl, unzip
- Baixa apktool 2.11.1 e jadx 1.5.6
- Clona `root-honda`, `2016PilotOneClick`, `ic1101`
- Descompila `HondaHack.apk` (análise feita no PC Windows, só pra ter rápido)
- Copia o KB e este briefing pra `~/honda-civic/`

Para o build do APK auto-OK + pacote OTA, precisa adicionalmente:
- JDK 17 Temurin (`~/sdks/jdk-17`) — AGP 7.4.2 não suporta JDK 25
- Android SDK API 33 + build-tools 33.0.2 (`~/sdks/Android`)
- Gradle 7.6.4 (pinned via `gradlew`)

Setup detalhado em `MIGRATION/setup.sh` + `docs/fase5-apk/compilar.md`.

## 🎯 Objetivos do projeto (retrospectiva)

1. **Primário:** eliminar a tela de "Aviso" que exige tocar OK na partida. **✅ ATINGIDO.**
2. **Secundário (aprendizado):** entender a plataforma por dentro. **✅ ATINGIDO** (ver `docs/fase7-deploy-2026-10-16/02-descobertas-tecnicas.md`).
3. **Decisão:** fazer manual, sem Honda Hack pago; construir nosso APK. **✅ CUMPRIDO.**

## ⚠️ Riscos conhecidos e aceitos pelo dono (resposta pós-deploy)

- Possibilidade de brick da central: **não realizada**. Nossa modificação é cirúrgica e aditiva.
- A tela da central é a mesma da câmera de ré: **ainda é**. Nenhum efeito observado na câmera.
- Updates da concessionária reverteriam mods: **sim**, se a Honda emitir OTA, o APK pode ser removido. Procedimento de reinstalação em `docs/fase7-deploy-2026-10-16/05-manutencao-e-futuro.md § Após atualização OTA Honda`.
- CarPlay/Bluetooth: **continuam funcionando normalmente**. Confirmado pós-deploy.

## 🚦 Status das Fases (final)

| # | Fase | Status |
|---|------|--------|
| 0 | Preparar ambiente análise | ✅ Completa |
| 1 | Reconhecimento no carro (fotos + Self-Diagnosis) | ✅ Completa (2 sessões) |
| 2 | Hardware (cabo + pendrive) | ✅ Pendrive serve. Cabo USB-A/A abandonado (passcord BR bloqueado). |
| 3 | ADB + extrair APKs | ❌ Abandonada. Substituída pela Rota B. |
| 4 | Análise APKs → achar Aviso | ✅ Feita via dump do /system via OTA. Activity + coords em `docs/fase7-deploy-2026-10-16/02-descobertas-tecnicas.md § 5`. |
| 5 | Escrever APK auto-OK | ✅ Compilado, assinado, deployado. `our-apk/app/build/outputs/apk/release/AutoOk.apk`. |
| 5b | Montar pacote OTA EvilValet | ✅ `tooling/ota-build/output/20261016T135537Z/0040/SwUpdate.mdt`. |
| 6 | Root da central | ✅ Via `su` setuid instalado junto no OTA. |
| 7 | Deploy + teste | ✅ **COMPLETA.** APK funciona em testes reais. |

## 📂 Pontos de entrada em `docs/`

- `docs/proxima-sessao.md` — ponto de partida operacional, atualizado com estado final.
- `docs/fase7-deploy-2026-10-16/` — pasta com toda a documentação do deploy final.
- `docs/pesquisa-rotas-sem-adb-2026-10-15.md` — contexto da escolha da Rota B (EvilValet).
- `central-multimidia-civic-g10-kb.md` — base de conhecimento histórica (pré-conclusão).

## 🔄 Em caso de precisar reverter

```bash
# Script de rollback (remove AutoOk.apk e su de /system)
sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sdX
# Depois: deployar no carro via protocolo normal (pendrive porta frontal + AUDIO 5s + confirmar)
```

Se o script não existir mais (reinstalação de sistema), reconstruir:

```bash
python3 tooling/ota-build/build-rollback.py
# Depois carregar pendrive manualmente com SwUpdate2.txt + 0040/SwUpdate.mdt
```

Instruções detalhadas em `docs/fase7-deploy-2026-10-16/05-manutencao-e-futuro.md § Rollback completo`.
