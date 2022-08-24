from peripheral import peripheral
from machine import UART, idle
import _thread
import ure


_thread.stack_size(4096*4)


@peripheral._trigger
def sendMessage(s, message):
    return s.send(message)


class uartcomml(peripheral):
    '''
    lite version of uartcomm
    does not provide onNewCommand and skipRepeats
    '''

    version = 0.1
    matchFunctions = '(.*?)\((.*?)\)'
    lineSeparator = "\n"

    def __init__(self, options={
        "autostart": True,
        "id": 2,
        "baudrate": 115200,
        "skipRepeats": True
    }):
        super().__init__(options)

        self.pType = "uartcomml"
        self.pClass = "OUT"

        self.connected = False
        self.synced = False

        self.commands["send"] = sendMessage

        self.__lastRead = False
        self.__tmpValue = False

        self.uart = UART(self.settings["id"], self.settings["baudrate"])

        if "autostart" in options.keys():
            if options["autostart"]:
                print("Autostart enabled")
                self.start()

    def start(self):
        try:
            self.thread = _thread.start_new_thread(self.run, ())
        except Exception:
            print("UART THREAD EXCEPTION")

        self.send("PING")
        print("\t"+self.pType+" "+str(self.settings["id"]) +
              " STARTED at " + str(self.settings["baudrate"]) + " bps")

    def run(self):
        a_lock = _thread.allocate_lock()
        while True:
            with a_lock:
                if self.uart.any():
                    self.value = self.uart.readline().decode().rstrip(self.lineSeparator)
                else:
                    idle()
        _thread.exit()

    def th_setValue(self, v):
        self.value = v

    @property
    def value(self):
        return self.__lastRead

    @value.setter
    def value(self, val):
        self.__lastRead = val
        self.onNewLine(val)

    @peripheral._trigger
    def onNewLine(self, value):
        pass

    @peripheral._trigger
    def send(self, message, lineSeparator="\n"):
        toRet = 0

        if type(message) is str:
            toRet = self.uart.write(message+lineSeparator)

        return toRet

    def getState(self):
        return {
            "connected": self.connected,
            "synced": self.synced,
            "value": self.value
        }

    def getObservableMethods(self):
        return ["command", "send", "onNewLine"]

    def getObservableProperties(self):
        return []
