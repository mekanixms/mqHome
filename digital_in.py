from peripheral import peripheral, TrueValues
from machine import Pin


class digital_in(peripheral):
    def __init__(self, options={"pinOut": 21}):
        super().__init__(options)

        self.pType = "digital_in"
        self.pClass = "IN"

        # self.commands["value"] = relayValue

        self.po = Pin(int(self.settings.get("pinOut")), Pin.IN)
        self.po.irq(handler=self._switch_change,
                    trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)

    def _switch_change(self, pin):
        self.value = self.po.value()
        self.changed(self.value)

    @property
    def value(self):
        return self.po.value()

    @value.setter
    @peripheral._watch
    def value(self, val):
        pass

    @peripheral._trigger
    def changed(self, val):
        return val

    def getState(self):
        return {"on": self.value}

    def getObservableMethods(self):
        return ["command", "changed"]

    def getObservableProperties(self):
        return ["value"]
