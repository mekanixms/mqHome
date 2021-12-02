import usocket
from time import sleep
import network


def waitForNetUp():
    net = network.WLAN()
    if not net.isconnected():
        print("\tWifi Disconnected")
        sleep(1)
        while not net.isconnected():
            try:
                net.connect()
            except:
                print("Error trying to reconnect wifi")
                print("\tretrying in 2s")
            sleep(2)
    return True


def waitForNetServiceUp(host, port):

    while True:        
        try:
            s = usocket.socket()
            s.connect(usocket.getaddrinfo(
                host, port, 0, usocket.SOCK_STREAM)[0][-1])
        except OSError as e:
            if e.args[0] == 104:
                s.close()
                sleep(1)
        except Exception as e:
            print("Errors occured")
            print("\t" + str(e).upper())
            s.close()
            sleep(1)
        else:
            break

    return True
