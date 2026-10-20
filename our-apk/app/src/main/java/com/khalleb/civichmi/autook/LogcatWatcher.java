package com.khalleb.civichmi.autook;

import android.util.Log;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class LogcatWatcher {

    public interface OnDetected {
        void onDetected();
    }

    private static final String TAG = AutoOkConfig.LOGCAT_TAG;

    private static final String EVENT_CREATE = "am_create_activity";
    private static final String EVENT_NEW_INTENT = "am_new_intent";
    private static final String ACTION_NORMAL = "dalauncher.action.NORMAL_STARTUP";

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
        if (thread != null) {
            return;
        }
        running = true;
        thread = new Thread(new WatchRunnable(this), "AutoOk-LogcatWatcher");
        thread.start();
    }

    public synchronized boolean isAlive() {
        if (!running) {
            return false;
        }
        Thread t = this.thread;
        return t != null && t.isAlive();
    }

    private static final class WatchRunnable implements Runnable {
        private final LogcatWatcher watcher;

        WatchRunnable(LogcatWatcher watcher) {
            this.watcher = watcher;
        }

        @Override
        public void run() {
            watcher.watchLoop();
        }
    }

    public synchronized void stop() {
        running = false;
        Process p = logcatProcess;
        if (p != null) {
            destroyQuietly(p);
        }
        logcatProcess = null;
        thread = null;
    }

    private static void destroyQuietly(Process p) {
        try {
            p.destroy();
        } catch (Throwable ignored) {
        }
    }

    private void watchLoop() {
        sleepQuietly(initialWaitMs);
        if (!running) {
            return;
        }
        BufferedReader reader = null;
        try {
            Process p = startLogcat();
            logcatProcess = p;
            reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
            consume(reader);
        } catch (IOException e) {
            Log.e(TAG, "logcat watch falhou: " + e.getMessage());
        } finally {
            closeQuietly(reader);
            Process p = logcatProcess;
            if (p != null) {
                destroyQuietly(p);
                logcatProcess = null;
            }
        }
    }

    private Process startLogcat() throws IOException {
        Process p = Runtime.getRuntime().exec("su");
        java.io.DataOutputStream out = new java.io.DataOutputStream(p.getOutputStream());
        out.writeBytes("exec logcat -b events -v threadtime am_create_activity:I am_new_intent:I *:S 2>&1\n");
        out.flush();
        return p;
    }

    private void consume(BufferedReader reader) throws IOException {
        String line;
        while (running && (line = reader.readLine()) != null) {
            if (!line.contains(activityNeedle)) {
                continue;
            }
            if (!line.contains(ACTION_NORMAL)) {
                continue;
            }
            if (!line.contains(EVENT_CREATE) && !line.contains(EVENT_NEW_INTENT)) {
                continue;
            }
            callback.onDetected();
        }
    }

    private static void sleepQuietly(int ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private static void closeQuietly(BufferedReader r) {
        if (r == null) {
            return;
        }
        try {
            r.close();
        } catch (IOException ignored) {
        }
    }
}
