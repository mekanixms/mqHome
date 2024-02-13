from peripheral import peripheral, TrueValues
from machine import SoftI2C, Pin, Timer
from mpu9250 import MPU9250
from sys import platform
from math import atan, atan2, sqrt, pi
from fusion import Fusion
from time import sleep_ms, ticks_us, ticks_diff
import json
from utils import file_exists, is_number

# TODO:
# - implement Calibrate cu swtich Pin 4 ca in FuseTest
# - declination


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


timerRunning = None


def sw(s):
    global timerRunning
    return not timerRunning


def calibrate_timcbk(t):
    global timerRunning
    timerRunning = False


def getmag(s):
    return s.imu.mag.xyz


class imu9250(peripheral):
    po = False
    isESP8266 = True if platform == 'esp8266' else False
    isESP32 = True if platform == 'esp32' else False

    period = 1000
    fuseUpdateTime = 1000
    doCalibrate = False
    calibrationPeriod = 20000
    declination = 0

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
                scl = 19 if "scl" not in self.settings else int(
                    self.settings["scl"])
                sda = 18 if "sda" not in self.settings else int(
                    self.settings["sda"])

                self.i2c = SoftI2C(scl=Pin(scl), sda=Pin(sda))

        self.imu = MPU9250(self.i2c)

        self.__stopTimer = True
        self.po = Timer(int(self.settings.get("id")))
        self.__heartbeat = True

        self.commands["start"] = enable
        self.commands["stop"] = disable
        self.commands["toggle"] = toggle
        self.commands["setPeriod"] = setPeriod

        if "calibrate" in self.settings:
            if self.settings["calibrate"] in TrueValues:
                self.doCalibrate = True
            else:
                if callable(self.settings["calibrate"]):
                    calibrate_call_method = self.settings["calibrate"]
                    self.doCalibrate = calibrate_call_method(self)

        if "declination" in self.settings:
            if callable(self.settings["declination"]):
                declination_call_method = self.settings["declination"]
                self.declination = declination_call_method()
            else:
                if is_number(self.settings["declination"]):
                    self.declination = float(self.settings["declination"])

        self.fuse = Fusion()

        self.magConfig = {}
        self.pcfgName = "fusioncalibration.conf"
        pcfg = None

        if file_exists(self.pcfgName):
            pcfg = open(self.pcfgName, "r")
            pcfgContent = pcfg.readlines()

            if len(pcfgContent) > 0:
                self.magConfig = json.loads("".join(pcfgContent))

            pcfg.close()

        if "mag_calibration" in self.magConfig:
            self.fuse.magbias = self.magConfig["mag_calibration"]
            print("CALIBRATION loaded into fusion: \t " +
                  str(self.magConfig["mag_calibration"]))
        if "fuseUpdateTime" in self.magConfig:
            print("FUSE update time loaded: " +
                  str(self.magConfig["fuseUpdateTime"]))
            self.fuseUpdateTime = self.magConfig["fuseUpdateTime"]

        if self.doCalibrate:
            self.calibrate()

    def calibrate(self, period=None):
        global timerRunning
        if period is None:
            period = self.calibrationPeriod

        print("Calibrating for "+str(period)+" uS")
        timerRunning = True
        self.po.init(period=period, mode=0,
                     callback=calibrate_timcbk)
        self.fuse.calibrate(lambda: getmag(self),
                            lambda: sw(self),
                            lambda: sleep_ms(100))
        # self.fuse.calibrate(getmag, sw, 20000)
        print(self.fuse.magbias)
        self.magConfig["mag_calibration"] = self.fuse.magbias

        mag = self.imu.mag.xyz
        accel = self.imu.accel.xyz
        gyro = self.imu.gyro.xyz
        start = ticks_us()
        self.fuse.update(accel, gyro, mag)
        self.fuseUpdateTime = ticks_diff(ticks_us(), start)
        print("Update time (uS):", self.fuseUpdateTime)
        self.magConfig["fuseUpdateTime"] = self.fuseUpdateTime

        cf = open(self.pcfgName, "w")
        cf.write(json.dumps(self.magConfig))
        cf.close()

    def deinit(self):
        pass

    def readData(self, t):
        axyz = self.imu.accel.xyz
        gxyz = self.imu.gyro.xyz
        mxyz = self.imu.mag.xyz
        self.fuse.update(axyz, gxyz, mxyz)
        self.accel_change(accel_xyz=axyz,
                          gyro_xyz=gxyz,
                          roll=self.fuse.roll,
                          pitch=self.fuse.pitch,
                          yaw=self.fuse.heading+self.declination,
                          imu=self.imu)
        self.heartbeat = not self.heartbeat

    @peripheral._trigger
    def accel_change(self, accel_xyz, gyro_xyz, roll, pitch, yaw, imu):
        pass

    def roll(self, xyz=None):
        yo = 0
        if xyz == None:
            yo = self.fuse.roll
        else:
            x, y, z = xyz
            yo = atan2(y, z) * 180.0 / pi
        return yo

    def pitch(self, xyz=None):
        yo = 0
        if xyz == None:
            yo = self.fuse.pitch
        else:
            x, y, z = xyz
            yo = atan2(-x, sqrt(y * y + z * z)) * 180.0 / pi
        return yo

    def yaw(self, xyz=None):
        yo = 0
        if xyz == None:
            yo = self.fuse.heading+self.declination
        else:
            x, y, z = xyz
            yo = 180 * atan(z/sqrt(x*x + z*z)) / pi
        return yo

    @property
    def stopTimer(self):
        return self.__stopTimer

    @stopTimer.setter
    @peripheral._watch
    def stopTimer(self, val):
        if self.po != None:
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
                "accel_change"]

    def getObservableProperties(self):
        return ["heartbeat", "stopTimer", "period"]
