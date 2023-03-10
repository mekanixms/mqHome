from peripheral import peripheral, TrueValues
from machine import Pin, UART
from time import sleep_ms
import _thread
from ubinascii import hexlify, unhexlify
from jsu import file_exists, importJsonDictionaryFromFile
import json
from os import listdir

_thread.stack_size(4096*2)


@peripheral._trigger
def sendSignal(s, key, dictionary="default", repeat=1):
    return s.send(key, dictionary, repeat)


@peripheral._trigger
def learnSignal(s, key, dictionary="default"):
    return s.learn(key, dictionary)


@peripheral._trigger
def learnPrefix(s, prefix, dictionary="default"):
    return s.setPrefix(prefix, dictionary)


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


class iruart(peripheral):

    version = 0.3

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
        self.commands["prefix"] = learnPrefix

        self.dictionary = {}

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
    def value(self, val):
        self.__lastRead = val
        self.rvalue(self.decodedValue())

        if self.learnThis.__class__.__name__ is "dict":
            tlDictName = list(self.learnThis.keys())[0]
            tlKeyName = self.learnThis[tlDictName]
            if tlDictName not in self.dictionary.keys():
                self.dictionary[tlDictName] = {
                    "prefix": "a1f1", "commands": {}}
            self.dictionary[tlDictName]["commands"][tlKeyName] = self.decodedValue()
            exportJsonDictionary(tlDictName+".ir", self.dictionary[tlDictName])

            self.learnThis = False

    def decodedValue(self):
        toRet = False

        if self.value.__class__.__name__ == 'bytes':
            try:
                toRet = hexlify(self.value).decode('utf-8')
            except UnicodeError as u:
                toRet = "Error "+u

        return toRet

    @peripheral._trigger
    def rvalue(self, rvalue):
        pass

    @peripheral._trigger
    def send(self, key, dictionary="default", repeat=1):
        # TODO: def send(self, key, dictionary="default", repeat=1, repeatTimeIncrement = 0.1s):
        # repeatTimeIncrement sa fie folosit de sleep_ms in for loop
        if dictionary in self.dictionary.keys():
            jsonDict = self.dictionary.get(dictionary)
            if key in jsonDict["commands"].keys():
                prefix = jsonDict["prefix"]
                cmd = jsonDict["commands"].get(key)
                signal = unhexlify(prefix)+unhexlify(cmd)

                r = 1

                if repeat.__class__.__name__ == "str" and repeat.isdigit():
                    r = int(repeat)
                else:
                    if repeat.__class__.__name__ == "float":
                        r = int(repeat)

                if r < 1:
                    r = 1

                for a in range(0, r):
                    self.uart.write(signal)
                    if r > 1:
                        sleep_ms(500)

                return {"sent": {dictionary: key}}

        return {"sent": "error"}

    def sendRaw(self, key):
        self.uart.write(key)

    @peripheral._trigger
    def setPrefix(self, prefix, dictionary):
        if dictionary in self.dictionary.keys():
            if len(prefix) % 2 == 0:
                self.dictionary[dictionary]["prefix"] = prefix
                exportJsonDictionary(
                    dictionary+".ir", self.dictionary[dictionary])
                return {"prefix": "set to "+prefix}

        return {"error": "could not set prefix "+prefix+" for "+dictionary}

    @peripheral._trigger
    def learn(self, key, dictionary):
        self.learnThis = {dictionary: key}

        return {"learning": "press a key on the remote"}

    def loadDictionary(self, newDict={}):
        pass

    def getState(self):
        return {
            "value": self.decodedValue(),
            "dicts": self.dictionary
        }

    def getObservableMethods(self):
        return ["command", "emit", "rvalue"]

    def getObservableProperties(self):
        return []
