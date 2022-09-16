import usocket as socket
from uerrno import ETIMEDOUT, EAGAIN
import time
from utime import ticks_ms
import uasyncio as asyncio

from .logging_enhanced import Logger_Enhanced
_logger =  Logger_Enhanced.get_logger_for_module(__name__) 

class Udp_Client:
    MAX_SEND_RETRIES = 5
    MAX_RECEIVE_RETRIES = 10
    RECEIVE_LOOP_DELAY = 10 # ms
    SEND_LOOP_DELAY = 1000 # ms

    def __init__(self) -> None:
        pass

    async def send_and_receive(self, send_data, receive_size, ip, port):
        receive_data = None
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)
        send_retries = self.MAX_SEND_RETRIES
        while send_retries > 0:
            receive_retries = self.MAX_RECEIVE_RETRIES
            res = self._socket.sendto(send_data, (ip, port))
            start_time = time.ticks_ms()
            while receive_retries > 0:
                try:
                    receive_data = self._socket.recv(receive_size)
                    end_time = time.ticks_ms()
                    self._socket.close()
                    send_retries = receive_retries = 0
                except OSError as err:
                    receive_retries -= 1
                    if err.errno == ETIMEDOUT or err.errno == EAGAIN:
                        pass
                    else:
                        _logger.error(f'send_and_receive(): Other OSError while receiving from NTP server. Error: Error: {err}.')
                    if receive_retries > 0:
                        await asyncio.sleep_ms(self.RECEIVE_LOOP_DELAY)
                    else:
                        end_time = time.ticks_ms()
                        send_retries -= 1
                        if send_retries > 0:
                            await asyncio.sleep_ms(self.SEND_LOOP_DELAY)
                        else:
                            self._socket.close()
                except Exception as err:
                    _logger.error(f'send_and_receive(): Exception while receiving from NTP server. Error: {err}, type: {type(err)}.')
                    raise
                else:
                    return receive_data
