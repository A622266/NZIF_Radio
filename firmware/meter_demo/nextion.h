/*
 * nextion.h — minimal Nextion HMI driver for the NZIF panel meter.
 *
 * Target: Nextion NX4832T035_011, Basic series, 480 x 320, font ID 0 loaded.
 *
 * The Nextion is not a framebuffer: it runs its own firmware and accepts ASCII
 * drawing commands over UART, each terminated by three 0xFF bytes. We only need
 * a handful of primitives, because the whole meter face is drawn with lines.
 *
 * Wiring matches the existing breadboard rig in
 * vfo_ten_tec/experiments/nextion_pico — do not rewire for this demo:
 *
 *   Display 5 V supply (>=1 A) -> Nextion +5V     (or Pico VBUS pin 40, not both)
 *   Supply negative + Pico GND -> Nextion GND     (common reference)
 *   Pico GP0 (pin 1, UART0 TX) -> Nextion RX      (commands to the display)
 *   Nextion TX                 -> leave disconnected
 *
 * The link is deliberately one-way, so nothing is ever read back. GP2..GP5 are
 * taken by that rig's indicator LEDs, which is why UART1 is not used here.
 *
 * NOTE for later integration: the radio's CAT port also wants UART0. When the
 * meter moves onto the NZIF board the panel should shift to UART1.
 */
#ifndef NZIF_NEXTION_H
#define NZIF_NEXTION_H

#include <stdint.h>

#define NEX_UART_ID   uart0
#define NEX_TX_PIN    0
#define NEX_RX_PIN    1

/*
 * The panel's Program.s sets baud=9600 at every power-up, and 9600 caps us near
 * 3 fps once a frame costs a few hundred bytes — nowhere near enough for a
 * moving needle. 115200 gives roughly 40 fps of headroom and is undemanding on
 * breadboard jumpers. Raise to 230400 if the needle still looks steppy.
 */
#define NEX_BAUD      115200

/* 16-bit 565 colour, which is what every Nextion drawing command wants. */
static inline uint16_t nex_rgb(uint8_t r, uint8_t g, uint8_t b)
{
    return (uint16_t)(((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3));
}

/* Brings the panel to NEX_BAUD from whatever baud it happens to be at. */
void nex_init(void);

void nex_cmd(const char *fmt, ...);
void nex_cls(uint16_t colour);
void nex_fill(int x, int y, int w, int h, uint16_t colour);
void nex_line(int x1, int y1, int x2, int y2, uint16_t colour);

/* Text via the panel's own font ID 0. Used for the readout strip, where the
 * background is plain black and a real font beats vector strokes. `centre`
 * horizontally centres the string in the box. */
void nex_text(int x, int y, int w, int h, uint16_t fg, uint16_t bg,
              int centre, const char *s);

/* Paint a whole stored picture at (x, y). */
void nex_pic(int x, int y, int picid);

/*
 * Crop (w x h) out of stored picture `picid` at (x, y) and paint it at the
 * same coordinates. This is how the needle is erased over artwork: there is
 * no flat colour to redraw, so the original pixels are put back instead.
 * Requires the picture to be full-screen and aligned 1:1 with the display.
 */
void nex_picq(int x, int y, int w, int h, int picid);

#endif /* NZIF_NEXTION_H */
