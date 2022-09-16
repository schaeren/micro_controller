#include <Arduino.h>
#include <Arduino_FreeRTOS.h>
#include <semphr.h>
#include <queue.h>

#define ARDUINO_UNO 1
#define ARDUINO_MEGA 2
#if BOARD == ARDUINO_UNO
const configSTACK_DEPTH_TYPE stackTaskBlinky = 70;
const configSTACK_DEPTH_TYPE stackTaskAnalogIn = 80;
const configSTACK_DEPTH_TYPE stackTaskLogWriter = 110;
#elif BOARD == ARDUINO_MEGA // Stack sizes with 100% reseve
const configSTACK_DEPTH_TYPE stackTaskBlinky = 70 * 2;
const configSTACK_DEPTH_TYPE stackTaskAnalogIn = 80 * 2;
const configSTACK_DEPTH_TYPE stackTaskLogWriter = 110 * 2;
#endif

uint8_t redLedPin = 4;          // Output for red LED
uint8_t yellowLedPin = 3;       // Output for yellow LED
uint8_t redPotPin = A0;         // ADC input for potentiometer for red LED
uint8_t yellowPotPin = A1;      // ADC input for potentiometer for yellow LED

// Configuration
const long delayBeforeAdcRead = 1; // Wait time before ADC is read in ticks (1 tick = 15ms)
                                   // Remark: A short recovery time between the reading of  
                                   // different ADC channels leads to more stable results.
const long minDelay = portTICK_PERIOD_MS; // Min. delay = min. half period time for LED flashing in ms
const long maxDelay = 1000;        // Max. delay = max. half period time for LED flashing in ms
const long minDelayDiff = 5;       // Min. difference so that delay change is written logQueue in ms

// Half period time for LEDs, access is protected by mutex
SemaphoreHandle_t delaysMutex;
int16_t delayRed = -1;      // ms
int16_t delayYellow = -1;   // ms

// Messag queue for delay times
QueueHandle_t delaysQueue;
UBaseType_t delaysQueueLen = 3;
struct DelaysQueueEntry_t {
    int16_t delayRed;
    int16_t delayYellow;
};

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

void sendTextToLogQueue (const char* format, ...);

void TaskAnalogIn([[maybe_unused]] void *pvParameters )
{
    int16_t _oldDelayRed = 0;
    int16_t _oldDelayYellow = 0;

    pinMode(redPotPin, INPUT);
    pinMode(yellowPotPin, INPUT);

    // Temporary local variables for delay times [ms], at the end of a loop 
    // these values will be written to global variables, too.
    int16_t _delayRed = 0, _delayYellow = 0;

    for (;;) {
        // Get delay for red LED
        vTaskDelay(delayBeforeAdcRead);
        int potRedValue = analogRead(redPotPin);
        _delayRed = map(potRedValue, 0, 1023, minDelay, maxDelay);

        // Get delay for yellow LED
        vTaskDelay(delayBeforeAdcRead);
        int potYellowValue = analogRead(yellowPotPin);
        _delayYellow = map(potYellowValue, 0, 1023, minDelay, maxDelay);

        if (abs(_delayRed - _oldDelayRed) > minDelayDiff || abs(_delayYellow - _oldDelayYellow) > minDelayDiff) {
            _oldDelayRed = _delayRed;
            _oldDelayYellow = _delayYellow;
            // Write delay times [ms] to global variables, access is protected by mutex.
            if (xSemaphoreTake(delaysMutex, portMAX_DELAY) == pdTRUE) {
                delayRed = _delayRed;
                delayYellow = _delayYellow;
                xSemaphoreGive(delaysMutex);
            }
            DelaysQueueEntry_t message = {
                .delayRed = _delayRed,
                .delayYellow = _delayYellow
            };
            if (xQueueSendToBack(delaysQueue, (void*) &message, portMAX_DELAY) != pdPASS) {
                Serial.println("Failed to send message to queue 'delaysQueue'!");
            }
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

void TaskLogWriter([[maybe_unused]] void *pvParameters )
{
    DelaysQueueEntry_t message;
    for (;;) {
        if (xQueueReceive(delaysQueue, (void*) &message, portMAX_DELAY) == pdTRUE) {
            char text[50];
            sprintf(text, "red: %-4d ms, yellow: %-4d ms.", message.delayRed, message.delayYellow);
            Serial.println(text);
        } else {
            Serial.println("Task TaskLogWriter: Failed to receive message from queue 'delaysQueue'!");
        }
    }
}

void setup() {
    Serial.begin(115200);
    while (!Serial); 

    UBaseType_t taskPriority = configMAX_PRIORITIES - 1 ;

    // Create/initialize mutex (semaphore).
    delaysMutex = xSemaphoreCreateMutex();

    // Create queue
    delaysQueue = xQueueCreate(delaysQueueLen, sizeof(DelaysQueueEntry_t));
    if (delaysQueue == NULL) {
        Serial.println("Failed to create queue 'delaysQueue'!");
    }

    // Create/start tasks.
    xTaskCreate(
        TaskLogWriter,          // task function
        "TaskLogWriter",        // task name
        stackTaskLogWriter,     // stack size
        NULL,                   // paramater for task
        taskPriority + 1,       // task priority (higher than other tasks!)
        NULL );                 // task handle

    xTaskCreate(
        TaskAnalogIn,           // task function
        "TaskAnalogIn",         // task name
        stackTaskAnalogIn,      // stack size
        NULL,                   // paramater for task
        taskPriority,           // task priority
        NULL );                 // task handle

    xTaskCreate(
        TaskBlinky,             // task function
        "TaskBlinky-red",       // task name
        stackTaskBlinky,        // stack size
        &taskRedBlinkyParams,   // paramater for task
        taskPriority,           // task priority
        NULL );                 // task handle

    xTaskCreate(
        TaskBlinky,             // task function
        "TaskBlinky-yellow",    // task name
        stackTaskBlinky,        // stack size
        &taskYellowBlinkyParams,// paramater for task
        taskPriority,           // task priority
        NULL );                 // task handle
}

void loop() {
    // idle task
}
