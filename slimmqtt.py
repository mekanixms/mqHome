import conf
from abstractObservable import observable
from rob import MQTTClient, ExceptionMqttDisconnected, simple
from time import sleep
import _thread
import ujson
from machine import unique_id
from ubinascii import hexlify
import netutils
from jsu import TrueValues

_thread.stack_size(4096*2)


class slimmqtt(observable):
    po = False

    def __init__(self, autostart=True):
        super().__init__()

        self.__msg = ""
        self.thread = None
        self.mqttInstance = False
        self.unique_id = hexlify(unique_id()).decode('utf-8')
        self.defaultTopic = conf.jsonConfig["defaultTopic"] if "defaultTopic" in conf.jsonConfig else "mqhomeintercom"
        self.topics = [self.defaultTopic, conf.PRESENCE, conf.DEVICE_CONFIG]
        self.topicHandlers = {}
        self.CLIENT_ID = 'mq'+self.unique_id
        self.online_mesg = ujson.dumps({
            "name": self.CLIENT_ID,
            "state": "ONLINE",
            "alias": conf.jsonConfig["alias"] if "alias" in conf.jsonConfig else "",
            "group": conf.jsonConfig["group"] if "group" in conf.jsonConfig else ""
        })

        if autostart:
            self.start()

    def start(self):
        self.connect()

        if self.mqttInstance.__class__ is MQTTClient:

            self.subscribe()

            try:
                self.thread = _thread.start_new_thread(self.run, ())
            except Exception:
                print("mqtt THREAD EXCEPTION")

            if self.mqttInstance.__class__ is MQTTClient:
                self.mqttInstance.publish(self.defaultTopic,
                                          '{"data":"subscribed","all":"*","from":"'+self.CLIENT_ID+'"}', retain=False, qos=0)

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
    @observable._watch
    def message(self, val):
        self.__msg = val

    def getState(self):
        return {
            "id": self.CLIENT_ID,
            "connected": True if self.mqttInstance.__class__ is MQTTClient else False,
            "topics": ",".join(self.topics)
        }

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

    def run(self):
        a_lock = _thread.allocate_lock()
        while True:
            with a_lock:
                try:
                    self.mqttInstance.wait_msg()
                except ExceptionMqttDisconnected as err:
                    print("Mqtt Server Disconnected")

                    netutils.waitForNetUp()

                    if conf.mosquitto_reconnect:
                        print("\t\tTrying to reconnect to Mosquitto Server")
                        self.mqttInstance.reconnect()
                except:
                    print("Unhandled errors occured")
                    # restart thread??
                    # sleep(4)
                    # break
        a_lock.release()

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
                            self.message = msgjs
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
