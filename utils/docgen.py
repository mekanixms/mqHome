import re
import json
from os import listdir

version = 0.6

matchClassNames = "^class\s{1}(?P<classname>\w*)\((?P<parentclass>\w*)\):"
matchClassMethods = "^\s{4}def\s{1}(?P<methodname>\w*)\((?P<methodparams>[\w\W]*)\):"
matchFunctions = "^def\s{1}(?P<funcname>\w*)\((?P<funcparams>[\w\W]*)\):"
matchCommands = "^\s*self.commands\[[\"'](?P<cmdname>\w*)[\"']\] = (?P<callfunction>[\w\W]*[^\n])"

externalCommandsAllClasses = {}


def dumpJson(fn, jout):
    fout = open(fn, "w")
    fout.write(json.dumps(jout))
    fout.close()


for f in listdir("."):
    if f.split(".")[-1] == "py":
        inputfile = open(f, "r")
        inputFileContent = inputfile.readlines()
        inputfile.close()

        linenum = 0

        doc = {}
        functions = {}
        classCommands = {}

        currentClass = None

        for cline in inputFileContent:

            check = re.match(matchClassNames, cline)
            if check is not None:
                # print(check.group('classname')+'\t'+check.group(1))
                # print(check.group('parentclass')+'\t'+check.group(2))
                # print("CLASS "+check.group('classname')+'\t parent ' +
                #       check.group('parentclass')+"\t LINE: "+str(linenum))

                classDoc = {}
                currentClass = check.group('classname')
                if check.group('classname') not in doc.keys():
                    classDoc["startLine"] = linenum
                    classDoc["className"] = check.group('classname')
                    classDoc["parentClass"] = check.group('parentclass')
                    classDoc["methods"] = {}
                    classDoc["commands"] = {}
                    doc[currentClass] = classDoc

            check = re.match(matchClassMethods, cline)
            if check is not None:
                # print("\tMETHOD "+check.group('methodname')+'\tparams ' +
                #       check.group("methodparams")+"\t LINE: "+str(linenum))
                if currentClass is not None:
                    if currentClass in doc.keys():
                        if linenum > doc[currentClass]["startLine"]:
                            doc[currentClass]["methods"][check.group('methodname')] = {
                                "line": linenum,
                                "params": check.group("methodparams")
                            }

            check = re.match(matchCommands, cline)
            if check is not None:
                # print("COMMANDS "+check.group('cmdname')+' calls for ' +
                #       check.group("callfunction")+"\t LINE: "+str(linenum))
                if currentClass is not None:
                    if currentClass in doc.keys():
                        if linenum > doc[currentClass]["startLine"]:
                            doc[currentClass]["commands"][check.group('cmdname')] = {
                                "line": linenum,
                                "function": check.group("callfunction")
                            }

            check = re.match(matchFunctions, cline)
            if check is not None:
                # print("FUNCTION "+check.group('funcname')+'\tparams ' +
                #       check.group("funcparams")+"\t LINE: "+str(linenum))
                functions[check.group('funcname')] = {
                    "line": linenum,
                    "params": check.group("funcparams")
                }

            linenum += 1

        dout = {"classes": doc, "functions": functions}

        dumpJson(f+".def", dout)

        for thisClass in doc:
            classCommands[thisClass] = {}
            for cmd in doc[thisClass]["commands"]:
                targetFunction = doc[thisClass]["commands"][cmd]["function"]
                if targetFunction in functions.keys():
                    paramsWithSelf = functions[targetFunction]["params"]
                    splitParams = paramsWithSelf.split(",")
                    if len(splitParams) <= 1:
                        paramsWithoutSelf = []
                    else:
                        splitParams.pop(0)
                        paramsWithoutSelf = splitParams

                    classCommands[thisClass][cmd] = ",".join(paramsWithoutSelf)

            externalCommandsAllClasses[thisClass] = classCommands[thisClass]

dumpJson("externalCommands.json", externalCommandsAllClasses)

print("Completed successfully")
