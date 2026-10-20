package com.khalleb.civichmi.autook;

public final class AutoOkConfig {

    public static final String AVISO_ACTIVITY_NAME = "com.mitsubishielectric.ada.app.dalauncher/.OpeningDivideActivity";

    public static final int BUTTON_OK_X = 400;
    public static final int BUTTON_OK_Y = 350;

    public static final int[][] TAP_FALLBACK_COORDS = new int[][] {
        {400, 350},
        {400, 340},
        {400, 360}
    };

    public static final int TAP_FALLBACK_INTERVAL_MS = 200;

    public static final int DELAY_SECONDS_AFTER_DETECT = 1;

    public static final int REARM_DELAY_SECONDS = 2;

    public static final int BOOT_INITIAL_WAIT_MS = 500;

    public static final int WATCHDOG_INTERVAL_SECONDS = 30;

    public static final int TAP_DEDUP_SECONDS = 3;

    public static final String LOGCAT_TAG = "AutoOk";

    public static final String FILE_LOG_NAME = "autook.log";

    public static final String HMI_SERVICE_START_ACTION =
        "com.mitsubishielectric.ada.appservice.powermanager.ACTION_HMI_SERVICE_START";

    public static final String ACTION_FORCE_RESTART =
        "com.khalleb.civichmi.autook.FORCE_RESTART";

    private AutoOkConfig() {
    }
}
