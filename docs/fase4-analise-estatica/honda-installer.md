# Análise estática do `honda_installer.apk`

Segunda passada da Fase 4 (2026-10-15). O `honda_installer.apk` fica embutido como resource bruto dentro do `HondaHack.apk` (ver `hondahack-mitsubishi.md` seção 3). É o único APK do ecossistema do `@codeage` cujo código Java **é legível** depois do apktool.

APK fonte: `tooling/apks-decoded/HondaHack/res/raw/honda_installer.apk`.
Descompilado em: `tooling/apks-decoded/honda_installer/`.

## 1. Identificação

| Campo | Valor |
|---|---|
| Pacote | `cn.autohack.hondainstaller` |
| `versionName` | `2.1` |
| `versionCode` | `1` |
| `minSdkVersion` | 17 ✅ (bate com a central) |
| `targetSdkVersion` | 17 |
| Autor (strings) | `@codeage`, email `codeage@hotmail.com`, QQ `199080868` |
| Copyright | `© 2018 @codeage` |
| Permissões | `WRITE_EXTERNAL_STORAGE`, `INTERNET` — **nenhuma** permissão sensível declarada |
| Entry point | `cn.autohack.hondainstaller.MyApplication` + `MainActivity` |

Observação sobre permissões: o manifest não declara nem `ACCESS_SUPERUSER` nem `READ_LOGS`. **O Installer não precisa dessas permissões** — ele chama `su` diretamente via `Runtime.getRuntime().exec()` (padrão libsuperuser do Chainfire), bypassando o controle de permissões do PackageManager. Isso só funciona porque ele é instalado como **system app** (ver seção 5).

Ofuscação: ProGuard leve. Classes renomeadas (`a.smali`, `b.smali`, `cn/autohack/a/`), mas **sem packer de criptografia** (diferente do HondaHack principal, que usa Tencent Legu). Dá para ler o código.

## 2. Papel do Installer no ecossistema

Pelas strings de `res/values/strings.xml` já ficou claro, mas vale cristalizar:

```
install_apk_title       → "Install an app"
install_hondahack_title → "Install Honda Hack"
uninstall_self_title    → "Uninstall Honda Installer"
```

O `honda_installer` é um **helper permanente** instalado em `/system/app/` da central. Depois que a central foi rooteada (via `root-honda`), o usuário interage com ele para:

1. **Instalar o `HondaHack.apk`** (opção pré-pronta: baixa via URL hardcoded + instala).
2. **Instalar qualquer outro APK** (file picker → seleciona APK em `/sdcard/Download`, `/usbdrive1`, `/usbdrive2` ou `/usbdrive3` → ele extrai signature + adiciona na whitelist + `pm install`).
3. **Desinstalar a si próprio** (quando o usuário quer voltar a central ao estado "pré-mod" sem factory reset).

Isso explica a separação arquitetural: **o Honda Installer é o único componente que precisa ser system app**; HondaHack, nosso APK auto-OK e qualquer outro ficam como user apps.

## 3. Detecção CLARION vs MITSUBISHI — enum + fingerprint por arquivo

Enum em `smali/cn/autohack/a/d.smali` (confirmado no header `.class final enum Lcn/autohack/a/d;`):

```java
enum HeadUnitType {   // nome original obfuscado para 'd'
    MITSUBISHI,       // valor 'a'
    CLARION           // valor 'b'
}
```

A classe `Lcn/autohack/a/b;` (singleton) detecta o tipo no construtor:

```java
if (! new File("/system/etc/factory_reset.sh").exists()) {
    this.type = HeadUnitType.MITSUBISHI;
} else {
    this.type = HeadUnitType.CLARION;
}
```

**Chave da detecção:** o `factory_reset.sh` só existe em `/system/etc/` em firmware Clarion. Mitsubishi não tem. Fingerprint by file.

Para nossa central Mitsubishi, significa que a lógica do Installer sempre entra no ramo "MITSUBISHI" — que é a parte que importa pra gente.

## 4. Fluxo de instalação de APK na central Mitsubishi

Classe `cn.autohack.hondainstaller.c` (uma `AsyncTask` que executa a instalação em background). O método `doInBackground()` (`a([Ljava/lang/Void;)Ljava/lang/Void;`) faz:

1. Log info `"Normal installation"`.
2. Executa via `su`: `pm set-install-location 0` — força instalação na memória interna.
3. Executa via `su`: `chmod 777 <apk_path> 2>&1`.
4. Monta comando com template `"%s \"%s\" %s \"%s\" %s %s 2>&1"` e argumentos:
   - `%s` ← caminho do script (`install_mitsubishi.sh` ou `install_clarion.sh` extraído dos resources para `/data/data/.../cache`)
   - `"%s"` ← caminho do APK alvo
   - `%s` ← nome do pacote alvo (extraído do APK via `PackageManager`)
   - `"%s"` ← signature hash (extraída lendo `META-INF/CERT.RSA` do ZIP do APK, ver seção 5)
   - `%s` ← `yes` ou `no` (force reinstall)
   - `%s` ← `yes` ou `no` (revert) — por padrão `no` baseado nos literais vistos no smali
5. Executa a linha via `su` (`La/a/a/c$a;->a([Ljava/lang/String;)Ljava/util/List;` — `Shell.SU.run()` do libsuperuser).
6. `Thread.sleep` enquanto espera o script terminar.
7. UI atualiza mostrando sucesso/falha.

Isso bate exatamente com a assinatura esperada pelo `install_mitsubishi.sh` que a gente leu em `hondahack-mitsubishi.md` seção 4:

```sh
install_mitsubishi.sh <apk_path> <package> <signature> <force> <revert>
```

Pronto: o Installer é a UI em cima do script shell. O script faz todo o trabalho de edição da whitelist e `pm install`.

## 5. Extração de signature do APK alvo

Classe `cn.autohack.a.a` (helper) lê o APK como ZIP (lib `java.util.zip`) e localiza o arquivo em `META-INF/` que termina em `.RSA` ou `.DSA`. Dessa entrada, extrai a cadeia de certificados X.509 e calcula um hash SHA (strings vistas no smali: `"META-INF/"`, `"Package has mismatched certificates at entry "`, `"Package has no certificates; ignoring!"` — essas mensagens vêm diretamente de `android.content.pm.PackageParser` do AOSP, confirmando que o código reaproveita o `PackageParser` para extrair a assinatura).

**Para o nosso APK auto-OK:** quando chegarmos à Fase 7, precisamos:

1. Assinar o APK com um keystore próprio (debug ou release — `keytool` + `jarsigner` ou `apksigner`).
2. Extrair o mesmo hash SHA que o Installer calcula — ou simplesmente deixar o Installer calcular para a gente (ele faz como UI, não precisamos replicar).
3. Inserir essa signature na whitelist via o próprio Installer (`Install an app` → seleciona nosso APK).

Então na prática, **não precisamos replicar a extração de signature**: usar o Installer como UI é o caminho reto. Alternativa: `GetAndroidSig.jar` mencionado no KB para extração offline (mesmo resultado).

## 6. Fluxo de uninstall self (`Lcn/autohack/hondainstaller/d$2;`)

Interessante por mostrar como ele remonta `/system` RW/RO:

```java
String[] cmds = {
    "mount -o remount,rw,sync /system",
    String.format("rm %s", getActivity().getPackageCodePath()),
    "mount -o remount,ro /system"
};
// executa via cn.autohack.hondainstaller.g (AsyncTask wrapper em libsuperuser)
```

`getPackageCodePath()` retorna `/system/app/HondaInstaller/HondaInstaller.apk` (ou similar — Android 4.2.2 pode ter sido `/system/app/HondaInstaller.apk` direto).

Esse é o template exato que a gente deve usar na nossa Fase 6/7 se precisarmos remontar `/system` RW em algum ponto:

```sh
mount -o remount,rw,sync /system   # abre para escrita
# ... faz o que precisa ...
mount -o remount,ro /system        # fecha
```

Importante: **não esquecer de remontar RO**. Deixar RW permanente é fonte conhecida de brick (corrompe `/system` em power loss).

## 7. Como o Installer é instalado inicialmente

Não analisado em código, porque é feito pelo `root.sh`/`nefarious.sh` do `root-honda` (sequência documentada no KB seção 4quater), não pelo próprio Installer. Fluxo esperado (consistente com `install_hondahack_summary`):

1. Rootear a central via dirtyCOW (fase 6 do KB).
2. Via ADB shell + su: `cp honda_installer.apk /system/app/HondaInstaller.apk`.
3. Reboot.
4. Agora o Installer aparece no launcher como ícone "Honda Installer".
5. Daí em diante, instalar/desinstalar outros APKs é via UI dele, sem precisar reconectar ADB.

Essa é a "unlock story" completa do ecossistema `@codeage` — root uma vez via ADB, depois tudo via UI do Installer.

## 8. Validação cruzada com strings do UI

Strings relevantes vistas em `strings.xml` e confirmadas nos smali:

- `apk_signature_error`: "Failed to obtain the signature of the apk file. The file is invalid or corrupt." → aparece quando a extração META-INF/CERT.RSA falha.
- `reboot_to_install`: "The whitelist has been updated but will not take effect before rebooting. Please restart the head unit..." → confirma que **o `com.mitsubishielectric.ada.appservice.whitelist` lê o `whitelist-1.0.xml` só no boot**. Qualquer edição exige reboot. Isso é importante para o nosso fluxo: assinatura adicionada → reboot obrigatório antes do `pm install` surtir efeito.
- `su_not_available`: "Failed to get root access. Make sure your head unit is rooted properly." → se o Installer rodar em central não rooteada, falha imediatamente (consistente com uso de libsuperuser).
- `not_system_app`: "Honda Installer was not installed as system app." → o Installer **verifica em runtime** se está em `/system/app/`. Provável check: `getApplicationInfo().flags & ApplicationInfo.FLAG_SYSTEM`.
- `install_hondahack_summary`: menção explícita a "automatically click the confirmation button at startup" — **confirma textualmente** que o auto-OK (nossa feature-alvo) é feature do HondaHack principal.

## 9. Implicações para o `our-apk/`

Resumo das decisões que esta análise confirma ou altera:

| Decisão | Status |
|---|---|
| Nosso APK pode ser instalado como user app (via `pm install`) | ✅ Confirmado (o HondaHack vai assim) |
| Precisamos assinar o APK com keystore próprio | ✅ Sim; qualquer keystore serve |
| Precisamos extrair signature do nosso APK | ⚠️ Opcional — se usarmos o Honda Installer como UI, ele faz; se automatizarmos, precisa |
| Precisamos adicionar signature na whitelist Mitsubishi antes do `pm install` | ✅ Sim; `/data/data/whitelist-1.0.xml` |
| Precisa reboot entre edit da whitelist e `pm install` | ✅ Confirmado por string `reboot_to_install` |
| Precisamos nós mesmos remontar `/system` RW | ❌ **Não** — só o Honda Installer precisa (ele é system app); nosso APK é user app |
| `READ_LOGS` em user app na central Mitsubishi funciona? | ⚠️ Ainda não confirmado — testar quando ADB subir |

Linha única: **nosso APK auto-OK fica mais simples do que o README do `our-apk/` imaginava**. Sem `/system/app/`, sem remount, sem edição manual de whitelist em código próprio — tudo isso vive no Installer que a gente ganha de graça.

## 10. Perguntas em aberto para a próxima rodada

1. **O `honda_installer.apk 2.1` ainda funciona em firmware `1.F187.16`?** O `@codeage` publicou essa versão em 2018; firmware da central dele é 2016. Compatibilidade esperada mas não confirmada.
2. **URL de download do HondaHack dentro do Installer** — não extraí ainda. Pode estar em uma string hardcoded em `MainActivity` ou `d.smali`.
3. **O Installer altera arquivos fora de `/data/data/whitelist-1.0.xml`?** Pela análise, não parece. Confirmar com `strings` focado em paths.
4. **O Installer tem telemetria para o `@codeage`?** `uses-permission INTERNET` + autor com email + QQ group levanta a questão. Vale um grep em URLs no smali antes de usar.

Esses três últimos são tarefas pra uma rodada de 15 min quando quisermos esgotar a análise.
