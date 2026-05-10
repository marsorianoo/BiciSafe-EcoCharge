#include <Arduino_Modulino.h>
#include <Arduino_RouterBridge.h>
#include <Arduino_RouterBridge.h>
#include <Arduino_LED_Matrix.h>
#include <vector>

ModulinoVibro vibro;
Arduino_LED_Matrix matrix;

void setup() {
  Bridge.begin();
  Modulino.begin(Wire1);
  matrix.begin();
  matrix.setGrayscaleBits(3);
  matrix.clear();
  Bridge.provide("draw", draw);

  // Wait until the vibration module is ready
  while (!vibro.begin()) {
    delay(1000);
  }

  Bridge.provide("activar_vibracion", activarVibracion);
}

// Activates the vibration motor for a fixed 500 ms on each detection event.
// The intensity and duration parameters are received but duration is intentionally ignored.
void activarVibracion(int intensidad, int duracion) {
  vibro.on(500); // Vibrate for half a second per detection
}

void loop() {
  delay(10);
}

// Draws the given pixel frame on the LED matrix.
// Skips empty frames to avoid overwriting the display with blank data.
void draw(std::vector<uint8_t> frame) {
  if (frame.empty()) return;
  matrix.draw(frame.data());
}
