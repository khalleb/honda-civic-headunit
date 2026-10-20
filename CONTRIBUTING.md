# Contribuindo / Contributing

🇧🇷 Obrigado pelo interesse em contribuir! · 🇺🇸 Thanks for your interest in contributing!

## Formas de contribuir / Ways to contribute

### 🚗 Reportar nova safra Honda / Report a new Honda firmware

**O MAIS VALIOSO.** Quanto mais safras documentadas, mais útil o projeto. Use o template [`nova-safra.md`](.github/ISSUE_TEMPLATE/nova-safra.md).

Mesmo que você não tenha tentado deployar — só os dados técnicos (DA version, rom_type, device, resolução, combo de cold boot) já ajudam a construir uma matriz de compatibilidade.

### 🐛 Bug reports

Template [`bug-report.md`](.github/ISSUE_TEMPLATE/bug-report.md). Logs são essenciais — sem logs, difícil debugar.

### 🌍 Tradução / Translation

- 🇧🇷 Portuguese: `docs/pt-BR/` (fonte original)
- 🇺🇸 English: `docs/en/` (resumo, precisa de tradução completa)
- 🇪🇸 Spanish? 🇯🇵 Japanese? 🇨🇳 Chinese? — abra PR com `docs/<lang>/`

Prioridade: **tradução completa para inglês** do `docs/pt-BR/`.

### 💡 Melhorias técnicas

Roadmap vivo: [`ROADMAP.md`](ROADMAP.md). Catálogo dos achados (plataforma mapeada, APIs AIDL, broadcasts, trust map) em [`DISCOVERIES.md`](DISCOVERIES.md).

Resumo dos candidatos atuais:

- Fase 9 — câmera de ré via `ICameraAPServiceReverseSignalListener` (sem logcat polling)
- Validar `DISCLAIMER_COMPLETE` como sinal canônico
- Dumpar `com.honda.displayaudio.whitelist.apk` real
- Testar `persist.sys.keyoff_reboot=1` como alternativa ao fluxo LP0

Caminhos descartados (com motivo) também vivem no ROADMAP — ler antes de propor para evitar reinventar.

### 📊 Dumps de outras safras

Se você tem acesso a HU com safra diferente, dump via o pacote de dump do nosso build. Instruções em [`docs/fase7-deploy-2026-10-16/06-dumps-obtidos.md § Como re-dumpar`](docs/fase7-deploy-2026-10-16/06-dumps-obtidos.md#como-re-dumpar).

**NÃO fazer upload dos dumps no repo** (firmware Honda é proprietário). Mas pode compartilhar extratos relevantes (strings, build.props) em issues.

## Padrões de código / Code standards

### Commits

- **Mensagens em português no imperativo**: "corrige X", "adiciona Y", "atualiza Z"
- Primeira linha ≤ 72 chars
- Descrição opcional abaixo com contexto
- Sem comentários de linha nos códigos (`//`, `#`, `/* */`) a menos que seja estritamente necessário — nomes bem escolhidos > comentário

### Pull requests

- Branch descritiva: `feat/<descrição>`, `fix/<descrição>`, `docs/<descrição>`
- Descreva o que + por quê (não só o diff — ele mostra o o quê)
- Vincule issue relacionado
- Documentação sempre atualizada junto com código

### Python

- Python 3.13+ (nosso build.py usa 3.13 features)
- Formatação: aceitamos qualquer coisa coerente, não usamos linter rígido

### Java (APK)

- Java 1.8 target
- Android SDK API 17 (Android 4.2.2)
- Named inner classes sempre (anonymous crasha o D8 em certos padrões)

### Markdown

- Marcadores internos usando `##` como primeiro nível (`#` é reservado pro título do doc)
- Preferência por tabelas quando é dado tabular
- Linhas duras ≤ 100 chars (não hard)

## Code of conduct

Seja respeitoso. Comunidade pequena, projeto de nicho — todo mundo aqui gosta do mesmo carro.

Zero tolerância para: discriminação, assédio, spam.

## Licença

Ao contribuir com código, você concorda que seu código será licenciado sob MIT (ver `LICENSE`). Documentação sob CC BY 4.0.

Você mantém direitos autorais sobre seu trabalho — só cede permissão de uso.
