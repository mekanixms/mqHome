from mcu import mcu
from time import sleep
from machine import idle

m=mcu()
m.wlanSTMode(True)
m.wifi.connect("tp","ipaq2490b")
while not m.wifi.isconnected():
    idle()

r = m.wifi.ifconfig()
print(r[0])