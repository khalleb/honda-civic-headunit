package com.khalleb.civichmi.autook;

import android.util.Log;

import java.io.DataOutputStream;
import java.io.IOException;

public final class Shell {

    private static final String TAG = AutoOkConfig.LOGCAT_TAG;

    private Shell() {
    }

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
            if (p != null) {
                p.destroy();
            }
        }
    }

    private static void closeQuietly(DataOutputStream o) {
        if (o == null) {
            return;
        }
        try {
            o.close();
        } catch (IOException ignored) {
        }
    }
}
