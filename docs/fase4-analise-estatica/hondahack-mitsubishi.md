# Análise estática do HondaHack — fluxo para central Mitsubishi

Primeira passada de análise estática no `HondaHack.apk` decodificado (pacote `cn.autohack.hondahack`, 3.7 MB, feita em 2026-10-15). O KB (seção 4quater) já tinha o resumo do algoritmo inferido pelas strings; este documento aprofunda **como o HondaHack lida com central Mitsubishi** especificamente — que é exatamente a nossa (seção 2 do KB atualizado).

APK em `tooling/apks-decoded/HondaHack/`, obtido via `root-honda/packages/HondaHack.apk` + `apktool d` (seção 5 do KB).

## 1. O código Java está inacessível (confirmado)

O KB já apontava isso. Agora confirmado em diff:

- `smali/` contém **só** `com/tencent/StubShell` e `com/tencent/bugly/*` — o packer Tencent Legu, nada de código do HondaHack.
- Código real do app está em `lib/armeabi/mix.dex` e `lib/armeabi/mixz.dex` (DEX criptografados), com as libs `libshella-2.10.7.1.so` e `libshellx-2.10.7.1.so` fazendo decryption no startup.
- `strings mix.dex | grep -i mitsubishi` → vazio. Confirma que o DEX não é lido como texto plano.

**Decisão:** não desempacotar o Tencent Legu (está fora do escopo do projeto e já temos o que precisamos pelos resources). Qualquer coisa útil está em `res/`, `res/raw/`, ou `AndroidManifest.xml`.

## 2. AndroidManifest.xml do HondaHack — activities declaradas

```
cn.autohack.hondahack.MainActivity          (launcher)
cn.autohack.hondahack.RemapKeysActivity
cn.autohack.hondahack.SdcardActivity
cn.autohack.hondahack.SettingsActivity
cn.autohack.hondahack.AppsActivity
cn.autohack.hondahack.StartupActivity
cn.autohack.hondahack.NavigatorActivity
cn.autohack.hondahack.FixActivity
cn.autohack.hondahack.AboutActivity
```

Receivers e services não aparecem exportados no Manifest; devem estar registrados em runtime pelo DEX empacotado. **`StartupActivity` + a feature `auto_confirm_agreement` descrita nas strings** confirmam que o auto-OK é o componente de "Startup".

Entry point: `com.tencent.StubShell.TxAppEntry` → carrega `cn.autohack.hondahack.MyApplication` a partir do DEX empacotado.

## 3. `res/raw/` — ouro puro

O resource bruto contém scripts e dados que **não passam pelo packer**:

| Arquivo | Função |
|---|---|
| `install_mitsubishi.sh` | Instalador para central Mitsubishi (nossa) — ver seção 4 |
| `install_clarion.sh` | Instalador para central Clarion (irmã, não é a nossa) |
| `whitelist_mitsubishi.xml` | Template de whitelist Mitsubishi (386 linhas) |
| `whitelist_clarion.xml` | Template de whitelist Clarion (355 linhas) |
| `factory_reset.sh` | Reset de fábrica — não analisado em detalhe (perigoso) |
| `platform.xml` | AOSP platform permissions override |
| `busybox` | Binário busybox para shell POSIX amplo |
| `pcm16bit.bin` | Áudio em PCM 16-bit (uso desconhecido) |
| `speed_meters.json` | Temas visuais do velocímetro (feature de dashboard) |
| `honda_installer.apk` | APK secundário que o HondaHack instala — ainda não analisado |

**`install_mitsubishi.sh`, `whitelist_mitsubishi.xml` e `install_clarion.sh` resolvem a maior parte da dúvida da seção 6 do nosso APK auto-OK** (como instalar como system app).

## 4. `install_mitsubishi.sh` — passo a passo decifrado

Reproduzindo o script, com comentários. Executado com argumentos `$1 = /sdcard/caminho/app.apk`, `$2 = <nome do pacote>`, `$3 = <signature hash>`, `$4 = yes|no` (force reinstall), `$5 = yes|no` (revert).

```sh
#!/system/bin/sh
echo $@
package=$2
sig=$3
force=$4
revert=$5

chmod 666 /data/data/whitelist-1.0.xml

if [ "$force" == "no" ] && [ $(grep -c "$package" /data/data/whitelist-1.0.xml) -ne 0 ]; then
    echo "Package name already exists in whitelist."
else
    mkdir /data/local/tmp/autohack
    cp /data/data/whitelist-1.0.xml /data/local/tmp/autohack
    chmod 666 /data/local/tmp/autohack/whitelist-1.0.xml

    # Remove as duas tags de fechamento para inserir uma <application> nova
    cat /data/local/tmp/autohack/whitelist-1.0.xml \
        | grep -v "</applicationLists" \
        | grep -v "</whiteList" \
        > /data/local/tmp/autohack/whitelist-1.0-new.xml

    cat >> /data/local/tmp/autohack/whitelist-1.0-new.xml <<EOF
        <application>
            <property>
                <name>$package</name>
                <package>$package</package>
                <versionCode>1-999999999</versionCode>
                <keyStoreLists>
EOF

    for signature in ${sig[@]}; do
        echo "<keyStore>$signature</keyStore>" >> ...-new.xml
    done

    cat >> ...-new.xml <<EOF
                </keyStoreLists>
            </property>
            <controlData>
                <withAudio>without</withAudio>
                <audioStreamType>STREAM_ADA_GUIDE</audioStreamType>
                <regulation>null</regulation>
                <revert>$revert</revert>
            </controlData>
        </application>
    </applicationLists>
</whiteList>
EOF

    cp /data/local/tmp/autohack/whitelist-1.0-new.xml /data/data/whitelist-1.0.xml
    chown system:system /data/data/whitelist-1.0.xml
fi

chmod 666 $1
pm install -r "$1"
```

**Decisões derivadas para o nosso APK auto-OK:**

| Pergunta | Resposta |
|---|---|
| Onde fica a whitelist na central Mitsubishi? | `/data/data/whitelist-1.0.xml` |
| Qual permissão de arquivo? | `0666`, dono `system:system` |
| Preciso de root para editar? | Sim (chmod + chown system:system) |
| Como adicionar nosso pacote? | Append de bloco `<application>` dentro de `</applicationLists>` |
| Qual signature usar? | A hash do keystore que assinou nosso APK (ver seção 6) |
| Preciso instalar como `/system/app/`? | **Não necessariamente.** O HondaHack usa `pm install -r "$1"` em modo user. Ver seção 7. |

**Isso é uma mudança significativa em relação à premissa anterior do nosso APK.** O README do `our-apk/` diz que o APK precisa ir em `/system/app/` por causa de `READ_LOGS`. Mas o HondaHack **não** faz isso — ele instala como app comum (user-space), **após** adicionar a assinatura à whitelist. O `READ_LOGS` funciona porque a assinatura passa a estar na whitelist Mitsubishi — não porque o APK é "system".

Vale re-verificar a semântica de `READ_LOGS` em Android 4.2.2 nesse contexto — pode ser que a whitelist Mitsubishi dê a mesma elevação que `signature|system` em runtime. Se for isso, o nosso APK auto-OK não precisa virar system app, só precisa estar na whitelist + rodar com `su`.

## 5. Estrutura da whitelist Mitsubishi — schema real

Trecho de `whitelist_mitsubishi.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<whiteList>
    <formatVersion>1.0</formatVersion>
    <contentVersion>1.5</contentVersion>
    <applicationLists>

        <application>
            <property>
                <name>Clock</name>
                <package>com.android.deskclock</package>
                <versionCode>1-999999999</versionCode>
                <keyStoreLists>
                    <keyStore>null</keyStore>
                </keyStoreLists>
            </property>
            <controlData>
                <withAudio>without</withAudio>
                <audioStreamType>null</audioStreamType>
                <regulation>speedtrigger</regulation>
                <revert>no</revert>
            </controlData>
        </application>

        <!-- ... mais 21 <application> ... -->

    </applicationLists>
</whiteList>
```

### Pacotes autorizados pela whitelist Mitsubishi (22 total)

**AOSP base (15):**
```
com.android.browser · com.android.calculator2 · com.android.calendar ·
com.android.certinstaller · com.android.contacts · com.android.deskclock ·
com.android.gallery3d · com.android.music · com.android.packageinstaller ·
com.android.providers.downloads · com.android.providers.downloads.ui ·
com.android.quicksearchbox · com.android.settings ·
com.android.wallpaper.livepicker
```

**Honda proprietários (6):**
```
com.honda.appupdater · com.honda.displayaudio.navi · com.honda.displayaudio.whitelist ·
com.honda.dummydisplayaudio.system.vehicleinfo · com.honda.hondaappstore ·
com.honda.telematics.core
```

Novos pacotes Honda descobertos aqui (não estavam no KB): `com.honda.displayaudio.navi`, `com.honda.telematics.core`, `com.honda.appupdater`, `com.honda.hondaappstore`, `com.honda.dummydisplayaudio.system.vehicleinfo`.

**Terceiros (2):**
```
com.aha.android.app                    (Aha Radio)
com.yesway.ycarstore.acura             (YESWAY apps — Acura; confirma firmware base compartilhado)
```

### Campos de `controlData` — reverse-engineering parcial

| Campo | Valores vistos | Significado inferido |
|---|---|---|
| `withAudio` | `with` / `without` | Se o app toca áudio |
| `audioStreamType` | `null`, `STREAM_ADA_GUIDE` | Tipo de stream (padrão Android) |
| `regulation` | `null`, `speedtrigger`, `park`, `park&speedtrigger` | **Trava DD VSS** — regula quando o app pode interagir (parado, trafegando) |
| `revert` | `yes` / `no` | Se o app pode ser removido pela whitelist |

**`regulation`** é a trava "distracted driver" (seção 3 do KB, trava b). O HondaHack usa `null` por padrão quando adiciona um pacote — ou seja, **sem restrição por movimento**. Interessante para quando o nosso APK precisar rodar na partida, mas provavelmente não é relevante para o auto-OK (que roda em `BOOT_COMPLETED` antes do carro estar em movimento).

## 6. Comparação com whitelist Clarion

Para completeza (não é a nossa central, mas serve de comparação):

- **Clarion:** whitelist em `/data/system/whitelist.xml` (sem versão no nome)
- **Mitsubishi:** whitelist em `/data/data/whitelist-1.0.xml`

Diff dos pacotes autorizados (Clarion → Mitsubishi):

- Clarion tem `cn.autohack.hondahack` já na whitelist (!!! — significa que o HondaHack foi pré-aprovado em firmware Clarion em algum momento)
- Mitsubishi tem a mais: `com.honda.hondaappstore`, `com.honda.dummydisplayaudio.system.vehicleinfo`, `com.yesway.ycarstore.acura`

## 7. Implicações para o nosso APK auto-OK

Revisão da estratégia do `our-apk/README.md` à luz desta análise:

### 7.1 Reconsiderar a necessidade de instalar como system app

O README atual diz:
> `READ_LOGS` em API 17 é `signature|system` — por isso o APK só vai funcionar instalado como system app, não como user app.

O HondaHack **contradiz** essa premissa — ele instala como user app via `pm install -r`, apenas após inserir sua signature na whitelist Mitsubishi. Hipóteses para investigar quando tivermos ADB:

- **(a)** A whitelist Mitsubishi concede permissões adicionais em runtime, incluindo `READ_LOGS`. Nesse caso basta estar na whitelist, não precisa ser `/system/app/`.
- **(b)** `READ_LOGS` em Android 4.2.2 ainda era disponível para user apps (foi em API 16 que o Google restringiu, mas firmware customizado Mitsubishi pode ter removido a restrição).
- **(c)** O HondaHack usa `su -c "logcat"` para contornar a restrição (seria mais invasivo mas plausível).

**Ação:** manter o Manifest atual (`uses-permission READ_LOGS`) e, quando tivermos ADB, testar o APK como user app primeiro antes de assumir instalação em `/system/app/`.

### 7.2 Fluxo de instalação resultante

Em vez da versão do README atual (`cp /sdcard/.apk /system/app/...`), o fluxo real que o HondaHack usa — e que vale copiar — é:

```
1. Rootear a central (seção 6 do KB, via root-honda)
2. Como root:
   a. chmod 666 /data/data/whitelist-1.0.xml
   b. Editar o XML inserindo o <application> do nosso pacote (schema seção 4)
   c. chown system:system /data/data/whitelist-1.0.xml
3. adb push nosso-apk.apk /sdcard/
4. adb shell pm install -r /sdcard/nosso-apk.apk
```

**Benefícios vs. instalar em `/system/app/`:**
- Reversível por `pm uninstall` + edit da whitelist
- Não precisa remount `/system`
- Updates do nosso APK via `pm install -r` em segundos
- Mais seguro (não mexe em `/system`, menor chance de brick)

### 7.3 Signature a inserir na whitelist

A whitelist tem `<keyStore>` com valor que parece ser SHA-1 do keystore do signer, mas o template usa `null` para apps AOSP (não checagem). Para o nosso APK precisaremos:

- Assinar o APK com um keystore próprio (chave debug ou de release)
- Extrair a signature com `GetAndroidSig.jar` (mencionado no KB) ou `keytool`
- Inserir essa signature na whitelist

Alternativa: usar `null` como valor de `keyStore` para "sem checagem" — não testado no firmware Mitsubishi, pode não ser aceito.

## 8. Perguntas em aberto para a próxima rodada

1. ✅ **Resolvida** — `honda_installer.apk` analisado em `honda-installer.md`. Ele é um helper permanente instalado em `/system/app/`, roda `install_mitsubishi.sh` com argumentos construídos via UI, usa libsuperuser do Chainfire, detecta Mitsubishi vs Clarion por fingerprint de arquivo (`/system/etc/factory_reset.sh`). Reduz muito o escopo do nosso APK auto-OK.
2. **Testar na central** (quando houver ADB) se adicionar `cn.autohack.hondahack` + signature na whitelist Mitsubishi + `pm install` funciona para user app com `READ_LOGS`. Se funcionar, a hipótese 7.1-(a) é confirmada e nosso APK não precisa ser system app.
3. **Lista completa de pacotes `com.honda.*`** no firmware do EXL BR — pela whitelist aqui, existem `com.honda.hondaappstore` e `com.honda.appupdater`, mas eles não apareceram no scroll do menu Version (seção 5.3 do `fase1-reconhecimento/achados-2026-10-15.md`). Pode ter sido perdido entre fotos, ou pode ser que o EXL BR não tenha esses apps.

## 9. Resumo prático

Os cinco pontos acionáveis:

1. ✅ **Instalador Mitsubishi decifrado** — já temos a receita exata.
2. ✅ **Schema da whitelist mapeado** — know how para injetar nosso pacote.
3. 🔄 **Nosso APK auto-OK pode ser user app**, não necessariamente system — reverter READ_LOGS no README do `our-apk/` quando confirmado em runtime.
4. ⏳ **Signature do nosso APK** — precisamos de keystore próprio + extração de signature (fase 5 do roadmap).
5. ⏳ **`honda_installer.apk`** aguardando análise.
