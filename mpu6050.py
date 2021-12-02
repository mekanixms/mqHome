from peripheral import peripheral, TrueValues
from machine import I2C, Pin, Timer
from imu import MPU6050
from sys import platform


def enable(s, period=1000):
    return s.setTimer(True, period)


def disable(s):
    return s.setTimer(False)


def toggle(s):
    if s.stopTimer:
        return s.setTimer(True, s.period)
    else:
        return s.setTimer(False)


@peripheral._trigger
def setPeriod(s, period=1000):

    if type(period) == int:
        s.period = period
    else:
        if type(period) == str:
            if period.isdigit():
                s.period = int(period)


class mpu6050(peripheral):
    po = False
    isESP8266 = True if platform == 'esp8266' else False
    isESP32 = True if platform == 'esp32' else False

    def __init__(self, options={"id": -1}):
        super().__init__(options)

        self.pType = self.__class__.__name__
        self.pClass = "INPUT"

        if self.isESP8266:
            self.i2c = I2C(scl=Pin(5), sda=Pin(4))
            print("ESP8266 i2c init")
        else:
            if self.isESP32:
                # hardware i2c canal 1 scl 18 sda 19
                print("ESP32 i2c init")
                self.i2c = I2C(0)

        self.imu = MPU6050(self.i2c)
        self.__inclination = 0
        self.__inclination_avg = 0
        self.__azimuth = 0
        self.__azimuth_avg = 0
        self.__elevation = 0
        self.__elevation_avg = 0
        self.__accel_ixyz = 0
        self.__accel_ixyz_avg = 0
        self.__gyro_ixyz = 0
        self.__gyro_ixyz_avg = 0

        self.__period = 1000
        self.__stopTimer = True
        self.po = Timer(int(self.settings.get("id")))
        self.__heartbeat = True

        self.commands["start"] = enable
        self.commands["stop"] = disable
        self.commands["toggle"] = toggle
        self.commands["setPeriod"] = setPeriod

        self.__msg = ""

    def deinit(self):
        pass

    def readData(self, t):
        self.inclination = self.imu.accel.inclination
        self.azimuth = self.imu.accel.azimuth
        self.elevation = self.imu.accel.elevation
        self.accel_ixyz = self.imu.accel.ixyz
        self.gyro_ixyz = self.imu.gyro.ixyz

    @property
    def period(self):
        return self.__period

    @period.setter
    @peripheral._watch
    def period(self, val):
        self.__period = val

    @property
    def inclination(self):
        return self.__inclination

    @inclination.setter
    @peripheral._watch
    def inclination(self, val):
        if self.__inclination == 0:
            self.__inclination_avg = self.__inclination
        else:
            # s = (abs(primaCitireInclinare) + abs(imu.accel.inclination))/2
            self.__inclination_avg = (val+self.__inclination)/2

        self.__inclination = val

    @property
    def azimuth(self):
        return self.__azimuth

    @azimuth.setter
    @peripheral._watch
    def azimuth(self, val):
        if self.__azimuth == 0:
            self.__azimuth_avg = self.__azimuth
        else:
            # s = (abs(primaCitireInclinare) + abs(imu.accel.inclination))/2
            self.__azimuth_avg = (val+self.__azimuth)/2

        self.__azimuth = val

    @property
    def elevation(self):
        return self.__elevation

    @elevation.setter
    @peripheral._watch
    def elevation(self, val):
        if self.__elevation == 0:
            self.__elevation_avg = self.__elevation
        else:
            # s = (abs(primaCitireInclinare) + abs(imu.accel.inclination))/2
            self.__elevation_avg = (val+self.__elevation)/2

        self.__elevation = val

    @property
    def accel_ixyz(self):
        return self.__accel_ixyz

    @accel_ixyz.setter
    @peripheral._watch
    def accel_ixyz(self, val):
        if self.__accel_ixyz == 0:
            self.__accel_ixyz_avg = self.__accel_ixyz
        else:
            # s = (abs(primaCitireInclinare) + abs(imu.accel.inclination))/2
            iax, iay, iaz = val
            self.__accel_ixyz_avg = [
                (iax+self.__accel_ixyz[0])/2,
                (iay+self.__accel_ixyz[1])/2,
                (iaz+self.__accel_ixyz[2])/2
            ]

        self.__accel_ixyz = val

    @property
    def gyro_ixyz(self):
        return self.__gyro_ixyz

    @gyro_ixyz.setter
    @peripheral._watch
    def gyro_ixyz(self, val):
        if self.__gyro_ixyz == 0:
            self.__gyro_ixyz_avg = self.__gyro_ixyz
        else:
            # s = (abs(primaCitireInclinare) + abs(imu.accel.inclination))/2
            igx, igy, igz = val
            self.__gyro_ixyz_avg = [
                (igx+self.__gyro_ixyz[0])/2,
                (igy+self.__gyro_ixyz[1])/2,
                (igz+self.__gyro_ixyz[2])/2
            ]

        self.__gyro_ixyz = val

    @property
    def stopTimer(self):
        return self.__stopTimer

    @stopTimer.setter
    @peripheral._watch
    def stopTimer(self, val):

        if val in TrueValues:
            self.__stopTimer = True
            self.po.deinit()
        else:
            self.__stopTimer = False
            self.po.init(period=int(self.period), mode=Timer.PERIODIC,
                         callback=self.readData)

    @property
    def heartbeat(self):
        return self.__heartbeat

    @heartbeat.setter
    @peripheral._watch
    def heartbeat(self, val):
        self.__heartbeat = val

    def setTimer(self, enable=False, period=1000):
        if enable:
            self.period = period
            self.stopTimer = False
        else:
            self.stopTimer = True

        return self.getState()

    def getState(self):
        return {
            "period": self.period,
            "running": not self.stopTimer
        }

    def getObservableMethods(self):
        return ["command"]

    def getObservableProperties(self):
        return ["inclination", "azimuth", "elevation", "accel_ixyz", "gyro_ixyz", "heartbeat", "stopTimer", "period"]
