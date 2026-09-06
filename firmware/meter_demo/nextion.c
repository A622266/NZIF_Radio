#include "nextion.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "pico/stdlib.h"
#include "hardware/uart.h"

static void nex_raw(const char *s)
{
    uart_write_blocking(NEX_UART_ID, (const uint8_t *)s, strlen(s));
    uart_write_blocking(NEX_UART_ID, (const uint8_t *)"\xFF\xFF\xFF", 3);
}

void nex_cmd(const char *fmt, ...)
{
    char buf[96];
    va_list ap;

    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    nex_raw(buf);
}

void nex_init(void)
{
    /*
     * "baud=" is a runtime change that lasts until the panel loses power, so
     * there are exactly two states worth handling: a cold panel sitting at the
     * 9600 its Program.s selects, and a warm one still at NEX_BAUD after the
     * Pico alone was reset. Announce the target from both. Bytes sent at the
     * wrong rate arrive as noise and are discarded by the panel's parser.
     */
    static const uint32_t probe[] = { 9600, NEX_BAUD };
    size_t i;

    uart_init(NEX_UART_ID, 9600);
    gpio_set_function(NEX_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(NEX_RX_PIN, GPIO_FUNC_UART);
    uart_set_hw_flow(NEX_UART_ID, false, false);
    uart_set_format(NEX_UART_ID, 8, 1, UART_PARITY_NONE);

    for (i = 0; i < sizeof(probe) / sizeof(probe[0]); i++) {
        uart_set_baudrate(NEX_UART_ID, probe[i]);
        sleep_ms(30);
        /* bkcmd=0 stops the panel returning a status code for every command,
         * which we never read and which would otherwise fill its TX buffer. */
        nex_raw("bkcmd=0");
        nex_cmd("baud=%u", (unsigned)NEX_BAUD);
        sleep_ms(60);
    }

    uart_set_baudrate(NEX_UART_ID, NEX_BAUD);
    sleep_ms(150);

    /* Flush: a bare terminator closes off any partial command the panel may
     * have latched from the mismatched-baud noise above, so our first real
     * instruction is parsed on its own. */
    uart_write_blocking(NEX_UART_ID, (const uint8_t *)"\xFF\xFF\xFF", 3);
    sleep_ms(20);

    nex_raw("bkcmd=0");
    nex_raw("page 0");
    sleep_ms(50);
}

void nex_cls(uint16_t colour)
{
    nex_cmd("cls %u", colour);
}

void nex_fill(int x, int y, int w, int h, uint16_t colour)
{
    nex_cmd("fill %d,%d,%d,%d,%u", x, y, w, h, colour);
}

void nex_line(int x1, int y1, int x2, int y2, uint16_t colour)
{
    nex_cmd("line %d,%d,%d,%d,%u", x1, y1, x2, y2, colour);
}

void nex_text(int x, int y, int w, int h, uint16_t fg, uint16_t bg,
              int centre, const char *s)
{
    /* xstr x,y,w,h,font,fg,bg,xcen,ycen,sta,"text" — sta=1 paints the box,
     * which is what lets a readout overwrite its previous value cleanly. */
    nex_cmd("xstr %d,%d,%d,%d,0,%u,%u,%d,1,1,\"%s\"",
            x, y, w, h, fg, bg, centre ? 1 : 0, s);
}

void nex_pic(int x, int y, int picid)
{
    nex_cmd("pic %d,%d,%d", x, y, picid);
}

void nex_picq(int x, int y, int w, int h, int picid)
{
    nex_cmd("picq %d,%d,%d,%d,%d", x, y, w, h, picid);
}
