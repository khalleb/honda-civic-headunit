# 06 — Troubleshooting

Decision tree pra quando algo não funciona.

**Antes de tentar qualquer coisa aqui:**
- Confirme que você tem o pacote **ROLLBACK pronto** no notebook. Veja [`07-rollback.md`](07-rollback.md).
- Faça backup do `~/.android/debug.keystore` em local separado.

---

## 🧭 Decision tree

```
Problema → onde está?

├─ Build (PC)
│   ├─ gradlew assembleRelease falha ............ § Build do APK falha
│   ├─ apksigner falha .......................... § Assinatura falha
│   └─ build.py falha ........................... § Build do OTA falha
│
├─ Pendrive
│   ├─ prepare-pendrive-install.sh falha ........ § Pendrive não detectado
│   └─ Pendrive copiado mas carro não reconhece . § Carro não lê o pendrive
│
├─ Carro (durante deploy OTA)
│   ├─ AUDIO 5s não abre diálogo ................ § Combo cold boot não funciona
│   ├─ Diálogo aparece mas depois nada acontece . § Pacote não aplica
│   ├─ Barra de progresso trava .................. § OTA trava no meio
│   └─ Reboot infinito pós-OTA .................. § Boot loop (CRÍTICO)
│
└─ Carro (depois do deploy)
    ├─ Aviso continua aparecendo sem dismiss .... § APK não dispara
    ├─ Aviso some mas trava a tela ............... § Tap errado
    ├─ APK funciona só no 1º boot ................ § Service morre entre boots
    └─ CarPlay/Bluetooth param .................. § Modificação danificou algo
```

---

## § Build do APK falha

### Erro: "D8: NullPointerException"
D8 (dexer) bug com anonymous inner classes. Converta pra **named** inner classes.

Exemplo que falha:
```java
new Runnable() {
    @Override public void run() { ... }
}
```

Exemplo que funciona:
```java
static class MyRunnable implements Runnable {
    @Override public void run() { ... }
}
new MyRunnable();
```

### Erro: "Unsupported Java version" ou "class file version"
JDK errado. Precisa ser **17**.
```bash
java -version   # tem que mostrar 17.X
JAVA_HOME=/usr/lib/jvm/java-17-openjdk ./gradlew clean assembleRelease
```

### Erro: "SDK location not found"
Crie `our-apk/local.properties`:
```properties
sdk.dir=/home/<seu-user>/sdks/Android
```

### Erro: "Could not resolve dependencies"
Primeiro build do Gradle precisa de internet pra baixar dependências. Confirme que tem conexão.

---

## § Assinatura falha

### Erro: "keystore was tampered with, or password was incorrect"
Keystore errado. Padrão é `~/.android/debug.keystore` com senha `android`:
```bash
ls ~/.android/debug.keystore
$APKSIGNER sign --ks ~/.android/debug.keystore --ks-pass pass:android \
  --out AutoOk.apk app-release-unsigned.apk
```

Se o keystore foi perdido, regenerar:
```bash
keytool -genkey -v -keystore ~/.android/debug.keystore \
  -alias androiddebugkey -keyalg RSA -keysize 2048 \
  -validity 10000 -dname "CN=Android Debug,O=Android,C=US" \
  -storepass android -keypass android
```

**ATENÇÃO:** keystore nova = assinatura nova = Android recusa upgrade do APK existente na central. Precisa fazer ROLLBACK antes de instalar APK com nova chave.

---

## § Build do OTA falha

### Erro: "ImportError: cannot import name 'main' from 'main'"
`tooling/references/ic1101/` não existe. Clone:
```bash
git clone https://github.com/librick/ic1101.git tooling/references/ic1101
```

### Erro: "FileNotFoundError: tooling/ota-build/bin/busybox"
Extraia o busybox do HondaHack APK:
```bash
unzip -o tooling/references/root-honda/packages/HondaHack.apk -d /tmp/hondahack
cp /tmp/hondahack/res/raw/busybox tooling/ota-build/bin/busybox
```

### Erro: "FileNotFoundError: tooling/ota-build/bin/su"
```bash
cp tooling/references/root-honda/su tooling/ota-build/bin/su
```

### Pacote gerado mas vazio (< 10 KB)
O overlay não foi incluído. Confirma que o APK existe:
```bash
ls -la tooling/ota-build/overlay/system/app/AutoOk.apk
```

Se não, copie:
```bash
cp our-apk/app/build/outputs/apk/release/AutoOk.apk \
   tooling/ota-build/overlay/system/app/AutoOk.apk
```

---

## § Pendrive não detectado

### `lsblk` não mostra o pendrive
- Plugue em outra porta USB do notebook
- Teste em outra máquina (confirma que o pendrive funciona)
- `dmesg | tail -20` após plugar — procura mensagens tipo `[sdb] Attached SCSI`

### `prepare-pendrive-install.sh` diz "não é USB"
O script verifica `lsblk -no TRAN` pra confirmar que é USB. Se seu pendrive aparece como `TRAN=sata` ou vazio, use outro pendrive.

### Script roda mas pendrive volta vazio
Script pode ter rodado em device errado! Confirma:
```bash
sudo mount /dev/sda1 /mnt/temp
ls -la /mnt/temp
sudo umount /mnt/temp
```

Deve ter `SwUpdate2.txt` e pasta `0040/`.

---

## § Carro não lê o pendrive

### Nenhuma barra de progresso aparece após AUDIO 5s + confirmar
Possíveis causas:
1. **Pendrive na porta errada**: USE A PORTA USB-A FRONTAL (perto do volante), não a USB-C nem a do console secundário
2. **FAT32 formato errado**: deve ser MSDOS FAT32, não exFAT, não NTFS
3. **Pendrive muito grande** (>128GB) — alguns BIOS automotivos rejeitam. Use 8-32GB
4. **rom_type errado**: pasta no pendrive precisa ser nomeada exatamente como `0040` (ou o rom_type da sua safra). Confere com `ls /run/media/<user>/HONDA_OTA/`
5. **SwUpdate2.txt faltando**: trigger file. Deve ter 28 bytes com `Ver:1\n`

### Barra aparece rápida e some
É normal — pode ser `SystemUpdate.apk` detectando mas rejeitando (assinatura ou rom_type errado). Vai pra `Error History` ler log:
- Com áudio off: `DAY/NIGHT + AUDIO + MENU` 2s → menu de serviço
- `Detail Information & Setting → Error History → Save`
- Puxa pendrive, lê `logcat.txt`:
```bash
grep "daupdater\|SystemUpdate" /run/media/<user>/HONDA_OTA/logcat.txt
```

---

## § Combo cold boot não funciona

### AUDIO 5s não abre diálogo
Testes:
1. **Botão mal pressionado**: segura firme no centro do botão AUDIO, não a borda
2. **Central muito "fria"**: abra a porta pra ativar a lâmpada interna + central (desperta de suspend profundo), tenta de novo
3. **Combo diferente na sua safra**: safras bem antigas podem precisar de `AUDIO + HOME` ou `HOME 5s`. Teste combinações
4. **Puxar fusível do radio por 15-20 min**: força desligamento completo da central. Religa o fusível, carro liga → combo deve funcionar

### "Quer reiniciar?" aparece mas confirmar não faz nada
Toque exatamente no botão OK (não "Cancelar"). Confirma visualmente que você acertou. Se persistir, veja [`07-rollback.md § Rollback de emergência`](07-rollback.md#rollback-de-emergência).

---

## § Pacote não aplica

### Fluxo OTA começa mas aborta
Logs no pendrive após deploy mostram motivo. Procura:

```bash
cat /run/media/<user>/HONDA_OTA/result.log
# Esperado: "2026/XX/XX : OK"
# Se mostrar "FAIL" ou errado:
cat /run/media/<user>/HONDA_OTA/install-0040.log  # (ou qualquer *.log)
```

Causas comuns:
- `signature verification failed`: pacote não assinado com testkey AOSP. Verifique `build.py`.
- `no partition APP`: edify falhou ao montar. Pode indicar que o recovery da sua safra é diferente.
- `set_perm failed`: faltou busybox embarcado. Confirme no overlay.

### Pacote aceito mas APK não aparece em `/system/`
Logs do `install-0040.log` devem mostrar `post-install-check` com `AutoOk.apk` listado. Se não, o `package_extract_file` falhou — rebuilda e tenta de novo.

---

## § OTA trava no meio

### Barra de progresso parada em 29% por minutos
Normal! A fase 29% é geralmente o `SystemUpdate.apk` copiando o pacote de `/mnt/usbdrive1` para `/data/system-update/`. Pode levar até 5-10 min dependendo do tamanho (pacotes grandes de dump raw demoram mais).

**Espera pelo menos 15 minutos antes de concluir que travou.**

Se travou de verdade:
1. **NÃO desliga o carro de qualquer jeito.** Deixa processar.
2. Se precisar interromper: puxa fusível do radio por 15 min.
3. Nunca interrompa durante escrita do /system — pode brickar.

---

## § Boot loop (CRÍTICO)

**Cenário:** central reinicia infinitamente após deploy OTA.

### 1. Mantém a calma
Boot loop sem acesso ao bootloader normal **ainda tem rota de recuperação**: o recovery continua acessível via combo + pendrive.

### 2. Deploy do ROLLBACK URGENTE

```bash
# No PC
sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sda
```

### 3. No carro
1. Pendrive na porta frontal
2. **AUDIO 5s + confirmar** (central vai estar em algum estado anormal, mas o combo ainda deve funcionar — ele é interpretado pelo bootloader, não pelo Android)
3. Recovery vai pegar o rollback automaticamente
4. ~2-3 min: rollback aplica
5. Central reinicia normal

### 4. Se o combo AUDIO 5s nem responde (central em recovery loop)
- **Puxa fusível do radio** por 15-20 min no fuse box interno
- Religa o fusível, religa o carro, tenta combo + rollback
- Ainda não funciona: **desconecta a bateria** (negativo) por 30 min
- Nuclear option: **troca da central** (R$ 1.000-2.000 na concessionária)

---

## § APK não dispara (aviso continua precisando clique manual)

**Cenário:** OTA aplicou com sucesso, mas aviso continua precisando toque humano.

### 1. Verifica se o APK está instalado
Via adb (se tiver essa rota):
```bash
adb shell "ls -la /system/app/AutoOk.apk /system/xbin/su"
```

Esperado:
```
-rw-r--r-- 1 root root 16890 ... AutoOk.apk
-rwsr-sr-x 1 root root 133472 ... su
```

Se faltam: deploy não aplicou. Repete.

### 2. Verifica se o Service está ativo
```bash
adb shell "ps | grep khalleb.civichmi"
```

Deve mostrar processo `com.khalleb.civichmi.autook`.

### 3. Verifica os logs do APK
```bash
adb shell "su -c 'cat /data/data/com.khalleb.civichmi.autook/files/autook.log'"
```

Deve mostrar linhas tipo `aviso detectado` e `tap ok=true`.

Se o log existe mas não tem `aviso detectado`:
- **Needle do logcat errado**: sua safra pode ter nome diferente da `OpeningDivideActivity`. Verifica via:
  ```bash
  adb shell "su -c 'logcat -v brief ActivityManager:I *:S'" | grep -i disclaimer
  ```
  Pega o nome real, atualiza `AVISO_ACTIVITY_NAME` em `AutoOkConfig.java`.

Se o log mostra `aviso detectado` mas `tap ok=false`:
- `su` não está funcionando. Testa `adb shell su -c id` — deve mostrar `uid=0(root)`.

Se o log mostra `tap ok=true` mas o aviso continua:
- **Coord errada**: tap acerta um pixel que não é o botão OK. Veja [`03-descobrindo-sua-safra.md § 4`](03-descobrindo-sua-safra.md) pra ajustar.

### 4. Verifica permissões
```bash
adb shell "pm list packages | grep khalleb"
# Deve retornar: package:com.khalleb.civichmi.autook
```

Se não listar: APK está em `/system/app/` mas não foi instalado como package. Pode ser signature. Verifica assinatura.

---

## § Tap errado (aviso some mas trava algo)

**Cenário:** aviso desaparece, mas depois do tap, aparece outra tela estranha ou o launcher não carrega direito.

Isso significa que o tap acertou um ponto fora do botão OK. Possíveis causas:
- Resolução da sua tela ≠ 800×480. Confere no menu de serviço.
- Layout do aviso ligeiramente diferente na sua safra.

Fix: ajustar `BUTTON_OK_X` e `BUTTON_OK_Y` em `AutoOkConfig.java`.

Pra descobrir coord corretas: [`03-descobrindo-sua-safra.md § 4`](03-descobrindo-sua-safra.md).

---

## § Service morre entre boots

Não deve acontecer na v0.3.0+ do APK (Service é `START_STICKY`, Watchdog recria se morrer, LogcatWatcher reusado entre taps).

Se acontecer:
1. Verifica versão instalada: `autook.log` deve mostrar `versionCode=3` ou maior
2. Se é v0.1 ou v0.2, atualize pra v0.3.0+ (tem o fix do `stopSelf()` e do EPERM)

---

## § CarPlay/Bluetooth param de funcionar

**Isso NÃO deve acontecer.** Nossa modificação é cirúrgica:
- Zero arquivos preexistentes modificados
- Zero alteração em `/system/vendor/`
- Zero mudança em services do Android base

Se parou de funcionar após deploy, suspeitar de:
1. **OTA aplicou mal**: APK pode ter conflitado com whitelist Mitsubishi. Deploy do ROLLBACK e teste de novo.
2. **Coincidência**: pode ter sido problema separado (CarPlay flaky, Bluetooth do celular, etc). Teste com outro celular, outro cabo.
3. **Rollback + re-test**: se depois do rollback os serviços voltam, nossa mod é a causa — abre issue.

---

## Coletar diagnóstico pra abrir issue

Se nada aqui resolveu, abre issue no [GitHub](https://github.com/khalleb/honda-civic-headunit/issues) com:

1. **Safra**: DA version + mercado (`1.F187.16 BR`, `1.F1A5.15 US`, etc.)
2. **Logs do deploy**: `result.log` + `install-*.log` do pendrive
3. **Logcat da central** (se conseguir):
   ```bash
   adb shell "su -c 'logcat -d -v brief'" > logcat-full.txt
   ```
4. **Log do APK**:
   ```bash
   adb shell "su -c 'cat /data/data/com.khalleb.civichmi.autook/files/autook.log'" > autook.log
   ```
5. **Comportamento observado**: antes vs depois do deploy, em que ciclo começou, se é intermitente ou sempre.

---

## Rede de segurança: pacote de emergência no porta-luvas

Deixa um pendrive extra, formatado FAT32 MSDOS, com pacote ROLLBACK carregado, no porta-luvas do carro. Em uma emergência (ex: carro travou em viagem), você pluga + AUDIO 5s + confirma, e tudo volta ao normal em 5 min.

Custa R$ 20 um pendrive. Dá paz de espírito permanente.
