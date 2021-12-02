from peripheral import peripheral, TrueValues
from machine import Pin, PWM


@peripheral._trigger
def drive(s, direction, speed):
    s.direction = direction
    s.speed = speed
    s.drive()

    return {"direction": s.direction, "speed": s.speed}


@peripheral._trigger
def stop(s):
    s.speed = 0
    s.drive()

    return {"direction": s.direction, "speed": s.speed}


class bts7960(peripheral):
    CW = 1
    CCW = 0

    def __init__(self, options={"R_PWM": 16, "L_PWM": 17, "default_freq": 50}):
        super().__init__(options)

        self.pType = "bts7960"
        self.pClass = "OUT"

        self.commands["drive"] = drive
        self.commands["stop"] = stop

        self._pol = Pin(int(self.settings.get("L_PWM")), Pin.OUT)
        self._por = Pin(int(self.settings.get("R_PWM")), Pin.OUT)
        self._default_freq = int(self.settings.get("default_freq"))
        self._pwL = PWM(self._pol)
        self._pwL.freq(self._default_freq)
        self._pwL.duty(0)
        self._pwR = PWM(self._por)
        self._pwR.freq(self._default_freq)
        self._pwR.duty(0)
        self.__dir = self.CW
        self.__sp = 0

    def deinit(self):
        if type(self._pwL) is PWM:
            self._pwL.deinit()
            self._pwL = False
        if type(self._pwR) is PWM:
            self._pwR.deinit()
            self._pwR = False

    @property
    def direction(self):
        return self.__dir

    @direction.setter
    @peripheral._watch
    def direction(self, val):
        if val in TrueValues:
            self.__dir = self.CW
        else:
            self.__dir = self.CCW
        return self.__dir

    @property
    def speed(self):
        return self.__sp

    @speed.setter
    @peripheral._watch
    def speed(self, val):
        setTo = 0
        if val.__class__ is str:
            if val.isdigit():
                setTo = int(val)
        else:
            if val.__class__ is int:
                setTo = val

        if setTo in range(0, 1023):
            self.__sp = setTo
            return self.__sp
        else:
            return None

    def drive(self):
        if self.direction == self.CW:
            self._pwL.duty(0)
            self._pwR.duty(self.speed)
        else:
            self._pwR.duty(0)
            self._pwL.duty(self.speed)

    def getState(self):
        return {
            "direction": self.direction,
            "speed": self.speed
        }

    def getObservableMethods(self):
        return ["command", "drive", "stop"]

    def getObservableProperties(self):
        return ["direction", "speed"]
