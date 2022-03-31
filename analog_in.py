from peripheral import peripheral, TrueValues
from machine import Pin, ADC


class analog_in(peripheral):
    def __init__(self, options={
        "pinOut": 34,
        "atten": ADC.ATTN_11DB,
        "width": ADC.WIDTH_12BIT
    }):
        super().__init__(options)

        self.pType = "analog_in"
        self.pClass = "IN"

        self.po = Pin(int(self.settings.get("pinOut")), Pin.IN)
        self.input = ADC(self.po)

        self.input.atten(
            ADC.ATTN_11DB if "atten" not in self.settings else self.settings["atten"])
        self.input.width(
            ADC.WIDTH_12BIT if "width" not in self.settings else self.settings["width"])

    #     self.po.irq(handler=self._switch_change,
    #                 trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)

    # def _switch_change(self, pin):
    #     self.changed(self.value)

    @property
    def value(self):
        return self.input.read()

    @value.setter
    @peripheral._watch
    def value(self, val):
        pass

    # @peripheral._trigger
    # def changed(self, val):
    #     return val

    def getState(self):
        return {"value": self.value,
                "width": self.settings.get("width"),
                "atten": self.settings.get("atten")
                }

    def getObservableMethods(self):
        return ["command"]

    def getObservableProperties(self):
        return ["value"]
