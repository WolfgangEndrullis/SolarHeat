#!/usr/bin/python
# coding=UTF-8
import time

import tinytuya


class DisableException(Exception):
    """ Exception if disabled heaters are requested.
        Fired in case of requests that only make sense for enabled heaters.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ConnectException(Exception):
    """ Exception if not connected heaters are requested.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Heater:
    """ Heater object with all its properties and functions for control and information.

        The Heater objects are generated in the class Heaters using the configuration file heaters.json.

        If a heater is disabled, no connection will be established to it.
        But a (dynamically) disabled heater can still have wattHours.
    """

    enabled = True
    name = ""
    ip = ""
    id = ""
    key = ""
    loadIndex = -1
    load = {}
    isOnIndex = -1

    # Device.
    heaterDevice = None

    # To sum the output of the heating.
    wattHours = 0
    lastChangeTime = None

    # To detect if network errors still exist we ask only every 3 minutes.
    connectError = False
    connectErrorTime = 0
    connectErrorRetrySeconds = 180

    # enabled = False  and  connectError = True  are critical values with implications for the HeatStep objects.
    # If this values change, the manager has to be informed via inform_about_new_step_definition().
    # To detect such changes, the following properties are used.
    lastEnabled = True
    lastConnect = False
    dynamic_config_change = False

    def __init__(self, heater_dictionary):
        """ Initializes the Heater object without establishing a connection to the heater device.

        :param heater_dictionary: the parameters of the heater
        """
        self.enabled = heater_dictionary['enable'].lower() == "true"
        self.name = heater_dictionary['name']
        self.ip = heater_dictionary['ip']
        self.id = heater_dictionary['id']
        self.key = heater_dictionary['key']
        self.isOnIndex = heater_dictionary['isOnIndex']
        self.loadIndex = heater_dictionary['loadIndex']
        self.load = heater_dictionary['load']

        self.lastEnabled = self.enabled
        self.lastConnect = False
        self.dynamic_config_change = False

    def __device(self) -> tinytuya.OutletDevice:
        """ The heater device provided by TinyTuya.

        This device object contains all connection properties, but the connection itself follows
        with other functions.

        :returns
            tinytuya.OutletDevice: self.heaterDevice (set or updated after self.connectError)
        :raises
            DisableException: if the heater is disabled by project configuration
        """
        if self.enabled:
            if self.heaterDevice is None or self.connectError:
                self.heaterDevice = tinytuya.OutletDevice(self.id, self.ip, self.key)
                self.heaterDevice.set_version(3.3)
            return self.heaterDevice
        else:
            raise DisableException

    def get_dps(self) -> dict:
        """ Requests the DPS dictionary from the heater.

        :returns
            Dictionary: original 'dps' content returned by the heater.
        :raises
            ConnectException: if the heater is not connected.
        """
        d: dict = self.get_status_dictionary()
        if "dps" not in d:
            raise ConnectException
        else:
            return d['dps']

    def get_load(self) -> str:
        """ Requests the current load from the heater.

        :returns
            str: load value
        :raises
            ValueError: if the heater load value is unknown in the definition file heaters.json
        """
        dps = self.get_dps()
        load_value = dps[str(self.loadIndex)]
        if load_value in self.load:
            return load_value
        else:
            raise ValueError("undefined load value", load_value)

    def get_status_dictionary(self) -> dict:
        """ Requests the heater status.

        :returns
            Dictionary: original status got from the heater converted to String
        :raises
            DisableException: if the heater is disabled
            ConnectException: if the heater is not connected
        """
        """ Returns the original heater status as dictionary.
            Typical return looks like: {'devId': '45...55', 'dps': {'1': False, '2': 36, '3': 22, '4': 'low', '12': 0}}
            Raises DisableException if the heater is disabled.
            Raises ConnectException if the heater is not connected.
        """
        if not self.enabled:
            raise DisableException
        if self.connectError:
            if (time.time() - self.connectErrorTime) < self.connectErrorRetrySeconds:
                self.__raise_connect_exception()
        data = self.__device().status()
        if "Error" in data:
            self.connectError = True
            self.connectErrorTime = time.time()
            self.__raise_connect_exception()
        else:
            self.connectError = False
            self.__check_new_step_definition_by_connect(True)
            return data

    def get_status_string(self) -> str:
        """ Requests the heater status.

        :returns
            str: original status got from the heater converted to String
        :raises
            DisableException: if the heater is disabled
            ConnectException: if the heater is not connected
        """
        try:
            data = self.get_status_dictionary()
            return '%r' % data
        except DisableException:
            return "dis"
        except ConnectException:
            return "err"

    def get_short_status(self) -> str:
        """ Requests the heater load and builds a very short status information.

        :returns
            str: short status information like 'off', 'low', 'high', 'dis', 'err'
        :raises
            ValueError: if the heater load value is unknown in the definition file heaters.json
        """
        try:
            if self.is_on():
                return self.get_load()
            else:
                return "off"
        except DisableException:
            return "dis"
        except ConnectException:
            return "err"
        except ValueError:
            return "INTERNAL ERROR 1"

    def get_watt(self) -> int:
        """ Requests the heater load and looks up in the heaters definition for the corresponding Watt value.

        :returns
            int: current heater load in Watt
            0: if the heater is disabled or if there are connection problems
        """
        try:
            is_on = self.is_on()
            if not is_on or not self.enabled:
                return 0
            load = self.get_load()
            return self.load[load]
        except DisableException:
            return 0
        except ConnectException:
            return 0

    def get_watt_of_status(self, status) -> int:
        """ Takes a status or load string and looks for the corresponding Watt value.

        :param status: string like 'off', 'dis', 'low', 'high', ...
        :returns
            int: Watt value
        :raises
            ValueError: if the heater load value is unknown in the definition file heaters.json
        """
        if status == "off" or status == "dis" or not self.is_enabled() or self.is_err():
            return 0
        if status not in self.load:
            raise ValueError
        return self.load[status]

    def get_watt_hours(self) -> int:
        """ Returns the sum of Watt hours of this heater since existence of this object.

        :return: int: sum of Watt hours
        """
        self.sum_watt_hours()
        return self.wattHours

    def is_enabled(self) -> bool:
        """ A heater can be defined but disabled, e.g. if it is not connected to the power grid.

        :return: bool: True if the heater is enabled in the file heaters.json
        """
        return self.enabled

    def is_err(self):
        """ A heater can be in error state, e.g. if it is enabled but not connected to the power grid.

        :return: bool: True if the heater is in error state.
        """
        try:
            self.get_status_dictionary()
            return False
        except ConnectException:
            self.lastChangeTime = None
            return True

    def is_on(self):
        """ Requests the heater device and determines whether the heater is on.

        :raises: ConnectException if the heater is not reachable.
        :return: bool: True if the heater currently is on.
        """
        dps = self.get_dps()
        return dps[str(self.isOnIndex)]

    def is_one_time_config_change(self):
        value = self.dynamic_config_change
        self.dynamic_config_change = False
        return value

    def set_enabled(self, value):
        """ Sets the heater enabled or disabled, but does not change the config file heaters.json.

            Does not change the status of the heater! This is done by the manager.

        :param value: bool: True if the heater shall be enabled.
        """
        self.__check_new_step_definition_by_enable(value)
        self.enabled = value

    def set_load(self, load):
        """ Sets the heater device load status.

        :param load: string like 'off', 'low', 'high', ...
        :raises
            DisableException: if the heater is disabled
            ValueError: if the value load is not defined in the config file heaters.json
        """
        if not self.enabled:
            raise DisableException
        if self.load is None or load not in self.load:
            raise ValueError
        self.sum_watt_hours()
        device = self.__device()
        device.turn_on()
        device.set_value(self.loadIndex, load)
        self.lastChangeTime = time.time()

    def sum_watt_hours(self):
        """ Summarizes watt hours. This can include dynamically disabled heaters.

            Updates the class properties self.wattHours and self.lastChangeTime.
        """
        if self.lastChangeTime is None:
            return
        hours = (time.time() - self.lastChangeTime) / 3600.0
        watt = self.get_watt()
        self.wattHours += watt * hours
        self.lastChangeTime = time.time()

    def turn_on(self):
        """ Switches the heater device on.

        :raises
            DisableException: if the heater is disabled
        """
        if self.enabled:
            device = self.__device()
            device.turn_on()
            self.lastChangeTime = time.time()
        else:
            self.__raise_disable_exception()

    def turn_off(self):
        """ Switches the heater device off.

        :raises
            DisableException: if the heater is disabled
        """
        if self.enabled:
            self.sum_watt_hours()
            device = self.__device()
            if device is not None:
                device.turn_off()
            self.lastChangeTime = None
        else:
            self.__raise_disable_exception()

    def __check_new_step_definition_by_enable(self, is_enabled):
        if not self.dynamic_config_change:
            if is_enabled != self.lastEnabled:
                self.dynamic_config_change = True
                self.lastEnabled = is_enabled

    def __raise_disable_exception(self):
        self.__check_new_step_definition_by_enable(False)
        raise DisableException

    def __check_new_step_definition_by_connect(self, is_connect):
        if not self.dynamic_config_change:
            if is_connect != self.lastConnect:
                self.dynamic_config_change = True
                self.lastConnect = is_connect

    def __raise_connect_exception(self):
        self.__check_new_step_definition_by_connect(False)
        raise ConnectException


# -------------------------------------------------------------------------------
# Test
# -------------------------------------------------------------------------------

if __name__ == '__main__':
    test_heater = Heater({'enable': "True", 'name': 'white', 'ip': '192.168.178.72', 'id': '05407354483fda1d10eb',
                          'key': '681631f67c6cebaa', 'isOnIndex': 1, 'loadIndex': 4,
                          'load': {'low': 750, 'high': 1500}})
    print('name:', test_heater.name)
    print('ip:', test_heater.ip)
    print('id:', test_heater.id)
    print('key:', test_heater.key)
    print('isOnIndex:', test_heater.isOnIndex)
    print('loadIndex:', test_heater.loadIndex)
    print('load:', test_heater.load)
