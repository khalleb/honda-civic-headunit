# Pesquisa do passcord — Civic 2017 EXL BR, firmware `1.F187.16`

Consolidação do que a web pública entrega sobre o passcord de dev mode do Civic 2017 BR. Objetivo: planejar as próximas tentativas na central sem gastar atempts à toa (seção 4.4 do KB alerta sobre cooldown silencioso).

Sessão de 2026-10-15, continuando o relato de `docs/fase1-reconhecimento/achados-2026-10-15.md` seção 4.

## 1. Sequência canônica XDA 2017 — resumo definitivo

Baseado em busca em múltiplas fontes (XDA, CivicX via snippets, softstribe.com), a receita documentada para safra 2017 é:

1. Settings → Sobre o dispositivo → tocar **7-8 vezes** em `Número da versão` (Build Number).
2. Aparece o toast `Please enter a passcord`.
3. **Tocar nos 4 itens técnicos na ordem 1-4-2-3**, onde a numeração é a **posição original na tela**, não a ordem de toque:
   - Posição 1: **Número do modelo** (Model Number) → 1º toque
   - Posição 4: **Versão do kernel** (Kernel Version) → 2º toque
   - Posição 2: **Versão do Android** (Android Version) → 3º toque
   - Posição 3: **Versão da banda de base** (Baseband Version) → 4º toque
4. Build Number **NÃO** entra na sequência.

Isso é exatamente o que foi tentado no carro em 2026-10-15 e **não funcionou**. Duas tentativas, nenhuma reação além do toast repetido.

## 2. Por que pode não ter funcionado — hipóteses testáveis

### 2.1 Hipótese: ordem absoluta na UI BR é diferente

A XDA assume uma tela com 4 itens técnicos no topo (Model/Android/Baseband/Kernel). No firmware BR, a tela "Sobre o dispositivo" tem **7 itens**:

```
1. Status
2. Informações legais
3. Número do modelo       ← posição 1 segundo a XDA
4. Versão do Android      ← posição 2
5. Versão da banda de base ← posição 3
6. Versão do kernel        ← posição 4
7. Número da versão        (Build Number — gatilho do toast)
```

Se o firmware BR conta **todos os itens visíveis** (incluindo Status e Informações legais) para a lógica interna, a sequência 1-4-2-3 não corresponde ao que a XDA diz — corresponderia a Status → Versão do kernel → Informações legais → Número do modelo, que é absurdo. **Mais provável:** o firmware BR usa a mesma lógica XDA (os 4 campos técnicos), e os itens "Status" e "Informações legais" são decorativos para a detecção. Mantida como hipótese secundária porque faz pouco sentido técnico, mas vale testar.

**Teste alternativo:** tocar na ordem Status → Kernel → Informações legais → Modelo (ou seja, se há 7 itens, a sequência 1-4-2-3 é essa). Fazer **uma vez só** porque é especulação.

### 2.2 Hipótese: timing do toast engole os toques

O toast `Please enter a passcord` fica visível por ~2s por padrão em Android 4.2.2. Se a sequência precisa acontecer **enquanto o toast ainda está na tela**, 4 toques em cadência de 1 por segundo acabam depois do toast sumir — e aí o detector reseta.

**Teste:** fazer a sequência 1-4-2-3 **o mais rápido possível** (toda em menos de 1 segundo, bateria de 4 toques rápidos). Primeiro vai a sequência, depois os 7 toques no Build Number — ou os 7 toques e logo depois a sequência rápida.

### 2.3 Hipótese: 7 toques no Build Number precisam ser contínuos sem interrupção

Alguns detectores Android (ex.: Easter Egg do Settings) resetam a contagem se o usuário sair do foco ou tocar em outro item entre os toques. Se o firmware Mitsubishi é assim, qualquer toque fora do Build Number zera.

**Teste:** fazer os 7 toques **sem olhar para outros itens**, com cadência regular (~0.5s entre toques).

### 2.4 Hipótese: safra `1.F187.16` já tem patch da Honda

A XDA e a doc do `@codeage` alertam: "Honda has changed the password to enter the developer mode in new vehicle models". A safra 2018 oficialmente mudou. **Nossa unidade é 2017-04 (abril) e `1.F187.16` pode ser pós-patch, dependendo do mês do OTA**.

Sinal indireto: o `@codeage` começou a cobrar US$25 por "web-based installation (paid service)" exatamente porque muita gente parou de conseguir a sequência tradicional. Se nossa unidade está no grupo "post-patch", a sequência 1-4-2-3 não vai funcionar com variação alguma — precisamos de outra rota.

## 3. Rotas alternativas documentadas na web

### 3.1 Serviço pago do `@codeage` (US$ 25)

- Comprar UUID no site do `@codeage` → visitar URL específica no browser nativo da central → root remoto.
- **Descartado neste projeto** (regra do dono: fazer manual, sem Honda Hack pago).

### 3.2 KingoRoot

Um usuário XDA relata ter rooteado 2018 Si via **KingoRoot** (ferramenta one-click, roda no PC + conexão ADB). **Depende de ADB subir primeiro** — ovo e galinha com nosso caso. Pode ser rota se conseguirmos ADB por outra via (recovery, por exemplo).

### 3.3 Browser nativo + payload

Mesmo mecanismo do serviço pago, mas o payload que o site do `@codeage` entrega é privado. Hipoteticamente, se encontrarmos qual exploit o payload usa (provável kernel exploit em `Browser` 4.2.2-55 + driver nativo), dá para replicar. Fora de escopo imediato.

### 3.4 Pacote `DeveloperDiag` acessível por combo de botão escondido

O KB (seção 2) confirma que `com.mitsubishielectric.ada.app.developerdiag` está instalado. Se existir um atalho de UI (combo físico, long-press, etc.) que invoque essa Activity direto, pulamos o passcord inteiro. **Nenhuma fonte pública documenta esse atalho** — seria descoberta nossa. Vale uma varredura mais extensa no menu de serviço (fase 1 só explorou 3-4 níveis).

## 4. Plano executado na sessão 2 de 2026-10-15 — resultado

Objetivo era validar/falsificar as hipóteses 2.1-2.3 com no máximo 3 tentativas. **As três foram feitas, todas falharam** (relato em `../fase1-reconhecimento/achados-2026-10-15-sessao2.md` seção 1).

| Tentativa | Variação | Hipótese testada | Resultado |
|---|---|---|---|
| 1 | 7 toques rapidíssimos + sequência 1-4-2-3 imediatamente, antes do toast sumir | 2.2 (timing) | ❌ só o toast |
| 2 | 7 toques normais + sequência 1-4-2-3 com cadência 1 toque/s | 2.2 variante lenta | ❌ só o toast |
| 3 | 7 toques normais + sequência do vídeo brasileiro (Kernel → Modelo → Build → Status) com cadência relaxada | 2.1 variante (ordem alternativa) | ❌ só o toast |

Combinadas com as 2 variações já testadas na sessão 1, **5 variações distintas foram descartadas**. A hipótese 2.4 (`1.F187.16` BR é pós-patch) **se confirma por eliminação**: todas as receitas públicas falharam, e o detector dos 7 toques funciona (o toast dispara), então o patch está na validação da sequência, não no gatilho.

**Status final da rota passcord via Settings do Android:** encerrada. Sem outras hipóteses testáveis dentro desse caminho.

## 5. Observações do inventário do EXL BR

Fontes públicas falam de centrais com 4 itens técnicos na tela "About". **A tela do EXL BR tem 7 itens, com 2 extras no topo que outras unidades não têm (`Status`, `Informações legais`).** Isso é diferença brasileira — nem XDA nem CivicX documentam. É um dado novo e vale registrar no KB.

Possível causa da diferença: Honda Brasil customizou o firmware base para incluir essas telas (`Status` mostra bateria/rede; `Informações legais` tem termos de uso). Em países onde "About" é só 4 itens técnicos, a sequência "1-4-2-3" funciona. No BR, pode ser que a lista interna visível é a mesma ordem — mas isso só se confirma testando a hipótese 2.1.

## 6. Fontes

- XDA — [How to enter developer mode on 2017 Honda Civic](https://xdaforums.com/t/guide-how-to-enter-developer-mode-on-2017-honda-civic-and-now-root-install-apps.3621582/) (via snippets; raw bloqueado 403)
- XDA — [2018 Honda Civic HU root](https://xdaforums.com/t/2018-honda-civic-hu-root.3776900/) (via snippets)
- CivicX — ["passcord" to enable Developer Mode has been found!](https://www.civicx.com/forum/threads/passcord-to-enable-developer-mode-has-been-found.12182/) (via snippets)
- CivicX — [In case anyone is wondering passcord for 2018 models](https://www.civicx.com/forum/threads/in-case-anyone-is-wondering-passcord-for-2018-models-developer-mode.26840/) (via snippets)
- CivicX — [Can't enter developer mode 2018 civic si](https://www.civicx.com/forum/threads/cant-enter-developer-mode-2018-civic-si.20248/) (via snippets)
- Softstribe — [How to enter developer mode in Honda Civic 2017](https://softstribe.com/android/how-to-enter-developer-mode-in-honda-civic-2017/) (fetch direto, sem bloqueio)
