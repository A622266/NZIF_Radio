# USB CDC CAT (Pico SDK)

Minimal USB CDC prototype for Kenwood-style CAT commands over a COM port.

## Supported commands (initial)
- `FA` (get/set frequency in Hz, 11 digits)
- `MD` (get/set mode)
- `TX` / `RX` (PTT)
- `ID` (returns Kenwood TS-2000 ID)
- `AI` (auto information off)
- `IF` (placeholder response)

## Build (Windows)
1. Install Pico SDK and set `PICO_SDK_PATH`.
2. From a build directory:
   - Configure: `cmake -G "Ninja" ..`
   - Build: `cmake --build .`

## Notes
This is a bring-up stub meant to confirm USB CDC and basic CAT parsing. The `IF` response is intentionally minimal and should be expanded for full compatibility.
