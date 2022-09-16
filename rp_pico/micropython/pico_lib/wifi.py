import uasyncio as asyncio
import network

from .settings_base import Settings_Base
from .iso8601 import Iso8601
from .logging_enhanced import Logger_Enhanced
_logger =  Logger_Enhanced.get_logger_for_module(__name__) 

class _Settings(Settings_Base):
    def __init__(self) -> None:
        super().__init__()
        self.ssid = ''
        self.password = ''

class Wifi:
    '''Set up WiFi/WLAN.'''
    
    def __init__(self, settings_file_path = 'secret/app_secrets.json'):
        '''Create WiFi instance.
        
        Requires settings file with WiFi SSID and password.
        '''
        self._settings = _Settings()
        self._settings.load(__name__, settings_file_path, 'wifi')
        _logger.info(self._settings.get_settings_as_text(intro_text = f'Settings for {type(self)}:'))
        self._sta_if = network.WLAN(network.STA_IF)

    def get_status(self):
        return self._sta_if.status()

    def disconnect(self):
        self._sta_if.disconnect()

    async def connect(self, *, check_connection = True):
        '''Connect to WiFi network.
        
        Optionally check if connection is stable (during a few seconds).
        Supports only RP2.
        Code partially copied from mqtt_as.
        '''
        wifi = self._sta_if
        wifi.active(True)
        # If we are already connected to the right WiFi (SSID) -> reuse connection.
        wifi_status = wifi.status()
        if wifi_status == 3:
            if wifi.config('ssid') == self._settings.ssid:
                _logger.info(f'Already connected to WiFi with SSID \'{self._settings.ssid}\'.')
                return
        if wifi_status != 0:
            wifi.disconnect()
            asyncio.sleep_ms(500)
            
        # See https://datasheets.raspberrypi.com/picow/connecting-to-the-internet-with-pico-w.pdf
        # See chapter 3.6.3. Power-saving mode.
        wifi.config(pm = 0xa11140)
        _logger.info(f'Connecting to WiFi with SSID \'{self._settings.ssid}\' ...')
        wifi.connect(self._settings.ssid, self._settings.password)
        max_time_to_connect = 60
        for _ in range(max_time_to_connect):
            await asyncio.sleep(1)
            if wifi.isconnected():
                break
            if not 1 <= wifi.status() <= 2:
                break
        else:
            wifi.disconnect()
            await asyncio.sleep(1)
        if not wifi.isconnected():  # Timed out
            _logger.warning(f'Timeout while connecting to WiFi with SSID \'{self._settings.ssid}\'.')
            raise OSError('Failed to connect to WiFi.')
        _logger.info(f'Connected successfully to WiFi with SSID \'{self._settings.ssid}\'.')

        if check_connection:
            # Ensure connection stays up for a few secs.
            _logger.info('Checking WiFi integrity ...')
            for _ in range(5):
                if not wifi.isconnected():
                    _logger.error(f'WiFi connection is unstable!')
                    raise OSError('WiFi connection is unstable')  # in 1st 5 secs
                await asyncio.sleep(1)
            _logger.info('Wifi connection is reliable.')        
