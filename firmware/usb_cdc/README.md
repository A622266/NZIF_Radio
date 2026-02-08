# USB CDC CAT (Pico SDK)

Minimal USB CDC prototype for Kenwood-style CAT commands over a USB virtual serial port.

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

## What This Does (Non-Programmer Summary)
- The Pico appears as a USB serial device when plugged in normally.
- Software can send CAT commands like `FA;` or `IF;` over USB.
- The firmware replies with simple, valid Kenwood-style responses.

## Step-by-Step (Linux)
### 1) Install build tools and Pico SDK
```bash
sudo apt update
sudo apt install -y cmake ninja-build gcc-arm-none-eabi libnewlib-arm-none-eabi build-essential git

mkdir -p ~/pico
cd ~/pico
git clone https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk
git submodule update --init
```

### 2) Build the firmware
```bash
cd ~/Documents/ham_radio/NZIF_Radio/firmware/usb_cdc
mkdir -p build
cd build
PICO_SDK_PATH=~/pico/pico-sdk cmake -G Ninja ..
cmake --build .
```

### 3) Flash the Pico (BOOTSEL mode)
1. Unplug the Pico.
2. Hold **BOOTSEL** and plug in USB.
3. You should see a drive named `RPI-RP2`.
4. Copy the UF2 file:
```bash
cp ~/Documents/ham_radio/NZIF_Radio/firmware/usb_cdc/build/nzif_usb_cdc.uf2 /media/$USER/RPI-RP2/
```
The Pico reboots after the copy.

### 4) Find the serial device
```bash
ls /dev/ttyACM*
```
Typical output: `/dev/ttyACM0`

### 5) Run the CAT test script
```bash
cd ~/Documents/ham_radio/NZIF_Radio
chmod +x scripts/cat_test.sh
./scripts/cat_test.sh /dev/ttyACM0
```

Expected output looks like:
```
> FA;
< FA00014070000;

> IF;
< IF00014070000000000000000000002000;
```

## Step-by-Step (Collaborator Checklist)
1. Install tools + Pico SDK (Step 1).
2. Build the firmware (Step 2).
3. Flash the Pico (Step 3).
4. Find the serial device (Step 4).
5. Run the test script (Step 5).

## Optional: Stable Device Names
Linux already provides stable names under `/dev/serial/by-id/`. You can use those in the test script instead of `/dev/ttyACM0`.

If you prefer a short custom name, add a udev rule (example):
```bash
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="2e8a", ATTRS{idProduct}=="000a", SYMLINK+="pico-cat-%s{serial}", GROUP="dialout", MODE="0660"' | sudo tee /etc/udev/rules.d/99-pico-cat.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```
Then use `/dev/pico-cat-<serial>` in the test script.

## Troubleshooting
- **Pico does not show up in `lsusb`:** Try a different USB cable (many are charge-only) and a different port.
- **No `RPI-RP2` drive in BOOTSEL mode:** Hold **BOOTSEL** while plugging in, and keep it held for 2–3 seconds.
- **No `/dev/ttyACM0` after flashing:** Unplug and replug *without* BOOTSEL. The Pico should appear as a CDC device.
- **`screen` says permission denied:** Add your user to the `dialout` group: `sudo usermod -a -G dialout $USER`, then log out/in.
- **Test script shows no responses:** Make sure commands end with `;` and use the updated script: `./scripts/cat_test.sh /dev/ttyACM0`.

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
