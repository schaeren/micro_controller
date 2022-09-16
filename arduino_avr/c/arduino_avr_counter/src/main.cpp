#include "Arduino.h"

unsigned long gCount = 0;

void initCounter1() {
    // Diable all interrupts (temporarily)
    noInterrupts();

    // Timer/Counter Control Register A of timer/counter 1
    TCCR1A = 0; // mode = Normal, i.e. WGM11..WGM10 = 00 (Waveform Generation Mode)
                // outputs OC1A and OC1B are disconnected
    // Timer/Counter Control Register B of timer/counter 1
    TCCR1B = 0; // mode = Normal, i.e. WGM13..WGM12 = 00 
    TCCR1B |= 1 << CS12 | 1 << CS11 | 1 << CS10; // no prescaler, use external clock, rising edge
    // Timer/Counter value register of timer/counter 1
    TCNT1 = 0; // set start value for counter
    
    // Enable interrupts again
    interrupts();
}

void setup() { 
    Serial.begin(115200);
    initCounter1();
}

void loop() {
    unsigned int count = TCNT1;
    if (gCount < count) {
        gCount = count;        
        Serial.println(gCount);
    }
    delay(10);
}
