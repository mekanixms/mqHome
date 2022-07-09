import conf
from mcu import mcu
import network
import ujson
from os import listdir
from jsu import getObservablesFileContent, applyObservablesFromJson, TrueValues, FalseValues


def file_exists(f):
    if f in listdir():
        return True
    else:
        return False






mpu = mcu()

w0 = network.WLAN(network.STA_IF)
w0.active(True)


if type(conf.jsonConfig["peripherals"]) is list and len(conf.jsonConfig["peripherals"]) > 0:
    for epfcfg in conf.jsonConfig["peripherals"]:
        mpu.addPeripheral(epfcfg)
        # if epfcfg["type"] in ["mqtt", "mqtta", "mqttht"]:
        #     mqtt = mpu.peripherals[-1]





applyObservables = False
scriptFilename = __file__.split('.')[0]

if "applyObservablesOnBoot" in conf.jsonConfig:
    if conf.jsonConfig["applyObservablesOnBoot"].__class__.__name__ == 'str':
        if scriptFilename in conf.jsonConfig["applyObservablesOnBoot"].split("|"):
            applyObservables = True
        else:
            if conf.jsonConfig.get("applyObservablesOnBoot") in TrueValues:
                applyObservables = True
    else:
        if conf.jsonConfig["applyObservablesOnBoot"].__class__.__name__ == 'bool':
            applyObservables = conf.jsonConfig["applyObservablesOnBoot"]

if applyObservables:
    oconf = ujson.loads(getObservablesFileContent(conf.observablesFile))

    for xi in range(len(mpu.peripherals)):
        print("Applying observables at boot for peripheral "+str(xi))
        if str(xi) in oconf["observables"] and len(oconf["observables"][str(xi)]) > 0:
            obsrvbToExec = oconf["observables"][str(xi)]
            applyObservablesFromJson(xi, obsrvbToExec, mpu)
        else:
            print("\tNone found for it")
else:
    print("\tObservables not applied")





executeStartupFile = True

if "executeStartupFile" in conf.jsonConfig:
    if conf.jsonConfig.get("executeStartupFile").__class__.__name__ == 'str':
        if scriptFilename not in conf.jsonConfig.get("executeStartupFile").split("|"):
            executeStartupFile = False
        else:
            if conf.jsonConfig.get("executeStartupFile") in FalseValues:
                executeStartupFile = False
    else:
        if conf.jsonConfig.get("executeStartupFile").__class__.__name__ == 'bool':
            executeStartupFile = conf.jsonConfig.get("executeStartupFile")

if executeStartupFile:
    if conf.startupFile:
        if file_exists(conf.startupFile):
            scfg = open(conf.startupFile, "r")
            scfgContent = scfg.readlines()
            scfg.close()

            if len(scfgContent) > 0:
                print("Running Startup script")
                try:
                    exec("".join(scfgContent), {
                        "dev": mpu.peripherals,
                        "mpu": mpu,
                        "runMode": "mqtt"
                        })
                except:
                    print("\tError, Bad script")
else:
    print("\tStartup script skipped")
