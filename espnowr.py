import conf
import network
from mcu import mcu
import ujson
from os import listdir
from jsu import getObservablesFileContent, applyObservablesFromJson, TrueValues, FalseValues


def file_exists(f):
    if f in listdir():
        return True
    else:
        return False


def mcuDoReboot(source, message):
    try:
        msg = ujson.loads(message)
    except ValueError:
        msg = message

    if type(msg) is str:
        if msg == "MPUREB":
            mpu.reboot()
    if type(msg) == dict:
        if msg["rebootTo"] in conf.runModes:
            print("Reboot request from "+source)
            conf.jsonConfig["run"] = msg["rebootTo"]
            conf.configFileSave()
            print("\tRebooting in "+msg["rebootTo"]+" mode")
            from machine import reset
            reset()
        else:
            print("Reboot in "+msg["rebootTo"]+" mode request skipped")


wif = network.WLAN(network.STA_IF)
wif.active(True)
if(wif.isconnected()):
    wif.disconnect()

mpu = mcu()

mpuAlias = conf.jsonConfig.get("executeStartupFile") if type(
    conf.jsonConfig.get("executeStartupFile")) == str else mpu.unique_id

espnowDriverInstance = None

if type(conf.jsonConfig["peripherals"]) is list and len(conf.jsonConfig["peripherals"]) > 0:
    for epfcfg in conf.jsonConfig["peripherals"]:
        mpu.addPeripheral(epfcfg)
        if epfcfg["type"] in ["espnowdrv"]:
            espnowDriverInstance = mpu.peripherals[-1]


if espnowDriverInstance.__class__.__name__ is "espnowdrv":
    espnowDriverInstance.addTrigger("rawMessage", "AFTER", mcuDoReboot)

    mac = "ffffffffffff"
    espnowDriverInstance.loadPeer(mac)
    espnowDriverInstance.send(msg="BCAST_REG_ALIAS/"+mpuAlias, to=mac)
    espnowDriverInstance.removePeer(mac)


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
                        "runMode": "espnow"
                    })
                except:
                    print("\tError, Bad script")
else:
    print("\tStartup script skipped")
