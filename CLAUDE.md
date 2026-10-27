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

1. **`docs/MAPA.md`** ⭐ — **Atlas navegável da central** (reflexo do estado real: partições, APKs, services, nossas modificações, hall of fame de bugs). Primeira consulta sempre.
2. **`docs/fase7-deploy-2026-10-16/README.md`** — Documentação do deploy final.
3. **`docs/proxima-sessao.md`** — Pontos de entrada específicos ("quero atualizar o APK", "preciso de rollback", etc.).

O MAPA cobre 90% das perguntas; os outros dois complementam quando precisa de narrativa de descoberta ou passo-a-passo detalhado.

### 🔴 REGRA DE OURO — SEMPRE ATUALIZAR O MAPA

**Tudo de importante que for descoberto, decidido ou aprendido sobre a central vai para `docs/MAPA.md`. Sem exceção.** Isso inclui novos nomes de Activity/Service/Receiver/Broadcast, novos arquivos/partições relevantes, novas modificações nossas, novos bugs corrigidos (com causa raiz), novas rotas de deploy, novos backups.

Antes de encerrar qualquer análise, mudança no APK, ou investigação de bug: **atualizar o MAPA é obrigatório** (seção §0 do próprio MAPA tem a tabela de onde registrar cada tipo de descoberta).

O MAPA deve ser mais fiel que a memória da sessão. Quando em dúvida entre "vale salvar?" vs "é trivial", sempre salve.

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
| Activity da câmera de ré | `com.mitsubishielectric.ada.app.camera/.activity.RearWideCameraDisplayActivity` |
| Broadcast crítico (recovery LP0) | `com.mitsubishielectric.ada.appservice.powermanager.ACTION_HMI_SERVICE_START` |
| Versão atual do APK | 9 (v0.5.4 — fix do mudo CarPlay + LP0 resume; baseline estável) |
| Testkey SHA-256 | `A4:0D:A8:0A:59:D1:70:CA:A9:50:CF:15:C1:8C:45:4D:47:A3:9B:26:98:9D:8B:64:0E:CD:74:5B:A7:1B:F5:DC` |

## Base de conhecimento histórica

O `central-multimidia-civic-g10-kb.md` **tem o histórico de descoberta** (pesquisa, hipóteses, análise estática) feito ao longo das 7 fases do projeto. Preservado como contexto histórico, mas **não é mais o ponto de entrada**. Para trabalho prático novo, começar pelos docs da Fase 7.

## Como ajudar o dono do projeto

1. **Antes de qualquer modificação do /system do carro:** garantir que o pacote de rollback está construído e pronto. Rede de segurança obrigatória. **Existem dois "rollback" diferentes — não confundir:**
   - `tooling/ota-build/output-rollback/` — rollback do **AutoOk**: remove `AutoOk.apk` + `su`. É o que os `prepare-pendrive-rollback.sh` sem argumento geram.
   - `tooling/ota-build/output-dalauncher-restore/` — restore do **DaLauncher** original (Fase 10): desfaz o patch do disclaimer. Precisa ser passado explicitamente: `prepare-pendrive-rollback.sh /dev/sdX tooling/ota-build/output-dalauncher-restore`. Para abortar a Fase 10 é **este**, não o do AutoOk.

2. **Nunca editar código em `tooling/references/*` diretamente.** São clones de projetos de terceiros. Usar monkey patch em `tooling/ota-build/`.

3. **Prefira análise estática no PC.** Dumps completos de /system em `tooling/apks-dumped/dump-0040/`. 197MB cobrindo /system/app, /system/vendor/app, /system/framework (parcial), /system/etc, build.props.

4. **Para novas descobertas:** adicionar em `docs/fase7-deploy-2026-10-16/02-descobertas-tecnicas.md` ou criar `fase8-*` se mudança for grande.

5. **Para modificações do APK:** rebuild via `our-apk/`, resign com apksigner, copiar pro overlay, rebuild OTA via `python3 tooling/ota-build/build.py`. Detalhes em `docs/fase7-deploy-2026-10-16/05-manutencao-e-futuro.md § Rebuild + redeploy do APK`.

## Idioma

O dono fala **português do Brasil**. Prefira respostas nessa língua.
Trechos técnicos (comandos, flags, nomes de pacotes) podem ficar em inglês.

## Convenções

- **Comentários no código são permitidos neste projeto** (liberado pelo dono em 2026-10-26). A regra global de zero comentários (`~/.claude/CLAUDE.md`) é do code review da Sittax e não vale aqui. Comentário explica o porquê, a invariante ou o workaround; não narra o que a linha faz.
- Documentação em Markdown
- Commits em português no imperativo
- **Testes obrigatórios para código com lógica** (ver abaixo)

## Testes obrigatórios

Regra do dono, a partir de 2026-10-24. Código com lógica de runtime **não entra sem teste**; o resto entra com **prova executável**. Teste decorativo não conta — vale a régua do `/review-khalleb`: se nenhuma mudança na lógica deixa o teste vermelho, ele documenta, não prova.

- **Código com lógica de runtime → teste unitário obrigatório.**
  - `our-apk/` (AutoOk): a lógica pura (match do needle do logcat, dedup temporal, decisão de tap) sai das bordas Android e é testada em JVM/JUnit, sem device nem emulador. É onde moram os bugs reais — ex.: a saga v0.5.0→v0.5.4 (needle frouxo, dedup, formato de logcat) seria pega aqui antes de ir ao carro.
  - `tooling/**/*.py` (geradores de pacote OTA): pytest que asserta as invariantes do artefato gerado — loop-break presente (`mv SwUpdate2.txt` + `rm /cache/.copy_complete`), nada que aborte o updater-script (falha dentro do recovery deixa o comando estagiado e vira recovery loop — por isso não há device-guard): nenhum `assert(`/`abort(`, e `set_perm` só em `/tmp`, porque no `update-binary` empacotado ele aborta quando o chown/chmod falha; em `/system`, `chown`/`chmod` do busybox via `run_program` (exceção conhecida: `build.py`, MAPA §17.18), gate do `rm` do `.odex`, paths caindo nas partições certas.
- **RE / smali / análise estática / docs → não força unit test**, mas **exige prova executável** sempre que produz um artefato (patch smali, pacote OTA, APK rebuildado). Ex.: `tooling/fase10/rebuild-dalauncher.sh` prova que só `OpeningDivideActivity` muda no bytecode entre orig e patch.
- **Shell com decisão** (ex.: `tooling/scripts/lib-pendrive.sh`: escolha do build, confirmação, limpeza, conferência de SHA-256) → funções isoladas e a sequência inteira testadas chamando `bash` a partir do unittest (`tooling/ota-build/tests/test_prepare_pendrive.py`), com stub no lugar do que exige root ou pendrive.
- **Shell de orquestração** (sem lógica testável) → a prova é o próprio artefato que ele gera, verificado no fim do script.

Rodar os testes de tooling (stdlib, sem dependências): `python3 -m unittest discover -s tooling/ota-build/tests`. O CI (`.github/workflows/ci.yml`, job `unit-tests`) roda a mesma suíte.

## Links úteis

- Repositório (público): https://github.com/khalleb/honda-civic-headunit
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
