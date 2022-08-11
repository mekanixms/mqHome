from peripheral import peripheral, TrueValues
from machine import Pin


def relayOn(s):
    s.value = True
    return s.value


def relayOff(s):
    s.value = False
    return s.value


def relayValue(s, to=None):
    if to in TrueValues:
        s.value = True
    else:
        s.value = False

    return s.value


@peripheral._trigger
def relayToggle(s):
    s.value = not s.value
    return s.value


class relay(peripheral):
    def __init__(self, options={"pinOut": 5}):
        super().__init__(options)

        self.pType = "relay"
        self.pClass = "OUT"

        self.commands["on"] = relayOn
        self.commands["off"] = relayOff
        self.commands["toggle"] = relayToggle
        self.commands["value"] = relayValue

        self.po = Pin(
            int(self.settings.get("pinOut")),
            Pin.OUT,
            -1,
            value=None if "default" not in self.settings else self.settings["default"]
        )

    @property
    def value(self):
        return self.po.value()

    @value.setter
    @peripheral._watch
    def value(self, val):
        if val in TrueValues:
            if self.po.value() != True:
                self.po.value(True)
        else:
            self.po.value(False)

    def getState(self):
        return {"on": self.value}

    def getObservableMethods(self):
        return ["command", "toggle"]

    def getObservableProperties(self):
        return ["value"]
