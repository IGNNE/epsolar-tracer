#!/usr/bin/env python3

# modified info.py for logging data

from pyepsolartracer.client import EPsolarTracerClient
from pyepsolartracer.registers import registers,coils
from pymodbus.client import ModbusSerialClient as ModbusClient
import serial.rs485

# configure the client logging
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)
#log.setLevel(logging.DEBUG)

# choose the serial client, use the proper serial port
serialclient = ModbusClient(method='rtu', port='/dev/ttyXRUSB0', baudrate=115200, stopbits = 1, bytesize = 8, timeout=1)
serialclient.connect()
try:
    serialclient.socket.rs485_mode = serial.rs485.RS485Settings()
except:
    pass

client = EPsolarTracerClient(serialclient = serialclient)


# this crashes on the boat charger
#response = client.read_device_info()
#print("Manufacturer:", repr(response.information[0]))
#print("Model:", repr(response.information[1]))
#print("Version:", repr(response.information[2]))

# for logging, only interested in registers
for reg in registers:
    value = client.read_input(reg.name)
    print(value)
    # and only the read-registers
    #if value.value is not None:
    #    print(client.write_output(reg.name,value.value))

# no coils ("switches") either
#for reg in coils:
    #print()
    #print(reg)
    #value = client.read_input(reg.name)
    #print(value)
    #print(client.write_output(reg.name,value.value))

client.close()
