package com.khalleb.civichmi.autook;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class TapDeduperTest {

    private static final int DEDUP = 3;

    @Test
    public void naoSuprime_primeiroTap_quandoNuncaHouveTapAntes() {
        assertFalse(TapDeduper.shouldSuppress(10_000L, 0L, DEDUP));
    }

    @Test
    public void suprime_quandoDentroDaJanelaDeDedup() {
        assertTrue(TapDeduper.shouldSuppress(11_000L, 10_000L, DEDUP));
    }

    @Test
    public void naoSuprime_quandoForaDaJanela() {
        assertFalse(TapDeduper.shouldSuppress(14_001L, 10_000L, DEDUP));
    }

    @Test
    public void naoSuprime_exatamenteNaBordaDaJanela() {
        assertFalse(TapDeduper.shouldSuppress(13_000L, 10_000L, DEDUP));
    }
}
