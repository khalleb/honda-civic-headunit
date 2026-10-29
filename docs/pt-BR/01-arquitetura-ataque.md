# 01 — Arquitetura do ataque

Como conseguimos **instalar código novo em `/system/` sem ADB, sem bootloader destravado e sem assinatura da Honda** — usando só um pendrive e o botão AUDIO.

Esse doc explica **por que funciona**. Pra receita de build, veja [`04-build-do-pacote.md`](04-build-do-pacote.md). Pra protocolo no carro, veja [`05-deploy-no-carro.md`](05-deploy-no-carro.md).

---

## O ponto fraco: EvilValet

A central multimídia tem um fluxo de atualização de firmware que roda assim:

1. Dono conecta pendrive FAT32 com uma pasta `/<rom_type>/SwUpdate.mdt` (o pacote OTA).
2. No **cold boot**, um service chamado `daupdater` escaneia o pendrive.
3. Se achar `SwUpdate.mdt` que:
   - está na pasta cujo nome bate com o `custom_rom.type` da central (ex: `0040`), **e**
   - está assinado com uma chave que o recovery AOSP aceita,
4. ...o recovery aplica o pacote como se fosse uma atualização legítima da Honda.

**O bug:** o recovery da safra Mitsubishi Andromeda aceita a **testkey AOSP pública** — a mesma chave que o Google usa em builds de teste do Android. Essa chave está no AOSP source e qualquer um pode assinar um `SwUpdate.mdt` com ela.

Essa vulnerabilidade foi descoberta e documentada por **Eric McDonald (librick)** em [juniperspring.org](https://juniperspring.org/posts/honda-evil-valet/) e batizada de **EvilValet** — "qualquer valet com um pendrive pode plantar firmware no seu carro".

### Por que o nome EvilValet

O cenário teórico original: você dá o carro pro valet do estacionamento. Enquanto você come, ele conecta um pendrive e aplica um pacote que planta spyware no `/system/`. Zero sinal visível.

Para nós, isso é um recurso, não um bug — permite que o dono do carro aplique modificações **com consentimento próprio**, sem precisar de bootloader destravado ou ferramentas caras.

---

## Pipeline completo

![Pipeline do deploy](../images/arquitetura.svg)

Em texto:

```
┌─────────────────────────────────────────────────────────────────────┐
│ NO PC (preparação)                                                  │
│                                                                      │
│  gradlew assembleRelease      →  AutoOk.apk (bytecode do nosso APK) │
│  apksigner --ks debug.keystore →  AutoOk.apk assinado com debug key │
│  python3 build.py             →  SwUpdate.mdt assinado c/ testkey   │
│  prepare-pendrive-install.sh  →  pendrive FAT32 com /0040/*.mdt     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (pendrive na porta USB-A frontal)
┌─────────────────────────────────────────────────────────────────────┐
│ NO CARRO (deploy)                                                   │
│                                                                      │
│  Dono segura AUDIO por 5s                                           │
│   └─ Central mostra diálogo "Quer reiniciar?"                       │
│      └─ Dono confirma → SHUTDOWN + COLD BOOT                        │
│         │                                                            │
│         ▼                                                            │
│      Boot cold → daupdater escaneia /mnt/usbdrive1/                 │
│         └─ Encontra /0040/SwUpdate.mdt                              │
│            └─ Valida signature contra testkey ✓                     │
│               └─ Transfere pro /cache + reboot pro recovery         │
│                  └─ Recovery AOSP aplica updater-script             │
│                     ├─ monta /system via edify                      │
│                     ├─ package_extract: AutoOk.apk, su, busybox     │
│                     ├─ set_perm: AutoOk.apk 0644, su 06755          │
│                     └─ umount + reboot                              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (central volta ao normal)
┌─────────────────────────────────────────────────────────────────────┐
│ EM OPERAÇÃO (toda vez que o carro liga)                             │
│                                                                      │
│  BOOT_COMPLETED → BootReceiver → AutoOkService                      │
│   └─ LogcatWatcher thread lê `logcat ActivityManager:I *:S` via su  │
│      └─ Procura string "...dalauncher/.OpeningDivideActivity"       │
│         └─ Quando encontra:                                          │
│            ├─ sleep 1s (deixa UI renderizar)                        │
│            ├─ su -c "input tap 400 350"  (coord do botão OK)        │
│            └─ sleep 10s + reseta flag → pronto pra próxima aparição │
└─────────────────────────────────────────────────────────────────────┘
```

---

## As 4 peças

### Peça 1 — Pacote OTA (`SwUpdate.mdt`)

Zip assinado com testkey AOSP. Contém:
- `META-INF/com/google/android/update-binary` — binário edify do AOSP
- `META-INF/com/google/android/updater-script` — comandos (mount, package_extract_file, set_perm, etc.)
- `system/app/AutoOk.apk` — nosso APK
- `system/xbin/su` — binário setuid root
- `busybox` — toolkit ARM estático (necessário porque recovery BR não tem `/sbin/sh`)
- `META-INF/MANIFEST.MF`, `CERT.SF`, `CERT.RSA` — assinatura

Construído por `tooling/ota-build/build.py` (nosso wrapper sobre o `ota-builder` do ic1101).

### Peça 2 — Pendrive de disparo

FAT32 MSDOS. Dois arquivos:
- `SwUpdate2.txt` — arquivo de 28 bytes contendo `Ver:1\n` (trigger file)
- `<rom_type>/SwUpdate.mdt` — o pacote

O daupdater busca especificamente nessa estrutura. Se o nome da pasta não bate com o `custom_rom.type` da central, o pacote é ignorado silenciosamente.

### Peça 3 — `AutoOk.apk` + `su`

Instalados em `/system/`:
- **`/system/app/AutoOk.apk`** (16 KB) — service persistente que monitora logcat
- **`/system/xbin/su`** (133 KB, mode `06755`) — root setuid simples (do root-honda)

Depois de instalados, qualquer boot cold da central:
1. Android sobe → `BOOT_COMPLETED` broadcast
2. Nosso `BootReceiver` captura → inicia `AutoOkService`
3. Service dispara `su` → `logcat` → observa transições de Activity

### Peça 4 — O tap simulado

Quando o APK detecta o aviso no logcat, roda:
```
su -c "input tap 400 350"
```

`input` é um binário padrão do Android em `/system/bin/` que simula eventos de toque. `(400, 350)` é o centro do botão OK na tela 800×480 da nossa safra BR.

Visualmente: a tela do aviso aparece → ~2 segundos depois um ponteiro invisível "clica" no OK → aviso some.

---

## Por que isso é mais seguro que alternativas

| Abordagem | Risco de brick | Reversível? | Honda pode detectar? |
|---|---|---|---|
| **Nosso (EvilValet + APK em /system/app)** | Baixo — só adicionamos 2 arquivos novos, não modificamos nada existente | Sim — rollback OTA remove tudo | Não — APK fica como se fosse app do sistema |
| Modificar `DaLauncher.apk` | Alto — brick do launcher = tela preta | Sim mas requer OTA | Não |
| Xposed Framework | Alto — patch do `/system/bin/app_process` = bootloop se der problema | Sim mas delicado | Possivelmente (fingerprint mudado) |
| Honda Hack (pago) | Baixo | Sim | Possível (checksum) |

Nosso ataque é **cirúrgico**: não mexe em nada que já existe no `/system`. Se der problema, basta remover os 2 arquivos novos que a central volta ao estado de fábrica.

---

## Como funciona em operação (persistência)

Depois de instalado, o APK precisa **sobreviver a todos os ciclos de uso do carro**. Como:

### Cold boot (chave off → chave on completo)

1. Kernel + init + Zygote + system services
2. Android dispara `android.intent.action.BOOT_COMPLETED`
3. Nosso `BootReceiver` escuta → `startService(AutoOkService)`
4. Service inicia LogcatWatcher thread
5. Logcat emite transições de Activity
6. Watcher vê a string da `OpeningDivideActivity` → callback dispara tap

### Resume do suspend (virar a chave quando o carro já estava "dormindo")

**Aqui tem uma pegadinha:** `BOOT_COMPLETED` **só dispara em cold boot real**. Resume do suspend não dispara. Mas o Service com `START_STICKY` fica vivo entre resumes.

Então após o primeiro cold boot do dia, o Service já está no ar e vai interceptar o aviso em todas as próximas viradas de chave.

### Múltiplas aparições do aviso numa mesma sessão

A `OpeningDivideActivity` pode voltar a aparecer se o dono entrar no modo diagnóstico e sair, por exemplo. O APK trata isso com um sistema de rearm:

- Após disparar o tap, flag `handled = true` por 10s (evita duplo-tap)
- Depois dos 10s, flag volta a `false` → próxima aparição dispara outro tap
- O processo `logcat` fica vivo entre taps (não é recriado) — zero overhead

### Watchdog

Thread extra que a cada 30s verifica se o LogcatWatcher ainda está vivo. Se morreu (crash, kill externo), recria. Resiliente a condições adversas.

---

## Camada 2: patch smali no DaLauncher (Fase 10, 2026-10-29)

Tudo acima descreve a **Camada 1** — o AutoOk como safety net automático que vai dispensando o aviso. Em 2026-10-29 adicionamos a **Camada 2**: um patch de bytecode no próprio `DaLauncher.apk` que faz o aviso **não existir mais** no fluxo de boot.

A arquitetura do ataque é a **mesma** da Camada 1 (pacote OTA EvilValet assinado com testkey AOSP), só muda o payload: em vez de instalar `AutoOk.apk` + `su` em `/system/app/` e `/system/xbin/`, substitui o `/system/vendor/app/DaLauncher.apk` por uma versão nossa com um patch smali de 1 instrução e remove o `.odex` velho (que impediria o Dalvik de carregar o `classes.dex` novo).

### A instrução patcheada

Dentro de `OpeningDivideActivity.createDisclaimerOrEcoIntent()`:

```diff
     sget-boolean v0, Lcom/mitsubishielectric/ada/app/dalauncher/OpeningDivideActivity;->sDisclamerFlg:Z

-    if-nez v0, :cond_9
+    goto :cond_9

     invoke-direct {p0}, ...->createDisclaimerOnHomeIntent()Landroid/content/Intent;
```

Faz o fluxo ir sempre pro `createEcoIntent()`, que já estava no código mas nunca era alcançado em uso real (o `sDisclamerFlg` é `static boolean` em memória, sempre começa `false`).

### Por que esse caminho e não "pular tudo"

O `EcoFragment` que o patch acorda dispara em `startNextActivity()` as 4 chamadas que CarPlay/Navegação esperam: `NavigationApService.disclaimerDisappeared`, `AppManagerService.setDisclaimerPassed(true)`, `CarPlayApService.setDisplayPermission(status=true)` e o broadcast `DISCLAIMER_COMPLETE`. Pular direto pro Launcher principal quebraria CarPlay/Navegação. Preservar o Eco mantém a sequência intacta.

Um segundo patch (Fase 10.1, mesmo dia) reduz o timer da tela Eco de 5000 ms para 500 ms, deixando a tela imperceptível (~1 s total com animação) mas ainda tempo suficiente pro tap do AutoOk cair no fundo seguro dela.

### Rebuild auto-contido

O `tooling/fase10/rebuild-dalauncher.sh` deodexa o `.odex` original, aplica os dois patches versionados em `tooling/fase10/*.patch`, **prova** que a diferença orig→patch no DEX é exatamente `EcoFragment.smali` + `OpeningDivideActivity.smali` (falha senão), reempacota, zipaligna e assina com a testkey AOSP. O `build-dalauncher-fase10.py` recusa empacotar um APK não assinado com o testkey.

### Rede de segurança

Antes de aplicar o install, aplicamos o pacote de **restore** do DaLauncher original (bytes idênticos aos que estão no `/system/vendor/app/` do carro = no-op intencional). Isso valida o caminho de rollback **antes** de arriscar o install real. Se qualquer coisa der errado com o install, o mesmo pacote de restore é a saída.

Guia passo a passo para reaplicar: [`09-fase10-remover-aviso.md`](09-fase10-remover-aviso.md). Timeline do deploy real: [`../fase10-deploy-2026-10-29/README.md`](../fase10-deploy-2026-10-29/README.md).

---

## Caminhos técnicos profundos

- **Receita do pacote OTA**: [`fase7-deploy-2026-10-16/03-build-ota-receita.md`](../fase7-deploy-2026-10-16/03-build-ota-receita.md)
- **Arquitetura do APK (código linha a linha)**: [`fase7-deploy-2026-10-16/04-apk-autook-detalhes.md`](../fase7-deploy-2026-10-16/04-apk-autook-detalhes.md)
- **Fase 10 — timeline do deploy e tabelas de SHA/md5**: [`../fase10-deploy-2026-10-29/README.md`](../fase10-deploy-2026-10-29/README.md)
- **Decisão de rota da Fase 10 (resign AOSP vs. odex-level patch)**: [`../fase10-decisao-rotas-2026-10-23.md`](../fase10-decisao-rotas-2026-10-23.md)
- **Descobertas específicas da safra BR**: [`fase7-deploy-2026-10-16/02-descobertas-tecnicas.md`](../fase7-deploy-2026-10-16/02-descobertas-tecnicas.md)
- **Mapa do filesystem da central**: [`../MAPA.md`](../MAPA.md)

## Créditos técnicos

- **EvilValet** descoberto e documentado por [Eric McDonald (librick)](https://juniperspring.org/) — [juniperspring.org/posts/honda-evil-valet](https://juniperspring.org/posts/honda-evil-valet/)
- **ota-builder** (base do nosso `build.py`): [github.com/librick/ic1101](https://github.com/librick/ic1101)
- **su setuid** (do nosso `/system/xbin/su`): [github.com/codeage/root-honda](https://github.com/codeage/root-honda)
- **busybox ARM estático**: embarcado no HondaHack APK, extraído e redistribuído

Sem esses três projetos, nada disso aqui seria possível.
