from peripheral import peripheral
from machine import UART, idle
import ure


@peripheral._trigger
def sendMessage(s, message):
    return s.send(message)


class uartcomm(peripheral):
    '''
    simple version of uartcomm with no automatic way to read the uart messages
    uses parseAllMessages method to parse them
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

        self.pType = "uartcomms"
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
        self.send("PING")
        print("\t"+self.pType+" "+str(self.settings["id"]) +
              " STARTED at " + str(self.settings["baudrate"]) + " bps")

    def parseAllMessages(self):
        while self.uart.any():
            try:
                self.value = self.uart.readline().decode().rstrip(self.lineSeparator)
            except:
                pass
            # except UnicodeError as ue:
            #     pass

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
