# 04 — Build do pacote

Passo a passo pra transformar o código do repositório em um `SwUpdate.mdt` pronto pra copiar no pendrive.

**Pré-requisito:** [`02-pre-requisitos.md`](02-pre-requisitos.md) todo marcado.

**Tempo:** ~2-5 minutos no primeiro build (download de dependências Gradle). ~30 segundos nos builds seguintes.

---

## Visão geral — 3 artefatos

O "build" produz 3 coisas distintas:

| Artefato | Comando | Saída |
|---|---|---|
| **1. APK** (`AutoOk.apk`) | `./gradlew assembleRelease` + `apksigner` | `our-apk/app/build/outputs/apk/release/AutoOk.apk` |
| **2. Pacote OTA INSTALL** | `python3 tooling/ota-build/build.py` | `tooling/ota-build/output/<timestamp>/0040/SwUpdate.mdt` |
| **3. Pacote OTA ROLLBACK** | `python3 tooling/ota-build/build-rollback.py` | `tooling/ota-build/output-rollback/<timestamp>/0040/SwUpdate.mdt` |

Os pacotes OTA referenciam o APK — então o fluxo é **APK primeiro, OTA depois**.

---

## Passo 1 — Build do APK

```bash
cd our-apk
./gradlew clean assembleRelease
```

**O que acontece:**
1. Gradle resolve dependências (primeira vez: baixa ~500 MB de Android SDK stuff)
2. Compila Java com javac
3. Converte bytecode Java → Dalvik DEX com D8
4. Empacota tudo em APK não-assinado

**Saída esperada:**
```
BUILD SUCCESSFUL in 10s
39 actionable tasks: 38 executed, 1 up-to-date
```

APK gerado em:
```
our-apk/app/build/outputs/apk/release/app-release-unsigned.apk
```

### Troubleshooting do build

**Erro: "D8: NullPointerException" com anonymous inner classes:**
D8 bug em versões antigas (4.0.52). Nosso código **não usa** anonymous inner classes exatamente por causa disso — usa named inner classes. Se você estiver modificando o código, mantenha nomes explícitos (`class AvisoCallback implements OnDetected { ... }` em vez de `new OnDetected() { ... }`).

**Erro: "Unsupported Java version":**
Confira que está usando JDK 17:
```bash
java -version
# Se não, force:
JAVA_HOME=/usr/lib/jvm/java-17-openjdk ./gradlew clean assembleRelease
```

**Erro: "SDK location not found":**
Crie `our-apk/local.properties`:
```properties
sdk.dir=/home/<seu-user>/sdks/Android
```

---

## Passo 2 — Assinar o APK

```bash
cd /caminho/do/honda-civic-headunit  # voltar pro root
APKSIGNER=$ANDROID_SDK_ROOT/build-tools/33.0.2/apksigner

$APKSIGNER sign \
  --ks ~/.android/debug.keystore \
  --ks-pass pass:android \
  --out our-apk/app/build/outputs/apk/release/AutoOk.apk \
  our-apk/app/build/outputs/apk/release/app-release-unsigned.apk
```

**Verifica assinatura:**
```bash
$APKSIGNER verify --print-certs \
  our-apk/app/build/outputs/apk/release/AutoOk.apk
```

Deve mostrar o certificado "Android Debug" e `Verifies` no fim.

---

## Passo 3 — Copiar pro overlay do pacote OTA

```bash
cp our-apk/app/build/outputs/apk/release/AutoOk.apk \
   tooling/ota-build/overlay/system/app/AutoOk.apk
```

O `tooling/ota-build/overlay/` é a "árvore virtual" que o `build.py` enfia dentro do pacote OTA. O que estiver aqui vai parar em `/system/` da central.

**Confira o SHA-256 pra garantir que copiou certo:**
```bash
sha256sum our-apk/app/build/outputs/apk/release/AutoOk.apk \
          tooling/ota-build/overlay/system/app/AutoOk.apk
# Os dois hashes devem ser idênticos
```

---

## Passo 4 — Build do pacote OTA INSTALL

```bash
python3 tooling/ota-build/build.py
```

**O que acontece:**
1. Importa `main` do `ic1101/ota-builder/src/main.py`
2. Monkey-patcha `stage_tree` para incluir nosso overlay + busybox embarcado
3. Gera `updater-script` edify com nossos comandos (mount, package_extract_file, set_perm)
4. Chama `build_mdt` que empacota tudo em zip + assina com testkey AOSP
5. Deposita o `.mdt` final em `output/<timestamp>/0040/SwUpdate.mdt`

**Saída esperada:**
```
INFO: deploy: /system/app/AutoOk.apk owner=0:0 mode=0644
INFO: rom_type=0040 -> /path/to/output/20261017T131606Z/0040/SwUpdate.mdt
OK: /path/to/output/20261017T131606Z
```

### Troubleshooting do OTA build

**Erro: "no such file: tooling/ota-build/bin/busybox":**
Esqueceu de extrair o busybox do HondaHack.apk. Veja [`02-pre-requisitos.md § Binários`](02-pre-requisitos.md).

**Erro: "ImportError: cannot import name 'main' from 'main'":**
`tooling/references/ic1101/` não foi clonado. Rode `./MIGRATION/setup.sh`.

**Pacote gerado mas vazio (~1KB) em vez de ~870KB:**
O overlay não está sendo incluído. Verifica se o APK está em `tooling/ota-build/overlay/system/app/AutoOk.apk`.

---

## Passo 5 — Build do pacote OTA ROLLBACK (SEMPRE!)

**Regra de ouro:** nunca deploy do INSTALL sem o ROLLBACK pronto.

```bash
python3 tooling/ota-build/build-rollback.py
```

**O que esse pacote faz na central:**
- `rm /system/app/AutoOk.apk`
- `rm /system/xbin/su`
- Verifica que ambos sumiram
- Grava log no pendrive

Volta a central exatamente ao estado anterior ao INSTALL.

**Saída esperada:**
```
INFO: rollback mdt: /path/to/output-rollback/<timestamp>/0040/SwUpdate.mdt
```

---

## Passo 6 — (Opcional) Build de dump raw / deep scan

Dois pacotes OTA extras que podem ser úteis:

### Dump raw bootable (recuperação de brick total)

```bash
python3 tooling/ota-build/build-dump-raw.py
```

Esse pacote **dumpa as partições APP + CAP + MITSU** inteiras pro pendrive em formato `.img.gz`. Dura ~18 minutos no carro. Resultado: imagens bootáveis que você pode usar pra restaurar via `dd` reverso se o firmware ficar inoperante.

Veja [`08-backups-e-rollback.md`](08-backups-e-rollback.md).

### Deep scan (mapa textual completo)

```bash
python3 tooling/ota-build/build-deep-scan.py
```

Esse pacote faz um "scan" textual de todas as partições + build.prop + packages.xml + /proc/* e empacota em `scan.tar.gz`. Útil pra sincronizar o [`docs/MAPA.md`](../MAPA.md) com o estado real da central.

Após deploy:
```bash
python3 tooling/scripts/gen-mapa.py
```

Gera `~/backup-honda-civic-g10/deep-scan-YYYY-MM-DD/RELATORIO.md`.

---

## Verificar o pacote pronto

```bash
ls -la tooling/ota-build/output/<timestamp>/0040/
# -rw-r--r--. 1 khalleb khalleb 872053 ... SwUpdate.mdt
```

Tamanho esperado: **~870 KB** (varia conforme APK). Se estiver muito pequeno (<10 KB) ou muito grande (>5 MB), algo deu errado.

**Verificar assinatura do pacote OTA (opcional):**
```bash
unzip -l tooling/ota-build/output/<timestamp>/0040/SwUpdate.mdt
# Deve listar META-INF/MANIFEST.MF, CERT.SF, CERT.RSA + system/ + busybox
```

---

## Script "tudo em um" (futuro)

Pra automatizar os passos 1-5, dá pra criar um `tooling/scripts/full-build.sh`. Ainda não existe — ver [`PENDENCIAS.md`](../../PENDENCIAS.md). Por enquanto, cola os comandos manualmente:

```bash
#!/bin/bash
set -e
cd our-apk && ./gradlew clean assembleRelease && cd ..
$ANDROID_SDK_ROOT/build-tools/33.0.2/apksigner sign \
  --ks ~/.android/debug.keystore --ks-pass pass:android \
  --out our-apk/app/build/outputs/apk/release/AutoOk.apk \
  our-apk/app/build/outputs/apk/release/app-release-unsigned.apk
cp our-apk/app/build/outputs/apk/release/AutoOk.apk \
   tooling/ota-build/overlay/system/app/AutoOk.apk
python3 tooling/ota-build/build.py
python3 tooling/ota-build/build-rollback.py
echo "✓ INSTALL + ROLLBACK prontos."
ls -la tooling/ota-build/output/*/0040/SwUpdate.mdt
ls -la tooling/ota-build/output-rollback/*/0040/SwUpdate.mdt
```

---

## Próximo passo

Pacote pronto? → [`05-deploy-no-carro.md`](05-deploy-no-carro.md) pra preparar o pendrive e deployar.
