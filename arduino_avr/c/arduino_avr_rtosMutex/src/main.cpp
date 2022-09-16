#include <Arduino.h>
#include <Arduino_FreeRTOS.h>
#include <semphr.h>

uint8_t redLedPin = 4;         // Output for red LED
uint8_t yellowLedPin = 3;      // Output for yellow LED
uint8_t redPotPin = A0;         // ADC input for potentiometer for red LED
uint8_t yellowPotPin = A1;      // ADC input for potentiometer for yellow LED

// Configuration
const long delayBeforeAdcRead = 1; // Wait time before ADC is read in ticks (1 tick = 15ms)
                                   // Remark: A short recovery time between the reading of  
                                   // different ADC channels leads to more stable results.
const long minDelay = portTICK_PERIOD_MS; // Min. delay = min. half period time for LED flashing in ms
const long maxDelay = 1000;        // Max. delay = max. half period time for LED flashing in ms

// Half period time for LEDs, access is protected by mutex
SemaphoreHandle_t delaysMutex;
int16_t delayRed = -1;      // ms
int16_t delayYellow = -1;   // ms

// struct used for task parameters
struct TaskParams_t {
    uint8_t ledPin;
    int16_t* delayTime;
};

TaskParams_t taskRedBlinkyParams = {
    .ledPin = redLedPin, 
    .delayTime = &delayRed
};
TaskParams_t taskYellowBlinkyParams = {
    .ledPin = yellowLedPin, 
    .delayTime = &delayYellow
};

void TaskAnalogIn([[maybe_unused]] void *pvParameters )
{
    pinMode(redPotPin, INPUT);
    pinMode(yellowPotPin, INPUT);

    // Temporary local variables for delay times [ms], at the end of a loop 
    // these values will be written to global variables, too.
    int16_t _delayRed = 0, _delayYellow = 0;

    for (;;) {
        // Get delay for red LED by reading voltage potentiometer 'red'
        vTaskDelay(delayBeforeAdcRead);                             // Wait a short time to stabilize the ADC value
        int potRedValue = analogRead(redPotPin);                    // Read value from ADC
        _delayRed = map(potRedValue, 0, 1023, minDelay, maxDelay);  // normalize ADC value to 16...1000
        
        // Get delay for yellow LED by reading voltage potentiometer 'yellow'
        vTaskDelay(delayBeforeAdcRead);                             // Wait a short time to stabilize the ADC value
        int potYellowValue = analogRead(yellowPotPin);              // Read value from ADC
        _delayYellow = map(potYellowValue, 0, 1023, minDelay, maxDelay); // normalize ADC value to 16...1000

        // Write normalized values to global variables, access is protected by mutex 
        // (to be used as delay times [ms])
        if (xSemaphoreTake(delaysMutex, portMAX_DELAY) == pdTRUE) {
            delayRed = _delayRed;
            delayYellow = _delayYellow;
            xSemaphoreGive(delaysMutex);
        }
    }
}

void TaskBlinky([[maybe_unused]] void *pvParameters )
{
    TaskParams_t* param = (TaskParams_t *) pvParameters;
    uint8_t ledPin = param->ledPin;

    pinMode(ledPin, OUTPUT);

    for (;;) {
        // Get delay time [ms] from global varibale, access is protected by mutex.
        int16_t _delayTime;
        if (xSemaphoreTake(delaysMutex, portMAX_DELAY) == pdTRUE) {
            _delayTime = *(param->delayTime);
            xSemaphoreGive(delaysMutex);
        }
        if (_delayTime != -1) {
            digitalWrite(ledPin, !digitalRead(ledPin));
            long _delayTicks = _delayTime / portTICK_PERIOD_MS;
            vTaskDelay(_delayTicks);
        }
    }
}

void setup() {
    UBaseType_t taskPriority = configMAX_PRIORITIES - 1 ;

    // Create/initialize mutex (semaphore).
    delaysMutex = xSemaphoreCreateMutex();

    // Create/start tasks.
    xTaskCreate(
        TaskAnalogIn,           // task function
        "TaskAnalogIn",         // task name
        200,                    // stack size
        NULL,                   // paramater for task
        taskPriority,           // task priority
        NULL );                 // task handle

    xTaskCreate(
        TaskBlinky,             // task function
        "TaskBlinky-red",       // task name
        150,                    // stack size
        &taskRedBlinkyParams,   // paramater for task
        taskPriority,           // task priority
        NULL );                 // task handle

    xTaskCreate(
        TaskBlinky,             // task function
        "TaskBlinky-yellow",    // task name
        150,                    // stack size
        &taskYellowBlinkyParams,// paramater for task
        taskPriority,           // task priority
        NULL );                 // task handle
}

void loop() {
    // idle task
}