package com.khalleb.civichmi.autook;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.os.IBinder;
import android.os.SystemClock;

public class AutoOkService extends Service {

    private final Object watcherLock = new Object();
    private LogcatWatcher watcher;
    private volatile boolean handled;

    private Thread watchdogThread;
    private volatile boolean watchdogRunning;

    private PendingIntent alarmPendingIntent;

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        FileLogger.init(this);
        FileLogger.startSessionOnce();
        if (!isConfigValid()) {
            FileLogger.log("ERRO: config invalida em AutoOkConfig");
            stopSelf();
            return START_NOT_STICKY;
        }

        String action = intent == null ? null : intent.getAction();
        if (AutoOkConfig.ACTION_FORCE_RESTART.equals(action)) {
            String source = intent.getStringExtra("source");
            String cause = intent.getStringExtra("cause");
            FileLogger.log("FORCE_RESTART source=" + source + " cause=" + cause);
            forceRestartWatcher();
            scheduleAlarm();
            return START_STICKY;
        }

        synchronized (watcherLock) {
            if (watcher == null) {
                watcher = buildWatcher();
                watcher.start();
                FileLogger.log("watcher iniciado needle=" + AutoOkConfig.AVISO_ACTIVITY_NAME);
            }
        }
        startWatchdog();
        scheduleAlarm();
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        stopWatchdog();
        stopWatcher();
        cancelAlarm();
        FileLogger.log("service destroyed");
        super.onDestroy();
    }

    private boolean isConfigValid() {
        boolean hasActivity = AutoOkConfig.AVISO_ACTIVITY_NAME != null
            && AutoOkConfig.AVISO_ACTIVITY_NAME.length() > 0;
        boolean hasCoords = AutoOkConfig.BUTTON_OK_X >= 0 && AutoOkConfig.BUTTON_OK_Y >= 0;
        boolean hasFallback = AutoOkConfig.TAP_FALLBACK_COORDS != null
            && AutoOkConfig.TAP_FALLBACK_COORDS.length > 0;
        return hasActivity && hasCoords && hasFallback;
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
        FileLogger.log("aviso detectado");
        if (!sleepSeconds(AutoOkConfig.DELAY_SECONDS_AFTER_DETECT)) {
            return;
        }
        boolean ok = Shell.suTapWithFallback(
            AutoOkConfig.TAP_FALLBACK_COORDS,
            AutoOkConfig.TAP_FALLBACK_INTERVAL_MS
        );
        FileLogger.log("tap ok=" + ok + " coords=" + AutoOkConfig.TAP_FALLBACK_COORDS.length);
        rearmWatcher();
    }

    private void rearmWatcher() {
        if (!sleepSeconds(AutoOkConfig.REARM_DELAY_SECONDS)) {
            return;
        }
        handled = false;
        FileLogger.log("rearmed (watcher reusado)");
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
        LogcatWatcher w;
        synchronized (watcherLock) {
            w = watcher;
            watcher = null;
        }
        if (w != null) {
            w.stop();
        }
    }

    private void forceRestartWatcher() {
        synchronized (watcherLock) {
            LogcatWatcher old = watcher;
            handled = false;
            if (old != null) {
                old.stop();
            }
            watcher = buildWatcher();
            watcher.start();
            FileLogger.log("watcher forcibly recreated");
        }
    }

    private void startWatchdog() {
        if (watchdogThread != null) {
            return;
        }
        watchdogRunning = true;
        watchdogThread = new Thread(new WatchdogRunnable(this), "AutoOk-Watchdog");
        watchdogThread.setDaemon(true);
        watchdogThread.start();
    }

    private void stopWatchdog() {
        watchdogRunning = false;
        Thread t = watchdogThread;
        if (t != null) {
            t.interrupt();
        }
        watchdogThread = null;
    }

    private static final class WatchdogRunnable implements Runnable {
        private final AutoOkService service;

        WatchdogRunnable(AutoOkService service) {
            this.service = service;
        }

        @Override
        public void run() {
            service.watchdogLoop();
        }
    }

    private void watchdogLoop() {
        while (watchdogRunning) {
            try {
                Thread.sleep(AutoOkConfig.WATCHDOG_INTERVAL_SECONDS * 1000L);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return;
            }
            if (!watchdogRunning) {
                return;
            }
            ensureWatcherAlive();
        }
    }

    private void ensureWatcherAlive() {
        synchronized (watcherLock) {
            if (handled) {
                return;
            }
            LogcatWatcher w = watcher;
            if (w != null && w.isAlive()) {
                return;
            }
            if (w != null) {
                w.stop();
            }
            watcher = buildWatcher();
            watcher.start();
            FileLogger.log("watchdog: watcher recriado (anterior=" + (w == null ? "null" : "morto") + ")");
        }
    }

    private PendingIntent getAlarmPendingIntent() {
        if (alarmPendingIntent != null) {
            return alarmPendingIntent;
        }
        Intent i = new Intent(this, AlarmReceiver.class);
        i.setAction(AutoOkConfig.ACTION_ALARM_HEALTHCHECK);
        alarmPendingIntent = PendingIntent.getBroadcast(this, 0, i, PendingIntent.FLAG_UPDATE_CURRENT);
        return alarmPendingIntent;
    }

    private void scheduleAlarm() {
        AlarmManager am = (AlarmManager) getSystemService(Context.ALARM_SERVICE);
        if (am == null) {
            return;
        }
        long interval = AutoOkConfig.ALARM_HEALTHCHECK_INTERVAL_SECONDS * 1000L;
        long first = SystemClock.elapsedRealtime() + interval;
        am.setRepeating(AlarmManager.ELAPSED_REALTIME_WAKEUP, first, interval, getAlarmPendingIntent());
    }

    private void cancelAlarm() {
        AlarmManager am = (AlarmManager) getSystemService(Context.ALARM_SERVICE);
        if (am != null && alarmPendingIntent != null) {
            am.cancel(alarmPendingIntent);
        }
    }
}
