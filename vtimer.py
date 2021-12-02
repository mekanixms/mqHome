import _thread
from time import time, ticks_ms, ticks_diff


class vtimer():
    ONE_SHOT = 0
    PERIODIC = 1
    VERSION = 0.5

    def __init__(self, period, mode=0, callback=None, seconds=True):
        self.period = period
        self.mode = mode
        self.callback = callback
        self.thread = None
        self.workWithSeconds = seconds
        self._stop = False
        self.heartbeat = True

    def __getTime(self):
        return time() if self.workWithSeconds else ticks_ms()

    def __getTimeDiff(self, a, b):
        return a-b if self.workWithSeconds else ticks_diff(a, b)

    def start(self):
        # print("Start")
        self._stop = False
        self.time_s = self.__getTime()
        self.a_lock = _thread.allocate_lock()
        try:
            self.thread = _thread.start_new_thread(self.__run, ())
        except OSError as err:
            print("Could not create new thread for virtual timer")
            # print(err)

    def stop(self):
        # print("Stop")
        self._stop = True

    def __run(self):
        run = True
        # print("Cycle")
        # self.a_lock.acquire()

        while run:
            if self._stop:
                # print("Cycle break")
                break

            with self.a_lock:
                try:
                    if self.__getTimeDiff(self.__getTime(), self.time_s) > self.period:
                        self.heartbeat = not self.heartbeat

                        if callable(self.callback) and self.callback is not None:
                            self.callback(self.heartbeat)

                        self.time_s = self.__getTime()

                        if self.mode == self.ONE_SHOT:
                            run = False
                except Exception as err:
                    print(err)
                except:
                    print("Unhandled errors occured")
                    break
        if self.a_lock.locked():
            self.a_lock.release()
        # print("loop ended")
