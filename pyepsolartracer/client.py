# -*- coding: iso-8859-15 -*-

# import the server implementation
from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.mei_message import *
from pyepsolartracer.registers import registerByName

from enum import Enum

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger(__name__)

# Battery state as reported by the charger, to make things a bit more readable
EPBatteryState = Enum('EpBatteryState', [
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
])

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
        """Returns a list of 1-3 EpBatteryState error codes, or [NORMAL] in case there are no errors"""
        output = []

        # hopefully the most common case
        if state == 0:
            output.append(EPBatteryState.NORMAL)
            return output
        # else we have errors, so let's decode the register

        # bits 0-3
        first_val = state & 0xF
        if first_val == 0:
            # no error code here
            pass
        elif first_val > 4 or first_val < 0:
            # something went wrong
            output.append(EPBatteryState.INVALID_VALUE)
        else:
            output.append(EPBatteryState[first_val])

        # bits 4-7
        second_val = (state >> 4) & 0xF
        if second_val == 0:
            # no error code here
            pass
        elif second_val > 2 or second_val < 0:
            output.append(EPBatteryState.INVALID_VALUE)
        else:
            # + 4 gets us to HOT/COLD in the enum
            output.append(EPBatteryState[second_val + 4])

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
