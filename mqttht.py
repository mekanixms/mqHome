import conf
from peripheral import peripheral
from umqtt.simple import MQTTClient, MQTTException
from time import sleep
import ujson
from machine import unique_id, Timer
from ubinascii import hexlify
import netutils
from jsu import TrueValues


def send(s, msg, to="*", topic=False, retain=False, qos=0, encapsulate=True):
    return s.send(msg, to, topic, retain, qos, encapsulate)


def subscribe(s, topic=False):
    s.subscribe(topic)
    return {"subscribed": "done"}


def enable(s):
    return s.connect()


def disable(s):
    return s.deinit()


class mqttht(peripheral):
    po = False

    def __init__(self, options={"autostart": False, "id": 2}):
        super().__init__(options)

        self.pType = self.__class__.__name__
        self.pClass = "VIRTUAL"
        self.__msg = ""
        self.hTimer = Timer(int(self.settings.get("id")))
        self.mqttInstance = False
        self.unique_id = hexlify(unique_id()).decode('utf-8')
        self.defaultTopic = conf.jsonConfig["defaultTopic"] if "defaultTopic" in conf.jsonConfig else "mqhomeintercom"
        self.topics = [self.defaultTopic, conf.PRESENCE,
                       conf.DEVICE_CONFIG, conf.PERIPHERAL_CMDS, conf.DEVICE_CMDS, conf.STATUS_UPDATE_TOPIC]
        self.topicHandlers = {}
        self.CLIENT_ID = 'mq'+self.unique_id
        self.commands["send"] = send
        self.commands["connect"] = enable
        self.commands["subscribe"] = subscribe
        self.commands["disconnect"] = disable
        self.online_mesg = ujson.dumps({
            "name": self.CLIENT_ID,
            "state": "ONLINE",
            "alias": conf.jsonConfig["alias"] if "alias" in conf.jsonConfig else "",
            "group": conf.jsonConfig["group"] if "group" in conf.jsonConfig else ""
        })

        if options["autostart"]:
            print("Autostart enabled")
            self.start()

    def start(self):
        self.connect()

        if self.mqttInstance.__class__ is MQTTClient:

            self.subscribe()

            if self.mqttInstance.__class__ is MQTTClient:
                self.mqttInstance.publish(self.defaultTopic,
                                          '{"data":"subscribed","all":"*","from":"'+self.CLIENT_ID+'"}', retain=False, qos=0)

            self.hTimer.init(period=100, mode=Timer.PERIODIC,
                             callback=self.run)

    def deinit(self):
        self.hTimer.deinit()
        self.mqttInstance.disconnect()

    def subscribe(self, newTopic=False):
        if self.mqttInstance.__class__ is MQTTClient:
            if newTopic.__class__ is str and len(newTopic) > 0:
                if newTopic not in self.topics:
                    self.topics.append(newTopic)
                    try:
                        self.mqttInstance.subscribe(newTopic)
                    except:
                        print("ERROR while trying to subscribe")
                else:
                    print("Already subscribed to "+newTopic)
            else:
                allTopics = []
                allTopics.extend(self.topics)
                # additionalTopics
                if "additionalTopics" in conf.jsonConfig:
                    allTopics.extend(
                        conf.jsonConfig["additionalTopics"].split(","))

                for t in allTopics:
                    print("Subscribing to "+t)
                    try:
                        self.mqttInstance.subscribe(t)
                    except:
                        print("\tERROR while trying to subscribe to "+t)

    @property
    def message(self):
        return self.__msg

    @message.setter
    @peripheral._watch
    def message(self, val):
        self.__msg = val

    @peripheral._trigger
    def rawMessage(self, topic, message, jsonmessage):
        pass

    def getState(self):
        return {
            "id": self.CLIENT_ID,
            "connected": True if self.mqttInstance.__class__ is MQTTClient else False,
            "topics": ",".join(self.topics)
        }

    def getObservableMethods(self):
        return ["rawMessage"]

    def getObservableProperties(self):
        return ["message"]

    def connect(self):
        skip = False
        netutils.waitForNetServiceUp(
            conf.mosquitto_server, conf.mosquitto_port)
        self.mqttInstance = MQTTClient(self.CLIENT_ID, conf.mosquitto_server, user=conf.mosquitto_user,
                                       password=conf.mosquitto_pass)

        self.mqttInstance.set_callback(self.sub_cb)

        try:
            self.mqttInstance.connect()
        except simple.MQTTException as e:
            print(ujson.dumps(e))
        except OSError as e:
            if e.args[0] == 104:
                print("Mqtt server not available")
                skip = True

        if self.mqttInstance.__class__ is MQTTClient and not skip:
            print("Connected to "+self.mqttInstance.server +
                  " on port "+str(self.mqttInstance.port))
            return self.mqttInstance
        else:
            return False

    def isconnected(self):
        try:
            self.mqttInstance.ping()
        except:
            print("\nlost connection to mqtt broker...")
            return False
        else:
            return True

    def run(self, t):
        try:
            self.mqttInstance.check_msg()
        except MQTTException as err:
            print("\n\n")
            print("Mqtt Exception")
            print(err)
            print("\n\n")

        except OSError as e:
            print("\n\n")
            print("OSError Exception")
            print(e)
            print(ujson.dumps(dir(e)))
            print("\n\n")

            netutils.waitForNetUp()

            if not self.isconnected():
                if conf.mosquitto_reconnect:
                    netutils.waitForNetServiceUp(
                        conf.mosquitto_server, conf.mosquitto_port)
                    try:
                        self.mqttInstance.connect(False)
                        self.subscribe()
                    except Exception as e:
                        print("Could not reconnect")
                        print(e)

    def send(self, msg, to="*", topic=False, retain=False, qos=0, encapsulate=True):

        toSend = {
            "from": self.CLIENT_ID,
            "to": to,
            "data": msg
        }

        if not topic:
            topic = self.defaultTopic

        if self.mqttInstance.__class__ is MQTTClient:
            if encapsulate in TrueValues:
                msgContent = ujson.dumps(toSend)
            else:
                msgContent = msg
            try:
                self.mqttInstance.publish(topic, msgContent, retain, qos)
            except:
                print("Error while trying to publish")

        return {
            "to": to,
            "topic": topic,
            "retain": retain,
            "qos": qos
        }

    def sub_cb(self, topic, msg):

        if type(self.mqttInstance) is MQTTClient:

            decodedTopic = topic.decode('utf-8')
            decodedMessage = msg.decode("utf-8")

            try:
                msgjs = ujson.loads(msg.decode("utf-8"))
            except ValueError:
                msgjs = {}

            if type(msgjs) is dict:
                if "data" in msgjs:
                    if type(msgjs["data"]) is str:
                        try:
                            msgjs["data"] = ujson.loads(msgjs["data"])
                        except ValueError:
                            pass

            rawMessagePosArgs = [decodedTopic, decodedMessage]
            rawMessageKwArgs = {
                "topic": decodedTopic,
                "message": decodedMessage
            }

            if type(msgjs) is dict:
                rawMessageKwArgs["jsonmessage"] = msgjs
            else:
                rawMessagePosArgs.append(msgjs)

            try:
                self.rawMessage(*rawMessagePosArgs, **rawMessageKwArgs)
            except TypeError as e:
                pass
                # print("\trawMessage call exception: "+"\n\t".join(e.args))

            if decodedTopic == conf.PRESENCE:
                self.mqttInstance.publish(
                    conf.BROADCAST_ONLINE, self.online_mesg, retain=True, qos=0)
            else:
                if decodedTopic == conf.defaultTopic:
                    go = False

                    if "from" in msgjs:
                        if msgjs["from"] == self.CLIENT_ID:
                            go = True

                    if "to" in msgjs:
                        if msgjs["to"] == self.CLIENT_ID or msgjs["to"] == "*":
                            go = True

                        if go:
                            self.message = msgjs
                else:
                    if msgjs == {}:
                        msgjs = msg.decode("utf-8")

                    if decodedTopic in self.topicHandlers:
                        tCBK = self.topicHandlers[decodedTopic]
                        if callable(tCBK):
                            try:
                                tCBK(**{"topic": decodedTopic,
                                        "message": msgjs,
                                        "mqttDriver": self
                                        })
                            except:
                                print(
                                    "Could not execute topic handler for: "+decodedTopic)
