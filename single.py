import conf
from mcu import mcu
import network
import ujson
from os import listdir
from jsu import getObservablesFileContent, applyObservablesFromJson


def file_exists(f):
    if f in listdir():
        return True
    else:
        return False


beVerbose = False

wifiHotspots = []

mpu = mcu()
mpu.wifi = network.WLAN()
mpu.wifi.active(False)

if type(conf.jsonConfig["peripherals"]) is list and len(conf.jsonConfig["peripherals"]) > 0:
    for epfcfg in conf.jsonConfig["peripherals"]:
        mpu.addPeripheral(epfcfg)

if "applyObservablesOnBoot" in conf.jsonConfig and conf.jsonConfig["applyObservablesOnBoot"]:
    oconf = ujson.loads(getObservablesFileContent(conf.observablesFile))

    for xi in range(len(mpu.peripherals)):
        print("\t Applying observables at boot for peripheral "+str(xi))
        if str(xi) in oconf["observables"] and len(oconf["observables"][str(xi)]) > 0:
            obsrvbToExec = oconf["observables"][str(xi)]
            applyObservablesFromJson(xi, obsrvbToExec, mpu)
        else:
            print("\t\tNone found for it")

if conf.startupFile:
    if file_exists(conf.startupFile):
        # incarc fisier configurare
        scfg = open(conf.startupFile, "r")
        scfgContent = scfg.readlines()
        scfg.close()

        if len(scfgContent) > 0:
            print("Running Startup script")
            try:
                exec("".join(scfgContent), {}, {"dev": mpu.peripherals})
            except:
                print("\tError, Bad script")
