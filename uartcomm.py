from peripheral import peripheral
from machine import UART, idle
import ure


@peripheral._trigger
def sendMessage(s, message):
    return s.send(message)


class uartcomm(peripheral):
    '''
    blocking version, using simple while loop
    to be instatiated with autostart False and started in startup.run
    '''

    version = 0.1
    matchFunctions = '(.*?)\((.*?)\)'
    lineSeparator = "\n"

    def __init__(self, options={
        "autostart": False,
        "id": 2,
        "baudrate": 115200,
        "skipRepeats": True
    }):
        super().__init__(options)

        self.pType = "uartcomm"
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

        print("\t"+self.pType+" "+str(self.settings["id"]) +
              " STARTing at " + str(self.settings["baudrate"]) + " bps")
        self.send("PING")
        self.run()

    def run(self):
        while True:
            if self.uart.any():
                self.value = self.uart.readline().decode().rstrip(self.lineSeparator)
            else:
                idle()

    def th_setValue(self, v):
        self.value = v

    @property
    def value(self):
        return self.__lastRead

    @value.setter
    def value(self, val):

        isSyncMessage = False
        skipThisOne = False

        if val != None:
            try:
                if val == "PING":
                    self.connected = True
                    isSyncMessage = True
                    self.send("PONG")

                if val == "PONG":
                    self.synced = True
                    isSyncMessage = True

                if not isSyncMessage:
                    if self.settings["skipRepeats"]:
                        if self.__lastRead != val:
                            self.__lastRead = val
                        else:
                            skipThisOne = True
                    else:
                        self.__lastRead = val
            except:
                pass

            if not skipThisOne:
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
        return ["command", "send", "onNewLine", "onNewCommand"]

    def getObservableProperties(self):
        return []
