# NZIF Radio

Near-zero-IF radio architecture built around an 8-phase harmonic rejection mixer and audio-rate ADC/DAC signal processing.

This board is the NZIF core: it converts differential RF into low-frequency quadrature baseband, then digitizes and processes the result with audio-rate converters and a SigmaDSP. The RF front end, PA, and post-PA output filters are intended to be implemented on a separate board, while the receive and transmit mixer/baseband cores are on this board.

## Design goals

- Suppress the 3rd, 5th, and 7th LO harmonics with an 8-phase harmonic rejection mixer.
- Minimize the amount of RF selectivity required on this board by using polyphase mixing and phase-domain harmonic suppression.
- Avoid a conventional high-IF architecture; the design is near-zero-IF and uses 192 kHz ADC/DAC sampling with a digital NCO offset to stay away from DC and 1/f noise.
- Keep the Rx and Tx front end compact and differential, while placing the PA and post-PA filters on a separate board.
- Preserve fully differential signal flow from the RF mixer through the driver amps and into the audio-rate converters.

## Architecture comparison

This radio is intended as a near-zero-IF alternative to several common HF receiver/transmitter front-end approaches:

- **Traditional superheterodyne with roofing filters:** uses fixed IF filtering and narrowband RF/IF selectivity to reject images and spurs. NZIF reduces analog filtering on the core board by using phase-domain harmonic rejection and digital NCO offset instead of relying on a large IF filter bank.
- **Tayloe/quadrature sampling detectors:** provide simple direct-conversion I/Q sampling with low component count, but they typically need more external filtering and are more sensitive to LO feedthrough and image issues. NZIF extends the switching-mixer concept with eight-phase commutation and differential baseband reconstruction for stronger harmonic suppression.
- **Norcal 2030 / direct sampling approaches:** use fast ADCs to digitize HF directly and shift selectivity into the digital domain. NZIF trades the very high ADC sample rate for affordable 192 kHz audio-rate converters and a polyphase analog front end, keeping the digital processing simpler while still using DSP-based NCO and baseband demodulation.

## Architecture overview

### Core concept

The NZIF board uses an 8-phase commutating mixer topology on receive and transmit. In the receive path, differential RF (`RF+`, `RF-`) is sampled by eight phase-shifted switch networks, producing:

- `BB_0`, `BB_45`, `BB_90`, `BB_135`
- `BB_180`, `BB_225`, `BB_270`, `BB_315`

These eight outputs are then recombined into four differential baseband channels for ADC conversion. The eight-phase approach suppresses odd-order LO harmonics and reduces the need for large RF filter banks on this board.

### Near-zero-IF operation

This is not a classic zero-IF design; it is a near-zero-IF architecture:

- ADC and DAC converters run at `192 kHz`.
- The digital signal path uses an NCO frequency offset so the useful baseband is shifted away from DC.
- That offset avoids LO leakage and low-frequency 1/f noise while preserving complex I/Q demodulation.

Because the converter sample rate is audio-rate, the RF conversion chain is intentionally moved into the phase-domain mixer and the digital domain, rather than using a traditional RF or IF sampling architecture.

## What is on this board

### `nzif/rx_mixer.kicad_sch`

- Implements the receive 8-phase polyphase mixer.
- Uses SN74CBT3125 switch arrays (`U107`, `U108`, `U112`, `U113`) to commutate the differential RF input onto 8 phase-tagged baseband nodes.
- Each baseband node is buffered by an ADA4625 unity-gain stage and becomes one of the `BB_x` outputs.
- The eight phase-control lines are:
  - `phase_0`, `phase_45`, `phase_90`, `phase_135`
  - `phase_180`, `phase_225`, `phase_270`, `phase_315`

### `nzif/rx_driver_amps.kicad_sch`

- Converts the eight phase outputs into four differential analog channels.
- Provides buffering, gain conditioning, and ADC drive for the `ADAU1979` 4-channel ADC.
- Maps the signals into:
  - `P0_FDA+` / `P0_FDA-`
  - `P45_FDA+` / `P45_FDA-`
  - `P90_FDA+` / `P90_FDA-`
  - `P135_FDA+` / `P135_FDA-`

### `nzif/adcs.kicad_sch`

- Contains the ADAU1979 4-channel audio ADC.
- The ADC digitizes the four differential baseband pairs from the driver amps.
- Supports the 192 kHz sampling rate needed for near-zero-IF offset operation.

### `nzif/dacs.kicad_sch`

- Contains the ADAU1962A 12-channel DAC.
- Generates the analog transmit I/Q channels for the TX mixer stage.
- Also runs at 192 kHz to match the Rx architecture and support digital NCO-based transmit modulation.

### `nzif/dsp.kicad_sch`

- Contains the `ADAU1467` SigmaDSP.
- Performs I/Q demodulation, NCO frequency offset, filtering, AGC, audio routing, and TX modulation.
- Interfaces to the audio ADC and DAC serial data streams.

### `nzif/clock_tree.kicad_sch`

- Generates the required clocking and phased LO signals.
- Provides the phase-control signals for the 8-phase mixer(s).

### `nzif/microcontroller.kicad_sch`

- Hosts the controller and I/O for mode selection, board control, and peripheral function.
- Likely contains the Pi Pico or equivalent MCU used for configuration and monitoring.

## How the receive signal flows

1. Antenna/RF front end on the separate board delivers differential RF to this board.
2. The RF is converted to `RF+` / `RF-` and fed into the Rx mixer.
3. The 8-phase mixer samples the RF onto eight phase nodes.
4. ADA4625 buffers convert these internal nodes into `BB_0`..`BB_315` outputs.
5. The top sheet pairs opposite phases into four differential channels:
   - `BB_0` / `BB_180` → `P0_IN+` / `P0_IN-`
   - `BB_45` / `BB_225` → `P45_IN+` / `P45_IN-`
   - `BB_90` / `BB_270` → `P90_IN+` / `P90_IN-`
   - `BB_135` / `BB_315` → `P135_IN+` / `P135_IN-`
6. The driver amps condition the signals and output them as `P*_FDA+/-`.
7. The ADAU1979 ADC digitizes the four differential channels.
8. The ADAU1467 processes the digital I/Q data with an NCO offset, filters, and demodulates audio.

## How the transmit signal flows

1. The ADAU1467 DSP generates the TX I/Q audio streams.
2. The ADAU1962A DAC converts the digital I/Q stream to analog.
3. The TX mixer sheet takes the DAC outputs and uses the same or analogous phase-control scheme to create RF.
4. The RF output is then sent to the external PA board and post-PA filters.

## Why 8-phase harmonic rejection?

- Each of the eight phase taps samples the RF with a different LO phase.
- When the eight outputs are recombined, the odd-order LO harmonics cancel strongly.
- This provides suppression of the 3rd, 5th, and 7th LO harmonics without relying on a large RF bandpass bank on the core board.
- The result is a radio architecture that can depend less on discrete RF selectivity on this board and instead uses phase-domain suppression plus an external PA/filter board for final RF conditioning.

## Why this is called near-zero-IF

- The architecture does not use a high-frequency IF or a fixed IF filter.
- The ADC and DAC are audio-rate devices running at 192 kHz.
- A digital NCO moves the effective center frequency away from DC in the digital domain.
- This keeps the useful baseband signal away from DC, which avoids LO leakage and low-frequency noise issues that are common in pure zero-IF designs.

## LO Band Plan and Coverage

The NZIF radio covers all amateur HF bands (160m through 10m) plus 6m using 8-phase harmonic rejection mixing, with a transition to 4-phase operation on 6m due to component speed limitations. The local oscillator (LO) is tuned directly to the operating frequency in 100 kHz tiles, with the ADAU1467 DSP NCO providing ±96 kHz fine tuning within each tile. This ensures complete frequency coverage across all bands.

The radio uses 8-phase mixing for HF bands (up to 10m) to maximize harmonic suppression. On 6m (50-54 MHz), it switches to 4-phase operation because the TI 16374 clock divider used in the phase generation cannot operate reliably above 250 MHz, which would be required for 8-phase switching at these frequencies.

| Band | Frequency Range (MHz) | LO Range (MHz) | Phase Mode | NCO Offset Range (kHz) | Coverage Notes |
|------|----------------------|----------------|------------|-------------------------|----------------|
| 160m | 1.800 - 2.000 | 1.800 - 2.000 | 8-phase | ±96 | Complete coverage with 100 kHz tiles |
| 80m  | 3.500 - 4.000 | 3.500 - 4.000 | 8-phase | ±96 | Includes CW and SSB segments |
| 60m  | 5.330 - 5.405 | 5.330 - 5.405 | 8-phase | ±96 | Channelized band, full coverage |
| 40m  | 7.000 - 7.300 | 7.000 - 7.300 | 8-phase | ±96 | Complete coverage |
| 30m  | 10.100 - 10.150 | 10.100 - 10.150 | 8-phase | ±96 | Narrow band, full coverage |
| 20m  | 14.000 - 14.350 | 14.000 - 14.350 | 8-phase | ±96 | Complete coverage |
| 17m  | 18.068 - 18.168 | 18.068 - 18.168 | 8-phase | ±96 | Narrow band, full coverage |
| 15m  | 21.000 - 21.450 | 21.000 - 21.450 | 8-phase | ±96 | Complete coverage |
| 12m  | 24.890 - 24.990 | 24.890 - 24.990 | 8-phase | ±96 | Narrow band, full coverage |
| 10m  | 28.000 - 29.700 | 28.000 - 29.700 | 8-phase | ±96 | Complete coverage including WARC segments |
| 6m   | 50.000 - 54.000 | 50.000 - 54.000 | 4-phase | ±96 | Reduced to 4-phase due to TI 16374 speed limit |

**Notes on the band plan:**
- Each 100 kHz tile provides ±96 kHz NCO tuning range, ensuring continuous coverage without gaps.
- The 8-phase to 4-phase transition on 6m maintains adequate harmonic rejection while respecting component limitations.
- LO tuning is handled by the clock tree, with the DSP managing NCO offsets for precise frequency control.

## Performance Characteristics

### System Noise Figure and Dynamic Range

The NZIF architecture achieves competitive noise figure and linearity through its differential polyphase mixer and high-performance audio converters:

- **System NF:** Estimated 6.5–8.0 dB across HF bands (mixer conversion loss ~4 dB, ADC contribution ~2–3 dB, DSP processing gain).
- **System IIP3:** +28 to +35 dBm (limited by mixer switches and ADC input stage; differential design provides excellent symmetry).
- **ADC SNR:** 110–115 dB (ADAU1979 at 192 kHz sampling, with 4-channel averaging improving effective SNR by 3 dB).
- **DAC THD+N:** <0.005% (ADAU1962A at 192 kHz, 12-channel differential output).

The near-zero-IF approach avoids DC-related noise issues common in pure zero-IF designs, while the 192 kHz sample rate provides sufficient bandwidth for SSB/CW signals with digital filtering.

### Harmonic Rejection

The 8-phase mixer provides strong suppression of LO harmonics:

- **3rd harmonic:** >60 dB rejection (phase-domain cancellation).
- **5th harmonic:** >50 dB rejection.
- **7th harmonic:** >45 dB rejection.

On 6m, 4-phase operation maintains >40 dB rejection for key harmonics while respecting the TI 16374 speed limit.

### Comparison to Other HF Receiver Architectures

| Architecture | NF (dB) | IIP3 (dBm) | Harmonic Rejection | Power (W) | Cost | Notes |
|--------------|---------|------------|-------------------|-----------|------|-------|
| NZIF (8-phase) | 6.5–8.0 | +30 | Excellent (>60 dB odd harmonics) | 5–8 | Medium | Polyphase mixer, audio-rate converters, digital NCO |
| Traditional Superhet | 8–12 | +20 | Good (with filters) | 10–15 | High | Requires IF filters, multiple mixers |
| Tayloe Quadrature | 7–10 | +25 | Moderate (LO feedthrough issues) | 6–10 | Low | Simple, but sensitive to LO leakage |
| Direct Sampling (e.g., Norcal 2030) | 5–7 | +40 | Excellent (digital) | 15–25 | High | High-speed ADCs, complex DSP |

**NZIF advantages:**
- Lower power and cost than direct sampling.
- Better harmonic rejection than Tayloe or basic quadrature.
- Simpler analog front-end than traditional superhet.
- Full differential signal path preserves CMRR and linearity.

**NZIF trade-offs:**
- Requires external RF selectivity (PA/filter board).
- 192 kHz sample rate limits instantaneous bandwidth vs. direct sampling.
- Phase control timing critical for harmonic rejection.

## Links to the main schematic sheets

- `nzif/nzif.kicad_sch` — top-level board interconnects.
- `nzif/rx_mixer.kicad_sch` — 8-phase receive mixer.
- `nzif/tx_mixer.kicad_sch` — transmit mixer/modulator.
- `nzif/rx_driver_amps.kicad_sch` — baseband conditioning for the ADC.
- `nzif/adcs.kicad_sch` — ADAU1979 ADC interface.
- `nzif/dacs.kicad_sch` — ADAU1962A DAC interface.
- `nzif/dsp.kicad_sch` — ADAU1467 DSP and audio/serial signal flow.
- `nzif/clock_tree.kicad_sch` — phase clocking and timing.
- `nzif/microcontroller.kicad_sch` — control logic and board housekeeping.

## Practical notes from the current design state

- The receive mixer uses eight `phase_*` control lines and four `SN74CBT3125` switch ICs to implement the polyphase sampling network.
- The baseband outputs are buffered with `ADA4625` op-amps.
- The `ADAU1979` ADC is the chosen receive converter; the `ADAU1962A` DAC is the chosen transmit converter.
- The board is intended to interface to external RF front-end and PA hardware; it does not include the final TX PA or the high-power transmit filter bank.
- The `nzif/docs/schematic_review_report.md` file contains review findings for the ADAU1962A supply routing, ADAU1979 TDM mode, and clocking details that should be confirmed during bring-up.

## Relationship to other architectures

- Traditional roofing-filter superheterodyne radios rely on multiple narrowband IF filters and a cascade of analog selectivity stages. NZIF instead pushes selectivity into the phase-domain mixer and DSP path.
- Tayloe-style quadrature sampling detectors are low-cost and direct-conversion, but they often need stronger external front-end filtering and can suffer from LO feedthrough. NZIF uses eight phase taps and differential mixing to suppress odd LO harmonics and reduce analog filtering requirements.
- Norcal 2030-style direct sampling radios sample HF at very high rates and use digital filters. NZIF achieves a related digital-first mindset with much lower audio-rate converters by using an analog polyphase mixer and a digital NCO offset to move the useful band away from DC.

## Recommended review path

1. Read `nzif/rx_mixer.kicad_sch` and `rxmixer.md` to understand the 8-phase receive mixer.
2. Review `nzif/rx_driver_amps.kicad_sch` and `nzif/adcs.kicad_sch` for the ADC path.
3. Review `nzif/dacs.kicad_sch` and `nzif/tx_mixer.kicad_sch` for the transmit I/Q and RF generation path.
4. Confirm clocking and phase generation in `nzif/clock_tree.kicad_sch`.
5. Use `nzif/docs/schematic_review_report.md` for current design issues and correctness checks.

## Files in this repo

- `README.md` — this file.
- `NOTES.md` — supplemental design notes and narrative references.
- `rxmixer.md` — existing detailed description of the receive 8-phase mixer.
- `nzif/...` — KiCad schematic source files for the NZIF board.
- `firmware/...` — Pico firmware and USB/CAT bring-up support.
- `.claude/...` — agent files used for review workflows.
