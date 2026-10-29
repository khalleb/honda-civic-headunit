# 00 — Visão geral

## Problema

Toda vez que você liga seu Honda Civic G10 (safra brasileira), a central multimídia mostra a tela:

> **"Aviso — O motorista é o responsável pela condução segura..."**

Você precisa tocar OK antes de poder usar CarPlay, rádio ou qualquer coisa. Pequena dor. Diária. Multiplicada por anos de uso = chatice considerável.

A Honda **nunca** liberou configuração para desabilitar essa tela — é tratada como responsabilidade legal.

## Opções existentes antes deste projeto

| Opção | Custo | Problemas |
|---|---|---|
| Honda Hack (`cn.autohack.hondahack`) | US$ 25 | Fechado, código obfuscado com Tencent StubShell, você paga pra sempre, autor pode sumir |
| Modificar o launcher | — | Risco de brick alto, requer root prévio, muito complexo |
| Nenhum | — | Clicar OK todo dia |

## O que fizemos — duas camadas

Tudo é entregue via **EvilValet** (vulnerabilidade descoberta e documentada por librick / Eric McDonald): pacotes OTA assinados com a testkey AOSP pública, aceitos pelo `daupdater` do carro como se fossem atualização oficial da Honda.

### Camada 1 — AutoOk (safety net automático, Fase 7, 2026-10-16)

APK próprio em `/system/app/AutoOk.apk` + `su` setuid em `/system/xbin/`. O APK monitora o logcat, detecta a Activity do Aviso ser iniciada e dispara `su -c "input tap 400 350"` — simula um toque no botão OK. **Resultado:** aviso aparecia e sumia sozinho em ~3 s, sem interação manual.

### Camada 2 — Fase 10 (patch smali no DaLauncher, 2026-10-29)

Patch de **uma instrução no bytecode** do `DaLauncher.apk` (`OpeningDivideActivity.smali:671`): `if-nez v0, :cond_9` → `goto :cond_9`. Força o fluxo de boot a pular o `DisclaimerFragment` (a tela do Aviso) e cair direto no caminho que já carregava CarPlay, navegação e tudo mais. **O aviso simplesmente não existe mais no fluxo**, para sempre.

Um segundo patch (Fase 10.1, mesmo dia) troca `const/16 v1, 0x1388` por `const/16 v1, 0x1f4` em `EcoFragment.startNoOperationTimer` — reduz uma tela intermediária de ecoscore de ~6 s para ~1 s mantendo todas as 4 chamadas que CarPlay/Navegação esperam (`DISCLAIMER_COMPLETE`, `setDisplayPermission`, `disclaimerDisappeared`, `setDisclaimerPassed`).

**Resultado observado no carro em 2026-10-29:** aviso removido completamente, CarPlay projeta, navegação funciona, câmera de ré funciona, zero crash. Guia passo a passo pra reaplicar: [`09-fase10-remover-aviso.md`](09-fase10-remover-aviso.md). Timeline completa do deploy real: [`../fase10-deploy-2026-10-29/README.md`](../fase10-deploy-2026-10-29/README.md).

## Resultado

| Com | Experiência visual | Pré-requisito |
|---|---|---|
| **Só Camada 1 (AutoOk)** | Aviso aparece e some sozinho em ~3 s | Pacote OTA do AutoOk |
| **Camadas 1 + 2 (recomendado)** | **Aviso não aparece.** Tela de ecoscore por ~1 s no lugar | Pacote OTA do AutoOk + pacote da Fase 10 |

CarPlay, Bluetooth, áudio, navegação, câmera de ré **continuam funcionando** nas duas rotas. Rollback disponível a qualquer momento via pacotes OTA correspondentes.

## Para quem é

- **Você:** dono de Civic G10 brasileiro (`1.F187.16`, EXL ou similar). Está testado e funciona.
- **Potencialmente outros:** safras G10 2016-2021 US/EU/AU, Civic Avancier/URV, CR-V 2016-2021, Accord 2016+. **Não testado** — precisa adaptar coord e rom_type. Veja [`03-descobrindo-sua-safra.md`](03-descobrindo-sua-safra.md).

## Como funciona em alto nível

```
Pendrive FAT32 com SwUpdate.mdt assinado testkey
      │
      ▼ (porta USB-A frontal + AUDIO 5s + confirmar reiniciar)
Central faz cold boot
      │
      ▼
SystemUpdate.apk aceita o update (porque assinatura passa)
      │
      ▼
daupdater valida rom_type (0040 na nossa safra) + reinicia pra recovery
      │
      ▼
Recovery valida assinatura testkey + aplica updater-script
      │
      ▼ (via busybox embarcado + edify mount)
Instala /system/app/AutoOk.apk + /system/xbin/su
      │
      ▼
Boot normal. AutoOkService inicia no BOOT_COMPLETED.
      │
      ▼ (toda vez que o Aviso aparece)
Logcat watcher detecta Activity → su -c input tap 400 350 → Aviso some
```

Diagrama detalhado: [`../images/flow-evilvalet.md`](../images/flow-evilvalet.md).

## Documentação técnica original

Esta sessão de deploy final está em [`docs/fase7-deploy-2026-10-16/`](../fase7-deploy-2026-10-16/) — 7 documentos com narrativa completa, descobertas técnicas detalhadas, receita de build, arquitetura do APK, manutenção, catálogo dos dumps.

Os docs nesta pasta (`docs/pt-BR/`) são **versão mais acessível** para pessoas que queiram usar/adaptar, sem precisar ler a jornada técnica inteira.

## Próximos passos

- Para deployar na sua safra `1.F187.16` BR: → [`QUICKSTART.md`](../../QUICKSTART.md) (Camada 1 — AutoOk)
- Para a solução definitiva (Camada 2 — Fase 10): → [`09-fase10-remover-aviso.md`](09-fase10-remover-aviso.md)
- Para outras safras: → [`03-descobrindo-sua-safra.md`](03-descobrindo-sua-safra.md)
- Para contexto de risco: → [`DISCLAIMER.md`](../../DISCLAIMER.md)
