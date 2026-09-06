/*
 * main.c — NZIF panel meter demo for the Nextion NX4832T035_011.
 *
 * Draws the Ten-Tec-style S-meter face on the panel and runs it from a
 * synthetic receive signal: a noisy HF band with an SSB station on it.
 *
 * All the metering itself — the S-unit scale mapping and the moving-coil
 * ballistics — comes from nzif/meter_display/meter.c, unchanged. This file
 * only generates a plausible signal and paces the frames.
 */

#include "face.h"
#include "meter.h"
#include "nextion.h"

#include <math.h>
#include <stdio.h>

#include "pico/stdlib.h"

#define FRAME_HZ     30
#define FRAME_US     (1000000 / FRAME_HZ)
#define READOUT_MS   200

/* Smallest needle move worth sending. One thousandth of sweep is about
 * 0.4 px at the tip, so anything below this is invisible traffic. */
#define MOVE_EPS     0.0015f

/* ------------------------------------------------------------------ *
 * Synthetic signal: a noisy band with an SSB station
 * ------------------------------------------------------------------ */

static uint32_t g_rng = 0x1234567u;

static float frandf(void)
{
    /* xorshift32 — cheap, and we want repeatable texture, not cryptography */
    g_rng ^= g_rng << 13;
    g_rng ^= g_rng >> 17;
    g_rng ^= g_rng << 5;
    return (float)(g_rng & 0xFFFFFF) / (float)0xFFFFFF;
}

static float demo_dbm(float t, float dt)
{
    static float noise_dbm = -110.0f;
    float n, syl, env, over, qsb, peak, sp, pn, ps;

    /*
     * Band noise. A random walk pulled back towards a floor around
     * -110 dBm, which is a little under S3 — enough to keep the needle
     * alive between overs, as a real band does.
     */
    noise_dbm += (frandf() - 0.5f) * 9.0f * dt;
    noise_dbm += (-110.0f - noise_dbm) * 1.6f * dt;
    n = noise_dbm + (frandf() - 0.5f) * 2.0f;

    /*
     * Speech envelope. Three sines at incommensurate rates give syllable,
     * word and phrase structure without sounding periodic; the exponent
     * sharpens the attack so peaks read like speech rather than a sine.
     */
    syl = sinf(t * 5.3f) * sinf(t * 1.87f) * sinf(t * 0.73f);
    env = (syl > 0.0f) ? powf(syl, 0.45f) : 0.0f;

    /* The station stops to listen every half minute or so. */
    over = sinf(t * 0.085f);
    if (over < -0.25f) {
        env = 0.0f;
    }

    /* Slow fading, so the peaks wander over about two S-units. */
    qsb  = 0.5f * (1.0f + 0.6f * sinf(t * 0.21f) + 0.4f * sinf(t * 0.13f + 1.1f));
    peak = -88.0f + 10.0f * qsb;

    sp = -125.0f + (peak + 125.0f) * env;

    /* Noise and signal add as powers, not as decibels. */
    pn = powf(10.0f, n  * 0.1f);
    ps = powf(10.0f, sp * 0.1f);
    return 10.0f * log10f(pn + ps);
}

/* ------------------------------------------------------------------ */

int main(void)
{
    meter_t        m;
    meter_config_t cfg;
    absolute_time_t next;
    uint64_t t_us0;
    float last_f;
    uint32_t last_readout = 0;

    stdio_init_all();          /* USB serial, for debug only */

    sleep_ms(1200);            /* let the panel finish its own power-up */
    nex_init();
    face_init();

    meter_config_defaults(&cfg);
    meter_init(&m, &cfg);
    meter_set_mode(&m, METER_MODE_RX);

    face_readout(2, "SSB");

    last_f = meter_needle(&m);
    face_needle_first(last_f);

    t_us0 = time_us_64();
    next  = get_absolute_time();

    for (;;) {
        float dt = 1.0f / (float)FRAME_HZ;
        float t  = (float)((time_us_64() - t_us0) / 1000u) * 0.001f;
        float dbm, f;
        uint32_t now_ms;

        dbm = demo_dbm(t, dt);
        meter_update_rx(&m, dbm);
        meter_tick(&m, dt);

        f = meter_needle(&m);
        if (fabsf(f - last_f) > MOVE_EPS) {
            face_needle(last_f, f);
            last_f = f;
        }

        now_ms = (uint32_t)((time_us_64() - t_us0) / 1000u);
        if (now_ms - last_readout >= READOUT_MS) {
            char s[24];
            last_readout = now_ms;

            meter_format_s(m.rx_dbm, s, sizeof(s));
            face_readout(0, s);

            snprintf(s, sizeof(s), "%d dBm", (int)lrintf(m.rx_dbm));
            face_readout(1, s);
        }

        next = delayed_by_us(next, FRAME_US);
        sleep_until(next);
    }
}
