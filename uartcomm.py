from peripheral import peripheral
from machine import UART, idle
from time import sleep_ms
import _thread
import ure


_thread.stack_size(4096*2)


@peripheral._trigger
def sendMessage(s, key):
    return s.send(key)


class uartcomm(peripheral):

    version = 0.1
    matchFunctions = '(.*?)\((.*?)\)'

    def __init__(self, options={
        "id": 2,
        "baudrate": 115200,
        "skipRepeats": True
    }):
        super().__init__(options)

        self.pType = "uartcomm"
        self.pClass = "OUT"

        self.learnThis = False

        self.commands["send"] = sendMessage

        self.__lastRead = False
        self.__tmpValue = False

        self.uart = UART(self.settings["id"], self.settings["baudrate"])

        try:
            self.thread = _thread.start_new_thread(self.run, ())
            print("STARTED")
        except Exception:
            print("UART THREAD EXCEPTION")

    def run(self):
        a_lock = _thread.allocate_lock()
        while True:
            with a_lock:
                if self.uart.any():
                    try:
                        self.__tmpValue = self.uart.readline().decode().rstrip('\n')
                        if self.settings["skipRepeats"]:
                            if self.__lastRead != self.__tmpValue:
                                if self.__tmpValue != None:
                                    self.value = self.__tmpValue
                        else:
                            if self.__tmpValue != None:
                                self.value = self.__tmpValue
                    except:
                        if False:
                            print("\tTrying to reconnect...implement me")
                            break
                else:
                    idle()
        _thread.exit()

    @property
    def value(self):
        return self.__lastRead

    @value.setter
    def value(self, val):
        self.__lastRead = val
        self.onNewLine(val)

        try:
            smthd = ure.match(self.matchFunctions, val)
            cmd = smthd.group(1)
            params = smthd.group(2).split(",")
            params.insert(0, cmd)
            self.onNewCommand(*params)
        except:
            pass

    @peripheral._trigger
    def onNewLine(self, value):
        pass

    @peripheral._trigger
    def onNewCommand(self, *args):
        pass

    @peripheral._trigger
    def send(self, key):
        self.uart.write(key)

    def getState(self):
        return {
            "value": self.value
        }

    def getObservableMethods(self):
        return ["command", "send", "onNewLine"]

    def getObservableProperties(self):
        return []
