# Como migrar o projeto pro Linux

## 📦 O que esta pasta `MIGRATION/` contém

- `setup.sh` — script que recria todo o ambiente no Linux
- `BRIEFING.md` — contexto do projeto pra uma nova sessão do Claude
- `central-multimidia-civic-g10-kb.md` — a base de conhecimento (adicionado abaixo)
- `COMO-USAR.md` — este arquivo

Tamanho total: menos de 1 MB. Cabe em qualquer pendrive.

## 🚚 Como transferir

### Opção A — GitHub (recomendado — fluxo escolhido)

1. No PC Windows (após `git init` e primeiro commit):
   ```powershell
   cd C:\repositorios\honda-civic
   git remote add origin https://github.com/<seu-usuario>/honda-civic-headunit.git
   git push -u origin main
   ```
2. No notebook Linux:
   ```bash
   mkdir -p ~/repositorios
   cd ~/repositorios
   git clone https://github.com/<seu-usuario>/honda-civic-headunit.git honda-civic
   cd honda-civic/MIGRATION
   chmod +x setup.sh
   ./setup.sh
   ```

### Opção B — Pendrive (alternativa offline)

1. Copia a pasta `C:\repositorios\honda-civic\` inteira para o pendrive.
2. No Linux: `cp -r /media/<USER>/<PENDRIVE>/honda-civic ~/repositorios/`
3. `cd ~/repositorios/honda-civic/MIGRATION && chmod +x setup.sh && ./setup.sh`

## 🖥️ No notebook Linux

### Passo 1 — Rodar o setup

```bash
cd ~/repositorios/honda-civic/MIGRATION
chmod +x setup.sh
./setup.sh
```

Isso vai:
- Instalar Java, ADB, Git, curl, unzip (via `sudo apt install`)
- Baixar apktool e jadx
- Clonar os 3 repositórios de referência
- Descompilar o HondaHack.apk
- Deixar tudo em `~/repositorios/honda-civic/tooling/`

Vai pedir sua senha pro `sudo apt install` uma vez.

### Passo 2 — Verificar que o setup funcionou

```bash
cd ~/repositorios/honda-civic
ls tooling/references/         # deve mostrar: root-honda, 2016PilotOneClick, ic1101
ls tooling/apks-decoded/       # deve mostrar: HondaHack
java -jar tooling/bin/apktool.jar --version   # deve dizer: 2.11.1
tooling/bin/jadx/bin/jadx --version          # deve dizer: 1.5.6
adb --version                                 # deve dizer: 1.0.41 ou superior
```

Se os 5 comandos funcionarem, o ambiente está pronto.

### Passo 3 — Iniciar uma sessão nova do Claude com contexto

Se o notebook da empresa tem **Claude Code** instalado:

```bash
cd ~/repositorios/honda-civic
claude
```

O arquivo `CLAUDE.md` na raiz do projeto é **carregado automaticamente** pelo
Claude Code — ele já vai saber do que se trata o projeto. Para dar o contexto
mais completo, cole o bloco de código do `MIGRATION/BRIEFING.md` como primeiro
prompt.

Se o notebook **não** tem Claude Code, você pode usar o **claude.ai no navegador**:

1. Abre https://claude.ai
2. Nova conversa
3. **Anexa o arquivo** `central-multimidia-civic-g10-kb.md`
4. Cola o prompt do BRIEFING.md
5. Pede pro Claude ler o KB antes de qualquer resposta

## 🔌 Próximo passo prático (depois do setup)

Com o cabo USB-C↔USB-A funcionando (teste do pendrive primeiro!):

1. Habilitar modo dev + ADB na central Honda (procedimento no KB)
2. Conectar cabo
3. `adb devices` → deve listar a central
4. Começa a Fase 3 (extrair APKs)

## ⚠️ Lembretes importantes de risco (notebook da empresa)

- **Rodar fora do horário de trabalho**
- **Desconectar da VPN corporativa** antes
- O binário `dirtycow` **vai disparar o antivírus** quando chegar nessa fase
- Se tiver política de uso restrita, pondere se vale continuar
- Prefira fazer em casa, não em espaços comuns

## 📞 Em caso de dúvida

Toda informação técnica está no `central-multimidia-civic-g10-kb.md`.
Se o Claude da nova sessão perder contexto, mande ele reler o KB.
