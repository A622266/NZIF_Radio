#!/usr/bin/env python3
"""Generate NZIF Radio comprehensive review report as LibreOffice Writer ODT."""

from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties, ParagraphProperties, TableProperties, \
    TableColumnProperties, TableRowProperties, TableCellProperties
from odf.text import H, P, Span, List, ListItem, LineBreak
from odf.table import Table, TableColumn, TableRow, TableCell
from odf import dc
import datetime

doc = OpenDocumentText()

# ── Styles ──────────────────────────────────────────────────────────────────

def make_style(name, family, parent=None, **kwargs):
    s = Style(name=name, family=family)
    if parent:
        s.setAttribute("parentstylename", parent)
    tp_props = {k: v for k, v in kwargs.items() if k in (
        "fontsize", "fontweight", "fontstyle", "color", "backgroundcolor",
        "textlinenumber",
    )}
    pp_props = {k: v for k, v in kwargs.items() if k in (
        "margintop", "marginbottom", "marginleft", "marginright",
        "breakbefore", "backgroundcolor_p",
        "borderbottom", "bordertop", "borderleft", "borderright",
        "padding",
    )}
    if tp_props:
        tp = TextProperties()
        for k, v in tp_props.items():
            tp.setAttribute(k, v)
        s.addElement(tp)
    return s

# Heading styles
h1 = Style(name="Heading 1", family="paragraph", parentstylename="Heading 1")
h1.addElement(TextProperties(fontsize="16pt", fontweight="bold", color="#1F4E79"))
h1.addElement(ParagraphProperties(margintop="12pt", marginbottom="4pt"))
doc.styles.addElement(h1)

h2 = Style(name="Heading 2", family="paragraph", parentstylename="Heading 2")
h2.addElement(TextProperties(fontsize="13pt", fontweight="bold", color="#2E75B6"))
h2.addElement(ParagraphProperties(margintop="10pt", marginbottom="3pt"))
doc.styles.addElement(h2)

h3 = Style(name="Heading 3", family="paragraph", parentstylename="Heading 3")
h3.addElement(TextProperties(fontsize="11pt", fontweight="bold", color="#404040"))
h3.addElement(ParagraphProperties(margintop="8pt", marginbottom="2pt"))
doc.styles.addElement(h3)

# Body text
body_style = Style(name="Body Text", family="paragraph")
body_style.addElement(TextProperties(fontsize="10pt"))
body_style.addElement(ParagraphProperties(margintop="3pt", marginbottom="3pt"))
doc.styles.addElement(body_style)

# Status styles
critical_style = Style(name="Critical", family="text")
critical_style.addElement(TextProperties(fontweight="bold", color="#C00000"))
doc.styles.addElement(critical_style)

high_style = Style(name="High", family="text")
high_style.addElement(TextProperties(fontweight="bold", color="#FF8C00"))
doc.styles.addElement(high_style)

new_style = Style(name="New", family="text")
new_style.addElement(TextProperties(fontweight="bold", color="#7030A0"))
doc.styles.addElement(new_style)

resolved_style = Style(name="Resolved", family="text")
resolved_style.addElement(TextProperties(color="#375623"))
doc.styles.addElement(resolved_style)

bold_style = Style(name="Bold", family="text")
bold_style.addElement(TextProperties(fontweight="bold"))
doc.styles.addElement(bold_style)

code_style = Style(name="Code", family="text")
code_style.addElement(TextProperties(fontfamily="Courier New", fontsize="9pt"))
doc.styles.addElement(code_style)

# Table styles
table_style = Style(name="TableGrid", family="table")
table_style.addElement(TableProperties(width="17cm", align="margins"))
doc.automaticstyles.addElement(table_style)

col_style_w = Style(name="ColWide", family="table-column")
col_style_w.addElement(TableColumnProperties(columnwidth="3cm"))
doc.automaticstyles.addElement(col_style_w)

col_style_n = Style(name="ColNarrow", family="table-column")
col_style_n.addElement(TableColumnProperties(columnwidth="2cm"))
doc.automaticstyles.addElement(col_style_n)

cell_style = Style(name="TableCell", family="table-cell")
cell_style.addElement(TableCellProperties(
    border="0.5pt solid #AAAAAA",
    padding="2pt"
))
doc.automaticstyles.addElement(cell_style)

cell_header_style = Style(name="TableCellHeader", family="table-cell")
cell_header_style.addElement(TableCellProperties(
    border="0.5pt solid #AAAAAA",
    padding="2pt",
    backgroundcolor="#1F4E79"
))
doc.automaticstyles.addElement(cell_header_style)

cell_critical_style = Style(name="TableCellCritical", family="table-cell")
cell_critical_style.addElement(TableCellProperties(
    border="0.5pt solid #AAAAAA",
    padding="2pt",
    backgroundcolor="#FCE4E4"
))
doc.automaticstyles.addElement(cell_critical_style)

cell_high_style = Style(name="TableCellHigh", family="table-cell")
cell_high_style.addElement(TableCellProperties(
    border="0.5pt solid #AAAAAA",
    padding="2pt",
    backgroundcolor="#FFF2CC"
))
doc.automaticstyles.addElement(cell_high_style)

cell_new_style = Style(name="TableCellNew", family="table-cell")
cell_new_style.addElement(TableCellProperties(
    border="0.5pt solid #AAAAAA",
    padding="2pt",
    backgroundcolor="#EFE6FF"
))
doc.automaticstyles.addElement(cell_new_style)

# Para style for table content
table_para = Style(name="TablePara", family="paragraph")
table_para.addElement(TextProperties(fontsize="9pt"))
table_para.addElement(ParagraphProperties(margintop="1pt", marginbottom="1pt"))
doc.styles.addElement(table_para)

table_header_para = Style(name="TableHeaderPara", family="paragraph")
table_header_para.addElement(TextProperties(fontsize="9pt", fontweight="bold", color="#FFFFFF"))
table_header_para.addElement(ParagraphProperties(margintop="1pt", marginbottom="1pt"))
doc.styles.addElement(table_header_para)

# ── Helper functions ─────────────────────────────────────────────────────────

def add_heading(doc, text, level=1):
    name = f"Heading {level}"
    h = H(outlinelevel=level, stylename=name)
    h.addText(text)
    doc.text.addElement(h)

def add_para(doc, *parts):
    """Add a paragraph. parts can be strings or (text, stylename) tuples."""
    p = P(stylename="Body Text")
    for part in parts:
        if isinstance(part, str):
            p.addText(part)
        elif isinstance(part, tuple):
            text, style = part
            sp = Span(stylename=style)
            sp.addText(text)
            p.addElement(sp)
    doc.text.addElement(p)

def add_table(doc, headers, rows, col_widths=None):
    """Add a table with given headers and rows.
    rows is list of lists of (text, cell_style) tuples or plain strings.
    """
    t = Table(stylename="TableGrid")

    if col_widths:
        for w in col_widths:
            cs = Style(name=f"Col{w}", family="table-column")
            cs.addElement(TableColumnProperties(columnwidth=w))
            doc.automaticstyles.addElement(cs)
            t.addElement(TableColumn(stylename=f"Col{w}"))
    else:
        n = len(headers)
        w = f"{17/n:.1f}cm"
        cs = Style(name=f"ColAuto{n}", family="table-column")
        cs.addElement(TableColumnProperties(columnwidth=w))
        doc.automaticstyles.addElement(cs)
        for _ in headers:
            t.addElement(TableColumn(stylename=f"ColAuto{n}"))

    # Header row
    hr = TableRow()
    for h in headers:
        tc = TableCell(stylename="TableCellHeader", valuetype="string")
        p = P(stylename="TableHeaderPara")
        p.addText(h)
        tc.addElement(p)
        hr.addElement(tc)
    t.addElement(hr)

    # Data rows
    for row in rows:
        tr = TableRow()
        cell_style_for_row = "TableCell"
        # Check if first cell indicates priority
        if row:
            first = row[0] if isinstance(row[0], str) else row[0][0]
            if "CRITICAL" in first.upper():
                cell_style_for_row = "TableCellCritical"
            elif "HIGH" in first.upper():
                cell_style_for_row = "TableCellHigh"
            elif "NEW" in first.upper():
                cell_style_for_row = "TableCellNew"

        for i, cell in enumerate(row):
            if isinstance(cell, tuple):
                text, cstyle = cell
            else:
                text = cell
                cstyle = cell_style_for_row if i == 0 else "TableCell"

            tc = TableCell(stylename=cstyle, valuetype="string")
            # Handle multi-line text
            for j, line in enumerate(text.split("\n")):
                p = P(stylename="TablePara")
                p.addText(line)
                tc.addElement(p)
            tr.addElement(tc)
        t.addElement(tr)

    doc.text.addElement(t)
    # Space after table
    doc.text.addElement(P(stylename="Body Text"))


def add_bullet(doc, text, level=1):
    p = P(stylename="Body Text")
    p.addText("  " * (level - 1) + "• " + text)
    doc.text.addElement(p)

# ── Document content ──────────────────────────────────────────────────────────

# Title
title_style = Style(name="Title", family="paragraph")
title_style.addElement(TextProperties(fontsize="20pt", fontweight="bold", color="#1F4E79"))
title_style.addElement(ParagraphProperties(margintop="0pt", marginbottom="6pt"))
doc.styles.addElement(title_style)

subtitle_style = Style(name="Subtitle", family="paragraph")
subtitle_style.addElement(TextProperties(fontsize="12pt", color="#404040"))
subtitle_style.addElement(ParagraphProperties(margintop="0pt", marginbottom="12pt"))
doc.styles.addElement(subtitle_style)

t = P(stylename="Title")
t.addText("NZIF Radio — System Architecture & Full Schematic Review")
doc.text.addElement(t)

s = P(stylename="Subtitle")
s.addText("Review Date: 2026-06-06 (corrected 2026-06-07) | Scope: All schematic sheets, mixer-to-DSP core | "
          "Status: HOLD — Critical items block layout freeze")
doc.text.addElement(s)

corr = P(stylename="Body Text")
corr_span = Span(stylename="New")
corr_span.addText("Correction note (2026-06-07): ")
corr.addElement(corr_span)
corr.addText(
    "Three Critical findings and related action items from the original 2026-06-06 draft "
    "claimed that custom power-rail symbols (e.g. −3.5V_RX_OPAMPS, +6.5V_RX_OPAMPS, "
    "+3.3V_CONVERTERS) were wired to the wrong global net because their lib_id did not match "
    "their displayed Value. This was verified empirically to be a false positive: kicad-cli "
    "netlist export from the actual schematic files shows each custom-labelled symbol creates "
    "its own correctly isolated net, named after its Value text. In KiCad, a power symbol's "
    "Value field — not its lib_id — determines the net it joins; overriding the Value "
    "on a generic power symbol is the standard, documented way to create custom rail labels. "
    "The three findings (previously Critical 1, 8, 9) and their associated action items "
    "(previously T1-1, T1-8, T1-9) have been removed; remaining items renumbered accordingly. "
    "\n\nA second finding — 'ADA4945-1 feedback caps all DNP → device will oscillate' — was "
    "also revisited at the designer's request. The ADA4945-1 datasheet (held in this repo at "
    "nzif/docs/datasheets/precision/ada4945-1.pdf) describes the standard feedback topology as "
    "a purely resistive four-resistor RF/RG network, shows its own gain-of-1 ADC-driving "
    "application circuit with no feedback capacitor, and never mentions oscillation or "
    "instability risk anywhere in 57 pages. These 180 pF parts are optional output-filter "
    "provisions, by design left DNP unless additional anti-aliasing filtering ahead of the ADC "
    "is wanted — exactly as the designer described. This finding has been downgraded from "
    "HIGH to a documentation note (previously Tier 2 item T2-2, now reworded to recommend "
    "annotating intent rather than populating the parts)."
    "\n\nA third finding — 'R701 = 1kΩ on OSC_CTRL; total load 11kΩ, below the AD9523-1's "
    "20kΩ minimum' — was checked against the actual netlist and both datasheets at the "
    "designer's prompt ('can I just change R701 to be 20k?'). The underlying concern is "
    "real, but the original finding misattributed the '10 kΩ' term in its math to an "
    "'internal' resistance on the AD9523-1 OSC_CTRL pin — no such figure exists anywhere "
    "in that datasheet (only unrelated 40 kΩ pull-ups/pull-downs on CS, RESET, SYNC, and "
    "similar digital pins). kicad-cli netlist export shows R701 is wired in series between "
    "AD9523-1 pin 8 (OSC_CTRL) and U7 (ABLNO-VCXO) pin 1 (Vc, the tuning-voltage input); "
    "the ABLNO datasheet (nzif/docs/datasheets/clocks/ABLNO.pdf) lists 'Control Voltage Port "
    "Impedance: 10 kΩ' for that very pin. So the 10 kΩ is real, and the series-sum math "
    "(R701 + VCXO Vc impedance) is the right model — it is simply the VCXO's input "
    "impedance, not an AD9523-1 internal resistance. At R701 = 1 kΩ the total load is "
    "11 kΩ, short of the AD9523-1's documented 'RLOAD > 20 kΩ' condition (Table 5) for "
    "guaranteed OSC_CTRL output-low levels. The designer's proposed fix — R701 = 20 kΩ — "
    "is correct and is actually better than this report's original T1-4 recommendation of "
    "'≥10 kΩ': 20 kΩ + 10 kΩ = 30 kΩ clears the spec with ~50% margin, whereas 10 kΩ would "
    "land exactly on the 20 kΩ boundary of a strict '>' inequality, with none. The finding's "
    "wording and the T1-4 action item have been corrected accordingly; the 'radio is "
    "inoperable' framing has also been softened to 'restricted VCXO tuning range / marginal "
    "PLL1 lock,' which better matches what an under-spec RLOAD condition actually does to a "
    "buffered control-voltage output (reduced swing/range) rather than an absolute failure."
)
doc.text.addElement(corr)

# ═══════════════════════════════════════════════════════════════════
# SECTION 1: EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════
add_heading(doc, "1. Executive Summary", 1)

add_para(doc,
    "This review covers the complete NZIF Radio schematic at the mixer-to-DSP level. "
    "Six domain expert reviews were conducted in parallel across all twelve schematic sheets. "
    "The design represents a genuinely novel 8-phase near-zero-IF architecture that is publishable "
    "in principle. However, the schematic has ",
    ("8 Critical", "Critical"),
    " issues, ",
    ("25+ High", "High"),
    " issues, and numerous Moderate findings that must be resolved before layout or fabrication. "
    "Hardware does not yet exist; all performance figures are theoretical estimates requiring "
    "bring-up validation."
)

add_para(doc,
    ("QST Verdict: ", "Bold"),
    "The architecture deserves a QST article. The execution needs a complete schematic correction "
    "pass before that becomes possible. The minimum viable path to a working prototype requires "
    "resolution of all Tier 1 critical items listed in Section 6."
)

# Top 8 critical issues table
add_heading(doc, "1.1 Top Critical Issues — Must Fix Before Layout", 2)

crit_headers = ["#", "Sheet", "Issue", "Risk"]
crit_rows = [
    ["CRITICAL 1", "power_ldos", "R903/R907/R908/R909 missing 'k' suffix\n(49.9 Ω not 49.9 kΩ)", "All four LDO rails produce ~5 mV;\ncomplete subsystem failure"],
    ["CRITICAL 2", "power_switching_reg", "LT8330 feedback R1101/R1102 wrong values\n(produces −1.79V not −5V)", "−5V rail absent;\nanalog op-amp supply fails"],
    ["CRITICAL 3", "power_switching_reg", "ADP2303 R1103/R1104 wrong values\n(1.6V not target voltage)", "Target rail at wrong voltage;\ndependent LDOs receive wrong input"],
    ["CRITICAL 4", "clock_tree", "R701 = 1 kΩ in series with VCXO Vc input\n(10 kΩ); total 11 kΩ load on OSC_CTRL,\nbelow AD9523-1's 20 kΩ minimum", "Restricted VCXO tuning range;\nmarginal PLL1 lock acquisition"],
    ["CRITICAL 5", "clock_tree", "U706 symbol=SN74CBT3253 (5V)\nvs. Value=SN74CBTLV3253 (3.6V max)", "Wrong device assembled;\n3.6V-max part destroyed at 5V supply"],
    ["CRITICAL 6", "dacs", "ADAU1962A AVDD driven from Q601 emitter\nfollower: ~2.7V vs. 3.0V minimum", "DAC internal references out of spec;\npossible startup failure"],
    ["CRITICAL 7", "audio_subsystem", "Net label 'DVDOUT' should be 'DVDDOUT';\nADAU1361 internal LDO decoupling disconnected", "Codec internal digital supply unstable;\ncodec non-functional"],
    ["CRITICAL 8", "adcs", "ADAU1979 PLL_FILT cap C406 (5600 pF)\nmarked DNP [NEW]", "ADC internal PLL cannot lock;\nADU1979 completely non-functional"],
]

add_table(doc, crit_headers, crit_rows,
          col_widths=["2.0cm", "2.5cm", "7.5cm", "5.0cm"])

# ═══════════════════════════════════════════════════════════════════
# SECTION 2: SYSTEM ARCHITECTURE ASSESSMENT
# ═══════════════════════════════════════════════════════════════════
add_heading(doc, "2. System Architecture Assessment", 1)

add_heading(doc, "2.1 Architecture Strengths", 2)

strengths = [
    ("8-Phase Polyphase Mixer — Genuine Novelty",
     "The 8-phase commutating topology with SN74CBT3125C bus switches provides theoretical "
     ">60 dB rejection of the 3rd LO harmonic, >50 dB of the 5th, and >45 dB of the 7th. "
     "No published amateur construction project has implemented this. The mathematics (8-point "
     "DFT phasor argument) is correct and is validated by the rxmixer.md simulation showing "
     "correct 45° phase spacing and matched amplitudes. This directly surpasses Tayloe's "
     "4-phase detector (QEX, May 2001) and is the primary novelty claim for a QST article."),
    ("AD9523-1 Dual-Output Clock Architecture",
     "Generating both the variable RF LO and the fixed audio MCLK from a single VCO, with the "
     "reference-path divider completely decoupled from PLL2 tuning, is architecturally elegant. "
     "Retuning the LO does not disturb the I2S clock domain — a non-trivial design insight that "
     "most amateur SDR designs get wrong. The AD9523-1's −226 dBc/Hz FOM is appropriate for "
     "a receiver targeting superheterodyne-class phase noise performance."),
    ("Ring Counter Phase Generation",
     "The SN74AUC16374 ring counter producing eight non-overlapping phase pulses from a "
     "circulating single-bit shift register is original and elegant. The 4:1 mux initialisation "
     "sequence (clear → seed → run) reproducibly places exactly one '1' in the loop, solving the "
     "undefined power-up state problem without external reset logic. The 2.5V supply choice "
     "allows 237.6 MHz operation for 10m (8-phase) within the 250 MHz typical device rating."),
    ("Fully Differential Signal Flow",
     "The receive chain is fully differential from the balun secondary through "
     "SN74CBT3125C switches → ADA4625-2 buffers → ADA4945-1 FDAs → ADAU1979 ADC. "
     "Maintaining differential mode throughout suppresses even-order nonlinearities and "
     "rejects common-mode RF interference. The LT5400 matched quad resistors for ADA4945-1 "
     "Rg positions (0.01% ratio matching, 0.5 ppm/°C tracking) are the right call for I/Q "
     "amplitude balance."),
    ("Near-Zero-IF + NCO Strategy",
     "The ADAU1467 digital NCO (±96 kHz) offsets the receive center from DC, avoiding LO "
     "leakage and 1/f noise without a switched IF filter bank. Combined with 100 kHz LO "
     "steps from the AD9523-1, this provides continuous HF coverage. The Weaver two-stage "
     "demodulation (first stage: analog 8-phase mixer; second stage: digital NCO in ADAU1467) "
     "is a legitimate and clean implementation."),
    ("LT3045/LT3094 Power Architecture",
     "The use of ultra-low-noise LDOs (2 µVrms) post-regulating from ADP2302/ADP2303 "
     "switchers, with domain-isolated rails for the clock tree, mixers, and audio converters, "
     "reflects serious attention to the ADC noise floor. The LT3045's 76 dB PSRR at 1 MHz "
     "directly addresses 700 kHz switcher ripple. This is a publishable design decision that "
     "most commercial SDR kits do not implement."),
    ("I/Q Calibration Architecture",
     "The directional coupler calibration tap + HMC1118 switch injecting a known spectrally "
     "clean signal into the receive path for runtime I/Q calibration goes beyond any published "
     "amateur receiver design. If implemented correctly, this allows image rejection to be "
     "maintained across temperature and band changes without manual trimming."),
    ("ADAU1467 SigmaDSP Integration",
     "The 294 MHz dual-core ADAU1467 running SigmaStudio graphical blocks (NCO, Weaver second "
     "stage, FIR/IIR filters, AGC, I/Q correction matrix) provides more DSP headroom than a "
     "comparably priced FPGA for audio-rate processing, without requiring custom firmware. "
     "I2C parameter RAM access from the Pico enables runtime calibration coefficient updates."),
]

for title, body in strengths:
    add_para(doc, (title + ": ", "Bold"), body)

add_heading(doc, "2.2 Architecture Concerns", 2)

concerns = [
    ("TX Reconstruction Filter Absent [CRITICAL]",
     "The tx_mixer.kicad_sch sheet title promises '16 Phase Tx Harmonic Mixer and "
     "Reconstruction Filter' but contains no filter components. DAC reconstruction images "
     "at LO ± 192 kHz and harmonics feed directly to the PA interface. The ZWAS LPF on the "
     "RF front-end board suppresses PA harmonics but not pre-PA mixer images. A fully "
     "differential LC filter at TX_RF+/TX_RF- is required before FCC Part 97 compliance "
     "can be claimed."),
    ("Hold Capacitor Values Produce ~4 kHz Baseband Bandwidth [NEW HIGH]",
     "The rx_mixer annotation uses N=1 in the bandwidth equation; the correct value for an "
     "8-phase topology is N=8. With 100 nF hold caps and Reff ≈ 50 Ω source / N=8: "
     "BW ≈ 1/(2π × 8 × 50 × 100 nF) ≈ 4 kHz. This is far below the ±96 kHz NCO range. "
     "For ±200 kHz bandwidth target: C_hold ≈ 2 nF. The current 100 nF caps limit the design "
     "to CW-only operation, inconsistent with the stated SSB/AM/digital mode goals."),
    ("VCXO vs. TCXO Conflict [NEW HIGH]",
     "CLAUDE.md and the architecture description state CTS_535_TCXO as the frequency reference, "
     "but clock_tree.kicad_sch instantiates an ABLNO-V-VCXO. These are functionally different "
     "devices. The AD9523-1 is designed for a VCXO reference on PLL1 (OSC_CTRL drives Vc), "
     "which makes the ABLNO-VCXO the architecturally correct choice — but the documentation "
     "and schematic disagree. This must be resolved explicitly."),
    ("6m 4-Phase Mode Spurious Response",
     "In 4-phase mode (6m), the 5th harmonic (f_LO/5 ≈ 10–10.8 MHz = 30m band) passes "
     "through with the same response vector as the fundamental. HP-2 (9 MHz cutoff) provides "
     "only modest attenuation at 10 MHz. Strong 30m signals will create interference on 6m. "
     "This limitation is inherent to 4-phase operation and should be quantified and disclosed "
     "in any QST article."),
    ("Power Sequencing Undefined",
     "No PGOOD connections link switching regulator outputs to downstream LDO enable pins. "
     "The ADAU1467 requires DVDD and IOVDD within 0.3 V of each other during power-up to "
     "prevent latch-up. All rails currently rise simultaneously with no defined order. "
     "ADP2303 PGOOD pins have no pull-up resistors."),
]

for title, body in concerns:
    add_para(doc, (title + ": ", "Bold"), body)

add_heading(doc, "2.3 QST Readiness Assessment", 2)

add_para(doc,
    ("Strengths for publication: ", "Bold"),
    "The 8-phase polyphase mixer topology is a publishable concept that advances the state "
    "of amateur radio construction. The dual-path clock architecture, ring counter phase "
    "generation, and I/Q calibration system are all novel and technically rigorous. "
    "The LTspice simulation validating the 45° phase spacing is a publication-ready figure. "
    "A QST reviewer familiar with Tayloe's detector would immediately recognise this as "
    "a significant advancement."
)

add_para(doc,
    ("Blockers to publication: ", "Bold"),
    "(1) 8 critical schematic errors that would prevent a built board from functioning. "
    "(2) No hardware exists — all performance figures are theoretical estimates. QST requires "
    "bench-measured data for all performance claims. "
    "(3) TX reconstruction filter absent — transmitter cannot claim Part 97 compliance. "
    "(4) Hold capacitor values inconsistent with stated ±96 kHz operating bandwidth."
)

add_para(doc,
    ("Recommended path to QST submission: ", "Bold"),
    "Fix all Tier 1 critical items → build first prototype → measure MDS, IIP3, harmonic "
    "rejection (3rd/5th/7th), image rejection, and TX spectrum → submit with measured data "
    "and corrected ERC-clean schematic."
)

# ═══════════════════════════════════════════════════════════════════
# SECTION 3: NEW FINDINGS (from this review cycle)
# ═══════════════════════════════════════════════════════════════════
add_heading(doc, "3. New Findings — This Review Cycle", 1)

add_para(doc, "The following issues were not in the prior schematic_review_report.md "
         "and were identified by this review cycle:")

new_headers = ["Priority", "Sheet", "Ref/Net", "Issue", "Action"]
new_rows = [
    ["CRITICAL [NEW]", "adcs", "C406\n(PLL_FILT)",
     "5600 pF PLL_FILT cap is marked DNP.\nADAU1979 internal PLL cannot lock\nwithout this capacitor → ADC non-functional",
     "Populate C406; do not DNP on prototype"],
    ["CRITICAL [NEW]", "dacs", "Net '2.5'\n(no V suffix)",
     "Label '2.5' (missing 'V') at line 6617 creates\na net isolated from all '2.5V' nets.\nFloating node risk at DAC reference",
     "Rename to '2.5V'; verify no other\ncase/suffix mismatches in DAC sheet"],
    ["HIGH [NEW]", "clock_tree", "X701 vs\nABLNO-VCXO",
     "Architecture docs say CTS_535_TCXO;\nschematic instantiates ABLNO-V-VCXO.\nFundamentally different parts (TCXO vs VCXO)",
     "Commit to ABLNO-VCXO (architecturally\ncorrect for AD9523-1 PLL1); update\nCLAUDE.md; remove unused CTS_535 symbol"],
    ["HIGH [NEW]", "rx_mixer", "HC_201–208\nhold caps",
     "Bandwidth annotation uses N=1 but topology\nhas N=8 phases. Correct BW with 100 nF:\n~4 kHz, not 96 kHz. Inconsistent with\n±96 kHz NCO design goal",
     "Recalculate for N=8: C_hold ≈ 2 nF\nfor 200 kHz target BW; update annotation\nand fitted values"],
    ["HIGH [NEW]", "adcs", "U401 VREF\nbuffer",
     "R410 (3kΩ) loads ADAU1979 VREF pin\n(unbuffered bandgap output) with 0.83 mA\nbefore the ADA4807-1 buffer — exceeds\nrecommended loading",
     "Move R410 to output of ADA4807-1\nbuffer, not input; ensure VREF pin\nsees only buffer input impedance"],
    ["HIGH [NEW]", "adcs", "C401, C403\nAVDD caps",
     "10 µF AVDD bypass caps assigned to\n0402 footprint. DC bias derating at 3.3V\nreduces effective C to 3–5 µF (marginal).\nNo 10 µF ceramic exists in 1005 metric",
     "Change footprint to 0805; use 10 µF\nX5R/X7R 0805 rated ≥6.3V"],
    ["HIGH [NEW]", "dacs", "Q601 / AVDD",
     "FZT951TA emitter follower produces\n~3.3V − 0.6V = 2.7V AVDD at room temp.\nFalls further with temperature.\nADAU1962A AVDD minimum is 3.0V",
     "Replace Q601 with LT3045 LDO;\nset output to 3.3V with correct\nSET resistor value"],
    ["HIGH [NEW]", "dsp", "SELFBOOT /\nU502 EEPROM",
     "SELFBOOT pin state unconfirmed.\nU502 (25AA1024 SPI EEPROM) footprint\nis empty — absent from layout.\nSelf-boot path cannot function without EEPROM",
     "Assign footprint to U502; confirm\nSELFBOOT pulled high (IOVDD);\ndocument boot mode in schematic note"],
    ["HIGH [NEW]", "tx_mixer", "Tx DAC\ndifferential\npolarity",
     "DAC_N+/DAC_N− assignment to switch\nport A vs. B not verified. Any polarity\nreversal injects image/sideband rather\nthan desired signal",
     "Trace each DAC± to switch port;\nannotate polarity on schematic"],
    ["MODERATE [NEW]", "dsp", "MiSO_M\nlabel",
     "Label 'MiSO_M' (mixed case) creates\na separate net from 'MISO_M' (all caps).\nKiCad net names are case-sensitive.\nADAU1467 SPI EEPROM read path broken",
     "Change 'MiSO_M' to 'MISO_M'\nthroughout; verify with ERC"],
    ["MODERATE [NEW]", "audio_subsystem", "C1215/C1216\nfootprint",
     "220 µF polarized electrolytic caps\nassigned to 0402 footprint (1.0×0.5 mm).\nNo 220 µF ceramic exists in 0402.\nAssembly will fail",
     "Change to through-hole radial or\nlarge-body SMD electrolytic footprint;\nconsider 470 µF for fc ≈ 11 Hz"],
    ["MODERATE [NEW]", "tx_mixer\nclock_tree", "Clock net\nnaming\ninconsistency",
     "clock_tree exports 'tx_phase_N';\ntx_mixer imports 'CLK_N';\nrx_mixer imports 'phase_N'.\nThree naming conventions for same signals",
     "Standardise on one naming scheme\nacross all sheets; verify all\nhierarchical connections are intact"],
    ["MODERATE [NEW]", "rx_driver_amps", "ADA4945-1\nVOCM pin",
     "VOCM pin not explicitly driven.\nDefault VOCM = midpoint of supply rails\n(+6.5V/−3.5V) = +1.5V.\nADAU1979 VOCM = AVDD/2 = 1.65V.\nMarginal match, supply-dependent",
     "Drive VOCM from resistor divider\nfrom ADAU1979 AVDD for stable\ncommon-mode matching"],
    ["MODERATE [NEW]", "power_switching_reg", "ADP2303 bulk\ncaps",
     "Output bulk caps '47u 6.3V' —\nif used on 8V ADP2303 output\n(R1112/R1113), 6.3V rating exceeded",
     "Verify which caps are on 8V output;\nreplace with 47µF 16V-rated parts"],
    ["MODERATE [NEW]", "power_ldos", "C913/C917/C922\n'04.7u' notation",
     "'04.7u' value notation on SET bypass\ncaps is ambiguous; BOM tools may parse\nas 4.7 µF or 0.47 µF — 10× difference\naffects LDO PSRR",
     "Change notation to '470n' (correct\nfor SET pin bypass); or '4.7u' if\nbulk bypass is intended; confirm intent"],
    ["MODERATE [NEW]", "dsp", "ADAU1467\nper-pin\ndecoupling",
     "ADAU1467 has 17 separate power pins\nacross 4 supply domains. Schematic\nmust verify one 100 nF cap per physical\npin at 294 MHz core clock frequency",
     "Verify one decoupling cap per power\npin on U501; ensure caps placed\nadjacent to each pin in layout"],
]

add_table(doc, new_headers, new_rows,
          col_widths=["2.5cm", "2.5cm", "2.5cm", "5.5cm", "4.0cm"])

# ═══════════════════════════════════════════════════════════════════
# SECTION 4: STATUS OF PRIOR REVIEW ISSUES
# ═══════════════════════════════════════════════════════════════════
add_heading(doc, "4. Status of Prior Review Issues", 1)

add_para(doc, "All items from the April 2026 review report (schematic_review_report.md) "
         "were re-evaluated against the current schematic. The following table summarises status:")

status_headers = ["Issue from Prior Report", "Sheet", "Prior Priority", "Current Status"]
status_rows = [
    ["Wrong lib_ids on custom power symbols\n(−3.5V_RX_OPAMPS shorts to +5V/+6V global net)",
     "rx_mixer\nrx_driver_amps", "CRITICAL", "RETRACTED — false positive. kicad-cli\nnetlist export confirms each custom\nValue (−3.5V_RX_OPAMPS, +6.5V_RX_OPAMPS,\n+3.3V_DSP_UC, etc.) creates its own\nisolated net. KiCad uses a power symbol's\nValue text — not its lib_id — as the net\nname. Rails are correctly isolated"],
    ["R903/907/908/909 missing 'k' suffix\n(49.9 Ω not 49.9 kΩ)", "power_ldos", "CRITICAL",
     "PARTIALLY FIXED — three other SET\nresistors corrected; four listed\ninstances still at bare '49.9'"],
    ["LT8330 R1101/R1102 wrong feedback\n(produces −1.79V not −5V)", "power_switching_reg", "CRITICAL",
     "OPEN — R1101=1M, R1102=806k\nconfirmed in schematic. Need\nR1101 = 4.22 MΩ for −5V"],
    ["ADP2303 R1103/R1104 wrong values\n(1.6V not target)", "power_switching_reg", "CRITICAL",
     "OPEN — both still 100kΩ → 1.6V.\nR1110/R1111, R1112/R1113 now\npopulated correctly (6V, 8V rails)"],
    ["R701 = 1kΩ on OSC_CTRL below 20kΩ min",
     "clock_tree", "CRITICAL", "OPEN — R701 still reads '1k'\nin schematic"],
    ["U706 SN74CBT3253/SN74CBTLV3253\npart-value mismatch", "clock_tree", "CRITICAL",
     "OPEN — symbol=SN74CBT3253,\nvalue=SN74CBTLV3253 mismatch\nstill present"],
    ["ADAU1962A AVDD 2.5V label\n(min 3.0V)", "dacs", "CRITICAL",
     "OPEN — four '2.5V' labels in DAC\nsheet; Q601 emitter follower\nproduces ~2.7V (below 3.0V min)"],
    ["#PWR0406 power:+3.3V for\n+3.3V_CONVERTER rail", "adcs", "CRITICAL",
     "RETRACTED — false positive. lib_id\n'power:+3.3V' (matching voltage) with\nValue overridden to '+3.3V_CONVERTERS'\nis the correct, standard way to create\nan isolated rail in KiCad. Netlist\nconfirms a separate '+3.3V_CONVERTERS'\nnet — no merge with digital +3.3V"],
    ["'DVDOUT' label should be 'DVDDOUT'\n(ADAU1361 LDO decoupling disconnected)",
     "audio_subsystem", "CRITICAL", "OPEN — 'DVDOUT' still present at\ntwo locations in schematic"],
    ["LT3045/LT3094 output caps 4.7µF\n(minimum 10µF for stability)", "power_ldos", "CRITICAL",
     "OPEN — all LT3045 outputs still\nat 4.7µF; multiple confirmed instances.\nLDOs will oscillate"],
    ["TX reconstruction filter absent\ndespite sheet title promising it", "tx_mixer", "HIGH",
     "OPEN — no filter components\npresent on tx_mixer sheet"],
    ["ADA4945-1 feedback caps all DNP\n(oscillation risk at 9.53kΩ Rf)", "rx_driver_amps", "HIGH",
     "DOWNGRADED — re-checked against\nADA4945-1 datasheet (in repo). Standard\nfeedback topology is purely resistive\n(4-resistor RF/RG network); datasheet's own\nADC-driving example uses G=1 with no Cf\nand never mentions oscillation risk. These\n180pF parts are optional output-filter\nprovisions (designer-confirmed), correctly\nDNP unless added filtering is desired"],
    ["R910 = 16.5kΩ produces 1.65V\nnot 1.8V on clocktree rail", "power_ldos", "HIGH",
     "OPEN — R910 still at 16.5kΩ;\nneed 18.0kΩ for 1.8V"],
    ["ADA4807-1 DISABLE pin unconfirmed",
     "adcs", "HIGH", "OPEN — pin 5 has no connection"],
    ["No differential shunt caps on\nAIN+/AIN− pairs", "adcs", "HIGH",
     "OPEN — C405 (390pF) and C406\n(5600pF) both DNP; no populated\nanti-aliasing cap on any AIN pair"],
    ["PLL1 LF1_EXT_CAP not confirmed\npresent", "clock_tree", "HIGH",
     "OPEN — no cap confirmed on\nAD9523-1 pin 7 net"],
    ["CTS 535 EOH and Vc not confirmed",
     "clock_tree", "HIGH", "OPEN — EOH pin disposition\nunconfirmed; VCXO vs TCXO\nconflict newly identified"],
    ["AD9523-1 ZD_IN/ZD_IN_b not\nterminated", "clock_tree", "HIGH",
     "OPEN — pins 70/71 disposition\nnot confirmed"],
    ["I2S/TDM pull-up resistors not\nconfirmed for ADAU1361", "audio_subsystem", "HIGH",
     "OPEN — no pull-ups found\nin audio_subsystem sheet"],
    ["SSM2211S bulk bypass cap missing",
     "audio_subsystem", "HIGH", "OPEN — only 100nF C1214 on\n5V supply; need 10–47µF bulk"],
    ["C623/C624/C628 value '0.iu' typo\n(unparseable by BOM tools)", "dacs", "CRITICAL",
     "OPEN — confirmed still '0.iu'\nat three locations"],
    ["ADP2303 PGOOD pins: no pull-ups",
     "power_switching_reg", "HIGH", "OPEN — no pull-up resistors;\nno sequencing defined"],
    ["ADP2303 inductors 3.3µH\n(datasheet recommends 4.7µH)", "power_switching_reg", "HIGH",
     "OPEN — three instances still\nat '3.3u 3A'"],
    ["Footprints missing on majority\nof passive components", "all sheets", "HIGH",
     "PARTIALLY ADDRESSED — some\nfootprints assigned; many still\nmissing across all sheets"],
]

add_table(doc, status_headers, status_rows,
          col_widths=["5.5cm", "2.5cm", "2.0cm", "7.0cm"])

# ═══════════════════════════════════════════════════════════════════
# SECTION 5: PER-SHEET FINDINGS SUMMARY
# ═══════════════════════════════════════════════════════════════════
add_heading(doc, "5. Per-Sheet Findings Summary", 1)

# Sheet by sheet
sheets = [
    ("5.1 rx_mixer.kicad_sch — 8-Phase Receive Mixer", [
        ("HIGH (NEW)", "Hold cap bandwidth: 100 nF with N=8 phases gives BW ≈ 4 kHz, not 96 kHz as annotated (annotation uses N=1). Recalculate for N=8: C_hold ≈ 2 nF for ±200 kHz target."),
        ("MODERATE", "ADA4625-2 exposed pad (EP, pin 9) not confirmed connected to V−. Required by datasheet; floating EP degrades thermal performance and substrate coupling between phase channels."),
        ("MODERATE", "10µF caps on +6.5V rail in 0603 package: 0603 ceramics typically rated ≤6.3V. Replace with 16V-rated 0805 parts."),
    ]),
    ("5.2 rx_driver_amps.kicad_sch — Differential Driver Amplifiers", [
        ("LOW (REVISED)", "ADA4945-1 feedback caps C343/C322/C319/C320/C340/C341/C344 (180pF) marked DNP. Re-checked against datasheet: standard feedback topology is purely resistive (RF/RG), the datasheet's own G=1 ADC-driving example uses no Cf, and oscillation is not mentioned anywhere in the part's documentation. These are optional output-filter provisions — correctly DNP as designed; populate only if additional anti-aliasing filtering ahead of the ADC is wanted."),
        ("HIGH (NEW)", "Rf = 9.53kΩ contributes 12.6 nV/√Hz thermal noise at virtual ground node, dominating ADA4945-1's own 1.7 nV/√Hz. Consider reducing to 2–4kΩ range."),
        ("MODERATE (NEW)", "ADA4945-1 VOCM pin not explicitly driven. Default VOCM = +1.5V (supply midpoint). ADAU1979 requires VOCM = AVDD/2 = 1.65V. Marginal match, supply-voltage dependent."),
        ("MODERATE", "BB_0/BB_180 to P0_IN+/P0_IN− pairing not confirmed at top level. Incorrect I/Q phase assignment destroys image rejection."),
    ]),
    ("5.3 clock_tree.kicad_sch — Phase Clock Generation", [
        ("CRITICAL (REVISED)", "R701 = 1kΩ wired in series between AD9523-1 pin 8 (OSC_CTRL, confirmed via netlist) and U7/ABLNO-VCXO pin 1 (Vc). ABLNO datasheet specifies 'Control Voltage Port Impedance' = 10kΩ at that pin (the source of the '10kΩ' figure — not an AD9523-1 internal resistance as originally stated; no such figure exists in that datasheet). Total series load = 1kΩ + 10kΩ = 11kΩ, below the AD9523-1's documented 'RLOAD > 20kΩ' condition (Table 5) for guaranteed OSC_CTRL output-low levels. Likely consequence: restricted VCXO tuning range / marginal PLL1 lock acquisition, not an absolute 'will not lock.' Designer-proposed fix (R701 → 20kΩ, giving 30kΩ total with ~50% margin) is correct and adopted — see T1-4."),
        ("CRITICAL", "U706: symbol=SN74CBT3253 (5V), value=SN74CBTLV3253 (3.6V max). Wrong device assembled; 3.6V-max part destroyed at 5V supply, or 5V part produces wrong specifications."),
        ("HIGH (NEW)", "VCXO vs. TCXO conflict: CLAUDE.md says CTS_535_TCXO; schematic instantiates ABLNO-V-VCXO. Commit to ABLNO-VCXO (correct for AD9523-1 PLL1); update documentation."),
        ("HIGH", "PLL1 external loop filter cap (AD9523-1 pin 7, LF1_EXT_CAP) not confirmed present. PLL1 cannot lock without it."),
        ("HIGH", "CTS 535 (or ABLNO-VCXO) EOH enable pin and Vc control not confirmed connected."),
        ("HIGH", "AD9523-1 ZD_IN/ZD_IN_b (pins 70/71) not driven or terminated for zero-delay-bypass mode."),
        ("MODERATE", "Frequency plan annotation absent from schematic. No divider settings, VCO frequencies, or output frequencies documented."),
        ("MODERATE", "OSC_IN_b (AD9523-1 pin 10) AC-ground capacitor (100nF to GND) not confirmed for single-ended input mode."),
    ]),
    ("5.4 adcs.kicad_sch — ADAU1979 ADC", [
        ("CRITICAL (NEW)", "C406 (5600pF, PLL_FILT) marked DNP. ADAU1979 internal PLL cannot lock without this external capacitor. ADC is completely non-functional."),
        ("HIGH (NEW)", "R410 (3kΩ) loads ADAU1979 VREF pin (unbuffered bandgap output) with 0.83 mA before ADA4807-1 buffer. Correct topology: buffer first, then divide. VREF voltage may be pulled low."),
        ("HIGH", "No differential shunt capacitors (100–470pF C0G) across any AIN+/AIN− pair. 10Ω series resistors alone provide no anti-aliasing or RF rejection."),
        ("HIGH", "ADA4807-1 DISABLE (pin 5) has no connection. Active-low; floating may disable the amplifier."),
        ("HIGH (NEW)", "10µF AVDD caps C401/C403 assigned to 0402 footprint. DC bias derating reduces effective C to 3–5µF at 3.3V — marginal for ADAU1979. Use 0805 instead."),
        ("MODERATE", "SA_MODE, ADDR0, ADDR1 pin levels not annotated. I2C address and serial interface mode undefined."),
    ]),
    ("5.5 dacs.kicad_sch — ADAU1962A DAC", [
        ("CRITICAL", "ADAU1962A AVDD below 3.0V minimum. Q601 (FZT951TA) emitter follower produces ~3.3V − 0.6V = 2.7V at room temp; falls further with temperature. DAC out of spec."),
        ("CRITICAL", "C623/C624/C628 have value '0.iu' — BOM tools cannot parse; capacitors will be omitted from build. Intended value: 100nF."),
        ("CRITICAL (NEW)", "Net '2.5' (no V suffix) at line 6617 creates isolated net separate from '2.5V' nets. Floating node risk at DAC reference circuitry."),
        ("HIGH (NEW)", "Q601 emitter-follower AVDD has no feedback regulation. Supply rejection is poor; DAC THD+N will be degraded from datasheet specification. Replace with LT3045 for correct AVDD."),
        ("MODERATE", "R614 (IBIAS, 3.32kΩ) has no tolerance annotation. Must be 1% tolerance per datasheet. 5% substitution shifts DAC full-scale by ±5%."),
        ("MODERATE (NEW)", "MCLK frequency not annotated. ADAU1962A requires MCLK ratio annotation (256× at 48kHz or 128× at 192kHz) to verify SigmaStudio configuration."),
    ]),
    ("5.6 dsp.kicad_sch — ADAU1467 SigmaDSP", [
        ("HIGH (NEW)", "SELFBOOT pin state not documented. 25AA1024 SPI EEPROM (U502) has empty footprint field — absent from layout. Self-boot path non-functional without EEPROM on PCB."),
        ("MODERATE (NEW)", "Label 'MiSO_M' (mixed case) creates separate net from 'MISO_M'. KiCad net names are case-sensitive. SPI EEPROM read path broken at this label."),
        ("MODERATE (NEW)", "17 ADAU1467 power pins across 4 supply domains require individual 100nF decoupling caps. Shared decoupling inadequate at 294 MHz core clock."),
        ("MODERATE (NEW)", "ADAU1467 I2C address configuration not documented. SELFBOOT/ADDR pin states must be annotated; address collisions with ADAU1979, ADAU1962A, ADAU1361 must be ruled out."),
        ("MODERATE (NEW)", "SigmaStudio project file not referenced from schematic. TDM slot assignments, MCLK ratio, NCO configuration cannot be verified by inspection."),
        ("MINOR", "DSP_CLK (MCLK) frequency not annotated on schematic. Critical for SigmaStudio PLL configuration."),
    ]),
    ("5.7 power_ldos.kicad_sch — LT3045/LT3094 LDOs", [
        ("CRITICAL", "R903/R907/R908/R909: value '49.9' without 'k' suffix = 49.9Ω → V_OUT ≈ 5mV on four LDO rails. Three other instances correctly read '49.9k'. Fix: add 'k' suffix to all four."),
        ("CRITICAL", "All LT3045 output caps at 4.7µF (confirmed multiple instances). LT3045 datasheet requires minimum 10µF ceramic for stability. All LDOs will oscillate."),
        ("HIGH", "R910 = 16.5kΩ → +1.8V_CLOCKTREE = 1.65V. Need 18.0kΩ for 1.8V output."),
        ("HIGH", "LT3094 output cap C931 = 4.7µF (minimum 10µF required for stability)."),
        ("MODERATE (NEW)", "'04.7u' notation on two SET bypass caps is ambiguous. Correct to '470n' (intended value for LT3045 SET pin bypass per datasheet)."),
        ("MODERATE", "No ferrite bead between ADP2303 8V output and LT3045 input pins. 700kHz switcher ripple degrades LDO PSRR advantage."),
    ]),
    ("5.8 power_switching_reg.kicad_sch — Switching Regulators", [
        ("CRITICAL", "LT8330 R1101 = 1MΩ produces −1.79V not −5V. Required: R1101 = 4.22MΩ (E96). Formula: R1 = R2 × (|Vout|/0.80V − 1) = 806k × 5.25 = 4.23MΩ."),
        ("CRITICAL", "ADP2303 R1103/R1104 = 100k/100k produces 1.6V. Formula: Vout = 0.800 × (1 + RTOP/RBOT). For 4V: RTOP = 4 × RBOT = 400kΩ."),
        ("HIGH (NEW)", "ADP2303 output bulk caps '47u 6.3V' — if on 8V output rail (R1112/R1113 instance), 6.3V rating is violated. Replace with 47µF 16V-rated on 8V rail."),
        ("HIGH", "PGOOD pins on U1102/U1103/U1104 (ADP2303): no pull-up resistors and no no-connect markers. Power sequencing undefined."),
        ("HIGH", "ADP2303 inductors: 3.3µH fitted vs. 4.7µH datasheet recommendation. Higher ripple current, saturation risk at full load."),
    ]),
    ("5.9 audio_subsystem.kicad_sch — ADAU1361 Codec", [
        ("CRITICAL", "Net label 'DVDOUT' should be 'DVDDOUT'. ADAU1361 DVDDOUT (pin 24, internal 1.8V LDO output) drives the 'DVDDOUT' net; the 10µF decoupling caps are stranded on floating 'DVDOUT' net. Codec non-functional."),
        ("CRITICAL (NEW)", "C1215/C1216 (220µF polarized) assigned to 0402 footprint. No 220µF ceramic in 0402 exists. Assembly will fail. Change to appropriate electrolytic/tantalum footprint."),
        ("HIGH", "SSM2211S (U1202): only 100nF C1214 on V+ supply. Peak current ≈400mA requires 10–47µF bulk bypass."),
        ("MODERATE", "RINP/RINN/RAUX (ADAU1361 pins 12/13/14) marked no_connect. Datasheet requires connection to CM. Floating analog inputs introduce noise into sigma-delta modulator."),
        ("MODERATE", "JACKDET/MICIN (pin 4) marked no_connect. Floating digital input — add pull to defined level."),
        ("MODERATE", "No RF EMI filter caps on any audio input. In RF radio environment, audio traces act as antennas. Add 100pF C0G to GND on each input."),
        ("MODERATE (NEW)", "AMP_SHUTDOWN default pull-down not confirmed at signal source. SSM2211S should default to shutdown (safe) at power-up."),
    ]),
    ("5.10 tx_mixer.kicad_sch — Transmit Mixer", [
        ("HIGH", "No reconstruction filter present despite sheet title 'Reconstruction Filter'. DAC images at LO ± 192kHz feed PA interface directly. Part 97 compliance cannot be claimed."),
        ("HIGH (NEW)", "DAC_N+/DAC_N− differential polarity per switch arm not verified. Polarity reversal injects image instead of desired signal."),
        ("MODERATE", "SN74CBT3125CPW symbol with Value 'SN74CBTLV3125' — BOM will pull wrong device (wrong voltage rating)."),
        ("MODERATE", "Duplicate hierarchical labels for all 8 CLK phases — benign if at different coordinates but creates ERC ambiguity; run ERC to confirm clean."),
        ("MODERATE (NEW)", "Clock signal naming 'CLK_N' inconsistent with 'tx_phase_N' from clock_tree and 'phase_N' from rx_mixer. Verify all hierarchical connections are intact."),
    ]),
    ("5.11 microcontroller.kicad_sch — Raspberry Pi Pico", [
        ("MODERATE", "Q501 USB_RESET circuit incomplete (acknowledged in schematic note). Complete or document replacement approach before fabrication."),
        ("MODERATE", "SWIO_0–3 hierarchical labels have no defined destination or purpose annotation. Add hierarchical labels and document SWIO_VLOGIC source voltage."),
        ("MODERATE", "MCP23017 GPA7/GPB7 must be outputs only (silicon errata). Confirm schematic and planned firmware enforce this."),
        ("MINOR", "ADAU1467 I2C/SPI address configuration not cross-referenced from this sheet. Verify address conflicts with other I2C devices are ruled out."),
    ]),
]

for sheet_title, findings in sheets:
    add_heading(doc, sheet_title, 2)
    sh_headers = ["Priority", "Finding"]
    sh_rows = []
    for priority, finding in findings:
        sh_rows.append([priority, finding])
    add_table(doc, sh_headers, sh_rows, col_widths=["3.0cm", "14.0cm"])

# ═══════════════════════════════════════════════════════════════════
# SECTION 6: PRIORITIZED ACTION PLAN
# ═══════════════════════════════════════════════════════════════════
add_heading(doc, "6. Prioritized Action Plan", 1)

add_heading(doc, "6.1 Tier 1 — Block Layout: Must Fix First", 2)
add_para(doc, "All Tier 1 actions must be completed and verified before committing to PCB stackup.")

tier1_headers = ["#", "Action", "Owner", "Sheets"]
tier1_rows = [
    ["T1-1", "Correct all LT3045/LT3094 SET resistors: add 'k' suffix to R903, R907, R908, R909 "
     "(49.9Ω → 49.9kΩ). Verify each LT3045 output voltage against target. Fix R910 to 18.0kΩ "
     "for +1.8V_CLOCKTREE.", "Power", "power_ldos"],
    ["T1-2", "Replace all LT3045/LT3094 output capacitors from 4.7µF to ≥10µF ceramic "
     "(X5R/X7R, 0805, adequate voltage derating). Verify C931 (LT3094 output) also replaced.",
     "Power", "power_ldos"],
    ["T1-3", "Recalculate switching regulator feedback resistors: R1101 → 4.22MΩ (LT8330 for −5V); "
     "R1103 → 402kΩ (ADP2303 for target voltage). Verify all six populated resistors "
     "(R1108–R1113) produce correct output voltages.", "Power", "power_switching_reg"],
    ["T1-4", "Change R701 (series resistor between AD9523-1 OSC_CTRL and the ABLNO-VCXO's "
     "Vc input, ~10kΩ port impedance) from 1kΩ to 20kΩ, as the designer proposed. This "
     "brings the total OSC_CTRL load to ~30kΩ, clearing the AD9523-1's 'RLOAD > 20kΩ' "
     "condition (Table 5) with ~50% margin — better than simply hitting the 20kΩ floor "
     "(10kΩ would land exactly on the boundary of a strict '>' spec). Document the "
     "series-load calculation (R701 + VCXO Vc port impedance) on the schematic.",
     "Clock", "clock_tree"],
    ["T1-5", "Resolve U706 part/value conflict. Commit to SN74CBT3253 (5V) for Tx mux; "
     "update symbol lib_id, value, footprint, and BOM entry consistently. "
     "Also resolve VCXO vs. TCXO conflict: commit to ABLNO-VCXO; update CLAUDE.md.",
     "Clock", "clock_tree"],
    ["T1-6", "Fix ADAU1962A AVDD supply: replace Q601 (FZT951TA emitter follower producing ~2.7V) "
     "with LT3045 LDO set to 3.3V. Fix '0.iu' typo on C623/C624/C628 → '100n'. "
     "Rename '2.5' net label → '2.5V'.", "Precision", "dacs"],
    ["T1-7", "Rename 'DVDOUT' → 'DVDDOUT' in audio_subsystem.kicad_sch (two instances). "
     "Run ERC to confirm CM and DVDDOUT nets are distinct.",
     "Audio", "audio_subsystem"],
    ["T1-8", "Populate C406 (5600pF, ADAU1979 PLL_FILT): remove DNP marker. "
     "ADC is non-functional with this cap absent.", "Precision", "adcs"],
    ["T1-9", "Correct hold cap values: recalculate for N=8 phases. For ±200kHz BW: "
     "C_hold ≈ 2nF. Update all HC_201–HC_208 values and correct N annotation "
     "from N=1 to N=8 in the design note.", "RF", "rx_mixer"],
]
add_table(doc, tier1_headers, tier1_rows,
          col_widths=["1.2cm", "9.0cm", "1.8cm", "3.0cm"])

add_heading(doc, "6.2 Tier 2 — Fix Before PCB Stackup Decisions", 2)

tier2_rows = [
    ["T2-1", "Fix ADAU1979 VREF buffer topology: move R410 (3kΩ) to ADA4807-1 output, not VREF pin input. Ensure ADA4807-1 DISABLE pin tied to V+.", "Precision", "adcs"],
    ["T2-2", "No action required: ADA4945-1 feedback caps (180pF, C343/C322/C319/C320/C340/C341/C344) are optional output-filter provisions, correctly DNP per datasheet (gain set by RF/RG resistor ratio; no Cf shown in any application circuit). Document this intent in a schematic note so future reviewers don't re-flag it.", "RF", "rx_driver_amps"],
    ["T2-3", "Add TX reconstruction filter at TX_RF+/TX_RF- output. Design 7-element differential LC Chebyshev with passband edge at ~300kHz, stopband at ~192kHz.", "RF/System", "tx_mixer\nnzif"],
    ["T2-4", "Confirm/add PLL1 loop filter cap (AD9523-1 pin 7, LF1_EXT_CAP) per datasheet recommendation. Drive EOH on VCXO to enable state. Terminate ZD_IN/ZD_IN_b.", "Clock", "clock_tree"],
    ["T2-5", "Connect OSC_IN_b (AD9523-1 pin 10) to AC ground via 100nF cap for single-ended input mode.", "Clock", "clock_tree"],
    ["T2-6", "Add frequency plan annotation table in clock_tree.kicad_sch: reference frequency, PLL1/PLL2 VCO frequencies, all divider settings, resulting output frequencies.", "Clock", "clock_tree"],
    ["T2-7", "Confirm ADAU1467 SELFBOOT pin pulled high (IOVDD). Assign footprint to U502 (25AA1024 SPI EEPROM) — must appear in layout for self-boot.", "DSP", "dsp"],
    ["T2-8", "Fix 'MiSO_M' label (mixed case) → 'MISO_M' throughout dsp.kicad_sch. Run ERC to confirm zero label case conflicts.", "DSP", "dsp"],
    ["T2-9", "Add PGOOD pull-ups (100kΩ) on ADP2303 PGOOD pins. Define power sequencing: connect PGOOD outputs to downstream LDO EN pins or add sequencer IC.", "Power", "power_switching_reg\npower_ldos"],
    ["T2-10", "Replace 0402 footprint on C1215/C1216 (220µF) with appropriate electrolytic/tantalum footprint. Consider 470µF for fc ≈ 11Hz margin.", "Audio", "audio_subsystem"],
    ["T2-11", "Drive ADA4945-1 VOCM pin from AVDD/2 resistor divider to match ADAU1979 common-mode input requirement (1.65V at 3.3V AVDD).", "RF", "rx_driver_amps"],
    ["T2-12", "Resolve VCXO vs TCXO conflict (document in T1-6); update CLAUDE.md to match schematic component selection.", "System", "clock_tree"],
    ["T2-13", "Verify each of 17 ADAU1467 power pins has individual 100nF decoupling cap placed adjacent in layout.", "DSP", "dsp"],
    ["T2-14", "Standardise clock signal naming across all sheets (tx_phase_N vs CLK_N vs phase_N). Verify all hierarchical connections intact after rename.", "System", "tx_mixer\nclock_tree\nrx_mixer"],
    ["T2-15", "Verify Tx DAC differential polarity: trace each DAC_N+/DAC_N− to switch port; annotate polarity on tx_mixer schematic.", "RF", "tx_mixer"],
]
add_table(doc, tier1_headers, tier2_rows,
          col_widths=["1.2cm", "9.0cm", "1.8cm", "3.0cm"])

add_heading(doc, "6.3 Tier 3 — Complete Before Final ERC Sign-Off", 2)

tier3_rows = [
    ["T3-1", "Assign all missing component footprints across all sheets. Priority: U401 (ADA4807-1), X701/ABLNO-VCXO, U704/U707 (SN74LVC8T245), C401/C403 (change to 0805 as per T2), all remaining passive footprints.", "All", "all sheets"],
    ["T3-2", "Add anti-aliasing caps (100–470pF C0G) across each AIN+/AIN− pair at ADAU1979 inputs. Remove DNP from C405/C406 per T1-11.", "Precision", "adcs"],
    ["T3-3", "Connect RINP/RINN/RAUX (ADAU1361 pins 12/13/14) to CM net instead of no_connect. Add pull to defined level on JACKDET/MICIN (pin 4).", "Audio", "audio_subsystem"],
    ["T3-4", "Add bulk bypass cap (10–47µF) on SSM2211S V+ supply (pin 6). Change C1212 from 0.47µF to 1µF (SSM2211S BYPASS pin recommendation).", "Audio", "audio_subsystem"],
    ["T3-5", "Add RF EMI filter caps (100pF C0G to GND) on all audio input traces at MIC_IN, Line_Input hierarchical label pins.", "Audio", "audio_subsystem"],
    ["T3-6", "Add ADA4625-2 EP (pin 9) connection to V− supply rail in rx_mixer.kicad_sch for all 8 instances.", "RF", "rx_mixer"],
    ["T3-7", "Replace 10µF 0603 caps on +6.5V rail with 16V-rated 0805 parts in rx_mixer.kicad_sch.", "RF", "rx_mixer"],
    ["T3-8", "Add ferrite bead + 10µF cap between ADP2303 8V output and LT3045 input pins. Restore LDO PSRR advantage at 700kHz.", "Power", "power_ldos"],
    ["T3-9", "Complete Q501 USB_RESET circuit or document alternative; remove incomplete schematic note.", "uC", "microcontroller"],
    ["T3-10", "Resolve SWIO_0–3 destinations; annotate SWIO_VLOGIC source voltage; define pin purpose.", "uC", "microcontroller\nnzif"],
    ["T3-11", "Annotate ADAU1467 and ADAU1979 I2C addresses on respective sheets. Document I2S/TDM mode (TDM4 vs TDM8) and slot assignments for both ICs. Reference SigmaStudio project location.", "DSP\nPrecision", "dsp\nadcs\ndacs"],
    ["T3-12", "Add AMP_SHUTDOWN pull-down to GND at source (microcontroller or top-level). SSM2211S must default to shutdown on power-up.", "Audio", "audio_subsystem\nmicrocontroller"],
    ["T3-13", "Confirm I2C pull-up resistors (2kΩ to IOVDD) exist at exactly one point in hierarchy for each I2C bus: ADAU1361, ADAU1467, ADAU1979, ADAU1962A, MCP23017.", "System", "all sheets"],
    ["T3-14", "Correct '04.7u' notation on LT3045 SET bypass caps to '470n' (unambiguous). Verify all LT3045 SET pin bypass caps are populated.", "Power", "power_ldos"],
    ["T3-15", "Run full ERC with zero errors and zero warnings as gate criterion for layout freeze.", "All", "all sheets"],
]
add_table(doc, tier1_headers, tier3_rows,
          col_widths=["1.2cm", "9.0cm", "1.8cm", "3.0cm"])

# ═══════════════════════════════════════════════════════════════════
# SECTION 7: PERFORMANCE ANALYSIS
# ═══════════════════════════════════════════════════════════════════
add_heading(doc, "7. Theoretical Performance Analysis", 1)

add_heading(doc, "7.1 Receive Signal Chain — Dynamic Range Estimate", 2)

add_para(doc, "All figures are theoretical estimates. Hardware bring-up measurements are required.")

add_para(doc,
    ("Noise floor: ", "Bold"),
    "Mixer conversion loss ≈ 6 dB. ADA4625-2 contributes ≈ 2–3 dB NF. ADA4945-1 with "
    "Rf = 9.53kΩ contributes 12.6 nV/√Hz Johnson noise (dominant). "
    "Total estimated system NF = 6–9 dB."
)

add_para(doc,
    ("ADC chain dynamic range: ", "Bold"),
    "ADAU1979 full-scale = 4.5 Vrms differential. ADA4945-1 noise floor ≈ 3.1 µVrms "
    "(over 192kHz BW). Theoretical dynamic range ≈ 123 dB. Practical expectation: "
    "110–115 dB (limited by ADC quantization + ADA4945-1 noise)."
)

add_para(doc,
    ("Harmonic rejection (theoretical): ", "Bold"),
    "3rd LO harmonic: >60 dB. 5th: >50 dB. 7th: >45 dB. "
    "Practical expectation for well-built board: 40–55 dB "
    "(limited by switch Rds(on) matching and phase-clock timing accuracy)."
)

add_para(doc,
    ("Hold cap bandwidth note [CRITICAL DESIGN ISSUE]: ", "Critical"),
    "Current 100nF hold caps with N=8 phases produce ≈4 kHz baseband bandwidth. "
    "This limits the receiver to CW-only operation and is inconsistent with the stated "
    "±96 kHz NCO range. Recalculate for N=8: C_hold ≈ 2 nF for ±200 kHz target BW."
)

perf_headers = ["Metric", "NZIF (estimated)", "NC2030 (measured)", "Notes"]
perf_rows = [
    ["System NF", "6–9 dB", "~12 dB", "NZIF: no on-board LNA; figures unverified"],
    ["System IIP3", "+25–35 dBm", "+28.5 dBm", "NZIF: SN74CBT3125 not characterised as RF mixer; must measure"],
    ["Harmonic rejection\n(3rd/5th/7th)", "40–55 dB (est.)", ">45 dB (phasing)", "NZIF: phase-clock timing accuracy is limiting factor"],
    ["Instantaneous BW", "±96 kHz (target)\n≈4 kHz (current caps)", "~1.5 kHz", "NZIF hold caps must be changed to 2nF for target BW"],
    ["ADC SNR", "110–115 dB (192kHz)", "N/A", "ADAU1979 specification; supply quality critical"],
    ["DAC THD+N", "<0.005% (target)", "N/A", "ADAU1962A spec; degraded by Q601 unregulated AVDD"],
    ["MDS at ±96kHz BW", "~−115 dBm (est.)", "−135 dBm\n@ 500Hz BW", "Bandwidth-corrected comparison: NZIF ~−109 dBm equivalent"],
]
add_table(doc, perf_headers, perf_rows,
          col_widths=["4.0cm", "4.0cm", "4.0cm", "5.0cm"])

# ═══════════════════════════════════════════════════════════════════
# SECTION 8: PATH TO QST PUBLICATION
# ═══════════════════════════════════════════════════════════════════
add_heading(doc, "8. Path to QST Publication", 1)

add_heading(doc, "8.1 What Would Impress QST Reviewers", 2)

impressive = [
    "8-phase polyphase commutating mixer: novel at amateur level, directly extending Tayloe's 4-phase detector (QEX May 2001) to 8-phase with harmonic rejection to the 7th LO harmonic. Phasor mathematics and LTspice simulation are publication-ready.",
    "AD9523-1 dual-output clock architecture: LO tuning without disturbing the audio clock domain is a non-trivial insight not seen in amateur SDR designs.",
    "SN74AUC16374 ring counter phase generation: elegant, reproducible single-bit shift register producing eight non-overlapping phases from a high-speed clock.",
    "Fully differential signal flow through LT5400 matched-quad resistors for I/Q amplitude balance.",
    "Weaver two-stage demodulation: first stage in analog 8-phase mixer, second stage in ADAU1467 digital NCO — clean and technically rigorous.",
    "I/Q calibration via directional coupler calibration tap: more sophisticated than any published amateur receiver design.",
    "LT3045/LT3094 power architecture: 2 µVrms noise floor, domain-isolated rails — publishable design decision that most commercial SDR kits skip.",
    "ZWAS quasi-elliptic LPF bank serving dual TX/RX purpose: the trap that rejects the 2nd PA harmonic on transmit is the same trap that notches the adjacent amateur band on receive.",
]
for item in impressive:
    add_bullet(doc, item)

add_heading(doc, "8.2 What Would Concern QST Reviewers", 2)

concerns_qst = [
    "TX reconstruction filter absent: transmitter cannot demonstrate Part 97 compliance. Mandatory before any submission.",
    "No measured performance data: all figures are theoretical estimates. QST requires bench-measured MDS, IIP3, harmonic rejection, and image rejection.",
    "8 critical schematic errors: any one would prevent a built board from functioning. Schematics must be ERC-clean before submission.",
    "Hold capacitor design error (N=8 vs N=1): ≈4 kHz bandwidth vs stated ±96 kHz. A reviewer will check this calculation.",
    "ADAU1467 is a 300-ball BGA: home construction requires professional PCB assembly. Note assembly requirements clearly.",
    "SigmaStudio proprietary toolchain: reviewer may ask whether design is replicable without purchasing SigmaStudio license. Provide .dspproj file.",
    "6m 4-phase spurious response to 30m signals: must be quantified and disclosed in article.",
    "Power supply bring-up risk (LDOs oscillate due to insufficient output capacitance, switcher feedback values wrong) means average builder may not diagnose failures.",
]
for item in concerns_qst:
    add_bullet(doc, item)

add_heading(doc, "8.3 Minimum Viable Path to Submission", 2)

mvp = [
    "Week 1: Complete all Tier 1 critical schematic fixes (T1-1 through T1-9).",
    "Week 2: Complete Tier 2 items, particularly TX reconstruction filter design (T2-3) and AD9523-1 configuration (T2-4–T2-6).",
    "Week 3: Assign all footprints, run ERC to zero errors, freeze schematic for layout.",
    "Layout: Length-match all phase_0...phase_315 traces. Isolate clock tree from baseband. Follow LT3045 layout guidelines for output cap placement.",
    "Bring-up: Measure and document: (1) All supply rail voltages with oscilloscope for LDO stability, (2) AD9523-1 lock status, (3) ADAU1979 and ADAU1962A I2C communication, (4) ADAU1467 program load verification.",
    "Performance measurements: MDS (Y-factor or noise source comparison), two-tone IIP3, harmonic rejection at f_LO/3, f_LO/5, f_LO/7, image rejection, TX spectrum (with reconstruction filter).",
    "Submission: Corrected ERC-clean schematic, SigmaStudio project file, AD9523-1 register dump, measured performance data table, Pico firmware source.",
]
for i, item in enumerate(mvp, 1):
    add_bullet(doc, f"Step {i}: {item}")

# Footer
doc.text.addElement(P(stylename="Body Text"))
footer_style = Style(name="Footer", family="paragraph")
footer_style.addElement(TextProperties(fontsize="8pt", color="#808080"))
doc.styles.addElement(footer_style)

fp = P(stylename="Footer")
fp.addText(f"NZIF Radio Schematic Review — Generated 2026-06-07 (corrected) | "
           f"Reviewers: HF Architecture, RF Mixer, Clock Tree, Power/Audio, Precision Analog, Audio Subsystem | "
           f"Status: HOLD — 8 Critical items block layout freeze")
doc.text.addElement(fp)

# ── Save ─────────────────────────────────────────────────────────────────────

outpath = "/home/andrew/OneDrive/github/NZIF_Radio/nzif/docs/NZIF_Radio_System_Architecture_Schematic_Review_2026-06-07_corrected.odt"
doc.save(outpath)
print(f"Saved: {outpath}")
