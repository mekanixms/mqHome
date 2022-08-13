import re
import json
from os import listdir

version = 0.8

matchClassNames = "^class\s{1}(?P<classname>\w*)\((?P<parentclass>\w*)\):"
matchClassMethods = "^\s{4}def\s{1}(?P<methodname>\w*)\((?P<methodparams>[\w\W]*)\):"
matchFunctions = "^def\s{1}(?P<funcname>\w*)\((?P<funcparams>[\w\W]*)\):"
matchCommands = "^\s*self.commands\[[\"'](?P<cmdname>\w*)[\"']\] = (?P<callfunction>[\w\W]*[^\n])"
matchDocStrings = "^\s*['\"]{3}$"
matchDocStringsMultilineAlternative = "\s*[\"']{3}(?P<docstring>.*)[\"']{3}"

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
        docStrings = []

        currentClass = None

        for cline in inputFileContent:
            try:
                docString
            except NameError:
                docString = {"open": None, "close": None}

            check = re.match(matchClassNames, cline)
            if check is not None:
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
                if currentClass is not None:
                    if currentClass in doc.keys():
                        if linenum > doc[currentClass]["startLine"]:
                            doc[currentClass]["methods"][check.group('methodname')] = {
                                "line": linenum,
                                "params": check.group("methodparams")
                            }

            check = re.match(matchCommands, cline)
            if check is not None:
                if currentClass is not None:
                    if currentClass in doc.keys():
                        if linenum > doc[currentClass]["startLine"]:
                            doc[currentClass]["commands"][check.group('cmdname')] = {
                                "line": linenum,
                                "function": check.group("callfunction")
                            }

            check = re.match(matchFunctions, cline)
            if check is not None:
                functions[check.group('funcname')] = {
                    "line": linenum,
                    "params": check.group("funcparams")
                }

            check = re.match(matchDocStrings, cline)
            if check is not None:
                if docString["open"] is None:
                    docString["open"] = linenum
                else:
                    docString["close"] = linenum

                    if docString["open"]+1 == docString["close"]-1:
                        docStringRange = [docString["open"]+1]
                    else:
                        docStringRange = range(
                            docString["open"]+1, docString["close"]-1)

                    docStringLines = (
                        inputFileContent[index].strip() for index in docStringRange)
                    docString["text"] = "".join(docStringLines)

                    docStrings.append(docString)
                    docString = {"open": None, "close": None}

            linenum += 1

        dout = {
            "classes": doc,
            "functions": functions,
            "docstrings": docStrings
        }

        for cClass in doc:
            for method in doc[cClass]["methods"]:
                for dstr in dout["docstrings"]:
                    if doc[cClass]["methods"][method]["line"]+1 == dstr["open"]:
                        if "text" in dstr.keys():
                            doc[cClass]["methods"][method]["docstring"] = dstr["text"]

        for cFunction in functions:
            for dstr in dout["docstrings"]:
                if functions[cFunction]["line"]+1 == dstr["open"]:
                    if "text" in dstr.keys():
                        functions[cFunction]["docstring"] = dstr["text"]

        dumpJson(f+"-def.json", dout)

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
