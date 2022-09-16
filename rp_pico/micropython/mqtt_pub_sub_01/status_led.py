import uasyncio as asyncio
import time
import _thread
from machine import Pin

from pico_lib import Logger_Enhanced
_logger =  Logger_Enhanced.get_logger_for_module(__name__) 

class MQTT_Client_Status:
    undefined = 0
    connecting_wifi = 1
    synchronizing_rtc = 2
    resolving_hostname = 3
    connecting_mqtt_server = 4
    connected_mqtt_server = 5
    connection_interrupted = 6


class Status_Led:
    '''Display status with blinking LED during application startup.
    
    - 2 flashes about every half second -> connecting to WiFi.
    - 3 flashes about every half second -> synchronizing RTC with NTP server.
    - LED on -> connection to MQTT broker, including TLS handshake.
    - 1 flash about every 2 secons -> connected to MQTT broker.
    - blinking 500ms/500ms -> connection is interrupted, trying to reconnect.
    '''
    def __init__(self) -> None:
        self._status = MQTT_Client_Status.undefined
        self._led = Pin('LED', Pin.OUT, value = 0)

    def start(self):
        try:
            _logger.debug(f'Starting {__name__} task ...')
            asyncio.create_task(self._update_tatus_led_task())
            pass
        except Exception as err:
            _logger.error(f'Status LED updater task failed: err={err}, type={type(err)}')

    def set_status(self, status):
        self._status = status

    async def _update_tatus_led_task(self):
        while True:
            if self._status == MQTT_Client_Status.undefined:
                self._led.off()
            elif self._status == MQTT_Client_Status.connecting_wifi:
                await self.blink(2)
            elif self._status == MQTT_Client_Status.synchronizing_rtc:
                await self.blink(3)
            elif self._status == MQTT_Client_Status.connecting_mqtt_server:
                self._led.on()
            elif self._status == MQTT_Client_Status.connected_mqtt_server:
                await self.blink(1, off_time=2000)
            elif self._status == MQTT_Client_Status.connection_interrupted:
                await self.blink(1, on_time=1000, off_time=1000, last_off_time=1000)
            else:
                self._led.off()
            await asyncio.sleep_ms(10)

    async def blink(self, count, on_time = 10, off_time = 100, last_off_time = 500):
        for i in range(count):
            self._led.on()
            await asyncio.sleep_ms(on_time)
            self._led.off()
            await asyncio.sleep_ms(off_time)
        await asyncio.sleep_ms(last_off_time - off_time)
