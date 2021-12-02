import network
import esp
from ubinascii import hexlify
import os
from machine import idle, Pin
import conf
from time import sleep
from sys import platform

if_station = None
if_ap = None
wlanMode = None

modeSwitch = Pin(int(conf.pinModeSwitch), Pin.IN)
btn1 = Pin(int(conf.pinBtn1), Pin.IN)
btn2 = Pin(int(conf.pinBtn2), Pin.IN)
devStatusLED = Pin(int(conf.pinDevStatusLED), Pin.OUT)

isESP8266 = True if platform == 'esp8266' else False
isESP32 = True if platform == 'esp32' else False


def file_exists(f):
    if f in os.listdir():
        return True
    else:
        return False


def startAP():
    global if_station, wlanMode

    mac = hexlify(network.WLAN().config('mac'), ':')
    fid = str(mac.decode().replace(":", ""))

    ssid = 'AP-{}'.format(fid)
    p = "{}pass".format(fid)

    if "appass" in conf.jsonConfig.keys():
        p = conf.jsonConfig["appass"]

    if "apssid" in conf.jsonConfig.keys():
        ssid = conf.jsonConfig["apssid"]

    if_ap = network.WLAN(network.AP_IF)
    if_ap.active(True)
    if_ap.config(essid=ssid, password=p, authmode=4)
    print("Started Access Point "+ssid)

    # while not station.isconnected():
    #     idle()
    while if_ap.active() == False:
        pass
    print("AP connected: "+ssid)
    wlanMode = network.AP_IF
    sleep(1)


def startSTA(cdata):
    global if_station, wlanMode

    if_station = network.WLAN(network.STA_IF)
    if_station.active(True)
    sleep(2)

    if "staticip" in conf.jsonConfig.keys():
        if type(conf.jsonConfig["staticip"]) == list and len(conf.jsonConfig["staticip"]) == 4:
            print("Static IP: " + " / ".join(conf.jsonConfig["staticip"]))
            if_station.ifconfig(conf.jsonConfig["staticip"])

    if not if_station.isconnected():
        if_station.connect(cdata, conf.jsonConfig["aps"][cdata])

    while not if_station.isconnected():
        idle()

    wlanMode = network.STA_IF
    print("IP Address:\t"+if_station.ifconfig()[0])


def blinkWDLS(hb):
    # blink watch dog LED standalone
    global devStatusLED
    if hb:
        devStatusLED.on()
    else:
        devStatusLED.off()


def isStationWifiSet():
    if "aps" in conf.jsonConfig.keys() and len(conf.jsonConfig["aps"]) > 0:
        return next(iter(conf.jsonConfig["aps"]))
    else:
        return False


def main():
    global if_station, wlanMode
    needsAPsSetup = False

    print("MAIN launched")
    # "config/ap|config/sta|mqtt/sta"
    runAs, stationMode = conf.run.split("/")

    if modeSwitch.value() == 1:
        # resore defaults - sterge apl.json,  observables si startup.ru
        pass

    if btn1.value() and btn2.value():
        print("Mode switch ON - running in CONFIG mode")
        runAs = "config"
        # from vtimer import vtimer
        # vt = vtimer(1, vtimer.PERIODIC, blinkWDLS)
        # vt.start()
        devStatusLED.on()

    if stationMode == "sta":
        sapfc = isStationWifiSet()

        if sapfc:
            startSTA(sapfc)
        else:
            print("No AP saved, running setup")
            stationMode = "ap"
            runAs = "config"

    if stationMode == "ap" or not if_station.isconnected():
        startAP()

    if runAs == "config":
        print("CONFIG mode")
        import jssr
        jssr.mpu.wlanMode = wlanMode
    else:
        if runAs == "mqtt":
            print("MQTT mode")
            import mqttr


main()
