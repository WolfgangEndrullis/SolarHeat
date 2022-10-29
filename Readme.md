# SolarHeat

SolarHeat is a small and simple solution to use superfluous electrical 
energy from a photovoltaic system for heating. 
It automatically manages a group of electric heaters in defined heat steps 
with the aim of making  maximum use of the own energy from the roof. It 
provides an HTTP server for remote control and information. 

The requirements to use the application are:

- an API to request your photovoltaic system,
- electrical heaters integrated in the Tuya framework,
- a Linux or Windos PC, ideally a Raspberry Pi, with Python.

The API of the photovoltaic system has to support some power flow real time 
data and the state of charge of the accumulator. The requests and features 
are summarized in solar.py. The present version supports the Fronius Solar 
API V1. It is tested and works every day with an inverter Fronius Symo Gen24.

To support another electric inverter, the class Solar has to be adjusted.

Electric heaters can today usually be controlled via an App. Many of them 
use in the background the Tuya framework, even if this is not obvious. Such 
devices can be remotely controlled with an API. [TinyTuya](https://github.com/jasonacox/tinytuya) is a nice library for this.

SolarHeat uses TinyTuya. Everything that needs to be done to use the Tuya 
framework is described in the [TinyTuya project](https://github.com/jasonacox/tinytuya).

SolarHeat is tested and works sucessfully with heaters named EVERWARM GPH 
1500W Wifi or WARM CRYSTAL 2000W Wifi. 

### To make it work for you

If your photovoltaic system supports another API than Fronius Solar API V1, 
you have to adjust the class Solar.

#### solar.py

The file solar.py contains the class Solar, which determines and provides 
among other properties the following power flow real time data:

    * watt_grid  - power flow between inverter and grid (negative to the grid, positive from grid to inverter)
    * watt_accu  - power flow between inverter and accumulator (negative to the accu, positive from accu to inverter)
    * charged_percent  - current state of charge of the accumulator in percent

If there is no accumulator in the system, watt_accu could simply set to 0.

Superfluous electrical energy goes into the grid and into the accumulator. 
But the accumulator should of course be charged up to a certain time of day! 
There are corresponding parameters defined in the Solar class to manage the 
energy. They are easy to understand.

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

