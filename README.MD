# mqHome - ESP32 IoT manager

## Introduction

This software is focused on ESP32 platform and provides integration and use of multiple peripherals with simple automation capabilities.  
Clients applications are available as well as a [Android App](https://play.google.com/store/apps/details?id=com.mekanix.mqhomeadmin)

Examples:

 ESP32 with peripherals [stimer,fet,mqtta]

     stimer

```sql
  WHEN(heartbeat[1]):  dev[1]/freq(value=2)
  WHEN(heartbeat[0]):  dev[1]/freq(value=5)
```

     mqtta

```sql
  ON(rawMessage[0==T51,1==blink]):  dev[0]/start(period=0.1,enabled=True)
  ON(rawMessage[0==T51,1==stop]):  dev[0]/stop()
```

 ESP32 with peripherals [mqttht,aht10]

```sql
  WHEN(temperature[0>>25]):  dev[0]/send(topic=DISPLAY,msg=pargs[0])
  WHEN(temperature[0<<26]):  dev[0]/send(to=a4cf126ca224,topic=DISPLAY,msg=pargs[0],encapsulate=FALSE)
```
## Description

Can be configured with multiple peripherals:

* *input* (ex: analog_in,digital_in,debounced buttons,aht10,realbuttonv2,rotencoder,...)
* *output* (ex: bts7969, fet, relay,mpu 6050, nokia display,servo,...)
* *virtual* (ex: stimer,mqtt,mqtta,mqttht,receiver,messager)

Each peripheral is controlled by a driver (extends peripheral class)

For each peripheral we can define actions (or observables) when / on property/method change/called.

```sql
WHEN(CONDITION[pargs1 >> value,pargs2,...]):  TARGET_ACTION_1 TARGET_ACTION_2 ...
  ON(CONDITION[...]):          TARGET_ACTION_1 TARGET_ACTION_2 ...
```

Observables are defined in config mode

* *Condition operands:*
 == >> << >= <= != <>

* *Target actions:*
 dev[peripheralID]/command(optionalParam,...)
 mpu/method(optionalParam,...)
 context/set(variableName1=ValVar1,variableName2=ValVar2,...)

* *Target actions parameters* are evaluated with the following context:
 dev[
 pargs[
  positional parameters of the condition
 kargs[
 context[

Example:

 mqtta driver

 ```sql
  ON(rawMessage[0==UPTIME]):  dev[0]/toggle() dev[2]/send(topic=DISPLAY,msg="CLK: "+str(context['clicked']),encapsulate=false)
  ON(rawMessage[0==CONTEXT]):    context/set(topic=pargs[0]+' '+pargs[1]+" "+str(dev[0].value),CLIENT=dev[2].CLIENT_ID)
```

 presence sensor:

 ```sql
  ON(changed[1]): context/set(count=context['count']+1)  dev[2]/send(topic=DRIVE,msg=ON,encapsulate=false)
  ON(changed[0]): dev[2]/send(topic=DRIVE,msg=OFF,encapsulate=false)
```

As for now, mqHome has 4 default run modes: config, mqtt, espnow and single

* config mode (configr.py):

  In config mode, although the mqtt drivers can be enabled, the users is able to change device settings as well as define "observables" for automation purposes.
  Config mode is basically a small http server running on the mcu. Can be accessed directly from the web browser, curl, ... or programatically.
  A config client application (see clients/mcu2.html) is provided with this software (can run remotely or locally on a computer or phone)
  More info on the jssr.py section below

* mqtt mode (mqttr.py):

  In mqtt mode the devices can communicate via mqtt
  Mqtt mode provides intercomnucation  and loads peripherals and observables  but do not provide any configuring options.
  A mqtt client application (see clients/mqtt2.html) is provided with this software (can run remotely or locally on a computer or phone)
  More info on the mqttr.py section below

* espnow mode (espnowr.py):

  Enables espnow driver for communication

* single mode (singler.py):

  No communication between esp devices

* Repl over BLE (blereplr.py):

  Since 0.15.5 onward. If the device detects the settings file, apl.json, does not exists or if the Btn 1 (pinBtn1 is 13 by default in conf.py, available to overwrite through conf.jsonConfig) is pressed or when run mode is set to blerepl/off

To define new run modes please follow the template of the default ones above.

The run mode script is accesible, from main.py, through runner variable (if you have a prompt after initialization)

There are 3 network modes predefined:

* sta

  Enables STATION IF at boot time
* ap

  Enables AP IF at boot time
* off

  Disables both AP and STA IFs

The run modes can be set with "run" setting in apl.json directly or in the configr web app (mcu2.html) or directy, in repl as follows:

```bold
import conf
conf.jsonConfig["run"] = "config/sta"
conf.configFileSave()
```

It is recommended to run the scripts (all, except main.py) precompiled (mpy-cross).
For best performance have them built into the firmware (<https://docs.micropython.org/en/latest/develop/natmod.html>)

More info on [precompiled modules](https://docs.micropython.org/en/latest/reference/mpyfiles.html)

## Client utils

Both below scripts can run locallty or on a small, local http server. Additionally, an Android app is [available](https://play.google.com/store/apps/details?id=com.mekanix.mqhomeadmin&pcampaignid=web_share)

* mcu2.html

Used to connect to the devices via http, while they run in config mode; in config mode you can change the defaults, work with some of the peripherals and define automate rules

* mqtt2.html

Used to play with all devices that are tunning in mqtt mode (ofcourse, connected to a wifi hotspot)

* repl over Bluetooth LE

Available with the [Android App](https://play.google.com/store/apps/details?id=com.mekanix.mqhomeadmin&pcampaignid=web_share) and provides access to repl

## Drivers

### Communication

* mqtt drivers

Check mqtt.py (tested / blocking), mqtta.py (tested/beta, working well) and mqttht.py (tested, stable)

* espnow

Check espnowdrv.py

* uart communication

Check uartcomm.py, uartcomml.py, uartcomms.py, uartcommht.py (tested, stable), uartcommt.py


### Drivers list

* aht10
* bts7960
* analog_in
* digital_in
* espnowdrv
* fet
* mpu6050
* mqtt, mqtta, mqttht
* nokiadisplay
* realbutton
* realbuttonv2
* relay
* rotencoder
* servo
* stimer
* uartcomm, uartcommht, uartcomml, uartcommp, uartcomms, uartcommt 
* vtimer

## Files description

### conf.py

 default options
 user rewriteble from apl.json

* run (conf/sta, mqtt/sta, conf/ap)
* mosquitto_server
* mosquitto_user
* mosquitto_pass
* group
* pinModeSwitch (used only in main.py)
* pinBtn1 (used only in main.py)
* pinBtn2 (used only in main.py)

### main.py

* boots up the esp in selected run mode

  runAs, stationMode = conf.run.split("/")
   where run can be conf/sta, mqtt/sta, conf/ap

* if btn1 and btn2 pressed overrites runAs to config mode
* if station not connected or stationMode is ap starts acces Point mode

### mqttr.py

* meant to provide mqtt communication to the mcu initialized with defined peripherals and obervables

* mqtt driver can be one of the following implementations:
  "mqtt" standard implementation (blocking)
  "mqtta" threaded implementation
  "mqttht" hardware timer implementation (default uses timer id 2)

* topicHandlers builtin and add to the last mqtt type peripheral
  
  BROADCAST_ONLINE = "DEVONLINE"
  BROADCAST_LASTWILL = "DEVLASTWILL"
  PRESENCE = "PRESENCE"

  STATUS_UPDATE_TOPIC = 'statusupdate'
   if messageIsForMe returns status of the mpu as json:

```json
   {
   "to": message["from"],
   "from": mqttDriver.CLIENT_ID,
   "data":{
                 "uptime": mpu.uptime(),
                 "muid": mpu.unique_id
                 },
    "data":{},
   //(if "pid" in message)
    "pid": mpu.peripherals[p_id].getState()
    }
```

  DEVICE_CONFIG = "DEVCONF"
   returns mpu config as json with the following data

```json
    {
      "to": message["from"],
    "from": mqttDriver.CLIENT_ID,
    "data":
        {
        "peripherals":
          [{"id","type","alias","commands"},
          {},....],
        "defaultPeripheral": conf.jsonConfig["defaultPeripheral"] if "defaultPeripheral" in conf.jsonConfig else 0,
        "byType": byType,
        "byAlias": byAlias,
        "muid": mpu.unique_id,
        "deviceid": mqttDriver.CLIENT_ID,
        "alias": conf.jsonConfig["alias"] if "alias" in conf.jsonConfig else mpu.unique_id,
        "hotspot": wifiName if wifiName is not None else "Not set",
        "network": mpu.wifi.ifconfig()
        }
    }
```

  PERIPHERAL_CMDS = "mqperipheralcmds"
    peripheral direct commands; comes as mqtt message with json content as

```json
    {
      "data": {"pid":,"cmd":,"opt":{}},
      "to": "mqac67b22cca0c",
      "from": "altClientNume"
    }
```

    if message is for this mpu and cmdName in mpu.peripherals[int(cmdto)].commandsList()
     executes mpu.peripherals[int(cmdto)].command(cmdName, cmdOptions)

  DEVICE_CMDS = "mqdevcmds"
    used to send direct command to the mpu
    if messageIsForMe execute
     ex: reboot in diferent working mode
      message["data"] in ["mqtt/sta", "config/sta", "config/ap"]:

  defaultTopic = "mqhomeintercom"
  
### configr.py

* "configr" script is running small http server (jss class) to configure the device
* http call example: <http://mcuaddress:port/cmd/0/freq?value=2>

Predefined routes:

#### /

```json
returns json
{
    "peripherals": [...],
    "byType": {},
    "byAlias": {},
    "uptime": mpu.uptime(),
    "muid": mpu.unique_id
}
```

#### /cmd

* /cmd/devid/cmdName/?options

```bold
    devid is numeric and corresponds to an existing peripheral
    cmdName one of the below otherwise, if found in periferalid.commandsList, execute peripheral command with options
```

* /cmd/devid/type

* /cmd/devid/commands

```bold
outputs peripheral commands list
```

* /cmd/devid/state

```bold
outputs peripheral state
```

* /cmd/devid/observable
*/observable/?what=properties*
*/observable/?what=methods*

* /cmd/devid/observables/?options
Where options are: set (json text), apply,load,reset

#### /machine

* /machine/reboot
* /machine/peripherals
* /machine/startup

#### /net

* /net/ap/enable
* /net/ap/started
* /net/st/list
*returns wifi.scan()*

```bash
curl http://localAddress:8080/net/st/list
```

* /net/st/connected
* /net/st/enable
*connects to what is saved with /conf/st/save*
* /net/st/connect/wifiName/wifiPass
*connects to wifiName*

#### /conf

* /conf/view
* /conf/st/saved
*get the saved station interface data*
* /conf/st/static?toip=..&netmask=...&gw=...&dns=...
*set station interface to static ip*
* /conf/st/dhcp
*set station interface ot get the ip address via dhcp*
* /conf/group/group1,group2,...
*set MCU groups*

* /conf/run/mqtt
* /conf/run/standalone
* /conf/alias/aliasName

* /conf/key/set/keyName?value=...
*set a variable to value in apl.json*

```bash
curl http://localAddress:8080/st/save/myWifiNetwork/myWifiPass
curl http://localAddress:8080/conf/key/set/run?value=mqtt/sta
```

* /conf/key/get/keyName
*get the value of keyName from apl.json*

* /conf/st/save/ssidName/pass
 *save station interface to connect to wifi*
* /conf/ap/save/ssidName/pass
 *save access point interface id and pass*

#### /message

    EXPERIMENTAL

#### /mqttsetup

* /mqttsetup/topic/set?script=...
* /mqttsetup/topic/get

### startup.run

* user defined python code executed after initilizing the peripherals and observables
* used for custom initialization of peripherals or mpu operations
* code executed with default context:
  "dev": mpu.peripherals
  "mpu": mpu
  "runMode":
      "config" for configr
      "mqtt" for mqttr
      "espnow" for espnowr
      "single" for singler

### apl.json

 contains json userdata to override some options in conf.py and manage others
 if not exists is initialized as empty json {}

### pph.json

 peripherals initialization
 user defined
 default []

### observables.json

 defined observables for each peripheral
 created by user in config mode (mcu2.html)

### utils/docgen.py

Python 3 script that extracts the docstrings for use with mcu2 and mqtt2 scripts


## How to Install

### Steps

1. Copy content of clients folder to a local webserver
2. Open pph.json and add your peripherals as needed. It contains some examples for your reference. I recommend you open the desired driver .py file and, from the __init__ constructor, copy the options to your .pph file (as value of initOptions key) and modify as needed
3. Transfer the .py scripts to your ESP32. For best performance is recommended to use a precompiled image (or make your own) or, at least, use mpy-cross to create the precompiled .mpy (all .py files, except main.py)
4. Copy  pph.json and startup.run on your ESP32
5. Reboot your device (first time would be recommended to stay connected to it so you can see the output and it boots properly)
6. Configure the device
- At first boot the device should go into config/ap mode
- preload mcu2.html (from the webserver) in a browser (Chrome, Firefox, Brave, Safari)
- connect your computer wifi to your esp AP interface (scan to find a ssid like below)
```text
    default ssid  is AP-XXXXXXXXXXXX
    default password is above XXXXXXXXXXXXpass
where XXXXXXXXXXXX is the device's mac address
```
When connected to device's AP wifi, add 192.168.4.1:8080 (default AP  address and config server port) and click OK;
in Setup Tab:
- Set a device alias
- Set a network configuration (STA interface); Click Network -> Scan for networks; when they are listed, click on the one you want and set the password; click Save when prompted and disregard the Could not connect message (at this stage is normal); Optionally AP network name and password
- You can also set the Mqtt Server connection info (port 1883 is the default one; remember is best if you have your mqtt server username and pass set to avoid unpredictable disconnect) and Groups option (used only to select the devices to display in mqtt2.html)
- If you click Config -> Show, the client will display the device's settings you did so far
- After above is set, is recommended to set Device -> Run mode to config/sta and do a Device -> Reboot;
- Try to connect with mcu2.html to the new address (you can either get it from the terminal, if you are still connected to the device via USB) or from your router; if you cannot connect or have any doubts, delete the apl.json file from the root of the ESP and redo this last step
- When you are connected, go and set the Mqtt Server data (if you use it), set the Run mode to whatever you need (ex mqtt/sta) and do reboot
- You could also set the Ip Config to static (it should give you the current ip address); change from dhcp to static
- If you use Mqtt, first Switch your computer wifi to the wifi network the device is currently set to, and you can load mqtt2.html, set the client required  mqtt server address, port (the default websocket port is typically 9001), username and password; once connected you will find each device listed as a tab and inside you will find peripherals; to reboot the device in a different run mode (ex: config/sta to go back and configure the device) look for Reboot and the nearby select will display a list of available run modes; select the right one and click go (remember the device address, from Device Info, if you need to connect to it via STA)
- more on mcu2 client (work with the device peripherals and set Animation) TODO
- more on mqtt2 client TODO


Notes:
- if you use mqtt, set a username and password on your server otherwise the devices will keep disconnecting
- before copying the client scripts, you may want to generate the 'json defs' using the script docgen.py inside utils directory;
```bash
$ python3 docgen.py
```
- copy generated externalCommands.json in the same location of mqtt2.html and mcu2.html and all the other *.py-def.json inside a pydef directory; these are loaded to give you instructions on the available parameters for each command


### Precompiled images
They are compiled from source of @glenn20 micropython v1.19.1 repo (ESPNow enabled https://github.com/glenn20/micropython/tree/espnow-g20)
- Generic ESP32
- SPIRam (WROVER)
[Available for download here](https://drive.google.com/drive/folders/1BDVXVYsRYnLQj8iEc7BwDJ-dXAx9ziKS?usp=share_link)


If you want to compile your own follows these steps:

```bash
# Download and install ESP-IDF
git clone -b v4.4 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh
source export.sh

# Download Glen20 Micropython source
git clone https://github.com/glenn20/micropython.git
cd micropython
git switch espnow-g20-v1.19.1


# Optional, if you want umqtt frozen in the firmware, otherwise you have to copy them later, manually 
cp /path/to/umqtt/files extmod/umqtt
cp extmod/uasyncio/manifest.py /extmod/umqtt
# add umqtt/simple.py and umqtt/robust.py 
mcedit extmod/umqtt/manifest.py
# add umqtt, similar with uasyncio
mcedit ports/esp32/boards/manifest.py



cd ports/esp32
# All .py files, except main.py
cp /path/to/mqHome/*.py modules/
make clean
# replace BOARD value with GENERIC or remove BOARD option for standard esp32
make BOARD=GENERIC_SPIRAM clean
make submodules
make
# or cp build-GENERIC/firmware.bin
cp build-GENERIC_SPIRAM/firmware.bin /to/safe/location/to-write-with-esptool



# Optional, compile mpy-cross executable, to compile for testing any .py and to mpy
make -C mpy-cross
```


Note:
- use esptool to write firmware.bin on your board

