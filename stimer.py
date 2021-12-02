from peripheral import peripheral, TrueValues
from machine import Timer
from jsu import current_milli_time


def enable(s, period=1000, mode=Timer.ONE_SHOT, execute={"function": None, "arguments": {}}):
    return s.setTimer(True, period, mode, execute)


def disable(s):
    return s.setTimer(False)


class stimer(peripheral):

    _trigger = peripheral._trigger

    def __init__(self, options={"id": -1, "minutes": True}):
        super().__init__(options)

        self.pType = "stimer"
        self.pClass = "VIRTUAL"

        self.timerStatus = {"mode": 0, "period": 0}
        self.__stopTimer = False
        self.timerExecute = {"function": None, "arguments": None}

        self.commands["start"] = enable
        self.commands["stop"] = disable

        self.po = Timer(int(self.settings.get("id")))

        self.__heartbeat = True

    @property
    def stopTimer(self):
        return self.__stopTimer

    @stopTimer.setter
    @peripheral._watch
    def stopTimer(self, val):

        if val in TrueValues:
            self.__stopTimer = True
            self.po.deinit()
        else:
            self.__stopTimer = False

        self.timerStatus["on"] = not(self.stopTimer)

    @property
    def heartbeat(self):
        return self.__heartbeat

    @heartbeat.setter
    @peripheral._watch
    def heartbeat(self, val):
        self.__heartbeat = val

    @_trigger
    def timcbk(self, t):
        self.heartbeat = not self.heartbeat

        if len(self.timerExecute) > 0:
            f = self.timerExecute["function"]
            if callable(f) and f is not None:
                if self.timerExecute["arguments"] == None:
                    f()
                else:
                    if type(self.timerExecute["arguments"]) == dict:
                        f(**self.timerExecute["arguments"])
                    else:
                        if type(self.timerExecute["arguments"]) == list or type(self.timerExecute["arguments"]) == tuple:
                            f(*self.timerExecute["arguments"])

    def setTimer(self,
                 enable=False,
                 period=1000,
                 mode=Timer.ONE_SHOT,
                 execute={"function": None, "arguments": None}):

        if enable:
            self.stopTimer = False
            self.timerExecute = execute

            if self.settings.get("minutes"):
                self.timerStatus["period"] = int(float(period)*60*1000)
            else:
                self.timerStatus["period"] = int(period)

            self.timerStatus["mode"] = int(mode)

            self.po.init(period=self.timerStatus["period"], mode=self.timerStatus["mode"],
                         callback=self.timcbk)
        else:
            self.stopTimer = True
            print("Timer stopped")

    def getState(self):
        return {
            "on": not self.stopTimer,
            "period": self.timerStatus["period"],
            "mode": self.timerStatus["mode"],
            "minutes": self.settings.get("minutes")
        }

    def getObservableMethods(self):
        return ["command", "timcbk"]

    def getObservableProperties(self):
        return ["stopTimer", "heartbeat"]
