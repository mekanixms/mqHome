import conf
from peripheral import peripheral
from umqtt.simple import MQTTClient, MQTTException
from time import sleep
import ujson
from machine import unique_id
from ubinascii import hexlify
import netutils
from jsu import TrueValues


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


class mqtt(peripheral):
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

        self.startmqtt()

        self.run()

    def startmqtt(self):
        self.mqttInstance = MQTTClient(client_id=self.CLIENT_ID, server=conf.mosquitto_server, user=conf.mosquitto_user,
                                       password=conf.mosquitto_pass, keepalive=65535)

        self.mqttInstance.set_callback(self.sub_cb)

        self.connect()

        if self.mqttInstance.__class__ is MQTTClient:

            self.subscribe()

            if self.mqttInstance.__class__ is MQTTClient:
                self.mqttInstance.publish(self.defaultTopic,
                                          '{"data":"subscribed","all":"*","from":"'+self.CLIENT_ID+'"}', retain=False, qos=0)

            sleep(5)

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
    def rawMessage(self, topic, message):
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
        # netutils.waitForNetServiceUp(
        #     conf.mosquitto_server, conf.mosquitto_port)

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
        while True:
            try:
                self.mqttInstance.wait_msg()
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
        go = False
        skipMessage = False

        if self.mqttInstance.__class__ is MQTTClient:

            decodedTopic = topic.decode('utf-8')
            self.rawMessage(decodedTopic, msg.decode("utf-8"))

            if decodedTopic == conf.PRESENCE:
                # raspund automat la PRESENCE
                self.mqttInstance.publish(
                    conf.BROADCAST_ONLINE, self.online_mesg, retain=True, qos=0)
            else:
                if decodedTopic == conf.defaultTopic:
                    # topic default interceptez cu observables in message
                    #  si prelucrez acolo; trimit datele doar json
                    try:
                        msgjs = ujson.loads(msg.decode("utf-8"))
                    except ValueError:
                        skipMessage = True

                    if "from" in msgjs:
                        if msgjs["from"] == self.CLIENT_ID:
                            skipMessage = True
                    else:
                        skipMessage = True

                    if not skipMessage:
                        # print("mqtt Msg to "+self.CLIENT_ID+"\tTopic: " +
                        #       topic.decode('utf-8')+"\n\t content:\t"+msg.decode("utf-8"))
                        # daca este pentru mine sau pt toate deviceurile sau pentru toate relele :)
                        if "to" in msgjs:
                            if msgjs["to"] == self.CLIENT_ID or msgjs["to"] == "*":
                                go = True
                            else:
                                go = False
                                # print("Not for me, skipping")

                        if go:
                            self.message = msgjs["data"]
                else:
                    # oricare al topic folosesc handler
                    # si apelez cu param topic si message
                    # daca mesajul este json parsez si trimit
                    # daca nu trimit text
                    try:
                        msgjs = ujson.loads(msg.decode("utf-8"))
                    except ValueError:
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
