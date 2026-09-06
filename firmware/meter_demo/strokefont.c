#include "strokefont.h"

#include <math.h>
#include <stddef.h>
#include <stdint.h>

/* 12 x 20 grid. Digits are seven-segment, which stays unambiguous at the 13 px
 * the scale numerals end up being. Letters are drawn as plain strokes. */
#define SEG_A   0,0, 12,0
#define SEG_B  12,0, 12,10
#define SEG_C  12,10, 12,20
#define SEG_D   0,20, 12,20
#define SEG_E   0,10,  0,20
#define SEG_F   0,0,   0,10
#define SEG_G   0,10, 12,10

static const int8_t g_0[] = { SEG_A, SEG_B, SEG_C, SEG_D, SEG_E, SEG_F };
static const int8_t g_1[] = { 4,2, 6,0,  6,0, 6,20,  2,20, 10,20 };
static const int8_t g_2[] = { SEG_A, SEG_B, SEG_G, SEG_E, SEG_D };
static const int8_t g_3[] = { SEG_A, SEG_B, SEG_G, SEG_C, SEG_D };
static const int8_t g_4[] = { SEG_F, SEG_G, SEG_B, SEG_C };
static const int8_t g_5[] = { SEG_A, SEG_F, SEG_G, SEG_C, SEG_D };
static const int8_t g_6[] = { SEG_A, SEG_F, SEG_G, SEG_E, SEG_C, SEG_D };
static const int8_t g_7[] = { SEG_A, SEG_B, SEG_C };
static const int8_t g_8[] = { SEG_A, SEG_B, SEG_C, SEG_D, SEG_E, SEG_F, SEG_G };
static const int8_t g_9[] = { SEG_A, SEG_B, SEG_C, SEG_D, SEG_F, SEG_G };

static const int8_t g_plus[] = { 3,10, 9,10,  6,7, 6,13 };

/* 'S' is the seven-segment '5'; in "S UNITS" and "SWR" the context carries it. */
static const int8_t g_S[] = { SEG_A, SEG_F, SEG_G, SEG_C, SEG_D };
static const int8_t g_U[] = { 0,0, 0,20,   0,20, 12,20,  12,20, 12,0 };
static const int8_t g_N[] = { 0,20, 0,0,   0,0, 12,20,   12,20, 12,0 };
static const int8_t g_I[] = { 4,0, 8,0,    6,0, 6,20,    4,20, 8,20 };
static const int8_t g_T[] = { 0,0, 12,0,   6,0, 6,20 };
static const int8_t g_W[] = { 0,0, 2,20,   2,20, 6,8,   6,8, 10,20,  10,20, 12,0 };
static const int8_t g_R[] = { 0,20, 0,0,   0,0, 12,0,   12,0, 12,11,
                              12,11, 0,11, 5,11, 12,20 };

typedef struct {
    char           ch;
    const int8_t  *d;
    uint8_t        nseg;
} glyph_t;

#define G(c, arr) { c, arr, (uint8_t)(sizeof(arr) / 4) }

static const glyph_t GLYPHS[] = {
    G('0', g_0), G('1', g_1), G('2', g_2), G('3', g_3), G('4', g_4),
    G('5', g_5), G('6', g_6), G('7', g_7), G('8', g_8), G('9', g_9),
    G('+', g_plus),
    G('S', g_S), G('U', g_U), G('N', g_N), G('I', g_I), G('T', g_T),
    G('W', g_W), G('R', g_R)
};

#define NGLYPH  (sizeof(GLYPHS) / sizeof(GLYPHS[0]))

/* Glyph cell is 12 wide; 4 units of side bearing gives a 16-unit advance. */
#define ADV_UNITS  16.0f
#define EM_UNITS   20.0f

static const glyph_t *find(char c)
{
    size_t i;
    for (i = 0; i < NGLYPH; i++) {
        if (GLYPHS[i].ch == c) {
            return &GLYPHS[i];
        }
    }
    return NULL;   /* space, and anything undefined, advances blank */
}

float sf_width(const char *s, float h_px)
{
    float u = h_px / EM_UNITS;
    size_t n = 0;
    while (s[n] != '\0') {
        n++;
    }
    if (n == 0) {
        return 0.0f;
    }
    /* Trailing side bearing is not part of the inked width. */
    return ((float)n * ADV_UNITS - (ADV_UNITS - 12.0f)) * u;
}

void sf_text(float cx, float cy, float h_px, float rot,
             const char *s, sf_emit_t emit, void *ctx)
{
    float u  = h_px / EM_UNITS;
    float w  = sf_width(s, h_px);
    float ca = cosf(rot), sa = sinf(rot);
    float penx = -w * 0.5f;
    float half = h_px * 0.5f;
    size_t i;

    for (i = 0; s[i] != '\0'; i++) {
        const glyph_t *g = find(s[i]);
        if (g != NULL) {
            uint8_t k;
            for (k = 0; k < g->nseg; k++) {
                const int8_t *p = &g->d[k * 4];
                /* glyph units -> local pixels, origin at the string centre */
                float lx1 = penx + (float)p[0] * u;
                float ly1 = (float)p[1] * u - half;
                float lx2 = penx + (float)p[2] * u;
                float ly2 = (float)p[3] * u - half;
                emit((int)lrintf(cx + lx1 * ca - ly1 * sa),
                     (int)lrintf(cy + lx1 * sa + ly1 * ca),
                     (int)lrintf(cx + lx2 * ca - ly2 * sa),
                     (int)lrintf(cy + lx2 * sa + ly2 * ca),
                     ctx);
            }
        }
        penx += ADV_UNITS * u;
    }
}
