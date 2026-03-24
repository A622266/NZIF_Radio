#!/usr/bin/env python3

import os
import sys
from pathlib import Path

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

from kicad_sym import KicadLibrary, KicadSymbol, Pin, Rectangle

DATASHEET_URL = "https://www.analog.com/media/en/technical-documentation/data-sheets/lt8330.pdf"
LIB_NAME = "LT8330"


def add_std_properties(symbol: KicadSymbol) -> None:
    symbol.add_default_properties()
    symbol.get_property("Reference").value = "U"
    symbol.get_property("ki_keywords").value = "LT8330 boost sepic inverting"
    symbol.get_property("Description").value = "Low IQ boost/SEPIC/inverting converter with 1A, 60V switch"
    symbol.get_property("Datasheet").value = DATASHEET_URL


def set_ref_value_positions(symbol: KicadSymbol, ref_y: float, value_y: float) -> None:
    symbol.get_property("Reference").posx = 0.0
    symbol.get_property("Reference").posy = ref_y
    symbol.get_property("Value").posx = 0.0
    symbol.get_property("Value").posy = value_y


def add_body(symbol: KicadSymbol, width_mm: float, height_mm: float) -> None:
    half_w = width_mm / 2
    half_h = height_mm / 2
    symbol.rectangles.append(Rectangle(half_w, -half_h, -half_w, half_h, stroke_width=0.254))


def add_lt8330_s6(lib: KicadLibrary) -> None:
    symbol = KicadSymbol.new(
        "LT8330xS6",
        LIB_NAME,
        reference="U",
        footprint="Package_TO_SOT_SMD:TSOT-23-6",
        datasheet=DATASHEET_URL,
        keywords="LT8330 boost sepic inverting converter",
        description="LT8330, 6-pin TSOT-23",
        fp_filters="TSOT*",
    )
    add_std_properties(symbol)
    set_ref_value_positions(symbol, ref_y=8.89, value_y=-8.89)
    add_body(symbol, width_mm=15.24, height_mm=12.70)

    symbol.pins.append(Pin(number="1", name="VIN", etype="power_in", posx=-2.54, posy=10.16, length=2.54, rotation=270))
    symbol.pins.append(Pin(number="2", name="GND", etype="power_in", posx=-2.54, posy=-10.16, length=2.54, rotation=90))
    symbol.pins.append(Pin(number="3", name="EN/UVLO", etype="input", posx=-10.16, posy=0.0, length=2.54, rotation=0))

    symbol.pins.append(Pin(number="4", name="FBX", etype="input", posx=10.16, posy=0.0, length=2.54, rotation=180))
    symbol.pins.append(Pin(number="5", name="SW", etype="output", posx=10.16, posy=2.54, length=2.54, rotation=180))
    symbol.pins.append(Pin(number="6", name="INTVCC", etype="output", posx=10.16, posy=5.08, length=2.54, rotation=180))

    lib.symbols.append(symbol)


def add_lt8330_ddb(lib: KicadLibrary) -> None:
    symbol = KicadSymbol.new(
        "LT8330xDDB",
        LIB_NAME,
        reference="U",
        footprint="Package_DFN_QFN:DFN-8-1EP_3x2mm_P0.5mm_EP1.7x1.6mm",
        datasheet=DATASHEET_URL,
        keywords="LT8330 boost sepic inverting converter",
        description="LT8330, 8-pin DFN 3x2mm with exposed pad",
        fp_filters="DFN*8*1EP*3x2mm*P0.5mm*",
    )
    add_std_properties(symbol)
    set_ref_value_positions(symbol, ref_y=10.16, value_y=-10.16)
    add_body(symbol, width_mm=15.24, height_mm=15.24)

    symbol.pins.append(Pin(number="1", name="FBX", etype="input", posx=-10.16, posy=7.62, length=2.54, rotation=0))
    symbol.pins.append(Pin(number="2", name="NC", etype="no_connect", posx=-10.16, posy=5.08, length=2.54, rotation=0, is_hidden=True))
    symbol.pins.append(Pin(number="3", name="SW", etype="output", posx=-10.16, posy=2.54, length=2.54, rotation=0))
    symbol.pins.append(Pin(number="4", name="SW", etype="output", posx=-10.16, posy=0.0, length=2.54, rotation=0))

    symbol.pins.append(Pin(number="5", name="GND", etype="power_in", posx=2.54, posy=-10.16, length=2.54, rotation=90))
    symbol.pins.append(Pin(number="6", name="VIN", etype="power_in", posx=2.54, posy=10.16, length=2.54, rotation=270))
    symbol.pins.append(Pin(number="7", name="INTVCC", etype="output", posx=10.16, posy=5.08, length=2.54, rotation=180))
    symbol.pins.append(Pin(number="8", name="EN/UVLO", etype="input", posx=10.16, posy=7.62, length=2.54, rotation=180))
    symbol.pins.append(Pin(number="9", name="GND", etype="passive", posx=2.54, posy=-10.16, length=2.54, rotation=90, is_hidden=True))

    lib.symbols.append(symbol)


def main() -> None:
    out_path = Path(__file__).with_name(f"{LIB_NAME}.kicad_sym")
    lib = KicadLibrary(str(out_path))
    add_lt8330_s6(lib)
    add_lt8330_ddb(lib)
    lib.write()
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
