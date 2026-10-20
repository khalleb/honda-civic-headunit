package com.khalleb.civichmi.autook;

import android.util.Log;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;

public final class Shell {

    private static final String TAG = AutoOkConfig.LOGCAT_TAG;

    private Shell() {
    }

    public static boolean suTap(int x, int y) {
        return suExec("input tap " + x + " " + y);
    }

    public static boolean suTapWithFallback(int[][] coords, int intervalMs) {
        for (int i = 0; i < coords.length; i++) {
            int[] c = coords[i];
            if (suTap(c[0], c[1])) {
                return true;
            }
            if (!sleepQuietly(intervalMs)) {
                return false;
            }
        }
        return false;
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

    public static String suExecCapture(String command) {
        Process p = null;
        DataOutputStream out = null;
        BufferedReader reader = null;
        try {
            p = Runtime.getRuntime().exec("su");
            out = new DataOutputStream(p.getOutputStream());
            out.writeBytes(command + "\n");
            out.writeBytes("exit\n");
            out.flush();
            reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append('\n');
            }
            p.waitFor();
            return sb.toString();
        } catch (IOException e) {
            Log.e(TAG, "su capture IOException: " + e.getMessage());
            return "";
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return "";
        } finally {
            closeQuietly(out);
            closeReader(reader);
            if (p != null) {
                p.destroy();
            }
        }
    }

    public static boolean isActivityOnTop(String activityComponent) {
        String out = suExecCapture("dumpsys activity top 2>/dev/null | grep 'ACTIVITY ' | head -1");
        return out != null && out.contains(activityComponent);
    }

    private static boolean sleepQuietly(int ms) {
        try {
            Thread.sleep(ms);
            return true;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
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

    private static void closeReader(BufferedReader r) {
        if (r == null) {
            return;
        }
        try {
            r.close();
        } catch (IOException ignored) {
        }
    }
}
