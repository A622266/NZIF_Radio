# NZIF Radio RF Schematic Review — Consolidated Report

**Project:** NZIF Radio RF  
**Review Date:** 2026-04-11  
**Sheets Reviewed:** audio_subsystem, clock_tree, power_switching_reg, power_ldos, adcs, dacs, rx_mixer, tx_mixer, rx_driver_amps, nzif, dsp, microcontroller  
**Status: HOLD — Do not proceed to layout freeze until Critical items are resolved**

---

## 1. Executive Summary — Top 10 Must-Fix Items

The six domain reviews identified **9 Critical**, **20+ High**, and numerous Moderate findings. The items below represent existential risks to board functionality or component survival and must be resolved before any layout work proceeds.

| # | Area | Issue | Risk |
|---|------|-------|------|
| 1 | **RF — Power Symbols** | Wrong lib_ids on all custom rails in rx_mixer and rx_driver_amps (power:+5V/+6V used for −3.5V, +3.3V, +6.5V nets) | Netlist cross-connects rails; −3.5V_RX_OPAMPS shorts to +5V global; ADG884 destruction guaranteed |
| 2 | **Power LDOs** | R903/R907/R908/R909 values missing "k" suffix (read as 49.9Ω not 49.9kΩ) → LT3045 SET pins receive 49.9Ω → V_OUT ≈ 5mV on all affected rails | All rails powered by these LDOs produce near-zero voltage; complete subsystem failure |
| 3 | **Power Switching** | R1101/R1102 (LT8330): feedback resistors produce −1.79V, not −5V. R1103/R1104 (ADP2303): 100k/100k produces 1.6V, not 4V. Six further resistors have empty Value fields | Multiple supply rails at wrong voltages; dependent circuits receive incorrect supply |
| 4 | **Clock Tree** | OSC_CTRL net: R701=1kΩ gives 11kΩ load at AD9523-1 pin 8, below 20kΩ minimum — VCXO control voltage corrupted; PLL will not lock | Radio is inoperable without a locked reference clock |
| 5 | **Clock Tree** | U706 part/value mismatch: symbol = SN74CBT3253 (5V), value = SN74CBTLV3253 (LV, 3.6V max) annotated "Rx switches are 5V" | Wrong device assembled; either functionality fails or 3.6V-max device is destroyed at 5V |
| 6 | **Precision/DACs** | ADAU1962A (U601/U602): "2.5V" local label may drive AVDD pins — AVDD minimum is 3.0V | DAC operates out of spec or fails to power up; no audio output |
| 7 | **Power LDOs** | LT3045 output capacitors at 4.7µF (multiple instances) and LT3094 C931=4.7µF — both below 10µF ceramic minimum for LDO stability | LDO oscillation; noisy or unregulated output on precision analog rails |
| 8 | **Audio** | Net label "DVDOUT" should be "DVDDOUT" — potential CM/DVDDOUT net merger causes codec common-mode to be shorted to digital supply | Codec ADAU1361 malfunction; possible device damage |
| 9 | **Precision/ADCs** | #PWR0406 uses lib_id power:+3.3V for "+3.3V_CONVERTER" net → AVDD joins global +3.3V net instead of isolated converter rail | ADC analog supply contaminated by digital noise; defeats supply isolation intent |
| 10 | **Clock Tree** | AD9523-1 PLL1 external loop filter cap (pin 7, LF1_EXT_CAP) not confirmed present — PLL1 cannot lock | Downstream clocks derived from PLL1 are absent or jitter-dominated |

**Additional urgent items not in the top 10:** RF reconstruction filter absent from tx_mixer sheet; ADA4945-1 feedback caps all DNP (oscillation risk); R910 produces 1.65V not 1.8V on +1.8V_CLOCKTREE rail.

---

## 2. Per-Sheet Findings

### 2.1 audio_subsystem.kicad_sch

| Priority | Ref | Net / Pin | Issue | Action |
|----------|-----|-----------|-------|--------|
| CRITICAL | U1202 (SSM2211S) | 5V_LOUDSPEAKER / LOUTP | Speaker- wire at y=152.4/177.8 in proximity to 5V_LOUDSPEAKER at y=157.48 — possible shared node creating supply-to-output short | Verify no junction; inspect netlist for Speaker- node connection to 5V_LOUDSPEAKER |
| CRITICAL | ADAU1361 | DVDDOUT / CM | Net label reads "DVDOUT" — missing second D; may merge CM and DVDDOUT nets | Rename label to "DVDDOUT"; run ERC to confirm nets are distinct |
| HIGH | U1202 (SSM2211S) | Pin 6 / 5V_LOUDSPEAKER | Only 0.1µF C1214 on 5V supply; peak current ≈400mA requires bulk bypass | Add 10–47µF bulk cap at pin 6 |
| HIGH | ADAU1361 | SDA / SCL / IOVDD | I2C pull-up resistors (2kΩ to IOVDD) not confirmed on SDA/SCL in this sheet or parent | Confirm pull-ups exist at exactly one point in hierarchy; add if absent |
| HIGH | C12xx, R12xx (all) | — | All passive footprints are blank | Assign footprints before layout freeze |
| MODERATE | ADAU1361 | LINP (pin 10) / CM | LINP tied to CM — confirm intentional single-ended input on LINN only | Document design intent; if differential not needed, mark with schematic note |
| MODERATE | ADAU1361 | RINP/RINN/RAUX (pins 12/13/14) | No-connect markers present; datasheet requires connection to CM | Connect all three to CM net or confirm datasheet revision permits NC |
| MODERATE | C1215, C1216 | Headphone output | 220µF polarized coupling caps — polarity unverified; fc≈22.6Hz into 32Ω load, marginal | Verify polarity; consider 470µF for fc≈11Hz margin |
| MODERATE | C1212 | SSM2211S BYPASS (pin 2) | 0.47µF fitted; datasheet recommends 1µF for PSRR | Change to 1µF |
| MODERATE | — | Audio inputs | No RF EMI filter caps on any audio input — board is in RF radio environment | Add RC or ferrite+C EMI filter on each audio input trace |
| MODERATE | U1202 / ADAU1361 | LOUTP / LOUTN | Shared between headphone output and SSM2211S input — noise coupling path | Review routing; add isolation if simultaneous use intended |
| MINOR | ADAU1361 | JACKDET/MICIN (pin 4) | No-connect on digital input pin — undefined logic level | Add pull resistor to defined level (IOVDD or GND) |
| MINOR | ADAU1361 | ADDR0 / ADDR1 | Both tied GND → I2C address 0x38 | Confirm firmware initialises to address 0x38 |
| MINOR | R1201 | MIC_IN | 49.9kΩ shunt shifts DC bias on MIC_IN — verify operating point is within codec input range | Simulate or calculate DC bias with mic capsule source impedance |

---

### 2.2 clock_tree.kicad_sch

| Priority | Ref | Net / Pin | Issue | Action |
|----------|-----|-----------|-------|--------|
| CRITICAL | R701 / U702 (AD9523-1) | OSC_CTRL / Pin 8 | R701=1kΩ → total load 11kΩ, below 20kΩ minimum per AD9523-1 Table 5 — VCXO VC voltage corrupted | Increase R701 to ≥10kΩ (recommended ≥20kΩ) |
| CRITICAL | U706 (SN74CBT/LV3253) | VCC / 5V | Symbol lib_id = SN74CBT3253 (5V rated), value = SN74CBTLV3253 (LV, 3.6V max); sheet note says "5V" | Resolve to SN74CBT3253 (5V) on Rx side; update symbol, value, and BOM |
| HIGH | U702 (AD9523-1) | LF1_EXT_CAP (pin 7) | PLL1 external loop filter capacitor not confirmed present — PLL1 cannot lock | Add loop filter cap per AD9523-1 datasheet Table; confirm net connects to capacitor to GND |
| HIGH | X701 (CTS 535 TCXO) | EOH / Vc | EOH enable pin connection and Vc control voltage not confirmed; undriven EOH disables oscillator | Confirm EOH driven to enable state; confirm Vc connected to OSC_CTRL or pulled appropriately |
| HIGH | U702 (AD9523-1) | ZD_IN / ZD_IN_b (pins 70/71) | Zero-delay input pins not confirmed driven or terminated | Drive ZD_IN/ZD_IN_b with reference or terminate per datasheet zero-delay bypass mode |
| HIGH | X701, U704, U707 | — | Footprints missing on CTS 535 TCXO (X701), both SN74LVC8T245 (U704, U707) | Assign footprints; confirm package selection |
| MODERATE | C730, C732, C734 | LDO_PLL1 / LDO_VCO / LDO_DIV_M1 | Three 0.47µF bypass caps — verify each individually covers its designated LDO output pin | Confirm one cap per LDO; add if shared or absent |
| MODERATE | U703 (SN74AUC16374) | OE / 1.8V | OE pull-up to 1.8V not confirmed — undefined state during power-up/down | Add explicit pull-up to 1.8V supply on OE pin |
| MODERATE | TR701 (ADT1-1) | SMA reference input | No 50Ω primary termination on SMA reference input | Add 50Ω termination at SMA; confirm transformer primary sees 50Ω source |
| MODERATE | U702 (AD9523-1) | OSC_IN_b (pin 10) | Complementary AC-grounding not confirmed for single-ended clock input mode | Connect OSC_IN_b to AC ground (100nF to GND) per datasheet single-ended input configuration |
| MODERATE | — | Entire sheet | No frequency plan annotation — no way to verify divider settings by inspection | Add schematic note: reference freq, PLL1/PLL2 VCO freq, all output divider settings, final output frequencies |
| MODERATE | U705, U706 | Mux outputs | Outputs may float when OE_b is high | Add weak pull-down or bus-hold on all mux outputs; confirm OE_b sequencing |

---

### 2.3 power_switching_reg.kicad_sch

| Priority | Ref | Net / Pin | Issue | Action |
|----------|-----|-----------|-------|--------|
| CRITICAL | R1101, R1102 | LT8330 (U1101) feedback | 1MΩ/806kΩ → V_OUT=−1.79V, not −5V. For −5V with R_lower=806kΩ: R_upper must be ≈4.23MΩ | Replace R1101 with 4.23MΩ (nearest E96: 4.22MΩ); verify formula with selected values |
| CRITICAL | R1103, R1104 | ADP2303 (U1102) feedback | 100kΩ/100kΩ → V_OUT=1.6V via V_OUT=0.8×(1+R_TOP/R_BOT), not 4V. For 4V: R_TOP/R_BOT=4; use 400kΩ/100kΩ | Replace R1103 with 400kΩ; recalculate all ADP2303 feedback pairs from first principles |
| CRITICAL | R1108–R1113 | Multiple rails | Six resistors have empty Value fields — output voltages for multiple rails undefined | Calculate and fill all six values before any further review |
| HIGH | U1102, U1103, U1104 (ADP2303) | PGOOD pins | PGOOD pins have no pull-up resistors and no no-connect markers — power-good function unresolved | Add 100kΩ pull-up to appropriate rail on each PGOOD; or place no-connect and document reason |
| HIGH | R1108, R1109 | LT8330 (U1101) EN/UVLO | Values empty → UVLO threshold undefined | Calculate EN resistor divider for correct UVLO; populate values |
| HIGH | L1102, L1103, L1104 | ADP2303 | 3.3µH inductors fitted; datasheet recommends 4.7µH — higher ripple current, potential saturation | Change to 4.7µH with adequate saturation current rating; verify DCR |
| MODERATE | D1104 (PMEG6010CEJ) | — | 1A rated device — confirm not placed as catch diode in a 3A path | Verify peak inductor current; uprate diode if needed |
| MODERATE | Title block | — | Rev field reads "0.-" — typographic error | Correct to proper revision string |
| MODERATE | Title block | — | Callsign inconsistent with other sheets | Standardise callsign/project name across all title blocks |

---

### 2.4 power_ldos.kicad_sch

| Priority | Ref | Net / Pin | Issue | Action |
|----------|-----|-----------|-------|--------|
| CRITICAL | R903, R907, R908, R909 | LT3045 SET pins | Value "49.9" missing "k" suffix → parsed as 49.9Ω → V_OUT≈5mV on all affected rails | Change all four values to "49.9k"; recalculate which resistor sets which rail voltage |
| CRITICAL | Multiple LT3045 instances | LDO output | Multiple output caps at 4.7µF — LT3045 minimum for stability is 10µF ceramic | Replace with 10µF X5R/X7R 0805 on each LT3045 output; verify MLCC voltage derating |
| HIGH | R910 | +1.8V_CLOCKTREE SET | 16.5kΩ → V_OUT=1.65V, not 1.8V. For 1.8V: R_SET=18.0kΩ | Replace R910 with 18.0kΩ (E96: 18.0kΩ) |
| HIGH | U9xx (LT3045) | +3.3V_CONVERTERS IN | 4V input, 3.3V output: only 700mV headroom — marginal at full load and temperature | Review input source; target ≥4.5V input to LT3045 feeding +3.3V_CONVERTERS |
| HIGH | U904 (LT3094) | Output / C931 | C931=4.7µF below 10µF minimum for LT3094 stability | Replace C931 with 10µF |
| HIGH | All LT3045 instances | SET bypass cap | 0.47µF SET bypass cap must be present on each LT3045 SET pin — verify all instances | Check each LT3045 in sheet; confirm bypass cap populates at SET pin |
| HIGH | C913, C917, C922 | SET bypass / LT3045 | Value "04.7u" (leading zero) — if intended as 0.47µF (470nF) confirm; if 4.7µF, 10× error on SET bypass function | Clarify intended value; correct notation to "470n" or "0.47u"; re-evaluate PSRR impact |
| HIGH | All rails | — | No power sequencing: PGOOD not connected to LDO enables; all rails rise simultaneously | Define sequencing requirement; connect PGOOD outputs to downstream LDO EN pins or add sequencer |
| MODERATE | All LT3045 instances | EN/UV pins | EN/UV left no-connected — no remote shutdown or sequencing capability | If sequencing required, connect EN; otherwise document deliberate NC with rationale |
| MODERATE | U904 (LT3094) | VIOC (pin 7) | VIOC pin disposition unconfirmed — must not be accidentally driven | Verify pin 7 is explicitly no-connected or properly terminated per datasheet |
| MODERATE | R911, R912 | 20mΩ ballast resistors | Implemented as discrete 0603 — datasheet recommends PCB trace for thermal tracking | Consider replacing with PCB trace resistance; if discrete must be used, ensure thermal coupling |
| MODERATE | — | ADP2303 → LT3045 | No ferrite bead between ADP2303 8V output and LT3045 IN pins — switcher noise degrades LDO PSRR at 700kHz | Add ferrite bead (e.g., 600Ω @ 100MHz) + 10µF cap between converter output and LDO input |

---

### 2.5 adcs.kicad_sch

| Priority | Ref | Net / Pin | Issue | Action |
|----------|-----|-----------|-------|--------|
| CRITICAL | #PWR0406 | +3.3V_CONVERTER / AVDD | lib_id = power:+3.3V → net joins global +3.3V, not isolated converter rail; AVDD contaminated | Create dedicated power symbol for +3.3V_CONVERTER; do not reuse global power symbol |
| HIGH | U401 (ADA4807-1) | DISABLE (pin 5) | DISABLE pin connection not confirmed; undriven pin may disable amplifier | Tie DISABLE to V+ (supply rail) to keep amplifier permanently enabled, or connect to control GPIO |
| HIGH | AIN pairs (all) | AIN+ / AIN− | No differential shunt capacitor across AIN pairs — only 10Ω series resistors; no anti-aliasing Cdiff | Add 100–470pF C0G across each AIN+/AIN− pair at ADC input pins |
| HIGH | U401, 37+ passives | — | Footprints missing on U401 (ADA4807-1) and 37+ other components | Complete footprint assignment for all components before layout |
| MODERATE | ADAU1979 | IOVDD (pin 12) bypass cap | Decoupling cap returns to AGND — should return to DGND | Reroute bypass cap return to DGND net |
| MODERATE | ADAU1979 | SA_MODE / ADDR0 / ADDR1 | Pins not confirmed driven — I2C address undefined; possible floating logic inputs | Tie SA_MODE/ADDR0/ADDR1 to defined levels; document resulting I2C address |
| MODERATE | R1214 | — | Non-sequential refdes — likely copy-paste from another sheet | Renumber R1214 to next available R4xx refdes in this sheet |
| MINOR | ADAU1979 | SDATAOUT2 (pin 14) | Not exported — TDM channel count unclear | Confirm whether TDM4 or TDM8 mode; export SDATAOUT2 if TDM8 is required |
| MINOR | ADAU1979 / ADAU1962A | MCLKIN / MCLK | Verify MCLKIN for ADC and MCLK for DAC are same domain and frequency | Cross-reference against clock tree output frequencies |

---

### 2.6 dacs.kicad_sch

| Priority | Ref | Net / Pin | Issue | Action |
|----------|-----|-----------|-------|--------|
| CRITICAL | U601, U602 (ADAU1962A) | AVDD pins / "2.5V" | "2.5V" local label may connect to AVDD — ADAU1962A AVDD minimum is 3.0V | Trace "2.5V" net to all pins; confirm AVDD receives ≥3.0V supply; move 2.5V reference to correct pin |
| CRITICAL | C623, C624, C628 | Decoupling | Value = "0.iu" — typo for "0.1u" (100nF) | Correct all three to "100n" or "0.1u" |
| HIGH | — (majority of passives) | — | Majority of passive footprints missing | Assign all footprints before layout |
| MODERATE | R614 | IBIAS (3.32kΩ) | No tolerance annotation — 5% substitution would shift IBIAS by up to ±5% | Add "1%" tolerance annotation to R614 |
| MODERATE | Q601 (FZT951TA) | AVDD pass element | VBE drifts −2mV/°C — AVDD supply voltage will shift with temperature | Consider replacing Q601 with an LDO or adding feedback for stable AVDD |
| MODERATE | C629, C631, C635 | 10nF filter caps | Dielectric not specified — 10nF X7R will distort in signal path | Specify C0G/NP0 dielectric on all three |
| MINOR | ADAU1962A (U601, U602) | TDM slot assignments | DSP firmware must map DAC_P0+–DAC_P315± to correct TDM slots | Annotate TDM slot assignments on schematic; cross-reference to DSP firmware |

---

### 2.7 rx_mixer.kicad_sch

| Priority | Ref | Net / Pin | Issue | Action |
|----------|-----|-----------|-------|--------|
| CRITICAL | All custom power symbols | −3.5V_RX_OPAMPS / +3.3V_RX_MIXER / +6.5V | Wrong lib_ids: power:+5V used for non-5V rails → −3.5V_RX_OPAMPS nets to global +5V in netlist | Replace every power symbol with correct dedicated symbol; regenerate netlist and verify |
| CRITICAL | SN74CBT3125C | +3.3V_RX_MIXER | 5V device on what is labelled as 3.3V rail — out of spec; sheet note says "Rx needs 5V" | If Rx mixer needs 5V, rename rail to +5V_RX_MIXER and supply 5V; update all connected nets |
| HIGH | HC_201–HC_208 | Hold caps / AIN+/AIN− | 100nF hold caps give BW≈12kHz with N=4 annotation; should be N=8 giving BW≈16kHz — annotation wrong and cap values may need adjustment | Correct N=8 in bandwidth annotation; recalculate hold cap value for target receive bandwidth; update cap values |
| MODERATE | ADA4625-2 | EP (pin 9) / V− | Exposed pad not confirmed connected to V− | Connect EP to V− (negative supply) as required by datasheet |
| MODERATE | 10µF caps | +6.5V rail | 0603 10µF — voltage rating is 6.3V; +6.5V exceeds rating | Replace with 16V-rated caps in 0805 or larger package |
| MINOR | "HC_" prefix | Capacitor refdes | Non-standard prefix — BOM tools may not parse correctly | Renumber to standard C_xxx refdes or confirm BOM tool handles custom prefixes |

---

### 2.8 tx_mixer.kicad_sch

| Priority | Ref | Net / Pin | Issue | Action |
|----------|-----|-----------|-------|--------|
| HIGH | — | Post-mixer output | No reconstruction filter present despite sheet title "16 Phase Tx Harmonic Mixer and Reconstruction Filter" | Locate reconstruction filter in hierarchy or add filter components to this sheet before layout freeze |
| MODERATE | — | CLK_0/90/135 | Duplicate hierarchical label pins at identical coordinates — ERC may miss shorted labels | Clean up duplicate label placements; run ERC and confirm clean |
| MODERATE | — | phase_N (Rx) vs CLK_N (Tx) | Naming inconsistency for same clock tree outputs — confirm both refer to same physical signals | Standardise net naming across Rx and Tx sheets; annotate which clock tree output drives each |
| MODERATE | — | Tx DAC differential polarity | Differential polarity per arm not confirmed — incorrect polarity injects image/sideband | Verify LOUTP/LOUTN assignment per Tx arm; annotate polarity on schematic |
| MINOR | SN74CBTLV3125 | Symbol vs value | Value = CBTLV3125 on CBT3125C symbol — assembly will receive wrong device | Create dedicated symbol matching exact part; update BOM |
| MINOR | U801–U804 | Digikey part numbers | Empty — BOM incomplete | Add Digikey/Mouser part numbers for all four |

---

### 2.9 rx_driver_amps.kicad_sch

| Priority | Ref | Net / Pin | Issue | Action |
|----------|-----|-----------|-------|--------|
| CRITICAL | All custom power symbols | −3.5V_RX_OPAMPS / +6V | All custom rails use power:+6V as base symbol → −3.5V_RX_OPAMPS shorts to global +6V | Fix all power symbol lib_ids; this is the same root cause as RX-1 — fix together |
| CRITICAL | ADG884 | VDD / "+6V" | ADG884 VDD connected to "+6V" due to DA-1 power symbol error — ADG884 abs max VDD=3.6V | After fixing power symbols, confirm ADG884 VDD connects to correct ≤3.3V rail |
| HIGH | C343, C322, C319, C320, C340, C341, C344 | ADA4945-1 feedback | All 180pF feedback caps DNP in Rev 0.0 — ADA4945-1 with 9.53kΩ Rf will likely oscillate | Either populate feedback caps (recommended) or redesign Rf to stable value without Cf; do not DNP on first prototype |
| HIGH | BB_0/180/90/270/45/225/135/315 | Px_IN+/− | Cross-sheet I/Q differential pairing not confirmed at top level — incorrect pairing destroys I/Q image rejection | Trace every BB_ net to its Px_IN± pin at top level; annotate mapping on nzif.kicad_sch |
| MODERATE | ADA4945-1 (all 4 instances) | Total supply / DISABLE | 10V total supply = rated limit; DISABLE pin disposition not confirmed | Verify supply rails sum to ≤10V under all conditions; confirm DISABLE tied to enable state |
| MODERATE | LT5400 | Resistor pairing / CMRR | Pin pair connectivity must be verified — misconnected pairs ruin CMRR | Verify LT5400 pin-out against KiCad symbol; confirm A1/B1 and A2/B2 pairing correct |
| MODERATE | ADA4945-1 feedback | 9.53kΩ Rf | Thermal noise ≈7.1nV/√Hz dominates amplifier noise floor | Evaluate reducing Rf to 2–4kΩ range; recalculate gain to compensate |

---

### 2.10 nzif.kicad_sch / dsp.kicad_sch / microcontroller.kicad_sch

| Priority | Ref | Net / Pin | Issue | Action |
|----------|-----|-----------|-------|--------|
| HIGH | — | TX reconstruction filter | Absent from tx_mixer sheet — must be located or added to hierarchy | Confirm filter location in hierarchy; if missing, design and add before layout freeze |
| HIGH | HC_201–HC_208 | Rx hold caps | 100nF + N=8 + R=50Ω → BW≈16kHz — reconcile against target receive bandwidth | Determine target BW; adjust hold cap values; correct N annotation to 8 |
| MODERATE | SWIO_0–3 | — | Four SWIO signals leave Microcontroller sheet with no destination or description | Define SWIO destinations; add hierarchical labels or net ties; document purpose |
| MODERATE | Pico module | XIN | XIN hierarchical label — Pico uses internal crystal; label may create dangling net | Add explicit no-connect to XIN if unused; remove hierarchical label |
| MODERATE | Q501 | USB_RESET / SDP | Schematic note acknowledges Q501 USB_RESET circuit is incomplete | Complete Q501 circuit or remove and document alternative USB reset method before fabrication |
| MODERATE | CLK_0/90/135 labels | TX mixer | Duplicate hierarchical label pins at identical coordinates | Resolve duplicates; run ERC and confirm zero errors |
| MODERATE | MCP23017 | GPA7 / GPB7 | Errata: GPA7/GPB7 must be outputs only — confirm schematic and firmware enforce this | Verify no-connect or output-only assignment on GPA7/GPB7 in schematic; add firmware note |
| MINOR | SWIO_VLOGIC | — | Level-shifting reference for SWIO bus undocumented | Add net note defining SWIO_VLOGIC voltage and source |
| MINOR | ADAU1467 | DSP_CLK | Clock frequency not annotated — 12.288 or 24.576 MHz? | Add frequency annotation on DSP_CLK net; cross-reference to clock tree output |
| MINOR | ADAU1979 / ADAU1962A | TDM mode | TDM4 vs TDM8 mode for ADAU1979 not confirmed; two ADAU1962A TDM slot assignments not documented | Annotate TDM mode and slot assignments on schematic; verify against DSP firmware |

---

## 3. Prioritized Action List Before Layout Freeze

Actions are grouped by work stream. Items within each tier should be completed in the order listed, as later items may depend on earlier ones.

### Tier 1 — Block Layout: Must Fix First (week 1)

| # | Action | Owner | Sheets |
|---|--------|-------|--------|
| 1 | **Fix all RF power symbol lib_ids** in rx_mixer and rx_driver_amps. Replace every power:+5V/+6V used for custom rails with correctly named dedicated symbols. Regenerate netlist and run ERC to confirm zero net cross-connections. | RF | rx_mixer, rx_driver_amps |
| 2 | **Correct all LT3045/LT3094 SET resistors**: Add "k" suffix to R903, R907, R908, R909 (49.9Ω → 49.9kΩ); recalculate which resistor value sets each rail; verify LT3094 R903 separately. | Power | power_ldos |
| 3 | **Recalculate all switching regulator feedback resistors**: R1101→4.23MΩ (LT8330 for −5V); R1103→400kΩ (ADP2303 for 4V); populate all six empty Value fields (R1108–R1113). | Power | power_switching_reg |
| 4 | **Fix OSC_CTRL load resistor**: Increase R701 from 1kΩ to ≥10kΩ to meet AD9523-1 20kΩ minimum load on pin 8. | Clock | clock_tree |
| 5 | **Resolve U706 part/value conflict**: Commit to SN74CBT3253 (5V) for Rx switches; update symbol lib_id, value, and BOM entry consistently. | Clock | clock_tree |
| 6 | **Fix ADAU1962A AVDD supply**: Trace "2.5V" label to all ADAU1962A pins; redirect AVDD to a ≥3.0V supply rail. | Precision | dacs |
| 7 | **Fix #PWR0406 in adcs.kicad_sch**: Replace power:+3.3V symbol with a dedicated +3.3V_CONVERTER power symbol to preserve rail isolation. | Precision | adcs |
| 8 | **Rename "DVDOUT" net label to "DVDDOUT"**: Run ERC to confirm CM and DVDDOUT nets are distinct. | Audio | audio_subsystem |

### Tier 2 — Fix Before PCB Stackup Decisions (week 2)

| # | Action | Owner | Sheets |
|---|--------|-------|--------|
| 9 | **Confirm or add PLL1 loop filter cap** on AD9523-1 pin 7 (LF1_EXT_CAP); add per AD9523-1 datasheet if absent. | Clock | clock_tree |
| 10 | **Confirm X701 (CTS 535) EOH and Vc connections**: Drive EOH high to enable; connect Vc to OSC_CTRL net or document alternative. | Clock | clock_tree |
| 11 | **Populate LT3045/LT3094 output capacitors**: Replace all 4.7µF instances with ≥10µF ceramic (X5R/X7R, 0805, adequate voltage derating). | Power | power_ldos |
| 12 | **Correct R910 to 18.0kΩ** for +1.8V_CLOCKTREE; verify all other LT3045 SET resistor values against target output voltages. | Power | power_ldos |
| 13 | **Clarify C913/C917/C922 values** ("04.7u"): confirm intended value (470nF or 4.7µF); correct notation; verify SET pin bypass function. | Power | power_ldos |
| 14 | **Populate ADA4945-1 feedback caps** C343/C322/C319/C320/C340/C341/C344 (180pF): do not DNP on first prototype with 9.53kΩ Rf. | RF | rx_driver_amps |
| 15 | **Confirm or add Tx reconstruction filter** in hierarchy; if absent from tx_mixer.kicad_sch, design and place filter before layout. | RF/System | tx_mixer, nzif |
| 16 | **Correct SN74CBT3125C power rail**: If Rx mixer requires 5V, rename "+3.3V_RX_MIXER" to "+5V_RX_MIXER" and route 5V supply; update all connected power symbols. | RF | rx_mixer |
| 17 | **Add ADP2303 PGOOD pull-ups** (100kΩ) on U1102/U1103/U1104; define power sequencing and connect PGOOD to downstream LDO EN pins. | Power | power_switching_reg, power_ldos |

### Tier 3 — Complete Before Final ERC Sign-Off (week 3)

| # | Action | Owner | Sheets |
|---|--------|-------|--------|
| 18 | **Assign all missing footprints**: U401 (ADA4807-1), X701 (CTS 535), U704/U707 (SN74LVC8T245), all 37+ passives in adcs, majority of passives in dacs, all C12xx/R12xx in audio. | All | all sheets |
| 19 | **Add anti-aliasing caps** (100–470pF C0G) across each AIN+/AIN− pair at ADAU1979 input. | Precision | adcs |
| 20 | **Confirm I/Q differential pairing** at top level: trace every BB_0/180/90/270/45/225/135/315 net to its Px_IN± destination; annotate mapping in nzif.kicad_sch. | RF/System | nzif, rx_driver_amps |
| 21 | **Add U1202 (SSM2211S) bulk bypass cap** (10–47µF) on 5V supply pin 6; add 1µF BYPASS cap C1212. | Audio | audio_subsystem |
| 22 | **Correct C623/C624/C628 typo** ("0.iu" → "100n") in dacs.kicad_sch. | Precision | dacs |
| 23 | **Verify AD9523-1 ZD_IN/ZD_IN_b** (pins 70/71) driven or terminated per datasheet zero-delay configuration. | Clock | clock_tree |
| 24 | **Tie ADA4807-1 DISABLE (pin 5)** to V+ to permanently enable; confirm for all instances. | Precision | adcs |
| 25 | **Connect ADA4625-2 EP (pin 9) to V−** in rx_mixer.kicad_sch. | RF | rx_mixer |
| 26 | **Replace 10µF 0603 caps on +6.5V rail** with 16V-rated 0805 parts in rx_mixer.kicad_sch. | RF | rx_mixer |
| 27 | **Complete Q501 USB_RESET circuit** or document replacement approach; remove incomplete schematic note. | uC | microcontroller |
| 28 | **Resolve SWIO_0–3 destinations**: add hierarchical labels, define SWIO_VLOGIC source voltage, and annotate purpose. | uC | microcontroller, nzif |
| 29 | **Add I2C pull-up resistors** (2kΩ to IOVDD) on SDA/SCL for ADAU1361 if not present in parent sheet; confirm pull-up at exactly one point in hierarchy. | Audio | audio_subsystem |
| 30 | **Add ferrite bead + 10µF cap** between ADP2303 8V output and LT3045 IN pins to restore LDO PSRR at 700kHz. | Power | power_ldos |
| 31 | **Add frequency plan annotation** to clock_tree.kicad_sch: reference frequency, PLL1/PLL2 VCO frequencies, all divider settings, output frequencies. | Clock | clock_tree |
| 32 | **Run full ERC** with zero errors/warnings as gate criterion for layout freeze; resolve all remaining ERC items not covered above. | All | all sheets |

---

**Sign-off criterion:** All Tier 1 actions verified closed, Tier 2 and Tier 3 actions tracked with assigned owners and target dates, before committing to PCB stackup and constraint setup.
