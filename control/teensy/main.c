
void setup() {
  Serial.begin(115200);
  while (!Serial);
}

void loop() {
  uint16_t s1 = analogRead(A0);
  uint16_t s2 = analogRead(A1);
  s1 = map(s1, 0, 1023, 0, 9600);
  s2 = map(s2, 0, 1023, 0, 9600);

  Serial.write(0xAA);                         // Start byte
  Serial.write((uint8_t*)&s1, 2);             // Sensor 1 (LSB, MSB)
  Serial.write((uint8_t*)&s2, 2);             // Sensor 2
}