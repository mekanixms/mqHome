import ujson


def messageIsForMe(msgjs, CLIENT_ID):
    go = False

    if msgjs.__class__ is dict:
        if "to" in msgjs:
            if msgjs["to"] == CLIENT_ID or msgjs["to"] == "*":
                go = True
            if "from" in msgjs:
                if msgjs["from"] == CLIENT_ID:
                    go = False
    else:
        go = True

    return go

