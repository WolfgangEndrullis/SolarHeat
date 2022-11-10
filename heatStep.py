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

    heater_name_status_list = []
    heater_names = []
    total_watt = 0
    # a tuple of heater names, defining an exchange in the heater_status_list
    switch_tuple = None

    def __init__(self, heater_status_list):
        self.heater_name_status_list = heater_status_list
        for heater_status in self.heater_name_status_list:
            the_name = self.__heater_name(heater_status[0])
            self.heater_names.append(the_name)
        self.__calculate_total_watt(True)

    def __calculate_total_watt(self, according_step_definition) -> int:
        """ Calculates the total load in Watt of this heating level.

        according_step_definition = True

        The calculation is performed according to the definition of the step.
        But disabled and faulty heaters produce 0 Watt.

        according_step_definition = False

        If a heater is switched off, disabled or cannot be reached, 0 Watt is assumed for this.

        :return: int: total load in Watt
        """
        self.total_watt = 0
        for heater_status in self.heater_name_status_list:
            the_name = self.__heater_name(heater_status[0])
            the_load = heater_status[1]
            heater = heaters.dict[the_name]
            if according_step_definition:
                if heater.is_enabled():
                    self.total_watt += heater.get_watt_of_status(the_load)
            else:
                try:
                    if heater.is_enabled() and heater.is_on():
                        self.total_watt += heater.get_watt_of_status(the_load)
                except ConnectException:
                    pass
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
        return len(self.heater_name_status_list)

    def get_heater_status_tuple(self, index) -> tuple:
        if index < 0 or index >= len(self.heater_name_status_list):
            return None, None
        else:
            return self.__heater_name(self.heater_name_status_list[index][0]), self.heater_name_status_list[index][1]

    def get_all_heater_status_tuple_as_string(self) -> str:
        result = " "
        for heater_status in self.heater_name_status_list:
            heater_name = self.__heater_name(heater_status[0])
            heater = heater_by_name(heater_name)
            short_status = heater.get_short_status()
            result += "[%s %4s] " % (heater_name, short_status)
        return result

    def get_total_watt(self, according_step_definition) -> int:
        return self.__calculate_total_watt(according_step_definition)

    def set_all_heater(self, verbose=True) -> None:
        """ Sets the status of all heater devices according to the step definition. """
        for heater_status in self.heater_name_status_list:
            a_name, a_status = heater_status
            heat(self.__heater_name(a_name), a_status, verbose=verbose)

    def switch(self, heater_name1, heater_name2) -> str:
        """ Switches two heaters in the heat step definition to change their priority.

        If these two heaters are already switched, they will be switched back.

        :param heater_name1: a unique heater name
        :param heater_name2: a unique heater name
        :return: str: information about the result of the operation
        """
        if heater_name1 not in self.heater_names:
            raise ValueError("Unknown heater name: %r " % heater_name1)
        if heater_name2 not in self.heater_names:
            raise ValueError("Unknown heater name: %r " % heater_name2)
        if not self.switch_tuple:
            self.switch_tuple = (heater_name1, heater_name2)
            return "Heaters %r and %r are switched" % (heater_name1, heater_name2)
        else:
            (name1, name2) = self.switch_tuple
            if heater_name1 == name1 or heater_name1 == name2:
                if heater_name2 == name1 or heater_name2 == name2:
                    self.switch_tuple = None
                    return "Heater %r and %r no longer switched" % (heater_name1, heater_name2)
            self.switch_tuple = (heater_name1, heater_name2)
            return "Heater %r and %r switched" % (heater_name1, heater_name2)

    def clear_switch(self):
        """ Removes the switching of heaters. """
        self.switch_tuple = None

    def turn_off_all_heater(self):
        """ Turns all heater off. """
        for heater_status in self.heater_name_status_list:
            a_name, a_status = heater_status
            heat(self.__heater_name(a_name), "off")
