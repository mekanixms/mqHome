from peripheral import peripheral, TrueValues
from machine import Pin, UART
from time import sleep_ms
import _thread
from ubinascii import hexlify, unhexlify
from jsu import file_exists
import json
from os import listdir

_thread.stack_size(4096*2)


@peripheral._trigger
def sendSignal(s, key, dictionary="default"):
    return s.send(key, dictionary)


@peripheral._trigger
def learnSignal(s, key, dictionary="default"):
    return s.send(key, dictionary)


def filesListAllType(dir="/", typeFilter="ir"):
    filteredFiles = []
    allFiles = listdir(dir)

    for f in allFiles:
        if len(f.split(".")) > 1:
            if f.split(".")[1] == typeFilter:
                filteredFiles.append(f.split(".")[0])

    return filteredFiles


def exportJsonDictionary(cfn, obj):
    configFile = open(cfn, "w")
    configFile.write(json.dumps(obj))
    configFile.close()


def importJsonDictionaryFromFile(cfgf):
    if file_exists(cfgf):
        # incarc fisier configurare
        configFile = open(cfgf, "r")
        configFileContent = configFile.readlines()

        if len(configFileContent) > 0:
            jsonConfig = json.loads("".join(configFileContent))
        else:
            jsonConfig = {cfgf: {}}

        configFile.close()
    else:
        jsonConfig = {cfgf: {}}

    return jsonConfig


class iruart(peripheral):

    version = 0.2

    def __init__(self, options={
        "id": 2,
        "baudrate": 9600,
        "wait": 500
    }):
        super().__init__(options)

        self.pType = "iruart"
        self.pClass = "OUT"

        self.learnThis = False

        self.commands["emit"] = sendSignal
        self.commands["learn"] = learnSignal

        self.dictionary = {
            # "default": {
            #     "prefix": 'a1f1',
            #     "commands": {
            #         "POWER": '04fb08',
            #         "CHUP": '04fb00',
            #         "CHDOWN": '04fb01',
            #         "MUTE": '04fb09',
            #     }
            # }
        }

        for cdfs in filesListAllType():
            if file_exists(cdfs+".ir"):
                self.dictionary[cdfs] = importJsonDictionaryFromFile(
                    cdfs+".ir")

        self.__lastRead = False
        self.__tmpValue = False

        self.uart = UART(self.settings["id"], self.settings["baudrate"])

        try:
            self.thread = _thread.start_new_thread(self.run, ())
        except Exception:
            print("UART THREAD EXCEPTION")

    def run(self):
        a_lock = _thread.allocate_lock()
        while True:
            with a_lock:
                try:
                    self.__tmpValue = self.uart.read()
                    if self.__lastRead != self.__tmpValue:
                        if self.__tmpValue != None:
                            self.value = self.__tmpValue
                except:
                    if False:
                        print("\tTrying to reconnect...implement me")
                        break
                sleep_ms(self.settings["wait"])
        _thread.exit()

    @property
    def value(self):
        return self.__lastRead

    @value.setter
    @peripheral._watch
    def value(self, val):
        self.__lastRead = val

    def decodedValue(self):
        toRet = False

        if self.value.__class__.__name__ == 'bytes':
            try:
                toRet = hexlify(self.value).decode('utf-8')
            except UnicodeError as u:
                toRet = "Error "+u

        return toRet

    @peripheral._trigger
    def send(self, key, dictionary="default"):
        if dictionary in self.dictionary.keys():
            jsonDict = self.dictionary.get(dictionary)
            if key in jsonDict["commands"].keys():
                prefix = jsonDict["prefix"]
                cmd = jsonDict["commands"].get(key)
                signal = unhexlify(prefix)+unhexlify(cmd)

                self.uart.write(signal)

                return {"sent": {dictionary: key}}

        return {"sent": "error"}

    def sendRaw(self, key):
        self.uart.write(key)

    @peripheral._trigger
    def learn(self, key, dictionary):
        self.learnThis = {dictionary:key}

    def loadDictionary(self, newDict={}):
        self.dictionary = newDict

    def getState(self):
        return {
            "value": self.decodedValue(),
            "dicts": self.dictionary
        }

    def getObservableMethods(self):
        return ["command", "emit"]

    def getObservableProperties(self):
        return ["value"]
