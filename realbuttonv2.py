from vtimer import vtimer
from peripheral import peripheral, TrueValues
from machine import Pin, Timer


class realbuttonv2(peripheral):
    def __init__(self, options={"pinOut": 27, "period": 200, "pull": Pin.PULL_DOWN}):
        super().__init__(options)

        self.pType = self.__class__.__name__
        self.pClass = "IN"

        pin = int(self.settings.get("pinOut"))
        check_period = int(self.settings.get("period"))
        pull = int(self.settings.get("pull"))
        checks = 3

        self.pin = Pin(pin, Pin.IN, pull)
        self.pin.irq(handler=self._switch_change,
                     trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)

        self.debounce_timer = None
        self._new_value_available = False
        self.prev_value = None
        self.debounce_checks = 0
        self.checks = checks
        self.check_period = check_period
        self.status = False
        self._bistatus = False

    @property
    def hold(self):
        return self._bistatus

    @hold.setter
    @peripheral._watch
    def hold(self, val):
        self._bistatus = val

    @property
    def new_value_available(self):
        return self._new_value_available

    @new_value_available.setter
    @peripheral._watch
    def new_value_available(self, val):
        self.hold = not self.hold
        self._new_value_available = val
        return self.value

    @peripheral._trigger
    def changed(self, val):
        return val

    @property
    def value(self):
        return self.status

    @value.setter
    @peripheral._watch
    def value(self, val):
        if val in TrueValues:
            self.status = True
        else:
            self.status = False

        self.changed(self.status)

    def getState(self):
        return {"on": self.value, "hold": self.hold}

    def getObservableMethods(self):
        return ["command", "changed"]

    def getObservableProperties(self):
        return ["value", "hold"]

    def _switch_change(self, pin):
        self.value = pin.value()

        self.debounce_checks = 0
        self._start_debounce_timer()

        # IRQs disabled while debouncing
        self.pin.irq(trigger=0)

    def _start_debounce_timer(self):
        # self.debounce_timer.init(period=self.check_period, mode=Timer.ONE_SHOT,
        #                          callback=self._check_debounce)
        self.debounce_timer = vtimer(
            self.check_period, 0, self._check_debounce, False)
        self.debounce_timer.start()

    def _check_debounce(self, _):
        new_value = self.pin.value()

        if new_value == self.value:
            self.debounce_checks = self.debounce_checks + 1

            if self.debounce_checks == self.checks:
                if self.prev_value != self.value:
                    self.new_value_available = True
                    self.prev_value = self.value

                self.pin.irq(handler=self._switch_change,
                             trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)
            else:
                self._start_debounce_timer()
        else:
            self.debounce_checks = 0
            self.value = new_value
            self._start_debounce_timer()
