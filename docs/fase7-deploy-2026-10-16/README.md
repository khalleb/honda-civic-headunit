# Fase 7 — Deploy final (2026-10-16)

Documento-índice da sessão em que o projeto foi concluído com sucesso: APK auto-OK instalado em `/system/app`, `su` setuid em `/system/xbin`, central Civic 2017 BR com Aviso suprimido automaticamente em cada ligar do carro.

## Resultado

Objetivo primário do projeto atingido. A tela de "Aviso" (`O motorista é o responsável pela condução segura...`) aparece por ~10 segundos em cada boot da central e some sozinha. Zero interação manual necessária após o deploy. CarPlay, Bluetooth, Áudio, Navegação — tudo preservado.

## Como chegamos aqui

Sem ADB (porta USB da central não enumera sem dev mode, dev mode bloqueado por passcord). Sem Honda Hack (produto pago US$ 25, descartado por decisão do dono). Sem precisar de cabo USB-A/A ou JTAG.

A rota foi **EvilValet** — descuido sistemático do pipeline de build Mitsubishi Andromeda: o recovery da central Honda aceita qualquer `SwUpdate.mdt` assinado com a `testkey.pk8` pública do AOSP. Isso dá execução arbitrária root no HU via um simples pendrive na porta USB-A frontal — se e somente se o pacote estiver com o `custom_rom.type` certo e seguir uma receita específica de formato.

**Fontes:**
- **Anúncio público do ataque** (nomenclatura, cenário "evil maid veicular"): [juniperspring.org/posts/honda-evil-valet](https://juniperspring.org/posts/honda-evil-valet/) por librick / Eric McDonald, 2026-06-13. **Esse post é anúncio** — o próprio autor avisa que não é writeup técnico.
- **Fonte primária técnica** (fluxo do daupdater, formato do pacote, checklist): `tooling/references/ic1101/docs/updates.md` do mesmo autor. **Esse foi o documento que seguimos linha a linha.**

Confirmações públicas antes da nossa: Civic 2021 US + um update file EU público. **Esta fase é a primeira confirmação pública em safra brasileira (`1.F187.16`), com o rom_type `0040` descoberto e documentado por nós.**

Essa fase refina EvilValet para a safra brasileira + instala nosso próprio APK + habilita root permanente — tudo numa única passagem OTA.

## Documentos nesta pasta

1. **[01-jornada-completa.md](01-jornada-completa.md)** — narrativa cronológica das 24h da descoberta: do primeiro build com rom_type errado até o `tap 400,350 -> true` confirmado nos logs.

2. **[02-descobertas-tecnicas.md](02-descobertas-tecnicas.md)** — ficha técnica consolidada da safra `1.F187.16` BR. Tudo que descobrimos: build.props, partições, lista completa de 50+ APKs vendor, framework, hardware, kernel, combos físicos. Base de referência para qualquer trabalho futuro na mesma central.

3. **[03-build-ota-receita.md](03-build-ota-receita.md)** — receita completa de como construir um pacote OTA (install + rollback). Como o `build.py` monkey-patcha o `ic1101/ota-builder`, como o `busybox` é embarcado, como o `su` é instalado com setuid, como o updater-script monta `/system` rw via edify. Com código.

4. **[04-apk-autook-detalhes.md](04-apk-autook-detalhes.md)** — tudo sobre o `AutoOk.apk`: arquitetura (BootReceiver → Service → LogcatWatcher → Shell), bug do D8 que forçou refactor pra named inner classes, o needle `/.OpeningDivideActivity` que precisa ter barra-ponto, por que `stopSelf()` quebrava persistência, por que o Service não morre nunca mais.

5. **[05-manutencao-e-futuro.md](05-manutencao-e-futuro.md)** — operação do dia-a-dia. Como atualizar o APK no futuro, como fazer rollback de emergência, troubleshooting quando algo não funciona, roadmap de melhorias futuras (reduzir delay, SuperSU opcional, remover Aviso de verdade modificando DaLauncher).

6. **[06-dumps-obtidos.md](06-dumps-obtidos.md)** — catálogo dos 197MB de dumps extraídos de `/system` sem ADB. O que está em cada pasta, como foi coletado, como re-coletar se precisar.

## Pontos de entrada em caso de voltar ao projeto

- **"Quero atualizar o APK"** → [05-manutencao-e-futuro.md § Rebuild + redeploy do APK](05-manutencao-e-futuro.md#rebuild--redeploy-do-apk)
- **"O APK parou de funcionar"** → [05-manutencao-e-futuro.md § Troubleshooting](05-manutencao-e-futuro.md#troubleshooting)
- **"Preciso remover tudo que fiz"** → [05-manutencao-e-futuro.md § Rollback completo](05-manutencao-e-futuro.md#rollback-completo)
- **"A Honda atualizou a central e o APK sumiu"** → [05-manutencao-e-futuro.md § Após atualização OTA Honda](05-manutencao-e-futuro.md#após-atualização-ota-honda)
- **"Quero entender como EvilValet funciona"** → [03-build-ota-receita.md § Fundamentos EvilValet](03-build-ota-receita.md#fundamentos-evilvalet)
- **"Quero dados técnicos da central"** → [02-descobertas-tecnicas.md](02-descobertas-tecnicas.md)

## Credenciais técnicas finais

| Campo | Valor |
|---|---|
| Central | Honda Civic 2017 EXL BR, Display Audio 7" Mitsubishi Andromeda |
| DA version | `1.F187.16` (release-keys, build 2016-04-07) |
| Rom type | `0040` |
| Device | `vcm30t30` (NVIDIA Tegra 3) |
| Android | 4.2.2 API 17 |
| Car model code | `TBAA` |
| Serial | `<serial-redactado>` |
| APK deployed | `/system/app/AutoOk.apk` SHA-1 `e76d35741c5fafb8289f97f9565aaf8e1bff4f66` |
| su deployed | `/system/xbin/su` mode `06755` (setuid) |

Deploy final: 2026-10-16 ~10:55 BRT.
