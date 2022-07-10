import conf
from peripheral import peripheral
from rob import ExceptionMqttDisconnected
from umqtt.simple import MQTTClient, MQTTException
from time import sleep
import _thread
import ujson
from machine import unique_id
from ubinascii import hexlify
import netutils
from jsu import TrueValues

_thread.stack_size(4096*2)


def send(s, msg, to="*", topic=False, retain=False, qos=0, encapsulate=True):
    return s.send(msg, to, topic, retain, qos, encapsulate)


# subscribe(self, newTopic)
def subscribe(s, topic=False):
    s.subscribe(topic)
    return {"subscribed": "done"}


def enable(s):
    return s.connect()


def disable(s):
    return s.deinit()


class mqtta(peripheral):
    po = False

    def __init__(self, options={"autostart": True}):
        super().__init__(options)

        self.pType = self.__class__.__name__
        self.pClass = "VIRTUAL"
        self.__msg = ""
        self.thread = None
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

        if self.isconnected():

            self.subscribe()

            if self.mqttInstance.__class__ is MQTTClient:
                self.mqttInstance.publish(self.defaultTopic,
                                          '{"data":"subscribed","all":"*","from":"'+self.CLIENT_ID+'"}', retain=False, qos=0)

            try:
                self.thread = _thread.start_new_thread(self.run, ())
            except Exception:
                print("mqtt THREAD EXCEPTION")

    def deinit(self):
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
        # print("Raw message")
        # print("\ttopic: " + topic)
        # print("\tmessage: " + message)
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
        except MQTTException as e:
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

    def run(self):
        a_lock = _thread.allocate_lock()
        while True:
            with a_lock:
                try:
                    self.mqttInstance.wait_msg()
                except OSError as e:
                    print("Mqtt Server Disconnected")
                    netutils.waitForNetUp()

                    if conf.mosquitto_reconnect:
                        print("\tTrying to reconnect to Mosquitto Server")
                        self.start()
                        break
                except:
                    self.connect()
        _thread.exit()

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

            self.rawMessage(decodedTopic, msg.decode("utf-8"), msgjs)

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
