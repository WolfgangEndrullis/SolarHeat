#!/usr/bin/python
# coding=UTF-8

from heatStep import *
from heat import *


class HeatSteps:
    """ Parses the file heatSteps.json and provides a list of HeatStep objects.

        Supports the dynamic exchange of two heaters in all HeatStep objects.
    """

    # definition file
    heatStepsFile = "heatSteps.json"

    # list of HeatStep objects
    heatStepList = []

    def __init__(self):
        print("Parse HeatSteps ... and check connections to heaters. \n"
              "This can take a while because TinyTuya asks several times if heaters are not connected.")
        self.__parse(self.__read())

    def __read(self):
        f = open(self.heatStepsFile, 'r')
        content = f.readlines()
        f.close()
        return ' '.join(content)

    def __parse(self, content):
        for heater_list in json.loads(content):
            heat_step = HeatStep(heater_list)
            self.heatStepList.append(heat_step)

    def get_step_count(self):
        """ Return the number of heating steps """
        return len(self.heatStepList)

    def get_list(self):
        return self.heatStepList

    def switch(self, heater_name1, heater_name2):
        result = ""
        for st in self.heatStepList:
            result = st.switch(heater_name1, heater_name2)
        return result

    def clear_switch(self):
        for st in self.heatStepList:
            st.clear_switch()


# -------------------------------------------------------------------------------
# Test
# -------------------------------------------------------------------------------

if __name__ == '__main__':

    test_heat_steps = HeatSteps()
    test_heat_step = test_heat_steps.heatStepList[4]
    print(test_heat_step)
    for i in range(0, test_heat_step.get_heater_count()):
        name, status = test_heat_step.get_heater_status_tuple(i)
        print(name, status)
        heat(name, status)
