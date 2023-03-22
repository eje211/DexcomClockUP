from dexcom import DexcomClock
from rgblcd import setText
from time import sleep

SLEEP_TIME = 120 # seconds
LINE_WIDTH = 16

dc = None

def init():
    global dc
    dc = DexcomClock()
    dc.connect()

def add_buffer(text):
    buffer_size = (LINE_WIDTH - len(text)) // 2
    return (' ' * buffer_size) + text

def updateDisplay():
    glucose, trend = dc.update()
    lines = [
        f'{glucose}mg/dL',
        str(trend)]
    lines = map(add_buffer, lines)
    setText('\n'.join(lines))
    
def run():
    while True:
        updateDisplay()
        sleep(SLEEP_TIME)


init()
run()