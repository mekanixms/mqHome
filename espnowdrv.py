import conf
from peripheral import peripheral
import _thread
import ujson
import gc
from jsu import importJsonDictionaryFromFile, urlStringDecode

import network
import espnow
import ubinascii


def rebootAs(s, mode):
    if mode in ["mqtt/sta", "config/sta", "config/ap", "espnow/ap", "espnow/sta"]:
        print("Reboot request from ")
        conf.jsonConfig["run"] = mode
        conf.configFileSave()
        print("\tRebooting in "+mode+" mode")
        from machine import reset
        reset()


def broadcastForRegistration(s):
    mac = "ffffffffffff"

    s.loadPeer(mac)
    result = s.send(msg="BCAST_REG_PEER", to=mac)
    s.removePeer(mac)

    return {"result": result}


def addpeer(s, mac):
    toRet = s.loadPeer(mac)
    s.savePeersToFile()
    return {"result": toRet}


def removepeer(s, mac):
    toRet = s.removePeer(mac)
    s.savePeersToFile()
    return {"result": toRet}


def send(s, msg, to='*'):
    if type(msg) is str:
        m = urlStringDecode(msg.encode("utf-8"))
    else:
        m = msg

    return {"result": s.send(m, to)}


def enable(s):
    return {"result": s.start()}


def disable(s):
    return {"result": s.deinit()}


def savePeers(s):
    return {"result": s.savePeersToFile()}


def mem_manage():
    gc.collect()
    gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())


# https://micropython-glenn20.readthedocs.io/en/latest/library/espnow.html#espnow-and-wifi-operation

class espnowdrv(peripheral):
    espnow = None
    peersAlias = {}
    stop = False
    broadcast = 'ff'*6
    version = 0.13
    wap = network.WLAN(network.AP_IF)

    def __init__(self, options={"autostart": True, "broadcast": True, "wap_channel": 6}):
        super().__init__(options)

        self.pType = self.__class__.__name__
        self.pClass = "VIRTUAL"
        self.__msg = ""
        self.thread = None

        self.commands["send"] = send
        self.commands["connect"] = enable
        self.commands["addPeer"] = addpeer
        self.commands["broadcastRegister"] = broadcastForRegistration
        self.commands["removePeer"] = removepeer
        self.commands["disconnect"] = disable
        self.commands["rebootAs"] = rebootAs
        self.commands["savePeers"] = savePeers

        self.wap.active(True)
        if "wap_channel" in self.settings.keys():
            wap_channel = int(self.settings["wap_channel"])
        else:
            wap_channel = 2

        self.wap.config(channel=wap_channel)
        print("\tESPNow AP channel="+str(wap_channel))

        self.espnow = espnow.ESPNow()
        self.espnow.active(True)

        self.loadPeers()

        if "broadcast" in options.keys():
            if options["broadcast"]:
                print("\tESPNOWDRV Broadcasting for registration")
                broadcastForRegistration(self)

        if "autostart" in options.keys():
            if options["autostart"]:
                print("Autostart enabled")
                self.start()

    def start(self):
        if "on_recv" in dir(self.espnow):
            self.espnow.on_recv(self.onrcvcbk)
            print("\tespnow driver running in on_recv mode mp < 1.20")
        else:
            if "irq" in dir(self.espnow):
                self.espnow.irq(self.onrcvcbk)
                print("\tespnow driver running in irq mode (mp >= 1.20)")
            else:
                _thread.stack_size(4096*2)
                try:
                    self.thread = _thread.start_new_thread(self.run, ())
                    print("\tespnow driver running in thread mode")
                except Exception:
                    print("THREAD EXCEPTION")

    def loadPeers(self):
        peers = importJsonDictionaryFromFile("peers.json")
        for peer in peers:
            self.loadPeer(peers.get(peer))
            self.peersAlias[peers.get(peer)] = peer

        return peers

    def savePeersToFile(self):
        peersOut = {}
        peers = self.getPeersByMac()
        i = 0
        for id in peers:
            label = i
            if id in self.peersAlias.keys():
                label = self.peersAlias.get(id)

            peersOut[label] = id
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
            "aliases": self.peersAlias,
            "stats": self.espnow.stats()
        }

    def getObservableMethods(self):
        return ["rawMessage"]

    def getObservableProperties(self):
        return ["message"]

    def __decodeHexBytes(self, val):
        return ubinascii.hexlify(val).decode("utf-8")

    def __encodeHexBytes(self, val):
        return ubinascii.unhexlify(bytes(val, "utf-8"))

    def __re(self, host, msg):
        decodedFromMac = self.__decodeHexBytes(host)

        try:
            m = ujson.loads(msg.decode("utf-8"))
        except ValueError:
            m = {"message": msg.decode("utf-8")}

            if m["message"] == "BCAST_REG_PEER":
                self.loadPeer(decodedFromMac)
                self.savePeersToFile()
            if m["message"].startswith("BCAST_REG_ALIAS/"):
                pAlias = m["message"].strip("BCAST_REG_ALIAS/")
                if pAlias:
                    self.peersAlias[decodedFromMac] = pAlias
                    self.loadPeer(decodedFromMac)
                    self.savePeersToFile()

        except:
            m = {"error": "other"}

        m["source"] = decodedFromMac
        if "message" not in m.keys():
            m["message"] = msg.decode("utf-8")

        # rmpa = [m["FROM"], m["message"]]
        # rmkwa = {"source": rmpa[0], "message": rmpa[1]}
        rmkwa = {"source": decodedFromMac, "message": msg}

        try:
            self.rawMessage(**rmkwa)
        except TypeError as e:
            pass

        self.message = m

        mem_manage()

    def onrcvcbk(self, enow):
        while enow.any():
            host, msg = enow.irecv(-1)
            # timeout < 0: Do not timeout, ie. wait forever for new messages
            # host, msg = self.espnow.irecv(-1)
            if msg:
                self.__re(host, msg)

    def run(self):
        a_lock = _thread.allocate_lock()
        while True:
            with a_lock:
                if self.espnow.any():
                    host, msg = self.espnow.irecv(-1)

                    if msg:
                        self.__re(host, msg)

                    if self.stop:
                        break

        _thread.exit()

    @peripheral._trigger
    def send(self, msg, to="*", sync=False):

        response = False

        try:
            if to == "*":
                #  If mac is None (ESP32 only) the message will be sent to all registered peers
                # except any broadcast or multicast MAC addresses
                response = self.espnow.send(None, msg)
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
