import conf
import jsu
from os import remove
from jss import jss
from jssu import unquote
from mcu import mcu
import network
import ujson
from os import listdir
from commonMqttUtils import messageIsForMe


def configHandler(REQUEST):
    contentType = "application/javascript"
    http_status = "200 OK"

    p = splitPath(REQUEST["PATH"])
    todo = p[1]
    done = False
    toSend = {"uptime": mpu.uptime()}

    if not done:
        if len(p) == 2:
            done = True
            #   /conf/view
            if todo == "view":
                toSend["view"] = conf.jsonConfig

            toSend["do"] = todo
            toSend["done"] = done

    if not done:
        if len(p) == 3:
            done = True
            whattodo = ""
            #   /conf/st/saved
            #   /conf/st/static?toip=..&netmask=...&gw=...&dns=...
            #   /conf/st/dhcp
            if todo == "st":
                whattodo = p[2]
                if whattodo == "static":
                    toip = REQUEST["GET"]["toip"] if "toip" in REQUEST["GET"].keys(
                    ) else None
                    nm = REQUEST["GET"]["netmask"] if "netmask" in REQUEST["GET"].keys(
                    ) else None
                    gw = REQUEST["GET"]["gw"] if "gw" in REQUEST["GET"].keys(
                    ) else None
                    dns = REQUEST["GET"]["dns"] if "dns" in REQUEST["GET"].keys(
                    ) else None
                    if toip and nm and gw and dns:
                        conf.jsonConfig["staticip"] = (toip, nm, gw, dns)
                        toSend["static"] = conf.jsonConfig["staticip"]
                        conf.configFileSave()
                    else:
                        toSend["error"] = "ip or netmask or gw or dns empty"

                if whattodo == "dhcp":
                    if "staticip" in conf.jsonConfig.keys():
                        conf.jsonConfig.pop("staticip", None)
                    toSend["dhcp"] = "set"
                    conf.configFileSave()

                if whattodo == "saved":
                    toSend["aps"] = conf.jsonConfig["aps"] if "aps" in conf.jsonConfig.keys(
                    ) else None

            toSend["do"] = whattodo
            toSend["done"] = done

    if not done:
        if len(p) == 4:
            done = True
            #   /conf/key/set/numek?value=
            #   /conf/key/get/numek
            whattodo = p[2].strip(" ")

            if todo == "key":
                if whattodo == "set":
                    confkn = p[3].strip(" ").replace("%20", " ")
                    confkv = REQUEST["GET"].get("value").strip(" ").replace(
                        "%20", " ") if "value" in REQUEST["GET"].keys() else None
                    if confkn:
                        conf.jsonConfig[confkn] = confkv
                        toSend[confkn] = conf.jsonConfig[confkn]
                    else:
                        toSend["error"] = "NOT SET"

                if whattodo == "get":
                    confkn = p[3].strip(" ").replace("%20", " ")
                    confkv = conf.jsonConfig.get(confkn)
                    if type(confkv) != None.__class__:
                        toSend[confkn] = confkv
                    else:
                        toSend["error"] = "NOT SET"

                conf.configFileSave()

            toSend["do"] = todo
            toSend["done"] = done

    if not done:
        if len(p) == 5:
            done = True
            #   /conf/st/save/ssidName/parola
            whattodo = p[2].strip(" ")
            if todo == "st":
                if whattodo == "save":
                    stname = p[3].strip(" ")
                    stpass = p[4].strip(" ")
                    conf.jsonConfig["aps"] = {}
                    conf.jsonConfig["aps"][stname] = stpass
                    conf.configFileSave()
            # /conf/ap/save/numeRetea/parola
            if todo == "ap":
                if whattodo == "save":
                    apname = p[3].strip(" ").replace("%20", " ")
                    appass = p[4].strip(" ").replace("%20", " ")
                    conf.jsonConfig["apssid"] = apname
                    conf.jsonConfig["appass"] = appass
                    conf.configFileSave()

            toSend["do"] = todo
            toSend["done"] = done

    return (contentType, http_status, toSend)


def machineHandler(REQUEST):
    contentType = "application/json"
    http_status = "200 OK"
    toSend = {"uptime": mpu.uptime()}
    # draft request:
    #   /machine/reboot
    #   /machine/peripherals
    #  /machine/startup
    p = splitPath(REQUEST["PATH"])
    todo = p[1]
    if todo == "reboot":
        from machine import reset
        reset()
    if todo == "startup":
        if "muid" in REQUEST["POST"] and mpu.unique_id == REQUEST["POST"]["muid"].strip():
            startupScript = REQUEST["POST"]["set"] if "set" in REQUEST["POST"].keys(
            ) else None
            if startupScript:
                configFile = open(conf.startupFile, "w")
                configFile.write(unquote(startupScript))
                configFile.close()
                toSend["saved"] = "done"
            else:
                toSend["error"] = "data not saved"
        else:
            toSend["error"] = "id match error"

    if todo == "peripherals":
        toSend = []
        pid = 0
        for bt in mpu.peripherals:
            po = {}
            po["id"] = pid
            po["type"] = bt.pType
            po["alias"] = bt.alias
            toSend.append(po)
            pid += 1

    return (contentType, http_status, toSend)


def netHandler(REQUEST):
    global wifiHotspots
    # ESTE NECESAR IN JSON SERVER?? poate doar st/connected st/list si ap/connected
    # contentType = REQUEST["HEADER"]["Accept"]
    contentType = "application/javascript"
    http_status = "200 OK"

    # draft request:
    #   /net/ap/enable
    #   /net/ap/started
    #   /net/st/list   face wifi.scan()
    #   /net/st/connected
    #   /net/st/enable
    # - se conecteaza la ce am salvat in /conf/st/save
    #   /net/st/connect/wifiName/wifiPass
    # - se conecteaza la acesta
    p = splitPath(REQUEST["PATH"])
    todo = p[1]
    done = False
    toSend = {"uptime": mpu.uptime()}

    if not done:
        if len(p) == 3:
            done = True
            whattodo = p[2].strip(" ")

            if todo == "ap":
                if whattodo == "started":
                    toSend["started"] = mpu.wifi.isconnected()
                    toSend["ifconfig"] = mpu.wifi.ifconfig()

                if whattodo == "enable":
                    mpu.wlanAPMode(True)

            if todo == "st":
                if whattodo == "connected":
                    toSend["connected"] = mpu.wifi.isconnected()
                    if toSend["connected"]:
                        toSend["ifconfig"] = mpu.wifi.ifconfig()

                if whattodo == "enable":
                    mpu.wlanSTMode(True)

                if whattodo == "list":
                    if mpu.wifi.__class__.__name__ == "WLAN":
                        n = mpu.wifi
                    else:
                        import network
                        n = network.WLAN()
                        n.active(True)

                    toSend["aps"] = []
                    wifiHotspots = n.scan()

                    if len(wifiHotspots) > 0:
                        for ap in wifiHotspots:
                            toSend["aps"].append({
                                "essid": ap[0].decode("utf-8"),
                                # "mac": ap[1],#da eroare la transfer json
                                "rssid": ap[3]
                            })
                    else:
                        toSend["error"] = "Retry scanning"

            toSend["do"] = todo
            toSend["done"] = done

    return (contentType, http_status, toSend)


def homeHandler(REQUEST):
    contentType = "application/javascript"
    http_status = "200 OK"

    byType = {}
    for bt in mpu.peripheralsByType:
        byType[bt] = len(mpu.peripheralsByType[bt])

    byAlias = {}
    for ba in mpu.peripheralsByAlias:
        byAlias[ba] = mpu.peripheralsByAlias[ba].pType

    toSend = {
        "peripherals": [],
        "byType": byType,
        "byAlias": byAlias,
        "uptime": mpu.uptime(),
        "muid": mpu.unique_id
    }

    pid = 0
    for bt in mpu.peripherals:
        po = {}
        po["id"] = pid
        po["type"] = bt.pType
        po["alias"] = bt.alias
        po["commands"] = bt.commandsList()
        po["observableMethods"] = bt.getObservableMethods()
        po["observableProperties"] = bt.getObservableProperties()
        toSend["peripherals"].append(po)
        pid += 1

    return (contentType, http_status, toSend)


def commandHandler(REQUEST):
    # /cmd/devid/type
    # /cmd/devid/commands
    # /cmd/devid/state
    # /cmd/devid/cmdName/?options
    contentType = "application/javascript"
    http_status = "200 OK"
    toSend = {"uptime": mpu.uptime()}

    p = splitPath(REQUEST["PATH"])
    deviceID = int(p[1])
    cmdName = p[2]

    if cmdName == "type":
        toSend["type"] = mpu.peripherals[deviceID].pType
    else:
        # "/observable/?what=properties"
        # "/observable/?what=methods"
        if cmdName == "observable":
            if "what" in REQUEST["GET"]:
                if REQUEST["GET"]["what"] == "methods":
                    toSend["methods"] = mpu.peripherals[deviceID].getObservableMethods()
                if REQUEST["GET"]["what"] == "properties":
                    toSend["properties"] = mpu.peripherals[deviceID].getObservableProperties()
            else:
                toSend["properties"] = [""]
        else:
            if cmdName == "observables":

                setObservables = REQUEST["GET"]["set"] if "set" in REQUEST["GET"].keys(
                ) else None
                applyObservables = REQUEST["GET"]["apply"] if "apply" in REQUEST["GET"].keys(
                ) else None
                loadObservables = REQUEST["GET"]["load"] if "load" in REQUEST["GET"].keys(
                ) else None
                resetObservables = REQUEST["GET"]["reset"] if "reset" in REQUEST["GET"].keys(
                ) else None

                if setObservables:
                    receivedObservables = ujson.loads(
                        unquote(REQUEST["GET"]["set"]))

                    jsu.saveObservables(receivedObservables,
                                        conf.observablesFile)

                    toSend["observables"] = "saved"

                if applyObservables:
                    print("Applying observables for "+str(deviceID))
                    toSend["observables"] = "applied"
                    oconf = ujson.loads(
                        jsu.getObservablesFileContent(conf.observablesFile))
                    obsrvbToExec = oconf["observables"][str(deviceID)]
                    print(obsrvbToExec)

                    toSend["applied"] = obsrvbToExec

                    jsu.applyObservablesFromJson(deviceID, obsrvbToExec, mpu)

                if resetObservables:
                    toSend["reset"] = {"peripheral": REQUEST["GET"]["reset"]}
                    oconf = ujson.loads(
                        jsu.getObservablesFileContent(conf.observablesFile))

                    if int(REQUEST["GET"]["reset"]) <= len(mpu.peripherals):
                        mpu.peripherals[int(REQUEST["GET"]["reset"])].watchers = {
                            "BEFORE": [], "AFTER": []}
                        mpu.peripherals[int(REQUEST["GET"]["reset"])].triggers = {
                            "BEFORE": [], "AFTER": []}

                    if REQUEST["GET"]["reset"] in oconf["observables"]:
                        oconf["observables"][REQUEST["GET"]["reset"]] = {}
                        jsu.saveJsonToObservablesFile(
                            oconf, conf.observablesFile)
                        toSend["reset"] = "DONE"

                    toSend["error"] = "none"

                if loadObservables:
                    toSend["load"] = {}
                    oconf = ujson.loads(
                        jsu.getObservablesFileContent(conf.observablesFile))
                    if REQUEST["GET"]["load"] in oconf["observables"]:
                        toSend["load"] = oconf["observables"][REQUEST["GET"]["load"]]

                    toSend["error"] = "none"

            else:
                if cmdName == "commands":
                    toSend["commands"] = list(
                        mpu.peripherals[deviceID].commandsList())
                else:
                    if cmdName == "state":
                        toSend["state"] = mpu.peripherals[deviceID].getState()
                    else:
                        # m.peripherals[0].command("freq",{"value":2})
                        # http://10.11.1.51:8080/cmd/0/freq?value=2

                        # m.peripherals[0].command("mode",{"pwm":True})
                        # http://10.11.1.51:8080/cmd/0/mode?pwm=True

                        # m.peripherals[0].command("on")
                        # http://10.11.1.51:8080/cmd/0/on

                        cmdto = p[1] if len(p) > 2 else ""
                        cmdName = p[2] if len(p) > 2 else ""
                        cmdOptions = REQUEST["GET"] if len(
                            REQUEST["GET"]) > 0 else ""

                        if cmdto and cmdName:
                            if cmdName in mpu.peripherals[int(cmdto)].commandsList():
                                crv = "DID NOT WORKED"
                                if(int(cmdto) < len(mpu.peripherals)):
                                    print("EXECUTING COMMAND: " +
                                          cmdName + " with OPTIONS")
                                    print(ujson.dumps(cmdOptions))
                                    crv = mpu.peripherals[int(cmdto)].command(
                                        cmdName, cmdOptions)
                                toSend = {"result": crv}
                            else:
                                toSend["error"] = cmdName + \
                                    " not in commands list"

    return (contentType, http_status, toSend)


def notfoundHandler(REQUEST):
    contentType = "application/javascript"
    http_status = "404 Not Found"

    toSend = {
        "RESOURCE": "NOT AVAILABLE",
        "uptime": mpu.uptime()
    }
    return (contentType, http_status, toSend)


def messageHandler(REQUEST):
    # http://10.11.1.61:8080/message?data=SOMEDATA
    # ca sa trimitem, mai jos cum se apeleaza emiter
    # http://10.11.1.61:8080/cmd/#/message?value=SOMEDATA
    # http://10.11.1.61:8080/cmd/#/send?to=10.11.1.61
    contentType = "application/json"
    http_status = "200 OK"

    if "receiver" in mcu.peripheralsByType and len(mcu.peripheralsByType["receiver"]) > 0:
        receiver = mcu.peripheralsByType["receiver"][0]
        toSend = {
            "msg": "received",
            "uptime": mpu.uptime()
        }

        if "data" in REQUEST["QUERY"]:
            receiver.message = REQUEST["QUERY"]["data"]
        else:
            toSend["msg"] = "pong"
    else:
        toSend = {
            "error": "receiver not found"
        }

    return (contentType, http_status, toSend)


def mqttsetupHandler(REQUEST):
    # /mqttsetup/topic/set?script=...
    # /mqttsetup/topic/get
    contentType = "application/json"
    http_status = "200 OK"
    toSend = {}

    p = splitPath(REQUEST["PATH"])
    topic = p[1].strip()
    action = p[2].strip()

    if action == "set":
        if "script" in REQUEST["POST"].keys():
            try:
                tFile = open("handler-"+topic+".def", "w")
                tFile.write(unquote(REQUEST["POST"]["script"]))
            except Exception as e:
                toSend["error"] = e.args[0]
            else:
                toSend["topic"] = "saved"
            finally:
                tFile.close()

    else:
        if action == "get":
            try:
                tFile = open("handler-"+topic+".def", "r")
                tFileContent = tFile.readlines()
            except Exception as e:
                toSend["error"] = e.args[0]
            else:
                toSend["topic"] = "".join(tFileContent)
            finally:
                tFile.close()

    return (contentType, http_status, toSend)


def splitPath(path):
    return path.strip("/").split("/")


def parsePath(path):
    # folosite in jss::serve
    p = path.strip("/").split("/", 1)
    return "/"+p[0]


def file_exists(f):
    if f in listdir():
        return True
    else:
        return False


beVerbose = False

wifiHotspots = []
j = jss(verbose=beVerbose, port=conf.jsonConfig.get("http_server_port"))
j.routeHandler = parsePath

mpu = mcu()
mpu.wifi.active(True)

if type(conf.jsonConfig["peripherals"]) is list and len(conf.jsonConfig["peripherals"]) > 0:
    for epfcfg in conf.jsonConfig["peripherals"]:
        if epfcfg["type"] in ["mqtt", "mqtta", "mqttht"]:
            epfcfg = {"type": epfcfg["type"],
                      "initOptions": {"autostart": False, "id": 2}}
        mpu.addPeripheral(epfcfg)



applyObservables = False
scriptFilename = __file__.split('.')[0]

if "applyObservablesOnBoot" in conf.jsonConfig:
    if conf.jsonConfig["applyObservablesOnBoot"].__class__.__name__ == 'str':
        if scriptFilename in conf.jsonConfig["applyObservablesOnBoot"].split("|"):
            applyObservables = True
        else:
            if conf.jsonConfig.get("applyObservablesOnBoot") in jsu.TrueValues:
                applyObservables = True
    else:
        if conf.jsonConfig["applyObservablesOnBoot"].__class__.__name__ == 'bool':
            applyObservables = conf.jsonConfig["applyObservablesOnBoot"]

if applyObservables:
    oconf = ujson.loads(jsu.getObservablesFileContent(conf.observablesFile))

    for xi in range(len(mpu.peripherals)):
        print("\t Applying observables at boot for peripheral "+str(xi))
        if str(xi) in oconf["observables"] and len(oconf["observables"][str(xi)]) > 0:
            obsrvbToExec = oconf["observables"][str(xi)]
            jsu.applyObservablesFromJson(xi, obsrvbToExec, mpu)
        else:
            print("\t\tNone found for it")
else:
    print("\t\tObservables not applied")





executeStartupFile = True

if "executeStartupFile" in conf.jsonConfig:
    if conf.jsonConfig.get("executeStartupFile").__class__.__name__ == 'str':
        if scriptFilename not in conf.jsonConfig.get("executeStartupFile").split("|"):
            executeStartupFile = False
        else:
            if conf.jsonConfig.get("executeStartupFile") in jsu.FalseValues:
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
                        "runMode": "config"
                        })
                except:
                    print("\tError, Bad script")
else:
    print("\tStartup script skipped")


j.route["/"] = homeHandler
j.route["/NOTFOUND"] = notfoundHandler
j.route["/cmd"] = commandHandler
j.route["/machine"] = machineHandler
j.route["/net"] = netHandler
j.route["/conf"] = configHandler
j.route["/message"] = messageHandler
j.route["/mqttsetup"] = mqttsetupHandler


j.start()
