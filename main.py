import network
from ubinascii import hexlify
import os
from machine import idle, Pin
import conf
from time import sleep
from sys import platform

wif = None
wap = None
wlanMode = None

isESP8266 = True if platform == 'esp8266' else False
isESP32 = True if platform == 'esp32' else False


def file_exists(f):
    if f in os.listdir():
        return True
    else:
        return False


def startAP():
    global wap, wlanMode

    mac = hexlify(network.WLAN().config('mac'), ':')
    fid = str(mac.decode().replace(":", ""))

    ssid = 'AP-{}'.format(fid)
    p = "{}pass".format(fid)

    if "appass" in conf.jsonConfig.keys():
        p = conf.jsonConfig["appass"]

    if "apssid" in conf.jsonConfig.keys():
        ssid = conf.jsonConfig["apssid"]

    wap = network.WLAN(network.AP_IF)
    wap.active(True)

    if ssid and p:
        wap.config(essid=ssid, password=p, authmode=4)
        print("Started Access Point "+ssid)

    while not wap.active():
        idle()

    print("AP connected: "+ssid)
    wlanMode = network.AP_IF
    sleep(1)


def startSTA(cdata):
    global wif, wlanMode

    wif = network.WLAN(network.STA_IF)
    wif.active(True)
    sleep(2)

    if "staticip" in conf.jsonConfig.keys():
        if type(conf.jsonConfig["staticip"]) == list and len(conf.jsonConfig["staticip"]) == 4:
            print("Static IP: " + " / ".join(conf.jsonConfig["staticip"]))
            wif.ifconfig(conf.jsonConfig["staticip"])

    if not wif.isconnected():
        wif.connect(cdata, conf.jsonConfig["aps"][cdata])

    while not wif.isconnected():
        idle()

    wlanMode = network.STA_IF
    print("IP Address:\t"+wif.ifconfig()[0])


def turnOffNetwork():
    wif = network.WLAN(network.STA_IF)
    wif.active(False)
    wap = network.WLAN(network.AP_IF)
    wap.active(False)


def isStationWifiSet():
    if "aps" in conf.jsonConfig.keys() and len(conf.jsonConfig["aps"]) > 0:
        return next(iter(conf.jsonConfig["aps"]))
    else:
        return False


def main():
    global wap, wif, wlanMode, runner

    modeSwitch = Pin(int(conf.pinModeSwitch), Pin.IN)
    btn1 = Pin(int(conf.pinBtn1), Pin.IN)
    btn2 = Pin(int(conf.pinBtn2), Pin.IN)
    devStatusLED = Pin(int(conf.pinDevStatusLED), Pin.OUT)

    print("MAIN launched")
    # "config/ap|config/sta|mqtt/sta"
    runAs, stationMode = conf.run.split("/")

    if modeSwitch.value() == 1:
        # restore defaults - sterge apl.json,  observables si startup.run
        pass

    if btn1.value() and btn2.value():
        print("Mode switch ON - running in CONFIG mode")
        runAs = "config"
        # from vtimer import vtimer
        # vt = vtimer(1, vtimer.PERIODIC, blinkWDLS)
        # vt.start()
        devStatusLED.on()
    else:
        if btn1.value():
            runAs = "blerepl"
            stationMode = "off"
    
    if not file_exists("apl.json"):
        runAs = "blerepl"
        stationMode = "off"

    if stationMode == "sta":
        sapfc = isStationWifiSet()

        if sapfc:
            startSTA(sapfc)
        else:
            print("No STA Wifi saved, running config / ap")
            stationMode = "ap"
            runAs = "config"

    if stationMode == "ap" or (wif is not None and not wif.isconnected()):
        startAP()

    if stationMode == "off":
        turnOffNetwork()

    print("\tRUNNING AS "+runAs+" net IF "+stationMode+"\n")
    try:
        runner = __import__(runAs+"r")
    except ImportError as e:
        print("\n\n\t"+e.value+"\n\n")


main()
