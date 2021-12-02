class observable:

    def __init__(self):
        self.triggers = {}
        self.watchers = {}

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
        # la apelare e de preferat ca cbk sa fie definita cu cbk(*args,**kwargs)
        # sau simplu cbk(*args)
        # EX:
        # >>> def g(*args):
        # ...     print("After watcher")
        # ...     import ujson
        # ...     print(ujson.dumps(args))
        # ...     
        # ...     
        # ... 
        # >>> vt.addWatcher("heartbeat","AFTER",g)

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
