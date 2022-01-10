from peripheral import peripheral, TrueValues
from servoLib import Servo
from machine import Pin


def setAngle(s, to=None):
    if to:
        s.angle = to

    return s.angle


def setUs(s, to=None):
    if to:
        s.us = to

    return s.us


class servo(peripheral):
    def __init__(self, options={"pin": 25, "freq": 50, "min_us": 600, "max_us": 2400, "angle": 180}):
        super().__init__(options)

        self.pType = "servo"
        self.pClass = "OUT"
        self._us = 0
        self._angle = 0

        self.commands["angle"] = setAngle
        self.commands["us"] = setUs

        self.po = Servo(
            Pin(int(self.settings.get("pin")), Pin.OUT),
            int(self.settings.get("freq")),
            int(self.settings.get("min_us")),
            int(self.settings.get("max_us")),
            int(self.settings.get("angle"))
        )

    @property
    def angle(self):
        return self._angle

    @angle.setter
    @peripheral._watch
    def angle(self, val):
        self._angle = int(val)
        self.po.write_angle(self._angle)

    @property
    def us(self):
        return self._us

    @us.setter
    @peripheral._watch
    def us(self, val):
        self._us = int(val)
        self.po.write_us(self._us)

    def getState(self):
        return {
            "angle": self.angle,
            "us": self.us
        }

    def getObservableMethods(self):
        return ["command"]

    def getObservableProperties(self):
        return ["angle", "us"]
