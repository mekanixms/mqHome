
from peripheral import peripheral, TrueValues
from debutton import debutton
from jsu import FalseValues


class realbutton(peripheral):
    VERSION = 0.2

    def __init__(self, options={"pinOut": 27, "period": 200, "pull": 2}):
        super().__init__(options)

        self.status = False

        self.pType = self.__class__.__name__
        self.pClass = "IN"

        def setValue(*args):
            self.val = args[0]

        self.button = debutton(
            options={
                'pinOut': int(self.settings.get("pinOut")),
                'period': int(self.settings.get("period")),
                'pull': int(self.settings.get("pull"))
            },
            cbk=setValue
        )

    @property
    def val(self):
        return self.status

    @val.setter
    @peripheral._watch
    def val(self, val):
        if val in TrueValues:
            self.status = True
        else:
            self.status = False

    def getState(self):
        return {"on": self.val}

    def getObservableMethods(self):
        return ["command", "setStatus"]

    def getObservableProperties(self):
        return ["val"]
