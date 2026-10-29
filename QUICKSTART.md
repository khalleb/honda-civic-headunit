# 🚀 Quick Start — Deploy em 20 minutos

Guia resumido para deployar na sua central Honda Civic G10 (safra `1.F187.16` BR confirmada).

**Para outras safras**, antes deste quickstart, siga [`docs/pt-BR/03-descobrindo-sua-safra.md`](docs/pt-BR/03-descobrindo-sua-safra.md).

> ⚠️ **ANTES DE COMEÇAR, LEIA O [DISCLAIMER.md](DISCLAIMER.md).**
> Risco de brick permanente. Troca de central: R$ 1.000-2.000. Você é 100% responsável.

## 🧭 Duas rotas de deploy

O projeto hoje oferece duas camadas de solução para o aviso. Você escolhe uma ou aplica as duas em sequência.

| | 🔹 **Camada 1 — AutoOk** (safety net) | 🎯 **Camada 2 — Fase 10** (solução definitiva) |
|---|---|---|
| O que faz | APK + `su` em `/system/`. Monitora logcat, dispara `input tap` no OK | Patch smali de 1 instrução no `DaLauncher.apk`. Força pular o `DisclaimerFragment` |
| Experiência visual | Aviso aparece e some sozinho em ~3 s | **Aviso não aparece.** Tela "ecoscore" por ~1 s (Fase 10.1) |
| Risco | Baixo (APK side-car, zero toque em app Mitsubishi existente) | Médio (modifica o DaLauncher — launcher principal; rede de segurança = pacote rollback) |
| Esforço | ~20 min total | ~30 min (precisa Camada 1 primeiro, ou outra forma de root pra validar o pipeline) |
| Reversível | Sim, via `prepare-pendrive-rollback.sh` sem argumento | Sim, via `prepare-pendrive-rollback.sh tooling/ota-build/output-dalauncher-restore` |

**Recomendação:** Camada 1 primeiro, testar 1 semana. Depois Camada 2 em cima. Este QUICKSTART detalha a Camada 1 passo a passo — a Camada 2 segue o mesmo esquema de pendrive OTA, roteiro completo em [`docs/fase10-execucao-2026-10-27.md`](docs/fase10-execucao-2026-10-27.md).

---

## 🛠️ Pré-requisitos

### Hardware

- **Honda Civic G10** 2017 EXL BR (safra `1.F187.16` confirmada; outras não testadas)
- **Pendrive USB-A** FAT32-formatável (qualquer tamanho ≥ 100MB funciona)
- **Notebook/PC Linux** (preferência Fedora/Ubuntu)
- Acesso físico ao carro

### Software no PC

```bash
# Dependências via package manager (Fedora)
sudo dnf install -y java-17-openjdk-devel android-tools git curl unzip parted dosfstools python3

# OU Ubuntu/Debian
sudo apt install -y openjdk-17-jdk android-tools-adb git curl unzip parted dosfstools python3
```

E Android SDK para `apksigner`:

```bash
mkdir -p ~/sdks/Android/cmdline-tools
cd ~/sdks/Android/cmdline-tools
curl -L -o cmdtools.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip cmdtools.zip && rm cmdtools.zip && mv cmdline-tools latest

export ANDROID_SDK_ROOT=~/sdks/Android
yes | $ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager --licenses
$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager "build-tools;33.0.2"
```

---

## 📥 1. Clonar o projeto e dependências

```bash
git clone https://github.com/khalleb/honda-civic-headunit.git
cd honda-civic-headunit

# Clonar os projetos de referência (ic1101 provê o ota-builder)
mkdir -p tooling/references
git clone https://github.com/librick/ic1101.git tooling/references/ic1101
git clone https://github.com/codeage/root-honda.git tooling/references/root-honda
```

## 📦 2. Preparar binários (busybox + su)

Esses binários vêm dos projetos de terceiros clonados acima:

```bash
mkdir -p tooling/ota-build/bin

# busybox do HondaHack (via root-honda packages)
# Se não houver HondaHack.apk no root-honda, baixe de outra fonte confiável
# ou compile busybox-static ARM você mesmo.
unzip -o tooling/references/root-honda/packages/HondaHack.apk -d /tmp/hondahack
cp /tmp/hondahack/res/raw/busybox tooling/ota-build/bin/busybox

# su do root-honda
cp tooling/references/root-honda/su tooling/ota-build/bin/su
```

## 🔨 3. Compilar o APK AutoOk

```bash
cd our-apk
./gradlew clean assembleRelease

# Assinar com debug keystore
APKSIGNER=$ANDROID_SDK_ROOT/build-tools/33.0.2/apksigner
$APKSIGNER sign \
  --ks ~/.android/debug.keystore \
  --ks-pass pass:android \
  --out app/build/outputs/apk/release/AutoOk.apk \
  app/build/outputs/apk/release/app-release-unsigned.apk

# Copiar pro overlay do pacote OTA
cp app/build/outputs/apk/release/AutoOk.apk ../tooling/ota-build/overlay/system/app/AutoOk.apk
cd ..
```

## 📦 4. Montar o pacote OTA

```bash
# Pacote de INSTALL (AutoOk.apk + su)
python3 tooling/ota-build/build.py

# Pacote de ROLLBACK (remove AutoOk.apk e su — rede de segurança)
python3 tooling/ota-build/build-rollback.py
```

Saída:

```
INFO: rom_type=0040 -> tooling/ota-build/output/<timestamp>/0040/SwUpdate.mdt
OK: tooling/ota-build/output/<timestamp>
```

## 💾 5. Preparar pendrive

Pluga o pendrive. Descobre o device (CUIDADO — rodar no device errado destrói dados do notebook!):

```bash
lsblk -o NAME,SIZE,MODEL,TRAN
```

Confirme qual `/dev/sdX` é o pendrive (`TRAN=usb`). Depois:

```bash
# Formatar FAT32 MSDOS (destrói conteúdo!)
sudo ./tooling/scripts/format-pendrive.sh /dev/sdX

# Carregar pacote INSTALL
sudo ./tooling/scripts/prepare-pendrive-install.sh /dev/sdX

# (Opcional, mas RECOMENDADO) Carregar outro pendrive com ROLLBACK pra ter de emergência
# ou guardar o rollback no notebook: tooling/ota-build/output-rollback/<timestamp>/
```

Puxa o pendrive do notebook.

---

## 🚗 6. Deploy no carro

1. **Pendrive na porta USB-A frontal** da central (perto do volante, não a do console central).
2. **Carro ligado** — chave em ACC ou ON, motor desligado.
3. **Segure o botão `AUDIO`** da central por **5 segundos**. Aparece diálogo "Quer reiniciar?".
4. **Confirma reiniciar**. A central inicia o fluxo:
   - Tela "Software update → Copying..." (barra 0% → 100%)
   - Central reinicia sozinha
   - Pode mostrar barra do recovery
   - Reboot normal
5. **Quando a central voltar à tela normal** (ou de Aviso), **puxa o pendrive**.
6. **Clica OK uma última vez manualmente** nessa primeira vez (APK vai começar a atuar no PRÓXIMO boot).

Tempo total: ~5-10 minutos de fluxo OTA.

## ✅ 7. Testar

- **Desligue o carro** (gira a chave para OFF).
- **Ligue de novo** (gira para ACC ou ON).
- A tela de Aviso aparece normalmente.
- **~10 segundos depois, deve sumir sozinha.**
- Teste várias vezes: desliga/liga, desliga/liga. Deve interceptar em TODAS.

Se funcionar: **🎉 projeto completo**. Pode remover a tela de aviso da sua lista mental.

---

## 🆘 Troubleshooting rápido

| Sintoma | Possível causa | Ação |
|---|---|---|
| Depois do AUDIO 5s, não aparece "Quer reiniciar?" | Combo wrong, central muito antiga | Tenta puxar fusível do radio por 15 min, religar — força cold boot |
| Tela "Software update" não aparece | Pendrive não detectado OU rom_type errado | Confere pendrive em outra porta USB, re-formata; se persistir, dumpar logs via Error History |
| Aviso aparece mas APK não bate | Service não iniciou OU needle da Activity errado | Veja [troubleshooting detalhado](docs/pt-BR/06-troubleshooting.md) |
| Central não boota depois | Algo deu errado | **Deploy do rollback urgente.** [docs/pt-BR/07-rollback.md](docs/pt-BR/07-rollback.md) |

Detalhes completos: [`docs/pt-BR/06-troubleshooting.md`](docs/pt-BR/06-troubleshooting.md).

## 🔙 Rollback

Se precisar reverter, carregue o pendrive com o pacote ROLLBACK e aplique igual ao INSTALL:

```bash
sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sdX
```

Depois no carro: mesmo protocolo (porta frontal + AUDIO 5s + confirma reiniciar). Pacote remove `AutoOk.apk` e `su` do `/system`.

---

**Próximo nível:**
- [`docs/fase7-deploy-2026-10-16/`](docs/fase7-deploy-2026-10-16/) — Camada 1 completa (fluxo EvilValet, análise do APK, descobertas da safra BR)
- [`docs/fase10-deploy-2026-10-29/README.md`](docs/fase10-deploy-2026-10-29/README.md) — **Camada 2 (Fase 10)**: patch smali no DaLauncher, timeline do deploy real, SHAs/md5 dos artefatos
- [`docs/fase10-execucao-2026-10-27.md`](docs/fase10-execucao-2026-10-27.md) — checklist passo a passo da Fase 10 no carro
- [`docs/MAPA.md`](docs/MAPA.md) — atlas navegável da central
