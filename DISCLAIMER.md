# ⚠️ Disclaimer — Leia antes de executar qualquer coisa / Read before executing anything

🇧🇷 **Português** / 🇺🇸 [English below](#-english)

---

Este repositório documenta trabalho de engenharia reversa feito em caráter
**pessoal e educativo** no veículo próprio do autor. Qualquer coisa aqui é
usada **inteiramente por sua conta e risco**.

Ao usar este código ou documentação, você reconhece que:

1. Está modificando o firmware do seu próprio veículo.
2. Entende que isso pode brickar a central e você vai arcar com os custos de troca.
3. Pode perder garantia e cobertura de seguro.
4. Os autores do projeto NÃO se responsabilizam por nenhum dano causado.

## Riscos técnicos reais

### Brick da central
Modificar `/system` da central pode torná-la inoperante. Casos reportados
pela comunidade:
- **Soft brick** (boot loop, tela preta) — às vezes recuperável via recovery
- **Hard brick** (central sem sinais de vida) — exige **substituir o aparelho**
  (R$ 1.000 a 2.000 em mercado de usados, mais em concessionária)

### Perda da câmera de ré
A tela da central Honda também exibe a imagem da câmera de ré. Brick da
central = sem imagem de ré. Em alguns países e situações isso tem implicações
de segurança veicular.

### Reversão por update da concessionária
Qualquer modificação feita em `/system` **será desfeita** quando a Honda ou
uma concessionária aplicar um update oficial de software.

### Possíveis efeitos secundários
A central comunica-se com o CAN bus do veículo (F-CAN e B-CAN). Modificações
mal planejadas podem potencialmente afetar outros sistemas conectados a esses
barramentos. Não há evidência de que o escopo coberto neste repositório
cause isso, mas o risco teórico existe.

## Avisos legais

### Marcas e software proprietário
Honda®, Civic®, Mitsubishi®, Clarion®, Tegra® e outras marcas pertencem a
seus respectivos donos. Este projeto **não é afiliado, endossado ou
patrocinado** por nenhuma dessas empresas.

### Software referenciado
Alguns softwares de terceiros são referenciados (não incluídos) por serem
necessários para o aprendizado da plataforma — por exemplo o APK conhecido
como "Honda Hack" (`cn.autohack.hondahack`). Esse software pertence aos seus
autores originais e não é redistribuído por este repositório. Compradores
devem obter licença diretamente dos autores.

### Garantia do veículo
Modificar a central pode anular a garantia do rádio/navegação do veículo.
No Brasil, a garantia padrão Honda é de 3 anos — verifique a sua antes de
executar qualquer modificação.

### Jurisdição e tráfego
Algumas modificações populares em centrais Honda (ex.: habilitar vídeo com
o carro em movimento) podem **violar leis de trânsito** em diversos países.
Nada neste repositório é destinado a facilitar violações. Faça apenas o que
é permitido na sua jurisdição.

## Isenção de responsabilidade

> **O(s) autor(es) e contribuidor(es) deste repositório não assumem qualquer
> responsabilidade por danos — materiais, veiculares, pessoais ou de terceiros
> — decorrentes do uso das informações aqui contidas.**
>
> Toda informação é fornecida **"como está"**, sem garantia de qualquer tipo,
> expressa ou implícita, incluindo mas não se limitando a garantias de
> comerciabilidade, adequação a propósito específico e não infração.
>
> Se você não aceita esses termos, **não execute o conteúdo deste
> repositório**.

## Para quem este projeto não é

- ❌ Para quem não aceita o risco de perder a central do carro
- ❌ Para quem quer fazer isso em veículo que não é seu
- ❌ Para quem precisa do rádio funcionando sem interrupção (trabalho)
- ❌ Para quem não tem como pagar a eventual troca da central
- ❌ Para quem busca "fazer dinheiro" vendendo mods

## Para quem este projeto é

- ✅ Para quem está aprendendo RE em sistemas embarcados
- ✅ Para quem quer entender como centrais automotivas funcionam
- ✅ Para quem tem uma central de teste (ou aceita conscientemente o risco)
- ✅ Para contribuir com conhecimento aberto sobre a plataforma

---

## 🇺🇸 English

**⚠️ Read before executing anything.**

This repository documents reverse engineering work done for **personal and educational**
purposes on the author's own vehicle. Anything here is used **entirely at your own risk**.

By using this code or documentation, you acknowledge that:

1. You are modifying the firmware of your own vehicle.
2. You understand this can brick the head unit, and you will bear the replacement costs.
3. You may lose warranty and insurance coverage.
4. The project authors are NOT responsible for any damage caused.

### Known real risks

- **Permanent brick** of the head unit if done wrong. Replacement cost: R$ 1,000-2,000 (~USD 200-400) in Brazil.
- **The HU screen is the backup camera** — brick = no backup camera until replacement.
- **Honda OTA updates may revert** the modification.
- **May void warranty** (depending on jurisdiction and dealer).

### Compatibility

Only tested on Honda Civic 2017 EXL Brazil (`1.F187.16`). Other variants are speculation.
See [`docs/pt-BR/03-descobrindo-sua-safra.md`](docs/pt-BR/03-descobrindo-sua-safra.md) for how to
check your firmware before deploying.

### Legal

- Rooting your own vehicle is **legal in the US** under DMCA § 1201(f) (interoperability research exemption).
- Legal status varies by country. **Consult your local laws.**
- You retain all responsibility for consequences.

### No warranty

This project is provided "AS IS", without warranty of any kind. Use at your own risk.

See [LICENSE](LICENSE) (MIT) for full code license terms.
