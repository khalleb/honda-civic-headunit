# Fase 10 — Remover o aviso de vez (pré-planejamento)

> Investigação técnica completa feita em 2026-10-20 a partir do diagnóstico
> coletado via `build-diagnostic.py`. Esse doc não é a execução — é o
> briefing pronto pra quando v0.5.4 ficar estável e quisermos atacar a
> remoção definitiva do disclaimer.
>
> Pré-requisito: v0.5.4 do AutoOk em produção e estável por pelo menos
> 1 semana. Enquanto v0.5.4 estiver sob observação, não abrir Fase 10.

## Objetivo

Eliminar a tela de aviso (`OpeningDivideActivity`) do boot da central
em definitivo. Hoje o AutoOk v0.5.4 tapa o OK automaticamente, mas a
tela ainda aparece por ~2-5 segundos. Fase 10 remove o fluxo todo:
zero aparição, zero tap, zero watcher.

## O gate descoberto

O `DaLauncher.apk` decide se mostra o aviso em um `static boolean`
chamado `sDisclamerFlg` em `OpeningDivideActivity`. Ele **não é
persistido em disco** — reseta pra `false` a cada boot da classe, por
isso o aviso aparece sempre.

Confirmado no smali deodex local (`tooling/apks-decoded/DaLauncher-deodexed/`):

```
OpeningDivideActivity.smali:17   .field public static sDisclamerFlg:Z
OpeningDivideActivity.smali:67   sput-boolean v0, ...sDisclamerFlg:Z    ← clinit, v0 = false
OpeningDivideActivity.smali:669  sget-boolean v0, ...sDisclamerFlg:Z    ← lê o flag
OpeningDivideActivity.smali:671  if-nez v0, :cond_9                      ← se true, pula o aviso
DisclaimerFragment.smali:4363    sput-boolean v5, ...sDisclamerFlg:Z    ← seta true depois do tap OK
HmiBroadcastReceiver.smali:492   sput-boolean v10, ...sDisclamerFlg:Z   ← Honda reseta false em LP0
HmiBroadcastReceiver.smali:636   sput-boolean v10, ...sDisclamerFlg:Z   ← outro reset
```

O método `createDisclaimerOrEcoIntent()` no `OpeningDivideActivity.smali`
(linhas 664-688) é o decisor:

```smali
.method private createDisclaimerOrEcoIntent()Landroid/content/Intent;
    sget-boolean v0, ...sDisclamerFlg:Z
    if-nez v0, :cond_9
    invoke-direct {p0}, ...createDisclaimerOnHomeIntent()...    # mostra o aviso
    move-result-object v0
    :goto_8
    return-object v0
    :cond_9
    invoke-direct {p0}, ...createEcoIntent()...                 # vai pra tela Eco (normal)
    move-result-object v0
    goto :goto_8
.end method
```

Em pseudo-Java:

```java
private Intent createDisclaimerOrEcoIntent() {
    if (sDisclamerFlg) {
        return createEcoIntent();              // próxima tela normal
    }
    return createDisclaimerOnHomeIntent();     // tela do aviso
}
```

## O patch

**Mudança mínima em `OpeningDivideActivity.smali` linha 671**:

```
Antes:   if-nez v0, :cond_9
Depois:  goto :cond_9
```

Isso força a jump incondicional pra `createEcoIntent()`, ignorando o
flag. Equivale a dizer que o disclaimer está sempre dispensado.

**Alternativa equivalente**: trocar a instrução no clinit (linha 67)
pra inicializar o flag como `true`:

```
Antes:   sput-boolean v0, ...sDisclamerFlg:Z    (v0 = 0)
Depois:  sput-boolean v1, ...sDisclamerFlg:Z    (v1 = 1)
```

Preferir a primeira (mudança no if). Mantém o estado do flag consistente
pros outros caminhos de código que leem.

## Signature do DaLauncher — por que o deploy é não-trivial

O DaLauncher.apk é assinado por **chave corporativa Mitsubishi** —
`CN=Melco Honda16MY, OU=Sanda Works, O=Mitsubishi Electric, L=Sanda, ST=Hyogo, C=JP`
— SHA-256 `93:14:CE:13:29:64:B4:87:22:79:6D:38:CE:FE:F1:6D:5B:95:8F:57:3D:A2:A0:BF:62:EE:21:8F:81:27:05:AD`.

Confirmado em 2026-10-20 via `keytool -printcert` sobre `META-INF/CERT.RSA`
extraído do APK em `tooling/apks-dumped/dump-0040/vendor-app/DaLauncher.apk`.

Outros vendor-apps (`PowerManagerApService`, `AppManager`,
`WhitelistApService`, `Camera`, `CameraAPService`) usam **outra chave
Mitsubishi** (SHA-256 começa com `A2:09:0F:C0:...:EF:65`). DaLauncher é
singular.

**Implicações:**

- Resign com nossa testkey AOSP (a mesma do AutoOk) → PackageManager
  detecta signature mismatch no boot e trata o DaLauncher como "new
  install", perdendo permissões de `/system/*`. Pode travar.
- Nenhum vendor-app parece compartilhar `android:sharedUserId` com o
  DaLauncher (chave singular), então substituir só ele **não quebra
  outros apps por mismatch**. É bom.
- Não temos a chave Mitsubishi (óbvio). Qualquer resign é lossy.

## Rotas de deploy

### Rota A — Odex-level patch (recomendada)

Modificar só o `.odex` do DaLauncher. O APK (com assinatura Mitsubishi
original) fica intocado em `/system/vendor/app/DaLauncher.apk`.

**Fluxo:**

1. Deodex local: `baksmali deodex DaLauncher.odex` — já temos (`tooling/apks-decoded/DaLauncher-deodexed/`)
2. Patch smali linha 671 (`if-nez` → `goto :cond_9`)
3. Re-smali → gera novo `classes.dex`
4. Converter dex → odex preservando o formato antigo (Dalvik)
5. Deploy só do `.odex` modificado via OTA; `.apk` segue o que está

**Prós:**

- Signature do APK nunca muda → PackageManager não suspeita
- Nenhuma outra permissão/UID é afetada
- Risco baixo de rejeição por framework

**Contras:**

- Re-odex de ARM dalvik é hairy. Pode exigir ferramenta `dexopt` ou
  deixar o `.odex` fora e deixar o Dalvik recriar no primeiro boot a
  partir do APK (que ainda tem só MANIFEST, sem `classes.dex` original)
- Alternativa: injetar o `classes.dex` novo DENTRO do APK e deixar o
  Dalvik gerar novo `.odex` automaticamente — mas isso invalida a
  signature do APK (MANIFEST.MF referencia o SHA do dex antigo)

### Rota B — Resign com testkey AOSP + "new install"

Deodex + patch smali + rebuild APK + resign com nossa testkey +
deploy via OTA. DaLauncher vira "new install" porque signature mudou.

**Prós:**

- Fluxo idêntico ao AutoOk — tooling já domina
- Patch cirúrgico, 1 instrução

**Contras:**

- DaLauncher perde permissões especiais `/system/*`
- Pode funcionar OU alguma permission faltante causa crash no boot
- Precisa deploy numa única passada com rollback preparado

### Rota C — Hex-swap só do classes.dex (não funciona)

Dropar `.odex`, injetar `classes.dex` modificado no APK sem resign.
`MANIFEST.MF`/`CERT.SF` referenciam SHA do dex antigo → signature
verify falha. Descartada.

## Rede de segurança obrigatória antes de executar

Antes de qualquer uma das rotas, garantir:

- [x] Dump raw do `/system` atual (temos de 2026-10-17 em `~/backup-honda-civic-g10/dump-raw-2026-10-17/`)
- [x] Rollback OTA do AutoOk pronto (`tooling/ota-build/output-rollback/`)
- [ ] Rollback OTA do DaLauncher pronto — **novo**: um pacote OTA que restaure `/system/vendor/app/DaLauncher.apk` e `DaLauncher.odex` originais
- [ ] Backup externo mais recente que o dump de 2026-10-17 (se mudar algo no HU entre lá e cá)

O rollback do DaLauncher precisa ser construído antes de executar a
Fase 10. Esquema:

- Build script novo: `tooling/ota-build/build-dalauncher-restore.py`
- Inclui `DaLauncher.apk` e `DaLauncher.odex` originais no overlay
- Updater-script substitui os arquivos modificados pelos originais

Sem esse rollback, Fase 10 fica proibida.

## Dependências de tooling

Pra executar:

- `baksmali` e `smali` — já temos (`tooling/references/ic1101/apk-rebuilder/input/`)
- `apksigner` — já temos (`~/sdks/Android/build-tools/33.0.2/apksigner`)
- `keytool` — JDK 17 (`~/.local/jdk/jdk-17.0.20.1+1/bin/keytool`)
- `dexopt` ou equivalente pra re-odex (ROTA A) — **falta**: pesquisar
  alternativas, provavelmente usar `dx` em modo compatibilidade ou
  deixar o Dalvik rebuildar `.odex` no primeiro boot
- Nossa `deodex-apk.sh` — já criada

## Checklist pra abrir Fase 10

Nessa ordem:

1. [ ] v0.5.4 em produção estável por 1+ semana
2. [ ] Confirmado via diagnostico que v0.5.4 zerou os taps falsos
3. [ ] Construído `build-dalauncher-restore.py` + testado o rollback no
       carro (deploy do rollback de DaLauncher sobre DaLauncher original
       deve ser no-op)
4. [ ] Decidido entre Rota A e Rota B (recomendado: tentar A primeiro)
5. [ ] Pacote OTA do DaLauncher patcheado gerado localmente
6. [ ] Deploy no carro + 1 reboot de teste
7. [ ] Observar aviso NUNCA mais aparecer no boot
8. [ ] Deixar v0.5.4 do AutoOk ativo como safety net por ~1 semana
9. [ ] Se tudo estável, remover AutoOk do `/system/app/` via rollback

## Caminho de aborto

Se Fase 10 der ruim:

- **Boot normal mas launcher travado**: aplicar rollback do DaLauncher
  (pacote construído no passo 3)
- **Boot loop**: pendrive com rollback do DaLauncher na USB-A frontal,
  AUDIO 5s + confirmar
- **Tela preta**: mesmo rollback. Se não resolver, fallback é o dump
  raw de 2026-10-17 (restaurar `/system` inteiro — mais pesado, mas
  recupera 100%)

## Riscos conhecidos (ordem decrescente)

| Risco | Mitigação |
|---|---|
| Launcher trava por signature mismatch (Rota B) | Rollback OTA pronto |
| HmiBroadcastReceiver reseta `sDisclamerFlg` em evento desconhecido e nosso patch não cobre | Patch no `if-nez` (nossa primeira escolha) ignora o flag completamente, imune a resets |
| `.odex` modificado não carrega por fingerprint divergente (Rota A) | Fallback pra Rota B |
| Alguma Activity dependente do fluxo esperar o disclaimer | Testar fluxo home → ajustes → câmera de ré pós-deploy, antes de remover AutoOk |

## Economia esperada

- Zero latência (hoje ~2-5s de aviso na tela)
- Zero CPU/bateria do `logcat` persistente do AutoOk
- Zero risco do tap acertar botão errado em qualquer contexto (bug que
  v0.5.4 corrigiu, mas que Fase 10 elimina pela raiz)

## Referências cruzadas

- [`../our-apk/`](../our-apk/) — fonte do AutoOk que ficará como safety net
- [`./MAPA.md § 11.1.1`](./MAPA.md) — OpeningDivideActivity internals
- [`./MAPA.md § 17.15`](./MAPA.md) — bug do mudo em CarPlay (contexto do v0.5.4)
- [`./MAPA.md § 17.16`](./MAPA.md) — gate do disclaimer descoberto
- [`./raio-x/02-broadcasts.md`](./raio-x/02-broadcasts.md) — ACTION_DISCLAIMER_COMPLETE
- [`./raio-x/05-trust-map.md`](./raio-x/05-trust-map.md) — permissões do DaLauncher
- [`../tooling/apks-decoded/DaLauncher-deodexed/`](../tooling/apks-decoded/) — smali local
