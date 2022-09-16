import uasyncio as asyncio
import time
from machine import Pin, RTC

from pico_lib import Wifi, Ntp_Client, MQTTClient_enhanced, Network_Utilities
from pico_lib import Iso8601, Button_Debounced, Logger_Enhanced
_logger =  Logger_Enhanced.get_logger_for_module(__name__) 
from status_led import MQTT_Client_Status, Status_Led


class Mqtt_Subscriber:
    def __init__(self) -> None:
        MQTTClient_enhanced.DEBUG = True  # Optional
        self._client = MQTTClient_enhanced()
        self._client.register_connection_state_changed_handler(self._on_connection_state_changed)
        self._client.register_connection_established_handler(self._on_connection_established)
        self._status_led = Status_Led()
        self._status_led.start()

        self._led_red    = Pin(16, Pin.OUT, value = 0)
        self._led_yellow = Pin(17, Pin.OUT, value = 0)
        self._led_green  = Pin(18, Pin.OUT, value = 0)

        self._button_red    = Button_Debounced(19, self._on_button_changed, 'button_red')
        self._button_yellow = Button_Debounced(20, self._on_button_changed, 'button_yellow')
        self._button_green  = Button_Debounced(21, self._on_button_changed, 'button_green')

    def start(self):
        '''Start async main program.'''
        try:
            asyncio.run(self._main())
        except Exception as err:
            _logger.error(f'Program terminated: exception. err={err}, type={type(err)}.')
            raise
        except BaseException as err:
                _logger.error(f'Program terminated: UNEXPECTED exception. err={err}, type={type(err)}.')
        finally:
            _logger.info("**** PROGRAM TERMINATED ****")
            self._client.close()  # Prevent LmacRxBlk:1 errors
            asyncio.new_event_loop()

    async def _main(self):
        '''This is the async main program.'''
        # Connect to WiFi ...
        self._status_led.set_status(MQTT_Client_Status.connecting_wifi)
        wifi = Wifi()
        await wifi.connect(check_connection = False)

        # Synchronize RTC with time server ...
        self._status_led.set_status(MQTT_Client_Status.synchronizing_rtc)
        ntp_client = Ntp_Client()
        await ntp_client.start_synch_task()

        # Check if MQTT hostname can be resolved ...
        self._status_led.set_status(MQTT_Client_Status.connecting_mqtt_server)
        host_name = self._client.get_host()
        if not Network_Utilities.get_address(host_name):
            err = f"Failed to resolve IP address for MQTT host '{host_name}'."
            _logger.error(err)
            raise RuntimeError(err)

        # Connect to MQTT host ...
        await self._client.connect()
        self._status_led.set_status(MQTT_Client_Status.connected_mqtt_server)

        # Main loop does nothing ...
        while True:
            await asyncio.sleep(3600)

    async def _on_connection_state_changed(self, is_connected):
        '''Called every time the connection state to MQTT broker has changed.'''
        if is_connected:
            _logger.info(f"Connection to MQTT broker '{self._client.get_host()}' is ESTABLISHED.")
            self._status_led.set_status(MQTT_Client_Status.connected_mqtt_server)
        else:
            _logger.warning(f"Connection to MQTT broker '{self._client.get_host()}' is INTERRUPTED.")
            self._status_led.set_status(MQTT_Client_Status.connection_interrupted)

    async def _on_connection_established(self, client):
        '''Called upon connection to MQTT server has been established.'''
        _logger.info("Subscribing MQTT topic 'inputs/#' ...")
        await client.subscribe('inputs/#', self._led_handler)

    def _led_handler(self, topic, msg, retained):
        _logger.debug(f'Receiced message for topic {topic.decode()}: {msg.decode()}.')
        topic_segments = topic.decode().split('/')
        if topic_segments[2] == 'isPressed':
            is_on = msg == 'True'
            if topic_segments[1] == 'button0':
                self._switch_led(self._led_red, is_on)
            elif topic_segments[1] == 'button1':
                self._switch_led(self._led_yellow, is_on)
            elif topic_segments[1] == 'button2':
                self._switch_led(self._led_green, is_on)
        elif topic_segments[2] == 'lastChangedAt':
            _logger.info(f"Button '{topic_segments[1]} changed at {msg.decode()}.'")

    def _switch_led(self, led, is_on):
        if is_on == True:
            led.on()
        else:
            led.off()

    async def _on_button_changed(self, name, state):
        _logger.debug(f"Calling button callback for {name}, state {state}.")
        topic_1 = ''
        value_1 = 'True' if state == 0 else 'False'
        topic_2 = ''
        value_2 = Iso8601.formatRtcDatetimeToIso(RTC().datetime())
        if name == 'button_red':
            topic_1 = 'inputs/button0/isPressed'
            topic_2 = 'inputs/button0/lastChangedAt'
        elif name == 'button_yellow':
            topic_1 = 'inputs/button1/isPressed'
            topic_2 = 'inputs/button1/lastChangedAt'
        elif name == 'button_green':
            topic_1 = 'inputs/button2/isPressed'
            topic_2 = 'inputs/button2/lastChangedAt'
        _logger.info(f'Publishing topic={topic_1}, value={value_1} ...')
        await self._client.publish(topic_1, value_1, qos = 1)
        _logger.info(f'Publishing topic={topic_2}, value={value_2} ...')
        await self._client.publish(topic_2, value_2, qos = 1)


import micropython
micropython.alloc_emergency_exception_buf(100)
Mqtt_Subscriber().start()
