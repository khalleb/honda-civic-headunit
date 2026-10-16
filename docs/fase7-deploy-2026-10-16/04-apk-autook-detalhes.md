# AutoOk.apk — detalhes técnicos

Tudo sobre o APK: arquitetura, decisões de design, bugs enfrentados e soluções, configuração final.

## Função

Instalar o APK em `/system/app/` + ter `su` em `/system/xbin/`, e nunca mais precisar clicar no "OK" do Aviso. Quando a central mostra o Aviso em qualquer boot, o APK:

1. Detecta via logcat que a Activity `OpeningDivideActivity` foi iniciada.
2. Aguarda 2 segundos (dar tempo pro Fragment renderizar).
3. Executa `su -c "input tap 400 350"` — simula um toque no botão OK.
4. Aviso some.
5. Re-arma pra interceptar a próxima aparição.

## Arquitetura

4 classes Java simples + 1 config:

```
AutoOkConfig       # constantes (Activity name, coords, delays)
    ↓
BootReceiver       # recebe BOOT_COMPLETED, inicia Service
    ↓
AutoOkService      # Service persistente, orquestra o LogcatWatcher
    ↓
LogcatWatcher      # thread que roda `su -c "logcat"` e procura match
    ↓
Shell              # helper pra executar `su -c "cmd"` arbitrário
```

### `AutoOkConfig.java`

```java
package com.khalleb.civichmi.autook;

public final class AutoOkConfig {

    public static final String AVISO_ACTIVITY_NAME =
        "com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity";

    public static final int BUTTON_OK_X = 400;
    public static final int BUTTON_OK_Y = 350;

    public static final int DELAY_SECONDS_AFTER_DETECT = 2;

    public static final int REARM_DELAY_SECONDS = 10;

    public static final int BOOT_INITIAL_WAIT_MS = 5000;

    public static final String LOGCAT_TAG = "AutoOk";

    private AutoOkConfig() {
    }
}
```

Observações:

- **`AVISO_ACTIVITY_NAME` tem `/.` (barra-ponto)** entre package e classe. Esse é o formato que o logcat usa (`cmp=com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity`). Precisa casar substring, não equals. Se usar `.` sozinho (`com....dalauncher.OpeningDivideActivity`), nunca bate.
- **Coordenadas (400, 350):** centro do botão OK calculado a partir do layout `mm_02_01_02.xml` (btnOK em x=223 y=328 width=354 height=44). Qualquer ponto dentro do retângulo aceita o tap, mas o centro dá margem de erro máxima.
- **`DELAY_SECONDS_AFTER_DETECT = 2`:** tempo entre detectar via logcat e tappar. Dá tempo da Activity + Fragment terem sido renderizados e aceitarem input. Se tappar cedo demais, pode cair fora da área sensível.
- **`REARM_DELAY_SECONDS = 10`:** depois do tap, aguarda 10s antes de resetar o `handled` e começar a monitorar de novo. Evita re-tappar múltiplas vezes na mesma Activity (que pode gerar `am_resume_activity` adicional após o tap).
- **`BOOT_INITIAL_WAIT_MS = 5000`:** depois do BOOT_COMPLETED, o Service aguarda 5s antes de abrir o logcat. Dá tempo do `su` estar disponível (binário ter sido carregado) e logcat ter mensagens iniciais relevantes.

### `AndroidManifest.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.khalleb.civichmi.autook"
    android:versionCode="1"
    android:versionName="0.1.0">

    <uses-sdk android:minSdkVersion="17" android:targetSdkVersion="17" />

    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />

    <application
        android:label="@string/app_name"
        android:allowBackup="false">

        <receiver
            android:name=".BootReceiver"
            android:enabled="true"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED" />
            </intent-filter>
        </receiver>

        <service
            android:name=".AutoOkService"
            android:exported="false" />
    </application>
</manifest>
```

Observações:

- **`minSdkVersion=17`** (Android 4.2.2 — SDK da nossa safra).
- **`targetSdkVersion=17`** — não target SDK mais novo para evitar comportamento diferente em permissions ou background services. 17 era pré-Oreo background restrictions, pré-Nougat JobScheduler mandatório.
- **Única permission:** `RECEIVE_BOOT_COMPLETED`. É level `normal`, auto-grant.
- **`READ_LOGS` NÃO está no manifest** — não precisamos pedir porque usamos `su -c logcat`, que roda como root e bypassa a verificação de permission do Android.
- **`ACCESS_SUPERUSER` NÃO está no manifest** — permission do SuperSU/Magisk que não temos. O warning do PackageManager quando essa permission existe (`Unknown permission android.permission.ACCESS_SUPERUSER`) é ignorável mas feio nos logs.
- **BootReceiver `exported=true`** — necessário para Android dispatchar BOOT_COMPLETED pra ele.
- **Service `exported=false`** — ninguém de fora precisa iniciar o Service.

### `BootReceiver.java`

```java
package com.khalleb.civichmi.autook;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) return;
        if (!Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) return;
        context.startService(new Intent(context, AutoOkService.class));
    }
}
```

Simples: só dispara o Service.

**Importante:** `BOOT_COMPLETED` só é broadcast **em cold boot**. "Virar a chave" na central Honda **não é cold boot** (vimos nos PowerLog + kernel uptime). Para o Service ser inicializado, precisa de cold boot (via `AUDIO 5s` ou puxar fusível).

### `Shell.java`

```java
package com.khalleb.civichmi.autook;

import android.util.Log;
import java.io.DataOutputStream;
import java.io.IOException;

public final class Shell {
    private static final String TAG = AutoOkConfig.LOGCAT_TAG;

    private Shell() {}

    public static boolean suTap(int x, int y) {
        return suExec("input tap " + x + " " + y);
    }

    public static boolean suExec(String command) {
        Process p = null;
        DataOutputStream out = null;
        try {
            p = Runtime.getRuntime().exec("su");
            out = new DataOutputStream(p.getOutputStream());
            out.writeBytes(command + "\n");
            out.writeBytes("exit\n");
            out.flush();
            return p.waitFor() == 0;
        } catch (IOException e) {
            Log.e(TAG, "su exec IOException: " + e.getMessage());
            return false;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        } finally {
            closeQuietly(out);
            if (p != null) p.destroy();
        }
    }

    // ...
}
```

Fluxo:

1. `Runtime.getRuntime().exec("su")` — spawn `su` como processo filho.
2. Escreve comando no stdin do su, seguido de `exit`.
3. Aguarda su terminar.
4. Retorna true se exit code = 0.

**Se `su` não existe no PATH do Runtime (sem root), lança IOException.** O código captura e loga. APK não brickeia, só não funciona. Essa é a razão de combinarmos APK + su no mesmo pacote OTA — garante que su exista.

### `LogcatWatcher.java`

```java
package com.khalleb.civichmi.autook;

import android.util.Log;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class LogcatWatcher {

    public interface OnDetected {
        void onDetected();
    }

    private final String activityNeedle;
    private final int initialWaitMs;
    private final OnDetected callback;

    private Thread thread;
    private volatile Process logcatProcess;
    private volatile boolean running;

    public LogcatWatcher(String activityNeedle, int initialWaitMs, OnDetected callback) {
        this.activityNeedle = activityNeedle;
        this.initialWaitMs = initialWaitMs;
        this.callback = callback;
    }

    public synchronized void start() {
        if (thread != null) return;
        running = true;
        thread = new Thread(new WatchRunnable(this), "AutoOk-LogcatWatcher");
        thread.start();
    }

    private static final class WatchRunnable implements Runnable {
        private final LogcatWatcher watcher;
        WatchRunnable(LogcatWatcher w) { this.watcher = w; }
        @Override public void run() { watcher.watchLoop(); }
    }

    public synchronized void stop() {
        running = false;
        Process p = logcatProcess;
        if (p != null) p.destroy();
        logcatProcess = null;
        thread = null;
    }

    private void watchLoop() {
        sleepQuietly(initialWaitMs);
        if (!running) return;

        BufferedReader reader = null;
        try {
            Process p = startLogcat();
            logcatProcess = p;
            reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
            consume(reader);
        } catch (IOException e) {
            Log.e(TAG, "logcat watch falhou: " + e.getMessage());
        } finally {
            // cleanup
        }
    }

    private Process startLogcat() throws IOException {
        Process p = Runtime.getRuntime().exec("su");
        DataOutputStream out = new DataOutputStream(p.getOutputStream());
        out.writeBytes("exec logcat -v brief ActivityManager:I *:S 2>&1\n");
        out.flush();
        return p;
    }

    private void consume(BufferedReader reader) throws IOException {
        String line;
        while (running && (line = reader.readLine()) != null) {
            if (line.contains(activityNeedle)) {
                callback.onDetected();
                return;
            }
        }
    }
    // ...
}
```

Observações:

- **`exec logcat`:** usa `exec` do shell para substituir o shell por `logcat`. Economiza um processo filho adicional.
- **`-v brief`:** formato de log compact `I/TAG(PID): message`.
- **`ActivityManager:I *:S`:** filtra para só mostrar tag `ActivityManager` em nível I+, silencia o resto. Reduz volume de logs lidos.
- **`line.contains(activityNeedle)`:** procura substring. Logcat ActivityManager emite linhas como:
  ```
  I/ActivityManager(940): START u0 {flg=0x30000000 cmp=com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity (has extras)} from pid 1831
  ```
  Nosso needle `com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity` casa como substring.
- **Named inner class `WatchRunnable`:** NÃO é anonymous. Veja seção de bug D8 abaixo.

### `AutoOkService.java`

```java
package com.khalleb.civichmi.autook;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.util.Log;

public class AutoOkService extends Service {
    private static final String TAG = AutoOkConfig.LOGCAT_TAG;

    private LogcatWatcher watcher;
    private volatile boolean handled;

    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (!isConfigValid()) {
            Log.e(TAG, "config pendente de preenchimento");
            stopSelf();
            return START_NOT_STICKY;
        }
        if (watcher != null) return START_STICKY;

        watcher = buildWatcher();
        watcher.start();
        Log.i(TAG, "watcher iniciado, aguardando " + AutoOkConfig.AVISO_ACTIVITY_NAME);
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        stopWatcher();
        super.onDestroy();
    }

    private boolean isConfigValid() {
        boolean hasActivity = AutoOkConfig.AVISO_ACTIVITY_NAME != null
            && AutoOkConfig.AVISO_ACTIVITY_NAME.length() > 0;
        boolean hasCoords = AutoOkConfig.BUTTON_OK_X >= 0 && AutoOkConfig.BUTTON_OK_Y >= 0;
        return hasActivity && hasCoords;
    }

    private LogcatWatcher buildWatcher() {
        return new LogcatWatcher(
            AutoOkConfig.AVISO_ACTIVITY_NAME,
            AutoOkConfig.BOOT_INITIAL_WAIT_MS,
            new AvisoCallback(this)
        );
    }

    private static final class AvisoCallback implements LogcatWatcher.OnDetected {
        private final AutoOkService service;
        AvisoCallback(AutoOkService s) { this.service = s; }
        @Override public void onDetected() { service.onAvisoDetected(); }
    }

    private void onAvisoDetected() {
        if (handled) return;
        handled = true;
        if (!sleepSeconds(AutoOkConfig.DELAY_SECONDS_AFTER_DETECT)) return;
        boolean ok = Shell.suTap(AutoOkConfig.BUTTON_OK_X, AutoOkConfig.BUTTON_OK_Y);
        Log.i(TAG, "tap " + AutoOkConfig.BUTTON_OK_X + "," + AutoOkConfig.BUTTON_OK_Y + " -> " + ok);
        rearmWatcher();
    }

    private void rearmWatcher() {
        if (!sleepSeconds(AutoOkConfig.REARM_DELAY_SECONDS)) return;
        handled = false;
        Log.i(TAG, "watcher rearmado");
        stopWatcher();
        watcher = buildWatcher();
        watcher.start();
    }

    private boolean sleepSeconds(int seconds) {
        try {
            Thread.sleep(seconds * 1000L);
            return true;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        }
    }

    private void stopWatcher() {
        LogcatWatcher w = watcher;
        if (w == null) return;
        w.stop();
        watcher = null;
    }
}
```

Decisões de design importantes:

- **`START_STICKY`:** Android recria o Service se for killed por memória baixa. Em teoria. Na prática, se Service morre em `stopSelf()`, não volta até próximo BOOT_COMPLETED. **Nossa estratégia é NUNCA chamar `stopSelf()`** depois do primeiro init.
- **`rearmWatcher()`:** depois do tap, reseta estado e re-cria watcher. Garante persistência mesmo depois de múltiplas aparições do Aviso.
- **`handled` flag:** debounce. Evita tappar múltiplas vezes se logcat emitir várias linhas sobre a mesma Activity em rápida sucessão. É resetado em `rearmWatcher()` depois de `REARM_DELAY_SECONDS`.
- **`AvisoCallback` named inner class:** veja bug D8 abaixo.
- **`isConfigValid()` early exit:** se por qualquer motivo (build errado?) as constantes estiverem com placeholder, Service para elegantemente ao invés de rodar com valores inválidos.

## Bug do D8 (dexer) e workaround

### O bug

Android Gradle Plugin 7.4.2 usa D8 4.0.52 (dexer que converte .class em .dex). Quando as constantes `AutoOkConfig.AVISO_ACTIVITY_NAME` é string **não vazia** com dot path (como `"com.a.b.OpeningDivideActivity"`), o D8 **crasha com NullPointerException** ao processar as anonymous inner classes `AutoOkService$1.class` e `LogcatWatcher$1.class`:

```
ERROR: ...AutoOkService$1.class: D8: java.lang.NullPointerException:
       Cannot invoke "String.length()" because "<parameter1>" is null
```

Com string vazia (placeholder `""`), não crasha — provavelmente porque o D8 otimiza as inner classes como dead code.

### A causa provável

Bug conhecido do D8/R8 em certos padrões de anonymous inner classes com references cross-package. O compilador tenta otimizar e falha num NPE interno.

### O workaround — named inner classes

Converter anonymous → named:

**ANTES (bug):**
```java
// Em AutoOkService
new LogcatWatcher.OnDetected() {
    @Override
    public void onDetected() {
        onAvisoDetected();
    }
}
```

**DEPOIS (ok):**
```java
// Em AutoOkService
private static final class AvisoCallback implements LogcatWatcher.OnDetected {
    private final AutoOkService service;
    AvisoCallback(AutoOkService s) { this.service = s; }
    @Override public void onDetected() { service.onAvisoDetected(); }
}
```

Equivalente para `WatchRunnable` em `LogcatWatcher`:

**ANTES:**
```java
thread = new Thread(new Runnable() {
    @Override public void run() { watchLoop(); }
}, "AutoOk-LogcatWatcher");
```

**DEPOIS:**
```java
thread = new Thread(new WatchRunnable(this), "AutoOk-LogcatWatcher");
```

Com `WatchRunnable` named static class externamente.

Build passou. Benefício colateral: código mais fácil de ler e debugar (stack traces têm nomes significativos).

## Observação sobre o needle do logcat

Logcat da nossa safra emite linhas sobre OpeningDivideActivity em várias tags:

```
I/AppManagerServiceApplication: ... name=com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity ...
I/am_create_activity: [0,...,com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity,...]
I/ActivityManager: START u0 {... cmp=com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity ...}
I/am_create_task, I/am_proc_bound, etc.
```

Nosso filtro `ActivityManager:I *:S` só captura a linha de **`ActivityManager: START u0`**. Isso é suficiente — essa linha é emitida exatamente uma vez por lançamento da Activity.

**Alternativa descartada:** tag `am_create_activity` também seria ok, mas tem múltiplas linhas por Activity (`am_create_task`, `am_proc_start`, etc.). `ActivityManager:I` é mais limpo.

Separador `/.` é o padrão de notação do Android para "package/.ClassName" (short notation quando a classe está no root do package). Alguns logs usam `/` + ClassName full. Nosso contains vai casar tanto `cmp=...dalauncher/.OpeningDivideActivity` quanto `cmp=...dalauncher/com.mitsubishielectric.ada.app.dalauncher.OpeningDivideActivity` se existir (mas na prática a safra usa só a forma curta).

## Observação sobre persistência vs. chave on/off

**Comportamento observado da central Honda Civic 2017 BR:**

- **Primeira ligação do dia (central estava "fria"):** cold boot → kernel reboota → BOOT_COMPLETED broadcast → nosso BootReceiver dispara → Service inicia.
- **Desligar chave + religar (central em suspend):** central acorda do suspend → NO cold boot → NO BOOT_COMPLETED. Nosso Service precisa estar vivo.

Logs capturados comprovam: só UM `am_proc_start` do autook em todos os logs (do cold boot), nenhuma reactivation ao religar.

Isso explica por que **nunca podemos chamar `stopSelf()`**:
- Com `stopSelf()`: Service morre após primeiro tap. Religou chave? Aviso aparece, APK não intercepta. Precisa de cold boot (via AUDIO 5s) para reiniciar.
- **Sem `stopSelf()` (nosso design)**: Service fica vivo até Android killar por memória. Religou chave? Aviso aparece, APK ainda vivo, re-intercepta.

Teste real feito pelo dono: desligar/ligar a chave várias vezes, aviso sempre intercepta. ✓

## Build do APK — passo a passo

### 1. Gradle build

```bash
cd our-apk
./gradlew clean assembleRelease
```

Saída esperada: `BUILD SUCCESSFUL`.

Arquivo gerado: `app/build/outputs/apk/release/app-release-unsigned.apk` (~6.3KB).

### 2. Assinar com apksigner

```bash
APKSIGNER=/home/khalleb/sdks/Android/build-tools/33.0.2/apksigner
$APKSIGNER sign \
  --ks ~/.android/debug.keystore \
  --ks-pass pass:android \
  --out app/build/outputs/apk/release/AutoOk.apk \
  app/build/outputs/apk/release/app-release-unsigned.apk
```

Resultado:
- `AutoOk.apk` (~12.8KB — maior porque assinatura v2+ embarca signing block).

Keystore: debug keystore padrão Android em `~/.android/debug.keystore`, senha `android`, alias `androiddebugkey`. Pra deploy no `/system/app/` isso serve — a whitelist Mitsubishi só filtra apps user via Honda Installer; apps system são carregados sem verificação de keystore.

### 3. Verificar

```bash
$APKSIGNER verify --print-certs AutoOk.apk
# Esperado:
# Verifies
# Verified using v1 scheme (JAR signing): true
# Verified using v2 scheme (APK Signature Scheme v2): true
# Signer #1 certificate SHA-1 digest: <SHA-1>
```

SHA-1 do cert com debug keystore nosso: `e3b14e2b697dcdf9245e9988cb0bae8b3b504860`.

### 4. Copiar para overlay do OTA

```bash
cp app/build/outputs/apk/release/AutoOk.apk \
   ../tooling/ota-build/overlay/system/app/AutoOk.apk
```

Daí build.py pega esse arquivo e inclui no `SwUpdate.mdt`.

## Versão deployada final

- Arquivo: `AutoOk.apk`
- Tamanho: 12794 bytes
- SHA-1 (arquivo): `e76d35741c5fafb8289f97f9565aaf8e1bff4f66`
- SHA-1 (certificate signer): `e3b14e2b697dcdf9245e9988cb0bae8b3b504860`
- `versionCode`: 1
- `versionName`: 0.1.0
- Target SDK: 17 (Android 4.2.2)
- Deploy: 2026-10-16 ~10:55 BRT
- Status: funcionando, confirmado pelo dono em testes múltiplos.

## Como atualizar o APK no futuro

Mudar código em `our-apk/app/src/main/java/com/khalleb/civichmi/autook/`, rebuild + sign + copy pro overlay + rebuild OTA + deploy. Detalhes em [05-manutencao-e-futuro.md](05-manutencao-e-futuro.md).

## Melhorias futuras possíveis

- **Reduzir `BOOT_INITIAL_WAIT_MS` + `DELAY_SECONDS_AFTER_DETECT`** para fazer o tap acontecer antes de 10s. Tentar 2000ms + 1s = tap em ~3s do boot.
- **Multi-Activity watch:** se outras Activities do Mitsubishi mostrarem botões similares (ex: `OpeningActivity`, `InfoClockOpeningActivity`), monitorar todas e tappar coord corretas pra cada.
- **Smart coord detection:** ler accessibility services para pegar coord real do botão OK em runtime, ao invés de hardcoded. Mais robusto para mudanças de UI em updates da Honda.
- **Mudar notification que BootReceiver mostra** para debug visível (mesmo que o Launcher da central não mostre notification bar).
- **Export logs** para pendrive via watcher se qualquer coisa der errado em runtime.
