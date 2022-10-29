#!/usr/bin/python
# coding=UTF-8 

import json
from heater import *


class Heaters:
    """ Parses the file heaters.json and provides a list and a dictionary
        of Heater objects.
    """
    
    heatersFile = "heaters.json"
    list = []
    dict = {}
    
    def __init__(self):
        self.__parse(self.__read())
    
    def __read(self) -> str:
        f = open(self.heatersFile, 'r')
        content = f.readlines()
        f.close()
        return ' '.join(content)
    
    def __parse(self, content) -> None:
        for heaterDict in json.loads(content):
            heater = Heater(heaterDict)
            self.list.append(heater)
            self.dict[heater.name] = heater

    def __calculate_total_watt_hours(self) -> int:
        """ Calculates the total electrical power produced by all heaters.

        :return: int: total electrical power
        """
        total_watt_hours = 0
        for heater in self.list:
            total_watt_hours += heater.get_watt_hours()
        return total_watt_hours

    def get_total_watt_hours(self):
        return self.__calculate_total_watt_hours()


# -------------------------------------------------------------------------------
# Test
# -------------------------------------------------------------------------------

if __name__ == '__main__':
    
    test_heaters = Heaters()
    print(test_heaters.list)
    print()
    print(test_heaters.dict)
    print()
    print(test_heaters.dict['white'])
    print()
    if len(test_heaters.list) > 0:
        print(test_heaters.list[0].name)
    