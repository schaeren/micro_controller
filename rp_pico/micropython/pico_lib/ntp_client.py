import struct
import time
import machine
import uasyncio as asyncio

from .settings_base import Settings_Base
from .networking import Network_Utilities
from .udp_client import Udp_Client
from .iso8601 import Iso8601
from .logging_enhanced import Logger_Enhanced
_logger =  Logger_Enhanced.get_logger_for_module(__name__) 


class _Settings(Settings_Base):
    def __init__(self) -> None:
        super().__init__()
        self.host = 'time.google.com'
        self.interval_secondes = 3600 * 6

class Ntp_Client:
    NTP_PORT = 123
    NTP_QUERY = '\x1b' + 47*'\0'
    NTP_EPOCH = 2208988800

    def __init__(self, settings_file_path = 'config/app_settings.json') -> None:
        self._settings = _Settings()
        self._settings.load(__name__, settings_file_path, 'ntp')
        _logger.info(self._settings.get_settings_as_text(intro_text = f'Settings for {type(self)}:'))
        self._udp = Udp_Client()

    async def synch_time(self):
        _logger.debug(f'Getting time from NTP server ...')
        addr = Network_Utilities.get_address(self._settings.host, self.NTP_PORT)
        response = await self._udp.send_and_receive(self.NTP_QUERY, 48, addr[0], self.NTP_PORT)
        if response:
            val = struct.unpack("!I", response[40:44])[0]
            t = val - self.NTP_EPOCH
            tm = time.gmtime(t)
            rtc = machine.RTC()
            oldTime = rtc.datetime()
            # Set date/time of Pico's RTC
            rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
            _logger.info(f"Synchronized RTC with NTP server '{self._settings.host}', datetime = {Iso8601.formatTimeGmtimeToIso(tm)}.")
            _logger.debug(f'rtc.datetime() before sync = {Iso8601.formatRtcDatetimeToIso(oldTime)}.')
            _logger.debug(f'rtc.datetime() after sync  = {Iso8601.formatRtcDatetimeToIso(rtc.datetime())}.')
            _logger.debug(f'time.gmtime()  after sync  = {Iso8601.formatTimeGmtimeToIso(time.gmtime())}.')
        else:
            _logger.error(f"Failed to get time from NTP server '{self._settings.host}'.")

    async def start_synch_task(self):
        '''Start task to synchonize periodically Pico's RTC with NTP server.'''
        try:
            # The first synchronization must be performed immediately (i.e. synchronously) to ensure 
            # that the RTC is synchronized as quickly as possible.
            await self.synch_time()
            asyncio.create_task(self._synch_task())
        except BaseException as err:
            _logger.error(f'Failed to start synch task: {err}, {type(err)}')
            raise

    async def _synch_task(self):
        '''Synchronize periodically RTC with NTP server.'''
        while True:
            await asyncio.sleep(self._settings.interval_secondes)
            try:
                await self.synch_time()
            except Exception as err:
                _logger.error(f"_synch_task(): Unexpected error while synchronizing with NTP server '{self._settings.host}': {err}, {type(err)}")
