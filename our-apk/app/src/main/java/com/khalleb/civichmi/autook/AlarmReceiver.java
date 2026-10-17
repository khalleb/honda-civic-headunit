package com.khalleb.civichmi.autook;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class AlarmReceiver extends BroadcastReceiver {

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) {
            return;
        }
        if (!AutoOkConfig.ACTION_ALARM_HEALTHCHECK.equals(intent.getAction())) {
            return;
        }
        Intent svc = new Intent(context, AutoOkService.class);
        svc.setAction(AutoOkConfig.ACTION_FORCE_RESTART);
        svc.putExtra("source", "alarm_60s");
        context.startService(svc);
    }
}
