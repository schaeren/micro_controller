#include "Arduino.h"

#define DEBUG

const int ledPin = 13;                  // pin used for LED (same as on-board led)
const int buttonPin = 2;                // pin used for button
unsigned long debouncingTime = 20;      // delay used to debouncing button press & release [ms]
unsigned long lastButtonChangeTime = 0; // time of 1st interrupt when button pressed/released

void onButtonUp();

void onButtonDown() {
    unsigned long now = millis();
    if (now - lastButtonChangeTime > debouncingTime) {
        #ifdef DEBUG
        Serial.print("onButtonDown(): lastBottonChangeTime: ");
        Serial.print(lastButtonChangeTime);
        Serial.print("ms - current time: ");
        Serial.print(now);
        Serial.println("ms");
        #endif

        lastButtonChangeTime = now;
        digitalWrite(ledPin, HIGH);
        // Switch to button release interrupt
        detachInterrupt(digitalPinToInterrupt(buttonPin));
        attachInterrupt(digitalPinToInterrupt(buttonPin), onButtonUp, RISING);
    }
}

void onButtonUp() {
    unsigned long now = millis();
    if (now - lastButtonChangeTime > debouncingTime) {
        #ifdef DEBUG
        Serial.print("onButtonUp(): lastBottonChangeTime: ");
        Serial.print(lastButtonChangeTime);
        Serial.print("ms - current time: ");
        Serial.print(now);
        Serial.print("ms - button press time: ");
        Serial.print(now - lastButtonChangeTime);
        Serial.println("ms");
        #endif

        lastButtonChangeTime = now;
        digitalWrite(ledPin, LOW);
        // Switch to button press interrupt
        detachInterrupt(digitalPinToInterrupt(buttonPin));
        attachInterrupt(digitalPinToInterrupt(buttonPin), onButtonDown, FALLING);
    }
}

void setup() { 
    pinMode(ledPin, OUTPUT);
    pinMode(buttonPin, INPUT_PULLUP);
    #ifdef DEBUG
    Serial.begin(115200);
    Serial.print("debouncingTime: ");
    Serial.print(debouncingTime);
    Serial.println("ms");
    #endif

    // Enable button press interrupt
    attachInterrupt(digitalPinToInterrupt(buttonPin), onButtonDown, FALLING);
}

void loop() {
}
