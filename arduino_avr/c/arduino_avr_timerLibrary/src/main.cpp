#include "Arduino.h"
#include "arduino-timer.h"

const int greenLedPin = 10; // green LED
const int redLedPin = 13;   // red LED
const int buttonPin = 2;    // button

// Delay to be used to debounce button [ms]
unsigned long debouncingTime = 100;

// timer is a 'software timer'. <2> indicates that up to 2 instances may be used concurrently. 
// One interval timer is used for green LED and one single-shot timer is used for red LED.
// For more information see also https://github.com/contrem/arduino-timer
Timer<2> timer;

unsigned long lastButtonDownTime = 0;

bool onSwitchOffRedLed(void *);

void onButtonDown() {
    unsigned int now = millis();
    if (now - lastButtonDownTime > debouncingTime) {
        Serial.print("Button DOWN, last call to onButtonDown() at ");
        Serial.print(lastButtonDownTime);
        Serial.print("ms - current time is ");
        Serial.print(now);
        Serial.println("ms");

        lastButtonDownTime = now;
        digitalWrite(redLedPin, HIGH);
        timer.in(2000, onSwitchOffRedLed);
    }
}

bool onSwitchOffRedLed(void *) {
    digitalWrite(redLedPin, LOW);
    return false; // stop timer
}

bool onTimer(void *) {
    digitalWrite(greenLedPin, !digitalRead(greenLedPin));
    return true; // keep timer running
}

void setup() { 
    pinMode(greenLedPin, OUTPUT);
    pinMode(redLedPin, OUTPUT);
    pinMode(buttonPin, INPUT_PULLUP);
    Serial.begin(115200);
    attachInterrupt(digitalPinToInterrupt(buttonPin), onButtonDown, FALLING);
    timer.every(100, onTimer); // timer for green led (blicking with 5Hz)

    Serial.println("START...:");
}

void loop() {
    timer.tick();
}
