# NZIF Radio

Near-zero-IF radio architecture built around an 8-phase harmonic rejection polyphase mixer and audio-rate ADC/DAC signal processing.

This board is the NZIF core: it converts differential RF into low-frequency quadrature baseband, then digitizes and processes the result with audio-rate converters and a SigmaDSP. The RF front end, PA, and post-PA output filters are implemented on a separate board; the receive and transmit mixer/baseband cores are on this board.

## Design goals

- Suppress the 3rd, 5th, and 7th LO harmonics with an 8-phase harmonic rejection mixer, reducing reliance on RF bandpass filters on this board.
- Use polyphase mixing and phase-domain harmonic suppression to minimize analog RF selectivity requirements.
- Avoid a conventional high-IF architecture: the design is near-zero-IF, using 192 kHz ADC/DAC sampling with a digital NCO offset to stay away from DC and 1/f noise.
- Keep the Rx and Tx front end compact and fully differential, while placing the PA and post-PA filters on a separate board.
- Preserve differential signal flow from the RF mixer through the driver amps and into the audio-rate converters.

## Architecture overview

### Core concept

The NZIF board uses an 8-phase commutating mixer topology on receive and transmit. In the receive path, differential RF (`RF+`, `RF-`) is sampled by eight phase-shifted switch networks, producing eight baseband phase taps. Opposite phases are then recombined into four differential channels for ADC conversion:

- `BB_0` / `BB_180` → `P0_IN+` / `P0_IN-`
- `BB_45` / `BB_225` → `P45_IN+` / `P45_IN-`
- `BB_90` / `BB_270` → `P90_IN+` / `P90_IN-`
- `BB_135` / `BB_315` → `P135_IN+` / `P135_IN-`

The eight-phase approach provides phase-domain cancellation of odd-order LO harmonics (3rd, 5th, 7th) and reduces the need for RF bandpass filtering on this board.

### Near-zero-IF operation

This is not a classic zero-IF design:

- ADC and DAC converters run at 192 kHz.
- The ADAU1467 DSP uses a digital NCO to shift the effective center frequency away from DC.
- That offset avoids LO leakage and 1/f noise while preserving complex I/Q demodulation.

Because the converters are audio-rate, the RF conversion chain moves entirely into the phase-domain mixer and the digital domain — there is no IF filter bank.

## How the receive signal flows

```
Antenna/RF board → SMA (J101) → 1:1 balun → RF+ / RF-
    → SN74CBT3125C quad switch arrays (×4)
        controlled by phase_0, phase_45, … phase_315
        ├─ BB_0    → ADA4625-2 unity-gain buffer
        ├─ BB_45   → ADA4625-2 unity-gain buffer
        ├─ BB_90   → ADA4625-2 unity-gain buffer
        ├─ BB_135  → ADA4625-2 unity-gain buffer
        ├─ BB_180  → ADA4625-2 unity-gain buffer
        ├─ BB_225  → ADA4625-2 unity-gain buffer
        ├─ BB_270  → ADA4625-2 unity-gain buffer
        └─ BB_315  → ADA4625-2 unity-gain buffer
    → top sheet pairs opposite phases into differential channels:
        BB_0/BB_180   → P0_IN+/P0_IN-
        BB_45/BB_225  → P45_IN+/P45_IN-
        BB_90/BB_270  → P90_IN+/P90_IN-
        BB_135/BB_315 → P135_IN+/P135_IN-
    → ADA4945-1 fully differential amplifiers (×4)
        → P0_FDA+/P0_FDA-, P45_FDA+/P45_FDA-,
          P90_FDA+/P90_FDA-, P135_FDA+/P135_FDA-
    → ADAU1979 4-channel 24-bit ADC (192 kHz)
    → ADAU1467 SigmaDSP: I/Q correction, NCO offset, filter, demodulate
    → ADAU1361 audio codec → headphone/speaker
```

## How the transmit signal flows

```
Mic → ADAU1361 ADC → ADAU1467 DSP (Weaver SSB / CW shaping)
    → ADAU1962A 12-ch DAC (I/Q baseband, 192 kHz)
    → SN74CBTLV3125 switch arrays
        driven by same phase_0 … phase_315 clock lines
    → 8-phase RF reconstruction → RF output
    → External PA board and post-PA LPF bank → antenna
```

## What is on this board

### `nzif/rx_mixer.kicad_sch`

Implements the receive 8-phase polyphase mixer.

- Four **SN74CBT3125CPW** quad bus-switch ICs commutate the differential RF input (`RF+`/`RF-`) onto eight phase-tagged baseband nodes. Two switch ICs handle the `RF+` half of the differential signal; two handle `RF-`. The eight phase-control lines (`phase_0`, `phase_45`, … `phase_315`) are driven from the clock tree.
- Each baseband node is buffered by one section of an **ADA4625-2** unity-gain op-amp. The ADA4625-2 is a dual JFET-input op-amp (3.3 nV/√Hz input noise, rail-to-rail output) that isolates the high-impedance switch nodes from the downstream differential signal chain and prevents charge injection from disturbing adjacent phase taps.

### `nzif/rx_driver_amps.kicad_sch`

Converts the eight single-ended phase outputs into four differential channels for the ADC.

- Four **ADA4945-1** fully differential amplifiers condition the signals. Each ADA4945-1 takes a pair of opposite-phase single-ended inputs and produces a differential output directly suitable for the ADAU1979 differential input. Gain is set by the Rf/Rg resistor network on each channel.
- Outputs: `P0_FDA+/P0_FDA-`, `P45_FDA+/P45_FDA-`, `P90_FDA+/P90_FDA-`, `P135_FDA+/P135_FDA-`.

### `nzif/adcs.kicad_sch`

- Contains the **ADAU1979** 4-channel 24-bit audio ADC.
- Digitizes the four differential baseband pairs at 192 kHz.
- The ADAU1979 is chosen for its 4.5 Vrms differential input range, which provides headroom against strong-signal transients before any AGC correction occurs.

### `nzif/dacs.kicad_sch`

- Contains the **ADAU1962A** 12-channel 24-bit audio DAC.
- Generates the analog transmit I/Q channels for the TX mixer at 192 kHz.
- The 12-channel output provides multiple differential pairs for the TX baseband; the same I2S/TDM protocol used by the ADAU1979 connects directly to the ADAU1467.

### `nzif/tx_mixer.kicad_sch`

- Implements the transmit 8-phase RF reconstruction mixer.
- Uses **SN74CBTLV3125** bus-switch arrays (the 3.3 V-rated LV variant, matched to DAC output levels) to commutate the I/Q baseband onto the 8-phase RF reconstruction network.
- Uses the same `phase_0` … `phase_315` control lines as the receive mixer.

### `nzif/dsp.kicad_sch`

- Contains the **ADAU1467** SigmaDSP (dual-core, 294 MHz).
- Programmed via SigmaStudio (graphical block-diagram, no traditional firmware).
- Receive functions: I/Q DC offset correction, gain and phase trim, NCO fine-tuning (±96 kHz), digital FIR/IIR selectivity filtering, AGC, SSB/CW/AM demodulation (Weaver method).
- Transmit functions: Weaver SSB encoding, CW keying-envelope shaping, TX I/Q baseband generation.
- The Pi Pico writes calibration coefficients and NCO frequency words to ADAU1467 parameter RAM over I2C.

### `nzif/clock_tree.kicad_sch`

Generates the LO and the eight phase-control signals for both the Rx and Tx mixers.

- **AD9523-1** clock generator provides both the RF LO and the system audio MCLK from a single on-chip VCO. The VCO-path outputs drive the phase distribution logic; a separate reference-path output provides a stable fixed MCLK to all audio ICs, completely independent of LO tuning.
- **CTS_535_TCXO** provides the precision reference clock for the AD9523-1 PLL.
- **SN74AUC16374** (16-bit D flip-flop register) latches the phase-select control words and distributes the phase clock edges to the mixer switch gates.
- **SN74CBT3253 / SN74CBTLV3253** multiplexers route the phase-clocked outputs to the correct switch control lines.

### `nzif/microcontroller.kicad_sch`

- Contains a **Raspberry Pi Pico** (RP2040, dual-core Arm Cortex-M0+, 133 MHz, 264 kB SRAM, 2 MB flash).
- Controls frequency tuning (programs the AD9523-1 via SPI), manages band changes, runs the I/Q calibration routine, handles front-panel input (rotary encoder, buttons, display), and presents a Hamlib-compatible UART CAT port for logging software.

### `nzif/audio_subsystem.kicad_sch`

- Contains the **ADAU1361** stereo audio codec.
- On receive: DAC output drives headphone/speaker with demodulated audio from the ADAU1467.
- On transmit: ADC input digitizes the microphone and feeds the ADAU1467 DSP.

### `nzif/power_ldos.kicad_sch`

- **LT3045** ultra-low-noise positive LDO (2 μVrms) for precision analog and RF rails.
- **LT3094** ultra-low-noise negative LDO for the bipolar op-amp supply rails.
- LDO choice is driven by the ADC noise floor and LO phase noise — both track supply noise on the precision analog rails.

### `nzif/power_switching_reg.kicad_sch`

- **LT8330** boost converter and **ADP2302/ADP2303** switching regulators for digital rails.

## LO chain

```
CTS_535_TCXO → AD9523-1 PLL → LO output   (VCO path → SN74AUC16374 phase register
                                             → SN74CBT3253/CBTLV3253 phase muxes
                                             → phase_0 … phase_315 → mixer switch gates)
                            → MCLK output  (reference path, fixed ~12.288 MHz
                                             → ADAU1979, ADAU1467, ADAU1962A, ADAU1361)
```

The AD9523-1 VCO is tuned by the Pi Pico (via SPI) to the operating frequency. A divider chain produces the 8-phase clock signals at 8× the LO frequency — equal to 8× the RF frequency for direct-conversion operation. The reference-path MCLK output is completely decoupled from VCO tuning, so retiming the LO does not disturb the audio clock.

**6m phase-mode transition:** For 8-phase operation at 50 MHz RF, the phase register clock must run at 8 × 50 MHz = 400 MHz. The SN74AUC16374 (rated to approximately 250 MHz in the AUC logic family) cannot operate reliably at this rate. The clock tree therefore switches to 4-phase operation for the 6m band (50–54 MHz), requiring only 200 MHz — within the register's operating range. Four-phase operation maintains adequate harmonic rejection (>40 dB) while respecting the component speed limit.

## Why 8-phase harmonic rejection?

A conventional 2-phase (single-switch) commutating mixer has a square-wave LO that contains odd harmonics. The 3rd harmonic at −9.5 dBc (amplitude ratio 1/3) causes a mixing response to signals at f_RF/3 — an unwanted reception at 1/3 of the operating frequency, suppressed only by external bandpass filtering.

The 8-phase architecture cancels these harmonics by phase. Each of the eight switch taps samples the RF with a LO phase that is an integer multiple of 45°. When the eight outputs are recombined, the harmonic responses cancel as rotating phasor sums:

- **3rd harmonic:** each tap's 3rd-harmonic component is phase-shifted by 3 × 45° = 135° relative to adjacent taps. Summing eight equal phasors separated by 135° gives a vector sum of zero. Theoretical rejection: >60 dB.
- **5th harmonic:** 5 × 45° = 225° per step; vector sum ≈ 0. Theoretical rejection: >50 dB.
- **7th harmonic:** 7 × 45° = 315° per step; vector sum ≈ 0. Theoretical rejection: >45 dB.

In practice the rejection is limited by phase and amplitude matching across the SN74CBT3125 switch array, PCB trace symmetry, and timing accuracy of the phase clock distribution. Well-designed 8-phase boards typically achieve 40–55 dB rejection. The 9th harmonic (9 × 45° = 405° ≡ 45°) is not cancelled and passes through — its product at f_RF/9 is far from any amateur band for most HF frequencies.

## Why near-zero-IF?

- No high-frequency IF or fixed IF filter is required, which eliminates a switched crystal or SAW filter bank.
- The ADC and DAC are audio-rate (192 kHz), keeping component cost and complexity low compared to RF-sampling approaches that require multi-GSPS ADCs.
- A digital NCO in the ADAU1467 moves the effective receive center frequency away from DC, avoiding LO leakage and 1/f noise that degrade pure zero-IF designs.
- The ±96 kHz NCO range, combined with 100 kHz LO tuning steps, provides continuous coverage of all HF amateur bands without gaps.

## Architecture comparison

**Traditional superheterodyne with roofing filters** (Elecraft K3, Icom IC-7610): uses a fixed IF and crystal roofing filter to remove out-of-band power before the second mixer. The roofing filter physically limits IMD to strong in-band signals. System IIP3 is typically +15–25 dBm (limited by the active first mixer before the roofing filter). Crystal filters are expensive speciality parts. NZIF relies on phase-domain harmonic rejection and high switch linearity rather than analog selectivity, and achieves IMD performance through linearity rather than filtering.

**Tayloe/quadrature sampling detectors** (4-phase commutating switch at RF → DC): low component count, directly produce I/Q baseband. More sensitive to LO feedthrough and image issues than an 8-phase design. NZIF extends the commutating-switch concept to eight phases, providing stronger odd-harmonic rejection at the cost of a more complex clock distribution.

**NorCal NC2030 (Tayloe, N7VE):** The closest published benchmark — a 4-phase direct-conversion phasing receiver with a narrow-band audio preamp (1.5 kHz BW). Measured specs: MDS −135 dBm (→ system NF ≈ 12 dB at 500 Hz BW), system IIP3 ≈ +28.5 dBm (calculated from measured IP3 DR plateau of 109 dB), BDR 119–142 dB across 2–20 kHz spacing. Image rejection >45 dB. CW-only, two bands, ~11 mA at 12 V. The NC2030's narrow audio preamp inherently rejects far-off blockers before the compression point — a genuine direct-conversion advantage. NZIF targets comparable IIP3 with 8-phase harmonic rejection in place of the analog phasing network.

**Norcal 2030 / direct sampling:** samples HF at very high ADC rates and moves all selectivity into the digital domain. Maximum flexibility but requires multi-GSPS ADCs (high cost, high power, ~15–25 W). NZIF achieves a comparable digital-first philosophy with audio-rate converters by using a polyphase analog front end and NCO offset.

## Key component rationale

| Part | Role | Why this part |
|------|------|---------------|
| SN74CBT3125CPW | Rx polyphase mixer switches | Logic-level LO drive; four switches per IC; rated 5 V for Rx chain; low on-resistance CMOS bus switch |
| SN74CBTLV3125 | Tx polyphase mixer switches | Same topology as Rx, 3.3 V-rated LV variant to match DAC output levels |
| ADA4625-2 | Baseband node buffers (Rx mixer) | Dual JFET op-amp, 3.3 nV/√Hz, unity-gain stable; isolates high-impedance switch nodes from the differential driver chain without loading the switching node |
| ADA4945-1 | Rx differential driver amps | Fully differential amplifier; converts single-ended phase-buffer outputs to the differential signal required by ADAU1979; maintains fully balanced path from mixer to ADC |
| ADAU1979 | 4-channel 24-bit Rx ADC | 4.5 Vrms differential input range prevents ADC clipping during strong-signal transients; 192 kHz max sample rate; I2S/TDM connects directly to ADAU1467 |
| ADAU1962A | 12-channel 24-bit Tx DAC | Multi-channel differential DAC for Tx I/Q baseband; I2S/TDM from ADAU1467; same Analog Devices audio ecosystem ensures compatible clocking and protocol |
| ADAU1467 | SigmaDSP core | 294 MHz dual-core fixed-point DSP; SigmaStudio graphical programming; integrates NCO, FIR/IIR filter bank, AGC, I/Q calibration, and demodulation in one chip; direct I2C parameter RAM access for runtime calibration updates from the Pi Pico |
| AD9523-1 | Clock generator | 14 independent outputs; single VCO generates both the variable RF LO and a fixed audio MCLK via the reference-path output; −226 dBc/Hz FOM; eliminates a separate audio oscillator |
| CTS_535_TCXO | Frequency reference | < 2 ppm TCXO stability adequate for amateur digital modes (FT8 requires < 1 Hz accuracy at HF, ≈ 0.1 ppm at 10 MHz) without oven complexity |
| Raspberry Pi Pico (RP2040) | Radio controller | Dual-core Arm M0+, 133 MHz; SPI for AD9523-1 and peripherals; I2C for ADAU1467 parameter RAM; GPIO for band switching; USB for CAT; low cost, widely available |
| LT3045 / LT3094 | Precision LDOs | 2 μVrms output noise; required to keep LDO supply noise below the ADC noise floor and avoid degrading LO phase noise on precision analog rails |

## LO band plan and coverage

The NZIF radio covers all amateur HF bands (160m through 10m) plus 6m. The LO is tuned directly to the operating frequency in 100 kHz tiles; the ADAU1467 NCO provides ±96 kHz fine-tuning within each tile, ensuring continuous coverage without gaps.

8-phase mixing is used through 10m. On 6m (50–54 MHz), the clock tree switches to 4-phase operation because 8-phase would require the phase register to operate at 400 MHz, beyond the SN74AUC16374's rated speed.

| Band | Frequency range (MHz) | LO range (MHz) | Phase mode | NCO range (kHz) | Coverage |
|------|-----------------------|----------------|------------|-----------------|----------|
| 160m | 1.800 – 2.000 | 1.800 – 2.000 | 8-phase | ±96 | Complete |
| 80m  | 3.500 – 4.000 | 3.500 – 4.000 | 8-phase | ±96 | CW and SSB |
| 60m  | 5.330 – 5.405 | 5.330 – 5.405 | 8-phase | ±96 | Channelized, full coverage |
| 40m  | 7.000 – 7.300 | 7.000 – 7.300 | 8-phase | ±96 | Complete |
| 30m  | 10.100 – 10.150 | 10.100 – 10.150 | 8-phase | ±96 | Complete |
| 20m  | 14.000 – 14.350 | 14.000 – 14.350 | 8-phase | ±96 | Complete |
| 17m  | 18.068 – 18.168 | 18.068 – 18.168 | 8-phase | ±96 | Complete |
| 15m  | 21.000 – 21.450 | 21.000 – 21.450 | 8-phase | ±96 | Complete |
| 12m  | 24.890 – 24.990 | 24.890 – 24.990 | 8-phase | ±96 | Complete |
| 10m  | 28.000 – 29.700 | 28.000 – 29.700 | 8-phase | ±96 | Complete |
| 6m   | 50.000 – 54.000 | 50.000 – 54.000 | 4-phase | ±96 | Reduced to 4-phase (clock rate limit) |

## Performance characteristics

### Signal chain and noise figure

The NZIF receive chain has no dedicated on-board LNA between the antenna port and the polyphase mixer. Noise figure and linearity are set by the SN74CBT3125 switch conversion loss and the ADA4625-2 / ADA4945-1 input noise.

**Estimated figures (cascade analysis; bring-up measurement required):**

- **System NF:** ~6–9 dB. Polyphase mixer conversion loss approximately 6 dB (dominated by switch Rds(on) and signal distribution to eight phases); ADA4625-2 contributes ~2–3 dB NF at baseband. Any gain provided by the RF front-end board directly improves this figure.
- **System IIP3:** Estimated +25–35 dBm at the antenna port. The SN74CBT3125 is not characterized as an RF mixer component; IIP3 must be measured during bring-up. The differential topology and high switch bandwidth suggest competitive linearity.
- **Harmonic rejection:** Theoretical >60 dB (3rd), >50 dB (5th), >45 dB (7th) from ideal 8-phase phase-domain cancellation. Practical expectation for a well-built board: 40–55 dB, limited by phase-clock timing accuracy and switch Rds(on) matching across the four ICs.
- **ADC SNR:** 110–115 dB (ADAU1979 at 192 kHz, 24-bit).
- **DAC THD+N:** < 0.005% (ADAU1962A at 192 kHz, 12-channel differential output).

### Comparison to published benchmarks

The NC2030 (Tayloe, N7VE) is the closest published measured benchmark: a 4-phase direct-conversion phasing receiver with a narrow-band audio preamp. Its specs are bench-measured; NZIF figures are estimated from cascade analysis.

| Metric | NC2030 (measured) | NZIF (estimated) |
|--------|-------------------|-----------------|
| System NF | ~12 dB (from MDS = −135 dBm at 500 Hz BW) | ~6–9 dB |
| System IIP3 | +28.5 dBm (from IP3 DR plateau = 109 dB) | +25–35 dBm (TBD) |
| Harmonic rejection | >45 dB (phasing network) | >40–55 dB (8-phase cancellation) |
| Instantaneous BW | ~1.5 kHz (audio preamp) | ±96 kHz (ADC + NCO) |
| Modes | CW only (2 bands) | All modes, all HF + 6m |
| Power | ~0.13 W | ~5–8 W |

**Why we should beat NC2030 on sensitivity:** No audio preamp compression bottleneck; the ADA4945-1 + ADAU1979 chain handles much wider bandwidth before limiting. The 8-phase architecture extends coverage to all HF bands.

**Where NC2030 has an inherent advantage:** The NC2030's narrow audio preamp (1.5 kHz BW, −39 dB rolloff at 20 kHz) acts as pre-compression selectivity — blockers 20 kHz away are attenuated 39 dB before the compression point. NZIF's wideband chain sees the full RF spectrum at the switch input; selectivity is applied only after the ADC.

**Caveat:** All NZIF figures are calculated estimates. NC2030's are bench-measured. Bring-up measurement is required to validate NZIF performance.

### Comparison to other HF receiver architectures

| Architecture | NF (dB) | IIP3 (dBm) | Harmonic rejection | Power (W) | Notes |
|---|---|---|---|---|---|
| NZIF (8-phase, est.) | 6–9 | +25–35 (est.) | 40–55 dB odd harmonics | 5–8 | No on-board LNA; measured values TBD |
| NC2030 (measured) | ~12 | +28.5 | >45 dB (phasing) | ~0.13 | CW only, 2 bands, narrow audio preamp |
| Traditional superhet | 8–12 | +15–25 | Good (with roofing filter) | 10–15 | Crystal roofing filter limits IMD |
| Direct sampling | 5–7 | +35+ | Excellent (digital) | 15–25 | High-speed ADCs required |

## Software architecture

Three processors divide the control and signal-processing work with non-overlapping roles.

### Raspberry Pi Pico (RP2040) — radio control layer

Programs hardware registers: AD9523-1 LO frequency and phase dividers (via SPI), band switching, PE4312 or equivalent AGC attenuator, front-panel encoder and buttons, OLED/TFT display. Runs the I/Q calibration routine at power-up and on each band change. Presents a Hamlib-compatible UART CAT port to an optionally connected PC for logging software (N1MM+, WSJT-X, fldigi, etc.).

### ADAU1467 (SigmaDSP) — baseband DSP layer

Receives 24-bit I/Q samples from the ADAU1979 at 192 kHz. SigmaStudio blocks implement in sequence:

- **I/Q correction matrix**: DC offset subtraction, gain trim, and phase trim applied before any demodulation. Coefficients written by the Pi Pico via I2C parameter RAM.
- **NCO**: digital quadrature oscillator (±96 kHz range) providing fine frequency offset between AD9523-1 PLL steps. Frequency word written by the Pi Pico at each tuning step.
- **Weaver demodulator**: the 8-phase mixer hardware provides the first quadrature mixing stage. The ADAU1467 completes the Weaver second stage — a second NCO at the audio center frequency followed by matched lowpass filters. Summing the two paths selects USB; subtracting selects LSB. AM demodulation uses envelope detection on the corrected I/Q magnitude.
- **Selectivity filters**: the lowpass filters following the second Weaver mixing stage define channel bandwidth. Multiple width settings (2.4 kHz SSB, 500 Hz CW, 6 kHz AM) are selectable by the Pi Pico over I2C.
- **AGC**: operates after the narrowband filter where processing gain has already improved effective SNR. Level detector drives the attenuator control for fast AGC.

On transmit: the ADAU1467 accepts microphone audio from the ADAU1361, applies Weaver SSB encoding, generates CW keying envelopes, and outputs I/Q baseband to the ADAU1962A DAC.

### I/Q calibration (Pi Pico, runs at power-up and each band change)

The polyphase mixer introduces three imperfections that degrade SSB image rejection: DC offset from CMOS switch charge injection, I/Q gain imbalance from switch Rds(on) mismatch between channels, and I/Q phase imbalance from clock distribution skew. The ADAU1467 applies a 2×2 correction matrix:

```
I_corr = I_raw − DC_I
Q_corr = (I_raw − DC_I) × sin(ε) + (Q_raw − DC_Q) × cos(ε) × g
```

Two calibration methods run in sequence:

1. **Noise covariance (fast, no external stimulus)**: thermal noise has equal power on I and Q and zero cross-correlation. Non-zero cross-correlation or power imbalance directly indicates gain or phase error. The Pi Pico reads accumulated I/Q statistics from ADAU1467 readback cells (via I2C), computes the correction matrix algebraically, and writes the result to parameter RAM. Converges in < 1 s.

2. **Tone injection (confirms result)**: the Pi Pico temporarily programs a known NCO offset and injects a reference tone into the RX path. A real-valued tone on the RF input should produce a single-sideband ADAU1467 response; residual image power measured from ADAU1467 readback registers indicates remaining I/Q imbalance. The Pi Pico iterates correction coefficients until image rejection ≥ 50 dB.

## Open items

The schematic review (see [`nzif/docs/schematic_review_report.md`](nzif/docs/schematic_review_report.md)) identified critical issues that must be resolved before layout. Status: **HOLD — do not proceed to layout freeze until Critical items are resolved.**

Key critical issues:

1. **Power symbol IDs on custom rails**: wrong library IDs on custom rails in `rx_mixer` and `rx_driver_amps` (e.g., `power:+5V` used for `−3.5V_RX_OPAMPS`) — netlist cross-connections will short rails and destroy components.
2. **LT3045 feedback resistors**: missing "k" suffix causes values to read as 49.9 Ω instead of 49.9 kΩ — all affected LDO rails produce near-zero output voltage.
3. **LT8330 / ADP2303 feedback**: wrong resistor values produce incorrect output voltages on multiple switching regulator rails.
4. **AD9523-1 VCXO control (R701)**: 1 kΩ value gives 11 kΩ total load, below the 20 kΩ minimum — VCXO control voltage corrupted, PLL will not lock.
5. **U706 part/value mismatch**: symbol is SN74CBT3253 (5 V rated); value is SN74CBTLV3253 (3.6 V max) — wrong device assembled at 5 V will be destroyed.
6. **ADAU1962A AVDD supply label**: "2.5V" label on AVDD pins (minimum 3.0 V) — DAC operates out of spec or fails to power up.
7. **LT3045 / LT3094 output capacitors**: 4.7 µF fitted; 10 µF ceramic minimum for LDO stability — LDOs will oscillate on precision analog rails.
8. **TX mixer RF reconstruction filter absent**: no output filter shown in `tx_mixer.kicad_sch` — required before the PA interface to suppress harmonics.
9. **ADA4945-1 feedback capacitors**: all DNP in the current schematic — oscillation risk at the differential driver outputs.

## Links to the main schematic sheets

- `nzif/nzif.kicad_sch` — top-level board interconnects.
- `nzif/rx_mixer.kicad_sch` — 8-phase receive mixer.
- `nzif/tx_mixer.kicad_sch` — transmit mixer/modulator.
- `nzif/rx_driver_amps.kicad_sch` — baseband conditioning for the ADC.
- `nzif/adcs.kicad_sch` — ADAU1979 ADC interface.
- `nzif/dacs.kicad_sch` — ADAU1962A DAC interface.
- `nzif/dsp.kicad_sch` — ADAU1467 DSP and audio/serial signal flow.
- `nzif/clock_tree.kicad_sch` — phase clocking and timing.
- `nzif/microcontroller.kicad_sch` — Raspberry Pi Pico control logic.
- `nzif/audio_subsystem.kicad_sch` — ADAU1361 audio codec (mic/speaker interface).
- `nzif/power_ldos.kicad_sch` — LT3045/LT3094 LDO regulators.
- `nzif/power_switching_reg.kicad_sch` — LT8330/ADP2302/ADP2303 switching supplies.

## Files in this repo

- `README.md` — this file.
- `NOTES.md` — supplemental design notes and signal-flow derivations.
- `rxmixer.md` — detailed description of the receive 8-phase mixer.
- `nzif/...` — KiCad schematic source files.
- `nzif/docs/schematic_review_report.md` — schematic review findings (Critical items block layout freeze).
- `firmware/...` — Pico firmware and USB/CAT bring-up support.
- `.claude/...` — agent files used for review workflows.
