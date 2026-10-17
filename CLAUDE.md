# Contexto automático — Projeto Honda Civic G10 Head Unit

> Este arquivo é lido automaticamente pelo Claude Code ao abrir o diretório
> do projeto. Dá contexto imediato pra qualquer nova sessão do Claude.

## Sobre o projeto

Engenharia reversa da central multimídia (Honda Display Audio 7") de um
Honda Civic 2017 EXL brasileiro. Objetivo primário: eliminar a tela de "Aviso"
que aparece na partida do carro, construindo um APK auto-OK próprio
(sem usar o Honda Hack pago).

## 🎉 Projeto concluído — 2026-10-16

O objetivo foi atingido. Aviso é suprimido automaticamente em cada boot.

**Antes de responder qualquer pergunta sobre o projeto, LEIA EM ORDEM:**

1. **`docs/MAPA.md`** ⭐ — **Atlas navegável da central** (reflexo do estado real: partições, APKs, services, nossas modificações, hall of fame de bugs). Primeira consulta sempre. Atualize sempre que descobrir fato novo ou modificar algo real.
2. **`docs/fase7-deploy-2026-10-16/README.md`** — Documentação do deploy final.
3. **`docs/proxima-sessao.md`** — Pontos de entrada específicos ("quero atualizar o APK", "preciso de rollback", etc.).

O MAPA cobre 90% das perguntas; os outros dois complementam quando precisa de narrativa de descoberta ou passo-a-passo detalhado.

## O que foi feito (resumo técnico)

- APK `AutoOk.apk` em `/system/app/AutoOk.apk` — monitora logcat, detecta Activity do Aviso, dispara `su -c "input tap 400 350"`.
- `su` ARM setuid em `/system/xbin/su` (do root-honda, mode 06755) — root permanente.
- Deploy via **EvilValet**: pacote OTA `SwUpdate.mdt` assinado com testkey AOSP, aceito pela recovery da nossa safra `1.F187.16` BR, rom_type `0040`.
- Zero modificação em arquivos preexistentes do /system. Nenhum risco de brick realizado.

## Credenciais técnicas rápidas

| Campo | Valor |
|---|---|
| DA version | `1.F187.16` |
| Rom type (EvilValet key) | `0040` |
| Device | `vcm30t30` (NVIDIA Tegra 3) |
| Android | 4.2.2 API 17 |
| Combo cold boot | **`AUDIO 5s`** + confirmar reiniciar |
| Botão OK do Aviso | X=400, Y=350 (tela 800×480) |
| Activity do Aviso | `com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity` |
| Testkey SHA-256 | `A4:0D:A8:0A:59:D1:70:CA:A9:50:CF:15:C1:8C:45:4D:47:A3:9B:26:98:9D:8B:64:0E:CD:74:5B:A7:1B:F5:DC` |

## Base de conhecimento histórica

O `central-multimidia-civic-g10-kb.md` **tem o histórico de descoberta** (pesquisa, hipóteses, análise estática) feito ao longo das 7 fases do projeto. Preservado como contexto histórico, mas **não é mais o ponto de entrada**. Para trabalho prático novo, começar pelos docs da Fase 7.

## Como ajudar o dono do projeto

1. **Antes de qualquer modificação do /system do carro:** garantir que o pacote de rollback (`tooling/ota-build/output-rollback/`) está construído e pronto. Rede de segurança obrigatória.

2. **Nunca editar código em `tooling/references/*` diretamente.** São clones de projetos de terceiros. Usar monkey patch em `tooling/ota-build/`.

3. **Prefira análise estática no PC.** Dumps completos de /system em `tooling/apks-dumped/dump-0040/`. 197MB cobrindo /system/app, /system/vendor/app, /system/framework (parcial), /system/etc, build.props.

4. **Para novas descobertas:** adicionar em `docs/fase7-deploy-2026-10-16/02-descobertas-tecnicas.md` ou criar `fase8-*` se mudança for grande.

5. **Para modificações do APK:** rebuild via `our-apk/`, resign com apksigner, copiar pro overlay, rebuild OTA via `python3 tooling/ota-build/build.py`. Detalhes em `docs/fase7-deploy-2026-10-16/05-manutencao-e-futuro.md § Rebuild + redeploy do APK`.

## Idioma

O dono fala **português do Brasil**. Prefira respostas nessa língua.
Trechos técnicos (comandos, flags, nomes de pacotes) podem ficar em inglês.

## Convenções

- **Zero comentários no código** (regra do dono — ver `~/.claude/CLAUDE.md`)
- Documentação em Markdown
- Commits em português no imperativo

## Links úteis

- Repositório (privado): https://github.com/khalleb/honda-civic-headunit
- **Documentação do deploy final:** [`./docs/fase7-deploy-2026-10-16/`](docs/fase7-deploy-2026-10-16/)
- **Ponto de partida de nova sessão:** [`./docs/proxima-sessao.md`](docs/proxima-sessao.md)
- Base de conhecimento histórica: [`./central-multimidia-civic-g10-kb.md`](central-multimidia-civic-g10-kb.md)
- Pesquisa das rotas sem-ADB: [`./docs/pesquisa-rotas-sem-adb-2026-10-15.md`](docs/pesquisa-rotas-sem-adb-2026-10-15.md)
- Setup para Linux: [`./MIGRATION/setup.sh`](MIGRATION/setup.sh)
- Disclaimer: [`./DISCLAIMER.md`](DISCLAIMER.md)
- Referências de terceiros (clonadas por `setup.sh`):
  - https://github.com/codeage/root-honda — `su` + SuperSU + whitelist Mitsubishi
  - https://github.com/jersacct/2016PilotOneClick — rooteador de Honda Pilot 2016
  - https://github.com/librick/ic1101 — pesquisa RE completa + `ota-builder` (base do nosso build)
