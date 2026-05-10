# BiciSafe&EcoCharge — Object Detection with Haptic Feedback and LED Matrix

An Arduino project that combines **video object detection**, **haptic feedback** (vibration motor) and an **animated battery indicator** on an LED matrix.

---

## Overview

When the camera detects an object, the vibration module activates for 500 ms as a haptic signal. At the same time, the LED matrix displays an animated battery indicator that blinks at different speeds depending on the simulated accumulated energy level.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│                  main.py                    │
│                                             │
│  VideoObjectDetection ──► send_detections   │
│         │                      │            │
│         │              Bridge.call("activar_vibracion")
│         │                      │            │
│  WebUI  ◄──── ui.send_message("detection") │
│                                             │
│  Thread 1: main_logic  (energy calculation) │
│  Thread 2: blink_loop  (LED animation)      │
└────────────────┬────────────────────────────┘
                 │ Bridge (USB / Serial)
┌────────────────▼────────────────────────────┐
│                sketch.ino                   │
│                                             │
│  Bridge.provide("draw")   ──► matrix.draw() │
│  Bridge.provide("activar_vibracion") ──► vibro.on(500ms)
└─────────────────────────────────────────────┘
```

---

## Project files

| File | Description |
|---|---|
| `main.py` | Main logic: detection, energy simulation, LED animation |
| `sketch.ino` | Arduino code: LED matrix and vibration module |
| `app.yaml` | Application configuration (ports, bricks) |
| `sketch.yaml` | Arduino platform and libraries |
| `leds.h` | (Reserved for additional LED logic) |
| `vibrador.h` | (Reserved for additional vibration logic) |

---

## Hardware requirements

- Arduino board compatible with `arduino:zephyr`
- **ModulinoVibro** — vibration module connected via `Wire1`
- **Arduino LED Matrix** — 8×13 matrix with 3-bit grayscale
- USB connection for the Bridge (Python ↔ Arduino communication)
- Camera compatible with `VideoObjectDetection`

---

## Software requirements

**Arduino libraries** (defined in `sketch.yaml`):

- `Arduino_Modulino` (0.8.0)
- `Arduino_RouterBridge`
- `Arduino_LED_Matrix`
- `ArduinoGraphics` (1.1.5)
- `Arduino_LSM6DSOX`, `Arduino_LPS22HB`, `Arduino_LTR381RGB`, etc.

**Python:**

```bash
pip install arduino-app-utils
```

---

## How it works

### Object detection

`VideoObjectDetection` analyses the video stream with a 50% confidence threshold. Each time an object is detected:

1. An `activar_vibracion` command is sent to the Arduino via Bridge.
2. The Arduino activates the vibrator for **500 ms**.
3. The detection (object name, confidence, timestamp) is sent to the web interface via WebSocket.

### LED battery animation

Two parallel threads handle the simulation:

- **`main_logic`**: simulates energy consumption using a list of test currents and accumulates Wh. Updates the battery level every second.
- **`blink_loop`**: draws the battery on the LED matrix and controls the blinking behaviour:

| Battery level | Behaviour |
|---|---|
| > 60% | Steady LED (no blinking) |
| 31–60% | Slow blink (800 ms) |
| ≤ 30% | Fast blink (200 ms) |

### Python ↔ Arduino Bridge

Communication is handled via `Bridge`:

```python
# Python → Arduino
Bridge.call("draw", frame_bytes)             # Draw a frame on the matrix
Bridge.call("activar_vibracion", 100, 1000)  # Activate the vibrator

# Arduino registers the functions
Bridge.provide("draw", draw);
Bridge.provide("activar_vibracion", activarVibracion);
```

---

## Configuration

### Energy parameters (main.py)

```python
VOLTAJE = 5.0    # Volts
META_WH = 0.05   # Energy target in Wh
```

### Blink parameters (main.py)

```python
BLINK_FAST_MS = 200   # Fast blink (low battery ≤ 30%)
BLINK_SLOW_MS = 800   # Slow blink (medium battery)
```

### Detection threshold

Can be adjusted in real time from the web interface:

```javascript
// From the web client
socket.emit("override_th", 0.7);  // Set threshold to 70%
```

---

## Running the project

```bash
# Upload the sketch to the Arduino first, then run:
python main.py
```

The web interface will be available on port **7000**.

---

## LED matrix layout

The battery occupies an **8 × 13** pixel grid:

```
[ 7  7  7  7  7  7  7  7  7  7  7  0  0 ]   ← Top border
[ 7  ·  ·  ·  ·  ·  ·  ·  ·  ·  7  0  0 ]
[ 7  ·  ·  ■  ■  ■  ■  ■  ■  ■  7  7  0 ]   ← Interior (rows 2–5)
[ 7  ·  ·  ■  ■  ■  ■  ■  ■  ■  7  7  7 ]   ← + Terminal
[ 7  ·  ·  ■  ■  ■  ■  ■  ■  ■  7  7  7 ]
[ 7  ·  ·  ■  ■  ■  ■  ■  ■  ■  7  7  0 ]
[ 7  ·  ·  ·  ·  ·  ·  ·  ·  ·  7  0  0 ]
[ 7  7  7  7  7  7  7  7  7  7  7  0  0 ]   ← Bottom border
```

Columns 2–8 of rows 2–5 fill progressively from left to right according to the battery percentage.





