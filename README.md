# NZIF_Radio
A near zero-if radio architecture using a polyphase mixer

## Pico USB CAT Bring-up (High Level)
We added a small Raspberry Pi Pico firmware that exposes a USB virtual serial port and responds to basic Kenwood-style CAT commands. This lets us confirm the USB connection, command parsing, and expected replies before tying into full radio hardware or logging software.

In short:
- The Pico connects via micro USB only (no pin headers required).
- Flashing is done by holding BOOTSEL and copying a .uf2 file to the Pico's USB drive.
- A simple test script sends CAT commands and prints the replies.

Details and step-by-step instructions are in [firmware/usb_cdc/README.md](firmware/usb_cdc/README.md).

## Rx Mixer Subsystem (First Stage)

Think of the mixer as a “signal shifter.” It takes the high-frequency radio signal coming in from the antenna and shifts it down to a much slower signal that is easier to process. This is like using a gear to make a fast spinning wheel turn slower so you can measure it.

### What it does in simple terms:
- **Takes the RF input** (the tiny signal from the antenna).
- **Uses a local oscillator (LO)** as a timing signal, kind of like a strobe light, to sample the RF.
- **Creates two versions of the signal** called I and Q. These are the same signal, just shifted in time by a quarter cycle, which helps computers figure out the exact frequency and phase.

### How it is built:
- **Switches (SN74CBT3125)** act like very fast on/off gates.
- **Multiple LO phases** (many evenly spaced timing signals) drive the switches to reduce unwanted mixing noise.
- **Resistor networks** add the pieces together to form clean I and Q outputs.
- **Op amps (ADA4620-2)** buffer and boost the tiny signals so the ADC can read them.

### Netnames and signal path (current schematic):
- **RF input:** The transformer outputs land on `RF+` and `RF-` and feed the six EPC2037 switching transistors.
- **Gate drive:** `LT8418ACBZ-R7` takes the LO phase nets (`CLK_P0`, `CLK_P45`, `CLK_P90`, `CLK_P135`, `CLK_P180`, `CLK_P225`, `CLK_P270`, `CLK_P315`) and drives the EPC2037 gates with fast, low-impedance edges so they sample the RF cleanly.
- **Sample/hold:** Each EPC2037 output charges a capacitor that holds the instantaneous voltage on the baseband nodes (`Baseband_0`, `Baseband_45`, `Baseband_90`, `Baseband_135`, `Baseband_180`, `Baseband_225`, `Baseband_270`, `Baseband_315`).
- **Buffer pickup:** The ADA4625-2ARDZ buffer amps read those held voltages and pass them forward to the driver amp inputs (`P0_IN+/-`, `P1_IN+/-`, `P2_IN+/-`, `P3_IN+/-`).

After this stage, the I and Q signals go to the ADCs so the DSP can do the rest of the radio processing.

## Rx Driver Amps (Signal Conditioning)

The Rx driver amps are like the “volume and protection” stage before the ADCs. They make sure the I and Q signals are the right size, clean, and safe for the converter.

### What they do in simple terms:
- **Boost or trim the signal level** so the ADC sees a strong, usable signal (not too weak, not too big).
- **Filter out unwanted noise** so the ADC samples a cleaner waveform.
- **Protect the ADC** by clamping or limiting signals that get too large.

### How it is built:
- **Fully differential amplifiers (ADA4945-1)** handle the I/Q pairs and keep noise low.
- **Clamp circuits and resistors** set the maximum signal swing.
- **Local power and decoupling** keep the amplifier stable and quiet.

### Netnames and signal path (driver amps to ADC):
- **Inputs from mixer buffers:** The driver stage receives four differential pairs on `P0_IN+/-`, `P1_IN+/-`, `P2_IN+/-`, and `P3_IN+/-`.
- **Gain/feedback routing:** Each channel has feedback nets `P*_FB+/-`, and the switchable gain path uses `P*_SW+/-` with `Gain_Mode` selecting which path is active.
- **Common-mode and clamps:** `VREF_BUF` sets the output common-mode for the ADA4945-1, while `+VCLAMP`/`-VCLAMP` limit large swings before the ADC.
- **Outputs to ADC sheet:** The driver amps export differential outputs on `P0_FDA+/-`, `P1_FDA+/-`, `P2_FDA+/-`, and `P3_FDA+/-`, which route to the ADC inputs (`AIN1P/N` ... `AIN4P/N`) on the ADC sheet.

This stage ensures the ADC gets a clean, correctly sized signal so the DSP can process it accurately.

## ADC Subsystem Operation

The ADC subsystem digitizes the four analog IF channels (I/Q from both receivers) for processing by the DSP. The design uses a multi-channel audio ADC configured for high-performance analog-to-digital conversion.

### Key Features:
- **4 Differential Analog Inputs**: Each receiver's I and Q channels are captured as differential pairs (AIN1P/N through AIN4P/N)
- **Digital Audio Interface**: Serial data output on SDATAOUT1 and SDATAOUT2 pins with BCLK (bit clock) and LRCLK (left/right clock) synchronization
- **Master Clock Input**: MCLKIN provides the sampling clock, distributed through series termination resistors (R202-R205, 49.9Ω) to minimize reflections
- **I2C Control**: Configuration and control via I2C interface (SDA/SCL) with 10kΩ pull-up resistors
- **Power Supply**: Separate analog (AVDD) and digital (DVDD/IOVDD) supplies with local decoupling capacitors for optimal noise performance
- **Reference Voltage**: External VREF pin allows precision voltage reference for improved accuracy

The ADC operates in slave mode, synchronized to the system master clock. Data is output in a time-division multiplexed format on the serial interface, allowing the DSP to process all four channels for quadrature demodulation and signal processing.

## DSP Subsystem Operation

The heart of the NZIF radio is the ADAU1467 SigmaDSP audio processor, a 300MHz programmable DSP with integrated ADC/DAC interfaces. This chip performs all digital signal processing functions including filtering, demodulation, AGC, and audio routing.

### Architecture Overview:
The ADAU1467 acts as the central signal processing hub, interfacing with multiple audio data streams:
- **4 TDM Input Channels**: Receive digitized RF signals from ADCs (TDM0-3)
- **4 TDM Output Channels**: Drive DACs for transmit and audio output
- **Multiple Multi-Purpose Pins (MP0-MP25)**: Configurable GPIOs for control signals
- **Auxiliary ADC Inputs (AUXADC0-7)**: Monitor analog signals like AGC levels

### ADC Interface:
The DSP receives digitized IF signals from the ADC subsystem via Time-Division Multiplexed (TDM) serial audio interfaces:
- **TDM0_SDOUT_ADC**: Primary input from 4-channel ADC carrying I/Q data from both receivers
- **Synchronous Clocking**: BCLK (bit clock) and LRCLK (frame clock) ensure proper data alignment
- **Master Clock**: System MCLK (typically 24.576 MHz for 48kHz sample rate) drives both ADC and DSP
- **I2C Control**: DSP can configure ADC parameters via shared I2C bus (SCLK/SCL and MISO/SDA lines)

The ADC streams arrive on `SDATA_IN0` input, where the DSP demultiplexes the four channels and routes them to internal processing blocks for demodulation and filtering.

### DAC Interface:
Processed audio and transmit signals are sent to DACs via TDM outputs:
- **TDM1_SDIN_DAC**: Transmit I/Q signals to TX DACs
- **Additional TDM Outputs**: Audio to codec (TDM2) and headphone output (TDM3)

### Power and Configuration:
- **Separate Power Domains**: AVDD (analog), DVDD (digital core), IOVDD (I/O) for optimal noise isolation
- **SPI/I2C Boot**: Can self-boot from external flash or be configured via control interface
- **Multipurpose Pins**: Flexible GPIO for AGC control, PTT sensing, and system coordination

The DSP performs real-time processing at audio sample rates (typically 48kHz or 96kHz), with sufficient MIPS to handle multiple receiver channels, filtering, AGC, and audio routing simultaneously.
