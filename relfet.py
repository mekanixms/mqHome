from peripheral import peripheral, TrueValues
from machine import Pin, PWM


def relayOn(s):
    s.value = True
    return s.value


def relayOff(s):
    s.value = False
    return s.value


def relayToggle(s):
    s.value = not s.value
    return s.value


def relayValue(s, to=None):
    if to in TrueValues:
        s.value = True
    else:
        s.value = False

    return s.value


def mode(s, pwm=None):

    if pwm != None:
        s.isPWM = pwm

    return True if type(s.pwm) is PWM else False


def duty(s, value):
    if s.isPWM:
        s.duty = int(value)

    return s.duty


def freq(s, value):
    if s.isPWM:
        s.freq = int(value)

    return s.freq


def pwmset(s, freq, duty):
    s.freq = int(freq)
    s.duty = int(duty)

    return {"freq": s.freq, "duty": s.duty}


class relfet(peripheral):
    pwm = False

    def __init__(self, options={"pinOut": 14}):
        super().__init__(options)

        self.pType = "relfet"
        self.pClass = "OUT"

        self.commands["on"] = relayOn
        self.commands["off"] = relayOff
        self.commands["toggle"] = relayToggle
        self.commands["relayValue"] = relayValue
        self.commands["mode"] = mode
        self.commands["duty"] = duty
        self.commands["freq"] = freq
        self.commands["pwmset"] = pwmset

        self.po = Pin(int(self.settings.get("pinOut")), Pin.OUT)

    def deinit(self):
        if type(self.pwm) is PWM:
            self.pwm.deinit()
            self.pwm = False

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

    @property
    def isPWM(self):
        if type(self.pwm) is PWM:
            return True
        else:
            return False

    @isPWM.setter
    @peripheral._watch
    def isPWM(self, val):
        global TrueValues

        mtv = TrueValues
        mtv.append("pwm")

        if val in mtv:
            self.pwm = PWM(self.po)
            return True
        else:
            if type(self.pwm) is PWM:
                self.pwm.deinit()
                self.pwm = False
                return False

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
            "pwm": self.isPWM,
            "freq": self.freq,
            "duty": self.duty,
            "on": self.value
        }

    def getObservableMethods(self):
        return ["command"]

    def getObservableProperties(self):
        return ["duty", "freq", "isPWM", "value"]
