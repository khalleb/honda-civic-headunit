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

## O que fizemos

Deployamos um APK próprio em `/system/app/AutoOk.apk` + `su` setuid em `/system/xbin/`:

1. **Instalação:** via pacote OTA (atualização de firmware falsa) assinado com testkey AOSP pública — usando a vulnerabilidade **EvilValet** descoberta e documentada por librick / Eric McDonald.
2. **Operação:** nosso APK monitora logcat; quando a Activity do Aviso é iniciada, dispara `su -c "input tap 400 350"` — simula um toque invisível no botão OK.
3. **Persistência:** APK é um Service que fica vivo pra sempre; a cada ligar do carro, intercepta o Aviso.

## Resultado

- Aviso aparece e some sozinho em ~10 segundos
- Zero interação manual
- CarPlay, Bluetooth, áudio, navegação continuam funcionando
- Rollback disponível a qualquer momento via pacote OTA de remoção

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

- Para deployar na sua safra `1.F187.16` BR: → [`QUICKSTART.md`](../../QUICKSTART.md)
- Para outras safras: → [`03-descobrindo-sua-safra.md`](03-descobrindo-sua-safra.md)
- Para contexto de risco: → [`DISCLAIMER.md`](../../DISCLAIMER.md)
