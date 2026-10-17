package com.khalleb.civichmi.autook;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class HmiServiceReceiver extends BroadcastReceiver {

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) {
            return;
        }
        String action = intent.getAction();
        if (!AutoOkConfig.HMI_SERVICE_START_ACTION.equals(action)) {
            return;
        }
        Intent svc = new Intent(context, AutoOkService.class);
        svc.setAction(AutoOkConfig.ACTION_FORCE_RESTART);
        try {
            svc.putExtra("source", "hmi_broadcast");
            String extraCause = intent.getStringExtra("state");
            if (extraCause != null) {
                svc.putExtra("cause", extraCause);
            }
        } catch (Throwable ignored) {
        }
        context.startService(svc);
    }
}
