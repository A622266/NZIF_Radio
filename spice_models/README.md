# SPICE Models

This folder contains SPICE models and testbenches for the NZIF signal path.

## Structure
- `rx_chain_testbench.cir` — starter testbench for EPC2037 -> LT8418 -> ADA4625 -> LT5400 -> ADA4945.
- `models/` — place vendor or custom SPICE models here (create as needed).
   - `EPCGaNLibrary.lib` — EPC GaN model library (includes EPC2037).

## How to use
1. Download vendor SPICE models for:
   - EPC2037
   - LT8418 (included with LTspice)
   - ADA4625
   - LT5400
   - ADA4945
2. Put the model files in `spice_models\models\`.
3. Update the `.include` paths in `rx_chain_testbench.cir`.
4. Run in LTspice or import to KiCad’s simulator.

## Notes
- The testbench uses placeholder subcircuit names. Adjust them to match vendor model names.
- Replace ideal sources and values as your actual schematic is finalized.
