# 🇧🇷 Documentação em Português

Documentação prática para usar/adaptar o projeto. Para quem só quer deployar na própria central.

## Índice

| Doc | Descrição |
|---|---|
| [`00-visao-geral.md`](00-visao-geral.md) | O que o projeto faz e por quê |
| [`01-arquitetura-ataque.md`](01-arquitetura-ataque.md) | Como o ataque EvilValet funciona |
| [`02-pre-requisitos.md`](02-pre-requisitos.md) | Hardware, software, keystore |
| [`03-descobrindo-sua-safra.md`](03-descobrindo-sua-safra.md) | Como adaptar pra outras safras |
| [`04-build-do-pacote.md`](04-build-do-pacote.md) | Compilar o pacote OTA passo a passo |
| [`05-deploy-no-carro.md`](05-deploy-no-carro.md) | Protocolo no carro |
| [`06-troubleshooting.md`](06-troubleshooting.md) | Decision tree pra quando algo falha |
| [`07-rollback.md`](07-rollback.md) | Reverter tudo |
| [`08-backups-e-rollback.md`](08-backups-e-rollback.md) | Catálogo completo de backups |

## Caminho recomendado

### Se é seu primeiro contato com o projeto

1. [`00-visao-geral.md`](00-visao-geral.md) — contexto
2. [`DISCLAIMER.md`](../../DISCLAIMER.md) — leia os riscos
3. Se safra `1.F187.16` BR: siga [`QUICKSTART.md`](../../QUICKSTART.md)
4. Se outra safra: [`03-descobrindo-sua-safra.md`](03-descobrindo-sua-safra.md)

### Se quer entender o ataque antes de aplicar

1. [`00-visao-geral.md`](00-visao-geral.md)
2. [`01-arquitetura-ataque.md`](01-arquitetura-ataque.md) — como EvilValet funciona
3. [`02-pre-requisitos.md`](02-pre-requisitos.md) — tudo que precisa ter
4. [`04-build-do-pacote.md`](04-build-do-pacote.md) + [`05-deploy-no-carro.md`](05-deploy-no-carro.md) — execução

### Se já deployou e algo deu errado

1. [`06-troubleshooting.md`](06-troubleshooting.md) — decision tree completa
2. Se nada ajudar: [`07-rollback.md`](07-rollback.md) — reverter tudo
3. Abra uma [issue](../../.github/ISSUE_TEMPLATE/) com log do APK + logs do deploy

### Se é pesquisador / quer entender a fundo

1. [`00-visao-geral.md`](00-visao-geral.md) — resumo
2. [`../MAPA.md`](../MAPA.md) — atlas navegável da central (partições, APKs, binários)
3. [`../fase7-deploy-2026-10-16/01-jornada-completa.md`](../fase7-deploy-2026-10-16/01-jornada-completa.md) — narrativa da descoberta
4. [`../fase7-deploy-2026-10-16/02-descobertas-tecnicas.md`](../fase7-deploy-2026-10-16/02-descobertas-tecnicas.md) — ficha técnica
5. [`../fase7-deploy-2026-10-16/`](../fase7-deploy-2026-10-16/) — resto dos docs técnicos

## Documentação em outros idiomas

- 🇺🇸 English: [`../en/`](../en/) — documentação completa traduzida

Quer traduzir pra outra língua? Fork + PR com `docs/<lang>/` nova. Veja [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
