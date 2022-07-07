import conf
from peripheral import peripheral
from time import sleep
import _thread
import ujson
from jsu import TrueValues, file_exists, importJsonDictionaryFromFile

import network
import espnow
import ubinascii

from micropython import schedule


_thread.stack_size(4096*2)


def send(s, msg, to="*"):
    return s.send(msg, to)


def enable(s):
    return s.start()


def disable(s):
    return s.deinit()


class espnowdrv(peripheral):
    espnow = None
    peers = {}
    stop = False

    def __init__(self, options={"autostart": True}):
        super().__init__(options)

        self.pType = self.__class__.__name__
        self.pClass = "VIRTUAL"
        self.__msg = ""
        self.thread = None

        self.wifi = network.WLAN()

        self.commands["send"] = send
        self.commands["connect"] = enable
        self.commands["disconnect"] = disable

        if options["autostart"]:
            print("Autostart enabled")
            self.start()

    def start(self):
        if not self.isconnected():
            self.wifi.active(True)

        self.espnow = espnow.ESPNow()
        self.espnow.active(True)

        self.loadPeers()

        try:
            self.thread = _thread.start_new_thread(self.run, ())
        except Exception:
            print("THREAD EXCEPTION")

    def loadPeers(self):
        self.peers = importJsonDictionaryFromFile("peers.json")
        for peer in self.peers:
            self.espnow.add_peer(ubinascii.unhexlify(self.peers.get(peer)))

        return self.peers

    def deinit(self):
        self.espnow.active(False)

    @property
    def message(self):
        return self.__msg

    @message.setter
    @peripheral._watch
    def message(self, val):
        self.__msg = val

    @peripheral._trigger
    def rawMessage(self, source, message):
        print(source)
        print(message)

    def getState(self):
        return {
            "connected": self.isconnected(),
            "registered_peers": self.espnow.get_peers(),
            "recorded_peers": self.peers,
            "stats": self.espnow.stats()
        }

    def getObservableMethods(self):
        return ["rawMessage"]

    def getObservableProperties(self):
        return ["message"]

    def isconnected(self):
        if self.wifi.active():
            if self.wifi.isconnected():
                return network.STA_IF
            else:
                return network.AP_IF
        else:
            return None

    def run(self):
        a_lock = _thread.allocate_lock()
        while True:
            with a_lock:
                host, msg = self.espnow.recv()
                if msg:
                    rcvdMsg = {}
                    try:
                        rcvdMsg = ujson.loads(msg.decode())
                    except ValueError:
                        rcvdMsg = {"message": msg.decode()}
                    except:
                        rcvdMsg = {"error": "other"}

                    rcvdMsg["FROM"] = ubinascii.hexlify(host)

                    self.rawMessage(
                        **{"source": host, "message": msg.decode()})

                    self.message = rcvdMsg

                if self.stop:
                    break

        _thread.exit()

    def send(self, msg, to="*", sync=False):

        response = False

        if to == "*":
            self.espnow.send(msg, sync)
        else:
            if len(to) == 12:
                response = self.espnow.send(ubinascii.unhexlify(to), msg, sync)

        return {
            "to": to,
            "msg": msg,
            "sync": sync,
            "response": response
        }
