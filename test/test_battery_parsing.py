import unittest

from pyepsolartracer.client import EPsolarTracerClient, EPBatteryState


class TestBatteryParsing(unittest.TestCase):
    """Test for the parse_battery_state function"""

    def setUp(self):
        # default will create a modbus element, but not attempt to connect => all good
        self.epsolar_client = EPsolarTracerClient()

    def test_parse_battery_state_normal(self):
        ret = self.epsolar_client.parse_battery_state(0x0)
        self.assertListEqual([EPBatteryState.NORMAL], ret)

    def test_parse_battery_state_one_flag(self):
        # test some random one-error-flag cases
        ret = self.epsolar_client.parse_battery_state(0x1)
        self.assertListEqual([EPBatteryState.OVERVOLT], ret)
        ret = self.epsolar_client.parse_battery_state(0x4)
        self.assertListEqual([EPBatteryState.OTHER_FAULT], ret)
        ret = self.epsolar_client.parse_battery_state(0x1 << 5)
        self.assertListEqual([EPBatteryState.COLD], ret)
        ret = self.epsolar_client.parse_battery_state(0x1 << 8)
        self.assertListEqual([EPBatteryState.INTERNAL_RESISTANCE_ABNORMAL], ret)
        ret = self.epsolar_client.parse_battery_state(0x1 << 15)
        self.assertListEqual([EPBatteryState.RATED_VOLTAGE_WRONG], ret)

    def test_parse_battery_state_multiple_flags(self):
        # see if it works with pretty much all errors at once
        # (which is admittedly a rare case)
        a_lot_of_errors = 0x3 | (0x1 << 4) | (0x1 << 8) | (0x1 << 15)
        expected_list = [
            EPBatteryState.UNDERVOLT_DISCONNECT,
            EPBatteryState.HOT,
            EPBatteryState.INTERNAL_RESISTANCE_ABNORMAL,
            EPBatteryState.RATED_VOLTAGE_WRONG
        ]
        ret = self.epsolar_client.parse_battery_state(a_lot_of_errors)
        self.assertListEqual(expected_list, ret)

    def test_parse_battery_state_invalid_state(self):
        ret = self.epsolar_client.parse_battery_state(0xFFFFFFFF)
        self.assertIn(EPBatteryState.INVALID_VALUE, ret)




if __name__ == '__main__':
    unittest.main()