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

# https://micropython-glenn20.readthedocs.io/en/latest/library/espnow.html#espnow-and-wifi-operation


class espnowdrv(peripheral):
    espnow = None
    peers = {}
    stop = False
    broadcast = 'ffffffffffff'

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
        peers = importJsonDictionaryFromFile("peers.json")
        for peer in peers:
            self.loadPeer(peers.get(peer))

        return peers

    def loadPeer(self, peer):
        success = True

        try:
            self.espnow.add_peer(self.__encodeHexBytes(peer))
        except:
            success = False

        return success

    def removePeer(self, peer):
        success = True

        try:
            self.espnow.del_peer(self.__encodeHexBytes(peer))
        except:
            success = False

        return success

    def peerInfo(self, peer):
        try:
            pi = self.espnow.get_peer(self.__encodeHexBytes(peer))
        except:
            pi = ()

        if len(pi) == 5:
            return {
                "mac": self.__decodeHexBytes(pi[0]),
                "lmk": pi[1] if pi[1].__class__.__name__ == "str" else pi[1].decode("utf-8"),
                "channel": pi[2],
                "ifidx": pi[3],
                "encrypt": pi[4]
            }
        else:
            return {}

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

    def getPeersByMac(self):
        peers = []
        #   0   1       2       3       4
        # (mac, lmk, channel, ifidx, encrypt (bool))
        for peer in self.espnow.get_peers():
            peers.append(self.__decodeHexBytes(peer[0]))

        return peers

    def getState(self):
        return {
            "connected": self.isconnected(),
            "peers": self.getPeersByMac(),
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

    def __decodeHexBytes(self, val):
        return ubinascii.hexlify(val).decode("utf-8")

    def __encodeHexBytes(self, val):
        return ubinascii.unhexlify(bytes(val, "utf-8"))

    def run(self):
        a_lock = _thread.allocate_lock()
        while True:
            with a_lock:
                host, msg = self.espnow.recv()
                if msg:
                    rcvdMsg = {}

                    try:
                        rcvdMsg = ujson.loads(msg.decode("utf-8"))
                    except ValueError:
                        rcvdMsg = {"message": msg.decode("utf-8")}
                        if rcvdMsg["message"] == "BCAST_REG_PEER":
                            self.loadPeer(self.__decodeHexBytes(host))
                    except:
                        rcvdMsg = {"error": "other"}

                    rcvdMsg["FROM"] = self.__decodeHexBytes(host)

                    self.rawMessage(rcvdMsg["FROM"], msg.decode("utf-8"))

                    self.message = rcvdMsg

                if self.stop:
                    break

        _thread.exit()

    def send(self, msg, to="*", sync=False):

        response = False

        if to == "*":
            self.espnow.send(msg)
        else:
            if len(to) == 12:
                encTo = self.__encodeHexBytes(to)
                response = self.espnow.send(encTo, msg, sync)

        return {
            "to": to,
            "msg": msg,
            "sync": sync,
            "response": response
        }
