# SolarHeat

SolarHeat is a small and simple solution to use superfluous electrical 
energy from a photovoltaic system for heating. 
It automatically manages a group of electric heaters in defined heat steps 
with the aim of making  maximum use of the own energy from the own roof. It 
provides an HTTP server for remote control and information. 

The requirements to use the application are:

- an API to request your photovoltaic system,
- electrical heaters integrated in the Tuya framework,
- a Linux or Windos PC, ideally a Raspberry Pi, with Python 3.

The API of the photovoltaic system has to support some power flow real time 
data and the accumulators state of charge. The requests and features 
are summarized in solar.py. The present version supports the Fronius Solar 
API V1. It is tested and works every day with an inverter Fronius Symo Gen24.

To support other electric inverters, the class Solar has to be adjusted.

Electric heaters can today usually be controlled via an App. Many of them 
use the Tuya framework in the background, even if this is not obvious. Such 
devices can be controlled remotely using an API. [TinyTuya](https://github.com/jasonacox/tinytuya) 
is a nice library for this.

SolarHeat uses TinyTuya. Everything that needs to be done to use the Tuya 
framework is described in the [TinyTuya project](https://github.com/jasonacox/tinytuya).

SolarHeat is tested and works sucessfully with heaters named EVERWARM GPH 
1500W Wifi or WARM CRYSTAL 2000W Wifi. 

It should be mentioned that the heaters can be controlled purely locally once they have been set up 
in the Tuya system. It is possible to withdraw all access rights to the Internet in the router!

### To make it work for you

If your photovoltaic system supports another API than Fronius Solar API V1, 
you have to adjust the class Solar.

#### solar.py

The file solar.py contains the class Solar, which determines and provides 
among other properties the following power flow real time data:

    * watt_grid  - power flow between inverter and grid (negative to the grid, positive from grid to inverter)
    * watt_akku  - power flow between inverter and accumulator (negative to the accu, positive from accu to inverter)
    * charged_percent  - current state of charge of the accumulator in percent

If there is no accumulator in the system, watt_akku could simply set to 0.

In general, superfluous electrical energy goes into the grid and/or 
accumulator. This amount of energy shows the power potentially available 
for heating. If, according to the settings of the solar system, no energy is 
supplied to the public grid, the following variable must be set False, 
otherwise True.

    * supply_to_grid = False | True

This variable will be interpreted by the HeatManager. It controls the basic 
algorithm.

Of course, the accumulator should be charged up to a certain time of day! 
There are corresponding parameters defined in the Solar class to manage this 
energy. They are easy to understand by their names:

    * max_charge - maximum charge level defined for the accumulator
    * full_akk_hour - final hour in which the accumulator should be charged

#### heaters.json

All heaters have to be defined in the file heaters.json. The example shows 
its principal structure. 

Some brief explanations of the properties:

    * enable    - heaters can be defined even if not currently being used
    * name      - a short unique name for the heater
    * ip        - IP address of the heater
    * id        - identifier of the heater in the Tuya framework
    * key       - key of the heater in the Tuya framework
    * isOnIndex - index in the heater property list, indicating status on | off
    * loadIndex - index in the heater property list, showing the heating level 
    * load      - names for the heating levels and corresponding power in Watt

### HeatServer

The server can be requested via HTTP requests:

http://...IP-ADDRESS...?do=...

It supports the following functions:

    do=start                            - starts the manager
    do=stop                             - stops the manager
    do=info                             - short information about the heaters
    do=status                           - full status information about the heaters und solar system
    do=verbose                          - turn on extensive logging on the server
    do=silent                           - turn off extensive logging on the server
    do=help                             - this help text
    do=enable&heater=name               - enable a heater
    do=disable&heater=name              - disable a heater
    do=switch&heater=name&heater=name   - exchanges two heaters in the HeatSteps definition
    do=clear                            - deletes the exchange of heaters

### HeatManager

The HeatManager controls the available energy and sets the maximum heating 
level. 

The heating levels are defined in the file heatSteps.json.

#### heatSteps.json

This file contains the states of all heaters in each heating stage. The 
heating levels must be specified in strictly ascending order. See the 
example file with three heaters.

#### Trial and error algorithm

If the solar system does not supply electricity to the public grid, the 
manager can only test what energy is available. This is done in the 
subroutine __try_loop(). See the class Solar and adjust 
supply_to_grid = False.

#### Measure and decide

If the solar systems does supply all its excess energy to the grid, the 
routine __measure_loop() is used. See the class Solar and adjust 
supply_to_grid = True.

#### Robustness

The process is on a 24x7 basis. Heaters can be unplugged and re-enabled. The 
manager can deal with intermittent errors and reintegrates heaters when they 
can be reached again via WLAN. The processing of changes usually takes a 
maximum of three minutes.

### Implementation

The following example shows an implementation on Linux, using **systemctl**. 
The application runs when the system is started as a system service - without the need for a user to login.

Create a file **start** with the following content in the directory with the 
Python project files - in this example /home/pi/bin/heat.

    #! /bin/sh

    cd /home/pi/bin/heat
    python3 server.py

Create a file **heat.system** with the following content in the directory 
/etc/systemd/system. Customize ExecStart!

    [Unit]
    Description=Heat Service and Manager
    Wants=network-online.target
    After=network.target network-online.target
    [Service]
    Type=idle
    User=pi
    ExecStart=/home/pi/bin/heat/start
    Restart=always
    RestartSec=60
    [Install]
    WantedBy=multi-user.target

During a session, the service can be controlled using the following commands:

    sudo systemctl start heat
    sudo systemctl stop heat
    sudo systemctl status heat
