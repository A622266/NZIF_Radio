# NZIF_Radio

A near zero-if radio architecture using a polyphase mixer

## Front-End Signal Example (7 MHz SSB Receive)

To make the receive path concrete, assume the antenna/front-end sees an **SSB** signal near **7.000 MHz** with a single audio tone of **1 kHz**.

### Time-domain view (at J101)

One simple model (USB case) is:

\[
s(t)=A_s\cos\left(2\pi\cdot\left(7\text{ MHz}+1\text{ kHz}\right)\cdot t\right)
\]

Where:

- `A_s` is received signal amplitude
- In ideal SSB, the transmitted carrier is suppressed
- For LSB, the RF component is at \(7\text{ MHz}-1\text{ kHz}\) instead

### Frequency-domain view (before mixing)

For this single-tone example, the spectrum at the RF input contains one dominant tone for the selected sideband:

- **USB example:** 7.001000 MHz (with little/no carrier at 7.000000 MHz)
- **LSB example:** 6.999000 MHz (with little/no carrier at 7.000000 MHz)

```text
Amplitude
    ^
    |                          |  USB tone (7.001 MHz)
    |
    |
    |                 .        .  (carrier at 7.000 MHz ideally suppressed)
    |
    |        |
    |        |  LSB tone (6.999 MHz)
    |--------|--------|-----------------------> Frequency
          6.999    7.000    7.001   MHz
```

This is the signal that enters `J101` and is then converted to differential (`RF+`/`RF-`) by `TR102` before polyphase downconversion.

### Why convert to differential (`RF+` / `RF-`)?

Converting the antenna signal from single-ended to differential gives several practical advantages in this receiver:

- **Better immunity to coupled noise:** interference that appears equally on both lines is common-mode and is largely rejected by the differential mixer/input stage.
- **Lower even-order distortion and feedthrough sensitivity:** balanced drive tends to cancel symmetry-related error terms, improving strong-signal behavior.
- **Improved LO isolation behavior in switching mixers:** differential structures generally reduce sensitivity to LO feedthrough and self-mixing artifacts around DC.
- **More signal swing for a given supply/headroom:** the receiver processes the voltage difference between `RF+` and `RF-`, which can improve effective dynamic range compared with a comparable single-ended stage.
- **Natural fit for downstream differential signal chain:** your baseband and ADC path are differential, so staying balanced from the mixer forward helps preserve CMRR and layout symmetry.

In short, the transformer is not only an impedance/interface element; it is also setting up a balanced signal environment that improves robustness and linearity for the NZIF conversion chain.

### What happens after NZIF mixing (LO = 7.000 MHz)

Using the USB single-tone example:

\[
f_{RF}=7.001\text{ MHz}, \quad f_{LO}=7.000\text{ MHz}
\]

Mixing produces sum and difference terms:

\[
f_{sum}=f_{RF}+f_{LO}=14.001\text{ MHz}
\]

\[
f_{diff}=|f_{RF}-f_{LO}|=1\text{ kHz}
\]

After low-pass filtering in the baseband path, the high-frequency sum product is rejected and the 1 kHz term remains.

```text
Mixer output (before LPF):

Amplitude
        ^
        |   | 1 kHz (difference, wanted baseband)
        |
        |
        |
        |                                    | 14.001 MHz (sum, filtered out)
        |------------------------------------|-----------------------------> Frequency
            near DC/audible region                 RF-range product

After baseband low-pass:

Amplitude
        ^
        |   | 1 kHz audio tone
        |   |
        |---|--------------------------------------------------------------> Frequency
            1 kHz
```

For an LSB tone at 6.999 MHz, the magnitude is still 1 kHz after mixing, but in complex I/Q representation it appears with opposite frequency sign. That sign is what preserves sideband sense through the DSP chain.

### Signal-to-netname map for this example

For the 7 MHz SSB example, the signal path aligns to your schematic labels as follows:

1. **Front-end RF input (`J101`)**  
    Received SSB energy near 7.000 MHz enters as a single-ended signal.

2. **Transformer conversion (`TR102`)**  
    The same RF content is converted to differential and appears on `RF+` / `RF-`.

3. **Polyphase switching mixer (`Rx_mixer`)**  
    LO phases `phase_0` ... `phase_315` commutate the RF onto baseband phase nodes:
    - `BB_0`, `BB_45`, `BB_90`, `BB_135`
    - `BB_180`, `BB_225`, `BB_270`, `BB_315`

4. **Differential phase pairing (top sheet wiring)**  
    Opposite baseband phases are paired into driver inputs:
    - `BB_0` / `BB_180` -> `P0_IN+` / `P0_IN-`
    - `BB_45` / `BB_225` -> `P45_IN+` / `P45_IN-`
    - `BB_90` / `BB_270` -> `P90_IN+` / `P90_IN-`
    - `BB_135` / `BB_315` -> `P135_IN+` / `P135_IN-`

5. **Driver outputs toward ADC sheet (`RX_Driver_Amps`)**  
    Conditioned differential baseband exits as:
    - `P0_FDA+/-`, `P45_FDA+/-`, `P90_FDA+/-`, `P135_FDA+/-`

6. **ADC differential inputs (`ADCs` sheet)**  
    These map to `AIN1` through `AIN4` differential pairs for digitization.

Practical interpretation: in this single-tone USB case, those baseband nets carry a low-frequency quadrature representation of a 1 kHz tone (rather than a 7 MHz waveform), which is exactly what the downstream ADC and DSP chain are designed to process.

### USB vs LSB at complex baseband (I/Q view)

With LO tuned to 7.000 MHz, a single audio-tone offset maps to complex baseband as:

- **USB tone (+1 kHz):** \(x_{bb}(t)=A\,e^{+j2\pi(1\text{ kHz})t}\)
- **LSB tone (-1 kHz):** \(x_{bb}(t)=A\,e^{-j2\pi(1\text{ kHz})t}\)

Equivalent I/Q forms:

- **USB:** \(I= A\cos(2\pi ft),\;Q= +A\sin(2\pi ft)\)
- **LSB:** \(I= A\cos(2\pi ft),\;Q= -A\sin(2\pi ft)\)

```text
Complex plane (I horizontal, Q vertical)

            +Q
             ^
             |
  USB (+f)   |   phasor rotates CCW
             |
-------------+----------------------> +I
             |
  LSB (-f)   |   phasor rotates CW
             |

Key point: same audio magnitude, opposite rotation/sign in complex baseband.
```

That opposite sign is why an I/Q receiver can distinguish USB from LSB even when both are near the same RF tuning frequency.

### Numeric sample points (normalized, A = 1)

For a 1 kHz baseband tone, one cycle is 1 ms. Sampling at quarter-cycle points:

| t | Phase | I = cos(2pi f t) | Q (USB) = +sin(2pi f t) | Q (LSB) = -sin(2pi f t) |
| --- | ---: | ---: | ---: | ---: |
| 0 us | 0 deg | +1.000 | +0.000 | -0.000 |
| 250 us | 90 deg | +0.000 | +1.000 | -1.000 |
| 500 us | 180 deg | -1.000 | +0.000 | -0.000 |
| 750 us | 270 deg | +0.000 | -1.000 | +1.000 |
| 1000 us | 360 deg | +1.000 | +0.000 | -0.000 |

The I column is the same for USB and LSB, while Q flips sign. That sign flip is the practical discriminator used by complex-baseband DSP.

### Effect of LO frequency error (tuning offset)

If the LO is not exactly on frequency, the recovered baseband tone shifts by the LO error:

\[
f_{bb}=f_{RF}-f_{LO}
\]

Example (USB tone):

- Desired RF tone: 7.001000 MHz
- LO set correctly: 7.000000 MHz -> baseband = 1.000 kHz
- LO set +50 Hz high: 7.000050 MHz -> baseband = 0.950 kHz
- LO set -50 Hz low: 6.999950 MHz -> baseband = 1.050 kHz

So a small tuning error appears directly as an audio pitch shift at baseband. In complex I/Q, the sideband sign (USB vs LSB) is still preserved, but the entire spectrum is translated by the LO offset.

## Receive Signal Path (J101 to ADC)

This is the receive chain on the top sheet for the `J101` input path:

1. **RF input connector (`J101`)**  
    The external receive signal enters as a single-ended RF input at `J101`.

2. **Input transformer (`TR102`, ADT1-1WT)**  
    `TR102` converts the single-ended RF input into a differential pair for the mixer front end.  
    The transformer secondary center tap is planned to be biased at **2.5 V**.

3. **Differential RF into mixer (`RF+`, `RF-`)**  
    The top sheet routes the transformer outputs to `RF+` and `RF-`, which feed the `Rx_mixer` sheet.

4. **Polyphase downconversion (`Rx_mixer`)**  
    The mixer uses LO phase inputs (`phase_0`, `phase_45`, `phase_90`, `phase_135`, `phase_180`, `phase_225`, `phase_270`, `phase_315`) and generates baseband phase outputs:
    - `BB_0`, `BB_45`, `BB_90`, `BB_135`
    - `BB_180`, `BB_225`, `BB_270`, `BB_315`

5. **Baseband phase pairing into driver amps (`RX_Driver_Amps`)**  
    The top sheet pairs opposite phases into differential driver inputs:
    - `BB_0` / `BB_180` → `P0_IN+` / `P0_IN-`
    - `BB_45` / `BB_225` → `P45_IN+` / `P45_IN-`
    - `BB_90` / `BB_270` → `P90_IN+` / `P90_IN-`
    - `BB_135` / `BB_315` → `P135_IN+` / `P135_IN-`

6. **Driver amplification and ADC drive**  
    `RX_Driver_Amps` conditions these signals and outputs:
    - `P0_FDA+/-`, `P45_FDA+/-`, `P90_FDA+/-`, `P135_FDA+/-`

7. **Routing into ADC channels (`ADCs` sheet)**  
    On the top sheet, driver outputs map into ADC differential inputs as:
    - `P0_FDA+` → `AIN1N`, `P0_FDA-` → `AIN1P`
    - `P45_FDA+` → `AIN2N`, `P45_FDA-` → `AIN2P`
    - `P90_FDA+` → `AIN3N`, `P90_FDA-` → `AIN3P`
    - `P135_FDA+` → `AIN4N`, `P135_FDA-` → `AIN4P`

8. **Digitization**  
    The ADC converts the four differential analog channels into serial digital audio data for downstream DSP processing.

## Pico USB CAT Bring-up (High Level)

We added a small Raspberry Pi Pico firmware that exposes a USB virtual serial port and responds to basic Kenwood-style CAT commands. This lets us confirm the USB connection, command parsing, and expected replies before tying into full radio hardware or logging software.

In short:

- The Pico connects via micro USB only (no pin headers required).
- Flashing is done by holding BOOTSEL and copying a .uf2 file to the Pico's USB drive.
- A simple test script sends CAT commands and prints the replies.

Details and step-by-step instructions are in [firmware/usb_cdc/README.md](firmware/usb_cdc/README.md).

## Rx Mixer Subsystem (First Stage)

Think of the mixer as a “signal shifter.” It takes the high-frequency radio signal coming in from the antenna and shifts it down to a much slower signal that is easier to process. This is like using a gear to make a fast spinning wheel turn slower so you can measure it.

### What it does in simple terms

- **Takes the RF input** (the tiny signal from the antenna).
- **Uses a local oscillator (LO)** as a timing signal, kind of like a strobe light, to sample the RF.
- **Creates two versions of the signal** called I and Q. These are the same signal, just shifted in time by a quarter cycle, which helps computers figure out the exact frequency and phase.

### How it is built

- **Multi-phase LO switching** performs the downconversion to baseband.
- **Polyphase baseband nodes** are combined into differential channel pairs.
- **Buffer/driver stages** condition the resulting baseband signals for the ADC path.

### Netnames and signal path (current schematic)

- **RF input:** The transformer outputs land on `RF+` and `RF-` and feed the `Rx_mixer` sheet.
- **LO drive:** LO phase nets (`phase_0`, `phase_45`, `phase_90`, `phase_135`, `phase_180`, `phase_225`, `phase_270`, `phase_315`) drive the switching sequence used for NZIF downconversion.
- **Baseband phases:** The mixer produces `BB_0`, `BB_45`, `BB_90`, `BB_135`, `BB_180`, `BB_225`, `BB_270`, and `BB_315`.
- **Driver inputs:** These phases are paired into differential driver inputs on the top sheet as `P0_IN+/-`, `P45_IN+/-`, `P90_IN+/-`, and `P135_IN+/-`.

After this stage, the I and Q signals go to the ADCs so the DSP can do the rest of the radio processing.

## Rx Driver Amps (Signal Conditioning)

The Rx driver amps are like the “volume and protection” stage before the ADCs. They make sure the I and Q signals are the right size, clean, and safe for the converter.

### What they do in simple terms

- **Boost or trim the signal level** so the ADC sees a strong, usable signal (not too weak, not too big).
- **Filter out unwanted noise** so the ADC samples a cleaner waveform.
- **Protect the ADC** by clamping or limiting signals that get too large.

### How it is built (driver amps)

- **Fully differential amplifiers (ADA4945-1)** handle the I/Q pairs and keep noise low.
- **Clamp circuits and resistors** set the maximum signal swing.
- **Local power and decoupling** keep the amplifier stable and quiet.

### Netnames and signal path (driver amps to ADC)

- **Inputs from mixer buffers:** The driver stage receives four differential pairs on `P0_IN+/-`, `P45_IN+/-`, `P90_IN+/-`, and `P135_IN+/-`.
- **Common-mode and clamps:** `VREF_BUF` sets the output common-mode for the ADA4945-1, while `+VCLAMP`/`-VCLAMP` limit large swings before the ADC.
- **Outputs to ADC sheet:** The driver amps export `P0_FDA+/-`, `P45_FDA+/-`, `P90_FDA+/-`, and `P135_FDA+/-`.
- **ADC mapping on top sheet:** `P0_FDA` → `AIN1`, `P45_FDA` → `AIN2`, `P90_FDA` → `AIN3`, `P135_FDA` → `AIN4` (with `+` routed to `N` and `-` routed to `P`).

This stage ensures the ADC gets a clean, correctly sized signal so the DSP can process it accurately.

## ADC Subsystem Operation

The ADC subsystem digitizes the four analog IF channels (I/Q from both receivers) for processing by the DSP. The design uses a multi-channel audio ADC configured for high-performance analog-to-digital conversion.

### Key Features

- **4 Differential Analog Inputs**: Each receiver's I and Q channels are captured as differential pairs (AIN1P/N through AIN4P/N)
- **Digital Audio Interface**: Serial data output on `SDATAOUT1` with BCLK (bit clock) and LRCLK (left/right clock) synchronization
- **Master Clock Input**: MCLKIN provides the sampling clock, distributed through series termination resistors (R202-R205, 49.9Ω) to minimize reflections
- **I2C Control**: Configuration and control via I2C interface (SDA/SCL) with 10kΩ pull-up resistors
- **Power Supply**: Separate analog (AVDD) and digital (DVDD/IOVDD) supplies with local decoupling capacitors for optimal noise performance
- **Reference Voltage**: External VREF pin allows precision voltage reference for improved accuracy

The ADC operates in slave mode, synchronized to the system master clock. Data is output in a time-division multiplexed format on the serial interface, allowing the DSP to process all four channels for quadrature demodulation and signal processing.

## DSP Subsystem Operation

The heart of the NZIF radio is the ADAU1467 SigmaDSP audio processor, a 300MHz programmable DSP with integrated ADC/DAC interfaces. This chip performs all digital signal processing functions including filtering, demodulation, AGC, and audio routing.

### Architecture Overview

The ADAU1467 acts as the central signal processing hub, interfacing with multiple audio data streams:

- **4 TDM Input Channels**: Receive digitized RF signals from ADCs (TDM0-3)
- **4 TDM Output Channels**: Drive DACs for transmit and audio output
- **Multiple Multi-Purpose Pins (MP0-MP25)**: Configurable GPIOs for control signals
- **Auxiliary ADC Inputs (AUXADC0-7)**: Monitor analog signals like AGC levels

### ADC Interface

The DSP receives digitized IF signals from the ADC subsystem via Time-Division Multiplexed (TDM) serial audio interfaces:

- **TDM0_SDOUT_ADC**: Primary input from 4-channel ADC carrying I/Q data from both receivers
- **Synchronous Clocking**: BCLK (bit clock) and LRCLK (frame clock) ensure proper data alignment
- **Master Clock**: System MCLK (typically 24.576 MHz for 48kHz sample rate) drives both ADC and DSP
- **I2C Control**: DSP can configure ADC parameters via shared I2C bus (SCLK/SCL and MISO/SDA lines)

The ADC streams arrive on `SDATA_IN0` input, where the DSP demultiplexes the four channels and routes them to internal processing blocks for demodulation and filtering.

### DAC Interface

Processed audio and transmit signals are sent to DACs via TDM outputs:

- **TDM1_SDIN_DAC**: Transmit I/Q signals to TX DACs
- **Additional TDM Outputs**: Audio to codec (TDM2) and headphone output (TDM3)

### Power and Configuration

- **Separate Power Domains**: AVDD (analog), DVDD (digital core), IOVDD (I/O) for optimal noise isolation
- **SPI/I2C Boot**: Can self-boot from external flash or be configured via control interface
- **Multipurpose Pins**: Flexible GPIO for AGC control, PTT sensing, and system coordination

The DSP performs real-time processing at audio sample rates (typically 48kHz or 96kHz), with sufficient MIPS to handle multiple receiver channels, filtering, AGC, and audio routing simultaneously.
