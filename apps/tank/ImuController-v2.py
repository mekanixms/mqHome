from math import atan2, sqrt, pi
import mcu
import network
from time import sleep
import ujson
import conf
from machine import Pin, PWM


def remap(x, in_min=-90, in_max=90, out_min=-1000, out_max=1000):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


sw = Pin(int(conf.pinModeSwitch), Pin.IN, Pin.PULL_DOWN)
conf.pinDevStatusLED = 14
statusLED = PWM(Pin(int(conf.pinDevStatusLED), Pin.OUT))
statusLED.duty(768)
statusLED.freq(1)


wap = network.WLAN(network.AP_IF)
wap.active(True)

wif = network.WLAN(network.STA_IF)
wif.active(True)

if wif.isconnected():
    wif.disconnect()

m = mcu.mcu()
m.addPeripheral({
    "type": 'espnowdrv',
    "initOptions": {
        "autostart": True, "broadcast": True, "wap_channel": 10
    }})

m.addPeripheral({
    "type": "mpu6050",
    "initOptions": {
            "id": 0,
            "alias": "Accel#HWT2"
    }
})

e = m.peripherals[0]
a = m.peripherals[1]

# if sw.value():
#     print("Calibrating gyro")
#     a.imu.gyro.calibrate(sw)

# print("Calibrating Accelometer")
# a.imu.accel.calibrate(sw)


def hb(val):
    global e

    xa, ya, za = a.imu.accel.xyz

    roll = atan2(ya, za) * 180.0 / pi
    pitch = atan2(-xa, sqrt(ya * ya + za * za)) * 180.0 / pi
    # roll = a.roll()
    # pitch = a.pitch()
    # print(str(int(remap(pitch - roll))) +
    #        ";"+str(int(remap(pitch + roll))))
    e.send(str(int(remap(pitch - roll))) +
           ";"+str(int(remap(pitch + roll))))


a.addWatcher("heartbeat", "AFTER", hb)

a.setTimer(True, period=200)
