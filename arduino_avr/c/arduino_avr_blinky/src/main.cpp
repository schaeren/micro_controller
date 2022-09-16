#include "Arduino.h"

void setup() {
    Serial.begin(115200);             // configure serial monitor (serial port over USB, 115200 is the speed)
    pinMode(LED_BUILTIN, OUTPUT);     // configure output for onboard LED
}

int loopCount = 0;

void loop() {
    digitalWrite(LED_BUILTIN, HIGH);  // turn the onboard LED on (HIGH is the voltage level)
    delay(5);                         // wait for 5 milliseconds
    digitalWrite(LED_BUILTIN, LOW);   // turn the onboard LED off
    delay(500);                       // wait for 500 milliseconds
    Serial.print("loopCount = ");
    Serial.println(++loopCount);
}