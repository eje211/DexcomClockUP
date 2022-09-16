import network
import time
import json

def get_credentials():
    with open('credentials.json', 'r') as f:
        return json.load(f)

def start_wifi():
    import time
    credentials = get_credentials()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(credentials['SSID'], credentials['WIFIPW'])
    return wlan