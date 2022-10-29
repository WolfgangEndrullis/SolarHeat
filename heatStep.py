#!/usr/bin/python
# coding=UTF-8

from heat import *


class HeatStep:
    """ Defines a group of heaters and their status. Offers functions to activate this heating level.

        The heaters and their status are given by string variables 'name' and 'status'.
        See class Heat for further explanation.

        Two heaters can be exchanged dynamically in the step definition.
        So the priority of this heaters can be switched.
    """

    heater_status_list = []
    total_watt = 0
    # a tuple of heater names, defining an exchange in the heater_status_list
    switch_tuple = None

    def __init__(self, heater_status_list):
        self.heater_status_list = heater_status_list
        self.__calculate_total_watt()

    def __calculate_total_watt(self) -> int:
        """ Calculates the total load in Watt of this heating level.

        :return: int: total load in Watt
        """
        self.total_watt = 0
        for heater_status in self.heater_status_list:
            the_name = self.__heater_name(heater_status[0])
            the_load = heater_status[1]
            heater = heaters.dict[the_name]
            if heater.is_enabled():
                self.total_watt += heater.get_watt_of_status(the_load)
        return self.total_watt

    def __heater_name(self, name) -> str:
        """ Gets the name of the heater considering a possibly defined switch_tuple.

        :param name: str: heater name
        :return: str: heater name
        """
        if not self.switch_tuple:
            return name
        else:
            (name1, name2) = self.switch_tuple
            if name == name1:
                return name2
            if name == name2:
                return name1
            return name

    def get_heater_count(self) -> int:
        return len(self.heater_status_list)

    def get_heater_status_tuple(self, index):
        if index < 0 or index >= len(self.heater_status_list):
            return None, None
        else:
            return self.__heater_name(self.heater_status_list[index][0]), self.heater_status_list[index][1]

    def get_all_heater_status_tuple_as_string(self):
        result = " "
        for heater_status in self.heater_status_list:
            heater_name = self.__heater_name(heater_status[0])
            heater = heater_by_name(heater_name)
            short_status = heater.get_short_status()
            result += "[%s %4s] " % (heater_name, short_status)
        return result

    def get_total_watt(self):
        return self.__calculate_total_watt() #self.total_watt

    def set_all_heater(self, verbose=True):
        for heater_status in self.heater_status_list:
            a_name, a_status = heater_status
            heat(self.__heater_name(a_name), a_status, verbose=verbose)

    def switch(self, heater_name1, heater_name2):
        if not self.switch_tuple:
            self.switch_tuple = (heater_name1, heater_name2)
        else:
            (name1, name2) = self.switch_tuple
            if heater_name1 == name1 or heater_name1 == name2:
                if heater_name2 == name1 or heater_name2 == name2:
                    self.switch_tuple = None
                    return
            self.switch_tuple = (heater_name1, heater_name2)

    def clear_switch(self):
        self.switch_tuple = None

    def turn_off_all_heater(self):
        for heater_status in self.heater_status_list:
            a_name, a_status = heater_status
            heat(self.__heater_name(a_name), "off")
