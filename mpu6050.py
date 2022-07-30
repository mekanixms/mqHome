from peripheral import peripheral, TrueValues
from machine import SoftI2C, Pin, Timer
from imu import MPU6050
from sys import platform
from math import atan, atan2, sqrt, pi


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
            scl = 5 if "scl" not in self.settings else int(
                self.settings["scl"])
            sda = 4 if "sda" not in self.settings else int(
                self.settings["sda"])

            self.i2c = SoftI2C(scl=Pin(scl), sda=Pin(sda))
        else:
            if self.isESP32:
                # hardware i2c canal 1 scl 18 sda 19
                # self.i2c = I2C(0)
                scl = 18 if "scl" not in self.settings else int(
                    self.settings["scl"])
                sda = 19 if "sda" not in self.settings else int(
                    self.settings["sda"])

                self.i2c = SoftI2C(scl=Pin(scl), sda=Pin(sda))

        self.imu = MPU6050(self.i2c)
        self.__inclination = 0
        self.__azimuth = 0
        self.__elevation = 0
        self.__accel_xyz = 0
        self.__gyro_xyz = 0
        self.__accel_ixyz = 0
        self.__gyro_ixyz = 0

        self.period = 1000
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
        # self.inclinationChange(
        #     inclination=self.imu.accel.inclination, imu=self.imu)
        # self.azimuthChange(azimuth=self.imu.accel.azimuth, imu=self.imu)
        # self.elevationChange(elevation=self.imu.accel.elevation, imu=self.imu)
        xyz = self.imu.accel.xyz
        self.accel_change(accel_xyz=xyz,
                          gyro_xyz=self.imu.gyro.xyz,
                          roll=self.roll(xyz),
                          pitch=self.pitch(xyz),
                          yaw=self.yaw(xyz),
                          imu=self.imu)
        # self.gyro_xyzChange(gyro_xyz=self.imu.gyro.xyz, imu=self.imu)
        # self.accel_ixyzChange(accel_ixyz=self.imu.accel.ixyz, imu=self.imu)
        # self.gyro_ixyzChange(gyro_ixyz=self.imu.gyro.ixyz, imu=self.imu)
        self.heartbeat = not self.heartbeat

    @peripheral._trigger
    def accel_change(self, accel_xyz, gyro_xyz, roll, pitch, yaw, imu):
        pass

    # @peripheral._trigger
    # def inclinationChange(self, inclination, imu):
    #     pass

    # @peripheral._trigger
    # def azimuthChange(self, azimuth, imu):
    #     pass

    # @peripheral._trigger
    # def elevationChange(self, elevation, imu):
    #     pass

    # @peripheral._trigger
    # def gyro_xyzChange(self, gyro_xyz, imu):
    #     pass

    # @peripheral._trigger
    # def accel_ixyzChange(self, accel_ixyz, imu):
    #     pass

    # @peripheral._trigger
    # def gyro_ixyzChange(self, gyro_ixyz, imu):
    #     pass

    def roll(self, xyz):
        # x, y, z = self.imu.accel.xyz
        x, y, z = xyz
        return atan2(y, z) * 180.0 / pi

    def pitch(self, xyz):
        # x, y, z = self.imu.accel.xyz
        x, y, z = xyz
        return atan2(-x, sqrt(y * y + z * z)) * 180.0 / pi

    def yaw(self, xyz):
        # x, y, z = self.imu.accel.xyz
        x, y, z = xyz
        # yaw = 180 * atan (accelerationZ/sqrt(accelerationX*accelerationX + accelerationZ*accelerationZ))/M_PI;
        return 180 * atan(z/sqrt(x*x + z*z)) / pi

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
        return ["command",
                #  "inclinationChange", "azimuthChange", "elevationChange", "accel_ixyzChange", "gyro_ixyzChange",
                "accel_change"
                #  ,"gyro_xyzChange"
                ]

    def getObservableProperties(self):
        return ["heartbeat", "stopTimer", "period"]
