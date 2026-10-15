# Contexto automático — Projeto Honda Civic G10 Head Unit

> Este arquivo é lido automaticamente pelo Claude Code ao abrir o diretório
> do projeto. Dá contexto imediato pra qualquer nova sessão do Claude.

## Sobre o projeto

Engenharia reversa da central multimídia (Honda Display Audio 7") de um
Honda Civic 2017 brasileiro. Objetivo primário: eliminar a tela de "Aviso"
que aparece na partida do carro, construindo um APK auto-OK próprio
(sem usar o Honda Hack pago).

## Antes de qualquer coisa — LEIA O KB

A base de conhecimento técnica completa está em:

```
./central-multimidia-civic-g10-kb.md
```

**Sempre leia esse arquivo antes de responder perguntas técnicas sobre
o projeto.** Ele contém:

- Perfil técnico da plataforma (NVIDIA Tegra 3, Android 4.2.2, framework
  Mitsubishi "Andromeda", pacotes `com.clarion.displayaudio.*`)
- Mecanismo de root (CVE-2016-5195 / dirtyCOW)
- Análise do HondaHack.apk (feature `auto_confirm_agreement`)
- Algoritmo inferido do auto-OK
- Combinações de botão dos menus ocultos (Manual Diag)
- CAN bus da família Civic G10
- Lista de ferramentas e dependências

## Estado atual (data da última atualização está no KB)

O projeto está estruturado em **7 fases**, com dependências:

| # | Fase | Pode fazer sem hardware? |
|---|------|---|
| 0 | Preparar ambiente análise | ✅ Sim |
| 1 | Fotos do Manual Diag / Build / Kernel | ✅ Sim (só celular) |
| 2 | Comprar cabo USB-A-A ou testar USB-C-A | 🟡 Comprar hardware |
| 3 | ADB + extrair APKs do /system | ❌ Precisa cabo |
| 4 | Analisar APKs → achar Activity do Aviso | ✅ Sim (após Fase 3) |
| 5 | Escrever nosso APK auto-OK | ✅ Sim (após Fase 4) |
| 6 | Rootear a central (dirtyCOW) | ❌ Precisa cabo + risco |
| 7 | Deploy e teste do APK no carro | ❌ Precisa Fase 6 |

Verificar o KB para o estado específico de cada fase na data atual.

## Como ajudar o dono do projeto

1. **Seja honesto sobre riscos.** O dono já aceitou conscientemente o risco
   de brick (R$1-2k pra trocar central + perda temporária da câmera de ré).
   Mas sempre reforce decisões irreversíveis antes de executar.

2. **Não dê passo-a-passo de exploit explícito.** O caminho de root é via
   ferramentas públicas (`root-honda`, `2016PilotOneClick`). Instrua o
   usuário a seguir a documentação dessas ferramentas, não "receita sua".

3. **Prefira análise estática no PC.** Descompilar APKs, estudar código,
   escrever o APK próprio — tudo isso é zero risco e é onde você mais
   agrega valor.

4. **Backup antes de modificar `/system`.** Sempre. Isso é obrigatório.

5. **Documente achados.** Qualquer coisa nova que descobrirmos juntos vai
   para o KB. É um documento vivo.

## Idioma

O dono fala **português do Brasil**. Prefira respostas nessa língua.
Trechos técnicos (comandos, flags, nomes de pacotes) podem ficar em inglês.

## Convenções

- **Zero comentários no código** (regra do dono — ver histórico no KB)
- Documentação em Markdown
- Commits em português no imperativo

## Links úteis

- Repositório (privado): https://github.com/khalleb/honda-civic-headunit
- Base de conhecimento: `./central-multimidia-civic-g10-kb.md`
- Setup para Linux: `./MIGRATION/setup.sh`
- Disclaimer: `./DISCLAIMER.md`
- Referências de terceiros (clonadas por `setup.sh`):
  - https://github.com/codeage/root-honda
  - https://github.com/jersacct/2016PilotOneClick
  - https://github.com/librick/ic1101
