from socket import socket
import usocket as socket
from uerrno import ETIMEDOUT, EAGAIN
import struct
import time
from utime import ticks_ms, ticks_diff
import machine
import uasyncio as asyncio
import network

from .settings_base import Settings_Base
from .iso8601 import Iso8601
from .logging_enhanced import Logger_Enhanced
_logger =  Logger_Enhanced.get_logger_for_module(__name__) 

class Network_Utilities:

    @classmethod
    def get_address(cls, hostname : str, port : int = 0):
        try:
            addr_info = socket.getaddrinfo(hostname, port)[0][-1]
        except Exception as ex:
            _logger.error(f"Failed to resolve host name to IP address '{hostname}'.")
            return None
        else:
            if addr_info and len(addr_info) == 2:
                _logger.debug(f"IP address of '{hostname}' is {addr_info[0]}.")
                return addr_info
            else:
                return None
