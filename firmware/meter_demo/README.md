# NZIF panel meter — Nextion demo firmware

Draws the Ten-Tec Model 540-style S-meter/SWR face on a Nextion 3.5″ panel and
runs the needle from a synthetic noisy HF band with an SSB station on it.

The metering itself is not implemented here. `nzif/meter_display/meter.c`
compiles straight into this firmware, unchanged — the same scale mapping and
moving-coil ballistics that the host-side harness exercises. This project only
adds the panel driver, the face artwork, and the demo signal.

## Hardware

- Nextion **NX4832T035_011**, Basic series, 480 × 320, with **font ID 0** loaded.
- Raspberry Pi Pico (RP2040).
- Wiring is exactly the existing breadboard rig in
  `vfo_ten_tec/experiments/nextion_pico` — nothing needs rewiring:

| From | To | Purpose |
|---|---|---|
| Display 5 V supply (≥ 1 A) | Nextion +5V | Display power only |
| Supply negative + Pico GND (pin 3) | Ground rail | Shared reference |
| Pico **GP0** (pin 1, UART0 TX) | Nextion RX | Commands to the display |
| Nextion TX | leave disconnected | Link is one-way |

Do not power the panel from Pico 3V3 or a GPIO. Pico VBUS (pin 40) is the
alternative to a separate supply — one or the other, never both.

## Two face renderers

Both implement `face.h`; CMake picks one.

### `face_pic.c` — stored artwork (default)

The whole face, lamp gradient and all, is one full-screen 480 × 320 image in
the panel's flash as **picture ID 0**. The needle is erased by putting the
original artwork back with `picq`, which restores the arc, ticks, numerals and
glow underneath it in one go — so there is no display list and no scale-repair
pass at all.

Restoring the needle's whole bounding box would be ~9,000 px at full tilt,
enough to flicker. The needle is split into 8 short segments and a small box
restored per segment, which cuts that to roughly 1,000 px.

A frame is 8 `picq` + 3 `line` = 248 bytes; at 30 fps that is 65 % of 115200
baud, with a ceiling near 46 fps.

### `face_drawn.c` — scale drawn at runtime (fallback)

Needs nothing in the `.tft` but a black page. Fills a flat amber rectangle and
draws the scale as ~226 line segments, each tagged with the angular and radial
span it occupies from the pivot; erasing the needle in the flat face colour
also erases whatever it lay over, so those segments are redrawn. Numerals are
vector strokes (`strokefont.c`) because they must be ~13 px and rotated, and
`xstr` can do neither.

Uglier — no gradient, no real type — but it is the version already confirmed
working on hardware, and it needs no Nextion Editor round-trip.

```sh
cmake -S . -B build -G Ninja -DPICO_BOARD=pico -DMETER_FACE_ARTWORK=OFF
```

## The artwork

`nzif/meter_display/make_face.py` renders the background **and** emits
`face_geom.h`, which this firmware includes. That is deliberate: the artwork
and the firmware must agree pixel for pixel, because the needle pivots about
`FG_CX, FG_CY` and the arc baked into the PNG is centred on the same point. A
few pixels of drift and the needle points off the marks. Regenerate both
together:

```sh
python3 nzif/meter_display/make_face.py
```

Proportions follow the real Model 540 face at **1.75 × 0.75 inches** (2.333:1),
so the amber is 468 × 201 px. Rendered larger than life on purpose: at the
panel's 6.5 px/mm, true size would be only 290 × 124 px.

Type is Nimbus Sans Narrow, close to the original's condensed silkscreen. The
whole face is drawn at 4× and downsampled, so curves and numerals are
antialiased — which is most of what the runtime-drawn version cannot do.

### Loading it into the panel

1. Open the project in Nextion Editor (`launch_editor.sh` under
   `vfo_ten_tec/experiments/nextion_pico`).
2. In the **Picture** pane, add `nzif/meter_display/artwork/meter_face_480x320.png`.
   It must land as **picture ID 0**; delete any earlier pictures so the IDs do
   not shift.
3. Select `page0`, set its background attribute from solid colour to **image**,
   and choose picture 0. The face is then already on screen at power-up.
4. Leave font ID 0 in place — the readout strip still uses it.
5. Keep `baud=9600` in `Program.s`; the firmware raises it.
6. Compile, export `display.tft`, upload by microSD as before.

`picq` requires a full-screen picture aligned 1:1 with the display, which this
is. The image adds ~300 kB to the `.tft`; there is 16 MB of flash.

### Baud

The panel's `Program.s` selects 9600 at power-up, which caps the needle near
3 fps. `nex_init()` raises it to **115200**, announcing the change from both
9600 (cold panel) and 115200 (warm panel, Pico alone reset) so it works either
way. Raise `NEX_BAUD` in `nextion.h` to 230400 if the needle still looks steppy.

## Build

The toolchain is already installed on this machine (arm-none-eabi-gcc 13.2,
CMake, Ninja, Pico SDK 2.2.0 at `~/pico/pico-sdk`).

```sh
cd firmware/meter_demo
export PICO_SDK_PATH=$HOME/pico/pico-sdk
cmake -S . -B build -G Ninja -DPICO_BOARD=pico
ninja -C build
```

Output: `build/nzif_meter_demo.uf2` (~80 kB). Builds clean; uses 45 kB flash
and 4.5 kB RAM. The drawn-scale fallback is larger — 48 kB flash and 14.6 kB
RAM — because it carries the display list.

## Flash

> **This replaces MicroPython on the Pico.** Thonny will no longer see the board
> as a MicroPython device. To go back, flash the MicroPython `.uf2` again the
> same way — nothing is permanently lost.

1. Unplug the Pico's USB cable.
2. Hold the **BOOTSEL** button down.
3. Plug the USB cable back in, then release BOOTSEL.
4. The Pico mounts as a USB drive named **RPI-RP2**.
5. Copy the firmware onto it:

```sh
cp build/nzif_meter_demo.uf2 /media/$USER/RPI-RP2/
sync
```

The Pico reboots automatically as soon as the copy completes and starts running
— there is no separate "run" step, and the drive disappearing is expected.

If it does not mount automatically, find it with `lsblk` and mount manually.
Alternatively use the picotool the build already fetched:

```sh
build/_deps/picotool/picotool load -f build/nzif_meter_demo.uf2
```

That needs udev rules or `sudo`; the drag-and-drop route above needs neither.

### Order of operations

Power the display **first**, then the Pico. The firmware waits 1.2 s before
talking to the panel, but the panel's own boot is slower than the Pico's. If
the face comes up blank or garbled, reset the Pico with the display already
running.

## The demo

Receive only, on a noisy band:

- A noise floor random-walking around −110 dBm, a little under S3, so the
  needle stays alive between overs.
- An SSB station whose envelope comes from three incommensurate sines, giving
  syllable, word and phrase structure without sounding periodic.
- The station stops to listen roughly every 35 s.
- Slow QSB moves the peaks over about two S-units, around S7–S9.

The readout strip shows the S-reading, the level in dBm, and the mode.

The SWR scale is drawn but not exercised — the demo is receive-only. Driving
it needs `meter_set_mode(&m, METER_MODE_TX)` and `meter_update_tx()` with a
pair of detector voltages.

## Known limits

- **Confirmed working on hardware** (2026-09-06, NX4832T035_011). The face
  renders and the needle runs from the demo signal.
- UART0 is used because that is how the breadboard is wired. The radio's CAT
  port also wants UART0, so when this moves onto the NZIF board the panel
  should shift to UART1.
- The artwork path has **not yet been run on hardware** — it builds clean and
  the geometry is shared with the PNG by construction, but it needs the Editor
  round-trip before it can be seen. `-DMETER_FACE_ARTWORK=OFF` returns to the
  version known to work.
- `picq` speed on the Basic series is estimated, not measured. If the needle
  drags, raise `NEX_BAUD` to 230400 or lower `NEEDLE_SEGS`.
