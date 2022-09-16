#include <Arduino.h>
#include <Arduino_FreeRTOS.h>

uint8_t redLedPin = 4;      // output for red LED
uint8_t yellowLedPin = 3;   // output for yellow LED
uint8_t redPotPin = A0;     // ADC input for potentiometer for red LED
uint8_t yellowPotPin = A1;  // ADC input for potentiometer for yellow LED

// struct used for task parameters
struct TaskParams_t {
    uint8_t ledPin;
    uint8_t potPin;
};

// Prepare task parameters
TaskParams_t taskRedBlinkyParams = {
    .ledPin = redLedPin, 
    .potPin = redPotPin
};
TaskParams_t taskYellowBlinkyParams = {
    .ledPin = yellowLedPin, 
    .potPin = yellowPotPin
};

void TaskBlinky([[maybe_unused]] void *pvParameters )
{
    TaskParams_t* param = (TaskParams_t *) pvParameters;
    uint8_t ledPin = param->ledPin;
    uint8_t potPin = param->potPin;
    pinMode(ledPin, OUTPUT);
    pinMode(potPin, INPUT);

    for (;;) {
        digitalWrite(ledPin, !digitalRead(ledPin));
        long potValue = analogRead(potPin);
        vTaskDelay((25 + potValue) / portTICK_PERIOD_MS);  // min. delay = 25ms
    }
}

void setup() {
    UBaseType_t taskPriority = configMAX_PRIORITIES - 1 ;

    xTaskCreate(
        TaskBlinky,             // task function
        "TaskBlinky-red",       // task name
        100,                    // stack size (bytes)
        &taskRedBlinkyParams,   // paramater for task
        taskPriority,           // task priority
        NULL );                 // task handle

    xTaskCreate(
        TaskBlinky,             // task function
        "TaskBlinky-yellow",    // task name
        100,                    // stack size (bytes)
        &taskYellowBlinkyParams,// paramater for task
        taskPriority,           // task priority
        NULL );                 // task handle
}

void loop() {
    // idle task
}