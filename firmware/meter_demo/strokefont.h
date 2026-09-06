/*
 * strokefont.h — tiny vector font for the meter's scale numerals.
 *
 * The panel does have a real font (ID 0, ~20 px ASCII), and the readout strip
 * uses it. The scale numerals cannot: they need to be small, and on the
 * Ten-Tec face they sit radially, rotated to follow the arc. Nextion's xstr
 * draws neither small enough nor rotated, so the numerals are drawn as line
 * strokes instead.
 *
 * Glyphs live on a 12 x 20 integer grid, origin top-left. Only the characters
 * the face actually uses are defined: digits, '+', and the letters in
 * "S UNITS" and "SWR".
 */
#ifndef NZIF_STROKEFONT_H
#define NZIF_STROKEFONT_H

/* Receives one stroke in screen coordinates. `ctx` is passed through. */
typedef void (*sf_emit_t)(int x1, int y1, int x2, int y2, void *ctx);

/* Width in pixels the string will occupy at the given glyph height. */
float sf_width(const char *s, float h_px);

/*
 * Draw `s` centred on (cx, cy), rotated `rot` radians clockwise, with glyphs
 * `h_px` tall. Every stroke is handed to `emit`.
 */
void sf_text(float cx, float cy, float h_px, float rot,
             const char *s, sf_emit_t emit, void *ctx);

#endif /* NZIF_STROKEFONT_H */
