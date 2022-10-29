#!/usr/bin/python
# coding=UTF-8 

import sys
from heaters import *

heaters = Heaters()


def heater_by_name(name):
    """ Returns the Heater object with given name. """
    return heaters.dict[name]


def heat(heater_name, heater_status=None, verbose=True):
    """ Interface routine for control and information about the heating system.

    :param heater_name: name of a heater | 'info' | 'help'
    :param heater_status: 'enable', 'disable', 'off', 'on', 'low', 'high', ...
    :param verbose: True or False
    :return: None
    """

    if heater_name == "info":
        text = ""
        for heater in heaters.list:
            text += "Status " + heater.name + ": " + heater.get_short_status() + "\n"
        text += "%r total Watt" % total_watt()
        print(text)
        return text

    if heater_name not in heaters.dict:
        print()
        print("Unknown heater name %r given!" % heater_name)
        print()
        raise ValueError

    heater = heater_by_name(heater_name)

    if heater_status is None:
        print()
        print("No status given! See help.")
        print()
        raise ValueError

    heater_status = heater_status.lower()

    status = heater.get_status_string()
    if status == "err":
        if verbose:
            print("Heater %r is ERR (may be not on the power grid)" % heater_name)
        return

    if status == "dis":
        if heater_status == "enable":
            heater.set_enabled(True)
            if verbose:
                print("Heater %r is ENABLED now." % heater_name)
            return
        else:
            if verbose:
                print("Heater %r is DISABLED." % heater_name)
            return

    if heater_status == "disable":
        heater.set_enabled(False)
        if verbose:
            print("Heater %r is DISABLED now." % heater_name)
        return

    if heater_status == "on":
        heater.turn_on()
        watt = heater.get_watt()
        if verbose:
            print("Heater %r is ON with %r Watt." % (heater_name, watt))
        return

    if heater_status == "off":
        heater.turn_off()
        if verbose:
            print("Heater %r is OFF." % heater_name)
        return

    if heater_status not in heater.load:
        print()
        print("Undefined status %r! See help." % heater_status)
        print()
        raise ValueError

    heater.set_load(heater_status)
    watt = heater.get_watt()
    if verbose:
        print("Heater %r is ON with %r Watt." % (heater_name, watt))


def total_watt():
    watt = 0
    for heater in heaters.list:
        watt += heater.get_watt()
    return watt


# -------------------------------------------------------------------------------
# Parse command line
# -------------------------------------------------------------------------------

if __name__ == '__main__':

    name = None
    status = None

    try:
        name = sys.argv[1]

        if name == "help":
            raise IndexError

        if len(sys.argv) > 2:
            status = sys.argv[2]
        heat(name, status)

    except IndexError:
        print(
            """
Usage 1: heat info

         Shows status information about all defined heaters
         and the photovoltaic unit.
         
Usage 2: heat [name]

         Shows status information about the heater with given name.
         Heater may not be named "info" or "help".

Usage 3: heat [name] [status]

         Sets the status of the heater with given name.
         
         status values are:
         on       - heater will be switched on
         off      - heater will be swichted off
         low      - heater will be switched on and set to low power
         high     - heater will be switches on and set to high power
         enable   - enable a disabled heater
         disable  - disable an enabled heater
         
         The heaters and their power steps have to be defined in the
         file heaters.json. You can define individual step names instead
         of 'low' and 'high', used to set the status of your heater.
         Each step name needs its corresponding electrical power in Watt.
         
Usage 4: heat help

         Shows this information.
""")
