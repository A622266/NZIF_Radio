/*
 * meter.h — NZIF front-panel meter: scale mapping, detector linearisation,
 *           and moving-coil ballistics.
 *
 * Portable C99. No dependencies beyond <math.h> and <stdbool.h>, so it
 * builds on the host for test and drops into the Pico firmware unchanged.
 *
 * Two jobs:
 *   RECEIVE  — take a level estimate in dBm from the ADAU1467 and place the
 *              needle on the S-unit scale.
 *   TRANSMIT — take the two Schottky detector voltages from the directional
 *              coupler, recover true SWR, and place the needle on the SWR scale.
 *
 * In both cases the needle position is a fraction of full sweep, 0.0 at the
 * left stop and 1.0 at full scale, which is what the renderer wants.
 */

#ifndef NZIF_METER_H
#define NZIF_METER_H

#include <stdbool.h>
#include <stddef.h>

/* ------------------------------------------------------------------ *
 * Scale constants
 * ------------------------------------------------------------------ */

#define METER_S9_DBM      (-73.0f)  /* S9 at the antenna, 50 ohm, HF */
#define METER_DB_PER_S      (6.0f)  /* one S-unit */

/* Directional coupler and detector constants.
 *
 * These are the numbers to fit at bring-up: drive a known power into a known
 * load, read both ADC channels, and solve. The values here are a physically
 * sensible starting point for a -40 dB coupler feeding an HSMS-286x-class
 * detector, giving about 2.0 V at 100 W forward — a comfortable span for the
 * RP2040's 3.3 V ADC without clipping. */
#define METER_COUPLING_DB   (40.0f)
#define METER_P_KNEE_W     (1.0e-5f) /* detector square-law/linear transition */
#define METER_V_KNEE_V    (0.0633f)  /* detector output at that knee */

/* Below this forward power the reflected reading is noise and SWR is
 * meaningless. The meter holds at rest rather than displaying garbage. */
#define METER_MIN_TX_W      (0.3f)

typedef enum {
    METER_MODE_RX = 0,
    METER_MODE_TX = 1
} meter_mode_t;

/* ------------------------------------------------------------------ *
 * Movement configuration
 * ------------------------------------------------------------------ */

typedef struct {
    float fn_hz;        /* natural frequency; real panel meters sit near 2-3 Hz */
    float zeta;         /* damping ratio; < 1 overshoots, as a real movement does */
    float avg_ms;       /* averaging applied to the level estimate, 0 to disable */
    bool  end_stops;    /* peg at the ends and lose energy, rather than pass them */
    bool  peak_hold;    /* hold the peak and decay slowly (the 540 has no such thing) */
    float peak_decay;   /* sweep fractions per second, when peak_hold is set */
} meter_config_t;

/* Sensible defaults, matching the values arrived at in the visual prototype. */
void meter_config_defaults(meter_config_t *cfg);

/* ------------------------------------------------------------------ *
 * Meter instance
 * ------------------------------------------------------------------ */

typedef struct {
    meter_config_t cfg;
    meter_mode_t   mode;

    /* movement state, in sweep-fraction units */
    float theta;        /* needle position */
    float omega;        /* needle velocity */
    float smoothed;     /* averaged target */
    float peak;

    /* most recent computed values, for display */
    float target;       /* where the needle is being asked to go, 0..1 */
    float rx_dbm;       /* last receive level */
    float tx_swr;       /* last recovered SWR; < 0 when there is no usable drive */
    float tx_fwd_w;     /* last recovered forward power at the antenna port */
    float tx_rev_w;
    bool  tx_valid;     /* false below METER_MIN_TX_W */
} meter_t;

void meter_init(meter_t *m, const meter_config_t *cfg);
void meter_set_mode(meter_t *m, meter_mode_t mode);

/* Feed the meter. Call whichever matches the current mode, then meter_tick(). */
void meter_update_rx(meter_t *m, float dbm);
void meter_update_tx(meter_t *m, float v_fwd, float v_rev, bool linearise);

/* Advance the movement by dt seconds. Integrated at a fixed sub-step so
 * behaviour does not change with call rate. */
void meter_tick(meter_t *m, float dt_s);

/* Needle position, 0..1 of full sweep (slightly beyond 1.0 when pegged). */
float meter_needle(const meter_t *m);

/* ------------------------------------------------------------------ *
 * Pure scale mapping — no state, safe to call anywhere
 * ------------------------------------------------------------------ */

/* Signal level in dBm to fraction of sweep, via the measured anchor table.
 * The mapping is deliberately NOT linear in dB: it reproduces the Model 540
 * face, where S1-S9 takes ~70 % of the sweep for 48 dB and +10/+20/+30 are
 * compressed into the remaining ~30 % for 30 dB. */
float meter_dbm_to_sweep(float dbm);

/* SWR to fraction of sweep. A moving-coil movement deflects on reflected
 * VOLTAGE, so this is just rho = (SWR-1)/(SWR+1): 1:1 at rest, 2:1 at one
 * third, 3:1 at one half, 5:1 at two thirds, open circuit at full scale. */
float meter_swr_to_sweep(float swr);

/* ------------------------------------------------------------------ *
 * Detector model
 * ------------------------------------------------------------------ */

/* Forward model — power at the detector to output volts. A Schottky detector
 * is square-law at low drive and linear at high drive:
 *
 *     V = Vk * x / sqrt(1 + x),   x = P / Pk
 *
 * As x -> 0,   V ~ Vk*x        (output follows POWER)
 * As x -> inf, V ~ Vk*sqrt(x)  (output follows VOLTAGE)
 *
 * Present here mainly to document and test the inverse below. */
float meter_detector_volts(float p_watts);

/* Exact inverse of the above. Solving r = x/sqrt(1+x) for x gives
 *
 *     x = (r^2 + sqrt(r^4 + 4 r^2)) / 2,   r = V / Vk
 *
 * which is closed-form, so the firmware needs no lookup table. */
float meter_detector_watts(float v);

/* The inverse the firmware would use if it wrongly assumed a plain linear
 * (square-root-law) detector throughout. Correct near full power, badly wrong
 * at low drive — which is exactly when someone is tuning up. Kept so the
 * error can be measured rather than argued about. */
float meter_detector_watts_naive(float v);

/* Recover SWR and forward power from the two detector voltages.
 * Returns false when forward power is below METER_MIN_TX_W, in which case
 * *swr is left untouched and the reading should be blanked. */
bool meter_swr_from_detectors(float v_fwd, float v_rev, bool linearise,
                              float *swr, float *p_fwd_w, float *p_rev_w);

/* ------------------------------------------------------------------ *
 * Display helpers
 * ------------------------------------------------------------------ */

/* "S7", "S9+20 dB", "below S1". Writes at most n bytes including the NUL. */
void meter_format_s(float dbm, char *buf, size_t n);

/* "2.00:1", or "---" when there is no usable drive. */
void meter_format_swr(const meter_t *m, char *buf, size_t n);

/* Value for the CAT "SM" command, 0..30, following the Kenwood TS-2000
 * convention the existing usb_cdc firmware already reports: 0..15 spans
 * S0-S9, 15..30 spans S9 to S9+60 dB. Note this is NOT the same curve as the
 * meter face — the face is the Ten-Tec scale, this is what Hamlib expects. */
int meter_cat_sm(float dbm);

#endif /* NZIF_METER_H */
