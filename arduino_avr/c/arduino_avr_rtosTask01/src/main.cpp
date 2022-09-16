#include <Arduino.h>
#include <Arduino_FreeRTOS.h>

uint8_t redLedPin = 4;      // output for red LED
uint8_t yellowLedPin = 3;   // output for yellow LED
uint8_t redPotPin = A0;     // ADC input for potentiometer for red LED
uint8_t yellowPotPin = A1;  // ADC input for potentiometer for yellow LED

void TaskRedBlinky([[maybe_unused]] void *pvParameters )
{
    pinMode(redLedPin, OUTPUT);
    pinMode(redPotPin, INPUT);

    for (;;) {
        digitalWrite(redLedPin, !digitalRead(redLedPin));
        long potValue = analogRead(redPotPin);
        vTaskDelay((25 + potValue) / portTICK_PERIOD_MS);  // min. delay = 25ms
    }
}

void TaskYellowBlinky([[maybe_unused]] void *pvParameters )
{
    pinMode(yellowLedPin, OUTPUT);
    pinMode(yellowPotPin, INPUT);

    for (;;) {
        digitalWrite(yellowLedPin, !digitalRead(yellowLedPin));
        long potValue = analogRead(yellowPotPin);
        vTaskDelay((25 + potValue) / portTICK_PERIOD_MS);  // min. delay = 25ms
    }
}

void setup() {
    Serial.begin(115200);
    Serial.print("configMAX_PRIORITIES = ");
    Serial.println(configMAX_PRIORITIES);
    UBaseType_t taskPriority = configMAX_PRIORITIES - 1 ;

    xTaskCreate(
        TaskRedBlinky,      // task function
        "TaskRedBlinky",    // task name
        100,                // stack size (bytes)
        NULL,               // paramater for task
        taskPriority,       // task priority
        NULL );             // task handle

    xTaskCreate(
        TaskYellowBlinky,   // task function
        "TaskYellowBlinky", // task name
        100,                // stack size (bytes)
        NULL,               // paramater for task
        taskPriority,       // task priority
        NULL );             // task handle
}

void loop() {
    // idle task
}