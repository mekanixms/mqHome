from peripheral import peripheral
from machine import UART, idle
import ure
import select


@peripheral._trigger
def sendMessage(s, message):
    return s.send(message)


class uartcommht(peripheral):
    '''
    select.poll version to read the messages from uart
    base example https://forum.micropython.org/viewtopic.php?t=1741
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

        self.pType = "uartcommht"
        self.pClass = "OUT"



        self.connected = False
        self.synced = False

        self.commands["send"] = sendMessage

        self.__lastRead = False
        self.__tmpValue = False

        self.uart = UART(self.settings["id"], self.settings["baudrate"])
        self.poll = select.poll()
        self.poll.register(self.uart, select.POLLIN)

        if "autostart" in options.keys():
            if options["autostart"]:
                print("Autostart enabled")
                self.start()

    def start(self):
        # TODO: finish implementation
        # self.hTimer.init(
        #     period=self.settings["timer_period"], mode=Timer.PERIODIC, callback=self.run)
        self.send("PING")
        print("\t"+self.pType+" "+str(self.settings["id"]) +
              " STARTED at " + str(self.settings["baudrate"]) + " bps")

    def run(self, t):
        if self.uart.any():
            self.value = self.uart.readline().decode().rstrip(self.lineSeparator)

    @property
    def value(self):
        return self.__lastRead

    @value.setter
    def value(self, val):
        try:
            self.__tmpValue = val

            skipThisOne = False

            if self.__tmpValue == "PING":
                self.connected = True
                skipThisOne = True
                self.send("PONG")

            if self.__tmpValue == "PONG":
                self.synced = True
                skipThisOne = True

            if not skipThisOne:
                if self.settings["skipRepeats"]:
                    if self.__lastRead != self.__tmpValue:
                        if self.__tmpValue != None:
                            self.__lastRead = self.__tmpValue
                else:
                    if self.__tmpValue != None:
                        self.__lastRead = self.__tmpValue
        except:
            pass

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
