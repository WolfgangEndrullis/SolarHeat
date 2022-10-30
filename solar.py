#!/usr/bin/python
# coding=UTF-8
import time

import requests


class Solar:
    """ Requests the parameter of the photovoltaic device.
        This class supports the Fronius Solar API V1.
        It needs to be adjusted for other power inverters.
    """

    # to request the power flow to (-) or from (+) the grid, accumulator and devices
    watt_url = "http://192.168.178.69/solar_api/v1/GetPowerFlowRealtimeData.fcgi"
    # to request the state of charge of the accumulator
    akku_url = "http://192.168.178.69/solar_api/v1/GetStorageRealtimeData.cgi"
    # the maximum charge level defined for the accumulator
    max_charge = 90
    # does the photovoltaic device supply to the grid?
    supply_to_grid = True
    # the final hour in which the accumulator should be charged
    full_akk_hour = 15
    # minimum power flow into the public grid after the accumulator has been charged
    min_grid_after_full_akk: 0

    # --------------------------------
    # power flow
    # --------------------------------
    watt_pv = 0
    watt_load = 0
    watt_akku = 0
    watt_grid = 0
    # --------------------------------
    # battery state of charge
    # --------------------------------
    charged_percent = 0

    def __init__(self):
        self.update()

    def update(self) -> None:
        """ Updates the solar realtime data """
        # --------------------------------
        # power flow
        # --------------------------------
        r = requests.get(self.watt_url)
        response = r.json()
        r.close()
        self.__parse_watt(response)
        # --------------------------------
        # battery state of charge
        # --------------------------------
        r = requests.get(self.akku_url)
        response = r.json()
        r.close()
        self.__parse_akku(response)

    def __parse_watt(self, response) -> None:
        site = response["Body"]["Data"]["Site"]
        self.watt_pv = site["P_PV"]
        self.watt_load = site["P_Load"]
        self.watt_akku = site["P_Akku"]
        self.watt_grid = site["P_Grid"]

    def __parse_akku(self, response) -> None:
        controller = response["Body"]["Data"]["0"]["Controller"]
        self.charged_percent = controller["StateOfCharge_Relative"]

    def get_watt_pv(self) -> int:
        return round(self.watt_pv, 2)

    def get_watt_load(self) -> int:
        return round(self.watt_load, 2)

    def get_watt_akku(self) -> int:
        return round(self.watt_akku, 2)

    def get_watt_grid(self) -> int:
        return round(self.watt_grid, 2)

    def get_watt_akku_grid(self) -> int:
        return round(self.watt_akku + self.watt_grid, 2)

    def get_charged_percent(self) -> int:
        return round(self.charged_percent, 2)

    def get_watt_minimum_charge(self) -> int:
        """ Calculates the minimum current in watts to charge the accumulator up to a certain time.

        :return: int: minimum current in watts
        """
        to_charge = self.max_charge - self.get_charged_percent()
        now = time.localtime()
        hour = now.tm_hour
        period = self.full_akk_hour - hour
        if period > 0:
            to_charge_with = 100 * to_charge / period
            # print("to charge with: %r Watt" %to_charge_with)
            return round(to_charge_with, 2)
        else:
            if to_charge < 5:
                return 0
            else:
                return round(100 * to_charge, 2)

    def is_supply_to_grid(self) -> bool:
        return self.supply_to_grid


# -------------------------------------------------------------------------------
# Test
# -------------------------------------------------------------------------------

if __name__ == '__main__':
    s = Solar()
    print("PV: %r  LOAD: %r  GRID: %r  AKKU: %r" %
          (s.get_watt_pv(), s.get_watt_load(), s.get_watt_grid(), s.get_watt_akku()))
    print("AKKU Charge: %r" % s.get_charged_percent())
    print(s.get_watt_minimum_charge())
