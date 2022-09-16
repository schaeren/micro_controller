#include "Arduino.h"
#include "avr8-stub.h"
#include "app_api.h" // only needed with flash breakpoints

double cycleTime;
double dutyCycle;
double step;
bool increase;

void setup() {
    cycleTime = 10.0; // Duration [ms] of a cycle consisting of one light and one dark phase
    dutyCycle = 0.0;  // duty cycle light on vs. off during one cycle [0.0...1.0]
    step = 0.01;      // dutyCycle increment between two cycles
    increase = true;  // true -> light becomes brighter / false -> light becomes darker 

    pinMode(LED_BUILTIN, OUTPUT);
    debug_init();
}

// LED periodically becomes brighter and darker again.
// Duration from dark to bright or vice versa (time of a half period): (1/step)*cycleTime [ms] aprox.
void loop() {
    int on = dutyCycle * cycleTime;
    int off = (1.0 - dutyCycle) * cycleTime;
    digitalWrite(LED_BUILTIN, HIGH);
    delay(on);
    digitalWrite(LED_BUILTIN, LOW);
    delay(off);
    dutyCycle += increase ? step : -step;
    if (dutyCycle <= 0.0) {
        dutyCycle = 0.0;
        increase = !increase;
    }
    else if (dutyCycle >= 1.0) {
        dutyCycle = 1.0;
        increase = !increase;
    }
}