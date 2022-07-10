import conf
from peripheral import peripheral
from time import sleep
import _thread
import ujson
from jsu import TrueValues, importJsonDictionaryFromFile

import network
import espnow
import ubinascii

from micropython import schedule


_thread.stack_size(4096*2)


def rebootAs(s, mode):
    if mode in ["mqtt/sta", "config/sta", "config/ap"]:
        # if "from" in message:
        print("Reboot request from ")
        conf.jsonConfig["run"] = mode
        conf.configFileSave()
        print("\tRebooting in "+mode+" mode")
        from machine import reset
        reset()
        # else:
        #     print("Reboot in "+message["data"]+" mode request skipped")
        #     print("\tfrom label not present")


def broadcastForRegistration(s):
    mac = "ffffffffffff"

    s.loadPeer(mac)
    result = s.send(msg="BCAST_REG_PEER", to=mac)
    s.removePeer(mac)

    return {"result": result}


def addpeer(s, mac):
    return {"result": s.loadPeer(mac)}


def removepeer(s, mac):
    return {"result": s.removePeer(mac)}


def send(s, msg, to="*"):
    return {"result": s.send(msg, to)}


def enable(s):
    return {"result": s.start()}


def disable(s):
    return {"result": s.deinit()}


def savePeers(s):
    return {"result": s.savePeersToFile()}

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
        self.commands["addPeer"] = addpeer
        self.commands["broadcastRegister"] = broadcastForRegistration
        self.commands["removePeer"] = removepeer
        self.commands["disconnect"] = disable
        self.commands["rebootAs"] = rebootAs
        self.commands["savePeers"] = savePeers

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

    def savePeersToFile(self):
        peersOut = {}
        peers = self.getPeersByMac()
        i = 0
        for id in peers:
            peersOut[i] = id
            i += 1

        configFile = open("peers.json", "w")
        configFile.write(ujson.dumps(peersOut))
        configFile.close()

        return peers

    def loadPeer(self, peer):
        success = True

        try:
            self.espnow.add_peer(self.__encodeHexBytes(peer))
        except:
            success = False

        self.savePeersToFile()

        return success

    def removePeer(self, peer):
        success = True

        try:
            self.espnow.del_peer(self.__encodeHexBytes(peer))
        except:
            success = False

        self.savePeersToFile()

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
        pass

    def getPeersByMac(self):
        peers = []
        #   0   1       2       3       4
        # (mac, lmk, channel, ifidx, encrypt (bool))
        for peer in self.espnow.get_peers():
            peers.append(self.__decodeHexBytes(peer[0]))

        return peers

    def getState(self):
        return {
            "connected": self.espnow.active(),
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
                            schedule(self.loadPeer,
                                     self.__decodeHexBytes(host))
                            # self.loadPeer(self.__decodeHexBytes(host))
                    except:
                        rcvdMsg = {"error": "other"}

                    rcvdMsg["FROM"] = self.__decodeHexBytes(host)

                    def re(m):
                        rmpa = [rcvdMsg["FROM"], msg.decode("utf-8")]
                        rmkwa = {"source": rmpa[0], "message": rmpa[1]}
                        try:
                            self.rawMessage(*rmpa, **rmkwa)
                        except TypeError as e:
                            pass

                        self.message = rcvdMsg

                    schedule(re, rcvdMsg)

                if self.stop:
                    break

        _thread.exit()

    def send(self, msg, to="*", sync=False):

        response = False

        try:
            if to == "*":
                response = self.espnow.send(msg)
            else:
                if len(to) == 12:
                    encTo = self.__encodeHexBytes(to)
                    response = self.espnow.send(encTo, msg, sync)
        except OSError as ose:
            response = str(ose.args[0]) + " : "+str(ose.args[1])

        return {
            "to": to,
            "msg": msg,
            "sync": sync,
            "response": response
        }
