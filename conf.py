import os
import json

# http server port
http_server_port = 8080

# valori default
cfgf = configFilename = "apl.json"
# peripherals definitions
pcfg = "pph.json"
observablesFile = "observables.json"
startupFile = "startup.run"

# run = "config/sta"  sau config/ap sau mqtt/sta
run = "config/ap"
mosquitto_server = "10.11.1.115"
mosquitto_port = 1883
mosquitto_user = "mqhome"
mosquitto_pass = "userpass"
mosquitto_reconnect = True
group = "default"

BROADCAST_ONLINE = "DEVONLINE"
BROADCAST_LASTWILL = "DEVLASTWILL"
PRESENCE = "PRESENCE"
STATUS_UPDATE_TOPIC = 'statusupdate'
DEVICE_CONFIG = "DEVCONF"
PERIPHERAL_CMDS = "mqperipheralcmds"
DEVICE_CMDS = "mqdevcmds"
defaultTopic = "mqhomeintercom"
jsonConfig = {}

runModes = ["mqtt/sta", "config/sta", "config/ap", "espnow/ap","espnow/sta"]


# default valoarea pt releu
pinModeSwitch = 35
pinBtn1 = 25
pinBtn2 = 27
pinDevStatusLED = 2


def file_exists(f):
    if f in os.listdir():
        return True
    else:
        return False


def configFileSave(**saveInfo):
    global configFilename, jsonConfig

    cfn = configFilename
    obj = jsonConfig

    if "fn" in saveInfo:
        cfn = saveInfo["fn"]
    if "data" in saveInfo:
        obj = saveInfo["data"]

    if "peripherals" in jsonConfig:
        jsonConfig.pop("peripherals")

    configFile = open(cfn, "w")
    configFile.write(json.dumps(obj))
    configFile.close()


# import continut json in var jsonConfig
if file_exists(cfgf):
    # incarc fisier configurare
    configFile = open(cfgf, "r")
    configFileContent = configFile.readlines()

    if len(configFileContent) > 0:
        jsonConfig = json.loads("".join(configFileContent))
    else:
        jsonConfig = {"aps": {}}

    configFile.close()
else:
    jsonConfig = {"aps": {}}


jsonConfig["peripherals"] = []
if file_exists(pcfg):
    # incarc fisier configurare
    pcfg = open(pcfg, "r")
    pcfgContent = pcfg.readlines()

    if len(pcfgContent) > 0:
        jsonConfig["peripherals"] = json.loads("".join(pcfgContent))

    pcfg.close()

# suprascriu valorile default daca se gasesc in json
if "configFilename" in jsonConfig:
    configFilename = jsonConfig["configFilename"]

if "run" in jsonConfig:
    run = jsonConfig["run"]

if "mosquitto_server" in jsonConfig:
    mosquitto_server = jsonConfig["mosquitto_server"]

if "mosquitto_user" in jsonConfig:
    mosquitto_user = jsonConfig["mosquitto_user"]

if "mosquitto_pass" in jsonConfig:
    mosquitto_pass = jsonConfig["mosquitto_pass"]

if "group" in jsonConfig:
    group = jsonConfig["group"]

if "pinModeSwitch" in jsonConfig:
    pinModeSwitch = jsonConfig["pinModeSwitch"]

if "pinBtn1" in jsonConfig:
    pinBtn1 = jsonConfig["pinBtn1"]

if "pinBtn2" in jsonConfig:
    pinBtn2 = jsonConfig["pinBtn2"]
