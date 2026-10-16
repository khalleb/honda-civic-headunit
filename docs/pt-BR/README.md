# 🇧🇷 Documentação em Português

Documentação prática para usar/adaptar o projeto. Para quem só quer deployar na própria central.

## Índice

| Doc | Descrição | Status |
|---|---|---|
| [`00-visao-geral.md`](00-visao-geral.md) | O que o projeto faz e por quê | ✅ |
| [`01-arquitetura-ataque.md`](01-arquitetura-ataque.md) | Como EvilValet funciona (ver [fase7/03](../fase7-deploy-2026-10-16/03-build-ota-receita.md)) | ↪ |
| [`02-pre-requisitos.md`](02-pre-requisitos.md) | Ferramentas, hardware (ver [QUICKSTART](../../QUICKSTART.md) § Pré-requisitos) | ↪ |
| [`03-descobrindo-sua-safra.md`](03-descobrindo-sua-safra.md) | Como adaptar pra outras safras | ✅ |
| [`04-build-do-pacote.md`](04-build-do-pacote.md) | Compilar o pacote OTA (ver [fase7/03](../fase7-deploy-2026-10-16/03-build-ota-receita.md)) | ↪ |
| [`05-deploy-no-carro.md`](05-deploy-no-carro.md) | Protocolo no carro (ver [QUICKSTART § 6](../../QUICKSTART.md#-6-deploy-no-carro)) | ↪ |
| [`06-troubleshooting.md`](06-troubleshooting.md) | Debug (ver [fase7/05 § Troubleshooting](../fase7-deploy-2026-10-16/05-manutencao-e-futuro.md#troubleshooting)) | ↪ |
| [`07-rollback.md`](07-rollback.md) | Reverter tudo | ✅ |
| [`08-backups-e-rollback.md`](08-backups-e-rollback.md) | Catálogo completo de backups + script `verificar-backups.sh` | ✅ |

Legenda:
- ✅ = doc nesta pasta
- ↪ = atalho para doc existente na pasta `fase7-deploy-2026-10-16/`

## Caminho recomendado

### Se é seu primeiro contato com o projeto:

1. [`00-visao-geral.md`](00-visao-geral.md) — contexto
2. [`DISCLAIMER.md`](../../DISCLAIMER.md) — leia os riscos
3. Se safra `1.F187.16` BR: siga [`QUICKSTART.md`](../../QUICKSTART.md)
4. Se outra safra: [`03-descobrindo-sua-safra.md`](03-descobrindo-sua-safra.md)

### Se já deployou e algo deu errado:

1. [`06-troubleshooting.md`](06-troubleshooting.md) (atalho para [`fase7/05 § Troubleshooting`](../fase7-deploy-2026-10-16/05-manutencao-e-futuro.md#troubleshooting))
2. Se nada ajudar, [`07-rollback.md`](07-rollback.md)
3. Abra uma issue com template de bug

### Se é pesquisador / quer entender a fundo:

1. [`00-visao-geral.md`](00-visao-geral.md)
2. [`../fase7-deploy-2026-10-16/01-jornada-completa.md`](../fase7-deploy-2026-10-16/01-jornada-completa.md) — narrativa da descoberta
3. [`../fase7-deploy-2026-10-16/02-descobertas-tecnicas.md`](../fase7-deploy-2026-10-16/02-descobertas-tecnicas.md) — ficha técnica
4. [`../fase7-deploy-2026-10-16/`](../fase7-deploy-2026-10-16/) — resto dos docs

## Documentação em outros idiomas

- 🇺🇸 English: [`../en/`](../en/) (resumo, precisa de tradução completa)

Quer traduzir pra outra língua? [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
