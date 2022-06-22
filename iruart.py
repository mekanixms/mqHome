from peripheral import peripheral, TrueValues
from machine import Pin, UART
from time import sleep_ms
import _thread
from ubinascii import hexlify

_thread.stack_size(4096*2)


@peripheral._trigger
def sendSignal(s, key):
    return s.send(key)


class iruart(peripheral):

    version = 0.1
    sendPrefix = b'\xA1\xF1'

    def __init__(self, options={
        "id": 2,
        "baudrate": 9600,
        "wait": 500
    }):
        super().__init__(options)

        self.pType = "iruart"
        self.pClass = "OUT"

        self.commands["emit"] = sendSignal

        self.dictionary = {
            "POWER": self.sendPrefix+b'\x04\xfb\x08',
            "CHUP": self.sendPrefix+b'\x04\xfb\x00',
            "CHDOWN": self.sendPrefix+b'\x04\xfb\x01'
        }

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

    @peripheral._trigger
    def send(self, key):
        if key in self.dictionary.keys():
            self.uart.write(self.dictionary.get(key))
            return {"sent": key}

        return {"sent": "error"}

    def learn(self, key):
        pass

    def loadDictionary(self, newDict={}):
        self.dictionary = newDict

    def getState(self):
        if self.value.__class__.__name__ == 'bytes':
            try:
                toRet = hexlify(self.value).decode('utf-8')
            except UnicodeError as u:
                toRet = "Error "+u

            return {"value": toRet}
            # return {"value": hexlify(self.value).decode('utf-8')}
        else:
            return {"value": self.value}

    def getObservableMethods(self):
        return ["command", "emit"]

    def getObservableProperties(self):
        return ["value"]
