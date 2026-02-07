#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "pico/stdlib.h"

#define CMD_BUFFER_SIZE 64

static uint64_t g_freq_hz = 14070000;
static int g_mode = 2; // 1=LSB, 2=USB, 3=CW, 4=FM, 5=AM
static bool g_ptt = false;

static void cat_write(const char *response) {
    if (response) {
        printf("%s", response);
        fflush(stdout);
    }
}

static void cat_write_fa(void) {
    char reply[32];
    snprintf(reply, sizeof(reply), "FA%011llu;", (unsigned long long)g_freq_hz);
    cat_write(reply);
}

static void cat_write_md(void) {
    char reply[16];
    snprintf(reply, sizeof(reply), "MD%d;", g_mode);
    cat_write(reply);
}

static void cat_write_tx(void) {
    char reply[16];
    snprintf(reply, sizeof(reply), "TX%d;", g_ptt ? 1 : 0);
    cat_write(reply);
}

static void cat_write_if(void) {
    // Placeholder IF response: freq + zeroed fields.
    // Format is intentionally minimal for early bring-up.
    char reply[48];
    snprintf(reply, sizeof(reply), "IF%011llu+0000000000;", (unsigned long long)g_freq_hz);
    cat_write(reply);
}

static void handle_command(const char *cmd) {
    if (!cmd || strlen(cmd) < 2) {
        return;
    }

    char c0 = (char)toupper((unsigned char)cmd[0]);
    char c1 = (char)toupper((unsigned char)cmd[1]);
    const char *args = cmd + 2;

    if (c0 == 'F' && c1 == 'A') {
        if (*args) {
            uint64_t val = strtoull(args, NULL, 10);
            if (val > 0) {
                g_freq_hz = val;
            }
        }
        cat_write_fa();
        return;
    }

    if (c0 == 'M' && c1 == 'D') {
        if (*args) {
            int val = atoi(args);
            if (val > 0) {
                g_mode = val;
            }
        }
        cat_write_md();
        return;
    }

    if (c0 == 'T' && c1 == 'X') {
        if (*args) {
            g_ptt = (atoi(args) != 0);
        } else {
            g_ptt = true;
        }
        cat_write_tx();
        return;
    }

    if (c0 == 'R' && c1 == 'X') {
        g_ptt = false;
        cat_write("RX;");
        return;
    }

    if (c0 == 'I' && c1 == 'D') {
        cat_write("ID019;"); // Kenwood TS-2000 ID for broad compatibility
        return;
    }

    if (c0 == 'A' && c1 == 'I') {
        cat_write("AI0;");
        return;
    }

    if (c0 == 'I' && c1 == 'F') {
        cat_write_if();
        return;
    }

    // Unknown command: ignore silently (Kenwood style).
}

int main(void) {
    stdio_init_all();

    // Give USB a moment to enumerate.
    sleep_ms(2000);

    char cmd_buffer[CMD_BUFFER_SIZE] = {0};
    size_t cmd_len = 0;

    while (true) {
        int ch = getchar_timeout_us(0);
        if (ch == PICO_ERROR_TIMEOUT) {
            tight_loop_contents();
            continue;
        }

        if (ch == '\r' || ch == '\n' || ch == ';') {
            if (cmd_len > 0) {
                cmd_buffer[cmd_len] = '\0';
                handle_command(cmd_buffer);
                cmd_len = 0;
            }
            continue;
        }

        if (cmd_len + 1 < sizeof(cmd_buffer)) {
            cmd_buffer[cmd_len++] = (char)ch;
        } else {
            cmd_len = 0; // overflow: reset
        }
    }
}
