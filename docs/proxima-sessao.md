# Próxima sessão — projeto concluído

**Projeto encerrado em 2026-10-16 com sucesso.** Aviso de partida da central Civic 2017 EXL BR
(`1.F187.16`, Mitsubishi Andromeda, Android 4.2.2) é suprimido automaticamente em cada ligar do
carro — zero interação manual.

Este documento é agora um **ponto de entrada histórico**. Se você está retomando o projeto depois
de meses, aqui estão os pontos de partida.

## O que foi feito

- APK `AutoOk.apk` em `/system/app/` — monitora logcat, detecta Activity do Aviso, dispara tap
  programático via `su -c "input tap 400 350"`.
- Binário `su` ARM setuid em `/system/xbin/` — dá root permanente à central.
- Deploy via EvilValet: pacote OTA `SwUpdate.mdt` assinado com testkey AOSP, aceito pela recovery
  da nossa safra.

## Documentação completa

Pasta: **[`fase7-deploy-2026-10-16/`](fase7-deploy-2026-10-16/)**

Arquivos nessa pasta:

| Arquivo | Conteúdo |
|---|---|
| `README.md` | Índice da fase + pontos de entrada rápidos |
| `01-jornada-completa.md` | Narrativa cronológica das 24h de descoberta |
| `02-descobertas-tecnicas.md` | Ficha técnica consolidada da safra BR |
| `03-build-ota-receita.md` | Como construir pacote OTA (install + rollback) |
| `04-apk-autook-detalhes.md` | Arquitetura, bugs, decisões do APK |
| `05-manutencao-e-futuro.md` | Como atualizar APK, troubleshooting, rollback, roadmap |
| `06-dumps-obtidos.md` | Catálogo dos 197MB de dumps obtidos |

## Perguntas frequentes de retomada

### "Quero atualizar o APK (mudar coord, mudar activity, mudar delay)"

→ [`fase7-deploy-2026-10-16/05-manutencao-e-futuro.md § Rebuild + redeploy do APK`](fase7-deploy-2026-10-16/05-manutencao-e-futuro.md#rebuild--redeploy-do-apk)

### "APK parou de funcionar"

→ [`fase7-deploy-2026-10-16/05-manutencao-e-futuro.md § Troubleshooting`](fase7-deploy-2026-10-16/05-manutencao-e-futuro.md#troubleshooting)

### "Preciso remover tudo que fiz"

→ [`fase7-deploy-2026-10-16/05-manutencao-e-futuro.md § Rollback completo`](fase7-deploy-2026-10-16/05-manutencao-e-futuro.md#rollback-completo)

### "A Honda atualizou a central e o APK sumiu"

→ [`fase7-deploy-2026-10-16/05-manutencao-e-futuro.md § Após atualização OTA Honda`](fase7-deploy-2026-10-16/05-manutencao-e-futuro.md#após-atualização-ota-honda)

### "Preciso entender como EvilValet funciona na nossa safra"

→ [`fase7-deploy-2026-10-16/03-build-ota-receita.md § Fundamentos EvilValet`](fase7-deploy-2026-10-16/03-build-ota-receita.md#fundamentos-evilvalet)

### "Preciso dos dados técnicos da central (build.props, partições, etc.)"

→ [`fase7-deploy-2026-10-16/02-descobertas-tecnicas.md`](fase7-deploy-2026-10-16/02-descobertas-tecnicas.md)

### "Quero fazer um dump atualizado do /system (depois de update, por exemplo)"

→ [`fase7-deploy-2026-10-16/06-dumps-obtidos.md § Como re-dumpar`](fase7-deploy-2026-10-16/06-dumps-obtidos.md#como-re-dumpar)

## Credenciais técnicas finais (sumário)

Para referência rápida:

| Campo | Valor |
|---|---|
| Rom type (chave do EvilValet) | `0040` |
| Device | `vcm30t30` (Tegra 3) |
| DA version | `1.F187.16` |
| Combo cold boot | `AUDIO 5s` + confirmar reiniciar |
| Botão OK do Aviso | X=400, Y=350 (tela 800×480) |
| Activity do Aviso | `com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity` |
| Partição /system | `/dev/block/platform/sdhci-tegra.3/by-name/APP` (= mmcblk0p3) |
| Testkey AOSP SHA-256 | `A4:0D:A8:0A:59:D1:70:CA:A9:50:CF:15:C1:8C:45:4D:47:A3:9B:26:98:9D:8B:64:0E:CD:74:5B:A7:1B:F5:DC` |

## Rede de segurança

Em caso de necessidade de rollback de emergência:

```
sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sdX
```

(Esse caminho é da sessão em que o script foi criado — se não existir mais, reconstruir via
`python3 tooling/ota-build/build-rollback.py` e carregar pendrive.)

## Fases anteriores do projeto

Preservadas em `docs/`:

- `fase1-reconhecimento/` — primeiro reconhecimento da central (2026-10 pré-Fase 7)
- `fase3-adb/` — tentativas (infrutíferas) de habilitar ADB via passcord
- `fase4-analise-estatica/` — análise do HondaHack.apk e framework Mitsubishi
- `fase5-apk/` — build do APK auto-OK (compilação, assinatura)
- `pesquisa-rotas-sem-adb-2026-10-15.md` — varredura das 8 rotas alternativas avaliadas antes da Fase 7
- `fase7-deploy-2026-10-16/` — ← **esta pasta, deploy final**

## Trabalhos abertos / melhorias futuras possíveis

Ver [`fase7-deploy-2026-10-16/05-manutencao-e-futuro.md § Roadmap futuro`](fase7-deploy-2026-10-16/05-manutencao-e-futuro.md#roadmap-futuro). Resumo:

**Baixo risco:**
- Reduzir delay do tap de ~10s para ~3s
- Logs persistentes do APK em `/sdcard/`
- Watchdog self-check do Service
- Multi-coord fallback

**Médio risco:**
- Modificar `DaLauncher.apk` para pular `DisclaimerFragment` por completo
- Instalar SuperSU opcional
- Xposed Framework

**Alto risco:**
- Modificar framework
- Firmware mod customizado

**Features bônus:**
- Script zero-config pra outros donos de Civic 2017 BR
- Interface web pra configuração
- Rollback automatizado por combo físico
