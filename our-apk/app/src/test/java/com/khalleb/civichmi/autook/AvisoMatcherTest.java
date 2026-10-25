package com.khalleb.civichmi.autook;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class AvisoMatcherTest {

    private static final String NEEDLE = AutoOkConfig.AVISO_ACTIVITY_NAME;

    private static String linha(String evento, String action) {
        return "10-25 08:00:01.123  1200  1200 I " + evento + ": [0,999," + NEEDLE + "," + action + "]";
    }

    @Test
    public void deveCasar_coldBoot_amCreateActivityComNormalStartup() {
        assertTrue(AvisoMatcher.matches(linha(AvisoMatcher.EVENT_CREATE, AvisoMatcher.ACTION_NORMAL), NEEDLE));
    }

    @Test
    public void deveCasar_lp0Resume_amNewIntentComNormalStartup() {
        assertTrue(AvisoMatcher.matches(linha(AvisoMatcher.EVENT_NEW_INTENT, AvisoMatcher.ACTION_NORMAL), NEEDLE));
    }

    @Test
    public void naoDeveCasar_quandoActionEhPrecedingStartup() {
        assertFalse(AvisoMatcher.matches(linha(AvisoMatcher.EVENT_CREATE, "dalauncher.action.PRECEDING_STARTUP"), NEEDLE));
    }

    @Test
    public void naoDeveCasar_quandoEventoEhDestroy() {
        assertFalse(AvisoMatcher.matches(linha("am_destroy_activity", AvisoMatcher.ACTION_NORMAL), NEEDLE));
    }

    @Test
    public void naoDeveCasar_quandoLinhaEhDeOutraActivity() {
        String outra = "10-25 08:00:01.123  1200  1200 I " + AvisoMatcher.EVENT_CREATE
            + ": [0,999,com.mitsubishielectric.ada.app.camera/.RearWideCameraDisplayActivity,"
            + AvisoMatcher.ACTION_NORMAL + "]";
        assertFalse(AvisoMatcher.matches(outra, NEEDLE));
    }

    @Test
    public void naoDeveCasar_linhaIrrelevante() {
        assertFalse(AvisoMatcher.matches("10-25 08:00:01.123  1200  1200 I SomeTag: nada a ver", NEEDLE));
    }

    @Test
    public void naoDeveCasar_entradasNulas() {
        assertFalse(AvisoMatcher.matches(null, NEEDLE));
        assertFalse(AvisoMatcher.matches("qualquer", null));
    }
}
