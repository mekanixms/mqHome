import ujson
from jsu import current_milli_time
from machine import reset
from sys import platform

isESP8266 = True if platform == 'esp8266' else False
isESP32 = True if platform == 'esp32' else False
isRP2 = True if platform == 'rp2' else False

if isESP32 or isESP8266:
    import network

esp32_blacklist_pins = [1, 3, 6, 7, 8, 9, 10, 11, 12]
esp32_safe_pins = [2, 4, 13, 16, 17, 18, 19, 21,
                   22, 23, 25, 26, 27, 32, 33, 34, 35, 36, 39]
esp32_input_only_pins = [34, 35, 36, 39]

safe_pins = {"esp32": esp32_safe_pins}
blacklist_pins = {"esp32": esp32_blacklist_pins}
input_only_pins = {"esp32": esp32_input_only_pins}


class mcu:
    platform = platform
    start_time = current_milli_time()
    wifi = None
    ap = None
    wlanMode = False
    unique_id = False

    peripherals = []
    peripheralsByType = {}
    peripheralsByAlias = {}
    userVariables = {}

    def __init__(self):
        from machine import unique_id
        from ubinascii import hexlify
        self.unique_id = hexlify(unique_id()).decode('utf-8')

        if isESP32 or isESP8266:
            self.wifi = network.WLAN(network.STA_IF)
            self.ap = network.WLAN(network.AP_IF)

    def uptime(self):
        return (current_milli_time()-self.start_time)/1000

    def reboot(self):
        reset()

    def wlanSetMode(self, mode=None, enable=False):
        if isESP32 or isESP8266:
            if mode is None:
                mode = network.STA_IF

            if mode == network.STA_IF:
                en = self.wifi
            if mode == network.AP_IF:
                en = self.ap

            en.active(enable)

            return en

    def wlanSTMode(self, enable=False):
        self.wlanSetMode(network.STA_IF, enable)

    def wlanAPMode(self, enable=False):
        self.wlanSetMode(network.AP_IF, enable)

    def getWlanMode(self):
        if self.wifi.active() and self.wifi.isconnected():
            return network.STA_IF
        else:
            if self.ap.active():
                return network.AP_IF
            else:
                return None

    def addPeripheral(self, thisOne={"type": "relay", "initOptions": {"pinOut": 5}}):
        if thisOne.get("type") in ["relay", "fet", "relfet", "stimer", "emiter",
                                   "receiver", "mpu6050", "bts7960", "aht10",
                                   "realbutton", "realbuttonv2", "rotencoder",
                                   "nokiadisplay", "mqtt", "mqtta", "mqttht",
                                   "messager", "servo", "digital_in", "analog_in",
                                   "iruart", "espnowdrv", "uartcomm"]:
            pt = thisOne.get("type")
            driverClass = getattr(__import__(pt), pt)

            if "initOptions" in thisOne.keys():
                if len(thisOne.get("initOptions")) > 0:
                    driverInstance = driverClass(thisOne.get("initOptions"))
                else:
                    driverInstance = driverClass()
            else:
                driverInstance = driverClass()

            if not pt in self.peripheralsByType:
                self.peripheralsByType[pt] = []

            self.peripherals.append(driverInstance)

            self.peripheralsByType[pt].append(driverInstance)

            if driverInstance.alias is not None:
                self.peripheralsByAlias[driverInstance.alias] = driverInstance

            print("New peripheral TYPE: "+driverInstance.pType)
            print("\twith init options")
            print("\t\t"+ujson.dumps(thisOne.get("initOptions")))
            return driverInstance
        else:
            return False

    def setPeripheral(self):
        pass
