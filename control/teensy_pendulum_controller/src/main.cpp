#include <Arduino.h>
#include <RotaryEncoder.h>
#include <CytronMotorDriver.h>

// === Pin definitions ===
#define ANGLE_ENCODER_HIGH 2
#define ANGLE_ENCODER_LOW 3
#define X_ENCODER_HIGH 4
#define X_ENCODER_LOW 5
#define MOTOR_PWM 14
#define MOTOR_DIR 15

// === Global objects ===
RotaryEncoder* x_encoder = nullptr;
RotaryEncoder* angle_encoder = nullptr;
CytronMD motor(PWM_DIR, MOTOR_PWM, MOTOR_DIR);

// === Encoder helpers ===
uint16_t encoderReadAngle() {
  int angle_raw = angle_encoder->getPosition();
  if (angle_raw < 0) angle_raw += 1200;
  else if (angle_raw >= 1200) angle_raw -= 1200;
  return angle_raw;
}

uint16_t encoderReadX() {
  return x_encoder->getPosition();
}

void checkPosition() {
  x_encoder->tick();
  angle_encoder->tick();
}

void setup() {
  Serial.begin(115200);
  while (!Serial);  // wait for serial to be ready

  // LED to show heartbeat or debug
  pinMode(LED_BUILTIN, OUTPUT);

  // === Setup encoders ===
  x_encoder = new RotaryEncoder(X_ENCODER_HIGH, X_ENCODER_LOW, RotaryEncoder::LatchMode::TWO03);
  x_encoder->setPosition(0);

  angle_encoder = new RotaryEncoder(ANGLE_ENCODER_HIGH, ANGLE_ENCODER_LOW, RotaryEncoder::LatchMode::TWO03);
  angle_encoder->setPosition(0);

  // Pull-ups and interrupts
  pinMode(X_ENCODER_HIGH, INPUT_PULLUP);
  pinMode(X_ENCODER_LOW, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(X_ENCODER_HIGH), checkPosition, CHANGE);
  attachInterrupt(digitalPinToInterrupt(X_ENCODER_LOW), checkPosition, CHANGE);

  pinMode(ANGLE_ENCODER_HIGH, INPUT_PULLUP);
  pinMode(ANGLE_ENCODER_LOW, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ANGLE_ENCODER_HIGH), checkPosition, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ANGLE_ENCODER_LOW), checkPosition, CHANGE);
}

void loop() {
  static uint16_t last_x_pos = 0;
  static uint16_t last_angle = 0;

  // === Read encoders and send sensor data if changed ===
  uint16_t x = encoderReadX();
  uint16_t angle = encoderReadAngle();

  if (x != last_x_pos || angle != last_angle) {
    Serial.write(0xAA);                     // sync byte
    Serial.write((uint8_t*)&x, 2);          // send x position
    Serial.write((uint8_t*)&angle, 2);      // send angle

    last_x_pos = x;
    last_angle = angle;
  }

  // === Handle incoming control signal ===
  if (Serial.available() >= 3) {
    if (Serial.read() == 0x55) {  // look for control sync byte
      int16_t control_input = 0;
      Serial.readBytes((char*)&control_input, 2);
      motor.setSpeed(control_input);
      digitalWrite(LED_BUILTIN, control_input != 0);
    }
  }  
}
