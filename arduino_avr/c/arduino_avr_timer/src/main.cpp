#include "Arduino.h"

const int greenLedPin = 10; // green LED
const int redLedPin = 13;   // red LED (and onboard LED)

// Start value for timer1, i.e timer/counter runs from this value up to 2^16-1 and then 
// restarts with 0 (=overflow). Each overflow creates a Timer Overflow Interrupt. The 
// interrupt handler will set the timer/counter again to this value.
//   65535 = 2^16 - 1  is the max value for timer/counter 1
//   16000000 is the CPU clock frequency (16 MHz)
//   1024 is the prescaler value set for timer/counter 1 (see initTimer1())
//
// timer-irq-freq = system-clock-freq / (prescaler * (65535 - timer2CompareValue + 1))
// => timer2CompareValue = 65535 + 1 - (system-clock-frq / (precaler * timer-irq-freq))
//
const unsigned int timer1StartValue = 65535 + 1 - (16000000 / (1024 * 1)); // = 49911

// Compare value for timer2, i.e timer/counter runs from 0 up to this value and then 
// restarts with 0. Each time this value is reached a Timer Compare Match Interrupt is
// created. 
//   16000000 is the CPU clock frequency (16 MHz)
//   100 divisor to get 10ms intervals
//   1024 is the prescaler value set for timer/counter 1 (see initTimer1())
//
// timer-irq-freq = system-clock-freq / (prescaler * (1 + timer2CompareValue))
// => timer2CompareValue = (system-clock-freq / (timer-irq-freq * prescaler)) - 1
// timer-irq-frq = (16000000 / (100 * 1025)) -1 = 155.25 -> 155
// timer-irq-freq = 16000000 / (1024 * (1 + 155)) = 100.160 Hz -> period = 9.984 ms
//
const unsigned short timer2CompareValue = (16000000 / 100 / 1024) - 1; // = 155

unsigned int timer2CycleCounter = 0;

void initTimer1() {
    // Diable all interrupts (temporarily)
    noInterrupts();

    // Timer/Counter Control Register A of timer1
    TCCR1A = 0; // mode = Normal, i.e. WGM11..WGM10 = 00 (Waveform Generation Mode)
                // outputs OC1A and OC1B are disconnected
    // Timer/Counter Control Register B of timer1
    TCCR1B = 0; // mode = normal, i.e. WGM13..WGM12 = 00 (Waveform Generation Mode) 
    TCCR1B |= 1 << CS12 | 1 << CS10; // Prescaler = 1024, i.e. CS12..CS10 = 101
    // Timer/Counter value register of timer1
    TCNT1 = timer1StartValue; // set start value for timer/counter 1
    // Timer/Counter Interrupt Mask Register of timer1
    TIMSK1 |= 1 << TOIE1; // enable Timer Overflow Interrupt  
    
    // Enable interrupts again
    interrupts();
}

void initTimer2() {
    // Diable all interrupts (temporarily)
    noInterrupts();

    // Timer/Counter Control Register A of timer2
    TCCR2A = 0;
    TCCR2A |= 1 << WGM21; // mode = CTC, i.e. WGM21..WGM20 = 10 (Waveform Generation Mode)
                          // CTC: Clear Timer on Compare Match
                          // outputs OC2A and OC2B are disconnected
    // Timer/Counter Control Register B of timer2
    TCCR2B = 0;  // mode = CTC, i.e. WGM22 = 0 (Waveform Generation Mode) 
    TCCR2B |= 1 << CS22 | 1 << CS21 | 1 >> CS20; // Prescaler = 1024, i.e. CS22..CS20 = 111
    // Output Compare Register A for timer2
    OCR2A = timer2CompareValue;
    // Timer/Counter value register of timer2
    TCNT2 = 0; // set start value for timer/counter 2
    // Timer/Counter Interrupt Mask Register of timer2
    TIMSK2 |= 1 << OCIE2A; // enable Timer Overflow Interrupt  
    
    // Enable interrupts again
    interrupts();
}

ISR(TIMER1_OVF_vect)        
{
    TCNT1 = timer1StartValue;
    Serial.print("Timer1: ");
    Serial.println(millis());
    digitalWrite(greenLedPin, digitalRead(greenLedPin) ^ 1);
}

ISR(TIMER2_COMPA_vect) {
    if (++timer2CycleCounter == 100) {
        timer2CycleCounter = 0;
        Serial.print("Timer2: ");
        Serial.println(millis());
        digitalWrite(redLedPin, digitalRead(redLedPin) ^ 1);
    }
}

void setup() { 
    pinMode(greenLedPin, OUTPUT);
    pinMode(redLedPin, OUTPUT);
    Serial.begin(115200);
    Serial.print("timer1StartValue = ");
    Serial.println(timer1StartValue);
    Serial.print("timer2CompareValue = ");
    Serial.println(timer2CompareValue);
    initTimer1();
    initTimer2();
}

void loop() {
}
