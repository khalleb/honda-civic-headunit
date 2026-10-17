package com.khalleb.civichmi.autook;

import android.content.Context;
import android.util.Log;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public final class FileLogger {

    private static final String TAG = AutoOkConfig.LOGCAT_TAG;
    private static final SimpleDateFormat FMT =
        new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US);
    private static final Object WRITE_LOCK = new Object();

    private static volatile File logFile;
    private static volatile File backupFile;
    private static volatile boolean sessionStarted;

    private FileLogger() {
    }

    public static synchronized void init(Context ctx) {
        if (logFile != null) {
            return;
        }
        File dir = ctx.getFilesDir();
        logFile = new File(dir, AutoOkConfig.FILE_LOG_NAME);
        backupFile = new File(dir, AutoOkConfig.FILE_LOG_NAME + ".1");
    }

    public static synchronized void startSessionOnce() {
        if (sessionStarted) {
            return;
        }
        sessionStarted = true;
        File current = logFile;
        File backup = backupFile;
        if (current != null && current.exists()) {
            if (backup != null && backup.exists()) {
                backup.delete();
            }
            if (backup != null) {
                current.renameTo(backup);
            }
        }
        log("=== session start versionCode=3 ===");
    }

    public static void log(String msg) {
        Log.i(TAG, msg);
        File f = logFile;
        if (f == null) {
            return;
        }
        synchronized (WRITE_LOCK) {
            FileWriter w = null;
            try {
                w = new FileWriter(f, true);
                w.write(FMT.format(new Date()));
                w.write(" ");
                w.write(msg);
                w.write("\n");
            } catch (IOException e) {
                Log.e(TAG, "file log falhou: " + e.getMessage());
            } finally {
                closeQuietly(w);
            }
        }
    }

    private static void closeQuietly(FileWriter w) {
        if (w == null) {
            return;
        }
        try {
            w.close();
        } catch (IOException ignored) {
        }
    }
}
