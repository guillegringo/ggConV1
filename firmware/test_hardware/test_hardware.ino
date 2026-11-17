// Prueba de hardware ANTES de flashear GUN4IR.
// Pro Micro (ATmega32U4) + DFRobot SEN0158 + 5 botones.
// Abrir el Monitor Serie a 115200: muestra los 4 puntos IR y el estado de los botones.

#include <Wire.h>

const uint8_t CAM_ADDR = 0x58;   // 0xB0 >> 1 (igual que la camara del Wiimote)

// Pines de botones (a GND, con pull-up interno)
const uint8_t PIN_TRIGGER = 4;
const uint8_t PIN_A       = 5;
const uint8_t PIN_B       = 6;
const uint8_t PIN_START   = 7;
const uint8_t PIN_SELECT  = 8;
const uint8_t PINS[]      = {PIN_TRIGGER, PIN_A, PIN_B, PIN_START, PIN_SELECT};
const char*   NAMES[]     = {"TRIG", "A", "B", "START", "SELECT"};

void camWrite(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(CAM_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
  delay(10);
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 4000) {}
  for (uint8_t p : PINS) pinMode(p, INPUT_PULLUP);

  Wire.begin();            // SDA = pin 2, SCL = pin 3 en el Pro Micro
  camWrite(0x30, 0x01);
  camWrite(0x30, 0x08);
  camWrite(0x06, 0x90);
  camWrite(0x08, 0xC0);
  camWrite(0x1A, 0x40);
  camWrite(0x33, 0x33);
  delay(100);

  Wire.beginTransmission(CAM_ADDR);
  Serial.println(Wire.endTransmission() == 0 ? F("Camara OK en 0x58")
                                             : F("ERROR: camara no responde (revisar SDA/SCL/VCC)"));
}

void loop() {
  uint8_t d[16] = {0};
  Wire.beginTransmission(CAM_ADDR);
  Wire.write(0x36);
  Wire.endTransmission();
  Wire.requestFrom(CAM_ADDR, (uint8_t)16);
  for (uint8_t i = 0; i < 16 && Wire.available(); i++) d[i] = Wire.read();

  for (uint8_t i = 0; i < 4; i++) {
    uint8_t s = d[3 + 3 * i];
    int x = d[1 + 3 * i] | ((s & 0x30) << 4);
    int y = d[2 + 3 * i] | ((s & 0xC0) << 2);
    Serial.print(F("P")); Serial.print(i);
    if (x == 1023) Serial.print(F(":----,----  "));
    else { Serial.print(':'); Serial.print(x); Serial.print(','); Serial.print(y); Serial.print(F("  ")); }
  }
  Serial.print(F("| "));
  for (uint8_t i = 0; i < 5; i++) {
    if (digitalRead(PINS[i]) == LOW) { Serial.print(NAMES[i]); Serial.print(' '); }
  }
  Serial.println();
  delay(50);
}
