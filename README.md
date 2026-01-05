# NZIF_Radio
A near zero-if radio architecture using a polyphase mixer

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
