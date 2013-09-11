#include <DigiUSB.h>

#define RED 0
#define GREEN 1
#define BLUE 2

void setup() {
  DigiUSB.begin();
  pinMode(0, OUTPUT);
  pinMode(1, OUTPUT);
  pinMode(2, OUTPUT);
}

void try_input() {
  while (DigiUSB.available()) {
    switch (DigiUSB.read()) {
    case 'R':
      digitalWrite(RED, HIGH);
      break;
    case 'G':
      digitalWrite(GREEN, HIGH);
      break;
    case 'B':
      digitalWrite(BLUE, HIGH);
      break;
    case '-':
      digitalWrite(RED, LOW);
      digitalWrite(GREEN, LOW);
      digitalWrite(BLUE, LOW);
      break;
    }
  }
  DigiUSB.delay(10);
}

void loop() {
  try_input();
}
