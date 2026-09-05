/*
 * meter_sim.c — host-side exercise harness for the NZIF panel meter.
 *
 * Builds and runs on the desktop with no Pico SDK. Drives meter.c with known
 * inputs and prints what the needle does, so the scale mapping, the detector
 * linearisation and the movement ballistics can all be checked against
 * numbers before any of it meets hardware.
 *
 *   make && ./meter_sim
 */

#include "meter.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

#define FRAME_HZ   60.0f
#define FRAME_DT   (1.0f / FRAME_HZ)

/* ------------------------------------------------------------------ *
 * ASCII rendering of the face, so the needle is visible and not just a
 * column of numbers.
 * ------------------------------------------------------------------ */

#define BAR_W 64

static void draw_scale_rx(void)
{
    char row[BAR_W + 1];
    const float marks_db[] = { -48, -36, -24, -12, 0, 10, 20, 30 };
    const char *lbl[]      = { "1", "3", "5", "7", "9", "+10", "+20", "+30" };
    char labels[BAR_W + 1];
    size_t i;

    memset(row, ' ', BAR_W);
    memset(labels, ' ', BAR_W);
    row[BAR_W] = labels[BAR_W] = '\0';

    for (i = 0; i < sizeof(marks_db) / sizeof(marks_db[0]); i++) {
        float f = meter_dbm_to_sweep(METER_S9_DBM + marks_db[i]);
        int c = (int)(f * (BAR_W - 1) + 0.5f);
        size_t n = strlen(lbl[i]);
        int start = c - (int)(n / 2);

        row[c] = '|';
        if (start < 0) {
            start = 0;
        }
        if (start + (int)n > BAR_W) {
            start = BAR_W - (int)n;
        }
        memcpy(labels + start, lbl[i], n);
    }
    printf("   %s   S UNITS\n", labels);
    printf("   %s\n", row);
}

static void draw_scale_swr(void)
{
    char row[BAR_W + 1];
    char labels[BAR_W + 1];
    const float marks[] = { 1.0f, 1.5f, 2.0f, 3.0f, 5.0f };
    const char *lbl[]   = { "1", "1.5", "2", "3", "5" };
    size_t i;

    memset(row, ' ', BAR_W);
    memset(labels, ' ', BAR_W);
    row[BAR_W] = labels[BAR_W] = '\0';

    for (i = 0; i < sizeof(marks) / sizeof(marks[0]); i++) {
        float f = meter_swr_to_sweep(marks[i]);
        int c = (int)(f * (BAR_W - 1) + 0.5f);
        size_t n = strlen(lbl[i]);
        int start = c - (int)(n / 2);

        row[c] = '|';
        if (start < 0) {
            start = 0;
        }
        if (start + (int)n > BAR_W) {
            start = BAR_W - (int)n;
        }
        memcpy(labels + start, lbl[i], n);
    }
    printf("   %s   SWR\n", labels);
    printf("   %s\n", row);
}

static void draw_needle(float f)
{
    char row[BAR_W + 1];
    int c;

    memset(row, '.', BAR_W);
    row[BAR_W] = '\0';

    c = (int)(f * (BAR_W - 1) + 0.5f);
    if (c < 0) {
        c = 0;
    }
    if (c > BAR_W - 1) {
        c = BAR_W - 1;
    }
    row[c] = '#';
    printf("   %s\n", row);
}

static void rule(const char *title)
{
    printf("\n");
    printf("== %s ", title);
    {
        int n = 72 - 4 - (int)strlen(title);
        int i;
        for (i = 0; i < n; i++) {
            putchar('=');
        }
    }
    printf("\n\n");
}

/* ------------------------------------------------------------------ *
 * Scenario 1 — receive, step to S7
 *
 * S7 is 12 dB below S9, so -85 dBm. This is the case asked for: the needle
 * starts at rest and has to get there and stay there.
 * ------------------------------------------------------------------ */

static void scenario_s7_step(void)
{
    meter_t m;
    meter_config_t cfg;
    char s[32];
    float dbm = METER_S9_DBM - 12.0f;      /* S7 = -85 dBm */
    float target, peak = 0.0f, settle_t = -1.0f;
    int frame;

    rule("Scenario 1: receive, step to S7 (-85 dBm)");

    meter_config_defaults(&cfg);
    meter_init(&m, &cfg);
    meter_set_mode(&m, METER_MODE_RX);

    meter_format_s(dbm, s, sizeof(s));
    target = meter_dbm_to_sweep(dbm);

    printf("  input        %.1f dBm   reads as %s\n", (double)dbm, s);
    printf("  target       %.4f of sweep\n", (double)target);
    printf("  CAT SM       %d  (Kenwood 0-30)\n", meter_cat_sm(dbm));
    printf("  movement     fn %.2f Hz, zeta %.2f, averaging %.0f ms\n\n",
           (double)cfg.fn_hz, (double)cfg.zeta, (double)cfg.avg_ms);

    printf("     t (ms)   needle    error     \n");
    printf("     ------   ------   -------    \n");

    for (frame = 0; frame <= (int)(2.5f * FRAME_HZ); frame++) {
        float t = frame * FRAME_DT;
        float n, err;

        meter_update_rx(&m, dbm);
        meter_tick(&m, FRAME_DT);
        n = meter_needle(&m);
        err = n - target;

        if (n > peak) {
            peak = n;
        }
        /* "settled" = within 1 % of sweep and staying there */
        if (fabsf(err) > 0.01f) {
            settle_t = -1.0f;
        } else if (settle_t < 0.0f) {
            settle_t = t;
        }

        if (frame % 6 == 0 && frame <= (int)(1.6f * FRAME_HZ)) {
            printf("     %6.0f   %6.4f   %+7.4f   ", (double)(t * 1000.0f),
                   (double)n, (double)err);
            draw_needle(n);
        }
    }

    printf("\n");
    draw_scale_rx();
    draw_needle(meter_needle(&m));
    printf("\n");
    /* Overshoot is quoted against the STEP, not against full sweep — that is
     * the quantity that compares to the textbook exp(-pi*zeta/sqrt(1-zeta^2))
     * and does not change when the step size does. */
    printf("  overshoot    %.1f %% of the step  (%.1f %% of full sweep)\n",
           (double)((peak - target) / target * 100.0f),
           (double)((peak - target) * 100.0f));
    if (settle_t >= 0.0f) {
        printf("  settled      %.0f ms to within 1 %% of sweep\n",
               (double)(settle_t * 1000.0f));
    } else {
        printf("  settled      never, within the 2.5 s window\n");
    }
    printf("  final        %.4f  (target %.4f)\n",
           (double)meter_needle(&m), (double)target);
}

/* ------------------------------------------------------------------ *
 * Scenario 2 — transmit, 2:1 SWR at 100 W
 *
 * The full round trip: true SWR -> reflected power -> coupler -> detector
 * volts -> back out through the linearisation -> recovered SWR -> needle.
 * ------------------------------------------------------------------ */

static void tx_detector_volts(float p_fwd_w, float swr_true,
                              float *v_fwd, float *v_rev)
{
    float coupling = powf(10.0f, -METER_COUPLING_DB / 10.0f);
    float rho = (swr_true - 1.0f) / (swr_true + 1.0f);
    float p_rev_w = p_fwd_w * rho * rho;

    *v_fwd = meter_detector_volts(p_fwd_w * coupling);
    *v_rev = meter_detector_volts(p_rev_w * coupling);
}

static void scenario_swr_2to1(void)
{
    meter_t m;
    meter_config_t cfg;
    char s[32];
    float p_fwd = 100.0f, swr_true = 2.0f;
    float v_fwd, v_rev;
    int frame;

    rule("Scenario 2: transmit, 2:1 SWR at 100 W");

    meter_config_defaults(&cfg);
    meter_init(&m, &cfg);
    meter_set_mode(&m, METER_MODE_TX);

    tx_detector_volts(p_fwd, swr_true, &v_fwd, &v_rev);

    printf("  at the antenna port\n");
    printf("    forward     %.1f W\n", (double)p_fwd);
    printf("    true SWR    %.2f:1   (rho %.4f, return loss %.1f dB)\n",
           (double)swr_true,
           (double)((swr_true - 1.0f) / (swr_true + 1.0f)),
           (double)(-20.0f * log10f((swr_true - 1.0f) / (swr_true + 1.0f))));
    printf("    reflected   %.2f W\n",
           (double)(p_fwd * powf((swr_true - 1.0f) / (swr_true + 1.0f), 2.0f)));

    printf("\n  what the Pico ADC actually sees, through a %.0f dB coupler\n",
           (double)METER_COUPLING_DB);
    printf("    V_fwd       %.4f V   (%4d counts of 4095 at 3.3 V)\n",
           (double)v_fwd, (int)(v_fwd / 3.3f * 4095.0f));
    printf("    V_rev       %.4f V   (%4d counts)\n",
           (double)v_rev, (int)(v_rev / 3.3f * 4095.0f));

    /* Settle the movement. */
    for (frame = 0; frame < (int)(2.0f * FRAME_HZ); frame++) {
        meter_update_tx(&m, v_fwd, v_rev, true);
        meter_tick(&m, FRAME_DT);
    }

    meter_format_swr(&m, s, sizeof(s));
    printf("\n  recovered by the firmware\n");
    printf("    SWR         %s   (error %+.3f)\n", s,
           (double)(m.tx_swr - swr_true));
    printf("    forward     %.1f W   (error %+.1f W)\n",
           (double)m.tx_fwd_w, (double)(m.tx_fwd_w - p_fwd));
    printf("    needle      %.4f of sweep\n\n", (double)meter_needle(&m));

    draw_scale_swr();
    draw_needle(meter_needle(&m));
}

/* ------------------------------------------------------------------ *
 * Scenario 3 — why the detectors have to be linearised
 *
 * True SWR held at 2:1 while drive is swept. The linearised path tracks it;
 * the naive square-root-law path collapses toward 1:1 as drive falls, which
 * is exactly the moment someone is tuning up and trusting the reading.
 * ------------------------------------------------------------------ */

static void scenario_detector_error(void)
{
    const float powers[] = { 100.0f, 50.0f, 20.0f, 10.0f, 5.0f, 2.0f, 1.0f, 0.5f };
    const float swr_true = 2.0f;
    size_t i;

    rule("Scenario 3: detector linearisation, true SWR held at 2:1");

    printf("     P_fwd    V_fwd     V_rev    linearised      naive     error\n");
    printf("       (W)      (V)       (V)                                  \n");
    printf("     -----   ------    ------    ----------    -------   -------\n");

    for (i = 0; i < sizeof(powers) / sizeof(powers[0]); i++) {
        float v_fwd, v_rev;
        float swr_lin = 0.0f, swr_naive = 0.0f;
        bool ok_lin, ok_naive;

        tx_detector_volts(powers[i], swr_true, &v_fwd, &v_rev);

        ok_lin   = meter_swr_from_detectors(v_fwd, v_rev, true,  &swr_lin,   NULL, NULL);
        ok_naive = meter_swr_from_detectors(v_fwd, v_rev, false, &swr_naive, NULL, NULL);

        printf("     %5.1f   %6.4f    %6.4f    ", (double)powers[i],
               (double)v_fwd, (double)v_rev);

        if (ok_lin) {
            printf("%6.3f:1    ", (double)swr_lin);
        } else {
            printf("   ---      ");
        }
        if (ok_naive) {
            printf("%5.3f:1   %+6.3f\n", (double)swr_naive,
                   (double)(swr_naive - swr_true));
        } else {
            printf("  ---         ---\n");
        }
    }

    printf("\n  The linearised column is flat because the inverse is exact.\n");
    printf("  The naive column reads low and gets worse as drive falls: the\n");
    printf("  reflected detector sits deeper in square law than the forward\n");
    printf("  one, so the ratio — and therefore the SWR — is understated.\n");
}

/* ------------------------------------------------------------------ *
 * Scenario 4 — where the scale marks actually land
 * ------------------------------------------------------------------ */

static void scenario_scale_map(void)
{
    const float s_units[] = { 1, 3, 5, 7, 9 };
    const float over[]    = { 10, 20, 30 };
    const float swrs[]    = { 1.0f, 1.5f, 2.0f, 3.0f, 5.0f, 10.0f };
    size_t i;

    rule("Scenario 4: scale mapping");

    printf("  Receive — S-unit scale\n");
    printf("     mark      dBm      uV(50R)    sweep    CAT SM\n");
    printf("     ------   ------    -------   ------    ------\n");
    for (i = 0; i < sizeof(s_units) / sizeof(s_units[0]); i++) {
        float dbm = METER_S9_DBM + (s_units[i] - 9.0f) * METER_DB_PER_S;
        float uv = sqrtf(powf(10.0f, dbm / 10.0f) * 1e-3f * 50.0f) * 1e6f;
        printf("     S%-5.0f   %6.1f    %7.2f   %6.4f    %4d\n",
               (double)s_units[i], (double)dbm, (double)uv,
               (double)meter_dbm_to_sweep(dbm), meter_cat_sm(dbm));
    }
    for (i = 0; i < sizeof(over) / sizeof(over[0]); i++) {
        float dbm = METER_S9_DBM + over[i];
        float uv = sqrtf(powf(10.0f, dbm / 10.0f) * 1e-3f * 50.0f) * 1e6f;
        printf("     S9+%-3.0f   %6.1f    %7.2f   %6.4f    %4d\n",
               (double)over[i], (double)dbm, (double)uv,
               (double)meter_dbm_to_sweep(dbm), meter_cat_sm(dbm));
    }

    printf("\n  Note the compression: S1-S9 spans 48 dB over %.3f of sweep,\n",
           (double)(meter_dbm_to_sweep(METER_S9_DBM)
                    - meter_dbm_to_sweep(METER_S9_DBM - 48.0f)));
    printf("  while S9+30 spans 30 dB over only %.3f. That is the Model 540\n",
           (double)(1.0f - meter_dbm_to_sweep(METER_S9_DBM)));
    printf("  face, not a modelling convenience.\n");

    printf("\n  Transmit — SWR scale, from rho = (SWR-1)/(SWR+1)\n");
    printf("     mark      rho     sweep\n");
    printf("     ------   -----   ------\n");
    for (i = 0; i < sizeof(swrs) / sizeof(swrs[0]); i++) {
        printf("     %4.1f:1   %5.3f   %6.4f\n", (double)swrs[i],
               (double)((swrs[i] - 1.0f) / (swrs[i] + 1.0f)),
               (double)meter_swr_to_sweep(swrs[i]));
    }
}

/* ------------------------------------------------------------------ *
 * Scenario 5 — choosing the damping ratio
 * ------------------------------------------------------------------ */

static void scenario_damping(void)
{
    const float zetas[] = { 0.3f, 0.5f, 0.65f, 0.8f, 1.0f, 1.3f };
    const float dbm = METER_S9_DBM - 12.0f;    /* step to S7 again */
    float target = meter_dbm_to_sweep(dbm);
    meter_config_t defaults;
    float cfg_avg_used;
    size_t i;

    meter_config_defaults(&defaults);
    cfg_avg_used = defaults.avg_ms;

    rule("Scenario 5: damping ratio, on the same S7 step");

    printf("     zeta   overshoot   settle (1%%)   character\n");
    printf("            (of step)                          \n");
    printf("     ----   ---------   -----------   ---------\n");

    for (i = 0; i < sizeof(zetas) / sizeof(zetas[0]); i++) {
        meter_t m;
        meter_config_t cfg;
        float peak = 0.0f, settle = -1.0f;
        int frame;
        const char *note;

        meter_config_defaults(&cfg);
        cfg.zeta = zetas[i];
        meter_init(&m, &cfg);

        for (frame = 0; frame < (int)(6.0f * FRAME_HZ); frame++) {
            float t = frame * FRAME_DT;
            float n;

            meter_update_rx(&m, dbm);
            meter_tick(&m, FRAME_DT);
            n = meter_needle(&m);

            if (n > peak) {
                peak = n;
            }
            if (fabsf(n - target) > 0.01f) {
                settle = -1.0f;
            } else if (settle < 0.0f) {
                settle = t;
            }
        }

        note = (zetas[i] < 0.45f) ? "rings, looks broken"
             : (zetas[i] < 0.60f) ? "lively, slow to settle"
             : (zetas[i] < 0.75f) ? "like a real movement"
             : (zetas[i] < 0.95f) ? "fast, but barely overshoots"
             : (zetas[i] < 1.05f) ? "critical, no overshoot"
                                  : "sluggish, reads cheap";

        if (settle >= 0.0f) {
            printf("     %4.2f   %8.1f%%   %9.0f ms   %s\n",
                   (double)zetas[i],
                   (double)((peak - target) / target * 100.0f),
                   (double)(settle * 1000.0f), note);
        } else {
            printf("     %4.2f   %8.1f%%   %12s   %s\n",
                   (double)zetas[i],
                   (double)((peak - target) / target * 100.0f),
                   "never", note);
        }
    }

    printf("\n  0.65 is the default: about 7 %% overshoot on the step, settled\n");
    printf("  inside half a second. Note the settle column is not monotonic —\n");
    printf("  0.80 gets inside the 1 %% band fastest, but with so little\n");
    printf("  overshoot that the needle stops looking like it has mass.\n");
    printf("\n  These figures assume the default %.0f ms of averaging. Raising\n",
           (double)cfg_avg_used);
    printf("  that suppresses the overshoot regardless of zeta — at 100 ms\n");
    printf("  even zeta 0.4 barely overshoots at all.\n");
}

/* ------------------------------------------------------------------ *
 * Scenario 6 — CW keying, where ballistics are actually judged
 *
 * A steady signal tells you almost nothing about the movement. Keyed carrier
 * does: the needle should indicate presence without slamming into the stops
 * on every dot.
 * ------------------------------------------------------------------ */

static void scenario_cw(void)
{
    meter_t m;
    meter_config_t cfg;
    const float dot = 0.06f;                   /* 20 wpm: 1.2/20 = 60 ms */
    const float on_dbm = METER_S9_DBM;         /* S9 while keyed */
    const float off_dbm = -115.0f;
    float lo = 1.0f, hi = 0.0f;
    int frame;

    rule("Scenario 6: keyed carrier, 20 wpm, S9 peaks");

    meter_config_defaults(&cfg);
    meter_init(&m, &cfg);

    printf("     t (ms)   key   needle\n");
    printf("     ------   ---   ------\n");

    for (frame = 0; frame < (int)(1.8f * FRAME_HZ); frame++) {
        float t = frame * FRAME_DT;
        /* PARIS-ish: dot dot dash, with spacing */
        static const int pattern[] = { 1,0,1,0,1,1,1,0,0,0,1,0,1,1,1,0 };
        int idx = ((int)(t / dot)) % (int)(sizeof(pattern) / sizeof(pattern[0]));
        int on = pattern[idx];
        float n;

        meter_update_rx(&m, on ? on_dbm : off_dbm);
        meter_tick(&m, FRAME_DT);
        n = meter_needle(&m);

        if (t > 0.4f) {                       /* ignore the initial rise */
            if (n < lo) { lo = n; }
            if (n > hi) { hi = n; }
        }

        if (frame % 3 == 0) {
            printf("     %6.0f    %s   %6.4f   ", (double)(t * 1000.0f),
                   on ? "ON " : "off", (double)n);
            draw_needle(n);
        }
    }

    printf("\n  swing after settling   %.4f to %.4f  (%.1f %% of sweep)\n",
           (double)lo, (double)hi, (double)((hi - lo) * 100.0f));
    printf("\n  The needle does NOT sit still — it swings across almost half\n");
    printf("  the scale at every dot, and no realistic amount of averaging\n");
    printf("  removes that: measured, the swing only falls from ~52 %% of\n");
    printf("  sweep at 0 ms to ~18 %% at 250 ms, by which point the meter is\n");
    printf("  too sluggish to be useful on SSB.\n");
    printf("\n  This is correct behaviour, not a defect. A real S-meter bounces\n");
    printf("  on CW for the same reason, and operators read the peak. It does\n");
    printf("  mean the peak-hold option is worth more on CW than the Model 540\n");
    printf("  precedent suggests — see the open question in the README.\n");
}

/* ------------------------------------------------------------------ */

int main(void)
{
    printf("\n");
    printf("NZIF panel meter — algorithm exercise\n");
    printf("S9 = %.0f dBm, %.0f dB per S-unit, %.0f dB coupler\n",
           (double)METER_S9_DBM, (double)METER_DB_PER_S,
           (double)METER_COUPLING_DB);

    scenario_s7_step();
    scenario_swr_2to1();
    scenario_detector_error();
    scenario_scale_map();
    scenario_damping();
    scenario_cw();

    printf("\n");
    return 0;
}
