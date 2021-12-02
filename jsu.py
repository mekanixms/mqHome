import os
import ujson
import ure
from time import time

TrueValues = ["True", "TRUE", "true", "ON", "On", "on", "1", 1, True]
FalseValues = ["False", "FALSE", "false",
               "OFF", "Off", "off", "0", 0, False, None]


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
    import ure
    testSeq = []

    # print("TEXT CONDITION:\t"+testCondition)
    if testCondition:
        # pt inline test
        i = 0

        allParamExpression = '(.*)\s*([!=<>]+[<>=]+)\s*(\w*)'

        # print("Lambda test:\t"+testCondition)
        for tline in testCondition.split(","):
            ctline = tline.strip()

            # print("Testing sequence member:\t"+ctline)
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
                    # print("Positional args")
                    # print("arg["+testArg+"]\t"+operator+"\t"+testVal)
                    # sau
                    # var1>=val,var2=val
                    # print("KW args")
                    # print("kwArg["+testArg+"]\t"+operator+"\t"+testVal)

                    testMember = {
                        "o1": testArg,
                        "o2": testVal,
                        "op": operator
                    }
            else:
                # val1,val2,val3...
                # print("Inline args test")
                # print(ctline)

                testMember = {
                    "o1": str(i),
                    "o2": ctline,
                    "op": "=="
                }

                i = i+1

            testSeq.append(testMember)

    return testSeq


def testStringSequence(testCondition, args, kwargs):
    import ure
    testResult = True

    # print("\t\ttestStringSequence method call for")
    # print(ujson.dumps(testCondition))
    for tline in testCondition:
        # testMember = {
        #     "o1": testArg,
        #     "o2": testVal,
        #     "op": operator
        # }
        testArg = tline["o1"]
        operator = tline["op"]
        testVal = tline["o2"]

        if testArg.isdigit():
            # print("inline or ARG test")
            # print("\t list#" + testArg+"\t with value" +
            #   str(args[int(testArg)])+" | operation " + operator + " testVal "+ujson.dumps(testVal))
            # 0<val1,3=val2
            # print("Positional args")
            # print("arg["+testArg+"]\t"+operator+"\t"+testVal)

            # val1,val2,val3...
            # print("Inline args test")
            # print(ctline)

            if len(args) > 0:
                if int(testArg) >= 0 and int(testArg) < len(args):
                    if type(args[int(testArg)]) == bool:
                        # print("\tArgument is Bool value")
                        testResult = testResult and performOperationFromString(whichBool(testVal), whichBool(
                            args[int(testArg)]), "==")
                    else:
                        # print("\tArgument is Numeric")
                        tr = performOperationFromString(
                            args[int(testArg)], (args[int(testArg)]).__class__(testVal), operator)
                        testResult = testResult and tr
                    # print("\t\tRESULT:\t"+str(testResult))
                # else:
                    # print("could not match param id '"+testArg +
                    #   "' / pair in Args list with len "+str(len(args)))
                    # print("\tSkipping")

            else:
                # print("KW test")
                # print("\t"+ testArg+" operation "+ operator+ " testVal "+ujson.dumps(testVal))
                # var1>=val,var2=val
                # print("KW args")
                # print("kwArg["+testArg+"]\t"+operator+"\t"+testVal)
                if len(kwargs) > 0:
                    # print("is "+testArg + " in "+",".join(kwargs))
                    if testArg in kwargs:
                        if type(kwargs.get(testArg)) == bool:
                            # print("\tKW Argument is Bool value")
                            testResult = testResult and performOperationFromString(
                                whichBool(testVal), whichBool(kwargs.get(testArg)), "==")
                        else:
                            # print("\tKW Argument is Numeric")
                            tr = performOperationFromString(
                                kwargs.get(testArg), (kwargs.get(testArg)).__class__(testVal), operator)
                            testResult = testResult and tr
                        # print("\t\tRESULT:\t"+str(testResult))

    return testResult


def saveJsonToObservablesFile(obj, conf):
    configFile = open(conf, "w")
    configFile.write(ujson.dumps(obj))
    configFile.close()


def getObservablesFileContent(conf):
    # import continut json in var jsonConfig
    if file_exists(conf):
        # incarc fisier configurare
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


def evalParams(p2eval, ps, triggerPositionalParameters, triggerKeywordParameters):
    toRet = {}

    # TODO match la string sa scot functiile periculoase

    if len(p2eval) > 0:
        for k in p2eval.keys():
            if nEsInterz(p2eval.get(k)):
                try:
                    if p2eval.get(k).find("dev[") != -1 or p2eval.get(k).find("pargs[") != -1 or p2eval.get(k).find("kargs[") != -1:
                        toRet[k] = eval(p2eval.get(k), {}, {
                                        "dev": ps, "pargs": triggerPositionalParameters, "kargs": triggerKeywordParameters
                                        })
                    else:
                        toRet[k] = p2eval.get(k)
                except:
                    toRet[k] = p2eval.get(k)

    return toRet


def lmbd(testCondition, pee, mpu):
    # m.peripherals[0].command("duty",{"value":256})
    # pee["pid"], pee["cmd"], pee["params"])
    def lF(*args, **kwargs):
        # if len(args) > 0:
        #     print("LAMDA LIST ARGUMENTS: ")
        #     print(ujson.dumps(args))
        # if len(kwargs) > 0:
        #     print("LAMDA keyway ARGUMENTS: ")
        #     print(ujson.dumps(kwargs))

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
            commandParams = buildParametersFromString(pee["params"])
            if len(commandParams) == 0:
                lFRet = mpu.peripherals[int(
                    pee["pid"])].command(pee["cmd"])
            else:
                lFRet = mpu.peripherals[int(pee["pid"])].command(
                    pee["cmd"], evalParams(commandParams, mpu.peripherals, args, kwargs))

        return lFRet

    return lF


def applyObservablesFromJson(deviceID, obsrvbToExec, mpu):
    # mpu.peripherals[deviceID].addTrigger("relayToggle", "AFTER", d)
    for whichObsrvbl in obsrvbToExec:
        if whichObsrvbl == "triggers":
            exThisOne = mpu.peripherals[int(
                deviceID)].addTrigger
        else:
            exThisOne = mpu.peripherals[int(
                deviceID)].addWatcher
        print("Preparing observable for " +
              str(deviceID)+" "+whichObsrvbl)

        for pMethod in obsrvbToExec[whichObsrvbl]:
            # 0 : before sau after, 1 numeMethod
            # daca are un singur element este numele metodei si before este default
            print("Create "+pMethod +
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
                print("ON: "+pMethod)

            for pE in pExec:
                # exThisOne(mthd, when, lambda *args, **kwargs: print("lambda cbk: farg="+str(args[0])+"\t"+sendToLambda))
                print("add "+whichObsrvbl+" for " +
                      " "+mthd+" "+when+" " +
                      "dev[{}] {}({})".format(pE["pid"], pE["cmd"], pE["params"]))

                exThisOne(mthd, when, lmbd(pTest, pE, mpu))
