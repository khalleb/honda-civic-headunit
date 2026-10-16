---
name: "🚗 Nova safra Honda / New Honda firmware"
about: Reportar dados de uma safra Honda G10 diferente / Report a different Honda G10 firmware
title: "[SAFRA] <marca> <modelo> <ano> — <DA_VERSION>"
labels: safra-nova
assignees: ''
---

🇧🇷 Preencha os campos abaixo para ajudar a construir uma matriz de compatibilidade.
🇺🇸 Fill in the fields below to help build a compatibility matrix.

## Dados do veículo / Vehicle data

- **Marca / Make:**
- **Modelo / Model:**
- **Ano / Year:**
- **Trim / Trim level:**
- **Mercado / Market:** (BR / US / EU / JP / AU / outros)
- **Prefixo do VIN / VIN prefix (3 primeiros chars):**

## Dados da central / Head unit data

Como descobrir estes campos: [`docs/pt-BR/03-descobrindo-sua-safra.md`](../../docs/pt-BR/03-descobrindo-sua-safra.md)
How to find these: see Portuguese doc, or follow the dump procedure.

- **DA version (`ro.build.id`):**
- **Rom type (`custom_rom.type`):**
- **Device (`ro.product.device`):**
- **Model (`ro.product.model`):**
- **Build tags (`ro.build.tags`):**
- **Resolução da tela (Display resolution, ex: 800×480):**
- **Combo pra cold boot da central (que forçou "Quer reiniciar?"):** (ex: AUDIO 5s)

## Status do deploy

- [ ] Nunca tentei — só reportando dados / Haven't tried yet — just reporting data
- [ ] Tentei, deu erro — detalhes abaixo / Tried, failed — details below
- [ ] Tentei, funcionou! / Tried, works!

## Detalhes adicionais / Additional details

Qualquer informação relevante: logs, screenshots, nome da Activity do Aviso, coordenadas do botão OK (se diferente de 400,350), etc.

Any relevant info: logs, screenshots, Warning Activity name, OK button coordinates (if different from 400,350), etc.

```
cole aqui / paste here
```

## Autorização para contribuir

- [ ] Autorizo que esses dados sejam agregados à matriz pública de compatibilidade / I authorize this data to be added to the public compatibility matrix
