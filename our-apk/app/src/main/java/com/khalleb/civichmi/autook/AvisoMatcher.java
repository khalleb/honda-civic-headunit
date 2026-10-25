package com.khalleb.civichmi.autook;

public final class AvisoMatcher {

    public static final String EVENT_CREATE = "am_create_activity";
    public static final String EVENT_NEW_INTENT = "am_new_intent";
    public static final String ACTION_NORMAL = "dalauncher.action.NORMAL_STARTUP";

    private AvisoMatcher() {
    }

    public static boolean matches(String line, String activityNeedle) {
        if (line == null || activityNeedle == null) {
            return false;
        }
        if (!line.contains(activityNeedle)) {
            return false;
        }
        if (!line.contains(ACTION_NORMAL)) {
            return false;
        }
        return line.contains(EVENT_CREATE) || line.contains(EVENT_NEW_INTENT);
    }
}
