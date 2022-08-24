
from peripheral import peripheral, TrueValues
from aht10driver import AHT10
from machine import Pin, SoftI2C
from jsu import FalseValues
import ujson


def all(s):
    s.temperature = s.temperature
    s.humidity = s.humidity

    return ujson.dumps({
        "humidity": s.humidity,
        "temperature": s.temperature,
        "mode": s.mode
    })


def temperature(s):
    return s.temperature


def humidity(s):
    return s.humidity


def mode(s, mode=None):
    if mode != None:
        s.mode = mode

    return s.mode


class aht10(peripheral):
    VERSION = 0.1

    def __init__(self, options={"scl": 21, "sda": 22, "mode": 0}):
        super().__init__(options)

        self.status = False

        self.pType = self.__class__.__name__
        self.pClass = "IN"

        self.commands["readTemperature"] = temperature
        self.commands["readHumidity"] = humidity
        self.commands["mode"] = mode

        self.sclInput = int(self.settings.get("scl"))
        self.sdaInput = int(self.settings.get("sda"))
        self.temperatureUnits = int(self.settings.get("mode"))
        # mode 0 C mode 1 F
        self._humidity = 0
        self._temperature = 0

        self.sensor = AHT10(i2c=SoftI2C(scl=Pin(self.sclInput), sda=Pin(
            self.sdaInput)), mode=self.temperatureUnits)

    @property
    def humidity(self):
        self._humidity = self.sensor.humidity()
        self.onHumidityUpdate(self._humidity)
        return self._humidity

    @peripheral._trigger
    def onHumidityUpdate(self, value):
        pass

    @property
    def temperature(self):
        self._temperature = self.sensor.temperature()
        self.onTemperatureUpdate(self._temperature)
        return self._temperature

    @peripheral._trigger
    def onTemperatureUpdate(self, value):
        pass

    @property
    def mode(self):
        return self.sensor.mode

    @mode.setter
    def mode(self, val):
        self.sensor.set_mode(val)

    def getState(self):
        return {"humidity": self.humidity, "temperature": self.temperature, "mode": self.mode}

    def getObservableMethods(self):
        return ["command", "onTemperatureUpdate", "onHumidityUpdate"]

    def getObservableProperties(self):
        return []
