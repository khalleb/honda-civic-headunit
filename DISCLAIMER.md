# ⚠️ Disclaimer — Leia antes de executar qualquer coisa

Este repositório documenta trabalho de engenharia reversa feito em caráter
**pessoal e educativo** no veículo próprio do autor. Qualquer coisa aqui é
usada **inteiramente por sua conta e risco**.

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
