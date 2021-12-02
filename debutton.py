from vtimer import vtimer
from machine import Pin


class debutton:
    VERSION = 0.1
    debounced_started = False

    def __init__(self, cbk=None, options={"pinOut": 27, "period": 200, "pull": Pin.PULL_DOWN}):

        self.pType = self.__class__.__name__
        self.pClass = "IN"

        pin = int(options["pinOut"])
        check_period = int(options["period"])
        pull = int(options["pull"])
        self.callback = cbk

        self.pin = Pin(pin, Pin.IN, pull)
        self.pin.irq(handler=self._switch_change,
                     trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)

        self.value = None
        self.check_period = check_period

        self.debounce_timer = None

    def _switch_change(self, pin):
        if not self.debounced_started:
            self.value = pin.value()

            self.debounced_started = True

            # Disable IRQs for GPIO pin while debouncing
            self.pin.irq(trigger=0)

        # Start timer to check for debounce
        self._start_debounce_timer()

    def _start_debounce_timer(self):
        self.debounce_timer = vtimer(
            self.check_period, 0, self._check_debounce, False)
        self.debounce_timer.start()

    def _check_debounce(self, _):
        if self.debounced_started:
            new_value = self.pin.value()

            if new_value != self.value:
                # executa callback
                if callable(self.callback) and self.callback is not None:
                    self.callback(new_value)

                self.debounced_started = False

            self.pin.irq(handler=self._switch_change,
                            trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)
