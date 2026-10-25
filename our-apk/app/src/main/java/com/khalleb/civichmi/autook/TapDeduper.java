package com.khalleb.civichmi.autook;

public final class TapDeduper {

    private TapDeduper() {
    }

    public static boolean shouldSuppress(long nowMs, long lastTapAtMs, int dedupSeconds) {
        return lastTapAtMs > 0 && (nowMs - lastTapAtMs) < dedupSeconds * 1000L;
    }
}
