# Based on Encoder library of Peter Hinch
# https://github.com/peterhinch/micropython-samples/blob/master/encoders/encoder_portable.py
from peripheral import peripheral, TrueValues
from machine import Pin


def setPosition(s, to=None):
    if to != None:
        if to.isdigit():
            s._pos = int(to)
        return {"set": to}
    return {"set": "false"}


def reset(s):
    s._pos = 0
    return {"reset": "done"}


class rotencoder(peripheral):
    def __init__(self, options={"pin_x": 32, "pin_y": 33, "reverse": False, "scale": 1, "limits": False}):
        super().__init__(options)

        self.pType = self.__class__.__name__
        self.pClass = "IN"

        self.reverse = self.settings.get("reverse") in TrueValues
        self.scale = float(self.settings.get("scale"))
        self.forward = True
        self.pin_x = Pin(int(self.settings.get("pin_x")), Pin.IN)
        self.pin_y = Pin(int(self.settings.get("pin_y")), Pin.IN)
        self._pos = 0
        self.commands["set"] = setPosition
        self.commands["reset"] = reset

        if self.settings.get("limits").__class__ is tuple:
            l = self.settings.get("limits")
            bl = l[0]
            tl = l[1]
            self.range = range(bl, tl)
        else:
            if self.settings.get("limits").__class__ is str:
                l = self.settings.get("limits").split(",")
                if l[0].strip().isdigit() and l[1].strip().isdigit():
                    bl = int(l[0].strip())
                    tl = int(l[1].strip())
                    self.range = range(bl, tl)
                else:
                    self.range = False
            else:
                self.range = False

        self.x_interrupt = self.pin_x.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.x_callback)
        self.y_interrupt = self.pin_y.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.y_callback)

    def inRange(self, v):
        if self.range.__class__ == range:
            if v in self.range:
                return True
            else:
                return False
        else:
            return True

    def x_callback(self, line):
        self.forward = self.pin_x.value() ^ self.pin_y.value() ^ self.reverse
        add = 1 if self.forward else -1
        if self.inRange(self.position + add):
            self.position += add

    def y_callback(self, line):
        self.forward = self.pin_x.value() ^ self.pin_y.value() ^ self.reverse ^ 1
        add = 1 if self.forward else -1
        if self.inRange(self.position + add):
            self.position += add

    @property
    def position(self):
        return int(self._pos * self.scale)

    @position.setter
    @peripheral._watch
    def position(self, value):
        self._pos = value // self.scale

    def getState(self):
        return {"position": self.position}

    def getObservableMethods(self):
        return ["command"]

    def getObservableProperties(self):
        return ["position"]
