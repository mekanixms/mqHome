from machine import Timer
from jsu import current_milli_time, TrueValues, FalseValues


class peripheral:

    def __init__(self, options={}):
        self.pClass = ""  # sau IN SAU OUT?
        self.pType = ""  # rel sau "fet" sau led sau buton
        # aici tin istanta obiectului nativ, adica Pin sau PWM sau ....
        self.po = False

        self.commands = {}
        self.settings = {}
        self.alias = None
        self.triggers = {}
        self.watchers = {}

        self.settings = options
        if type(options) == dict and "alias" in options.keys():
            self.alias = options["alias"]

    def _trigger(func):
        def wrapper(self, *args, **kwargs):

            executeThese = {}
            if func.__name__ in self.triggers.keys():
                executeThese = self.triggers[func.__name__]

            if "BEFORE" in executeThese and len(executeThese["BEFORE"]) > 0:
                for ebf in executeThese["BEFORE"]:
                    ebf(*args, **kwargs)

            out = func(self, *args, **kwargs)

            if "AFTER" in executeThese and len(executeThese["AFTER"]) > 0:
                for ebf in executeThese["AFTER"]:
                    ebf(*args, **kwargs)

            return out
        return wrapper

    def _watch(func):
        def wrapper(self, *args, **kwargs):

            executeThese = {}
            if func.__name__ in self.watchers.keys():
                executeThese = self.watchers[func.__name__]

            if "BEFORE" in executeThese and len(executeThese["BEFORE"]) > 0:
                for ebf in executeThese["BEFORE"]:
                    ebf(*args)

            out = func(self, *args, **kwargs)

            if "AFTER" in executeThese and len(executeThese["AFTER"]) > 0:
                for ebf in executeThese["AFTER"]:
                    ebf(*args)

            return out
        return wrapper

    @_trigger
    def setOptions(self, options={}):
        if len(options) > 0 and type(options).__name__ == "dict":
            for k in options:
                self.settings[k] = options[k]

    def deinit(self):
        print("PERIPHERAL")

    def commandsList(self):
        return list(self.commands.keys())

    def addTrigger(self, forThisFunction, when, whatToDo):

        if forThisFunction not in self.triggers.keys():
            self.triggers[forThisFunction] = {"BEFORE": [], "AFTER": []}

        where = None

        if when in ["BEFORE", 0, False]:
            where = "BEFORE"
        else:
            if when in ["AFTER", 1, True]:
                where = "AFTER"

        if where is not None:
            self.triggers[forThisFunction][where].append(whatToDo)

    def addWatcher(self, forThisFunction, when, whatToDo):

        if forThisFunction not in self.watchers.keys():
            self.watchers[forThisFunction] = {"BEFORE": [], "AFTER": []}

        where = None

        if when in ["BEFORE", 0, False]:
            where = "BEFORE"
        else:
            if when in ["AFTER", 1, True]:
                where = "AFTER"

        if where is not None:
            self.watchers[forThisFunction][where].append(whatToDo)

    @_trigger
    def command(self, command, cmdParams={}):
        if command in self.commands:
            f = self.commands[command]

            cfr = None
            if len(cmdParams) > 0:
                try:
                    cfr = f(self, **cmdParams)
                except TypeError as e:
                    print("TypeError executing command "+command)
                    print("with params: "+" / ".join(cmdParams.keys()))
                    print("\n".join(e.args))
            else:
                try:
                    cfr = f(self)
                except TypeError as e:
                    print("TypeError executing command "+command)
                    print("without params")
                    print("\n".join(e.args))

            return cfr
