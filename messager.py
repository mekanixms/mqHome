from peripheral import peripheral


def sendMsg(s, message, to="*", topic=False, retain=False, qos=0):
    if message:
        if s.driver.__class__.__name__ is "slimmqtt":
            return s.driver.send(message, to, topic, retain, qos)
    else:
        return s.message


def receiveMsg(s, message):
    if message:
        s.message = message
        return {"message": "delivered"}
    else:
        return {"error": "not delivered"}


class messager(peripheral):
    po = False

    def __init__(self, options={}):
        super().__init__(options)

        self.pType = self.__class__.__name__
        self.pClass = "VIRTUAL"

        self.driver = ""

        self.__msg = ""

        self.commands["sendMessage"] = sendMsg
        self.commands["receiveMessage"] = receiveMsg

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
        return {
            "driver": self.driver.getState() if self.driver.__class__.__name__ is "slimmqtt" else "driver offline"
        }

    def getObservableMethods(self):
        return []

    def getObservableProperties(self):
        return ["message"]
