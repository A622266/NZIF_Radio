# NZIF_Radio
A near zero-if radio architecture using a polyphase mixer

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
