#include <Arduino.h>
#include <RotaryEncoder.h>

// Pin definitions for the rotary encoders
#define ANGLE_ENCODER_HIGH 2
#define ANGLE_ENCODER_LOW 3
#define X_ENCODER_HIGH 4
#define X_ENCODER_LOW 5

RotaryEncoder *x_encoder = nullptr;
RotaryEncoder *angle_encoder = nullptr;

uint16_t encoderReadAngle() { // after angle = 1200 this will wrap back to 0
  int angle_raw = angle_encoder->getPosition();
  if (angle_raw < 0) {
    angle_raw += 1200; // wrap around to positive
  } else if (angle_raw >= 1200) {
    angle_raw -= 1200; // wrap around to less than 1200
  }
  return angle_raw;
}

uint16_t encoderReadX() {
  return x_encoder->getPosition();
}

void checkPosition()
{
  x_encoder->tick(); // just call tick() to check the state.
  angle_encoder->tick(); // just call tick() to check the state.
}

void setup() {
  Serial.begin(115200);
  while (!Serial){
    // Wait for Serial to be ready
  };

  Serial.println("Rotary Encoder Test");

  x_encoder = new RotaryEncoder(X_ENCODER_HIGH, X_ENCODER_LOW, RotaryEncoder::LatchMode::TWO03);
  x_encoder->setPosition(0); // Initialize position to 0

  angle_encoder = new RotaryEncoder(ANGLE_ENCODER_HIGH, ANGLE_ENCODER_LOW, RotaryEncoder::LatchMode::TWO03);
  angle_encoder->setPosition(0); // Initialize position to 0

  // setup interrupt for encoder pins
  pinMode(X_ENCODER_HIGH, INPUT_PULLUP);
  pinMode(X_ENCODER_LOW, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(X_ENCODER_HIGH), checkPosition, CHANGE);
  attachInterrupt(digitalPinToInterrupt(X_ENCODER_LOW), checkPosition, CHANGE);

  pinMode(ANGLE_ENCODER_HIGH, INPUT_PULLUP);
  pinMode(ANGLE_ENCODER_LOW, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ANGLE_ENCODER_HIGH), checkPosition, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ANGLE_ENCODER_LOW), checkPosition, CHANGE);
}

void loop()
{
  static uint16_t x_encoder_position = 0 - 16200/2;
  static uint16_t angle_encoder_position = 0;

  int new_x_pos = encoderReadX();
  uint16_t new_angle_pos = encoderReadAngle();
  if (x_encoder_position != new_x_pos || angle_encoder_position != new_angle_pos) {
    
    // Send sensor data with sync byte 0xAA
    Serial.write(0xAA); // sync byte
    Serial.write((uint8_t*) &new_x_pos, 2);
    Serial.write((uint8_t*) &new_angle_pos, 2);

    x_encoder_position = new_x_pos;
    angle_encoder_position = new_angle_pos;
  }
}

