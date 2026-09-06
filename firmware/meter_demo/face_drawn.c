#include "face.h"
#include "nextion.h"
#include "strokefont.h"
#include "meter.h"

#include <math.h>
#include <string.h>
#include <stdint.h>

#include "pico/stdlib.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ------------------------------------------------------------------ *
 * Geometry
 *
 * The Model 540 face is a wide, shallow arc, so the pivot sits well below the
 * glass — here 255 px below the bottom edge of a 480 x 320 panel. That is what
 * gives the needle its long, flat sweep instead of a car-dashboard curve.
 * ------------------------------------------------------------------ */

#define CX           240.0f
#define CY           495.0f
#define ARC_R        440.0f
#define SWEEP_RAD    (27.0f * (float)M_PI / 180.0f)

#define TICK_MAJ      12.0f    /* S-unit ticks, drawn outward from the arc */
#define SWR_TICK      12.0f    /* SWR ticks, drawn inward */
#define S_LABEL_R    (ARC_R + 28.0f)
#define SWR_LABEL_R  (ARC_R - 28.0f)
#define NAME_R       (ARC_R + 52.0f)

#define NEEDLE_RIN   292.0f
#define NEEDLE_ROUT  ARC_R     /* tip reaches the scale line, as on the real meter */

/* Colours. The face is a flat amber rather than the real instrument's lamp
 * gradient: flat is what makes erasing the needle a single line command. */
#define C_FACE   nex_rgb(226, 150,  45)
#define C_INK    nex_rgb( 24,  18,  10)
#define C_BLACK  0
#define C_READ   nex_rgb(255, 176,  86)
#define C_RULE   nex_rgb( 90,  58,  20)

/* Repair window. The needle is 3 px wide; 0.011 rad is a little over half a
 * degree, comfortably more than 1.5 px at the pivot distances involved. */
#define REPAIR_MARGIN  0.011f

/* ------------------------------------------------------------------ *
 * Display list
 * ------------------------------------------------------------------ */

#define MAX_SEGS  420

typedef struct {
    int16_t x1, y1, x2, y2;
    float   amin, amax;      /* angular span seen from the pivot */
    float   rmin, rmax;      /* radial span from the pivot */
} fseg_t;

static fseg_t  g_seg[MAX_SEGS];
static int     g_nseg;

static float ang_of(float x, float y) { return atan2f(y - CY, x - CX); }
static float rad_of(float x, float y)
{
    float dx = x - CX, dy = y - CY;
    return sqrtf(dx * dx + dy * dy);
}

static void seg_add(int x1, int y1, int x2, int y2, void *ctx)
{
    fseg_t *s;
    float a1, a2, r1, r2;

    (void)ctx;
    if (g_nseg >= MAX_SEGS) {
        return;
    }
    s = &g_seg[g_nseg++];
    s->x1 = (int16_t)x1; s->y1 = (int16_t)y1;
    s->x2 = (int16_t)x2; s->y2 = (int16_t)y2;

    a1 = ang_of((float)x1, (float)y1);
    a2 = ang_of((float)x2, (float)y2);
    s->amin = a1 < a2 ? a1 : a2;
    s->amax = a1 < a2 ? a2 : a1;

    r1 = rad_of((float)x1, (float)y1);
    r2 = rad_of((float)x2, (float)y2);
    s->rmin = r1 < r2 ? r1 : r2;
    s->rmax = r1 < r2 ? r2 : r1;
}

/* ------------------------------------------------------------------ *
 * Polar helpers
 * ------------------------------------------------------------------ */

float face_angle(float f)
{
    return -(float)M_PI * 0.5f + (2.0f * f - 1.0f) * SWEEP_RAD;
}

static void polar(float a, float r, int *x, int *y)
{
    *x = (int)lrintf(CX + r * cosf(a));
    *y = (int)lrintf(CY + r * sinf(a));
}

static void radial_seg(float f, float r0, float r1)
{
    float a = face_angle(f);
    int x0, y0, x1, y1;
    polar(a, r0, &x0, &y0);
    polar(a, r1, &x1, &y1);
    seg_add(x0, y0, x1, y1, NULL);
}

/* Labels sit radially, turned to follow the arc, as on the original face. */
static void radial_text(float f, float r, float h, const char *s)
{
    float a = face_angle(f);
    int x, y;
    polar(a, r, &x, &y);
    sf_text((float)x, (float)y, h, a + (float)M_PI * 0.5f, s, seg_add, NULL);
}

/* ------------------------------------------------------------------ *
 * Building the face
 * ------------------------------------------------------------------ */

static const char *S_LBL[]   = { "3", "5", "7", "9", "+10", "+20", "+30" };
static const float S_LBL_DB[] = { -36, -24, -12, 0, 10, 20, 30 };

static const float SWR_TICKS[] = { 1.0f, 1.5f, 2.0f, 2.5f, 3.0f, 4.0f, 5.0f };
static const char *SWR_LBL[]   = { "1", "2", "3", "5" };
static const float SWR_LBL_V[] = { 1.0f, 2.0f, 3.0f, 5.0f };

static void build(void)
{
    const int ARC_SEGS = 72;
    int i;

    g_nseg = 0;

    /* Scale arc, as short chords so a crossing needle only disturbs a couple. */
    for (i = 0; i < ARC_SEGS; i++) {
        float f0 = (float)i / ARC_SEGS;
        float f1 = (float)(i + 1) / ARC_SEGS;
        int x0, y0, x1, y1;
        polar(face_angle(f0), ARC_R, &x0, &y0);
        polar(face_angle(f1), ARC_R, &x1, &y1);
        seg_add(x0, y0, x1, y1, NULL);
    }

    /* S-unit ticks. One per S-unit only: at 6.5 px/mm the half-unit marks of
     * the original land about 3 px apart and read as a smudge. */
    for (i = 1; i <= 9; i++) {
        float db = (float)(i - 9) * METER_DB_PER_S;
        radial_seg(meter_dbm_to_sweep(METER_S9_DBM + db), ARC_R, ARC_R + TICK_MAJ);
    }
    for (i = 10; i <= 30; i += 10) {
        radial_seg(meter_dbm_to_sweep(METER_S9_DBM + (float)i), ARC_R, ARC_R + TICK_MAJ);
    }

    for (i = 0; i < (int)(sizeof(S_LBL) / sizeof(S_LBL[0])); i++) {
        radial_text(meter_dbm_to_sweep(METER_S9_DBM + S_LBL_DB[i]),
                    S_LABEL_R, 13.0f, S_LBL[i]);
    }

    /* SWR ticks and numerals, inside the arc. Their positions are not measured
     * from the photograph: a moving-coil movement deflects on reflected
     * voltage, so meter_swr_to_sweep puts them where rho does. */
    for (i = 0; i < (int)(sizeof(SWR_TICKS) / sizeof(SWR_TICKS[0])); i++) {
        float f = meter_swr_to_sweep(SWR_TICKS[i]);
        bool major = (SWR_TICKS[i] == 1.0f || SWR_TICKS[i] == 2.0f ||
                      SWR_TICKS[i] == 3.0f || SWR_TICKS[i] == 5.0f);
        radial_seg(f, ARC_R - (major ? SWR_TICK : SWR_TICK * 0.55f), ARC_R);
    }
    for (i = 0; i < (int)(sizeof(SWR_LBL) / sizeof(SWR_LBL[0])); i++) {
        radial_text(meter_swr_to_sweep(SWR_LBL_V[i]), SWR_LABEL_R, 12.0f, SWR_LBL[i]);
    }

    /* Silkscreened scale names, as on the original: S UNITS left, SWR right. */
    radial_text(0.10f, NAME_R, 12.0f, "S UNITS");
    radial_text(0.93f, SWR_LABEL_R - 22.0f, 12.0f, "SWR");
}

/* ------------------------------------------------------------------ *
 * Needle
 * ------------------------------------------------------------------ */

static void needle_draw(float f, uint16_t colour)
{
    float a  = face_angle(f);
    float px = -sinf(a), py = cosf(a);     /* unit normal to the needle */
    int k;

    for (k = -1; k <= 1; k++) {
        float ox = px * (float)k, oy = py * (float)k;
        int x0 = (int)lrintf(CX + NEEDLE_RIN  * cosf(a) + ox);
        int y0 = (int)lrintf(CY + NEEDLE_RIN  * sinf(a) + oy);
        int x1 = (int)lrintf(CX + NEEDLE_ROUT * cosf(a) + ox);
        int y1 = (int)lrintf(CY + NEEDLE_ROUT * sinf(a) + oy);
        nex_line(x0, y0, x1, y1, colour);
    }
}

static void repair(float f)
{
    float a = face_angle(f);
    int i;

    for (i = 0; i < g_nseg; i++) {
        const fseg_t *s = &g_seg[i];
        if (a < s->amin - REPAIR_MARGIN || a > s->amax + REPAIR_MARGIN) {
            continue;
        }
        /* Skip anything the needle cannot physically have covered. */
        if (s->rmin > NEEDLE_ROUT || s->rmax < NEEDLE_RIN) {
            continue;
        }
        nex_line(s->x1, s->y1, s->x2, s->y2, C_INK);
    }
}

void face_needle_first(float f)
{
    needle_draw(f, C_INK);
}

void face_needle(float from, float to)
{
    needle_draw(from, C_FACE);   /* erase */
    repair(from);                /* put back whatever that erased */
    needle_draw(to, C_INK);
}

/* ------------------------------------------------------------------ *
 * Readout strip
 * ------------------------------------------------------------------ */

#define CELLS   3
#define CELL_W  (SCR_W / CELLS)
#define CELL_Y  254
#define CELL_H  42

static char g_cell[CELLS][20];

void face_readout(int cell, const char *text)
{
    if (cell < 0 || cell >= CELLS) {
        return;
    }
    if (strncmp(g_cell[cell], text, sizeof(g_cell[0])) == 0) {
        return;                  /* unchanged — do not repaint, do not flicker */
    }
    strncpy(g_cell[cell], text, sizeof(g_cell[0]) - 1);
    g_cell[cell][sizeof(g_cell[0]) - 1] = '\0';
    nex_text(cell * CELL_W, CELL_Y, CELL_W, CELL_H, C_READ, C_BLACK, 1, text);
}

/* ------------------------------------------------------------------ *
 * Init
 * ------------------------------------------------------------------ */

void face_init(void)
{
    int i;

    nex_cls(C_BLACK);
    sleep_ms(40);

    nex_fill(0, 0, SCR_W, FACE_H, C_FACE);
    sleep_ms(40);

    build();

    /*
     * Roughly 200 line commands go out here. The panel drains its serial
     * buffer as it draws, but a continuous burst can outrun it, so pause
     * briefly every few segments while the face is laid down.
     */
    for (i = 0; i < g_nseg; i++) {
        nex_line(g_seg[i].x1, g_seg[i].y1, g_seg[i].x2, g_seg[i].y2, C_INK);
        if ((i & 0x0F) == 0x0F) {
            sleep_ms(4);
        }
    }

    nex_line(0, FACE_H, SCR_W - 1, FACE_H, C_RULE);
    for (i = 0; i < CELLS; i++) {
        g_cell[i][0] = '\0';
    }
    sleep_ms(20);
}
