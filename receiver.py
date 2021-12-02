from peripheral import peripheral


def msg(s, value=""):
    if value:
        s.message = value
    else:
        return s.message


class receiver(peripheral):
    po = False

    def __init__(self, options={}):
        super().__init__(options)

        self.pType = "receiver"
        self.pClass = "VIRTUAL"

        self.commands["message"] = msg

        self.__msg = ""

    def deinit(self):
        pass

    @property
    def message(self):
        return self.__msg

    @message.setter
    @peripheral._watch
    def message(self, val):
        self.__msg = val

    def getState(self):
        return {"message": self.__msg}

    def getObservableMethods(self):
        return ["command"]

    def getObservableProperties(self):
        return ["message"]
