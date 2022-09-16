try:
    import uasyncio
except ModuleNotFoundError:
    import asyncio as uasyncio
from pydexcom import Dexcom, GlucoseReading
from typing import Optional
import logging
import json
from collections import namedtuple
import time

try:
    import wifi
    wlan = wifi.start_wifi()
    while not wlan.isconnected():
        time.sleep(.5)
except (NameError, ModuleNotFoundError, AttributeError):
    pass


GlucoseAndTrend = namedtuple('GlucoseAndTrend', ('glucose_level', 'trend_description'))


logging.basicConfig(level=logging.INFO)


with open('credentials.json', mode='r') as f:
    credentials = json.loads(f.readlines()[0])


class Config:
    username = credentials['USERNAME']
    password = credentials['PASSWORD']


class DexcomClock:

    def __init__(self):
        self._dexcom: Optional[Dexcom] = None
        self._blood_glucose: Optional[GlucoseReading] = None
        self.found = False

    def connect(self):
        """
        Connects to the Dexcom server and sets the "connected" instance
        attribute to True.
        """
        logging.info("Calling Dexcom...")
        self._dexcom = Dexcom(Config.username, Config.password)
        logging.info('Connected with Dexcom!')
        self.found = True

    def update(self):
        """
        Get the latest glucose reading from the associated transmitter.
        Connects first if the instance is not connected.
        :return: the latest glucose reading.
        """
        try:
            return self._update()
        except AttributeError:
            self.connect()
            return self._update()

    def _update(self):
        """
        Gets the latest glucose reading from the associated transmitter
        without connecting first.
        :return: The latest glucose reading.
        """
        self._blood_glucose = self._dexcom.get_current_glucose_reading()
        return GlucoseAndTrend(self._blood_glucose.value, self._blood_glucose.trend_description)

    async def message(self):
        if logging.root.level > logging.INFO:
            return
        while self.found is False:
            await uasyncio.sleep(0.2)
            logging.info('Waiting for response.')
            await uasyncio.sleep(0.2)
            logging.info('')

    async def to_thread(self, func):
        from asyncio import events
        loop = events.get_running_loop()
        return await loop.run_in_executor(None, self.connect)

    async def async_loop(self):
        await uasyncio.gather(
            self.message(),
            self.to_thread(self.connect))

    def start_async_loop(self):
        uasyncio.run(self.async_loop())
        logging.info('Done with async')
