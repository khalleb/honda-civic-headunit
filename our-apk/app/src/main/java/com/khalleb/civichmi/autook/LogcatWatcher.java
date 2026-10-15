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
        thread = new Thread(new Runnable() {
            @Override
            public void run() {
                watchLoop();
            }
        }, "AutoOk-LogcatWatcher");
        thread.start();
    }

    public synchronized void stop() {
        running = false;
        Process p = logcatProcess;
        if (p != null) {
            p.destroy();
        }
        logcatProcess = null;
        thread = null;
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
                p.destroy();
                logcatProcess = null;
            }
        }
    }

    private Process startLogcat() throws IOException {
        ProcessBuilder pb = new ProcessBuilder(
            "logcat", "-v", "brief", "ActivityManager:I", "*:S"
        );
        pb.redirectErrorStream(true);
        return pb.start();
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
