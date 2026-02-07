#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "pico/stdlib.h"

#define CMD_BUFFER_SIZE 128

static uint64_t g_vfo_a_hz = 14070000;
static uint64_t g_vfo_b_hz = 7074000;
static bool g_active_vfo_b = false;
static bool g_tx_vfo_b = false;
static bool g_split = false;
static int g_mode = 2; // 1=LSB, 2=USB, 3=CW, 4=FM, 5=AM, 6=FSK
static bool g_ptt = false;
static int g_keyer_wpm = 20;
static int g_rf_gain = 128;
static int g_af_gain = 128;
static int g_smeter = 0; // 0-30
static int g_agc = 2; // 0=off,1=slow,2=mid,3=fast

static uint64_t current_rx_freq_hz(void) {
    return g_active_vfo_b ? g_vfo_b_hz : g_vfo_a_hz;
}

static uint64_t current_tx_freq_hz(void) {
    bool tx_vfo_b = g_split ? g_tx_vfo_b : g_active_vfo_b;
    return tx_vfo_b ? g_vfo_b_hz : g_vfo_a_hz;
}

static void cat_write(const char *response) {
    if (response) {
        printf("%s", response);
        fflush(stdout);
    }
}

static void cat_write_fa(void) {
    char reply[32];
    snprintf(reply, sizeof(reply), "FA%011llu;", (unsigned long long)g_vfo_a_hz);
    cat_write(reply);
}

static void cat_write_fb(void) {
    char reply[32];
    snprintf(reply, sizeof(reply), "FB%011llu;", (unsigned long long)g_vfo_b_hz);
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
    // Kenwood-style IF response (minimal but structured).
    // IF[11]=freq [4]=step [5]=rit [5]=xit [1]=rit_on [1]=xit_on [1]=tx
    // [1]=mode [1]=vfo [1]=scan [1]=split [1]=tone
    char reply[64];
    snprintf(reply, sizeof(reply), "IF%011llu%04d%05d%05d%d%d%d%d%d%d%d;",
             (unsigned long long)current_rx_freq_hz(),
             0, 0, 0,
             0, 0,
             g_ptt ? 1 : 0,
             g_mode,
             g_active_vfo_b ? 1 : 0,
             0,
             g_split ? 1 : 0,
             0);
    cat_write(reply);
}

static void cat_write_ag(void) {
    char reply[16];
    snprintf(reply, sizeof(reply), "AG%03d;", g_af_gain);
    cat_write(reply);
}

static void cat_write_rg(void) {
    char reply[16];
    snprintf(reply, sizeof(reply), "RG%03d;", g_rf_gain);
    cat_write(reply);
}

static void cat_write_sm(void) {
    char reply[16];
    snprintf(reply, sizeof(reply), "SM%03d;", g_smeter);
    cat_write(reply);
}

static void cat_write_gt(void) {
    char reply[16];
    snprintf(reply, sizeof(reply), "GT%d;", g_agc);
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
                g_vfo_a_hz = val;
            }
        }
        cat_write_fa();
        return;
    }

    if (c0 == 'F' && c1 == 'B') {
        if (*args) {
            uint64_t val = strtoull(args, NULL, 10);
            if (val > 0) {
                g_vfo_b_hz = val;
            }
        }
        cat_write_fb();
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

    if (c0 == 'A' && c1 == 'G') {
        if (*args) {
            int val = atoi(args);
            if (val >= 0 && val <= 255) {
                g_af_gain = val;
            }
        }
        cat_write_ag();
        return;
    }

    if (c0 == 'R' && c1 == 'G') {
        if (*args) {
            int val = atoi(args);
            if (val >= 0 && val <= 255) {
                g_rf_gain = val;
            }
        }
        cat_write_rg();
        return;
    }

    if (c0 == 'S' && c1 == 'M') {
        cat_write_sm();
        return;
    }

    if (c0 == 'G' && c1 == 'T') {
        if (*args) {
            int val = atoi(args);
            if (val >= 0 && val <= 3) {
                g_agc = val;
            }
        }
        cat_write_gt();
        return;
    }

    if (c0 == 'K' && c1 == 'S') {
        if (*args) {
            int val = atoi(args);
            if (val >= 5 && val <= 60) {
                g_keyer_wpm = val;
            }
        }
        char reply[16];
        snprintf(reply, sizeof(reply), "KS%03d;", g_keyer_wpm);
        cat_write(reply);
        return;
    }

    if (c0 == 'K' && c1 == 'Y') {
        // Accept CW text (ignored for now). Return KY0; to acknowledge.
        cat_write("KY0;");
        return;
    }

    if (c0 == 'F' && c1 == 'R') {
        if (*args) {
            g_active_vfo_b = (atoi(args) != 0);
        }
        cat_write(g_active_vfo_b ? "FR1;" : "FR0;");
        return;
    }

    if (c0 == 'F' && c1 == 'T') {
        if (*args) {
            g_tx_vfo_b = (atoi(args) != 0);
        }
        g_split = (g_tx_vfo_b != g_active_vfo_b);
        cat_write(g_tx_vfo_b ? "FT1;" : "FT0;");
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
