import unittest

from pyepsolartracer.client import EPsolarTracerClient, EPChargerState


class TestChargerParsing(unittest.TestCase):

    def setUp(self):
        # default will create a modbus element, but not attempt to connect => all good
        self.epsolar_client = EPsolarTracerClient()

    def test_parse_charger_state_charging_modes(self):
        # 0x1 for running, bits 2-3 for charging mode
        # normal operation mode, let's test the charge mode bits

        ret = self.epsolar_client.parse_charger_state(0x1)
        self.assertListEqual([EPChargerState.CHARGE_STOP], ret)

        ret = self.epsolar_client.parse_charger_state(0x1 | (0x1 << 2))
        self.assertListEqual([EPChargerState.CHARGE_FLOAT], ret)

        ret = self.epsolar_client.parse_charger_state(0x1 | (0x2 << 2))
        self.assertListEqual([EPChargerState.CHARGE_BOOST], ret)

        ret = self.epsolar_client.parse_charger_state(0x1 | (0x3 << 2))
        self.assertListEqual([EPChargerState.CHARGE_EQUALIZE], ret)

    def test_parse_charger_state_one_flag(self):
        # test the most important one-error-flag cases
        # (charge state is always parsed, too)

        ret = self.epsolar_client.parse_charger_state(0x0)
        self.assertListEqual([EPChargerState.CHARGE_STOP, EPChargerState.STANDBY], ret)

        ret = self.epsolar_client.parse_charger_state(0x1 | (0x1 << 1))
        self.assertListEqual([EPChargerState.CHARGE_STOP, EPChargerState.FAULT], ret)

        ret = self.epsolar_client.parse_charger_state(0x1 | (0x1 << 4))
        self.assertListEqual([EPChargerState.CHARGE_STOP, EPChargerState.SHORT_PV], ret)

        ret = self.epsolar_client.parse_charger_state(0x1 | 0x1 << 8)
        self.assertListEqual([EPChargerState.CHARGE_STOP, EPChargerState.SHORT_LOAD], ret)

        ret = self.epsolar_client.parse_charger_state(0x1 | 0x1 << 9)
        self.assertListEqual([EPChargerState.CHARGE_STOP, EPChargerState.OVERCURRENT_LOAD], ret)

        ret = self.epsolar_client.parse_charger_state(0x1 | 0x1 << 10)
        self.assertListEqual([EPChargerState.CHARGE_STOP, EPChargerState.OVERCURRENT_INPUT], ret)

        ret = self.epsolar_client.parse_charger_state(0x1 | 0x1 << 14)
        self.assertListEqual([EPChargerState.CHARGE_STOP, EPChargerState.INPUT_NOT_CONNECTED], ret)

        ret = self.epsolar_client.parse_charger_state(0x1 | 0x2 << 14)
        self.assertListEqual([EPChargerState.CHARGE_STOP, EPChargerState.INPUT_OVERVOLT], ret)

        ret = self.epsolar_client.parse_charger_state(0x1 | 0x3 << 14)
        self.assertListEqual([EPChargerState.CHARGE_STOP, EPChargerState.INPUT_VOLTAGE_ERROR], ret)

    def test_parse_charger_state_multiple_flags(self):
        # see if it works with pretty much all errors at once
        # (even though it might not make sense)

        # I have no idea how the charging/anti-reverse thingy is supposed to behave, so I'm
        # not touching it - I might have to change it later, or maybe it isn't even 
        # implemented in our controller..

        a_lot_of_errors = (0x1 << 1) | (0x1 << 2) | (0x1 << 4) | (0x1 << 7) | (0x1 << 8)
        a_lot_of_errors |= (0x1 << 9) | (0x1 << 10) | (0x3 << 14)
        expected_list = [
            EPChargerState.CHARGE_FLOAT,
            EPChargerState.STANDBY,
            EPChargerState.FAULT,
            EPChargerState.SHORT_PV,
            EPChargerState.SHORT_LOAD_FET,
            EPChargerState.SHORT_LOAD,
            EPChargerState.OVERCURRENT_LOAD,
            EPChargerState.OVERCURRENT_INPUT,
            EPChargerState.INPUT_VOLTAGE_ERROR,
        ]
        ret = self.epsolar_client.parse_charger_state(a_lot_of_errors)
        self.assertListEqual(expected_list, ret)

    def test_parse_charger_state_invalid_state(self):
        ret = self.epsolar_client.parse_charger_state(0xFFFFFFFF)
        self.assertIn(EPChargerState.INVALID_VALUE, ret)



if __name__ == '__main__':
    unittest.main()