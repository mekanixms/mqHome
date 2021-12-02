from peripheral import peripheral
import urequests as requests
import ujson


def message(s, value):
    s.message = value


def send(s, to, port="8080"):
    url = "http://"+to+":"+port+"/message"
    setup = {
        "data": s.message,
        "headers": {
            "Accept": "application/json"
        }
    }

    print("Sending message to "+url)

    try:
        req = requests.request("GET", url, **setup)
        s.message = req.text
        req.close()
        return s.message
    except OSError as e:
        print("Error sending message: \n"+str(e))
        return {
            "error": str(e)
        }


class emiter(peripheral):
    po = False

    def __init__(self, options={}):
        super().__init__(options)

        self.pType = "emiter"
        self.pClass = "VIRTUAL"

        self.commands["message"] = message
        self.commands["send"] = send

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
