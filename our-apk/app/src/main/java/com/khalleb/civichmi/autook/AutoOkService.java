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
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (!isConfigValid()) {
            Log.e(TAG, "config pendente de preenchimento em AutoOkConfig (Activity e X/Y do OK)");
            stopSelf();
            return START_NOT_STICKY;
        }
        if (watcher != null) {
            return START_STICKY;
        }
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

        AvisoCallback(AutoOkService service) {
            this.service = service;
        }

        @Override
        public void onDetected() {
            service.onAvisoDetected();
        }
    }

    private void onAvisoDetected() {
        if (handled) {
            return;
        }
        handled = true;
        if (!sleepSeconds(AutoOkConfig.DELAY_SECONDS_AFTER_DETECT)) {
            return;
        }
        boolean ok = Shell.suTap(AutoOkConfig.BUTTON_OK_X, AutoOkConfig.BUTTON_OK_Y);
        Log.i(TAG, "tap " + AutoOkConfig.BUTTON_OK_X + "," + AutoOkConfig.BUTTON_OK_Y + " -> " + ok);
        rearmWatcher();
    }

    private void rearmWatcher() {
        if (!sleepSeconds(AutoOkConfig.REARM_DELAY_SECONDS)) {
            return;
        }
        handled = false;
        Log.i(TAG, "watcher rearmado, aguardando proxima aparicao");
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
        if (w == null) {
            return;
        }
        w.stop();
        watcher = null;
    }
}
