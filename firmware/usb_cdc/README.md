# USB CDC CAT (Pico SDK)

Minimal USB CDC prototype for Kenwood-style CAT commands over a COM port.

## Supported commands (initial)
- `FA` / `FB` (get/set VFO A/B frequency in Hz, 11 digits)
- `FR` / `FT` (select RX/TX VFO)
- `MD` (get/set mode)
- `TX` / `RX` (PTT)
- `ID` (returns Kenwood TS-2000 ID)
- `AI` (auto information off)
- `IF` (structured response)
- `AG` / `RG` (AF/RF gain)
- `SM` (S-meter)
- `GT` (AGC)
- `KS` / `KY` (keyer speed / CW text ack)

## Build (Windows)
1. Install Pico SDK and set `PICO_SDK_PATH`.
2. From a build directory:
   - Configure: `cmake -G "Ninja" ..`
   - Build: `cmake --build .`

## Quick CAT test (Windows)
Use the PowerShell script in [scripts/cat_test.ps1](scripts/cat_test.ps1):

- Example: `powershell -File .\scripts\cat_test.ps1 -Port COM5`

## Notes
This is a bring-up stub meant to confirm USB CDC and basic CAT parsing. The `IF` response is structured but still simplified and should be expanded for full compatibility.
