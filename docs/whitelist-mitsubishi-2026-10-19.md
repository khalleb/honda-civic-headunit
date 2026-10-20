# Whitelist Mitsubishi — análise estática completa

**Data:** 2026-10-19
**Ferramenta:** REA (`morluto/rea` v6.7.0) + JADX headless 0.7.1 + baksmali/smali 2.5.2
**Pergunta de partida:** se o PowerManager não re-inicia nosso Service após LP0, pode ser porque não estamos na "whitelist Mitsubishi"? Adicionar nosso APK à whitelist elimina o workaround da v0.4.0?
**Resposta curta:** **não.** A whitelist Mitsubishi é um mecanismo de UX de instalação de apps, consultado apenas por `AppManager.apk` e `FileManager.apk`. O PowerManager usa um padrão pub/sub puro via broadcast — qualquer app que registre o receiver certo participa. Nossa v0.4.0 já segue esse padrão.

Este documento preserva o fluxo completo da whitelist e do recovery pós-LP0, mesmo que a rota de "entrar na whitelist" não resolva o nosso workaround — porque entender esse subsistema abre outras oportunidades (ex: metadata amigável no AppManager, uso de outros broadcasts do PowerManager).

---

## Sumário executivo

| Pergunta | Resposta | Evidência |
|---|---|---|
| Quem define a whitelist? | O APK `com.honda.displayaudio.whitelist` (14 KB em `/system/vendor/etc/honda/`, não dumpado), via ContentProvider que serve um ZIP contendo `whitelist-1.0.xml` | `WhitelistContentResolver.getWhitelistZip()` (abaixo) |
| Onde o XML vive em runtime? | `/data/data/whitelist-1.0.xml` (literal, direto no root de `/data/data/` — o `WhitelistApService` roda com `android.uid.system`) | `WhitelistUtil.WHITELIST_FILE_REGEX`, `WhitelistFileManager.WHITELIST_DIRECTORY` |
| Como se atualiza? | Boot: `WhitelistApService.onCreate` → consulta content provider → se `contentVersion` novo > atual, substitui o arquivo local. Runtime: `PACKAGE_REPLACED` do `com.honda.displayaudio.whitelist` dispara `WhitelistUpdateService` que faz o mesmo | `WhitelistContentResolver.updateWhitelist()`, `WhitelistContentReceiver.onReceive()` |
| Formato do XML? | `<whiteList><contentVersion/><controlData><application>…</application>…</controlData></whiteList>` com `<package>`, `<versionCode>`, `<keyStore>`, `<audioStreamType>`, `<withAudio>`, `<regulation>`, `<revert>` | `WhitelistXmlParser` fields literais no smali |
| Quem consulta a whitelist? | Só UI: `AppManager.apk` (gerenciador) chama `getApplicationName`, `getAudioInfo`, `getRegulation`, `getRevert`. `FileManager.apk` (telas de instalação do USB). **Nenhum HMI service, nenhum PowerManager, nenhum launcher.** | grep em 120 odex deodexados — só 3 consumidores |
| Entrar na whitelist resolve LP0? | **Não.** PowerManager não consulta whitelist. Reinício pós-LP0 é via broadcast `ACTION_HMI_SERVICE_START` que todo app pode escutar sem permissão | `PowerManagerBroadcastSender`, 33 APKs listeners |

---

## 1. Como analisamos

### 1.1 Preparação

Toda a vendor-app da Mitsubishi é **odex-only** (pré-dexed). Para o JADX/REA abrir qualquer APK, precisamos:

1. `tooling/deodex/deodex-apk.sh <APK>` — monta bootclasspath com `system-framework/*.odex` + `vendor-framework/*.odex`, roda `baksmali deodex`, `smali assemble`, injeta `classes.dex` numa cópia do APK.
2. Para bibliotecas (`vendor-framework/*.jar`), o REA rejeita `.jar` puro — então criamos um "APK wrapper" copiando o manifest de um APK vazio (o próprio WhitelistApService) e trocando o `classes.dex`. Hack simples, funciona.

### 1.2 Bulk deodex

Para esta análise, foi necessário deodexar os 120 APKs de `vendor-app/` + `vendor-framework/` em bloco para fazer grep global. O workspace em `/tmp/.../scratchpad/bulk-smali/by-apk/<Name>/com/mitsubishielectric/.../` ficou pronto em ~2 min.

### 1.3 Reproduzir

```bash
export REA_JADX_MCP_JAR=~/.local/share/rea/android/jadx-headless-mcp-0.7.1-all.jar

./tooling/deodex/deodex-apk.sh tooling/apks-dumped/dump-0040/vendor-app/WhitelistApService.apk

APK=tooling/apks-decoded/WhitelistApService-deodexed.apk
npx -y rea-agents@latest inspect-android-package   "$APK" --json
npx -y rea-agents@latest search-android-classes    "$APK" "" --json
npx -y rea-agents@latest inspect-android-class     "$APK" com.mitsubishielectric.ada.appservice.whitelist.WhitelistApService --json
npx -y rea-agents@latest inspect-android-method    "$APK" com.mitsubishielectric.ada.appservice.whitelist.WhitelistContentResolver updateWhitelist --json
```

Para a lib: deodex `vendor-framework/WhitelistLib.odex` manualmente, injeta `classes.dex` numa cópia da `WhitelistApService-deodexed.apk`, e o REA aceita como APK.

---

## 2. As três entidades

```
                    ┌──────────────────────────────────────────────┐
                    │  Outros apps (AppManager, FileManager, …)    │
                    │  bindService(action=IWhiteListApService) ────┼─────┐
                    └──────────────────────────────────────────────┘     │
                                                                          ▼
┌──────────────────────────────────┐   uses-library   ┌──────────────────────────────┐
│ WhitelistApService.apk (vendor)  │ ───────────────▶ │ WhitelistLib.jar             │
│  — 5 classes shell:              │                  │   (vendor-framework)         │
│   WhitelistApService (binder)    │                  │ — 15 classes de verdade:     │
│   WhitelistContentReceiver       │                  │   IWhitelistApService (AIDL) │
│   WhitelistContentResolver       │                  │   IWhitelistApService$Stub   │
│   WhitelistUpdateService         │                  │   WhitelistFileManager       │
│   R                              │                  │   WhitelistXmlParser         │
│  — sharedUserId=android.uid.system│                 │   WhitelistModel             │
│  — permission VEHICLE_RW         │                  │   WhitelistCriteria          │
└──────────────────────────────────┘                  │   WhitelistUtil              │
            │ onCreate                                │   WhitelistConst             │
            │ updateWhitelist()                       │   enums.{Audio,Regulation,   │
            ▼                                         │     Revert,Stream,Symbol}   │
┌──────────────────────────────────┐                  └──────────────────────────────┘
│ WhitelistContentResolver         │
│  openAssetFileDescriptor(        │
│   "content://com.honda.           │   ContentProvider
│    displayaudio.whitelist/1.0")  │ ───────────────────┐
└──────────────────────────────────┘                    │
                                                        ▼
                            ┌──────────────────────────────────────────┐
                            │ APK com.honda.displayaudio.whitelist.apk │
                            │  — portador do ZIP com whitelist-1.0.xml │
                            │  — path: /system/vendor/etc/honda/       │
                            │  — ~14 KB (per MAPA §7)                  │
                            │  — NÃO ESTÁ NO DUMP ATUAL (gap scan)     │
                            └──────────────────────────────────────────┘
```

### 2.1 WhitelistApService.apk (`com.mitsubishielectric.ada.appservice.whitelist`)

- **Manifest key points:**
  - `android:sharedUserId="android.uid.system"` — roda com UID system.
  - `uses-permission com.mitsubishielectric.ada.permission.VEHICLE_RW`
  - `uses-permission android.permission.WRITE_EXTERNAL_STORAGE`
  - 3 `uses-library`: `explog.lib`, `constext.lib`, `whitelist.lib`.
  - 2 services:
    - `.WhitelistApService` com `intent-filter action=com.mitsubishielectric.ada.appservice.whitelist.IWhiteListApService` (⚠️ note o `WhiteList` com L maiúsculo nesse action — o resto do código usa `IWhitelistApService` com l minúsculo).
    - `.WhitelistUpdateService` protegido por `com.mitsubishielectric.ada.permission.VEHICLE_RW`.
  - 1 receiver: `.WhitelistContentReceiver` escutando `android.intent.action.PACKAGE_REPLACED` com `data scheme=package`.

- **Classes (5):** `R`, `WhitelistApService`, `WhitelistContentReceiver`, `WhitelistContentResolver`, `WhitelistUpdateService`. Zero lógica — todo o trabalho é delegado à lib.

### 2.2 WhitelistLib.jar (`vendor-framework/WhitelistLib.{jar,odex}`)

15 classes carregadas via `<uses-library>`. As de interesse:

| Classe | Papel |
|---|---|
| `IWhitelistApService` (interface AIDL) | 7 métodos públicos (listados abaixo) |
| `IWhitelistApService$Stub` | implementação base do binder |
| `WhitelistFileManager` | lê/grava `/data/data/whitelist-1.0.xml` + `TEMP_whitelist-1.0.xml` |
| `WhitelistXmlParser` | XmlPullParser consumindo as tags |
| `WhitelistModel` | POJO com o conteúdo parseado |
| `WhitelistCriteria` + `WhitelistCriteriaProtocol` | parsers de regras (comma-delimited) |
| `WhitelistUtil` | `isWhitelistXMLFile`, `compareWhitelistContentVersion`, `getContentVersion`, `isExternalPath`, `checkHondaApplication` |
| `WhitelistConst` | 24 constantes (regulation, revert, stream, symbol) |
| `enums.*` | enums tipados dos valores inteiros |

### 2.3 APK portador do XML — `com.honda.displayaudio.whitelist.apk`

**Está citado no MAPA §7 como estando em `/system/vendor/etc/honda/com.honda.displayaudio.whitelist.apk` (~14 KB), mas o deep-scan 0040 não trouxe esse arquivo.** O diretório `system-etc/honda/` nem existe no dump — gap do deep-scan: a próxima rodada deve incluir `/system/vendor/etc/honda/*`.

Pelo que o código deduz, esse APK:
- É um pacote regular (não precisa de código Java — pode ser só manifest + ContentProvider que lê um asset).
- Publica um `ContentProvider` com `authority="com.honda.displayaudio.whitelist"`.
- O path `/1.0` do URI expõe um `AssetFileDescriptor` apontando para um ZIP (asset do APK).
- O ZIP contém **uma entry chamada `whitelist-1.0.xml`** (nome exato — a comparação em `WhitelistUtil.isWhitelistXMLFile` é `filename.equals("whitelist-1.0.xml")`).

---

## 3. Interface pública (AIDL `IWhitelistApService`)

7 métodos expostos via Binder. Qualquer app que faça `bindService` com `action = "com.mitsubishielectric.ada.appservice.whitelist.IWhiteListApService"` pode chamá-los (**sem permissão exigida** no intent-filter):

| Método | Para quê serve |
|---|---|
| `boolean checkInstallPackage(String pkg)` | ⭐ "esse pacote está autorizado?" — **MAS NUNCA é chamado em nenhum APK do shipping** |
| `List<String> getPackageNames(String ???, boolean withAudio)` | enumerar pacotes com/sem áudio |
| `String getApplicationName(String pkg, int versionCode)` | nome amigável do app (ex: "Android Auto") |
| `int getAudioInfo(String pkg, int versionCode)` | 0=sem áudio, 1=com áudio |
| `int getAudioStreamType(String pkg, int versionCode)` | 0=NULL, 1=SYSTEM, 2=ADA_GUIDE_HIGH, 3=VOICE_RECOGNITION, 4=ADA_GUIDE, 5=ADA_GUIDE_LOW, 6=MUSIC |
| `int getRegulation(String pkg, int versionCode)` | 0=NULL, 1=PARKTRIGGER (só com carro parado), 2=SPEEDTRIGGER (só em movimento), 3=PARKSPEEDTRIGGER (ambos) |
| `int getRevert(String pkg, int versionCode)` | 0=NO, 1=YES |

### Quem realmente chama (`invoke-interface` sobre `IWhitelistApService` em 120 APKs deodexados)

**3 consumidores, todos UI:**

1. **`AppManager.apk` → `WhiteListAdapter.smali` + `WhiteListAdapter$1.smali`**
   Chama: `getApplicationName`, `getAudioInfo`, `getRegulation`, `getRevert`.
   Função: popular a lista de aplicações no gerenciador de apps interno (nome amigável + condição de uso).

2. **`FileManager.apk` → `FileManagerActivity.smali`, `TelopInstallPopup.smali`, `commonservice/CommonServiceConnection.smali`, `FileManagerActivity$6.smali`**
   Função: validar/exibir metadata quando o usuário conecta um pendrive com APKs e tenta instalar algo.

3. **`WhitelistLib` + `WhitelistApService` próprios** (não contam — é o próprio service).

**`checkInstallPackage` nunca aparece como `invoke-interface` em lugar nenhum do shipping.** Existe no AIDL, mas na prática ninguém chama.

**Nenhum serviço HMI, nenhum launcher, nenhum PowerManager, nenhum componente de boot consulta a whitelist.**

---

## 4. Formato do XML

### 4.1 Tags (de `WhitelistXmlParser.smali`, campos literais)

```xml
<whiteList>
  <formatVersion>1.0</formatVersion>
  <contentVersion>N</contentVersion>
  <controlData>
    <application>
      <name>Nome Amigável</name>
      <package>com.exemplo.app</package>
      <versionCode>1</versionCode>
      <keyStore>SHA-256_do_certificado_de_assinatura_em_hex</keyStore>
      <audioStreamType>0</audioStreamType>
      <withAudio>false</withAudio>
      <regulation>0</regulation>
      <revert>0</revert>
    </application>
    <application>…</application>
  </controlData>
</whiteList>
```

- Encoding: UTF-8.
- `<keyStore>` provavelmente é hex do SHA-256 do certificado de assinatura — nossa chave de debug tem hash conhecido:
  `A40DA80A59D170CAA950CF15C18C454D47A39B26989D8B640ECD745BA71BF5DC` (CLAUDE.md).

### 4.2 Caminhos no filesystem (de `WhitelistConst.smali` e `WhitelistUtil.smali`)

| Constante | Valor |
|---|---|
| `WHITELIST_FILE_REGEX` (apesar do nome, é string literal) | `whitelist-1.0.xml` |
| `WHITELIST_DIRECTORY` | `/data/data/` |
| `WHITELIST_TEMP_NAMEADITION` | `TEMP_` (prefixo durante update) |
| `WHITELIST_USB_DIRECTORY` | `/data/data/usbtmp` |
| `WHITELIST_FORMAT_VERSION_FLOATING` | `1.0` |
| `MNT_USBDRIVE1` / `MNT_USBDRIVE2` | `/mnt/usbdrive1` / `/mnt/usbdrive2` |
| `PACKAG_MITSUBISH` | `mitsubishielectric` (substring usada em `checkHondaApplication`) |

### 4.3 Enums (de `WhitelistConst.smali`)

```
WHITELIST_AUDIO_WITH          = 1
WHITELIST_AUDIO_WITHOUT       = 0

WHITELIST_REGULATION_NULL             = 0
WHITELIST_REGULATION_PARKTRIGGER      = 1
WHITELIST_REGULATION_SPEEDTRIGGER     = 2
WHITELIST_REGULATION_PARKSPEEDTRIGGER = 3

WHITELIST_REVERT_NO  = 0
WHITELIST_REVERT_YES = 1

WHITELIST_STREAM_NULL                   = 0
WHITELIST_STREAM_SYSTEM                 = 1
WHITELIST_STREAM_ADA_GUIDE_HIGH         = 2
WHITELIST_STREAM_ADA_VOICE_RECOGNITION  = 3
WHITELIST_STREAM_ADA_GUIDE              = 4
WHITELIST_STREAM_ADA_GUIDE_LOW          = 5
WHITELIST_STREAM_MUSIC                  = 6

WHITELIST_SYMBOL_AUDIO      = 1
WHITELIST_SYMBOL_STREAM     = 2
WHITELIST_SYMBOL_REGULATION = 3
WHITELIST_SYMBOL_REVERT     = 4

WHITELIST_NOT_EXIST       = -1  (retorno sentinel)
WHITELIST_NOT_DEFINITION  = -2
```

---

## 5. Fluxos

### 5.1 Boot — ingestão inicial

`WhitelistApService.onCreate()`:

```java
public void onCreate() {
    super.onCreate();
    ExpLog.setTag("WhitelistApService");
    ExpLog.trace("onCreate service!");
    WhitelistFileManager.createUsbtemp();       // mkdir /data/data/usbtmp
    this.mFileManager = new WhitelistFileManager();
    updateWhitelist();                           // ver 5.2
}
```

### 5.2 Update (boot ou PACKAGE_REPLACED)

`WhitelistApService.updateWhitelist()`:

```java
private void updateWhitelist() {
    WhitelistContentResolver resolver = new WhitelistContentResolver(this);
    if (resolver.updateWhitelist()) {           // true se sobrescreveu
        this.mWhitelistXmlFileName = this.mFileManager.getWhitelistInDirectory();
        if (this.mWhitelistXmlFileName != null) {
            sWhitelistXml = this.mFileManager.getWhitelistModel(this.mWhitelistXmlFileName);
        }
    }
}
```

`WhitelistContentResolver.updateWhitelist()` (simplificado — o JADX decompile veio feio com try/catch duplicados):

```
1. checkDescriptor = resolver.openAssetFileDescriptor(
     Uri.parse("content://com.honda.displayaudio.whitelist/1.0"), null);
2. targetDescriptor = idem (duas streams independentes)
3. checkZis = ZipInputStream(checkDescriptor.createInputStream())
4. newZipEntry = getWhitelistInZip(checkZis)   // acha entry chamada "whitelist-1.0.xml"
5. targetZis = ZipInputStream(targetDescriptor.createInputStream())
6. seekZipStream("whitelist-1.0.xml", targetZis)   // posiciona
7. mFileManager.updateNewWhitelistInDirectory(targetZis, newZipEntry)
```

`WhitelistFileManager.updateNewWhitelistInDirectory`:

```java
public boolean updateNewWhitelistInDirectory(ZipInputStream zis, ZipEntry newEntry) {
    boolean res = saveFile(zis, newEntry);     // escreve /data/data/TEMP_whitelist-1.0.xml
    if (getWhitelistInDirectory() == null) {   // primeira vez — não há XML antigo
        res = renameFile(newEntry);            // TEMP_ → whitelist-1.0.xml
    } else {
        String tempfilename = "TEMP_" + newEntry.getName();
        String filename = newEntry.getName();
        if (WhitelistUtil.compareWhitelistContentVersion(tempfilename, filename) > 0) {
            res = renameFile(newEntry);        // só substitui se temp.contentVersion > atual
        }
        deleteFile(createFilePath(tempfilename));
    }
    return res;
}
```

**Regra crítica:** o `<contentVersion>` precisa ser **estritamente maior** para substituir. Qualquer modificação do XML tem que vir com `<contentVersion>` incrementado.

### 5.3 PACKAGE_REPLACED — update runtime

`WhitelistContentReceiver.onReceive`:

```java
public void onReceive(Context context, Intent intent) {
    if (intent == null) return;
    String action = intent.getAction();
    String packageName = intent.getDataString();
    if (!"android.intent.action.PACKAGE_REPLACED".equals(action)
        || !"package:com.honda.displayaudio.whitelist".equals(packageName)) {
        return;    // só reage se foi o pacote da whitelist que mudou
    }
    Intent updateIntent = new Intent();
    updateIntent.setClassName(UPDATE_SERVICE_PACKAGE, UPDATE_SERVICE_CLASS);
    context.startService(updateIntent);        // chama WhitelistUpdateService
}
```

`WhitelistUpdateService` roda em thread (`mUpdateThread`), chama o mesmo `WhitelistContentResolver.updateWhitelist()` do boot.

### 5.4 Consulta (quem usa — pattern binder)

```java
Intent i = new Intent("com.mitsubishielectric.ada.appservice.whitelist.IWhiteListApService");
context.bindService(i, serviceConnection, Context.BIND_AUTO_CREATE);
// serviceConnection.onServiceConnected recebe IBinder:
IWhitelistApService svc = IWhitelistApService.Stub.asInterface(binder);
String nome = svc.getApplicationName("com.exemplo.app", 1);
int regulacao = svc.getRegulation("com.exemplo.app", 1);
```

É isso que o `AppManager/WhiteListAdapter` faz. Nem permission check — qualquer app pode consultar.

---

## 6. Recovery pós-LP0 — como realmente funciona

### 6.1 PowerManager é pub/sub puro

`com.mitsubishielectric.ada.appservice.powermanager.PowerManagerApService` **não mantém lista de serviços para reiniciar**. Ele envia broadcasts em pontos chave do ciclo de power. Cada app que quer participar do fluxo HMI registra receivers no manifest.

### 6.2 Broadcasts emitidos (de `PowerManagerBroadcastSender`, 16 métodos)

| Método | Quando | Que action envia |
|---|---|---|
| `sendHMIServiceStartIntent(ctx, cause)` | Saída de LP0 ou ACC-on-restart | `ACTION_HMI_SERVICE_START` com extra `state` = cause (ex: `"ExitLP0"`, `"AccOnRestart"`, `"ColdBoot"`) |
| `sendHMIServiceStopIntent(ctx, cause)` | Entrando em LP0 ou shutdown | `ACTION_HMI_SERVICE_STOP` |
| `sendHMIServicePreStopIntent(ctx, cause)` | Preparando para LP0 | `ACTION_HMI_SERVICE_PRE_STOP` |
| `sendHMIServiceRestartIntent(ctx, cause)` | ACC-on durante transição | `ACTION_HMI_SERVICE_RESTART` |
| `sendHMIServiceStopIntentSplit(ctx, cause, extra)` | Variante com split info | idem stop |
| `sendFinishAllRunnningTaskForegroundIntent` | Mata foreground antes de LP0 | `ACTION_FINISH_ALL_RUNNING_TASKS_FOREGROUND` |
| `sendFinishAllRunnningTaskIntent` / `Partial` | Mata processos (variantes) | duas actions parecidas |
| `sendResumeCameraIntent(ctx)` | ⭐ Retomada da câmera de ré | action dedicada — **oportunidade**: hoje o AutoOk polla logcat; esse broadcast é limpo |
| `sendStartAnimationIntent(ctx)` | Animação de boot | — |
| `sendChangeStartCauseNoticeIntent(ctx, cause)` | Mudança da razão de startup | — |
| `sendKeyOffLimitNoticeIntent(ctx, cause)` | Timer de key-off expirando | — |
| `sendSetVbusResIntent(ctx, cause, res)` | VBUS result | — |
| `sendSyscomResetStartNoticeIntent(ctx)` | SysCom reset | — |
| `sendVbusOffNoticeIntent(ctx)` | VBUS desligou | — |

### 6.3 Listeners confirmados no shipping

Grep bytecode em 120 APKs: **33 referenciam `ACTION_HMI_SERVICE_START`.** Lista completa:

```
AcuraLinkApService        AndroidAuto           AppManager
AppModeApService          AV                    Camera
CameraAPService           CarPlayService        ClockSync
CompassService            DaLauncher            DiagApService
EmergencyApService        ErrorManager          ExternalDisplayApService
ExternalDisplayOutService HftApp                HftApService
MirrorLink                Navigation            PhoneCoordination
PowerManagerApService     PowerManagerApServiceLib
ScreenshotApService       SensorMonitor         StrgSW
SystemUpdate              Telematics            UnitInfoManager
VehicleCoordination       VehicleInfoManager    VoicePortalAp
WifiApService
```

Top 5 em número de ocorrências: `DaLauncher` (4), `Camera` (4), `AV` (4), `AppManager` (4), `EmergencyApService` (3). O `DaLauncher.Launcher$HMIServiceReceiver` é, inclusive, o que lança a `OpeningDivideActivity` que o AutoOk v0.4.0 fecha.

### 6.4 Nossa v0.4.0 já está no padrão

`AutoOk/HmiServiceReceiver` escuta `ACTION_HMI_SERVICE_START` e re-inicia o watcher. Mesmo pattern que os 33 serviços do sistema.

**Não há como "pular na frente" desse mecanismo entrando numa lista — a lista não existe.**

---

## 7. Rotas descartadas

### 7.1 Rota A — gravar `/data/data/whitelist-1.0.xml` direto

**Descartada.** Mesmo que funcione tecnicamente (temos root), o único efeito seria:
- Nosso APK aparecer no `AppManager` do carro com nome amigável.
- Nosso APK aparecer na UI do `FileManager` se tentarmos instalar via pendrive.

Não afeta LP0. Não remove código da v0.4.0.

### 7.2 Rota B — modificar `com.honda.displayaudio.whitelist.apk`

**Descartada pelo mesmo motivo**, com dificuldade extra: o APK não está no dump 0040 (gap do deep-scan — precisa incluir `/system/vendor/etc/honda/*` na próxima rodada). Mais limpo que a Rota A porque sobrevive a `updateWhitelist()` posterior, mas o ganho continua sendo só UX.

### 7.3 Hipótese inicial errada

Nossa suspeita era que o PowerManager mantém uma lista de "HMI services" baseada na whitelist e, por isso, não re-inicia nosso Service após LP0. **Está errada.** O PowerManager é agnóstico à whitelist; o reinício depende apenas do receiver registrado no manifest. Nosso `HmiServiceReceiver` da v0.4.0 **é** o mecanismo correto.

---

## 8. Oportunidades descobertas de bônus

### 8.1 Entrar na whitelist pelo valor cosmético

Se um dia quisermos que o AutoOk apareça no "Gerenciador de Apps" oficial do carro com nome amigável ("AutoOk — supressor de aviso") + regulação configurada (ex: `0` = sem restrição), a Rota A é viável. Baixa prioridade.

### 8.2 Escutar `ACTION_HMI_SERVICE_STOP` e `_PRE_STOP`

Hoje o AutoOk v0.4.0 só reage à **retomada**. Reagir ao `_PRE_STOP` permitiria salvar estado antes de LP0 (ex: offset do last-known-log-position), para retomar exatamente de onde parou. Hoje perdemos esse estado.

### 8.3 ⭐ `sendResumeCameraIntent` como gatilho de ré

Hoje o AutoOk descobre que a câmera de ré voltou/saiu via **logcat polling** (ver §13 do MAPA). Isso é frágil e caro. O PowerManager emite um broadcast dedicado — `sendResumeCameraIntent` — que seria um gatilho muito mais limpo.

Vale uma Fase 9: trocar a detecção da câmera por receiver registrado nessa action. Antes precisa confirmar qual é a string da action (não está nas constantes visíveis — provavelmente no `PowerManagerConstants.smali` ou é hardcoded no método).

### 8.4 Lista completa de broadcasts como contrato de debug

Os 16 broadcasts do `PowerManagerBroadcastSender` formam o contrato público de power management da plataforma. Registrar listeners de todos num app de instrumentação (não precisa ser o AutoOk — pode ser um APK à parte) daria um timeline detalhado do power state do veículo. Útil pra diagnosticar comportamentos estranhos.

---

## 9. APKs decoded nesta análise

Agora em `tooling/apks-decoded/`:

- `WhitelistApService-deodexed.apk` (6 smali, 12 KB classes.dex)
- `WhitelistLib-asapk.apk` (20 smali, 47 KB — APK wrapper com classes.dex da lib)
- `PowerManagerApService-deodexed.apk` (40 smali, 184 KB)
- `AppManagerServiceLib-asapk.apk` (41 smali, 128 KB — APK wrapper)
- `DaLauncher-deodexed.apk` (579 smali, 1.2 MB — da análise anterior do OpeningDivideActivity)

Em `/tmp/.../scratchpad/bulk-smali/by-apk/<Name>/` ficaram **120 projetos smali** completos (vendor-app + vendor-framework) — temporário, apagado no fim da sessão.

---

## 10. Pergunta aberta

**Qual é a action exata do `sendResumeCameraIntent`?** Vale 10 min no `PowerManagerBroadcastSender.sendResumeCameraIntent` pseudocode ou no `PowerManagerConstants.smali` — fica como follow-up quando/se decidirmos abrir a Fase 9.

---

**Evidence IDs (REA):** `ev_37e5ff64…`, `ev_742e311a…`, `ev_132387ab…`, `ev_805e74e4…`, `ev_357179c9…`, `ev_4c114516…`, `ev_7af9ae97…`, `ev_f6b0aa1a…`, `ev_fbd80713…`, `ev_08123e7b…`, `ev_13418a33…`, `ev_f83f62bd…`, `ev_2d83999a…`, `ev_60eb9f9a…`, `ev_a50a86d2…`, `ev_e7649556…`, `ev_645101a2…`, `ev_115cbd7c…`. Toda consulta é reproduzível via REA/CLI contra os APKs em `tooling/apks-decoded/`.
