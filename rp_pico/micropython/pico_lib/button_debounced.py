from machine import Pin
import uasyncio as asyncio
import time

from .logging_enhanced import Logger_Enhanced
_logger =  Logger_Enhanced.get_logger_for_module(__name__) 

class Button_Debounced:
    def __init__(self, pin, callback, name = None, pull_up_down = Pin.PULL_UP, debouncing_time = 20) -> None:
        self._callback = callback
        self._name = name if name else f'button_{pin}'
        self._debouncing_time = debouncing_time
        self._button = Pin(pin, Pin.IN, pull_up_down)
        self._button.irq(handler=self._on_button_changed, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)
        self._last_changed = time.ticks_ms()
        self._state = 1 if pull_up_down == Pin.PULL_UP else 0

    def _on_button_changed(self, button):
        now = time.ticks_ms()
        state = button.value()
        _logger.debug(f"Button '{self._name}' changes state to {state}.")
        if ((now - self._last_changed) > self._debouncing_time) and (state != self._state):
            self._last_changed = now
            self._state = state
            if self._callback:
                cb = self._callback
                asyncio.create_task(self._callback(self._name, button.value()))