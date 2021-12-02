from jss import jss
import mcu
import ujson

m = mcu.mcu()

m.wlanAPMode(True)
m.wifi.active(True)

# Motor 1
m.addPeripheral({"type": 'fet', "initOptions": {"pinOut": 16}})
p16 = m.peripheralsByType['fet'][0]
p16.duty = 0


m.addPeripheral({"type": 'fet', "initOptions": {"pinOut": 17}})
p17 = m.peripheralsByType['fet'][1]
p17.duty = 0

ml = {"f": p16, "r": p17}


# Motor 2
m.addPeripheral({"type": 'fet', "initOptions": {"pinOut": 25}})
p25 = m.peripheralsByType['fet'][2]
p25.duty = 0


m.addPeripheral({"type": 'fet', "initOptions": {"pinOut": 26}})
p26 = m.peripheralsByType['fet'][3]
p26.duty = 0


mr = {"f": p25, "r": p26}


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


# SERVER

def home(REQUEST):
    contentType = "application/javascript"
    http_status = "200 OK"

    toSend = {
        "freq": "freq",
        "duty": "",
        "SERVER": REQUEST
    }

    mlv = int(REQUEST["GET"]["ml"]) if "ml" in REQUEST["GET"].keys() else None
    mrv = int(REQUEST["GET"]["mr"]) if "mr" in REQUEST["GET"].keys() else None

    if mlv.__class__.__name__ == "int":
        if mlv > 0:
            fw(ml, mlv)
        if mlv < 0:
            rv(ml, -1*mlv)
        if mlv == 0:
            st(ml)

    if mrv.__class__.__name__ == "int":
        if mrv > 0:
            fw(mr, mrv)
        if mrv < 0:
            rv(mr, -1 * mrv)
        if mrv == 0:
            st(mr)

    return (contentType, http_status, toSend)


def splitPath(path):
    return path.strip("/").split("/")


def parsePath(path):
    return "/"


def file_exists(f):
    if f in listdir():
        return True
    else:
        return False


j = jss(verbose=False)
j.routeHandler = parsePath

j.route["/"] = home


j.start()
