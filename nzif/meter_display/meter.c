/*
 * meter.c — NZIF front-panel meter implementation.
 *
 * See meter.h for the interface and for what the constants mean.
 */

#include "meter.h"

#include <math.h>
#include <stdio.h>

/* M_PI is POSIX, not C99 — define our own so this builds under -std=c99. */
#define METER_TWO_PI 6.28318530717958647692f

/* ------------------------------------------------------------------ *
 * Scale calibration
 *
 * Anchors measured from label positions in the reference photograph of the
 * Ten-Tec Model 540 face (nzif/meter_display/ten tec meter.jpeg).
 *
 *   db  — level relative to S9, in dB
 *   f   — fraction of total needle sweep
 *
 * Interpolation between anchors is linear, so a single mark can be trimmed
 * without disturbing the rest of the face.
 *
 * CAVEAT: the reference photograph is taken at an angle with lamp glare
 * across the face. These are good to perhaps a couple of percent of sweep —
 * enough to build against, not enough to cut artwork from.
 * ------------------------------------------------------------------ */

typedef struct {
    float db;
    float f;
} anchor_t;

static const anchor_t S_ANCHORS[] = {
    { -48.0f, 0.000f },   /* S1  */
    { -36.0f, 0.205f },   /* S3  */
    { -24.0f, 0.393f },   /* S5  */
    { -12.0f, 0.564f },   /* S7  */
    {   0.0f, 0.701f },   /* S9  */
    {  10.0f, 0.769f },   /* +10 */
    {  20.0f, 0.897f },   /* +20 */
    {  30.0f, 1.000f }    /* +30 */
};

static const size_t N_ANCHORS = sizeof(S_ANCHORS) / sizeof(S_ANCHORS[0]);

float meter_dbm_to_sweep(float dbm)
{
    float rel = dbm - METER_S9_DBM;
    size_t i;

    if (rel <= S_ANCHORS[0].db) {
        return 0.0f;
    }
    if (rel >= S_ANCHORS[N_ANCHORS - 1].db) {
        return 1.0f;
    }

    for (i = 0; i + 1 < N_ANCHORS; i++) {
        if (rel <= S_ANCHORS[i + 1].db) {
            float span = S_ANCHORS[i + 1].db - S_ANCHORS[i].db;
            float t = (rel - S_ANCHORS[i].db) / span;
            return S_ANCHORS[i].f + t * (S_ANCHORS[i + 1].f - S_ANCHORS[i].f);
        }
    }
    return 1.0f;
}

float meter_swr_to_sweep(float swr)
{
    if (!(swr >= 1.0f)) {          /* also catches NaN */
        return 0.0f;
    }
    return (swr - 1.0f) / (swr + 1.0f);   /* = rho, reflection coefficient */
}

/* ------------------------------------------------------------------ *
 * Detector model
 * ------------------------------------------------------------------ */

float meter_detector_volts(float p_watts)
{
    float x;

    if (p_watts <= 0.0f) {
        return 0.0f;
    }
    x = p_watts / METER_P_KNEE_W;
    return METER_V_KNEE_V * x / sqrtf(1.0f + x);
}

float meter_detector_watts(float v)
{
    float r, r2;

    if (v <= 0.0f) {
        return 0.0f;
    }
    r = v / METER_V_KNEE_V;
    r2 = r * r;
    /* x^2 - r^2 x - r^2 = 0, positive root */
    return METER_P_KNEE_W * (r2 + sqrtf(r2 * r2 + 4.0f * r2)) * 0.5f;
}

float meter_detector_watts_naive(float v)
{
    float r;

    if (v <= 0.0f) {
        return 0.0f;
    }
    r = v / METER_V_KNEE_V;
    return METER_P_KNEE_W * r * r;
}

bool meter_swr_from_detectors(float v_fwd, float v_rev, bool linearise,
                              float *swr, float *p_fwd_w, float *p_rev_w)
{
    float coupling = powf(10.0f, -METER_COUPLING_DB / 10.0f);
    float pf_det, pr_det, pf_line, pr_line, ratio, rho;

    if (linearise) {
        pf_det = meter_detector_watts(v_fwd);
        pr_det = meter_detector_watts(v_rev);
    } else {
        pf_det = meter_detector_watts_naive(v_fwd);
        pr_det = meter_detector_watts_naive(v_rev);
    }

    /* Refer both back through the coupler to the antenna port. */
    pf_line = pf_det / coupling;
    pr_line = pr_det / coupling;

    if (p_fwd_w != NULL) {
        *p_fwd_w = pf_line;
    }
    if (p_rev_w != NULL) {
        *p_rev_w = pr_line;
    }

    if (pf_line < METER_MIN_TX_W) {
        return false;
    }

    ratio = pr_line / pf_line;
    if (ratio < 0.0f) {
        ratio = 0.0f;
    }
    if (ratio > 0.998f) {          /* keep the SWR expression finite */
        ratio = 0.998f;
    }

    rho = sqrtf(ratio);
    if (swr != NULL) {
        *swr = (1.0f + rho) / (1.0f - rho);
    }
    return true;
}

/* ------------------------------------------------------------------ *
 * Movement
 * ------------------------------------------------------------------ */

void meter_config_defaults(meter_config_t *cfg)
{
    if (cfg == NULL) {
        return;
    }
    cfg->fn_hz      = 2.2f;    /* where real panel meters sit */
    cfg->zeta       = 0.65f;   /* under-damped: ~6.8 % overshoot, then settles */
    /*
     * Deliberately small. The movement itself is already a heavy low-pass at
     * 2.2 Hz, so this averaging is only here to take the edge off ADC noise.
     * Turning it up destroys the overshoot that makes the needle read as a
     * physical object: measured on a step to S7, overshoot falls from 6.8 %
     * of the step at 0 ms, to 3.6 % at 60 ms, to almost nothing by 100 ms.
     */
    cfg->avg_ms     = 25.0f;
    cfg->end_stops  = true;
    cfg->peak_hold  = false;
    cfg->peak_decay = 0.22f;
}

void meter_init(meter_t *m, const meter_config_t *cfg)
{
    meter_config_t defaults;

    if (m == NULL) {
        return;
    }
    if (cfg == NULL) {
        meter_config_defaults(&defaults);
        cfg = &defaults;
    }

    m->cfg      = *cfg;
    m->mode     = METER_MODE_RX;
    m->theta    = 0.0f;
    m->omega    = 0.0f;
    m->smoothed = 0.0f;
    m->peak     = 0.0f;
    m->target   = 0.0f;
    m->rx_dbm   = -140.0f;
    m->tx_swr   = -1.0f;
    m->tx_fwd_w = 0.0f;
    m->tx_rev_w = 0.0f;
    m->tx_valid = false;
}

void meter_set_mode(meter_t *m, meter_mode_t mode)
{
    if (m == NULL || m->mode == mode) {
        return;
    }
    m->mode = mode;
    m->peak = 0.0f;      /* peak hold does not carry across a T/R transition */
}

void meter_update_rx(meter_t *m, float dbm)
{
    if (m == NULL) {
        return;
    }
    m->rx_dbm = dbm;
    m->target = meter_dbm_to_sweep(dbm);
}

void meter_update_tx(meter_t *m, float v_fwd, float v_rev, bool linearise)
{
    float swr = 1.0f;

    if (m == NULL) {
        return;
    }

    m->tx_valid = meter_swr_from_detectors(v_fwd, v_rev, linearise,
                                           &swr, &m->tx_fwd_w, &m->tx_rev_w);
    if (m->tx_valid) {
        m->tx_swr = swr;
        m->target = meter_swr_to_sweep(swr);
    } else {
        m->tx_swr = -1.0f;
        m->target = 0.0f;    /* hold at rest rather than show garbage */
    }
}

void meter_tick(meter_t *m, float dt_s)
{
    const float sub_step = 0.001f;   /* fixed 1 ms, so behaviour is rate-independent */
    float applied, wn, h;
    int steps, i;

    if (m == NULL || dt_s <= 0.0f) {
        return;
    }
    if (dt_s > 0.25f) {
        dt_s = 0.25f;                /* do not integrate across a long stall */
    }

    /* Averaging ahead of the movement (the AGC-side time constant). */
    if (m->cfg.avg_ms > 0.0f) {
        float alpha = 1.0f - expf(-dt_s / (m->cfg.avg_ms * 0.001f));
        m->smoothed += (m->target - m->smoothed) * alpha;
    } else {
        m->smoothed = m->target;
    }

    applied = m->smoothed;
    if (m->cfg.peak_hold) {
        m->peak -= m->cfg.peak_decay * dt_s;
        if (m->smoothed > m->peak) {
            m->peak = m->smoothed;
        }
        applied = m->peak;
    }

    /*
     * Damped second-order movement:
     *
     *     theta'' = wn^2 (target - theta) - 2 zeta wn theta'
     *
     * Semi-implicit Euler at a fixed sub-step. On an M0+ with no FPU this is
     * a few hundred soft-float operations per frame at 60 Hz — negligible
     * against a 133 MHz core.
     */
    wn = METER_TWO_PI * m->cfg.fn_hz;
    steps = (int)(dt_s / sub_step);
    if (steps < 1) {
        steps = 1;
    }
    if (steps > 250) {
        steps = 250;
    }
    h = dt_s / (float)steps;

    for (i = 0; i < steps; i++) {
        float acc = wn * wn * (applied - m->theta) - 2.0f * m->cfg.zeta * wn * m->omega;
        m->omega += acc * h;
        m->theta += m->omega * h;

        if (m->cfg.end_stops) {
            if (m->theta < 0.0f) {
                m->theta = 0.0f;
                if (m->omega < 0.0f) {
                    m->omega *= -0.18f;      /* bounce off the stop, losing energy */
                }
            }
            if (m->theta > 1.04f) {
                m->theta = 1.04f;
                if (m->omega > 0.0f) {
                    m->omega *= -0.18f;
                }
            }
        }
    }
}

float meter_needle(const meter_t *m)
{
    return (m != NULL) ? m->theta : 0.0f;
}

/* ------------------------------------------------------------------ *
 * Display helpers
 * ------------------------------------------------------------------ */

void meter_format_s(float dbm, char *buf, size_t n)
{
    float rel, s, over;
    int s_int;

    if (buf == NULL || n == 0) {
        return;
    }

    rel = dbm - METER_S9_DBM;

    if (rel >= 0.0f) {
        snprintf(buf, n, "S9+%d dB", (int)(rel + 0.5f));
        return;
    }

    s = 9.0f + rel / METER_DB_PER_S;
    if (s < 1.0f) {
        snprintf(buf, n, "below S1");
        return;
    }

    s_int = (int)s;
    over = (s - (float)s_int) * METER_DB_PER_S;

    if (over >= 1.0f) {
        snprintf(buf, n, "S%d+%d dB", s_int, (int)(over + 0.5f));
    } else {
        snprintf(buf, n, "S%d", s_int);
    }
}

void meter_format_swr(const meter_t *m, char *buf, size_t n)
{
    if (buf == NULL || n == 0) {
        return;
    }
    if (m == NULL || !m->tx_valid) {
        snprintf(buf, n, "---");
        return;
    }
    if (m->tx_swr > 9.95f) {
        snprintf(buf, n, ">10:1");
        return;
    }
    snprintf(buf, n, "%.2f:1", (double)m->tx_swr);
}

int meter_cat_sm(float dbm)
{
    float rel = dbm - METER_S9_DBM;
    float v;

    if (rel < 0.0f) {
        /* S0..S9 maps to 0..15 */
        float s = 9.0f + rel / METER_DB_PER_S;
        v = (s < 0.0f) ? 0.0f : s * (15.0f / 9.0f);
    } else {
        /* S9..S9+60 dB maps to 15..30 */
        v = 15.0f + rel * 0.25f;
    }

    if (v < 0.0f) {
        v = 0.0f;
    }
    if (v > 30.0f) {
        v = 30.0f;
    }
    return (int)(v + 0.5f);
}
