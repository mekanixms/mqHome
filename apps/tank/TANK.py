import mcu
import network

wap = network.WLAN(network.AP_IF)
wap.active(True)

wif = network.WLAN(network.STA_IF)
wif.active(True)
if wif.isconnected():
    wif.disconnect()

m = mcu.mcu()


m.addPeripheral({"type": 'espnowdrv',
                 "initOptions": {
                     "autostart": True, "broadcast": True, "wap_channel": 10
                 }})

e = m.peripherals[0]

# Motor 1
m.addPeripheral({"type": 'fet', "initOptions": {"pinOut": 16}})
p16 = m.peripheralsByType['fet'][0]
p16.duty = 0


m.addPeripheral({"type": 'fet', "initOptions": {"pinOut": 17}})
p17 = m.peripheralsByType['fet'][1]
p17.duty = 0


# Motor 2
m.addPeripheral({"type": 'fet', "initOptions": {"pinOut": 21}})
p21 = m.peripheralsByType['fet'][2]
p21.duty = 0


m.addPeripheral({"type": 'fet', "initOptions": {"pinOut": 22}})
p22 = m.peripheralsByType['fet'][3]
p22.duty = 0


ml = {"f": p16, "r": p17}
mr = {"f": p21, "r": p22}


def fw(motor, speed):
    # forward
    motor["r"].duty = 0
    motor["f"].duty = int(speed)


def rv(motor, speed):
    # reverse
    motor["f"].duty = 0
    motor["r"].duty = int(speed)


def st(motor):
    # stop
    motor["f"].duty = 0
    motor["r"].duty = 0


def runMotor(m, speed):
    s = speed
    if s != 0:
        sign = speed/abs(speed)
        if abs(speed) > 1023:
            s = 1023*sign

    if s > 0:
        fw(m, s)
    else:
        rv(m, -1*s) if s < 0 else st(m)


def drive(source, message):
    # ml mr
    # 130;233
    mParts = message.split(";")
    if len(mParts) == 2:
        runMotor(ml, int(mParts[0]))
        runMotor(mr, int(mParts[1]))


e.addTrigger("rawMessage", "BEFORE", drive)
