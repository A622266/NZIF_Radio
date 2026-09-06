/*
 * face.h — the Ten-Tec-style meter face, drawn on a Nextion over serial.
 *
 * The panel's .tft is a bare black page, so every mark is drawn at runtime.
 * The face is built once into a display list of line segments, each tagged
 * with the angular and radial span it occupies as seen from the needle pivot.
 *
 * That tagging is what lets the needle cross the printed scale. Each frame the
 * needle is erased by redrawing it in the face colour — which would also erase
 * any scale marking it happened to lie over — so the segments whose span the
 * old needle touched are then redrawn. Typically that is two or three arc
 * segments; only when the needle passes a numeral does it cost more.
 */
#ifndef NZIF_FACE_H
#define NZIF_FACE_H

#include <stdbool.h>

#define SCR_W       480
#define SCR_H       320
#define FACE_H      240        /* amber face; below this is the readout strip */

/* Paints the face and draws the complete scale. Call once at startup. */
void face_init(void);

/* Moves the needle from sweep fraction `from` to `to`, both 0..1. */
void face_needle(float from, float to);

/* Draws the needle for the first time, with nothing to erase. */
void face_needle_first(float f);

/* Readout strip. Each cell repaints only when its text changes, which keeps
 * the strip from flickering under a needle running at 30 fps. */
void face_readout(int cell, const char *text);

/* Sweep fraction -> needle angle in radians, for change detection. */
float face_angle(float f);

#endif /* NZIF_FACE_H */
