# -*- coding: iso-8859-15 -*-

# import the server implementation
from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.mei_message import *
from pyepsolartracer.registers import registerByName

from enum import IntEnum

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger(__name__)

# Battery state flags as reported by the charger, to make things more readable
EPBatteryState = IntEnum('EpBatteryState', [
    'NORMAL',
    'OVERVOLT',
    'UNDERVOLT',
    'UNDERVOLT_DISCONNECT',
    'OTHER_FAULT',
    'HOT',
    'COLD',
    'INTERNAL_RESISTANCE_ABNORMAL',
    'RATED_VOLTAGE_WRONG',
    'INVALID_VALUE'
], start=0)


#  Charger state flags as reported by the charger
# "RUNNING"/"NORMAL" is replaced by 
EPChargerState = IntEnum('EPChargerState', [
    'CHARGE_STOP',
    'CHARGE_FLOAT',
    'CHARGE_BOOST',
    'CHARGE_EQUALIZE',
    'STANDBY',
    'FAULT',
    'SHORT_PV',
    'SHORT_LOAD_FET',
    'SHORT_LOAD',
    'OVERCURRENT_LOAD',
    'OVERCURRENT_INPUT',
    'SHORT_ANTIREVERSE',
    'SHORT_CHARGING_OR_ANTIREVERSE',
    'SHORT_CHARGING_FET',
    'INPUT_NOT_CONNECTED',
    'INPUT_OVERVOLT',
    'INPUT_VOLTAGE_ERROR',
    'INVALID_VALUE'
], start=0)


class EPsolarTracerClient:
    ''' EPsolar Tracer client
    '''

    def __init__(self, unit = 1, serialclient = None, **kwargs):
        ''' Initialize a serial client instance
        '''
        self.unit = unit
        if serialclient == None:
            port = kwargs.get('port', '/dev/ttyXRUSB0')
            baudrate = kwargs.get('baudrate', 115200)
            self.client = ModbusClient(method = 'rtu', port = port, baudrate = baudrate, kwargs = kwargs)
        else:
            self.client = serialclient

    def connect(self):
        ''' Connect to the serial
        :returns: True if connection succeeded, False otherwise
        '''
        return self.client.connect()

    def close(self):
        ''' Closes the underlying connection
        '''
        return self.client.close()

    def read_device_info(self):
        request = ReadDeviceInformationRequest (unit = self.unit)
        response = self.client.execute(request)
        return response

    def parse_battery_state(self, state):
        """Returns a list of 1-3 EPChargerState error codes, or [NORMAL] in case there are no errors"""

        output = []

        # hopefully the most common case
        if state == 0:
            output.append(EPBatteryState.NORMAL)
            return output
        # else we have errors, so let's decode the register

        # if the value is larger than the register length
        if state & (~0xFFFF) != 0:
            output.append(EPBatteryState.INVALID_VALUE)

        # bits 0-3
        first_val = state & 0xF
        if first_val == 0:
            # no error code here
            pass
        elif first_val > 4 or first_val < 0:
            # something went wrong
            output.append(EPBatteryState.INVALID_VALUE)
        else:
            output.append(EPBatteryState(first_val))
        # bits 4-7
        second_val = (state >> 4) & 0xF
        if second_val == 0:
            # no error code here
            pass
        elif second_val > 2 or second_val < 0:
            output.append(EPBatteryState.INVALID_VALUE)
        else:
            # + 4 gets us to HOT/COLD in the enum
            output.append(EPBatteryState(second_val + 4))
        # bit 8
        if state & 0x100:
            output.append(EPBatteryState.INTERNAL_RESISTANCE_ABNORMAL)
        # bit 15
        if state & 0x8000:
            output.append(EPBatteryState.RATED_VOLTAGE_WRONG)

        # somehow, no error was detected, but it's also not 0?
        if len(output) == 0:
            output.append(EPBatteryState.INVALID_VALUE)

        return output

    def parse_charger_state(self, state):
        """Returns a list of EPChargerState codes:

        First is always charging state (or INVALID_VALUE); any following EPChargerStates are non-normal states / error codes
        """

        output = []

        # if the value is larger than the register length
        if state & (~0xFFFF) != 0:
            output.append(EPChargerState.INVALID_VALUE)

        # bit 2-3: charging state
        charging_state = (state & (3 << 2)) >> 2
        output.append(EPChargerState(charging_state))
        # bit 0: running/standby
        if state & 1 == 0:
            output.append(EPChargerState.STANDBY)
        # bit 1: general fault
        if state & (1 << 1) != 0:
            output.append(EPChargerState.FAULT)
        # bit 4: pv short
        if state & (1 << 4) != 0:
            output.append(EPChargerState.SHORT_PV)
        # bit 7: load mosfet short - how is this different from load short? internal error?
        if state & (1 << 7) != 0:
            output.append(EPChargerState.SHORT_LOAD_FET)
        # bit 8: load short
        if state & (1 << 8) != 0:
            output.append(EPChargerState.SHORT_LOAD)
        # bit 9: load oc
        if state & (1 << 9) != 0:
            output.append(EPChargerState.OVERCURRENT_LOAD)
        # bit 10: input oc
        if state & (1 << 10) != 0:
            output.append(EPChargerState.OVERCURRENT_INPUT)
        # bit 11: anti-reverse-fet short
        if state & (1 << 11) != 0:
            output.append(EPChargerState.SHORT_ANTIREVERSE)
        # bit 12: anti-reverse-fet short or(?) charging fet short
        # TODO: figure out how this works for our controller, and merge 11-13 with some logic?
        if state & (1 << 12) != 0:
            output.append(EPChargerState.SHORT_CHARGING_OR_ANTIREVERSE)
        # bit 13: charging mostfet short
        if state & (1 << 13) != 0:
            output.append(EPChargerState.SHORT_CHARGING_FET)
        # bit 14-15: input voltage status
        input_voltage_state = (state & (3 << 14)) >> 14
        if input_voltage_state == 0:
            # normal
            pass
        else:
            # map input voltage errors 1-3 to INPUT_NOT_CONNECTED/INPUT_OVERVOLT/INPUT_VOLTAGE_ERROR
            output.append(EPChargerState(EPChargerState.INPUT_NOT_CONNECTED - 1
                                            + input_voltage_state))

        return output

    def read_input(self, name):
        register = registerByName(name)
        if register.is_coil():
            response = self.client.read_coils(address=register.address, count=register.size, slave = self.unit)
        elif register.is_discrete_input():
            response = self.client.read_discrete_inputs(address=register.address, count=register.size, slave = self.unit)
        elif register.is_input_register():
            response = self.client.read_input_registers(address=register.address, count=register.size, slave = self.unit)
        else:
            response = self.client.read_holding_registers(address=register.address, count=register.size, slave = self.unit)
        return register.decode(response)

    def write_output(self, name, value):
        register = registerByName(name)
        values = register.encode(value)
        response = False
        if register.is_coil():
            self.client.write_coil(address=register.address, value=values, slave = self.unit)
            response = True
        elif register.is_discrete_input():
            _logger.error("Cannot write discrete input " + repr(name))
            pass
        elif register.is_input_register():
            _logger.error("Cannot write input register " + repr(name))
            pass
        else:
            self.client.write_registers(address=register.address, value=values, slave = self.unit)
            response = True
        return response

__all__ = [
    "EPsolarTracerClient",
]
