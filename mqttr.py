import conf
from mcu import mcu
import network
import ujson
from os import listdir
from jsu import getObservablesFileContent, applyObservablesFromJson
from commonMqttUtils import messageIsForMe


def file_exists(f):
    if f in listdir():
        return True
    else:
        return False


def deviceDirectCommandHandler(topic, message, mqttDriver):
    if messageIsForMe(message, mqttDriver.CLIENT_ID):
        if message["data"] in ["mqtt/sta", "config/sta", "config/ap"]:
            if "from" in message:
                print("Reboot request from "+message["from"])
                conf.jsonConfig["run"] = message["data"]
                conf.configFileSave()
                print("\tRebooting in "+message["data"]+" mode")
                from machine import reset
                reset()
            else:
                print("Reboot in "+message["data"]+" mode request skipped")
                print("\tfrom label not present")


def deviceStatusCommandHandler(topic, message, mqttDriver):
    if messageIsForMe(message, mqttDriver.CLIENT_ID):
        if "from" in message:
            tspkg = {
                "to": message["from"],
                "from": mqttDriver.CLIENT_ID
            }

            if "pid" in message:
                # daca mesajul are un peripheral id
                # returnex getState al periperic pid
                toSend = {}
                p_id = int(message["pid"])
                if p_id < len(mpu.peripherals) and "getState" in dir(mpu.peripherals[p_id]):
                    tspkg["pid"] = p_id
                    toSend = mpu.peripherals[p_id].getState()
            else:
                toSend = {
                    "uptime": mpu.uptime(),
                    "muid": mpu.unique_id
                }

            tspkg["data"] = ujson.dumps(toSend)

            try:
                mqttDriver.mqttInstance.publish(
                    topic, ujson.dumps(tspkg), False, 0)
            except:
                print("Error while trying to publish")


def peripheralDirectCommandHandler(topic, message, mqttDriver):
    val = message
    # din slimmqtt vine:
    # {"data": "relon", "to": "mqac67b22cca0c", "from": "altClientNume"}
    global mpu
    if val.__class__ is dict and "data" in val:
        if messageIsForMe(message, mqttDriver.CLIENT_ID):
            try:
                msgjs = ujson.loads(val["data"])
            except ValueError:
                print("Wrong JSON format")
            except:
                print("Other error")
            finally:
                cmdto = int(msgjs["pid"])
                cmdName = msgjs["cmd"]
                cmdOptions = msgjs["opt"] if "opt" in msgjs else False

                if cmdto.__class__ == int and cmdName:
                    if cmdName in mpu.peripherals[int(cmdto)].commandsList():
                        if(int(cmdto) < len(mpu.peripherals)):
                            try:
                                if not cmdOptions:
                                    mpu.peripherals[int(cmdto)].command(
                                        cmdName)
                                else:
                                    mpu.peripherals[int(cmdto)].command(
                                        cmdName, cmdOptions)
                            except Exception as e:
                                # except Exception as e:
                                print("Error while executing: " + str(e).upper())
                                print("\tCOMMAND: " + cmdName +
                                      "\twith OPTIONS " + "for dev["+str(cmdto)+"]")
                                print("\t"+val["data"])
                    else:
                        print("Not in commands list")


def devconfTopicHandler(topic, message, mqttDriver):
    global mpu

    if messageIsForMe(message, mqttDriver.CLIENT_ID):
        if "to" in message and "from" in message:
            print(topic+" request received from "+message["from"])
            byType = {}
            for bt in mpu.peripheralsByType:
                byType[bt] = len(mpu.peripheralsByType[bt])

            byAlias = {}
            for ba in mpu.peripheralsByAlias:
                byAlias[ba] = mpu.peripheralsByAlias[ba].pType

            wifiName = None

            if "aps" in conf.jsonConfig.keys() and len(conf.jsonConfig["aps"]) > 0:
                wifiName = next(iter(conf.jsonConfig["aps"]))

            toSend = {
                "peripherals": [],
                "defaultPeripheral": conf.jsonConfig["defaultPeripheral"] if "defaultPeripheral" in conf.jsonConfig else 0,
                "byType": byType,
                "byAlias": byAlias,
                "muid": mpu.unique_id,
                "deviceid": mqttDriver.CLIENT_ID,
                "alias": conf.jsonConfig["alias"] if "alias" in conf.jsonConfig else mpu.unique_id,
                "hotspot": wifiName if wifiName is not None else "Not set",
                "network": mpu.wifi.ifconfig()
            }

            pid = 0
            for bt in mpu.peripherals:
                po = {}
                po["id"] = pid
                po["type"] = bt.pType
                po["alias"] = bt.alias
                po["commands"] = bt.commandsList()
                # po["observableMethods"] = bt.getObservableMethods()
                # po["observableProperties"] = bt.getObservableProperties()
                toSend["peripherals"].append(po)
                pid += 1

            # nu merge ?!
            # mqttDriver.send(ujson.dumps(toSend), message["from"], topic)
            tspkg = {
                "data": ujson.dumps(toSend),
                "to": message["from"],
                "from": mqttDriver.CLIENT_ID
            }
            try:
                mqttDriver.mqttInstance.publish(
                    topic, ujson.dumps(tspkg), False, 0)
            except:
                print("Error while trying to publish")


mpu = mcu()
mpu.wifi.active(True)
mqtt = None

if type(conf.jsonConfig["peripherals"]) is list and len(conf.jsonConfig["peripherals"]) > 0:
    for epfcfg in conf.jsonConfig["peripherals"]:
        mpu.addPeripheral(epfcfg)
        if epfcfg["type"] in ["mqtt", "mqtta", "mqttht"]:
            mqtt = mpu.peripherals[-1]

if "applyObservablesOnBoot" in conf.jsonConfig and conf.jsonConfig["applyObservablesOnBoot"]:
    oconf = ujson.loads(getObservablesFileContent(conf.observablesFile))

    for xi in range(len(mpu.peripherals)):
        print("\t Applying observables at boot for peripheral "+str(xi))
        if str(xi) in oconf["observables"] and len(oconf["observables"][str(xi)]) > 0:
            obsrvbToExec = oconf["observables"][str(xi)]
            applyObservablesFromJson(xi, obsrvbToExec, mpu)
        else:
            print("\t\tNone found for it")

if mqtt.__class__.__bases__[0].__name__ == 'peripheral':
    print("MQTT driver found, attaching predefined topic handlers")
    mqtt.topicHandlers[conf.DEVICE_CONFIG] = devconfTopicHandler
    mqtt.topicHandlers[conf.PERIPHERAL_CMDS] = peripheralDirectCommandHandler
    mqtt.topicHandlers[conf.DEVICE_CMDS] = deviceDirectCommandHandler
    mqtt.topicHandlers[conf.STATUS_UPDATE_TOPIC] = deviceStatusCommandHandler

if conf.startupFile:
    if file_exists(conf.startupFile):
        # incarc fisier configurare
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
