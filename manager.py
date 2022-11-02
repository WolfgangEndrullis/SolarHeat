#!/usr/bin/python3
# coding=UTF-8

import threading
from heatSteps import *
from solar import *

heatSteps = HeatSteps()


def get_time_string():
    return time.strftime("%d.%m.%y %H:%M")


class HeatManager(threading.Thread):
    """ Manages the use of HeatSteps depending on the current photovoltaic production.

        Runs a loop and checks every loop_time seconds, if there is
    """

    loop_time_seconds = 60
    tolerated_akku_grid_usage_in_watt = 30

    solar = None
    heatStepList = None
    heatStepIndex = 0
    running = False
    verbose = True

    step = None
    dynamic_config_change = False

    status_print = ""

    def __init__(self):
        super().__init__()
        self.solar = Solar()
        self.heatStepList = heatSteps.heatStepList

    def is_running(self):
        return self.running

    def run(self):
        if self.running is True:
            return
        self.running = True
        # wait a few seconds - let the HeatServer lead
        time.sleep(5)
        print(get_time_string() + " Manager is started!")
        if self.solar.is_supply_to_grid():
            self.__measure_loop()
        else:
            self.__try_loop()

    def set_verbose(self, verbose):
        self.verbose = verbose

    def __start_try_loop(self):
        """ Sets the highest possible HeatStep """
        for index in range(0, len(self.heatStepList)):
            self.step = self.heatStepList[index]
            self.solar.update()
            akku_grid = self.solar.get_watt_akku_grid()
            print("AKKU+GRID:", akku_grid)
            if akku_grid < self.tolerated_akku_grid_usage_in_watt:
                self.step.set_all_heater()
                self.heatStepIndex = index
                time.sleep(self.loop_time_seconds)

    def __try_loop(self):
        """ Sets and updates to the highest possible HeatStep """
        self.__start_try_loop()
        sticky_count = 0
        while self.running:
            now = get_time_string()
            self.solar.update()
            akku_grid = self.solar.get_watt_akku_grid()
            print(now, "AKKU+GRID", akku_grid, "  ", self.step.get_all_heater_status_tuple_as_string())
            if akku_grid > self.tolerated_akku_grid_usage_in_watt:  # parameter
                if self.heatStepIndex > 0:
                    self.heatStepIndex -= 1
                    self.step = self.heatStepList[self.heatStepIndex]
                    self.step.set_all_heater()
                    self.stickyStepIndex = self.heatStepIndex
                    sticky_count = 5  # parameter
            else:
                if sticky_count > 0:
                    sticky_count -= 1
                else:
                    if self.heatStepIndex < len(self.heatStepList) - 1:
                        self.heatStepIndex += 1
                        self.step = self.heatStepList[self.heatStepIndex]
                        self.step.set_all_heater()
            time.sleep(self.loop_time_seconds)

    def __measure_loop(self):
        self.step = self.heatStepList[0]
        self.step.set_all_heater(verbose=self.verbose)
        while self.running:
            try:
                # 'available' takes into account the current availability of the heaters
                #
                # If some heaters are temporarily unavailable, a high heat setting can be selected
                # with the remaining heaters. If the heaters are available again, this change must
                # lead to a recalculation of the heating level. The suddenly high value of 'available'
                # does not reflect the real power use.
                available = self.__get_status_and_available()
                if not self.dynamic_config_change:
                    self.dynamic_config_change = heaters.is_dynamic_configuration_change()
                cs = "  CS" if self.dynamic_config_change else ""
                if self.verbose:
                    print(self.status_print + cs)
                i = len(self.heatStepList)
                for st in reversed(self.heatStepList):
                    i -= 1
                    # print(st.heater_status_list)
                    total_watt = st.get_total_watt(True)
                    # print("TOTAL", total_watt)
                    if available >= total_watt or i == 0:
                        if st != self.step or self.dynamic_config_change:
                            self.dynamic_config_change = False
                            st.set_all_heater(self.verbose)
                            self.step = st
                        break
                time.sleep(self.loop_time_seconds)
            except Exception:
                pass
        self.step.turn_off_all_heater()
        print("Manager is stopped and all Heaters are OFF!")

    def __get_status_and_available(self):
        if self.solar is None or self.step is None:
            return ""
        now = get_time_string()
        self.solar.update()
        watt_pv = self.solar.get_watt_pv() / 1000.0
        watt_grid = self.solar.get_watt_grid()  # negative into the grid
        watt_akku = self.solar.get_watt_akku()  # negative into the akku
        watt_minimal_charge = - self.solar.get_watt_minimum_charge()
        percent = self.solar.get_charged_percent()
        # --- available ---
        # watt_grid < 0 and watt_akku < 0, if excess energy goes into these systems.
        # watt_minimal_charge < 0, since charging power is always negative in the system.
        # We want to calculate the available power with positive sign!
        # So really available is first:  - watt_grid - watt_akku
        # We need to subtract the minimum charge current from that: watt_minimal_charge
        # But if electricity is already flowing into the heaters, then we have to take this into account.
        # self.step.get_total_watt() has to calculate the really current flow,
        # not the theoretical load level of the HeatStep.
        available = round(- watt_grid - watt_akku + watt_minimal_charge + self.step.get_total_watt(False), 2)
        total_kwh = heaters.get_total_watt_hours() / 1000.0
        heater_string = self.step.get_all_heater_status_tuple_as_string()
        self.status_print = \
            "%s  (%3.1fk) %+8.1f GRD %+8.1f AKK (%2.1f) %8.1f MIN %+8.1f AVA %s %.1f kWh" % \
            (now, watt_pv, watt_grid, watt_akku, percent, watt_minimal_charge, available, heater_string, total_kwh)
        return available

    def get_status_print(self):
        self.__get_status_and_available()
        return self.status_print

    def inform_about_new_step_definition(self):
        self.dynamic_config_change = True

    def stop(self):
        self.running = False


manager = HeatManager()


def start_manager(verbose=True):
    if manager.is_running():
        return "Manager is already running."
    print(get_time_string(), "Manager is starting ...")
    manager.set_verbose(verbose)
    manager.start()
    return "Manager is starting ..."


def stop_manager():
    if not manager.is_running():
        return "Manager is already stopped."
    manager.stop()
    return "Manager is stopping and all Heaters will be OFF!"


def verbose_manager(verbose):
    manager.set_verbose(verbose=verbose)
    return "Manager is set verbose = " + verbose


def status():
    global manager
    if manager is None:
        return "Manager has to been started first."
    return manager.get_status_print()


# -------------------------------------------------------------------------------
# Test
# -------------------------------------------------------------------------------

if __name__ == '__main__':
    start_manager(verbose=True)
