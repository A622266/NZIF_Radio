# Virtual Analog Meter (S-meter / SWR meter)

A digitally rendered meter for the NZIF radio front panel that looks and behaves like
a real moving-coil meter. One needle serves two purposes:

- **Receive:** signal strength, S1–S9 then S9+10, +20, +30 dB.
- **Transmit:** SWR, 1:1 through roughly 5:1 (plus forward power as a secondary reading).

The visual and behavioural reference is the **Ten-Tec Model 540 (Triton IV)** meter.
From the reference photograph in this folder (`ten tec meter.jpeg`):

- The face is **lamp-lit warm amber**, not cream. The incandescent backlight, with its
  hotspot left of centre, is the meter's whole visual signature.
- **No red band.** All printing is black on amber. (An earlier draft of this README
  assumed a red S9+ region — the photo says otherwise.)
- **Both scales share one arc**: S-units labelled above it, SWR below, with `S UNITS`
  and `SWR` silkscreened at opposite ends.
- The pivot sits **below the visible face** — the needle base runs off the bottom edge.
- The arc is shallow and wide, roughly ±27° of sweep.

## Why this exists

Everything upstream of the meter is already digital. Signal strength comes out of the
ADAU1467 as a level estimate; forward and reflected power come from the directional
coupler detectors on the RF front-end board into the Pi Pico ADC. There is no analog
meter movement in the design, so the meter has to be drawn — but a bare numeric readout
loses the thing an analog meter is genuinely good at: showing *rate of change* and
letting you judge a signal at a glance without reading digits.

## Scope of the work

### 1. Meter face artwork

- Scale arc, tick marks, and numerals matching the Model 540 layout.
- Dual scale printing: S-units on the upper arc, SWR on the lower arc.
- Red band from S9 upward (RX) and from ~2:1 upward (TX).
- Must remain legible at the target panel size and viewing distance.

### 2. Needle rendering and movement physics

The needle should not jump to its target value. It is modelled as a damped
second-order system, the way a real D'Arsonval movement behaves:

```text
θ'' = ω²(θ_target − θ) − 2ζω·θ'
```

**Settled values: ζ = 0.65, fₙ = 2.2 Hz, 25 ms averaging.** Measured on a step to S7,
that gives about 6.1 % overshoot on the step and settles inside 450 ms — close to the
analytic 6.8 % for a pure second-order system, which is a useful check that the
integrator is behaving.

Two things the harness established that were not obvious going in:

- **Quote overshoot against the step, not against full sweep.** They differ by the step
  size — 6.8 % of a step that spans 0.564 of sweep is only 3.8 % of sweep. Mixing the
  two makes the movement look wrongly damped.
- **Averaging is not a free knob.** It suppresses exactly the overshoot that makes the
  needle read as a physical object. At ζ = 0.65 the overshoot falls from 6.8 % of the
  step at 0 ms, to 3.6 % at 60 ms, to essentially nothing by 100 ms. An early draft
  defaulted to 60 ms and was quietly flattening the ballistics it had just been tuned
  for. The movement is already a heavy low-pass at 2.2 Hz; the averaging is there only
  to take the edge off ADC noise, and 25 ms is enough.

### 3. Receive scale calibration

S-units are a defined standard, not an arbitrary scale:

- S9 = −73 dBm at the antenna (50 Ω) on HF.
- One S-unit = 6 dB, so S1 = −121 dBm.
- Above S9 the scale switches to dB-over-S9 and is linear in dB: +10, +20, +30.

The mapping from S-unit to needle angle is **not linear in dB**. Measured from the
reference photograph, S1–S9 occupies about 70 % of the sweep for 48 dB, while
+10/+20/+30 are packed into the remaining 30 % for 30 dB — the top of the scale is
compressed by roughly 1.5×. The spacing also tightens as it climbs *within* the S-unit
region. Both effects are encoded as an anchor table with linear interpolation between
anchors (see `S_ANCHORS` in the prototype), so individual marks can be trimmed without
disturbing the rest.

Calibration constants must be per-band — front-end gain and mixer conversion loss are
not flat across 160m–6m — and stored so they can be trimmed after bring-up.

### 4. Transmit scale (SWR)

- Derived from the forward and reflected detector voltages:
  `SWR = (1 + √(Pr/Pf)) / (1 − √(Pr/Pf))`
- **Tick positions do not need measuring from the photo.** A moving-coil movement
  deflects on reflected *voltage*, so the marks fall exactly where
  `ρ = (SWR−1)/(SWR+1)` puts them: 1:1 at rest, 2:1 at ⅓ sweep, 3:1 at ½, 5:1 at ⅔,
  running to an unreachable open circuit at full scale. This reproduces the bunching
  visible at the top of the reference face from physics rather than guesswork.
- Needs the Schottky detector response linearised; those detectors are square-law at
  low level and linear at high level. The prototype models this as
  `V = Vk · x/√(1+x)` with `x = P/Pk`, which is **invertible in closed form**
  (`x = (r² + √(r⁴+4r²))/2`, `r = V/Vk`) — so firmware needs no lookup table.
  A toggle in the prototype disables the correction to show the resulting error:
  acceptable near full power, badly wrong at low drive, which is precisely when
  someone is tuning up.
- Should blank or hold rather than display garbage when forward power is below a
  usable threshold.
- Fold-back protection already lives in Pico firmware; the meter reads the same data
  but is a display, not a control path.

### 5. Mode switching

The meter follows T/R state. Transition between RX and TX scales should be visually
clean — either a scale crossfade or a deliberate needle sweep — not an instant snap
that reads as a glitch.

## Open decisions

**Display hardware is decided: a Nextion 3.5″ TFT, 480 × 320.** See the section below
for what that changes. Remaining:

| Decision | Notes |
|---|---|
| Exact Nextion model | Assumed **NX4832T035** (Basic series) — the common 3.5″ part: 480×320, 16 MB flash, 3584 B RAM, 48 MHz, 65K colour, resistive touch. Enhanced (K035) adds RTC and GPIO; Intelligent (P035) has far better graphics and would change the needle options below. Everything here is designed to the Basic series, so it works on any of them. |
| Needle rendering method | Three viable approaches with different cost/fidelity trades — see below. Needs a look at the panel before committing. |
| Face detail level | 480×320 over 73.4 mm is 6.5 px/mm; the photographed tick density does not survive. `nextion_face.html` compares three densities at true size. |
| Peak hold | The Model 540 has none, and the original plan was to follow it. The CW measurement above argues for offering it after all. |

## The Nextion panel

### What it changes

The Nextion is **not a framebuffer**. It runs its own firmware on its own 48 MHz MCU,
holds the artwork in its 16 MB of flash, and accepts drawing instructions over UART
(commands terminated by three `0xFF` bytes). The Pico never sends pixels — it sends a
needle angle.

That suits `meter.c` exactly, and vindicates two earlier decisions:

- It emits a **sweep fraction and draws nothing**, so it needs no changes at all.
- `meter_tick()` **sub-steps internally at 1 ms**, so it stays physically correct even
  when called at the 20–30 Hz the panel can actually repaint. Had the integrator been
  tied to its call rate, the ballistics would have had to be re-tuned for the display.

### The needle problem

The obvious route — the built-in **Gauge component** — does not work well here. It
repaints its entire bounding square every update (order 20,000 pixels), which both
flickers visibly and throttles the rate. Its needle is also a plain straight line, so
the tapered Ten-Tec needle is not available through it.

The workable method is to draw the needle with `line` and undraw it by restoring what
was underneath. How cheap that is depends entirely on what *is* underneath:

| Approach | Cost per frame | Fidelity |
|---|---|---|
| Built-in Gauge | ~20,000 px | Poor — plain line, flickers |
| `line` + undraw in a flat colour | ~140 px | Good, but the swept band must be flat-shaded |
| `line` + `xpic` one bounding box | ~48,000 px worst case | Full — but slower than the Gauge |
| `line` + `xpic` in ~10 segments | ~2,500 px | Full, and fast. **Recommended.** |

The segmented `xpic` approach restores the amber gradient and the scale printing from
the stored background picture, a small rectangle at a time. It costs about 11 commands
per frame instead of 2, so run the UART at **921600 baud** rather than the 9600 default.

`nextion_face.html` renders all of this at true panel size and includes a live cost
table; the "swept band" toggle shows exactly which pixels need restoring.

### Schematic impact

**The board has no display connector.** `nzif/microcontroller.kicad_sch` needs a 4-pin
header — 5 V, GND, Pico TX → Nextion RX, Nextion TX → Pico RX. Notes:

- The panel wants **5 V**, not 3.3 V, and draws roughly 150 mA with the backlight up.
  It must come off the 5 V rail, not the Pico's 3.3 V regulator.
- Nextion UART is 3.3 V logic, so it interfaces to the Pico directly with no level
  shifting.
- The Pico's UART0 is already committed to the Hamlib CAT port, so the panel needs
  **UART1**.

This is a schematic change and has not been made — the project is on HOLD for the
Critical items in `nzif/docs/schematic_review_report.md`, and this should be folded in
with that work rather than done piecemeal.

### Peak hold: the CW case

On keyed CW at 20 wpm with S9 peaks, the needle swings across **roughly half the scale
on every dot** — 48 % of sweep at the default 25 ms averaging. Averaging barely helps:
even at 250 ms it is still 18 %, and by then the meter is too sluggish for SSB.

This is not a defect. A real S-meter bounces on CW for exactly the same reason, and
operators read the peak. But it does mean peak hold earns its place as a *mode-dependent*
option — useful on CW, unnecessary on SSB — rather than being rejected on the grounds
that the Model 540 lacked it. Implemented behind `cfg.peak_hold`, off by default.

## Development approach

Build the meter as a **standalone prototype first**, driven by synthetic data, so the
artwork and ballistics can be iterated without the radio. Only once it looks right does
it get wired to real ADAU1467 / Pico data. Two halves, done:

1. `meter_prototype.html` — the *visual* prototype. Answers "does it look right?"
2. `meter.c` + `meter_sim.c` — the *numerical* prototype. Answers "are the numbers
   right?", and is the code that actually ships.

Keeping both matters: the visual prototype is where the face and the feel get judged,
but it cannot tell you that your overshoot figure is quoted against the wrong
denominator, or that 60 ms of averaging is silently cancelling your ballistics. The
harness caught both.

### Next steps

1. ~~Build `meter_sim`~~ — done; builds clean and all six scenarios run.
2. ~~Decide the display hardware~~ — done; Nextion 3.5″, 480×320.
3. Judge the face at true size in `nextion_face.html` and settle the tick density and
   numeral size. Then export the background PNG and build the `.tft` in the Nextion
   Editor.
4. Write the Nextion command layer: sweep fraction → `line` + segmented `xpic`.
5. Add the 4-pin display header to `nzif/microcontroller.kicad_sch`, folded in with the
   Critical schematic fixes.
6. Fit `METER_COUPLING_DB`, `METER_P_KNEE_W` and `METER_V_KNEE_V` against the real
   coupler and detectors at bring-up. The values in `meter.h` are physically sensible
   placeholders, not measurements.
7. Replace the placeholder per-band trims with measured figures.
8. Get a straight-on scan of the meter face to tighten the S-unit anchors.

## Contents of this folder

- `README.md` — this file.
- `ten tec meter.jpeg` — reference photograph of the Ten-Tec Model 540 meter face.
- `meter_prototype.html` — standalone visual prototype (see below).
- `nextion_face.html` — the same face at the Nextion's true 480×320, with tick-density
  options, the needle's swept band, a redraw cost table, and a background-PNG export for
  the Nextion Editor. **Open this one locally** — the export is blocked in the published
  view.
- `meter.h` / `meter.c` — **the implementation.** Portable C99, no dependencies
  beyond `<math.h>`. Intended to compile unchanged into the Pico firmware.
- `meter_sim.c` — host-only exercise harness. Not firmware.
- `Makefile` — host build of the harness.

## The implementation

`meter.c` is the real thing: scale mapping, detector linearisation, and movement
ballistics, with no Pico SDK dependency so it can be exercised on a desktop first.
The interface is small:

```c
meter_t m;
meter_config_t cfg;

meter_config_defaults(&cfg);
meter_init(&m, &cfg);

/* receive */
meter_set_mode(&m, METER_MODE_RX);
meter_update_rx(&m, level_dbm);              /* from the ADAU1467 */

/* transmit */
meter_set_mode(&m, METER_MODE_TX);
meter_update_tx(&m, v_fwd, v_rev, true);     /* raw Pico ADC volts */

meter_tick(&m, dt_seconds);                  /* advance the movement */
float needle = meter_needle(&m);             /* 0..1 of full sweep */
```

`meter_tick()` integrates at a fixed 1 ms sub-step, so the movement behaves the same
whether it is called at 30 Hz or 120 Hz. On an M0+ with no FPU this is a few hundred
soft-float operations per frame — negligible against a 133 MHz core.

There is also `meter_cat_sm()`, which produces the 0–30 value for the CAT `SM` command
that `firmware/usb_cdc/main.c` already reports via `g_smeter`. Note it deliberately
uses the **Kenwood TS-2000 curve** (0–15 spans S0–S9, 15–30 spans S9 to S9+60), not the
Ten-Tec face curve — Hamlib expects the former, the panel shows the latter, and
conflating them would make the CAT reading wrong.

### Running the harness

```sh
cd nzif/meter_display
mingw32-make CC=clang run     # Windows
make run                      # Linux / macOS
```

Or skip make entirely — it is only two files:

```sh
clang -std=c99 -Wall -Wextra -Wpedantic -O2 -o meter_sim.exe meter.c meter_sim.c -lm
```

It drives six scenarios and prints an ASCII needle alongside the numbers: the S7 step,
2:1 SWR at 100 W, the detector linearisation error sweep, the full scale map, a damping
comparison, and keyed CW. Builds clean under `-Wall -Wextra -Wpedantic`.

### Toolchain on this machine

This is **Windows 11 on ARM64**, which rules out most of the usual advice — MSYS2,
MinGW-w64 and w64devkit all ship x86_64 binaries that would run under emulation.

Two things are installed:

- **LLVM 22.1.8** via `winget install LLVM.LLVM` (native `woa64` build). Its default
  target is `aarch64-pc-windows-msvc`, which needs Visual Studio's headers — so on its
  own it **cannot** build this, failing with `'math.h' file not found`.
- **llvm-mingw 20260826, ucrt-aarch64**, unpacked to
  `%USERPROFILE%\llvm-mingw-20260826-ucrt-aarch64`. Self-contained: native ARM64 clang
  targeting `aarch64-w64-windows-gnu`, with its own headers and libs, plus a bundled
  `mingw32-make`. **This is the one that works**, and no Visual Studio install is needed.

Add its `bin` to PATH, or invoke it by full path.

### Building the Pico firmware is a separate problem

`firmware/usb_cdc` needs `arm-none-eabi-gcc`, a *cross*-compiler targeting the RP2040's
Cortex-M0+. Neither toolchain above can build it, and it cannot build the host harness.
The Raspberry Pi Pico VS Code extension installs the SDK, ARM toolchain, CMake and Ninja
together; neither the SDK nor that toolchain is present yet.

`meter.c` is deliberately free of SDK dependencies so it can be exercised on the host
today and dropped into the firmware unchanged later.

## The prototype

`meter_prototype.html` is a self-contained page: open it in a browser, no build step,
no dependencies. It renders the face to a canvas at device resolution and drives the
needle with the damped second-order model above.

What it lets you trim:

- **Ballistics** — natural frequency, damping ratio, and AGC averaging, live.
- **Scenarios** — steady carrier, band noise, SSB speech envelope, 20 wpm CW, and QSB
  fading. The speech and CW cases are where ballistics are actually judged; a steady
  slider tells you very little.
- **Per-band trim** — placeholder offsets for all ten bands.
- **Transmit** — forward power and load mismatch, with the detector linearisation
  toggle described above.
- **Options under question** — peak hold and mechanical end stops, both switchable.

The calibration anchor table is displayed on the page in dBm and degrees so the face
geometry can be checked against a real one.

### Known limits of the current calibration

The reference photograph is taken at an angle with lamp glare across the face, so the
S-unit anchors are good to perhaps a couple of percent of sweep — enough to build
against, **not enough to cut artwork from**. A straight-on scan would let these be
tightened. The SWR marks are unaffected, being derived rather than measured.

## Related

- `nzif/microcontroller.kicad_sch` — Pi Pico, front panel I/O, coupler detector ADC inputs.
- `nzif/dsp.kicad_sch` — ADAU1467, source of the receive level estimate.
- Project `README.md` — directional coupler and detector description under "RF front-end board".
