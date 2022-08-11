from peripheral import peripheral, TrueValues
from machine import Pin, PWM


def duty(s, value):
    s.duty = int(value)

    return s.duty


def freq(s, value):
    s.freq = int(value)

    return s.freq


def pwmset(s, freq, duty):
    s.freq = int(freq)
    s.duty = int(duty)

    return {"freq": s.freq, "duty": s.duty}


class fet(peripheral):
    po = False

    def __init__(self, options={"pinOut": 14}):
        super().__init__(options)

        self.pType = "fet"
        self.pClass = "OUT"

        self.commands["duty"] = duty
        self.commands["freq"] = freq
        self.commands["pwmset"] = pwmset

        self.po = Pin(int(self.settings.get("pinOut")), Pin.OUT)
        self.pwm = PWM(self.po)

    def deinit(self):
        if type(self.pwm) is PWM:
            self.pwm.deinit()
            self.pwm = False

    @property
    def duty(self):
        if type(self.pwm) is PWM:
            return self.pwm.duty()
        else:
            return False

    @duty.setter
    @peripheral._watch
    def duty(self, val):
        if type(self.pwm) is PWM:
            if self.pwm.duty() != int(val):
                self.pwm.duty(int(val))
            return self.pwm.duty()
        else:
            return False

    @property
    def freq(self):
        if type(self.pwm) is PWM:
            return self.pwm.freq()
        else:
            return False

    @freq.setter
    @peripheral._watch
    def freq(self, val):
        if type(self.pwm) is PWM:
            if self.pwm.freq() != int(val):
                self.pwm.freq(int(val))
            return self.pwm.duty()
        else:
            return False

    def getState(self):
        return {
            "freq": self.freq,
            "duty": self.duty
        }

    def getObservableMethods(self):
        return ["command"]

    def getObservableProperties(self):
        return ["duty", "freq"]
