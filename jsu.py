import os
import ujson
import ure
from time import time

TrueValues = ["True", "TRUE", "true", "ON", "On", "on", "1", 1, True]
FalseValues = ["False", "FALSE", "false",
               "OFF", "Off", "off", "0", 0, False, None]


def urlStringDecode(aData: bytearray) -> str:
    # Credits  https://github.com/micropython/micropython-lib/blob/master/urllib.parse/urllib/parse.py
    Bits = aData.split(b'%')
    Arr = [Bits[0]]
    for Item in Bits[1:]:
        Code = Item[:2]
        Char = bytes([int(Code, 16)])
        Arr.append(Char)
        Arr.append(Item[2:].replace(b'+', b' '))
    Res = b''.join(Arr)
    return Res.decode('utf-8')


def whichBool(val):
    # print("\t\tWhichbool testing "+str(val))
    if val in TrueValues:
        return True
    else:
        if val in FalseValues:
            return False
        else:
            return None


def file_exists(f):
    if f in os.listdir():
        return True
    else:
        return False


def importJsonDictionaryFromFile(cfgf):
    if file_exists(cfgf):
        configFile = open(cfgf, "r")
        configFileContent = configFile.readlines()

        if len(configFileContent) > 0:
            jsonConfig = ujson.loads("".join(configFileContent))
        else:
            jsonConfig = {cfgf: {}}

        configFile.close()
    else:
        jsonConfig = {cfgf: {}}

    return jsonConfig


def current_milli_time(): return int(round(time() * 1000))


def performOperationFromString(o1, o2, op):
    res = None

    if op.strip() == "==":
        res = o1 == o2
    else:
        if op.strip() == ">>":
            res = o1 > o2
        else:
            if op.strip() == "<<":
                res = o1 < o2
            else:
                if op.strip() == "<=":
                    res = o1 < o2
                else:
                    if op.strip() == ">=":
                        res = o1 >= o2
                    else:
                        if op.strip() == "!=" or op.strip() == "<>":
                            res = o1 != o2

    # print("OpfromString: \t"+str(o1)+" "+str(op)+" "+str(o2)+":\t"+str(res))

    return res


def prepareStringSequence(testCondition):
    testSeq = []

    if testCondition:
        # pt inline test
        i = 0

        allParamExpression = '(.*)\s*([!=<>]+[<>=]+)\s*(\w*)'

        for tline in testCondition.split(","):
            ctline = tline.strip()

            paramsDefinitionCheck = ure.match(allParamExpression, ctline)
            if paramsDefinitionCheck is not None:
                paramsNumber = int(
                    ure.match('^<match num=(\d*)>$', str(paramsDefinitionCheck)).group(1))
                if paramsNumber == 4:
                    # var1       >=      val
                    # testArd operator testVal
                    testArg = paramsDefinitionCheck.group(1)
                    operator = paramsDefinitionCheck.group(2)
                    testVal = paramsDefinitionCheck.group(3)
                    # 0<val1,3=val2
                    testMember = {
                        "o1": testArg,
                        "o2": testVal,
                        "op": operator
                    }
            else:
                # val1,val2,val3...
                testMember = {
                    "o1": str(i),
                    "o2": ctline,
                    "op": "=="
                }

                i = i+1

            testSeq.append(testMember)

    return testSeq


def testStringSequence(testCondition, args, kwargs):
    testResult = True

    for tline in testCondition:
        tr = False
        # testMember = {
        #     "o1": testArg,
        #     "o2": testVal,
        #     "op": operator
        # }
        testArg = tline["o1"]
        operator = tline["op"]
        testVal = tline["o2"]

        if testArg.isdigit():
            # ON(rawMessage[1==TOGGLE]): dev[1]/toggle()
            if len(args) > 0:

                # print("\t"+testArg + "\t"+operator+"\t"+testVal)

                if int(testArg) >= 0 and int(testArg) < len(args):
                    if type(args[int(testArg)]) == bool:
                        tr = args[int(testArg)] and whichBool(testVal)
                    else:
                        tr = performOperationFromString(
                            args[int(testArg)], (args[int(testArg)]).__class__(testVal), operator)

        else:
            # ON(rawMessage[message==TOGGLE]): dev[1]/toggle()
            if testArg in kwargs.keys():

                # print("\t"+kwargs.get(testArg) + "\t"+operator+"\t"+testVal)

                if type(kwargs.get(testArg)) is bool:
                    tr = kwargs.get(testArg) and whichBool(testVal)
                else:
                    tr = performOperationFromString(
                        kwargs.get(testArg), (kwargs.get(testArg)).__class__(testVal), operator)

            else:
                # ON(rawMessage[jsonmessage/data==TOGGLE]):  dev[1]/toggle()
                # ON(rawMessage[jsonmessage/0==TOGGLE]):  dev[1]/toggle()
                testArgSplit = testArg.split("/")
                if len(testArgSplit) == 2:
                    neededArgName = testArgSplit[0]
                    if neededArgName in kwargs.keys():
                        neededArg = kwargs.get(neededArgName)
                        neededArgKey = testArgSplit[1]
                        # ON(rawMessage[jsonmessage/data==TOGGLE]):  dev[1]/toggle()
                        if type(neededArg) is dict:
                            if neededArgKey in neededArg.keys():

                                # print("\t"+neededArgName+"/" + neededArgKey + "\t"+operator+"\t"+testVal)

                                requiredArgValue = neededArg.get(neededArgKey)

                                try:
                                    evaluatedTestVal = eval(testVal)
                                except:
                                    evaluatedTestVal = testVal

                                if type(requiredArgValue) == bool:
                                    tr = requiredArgValue and whichBool(
                                        evaluatedTestVal)
                                else:
                                    try:
                                        # o==int("alphanumeric")
                                        tr = performOperationFromString(
                                            requiredArgValue, (requiredArgValue).__class__(
                                                evaluatedTestVal), operator
                                        )
                                    except ValueError:
                                        tr = False

                        # ON(rawMessage[jsonmessage/0==TOGGLE]):  dev[1]/toggle()
                        if type(neededArg) is list:
                            if neededArgKey.isdigit():

                                # print("\t"+neededArgName+"/" + neededArgKey + "\t"+operator+"\t"+testVal)

                                neededArgKey = int(neededArgKey)
                                if neededArgKey < len(neededArg):

                                    requiredArgValue = neededArg[neededArgKey]

                                    try:
                                        evaluatedTestVal = eval(testVal)
                                    except:
                                        evaluatedTestVal = testVal

                                    if type(requiredArgValue) is bool:
                                        tr = requiredArgValue and whichBool(
                                            evaluatedTestVal)
                                    else:
                                        try:
                                            # o==int("alphanumeric")
                                            tr = performOperationFromString(
                                                requiredArgValue, (requiredArgValue).__class__(evaluatedTestVal), operator)
                                        except ValueError:
                                            tr = False

        testResult = testResult and tr

    return testResult


def saveJsonToObservablesFile(obj, conf):
    configFile = open(conf, "w")
    configFile.write(ujson.dumps(obj))
    configFile.close()


def getObservablesFileContent(conf):
    if file_exists(conf):
        configFile = open(conf, "r")
        configFileContent = configFile.readlines()
        configFile.close()
        return "".join(configFileContent)
    else:
        return '{"observables": {}}'


def saveObservables(receivedObservables, conf):
    configFileContent = getObservablesFileContent(conf)

    if len(configFileContent) > 0:
        jsonConfig = ujson.loads(configFileContent)
    else:
        jsonConfig = {"observables": {}}

    for obsType in receivedObservables:
        for whichDevsObs in receivedObservables[obsType]:
            if not whichDevsObs in jsonConfig["observables"]:
                jsonConfig["observables"][whichDevsObs] = {
                }
            if not obsType in jsonConfig["observables"][whichDevsObs]:
                jsonConfig["observables"][whichDevsObs][obsType] = receivedObservables[obsType][whichDevsObs]
            else:
                for whichAction in receivedObservables[obsType][whichDevsObs]:
                    if not whichAction in jsonConfig["observables"][whichDevsObs][obsType]:
                        jsonConfig["observables"][whichDevsObs][obsType][
                            whichAction] = receivedObservables[obsType][whichDevsObs][whichAction]
                    else:
                        jsonConfig["observables"][whichDevsObs][obsType][
                            whichAction] = receivedObservables[obsType][whichDevsObs][whichAction]

    configFile = open(conf, "w")
    configFile.write(ujson.dumps(jsonConfig))
    configFile.close()


def buildParametersFromString(pt):
    # pmComponents = ure.sub("\s\s*", " ", pMethod.strip())
    returnParamsDict = {}

    if len(pt) > 0:
        ptComponents = pt.split(",")
        for textParam in ptComponents:
            pc = textParam.strip().split("=")
            if len(pc) == 2:
                # pc[1].strip() este de unde scot si evaluez valori
                returnParamsDict[pc[0].strip()] = pc[1].strip()
            else:
                print("wrong parameter " + textParam +
                      "\t"+ujson.dumps(pc)+"\n")
                print("parameters string:\t"+pt)

    return returnParamsDict


def nEsInterz(expr):
    return True


def evalParams(p2eval, ps, triggerPositionalParameters, triggerKeywordParameters, userVars):
    toRet = {}

    # TODO match la string sa scot functiile periculoase

    if len(p2eval) > 0:
        for k in p2eval.keys():
            if nEsInterz(p2eval.get(k)):
                try:
                    if p2eval.get(k).find("dev[") != -1 or p2eval.get(k).find("pargs[") != -1 or p2eval.get(k).find("kargs[") != -1 or p2eval.get(k).find("context[") != -1:
                        # TODO adauga aici, ca si periphericele, niste variabile, atasate MCU, care sunt accesibile oricarui eriferic
                        # de ex var daytime [zi, noapte] si aht10 comanda on doar daca var are val noapte
                        toRet[k] = eval(p2eval.get(k), {}, {
                                        "dev": ps, "pargs": triggerPositionalParameters, "kargs": triggerKeywordParameters, "context": userVars
                                        })
                    else:
                        toRet[k] = p2eval.get(k)
                except:
                    toRet[k] = p2eval.get(k)

    return toRet


def lmbdForPeripheralObservable(testCondition, pee, mpu):

    def lF(*args, **kwargs):
        lFRet = None

        executePeripheralCommand = True

        if testCondition:
            testForValue = testStringSequence(testCondition, args, kwargs)

            if testForValue:
                executePeripheralCommand = True
            else:
                executePeripheralCommand = False

        else:
            executePeripheralCommand = True

        # dev[numeric] execut comanda periferic
        if executePeripheralCommand:
            # # topic=DISPLAY,msg="T:"+str(pargs[0]),encapsulate=False
            commandParams = buildParametersFromString(pee["params"])
            if len(commandParams) == 0:
                lFRet = mpu.peripherals[int(
                    pee["pid"])].command(pee["cmd"])
            else:
                lFRet = mpu.peripherals[int(pee["pid"])].command(
                    pee["cmd"], evalParams(commandParams, mpu.peripherals, args, kwargs, mpu.userVariables))

        return lFRet

    return lF


def lmbdForContext(testCondition, pee, mpu):
    def lF(*args, **kwargs):

        lFRet = {}

        executeCommand = True

        if testCondition:
            testForValue = testStringSequence(testCondition, args, kwargs)

            if testForValue:
                executeCommand = True
            else:
                executeCommand = False
                # print(str(args[0]) + " == " + (args[0]).__class__.__name__ + "("+testCondition+")" +
                #       " not passed \n NotExecuted:"+ujson.dumps(pee))
        else:
            executeCommand = True

        # dev[numeric] execut comanda periferic
        if executeCommand:
            # # topic=DISPLAY,msg="T:"+str(pargs[0]),encapsulate=False
            commandParams = buildParametersFromString(pee["params"])
            if len(commandParams) > 0:
                evaluatedParams = evalParams(
                    commandParams, mpu.peripherals, args, kwargs, mpu.userVariables)

                for k in evaluatedParams.keys():
                    mpu.userVariables[k] = evaluatedParams[k]
                    lFRet[k] = evaluatedParams[k]

        return lFRet

    return lF


def dictAddItemAtBegining(toThisDict, addThis):
    newDict = addThis

    for k in toThisDict:
        newDict[k] = toThisDict[k]

    return newDict


def lmbdForMpu(testCondition, pee, mpu):

    def lF(*args, **kwargs):

        lFRet = None

        executePeripheralCommand = True

        if testCondition:
            testForValue = testStringSequence(testCondition, args, kwargs)

            if testForValue:
                executePeripheralCommand = True
            else:
                executePeripheralCommand = False
                # print(str(args[0]) + " == " + (args[0]).__class__.__name__ + "("+testCondition+")" +
                #       " not passed \n NotExecuted:"+ujson.dumps(pee))
        else:
            executePeripheralCommand = True

        if executePeripheralCommand:
            # # topic=DISPLAY,msg="T:"+str(pargs[0]),encapsulate=False
            commandParams = buildParametersFromString(pee["params"])
            # acces prop metode obiect mcu
            # mcu.__dict__["uptime"]
            #   uptime este functie
            # testez asa: callable(mcu.__dict__["uptime"])
            # sau asa: mcu.__dict__["uptime"].__class__.__name__ == 'function'
            if pee["cmd"] in mpu.__class__.__dict__ and callable(mpu.__class__.__dict__[pee["cmd"]]):
                mpuCmd = mpu.__class__.__dict__[pee["cmd"]]

                mpuCmdParams = evalParams(
                    commandParams, mpu.peripherals, args, kwargs, mpu.userVariables)
                mpuCmdParamsWithSelf = dictAddItemAtBegining(
                    mpuCmdParams, {"self": mpu})

                lFRet = mpuCmd(**mpuCmdParamsWithSelf)

        return lFRet

    return lF


def applyObservablesFromJson(deviceID, obsrvbToExec, mpu):
    # pornesc  de la
    # dev[0]/send(topic=DISPLAY,msg="T:"+str(pargs[0]),encapsulate=False)
    # si trebuie sa execut asa
    # mpu.peripherals[deviceID].addTrigger("relayToggle", "AFTER", d)
    for whichObsrvbl in obsrvbToExec:
        if whichObsrvbl == "triggers":
            exThisOne = mpu.peripherals[int(
                deviceID)].addTrigger
        else:
            exThisOne = mpu.peripherals[int(
                deviceID)].addWatcher
        print("\tPreparing observable for " +
              str(deviceID)+" "+whichObsrvbl)

        for pMethod in obsrvbToExec[whichObsrvbl]:
            # 0 : before sau after, 1 numeMethod
            # daca are un singur element este numele metodei si before este default
            print("\tCreate "+pMethod +
                  " for peripheral " + str(deviceID))

            when = "BEFORE"
            pmComponents = ure.sub(
                "\s\s*", " ", pMethod.strip()).split(" ")
            if len(pmComponents) == 1:
                mthd = pmComponents[0].strip()
            else:
                if len(pmComponents) == 2:
                    if pmComponents[0].upper() in ["BEFORE", "AFTER"]:
                        when = pmComponents[0].upper()
                        mthd = pmComponents[1].strip()

            smthd = ure.match('(.*?)\[(.*?)\]', mthd)
            # iau in considerare doar numele comenzii si scot testul
            # facut asa ca sa pot face trigger -> actiune[test] actiune[test1]
            # altfel aveam doar actiune {test, exec}
            mthd = smthd.group(1)

            pTest = prepareStringSequence(
                obsrvbToExec[whichObsrvbl][pMethod]["test"])
            pExec = obsrvbToExec[whichObsrvbl][pMethod]["execute"]

            if len(pTest) > 0:
                print("\t\tON: "+pMethod)

            # model pE
            #         "execute": [
            #             {
            #                 "pid": "2",
            #                 "params": "text=pargs[1],col=1,row=1",
            #                 "cmd": "show"
            #             },
            #             {
            #                 "pid": "context",
            #                 "params": "topic=DISPLAY",
            #                 "cmd": "set"
            #             },
            #             {
            #                 "pid": "mpu",
            #                 "params": "topic=DISPLAY,ceva=valoare",
            #                 "cmd": "metodaMpu"
            #             }
            #         ]

            for pE in pExec:
                cmdTarget = pE["pid"]

                if cmdTarget == "context":
                    # exThisOne pe datele din context
                    # adauga lambda la triggers sau watcher
                    exThisOne(mthd, when, lmbdForContext(pTest, pE, mpu))
                else:
                    if cmdTarget == "mpu":
                        # exThisOne pe datele din context
                        # adauga lambda la triggers sau watcher
                        exThisOne(mthd, when, lmbdForMpu(pTest, pE, mpu))
                    else:
                        # este comanda catre device
                        print("\t\tadd "+whichObsrvbl+" for " +
                              " "+mthd+" "+when+" " +
                              "dev[{}] {}({})".format(pE["pid"], pE["cmd"], pE["params"]))
                        # pE["pid"] == "context" si nu este numeric?? dev[context] execut ceva pt mpu??
                        #   ATENTIE: pid poate fi doar numeric, asa vine din js (Animation/Save)
                        #
                        # altfel, este comanda pt periferic, adaug trigger sau watcher:
                        exThisOne(
                            mthd, when, lmbdForPeripheralObservable(pTest, pE, mpu))
