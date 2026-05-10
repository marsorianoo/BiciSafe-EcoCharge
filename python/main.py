# main.py

from arduino.app_utils import App, Bridge # <--- Import Bridge
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection
from datetime import datetime, UTC
from arduino.app_utils import *
import threading
import time

# --- Energy simulation constants ---
VOLTAJE = 5.0
META_WH = 0.05  
corrientes_test = [1.5, 2.0, 3.5, 0.0, 0.0, 4.5, 5.0, 1.0]

# --- LED blink timing constants (milliseconds) ---
BLINK_FAST_MS = 200
BLINK_SLOW_MS = 800

# --- LED matrix interior cell coordinates ---
INTERIOR_ROWS = [ 2, 3, 4, 5]
INTERIOR_COLS = [2, 3, 4, 5, 6, 7, 8]

# --- Initialise web UI and video detection stream ---
ui = WebUI()
detection_stream = VideoObjectDetection(confidence=0.5, debounce_sec=0.0)

# Allow the web UI to override the detection confidence threshold at runtime
ui.on_message("override_th", lambda sid, threshold: detection_stream.override_threshold(threshold))

class EnergySystem:
    """Tracks accumulated energy and the current battery level."""
    def __init__(self):
        self.acumulado_wh = 0.0
        self.current_level = 0
        self.idx = 0

state = EnergySystem()

def _base_frame():
    """Return the static battery outline as an 8×13 pixel grid."""
    return [
        [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0],
        [7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0],
        [7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 0],
        [7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 7],
        [7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 7],
        [7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 0],
        [7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0],
        [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0],
    ]

def build_battery_frame(level, interior_on=True):
    """
    Build a battery frame for the given charge level.

    Args:
        level: Battery percentage (0–100).
        interior_on: If False, the interior cells are left dark (used for blinking).

    Returns:
        A bytes object ready to send to the LED matrix.
    """
    total_cols = len(INTERIOR_COLS)
    filled = round((level / 100) * total_cols)
    filled_cols = set(INTERIOR_COLS[:filled])
    
    frame = _base_frame()
    if interior_on:
        for r in INTERIOR_ROWS:
            for c in filled_cols:
                frame[r][c] = 7
    return bytes(v for row in frame for v in row)


def send_frame(frame_bytes):
    """Send a rendered frame to the Arduino LED matrix via Bridge."""
    Bridge.call("draw", frame_bytes)

def main_logic():
    """
    Background thread: simulate energy consumption.
    Cycles through test current values every second and updates the battery level.
    """
    while True:
        amp = corrientes_test[state.idx % len(corrientes_test)]
        state.idx += 1
        state.acumulado_wh += (VOLTAJE * amp / 3600.0)
        state.current_level = min(100, int((state.acumulado_wh / META_WH) * 100))
        time.sleep(1)

def blink_loop():
    """
    Background thread: drive the LED matrix animation.
    - Above 60 %: steady on.
    - 31–60 %:    slow blink (BLINK_SLOW_MS interval).
    - 0–30 %:     fast blink (BLINK_FAST_MS interval).
    """
    while True:
        level = state.current_level
        on_frame = build_battery_frame(level, True)
        off_frame = build_battery_frame(level, False)
        if level > 60:
            send_frame(on_frame)
            time.sleep(1)
        else:
            interval = (BLINK_FAST_MS if level <= 30 else BLINK_SLOW_MS) / 1000.0
            send_frame(on_frame)
            time.sleep(interval)
            send_frame(off_frame)
            time.sleep(interval)

# Start background threads
threading.Thread(target=main_logic, daemon=True).start()
threading.Thread(target=blink_loop, daemon=True).start()

# Callback triggered whenever objects are detected in the video stream
def send_detections_to_ui(detections: dict):
    # A non-empty dict means at least one object was detected
    if detections:
        # Call the Arduino function via Bridge, passing intensity and duration
        # Note: duration is ignored in the .ino; vibration is fixed at 500 ms
        Bridge.call("activar_vibracion", 100, 1000)

    for key, values in detections.items():
        for value in values:
            entry = {
                "content": key,
                "confidence": value.get("confidence"),
                "timestamp": datetime.now(UTC).isoformat()
            }
            ui.send_message("detection", message=entry)

detection_stream.on_detect_all(send_detections_to_ui)

App.run()
