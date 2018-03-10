import unittest

import serial

from pyblackbird import (get_blackbird, get_async_blackbird, ZoneStatus)
from tests import create_dummy_port
import asyncio


class TestZoneStatus(unittest.TestCase):

	def test_zone_status_broken(self):
		self.assertIsNone(ZoneStatus.from_string(None))
		self.assertIsNone(ZoneStatus.from_string('VA: 09-<01\r'))
		self.assertIsNone(ZoneStatus.from_string('\r\n\r\n'))

class TestBlackbird(unittest.TestCase):
	def setUp(self):
		self.responses = {}
		self.blackbird = get_blackbird(create_dummy_port(self.responses))

	def test_system_power_status(self):
		self.responses[b'%9962.\r'] = b'PWON \r'
		status = self.blackbird.system_power_status()
		self.assertEqual(0, len(self.responses))

	def test_zone_status(self):
		self.responses[b'Status1.\r'] = b'AV: 02->01\r\nIR: 02->01\r'
		self.responses[b'%9962.\r'] = b'PWON \r'
		status = self.blackbird.zone_status(1)
		self.assertEqual(1, status.zone)
		self.assertTrue(status.power)
		self.assertEqual(2, status.av)
		self.assertEqual(2, status.ir)

	def test_set_system_power(self):
		self.responses[b'PWON.\r'] = b'PWON\r'
		self.blackbird.set_system_power(1)
		self.responses[b'PWOFF.\r'] = b'PWOFF\r'
		self.blackbird.set_system_power(0)
		self.responses[b'STANDBY.\r'] = b'STANDBY\r'
		self.blackbird.set_system_power(2)
		self.responses[b'\r'] = b'\r'
		self.blackbird.set_system_power(3)
		self.assertEqual(0, len(self.responses))

	def test_set_zone_power(self):
		self.responses[b'1@.\r'] = b'01 Open.\r'
		self.blackbird.set_zone_power(1, True)
		self.responses[b'1@.\r'] = b'01 Open.\r'
		self.blackbird.set_zone_power(1, 'True')
		self.responses[b'1@.\r'] = b'01 Open.\r'
		self.blackbird.set_zone_power(1, 1)
		self.responses[b'1$.\r'] = b'01 Closed.\r'
		self.blackbird.set_zone_power(1, False)
		self.responses[b'1$.\r'] = b'01 Closed.\r'
		self.blackbird.set_zone_power(1, None)
		self.responses[b'1$.\r'] = b'01 Closed.\r'
		self.blackbird.set_zone_power(1, 0)
		self.responses[b'1$.\r'] = b'01 Closed.\r'
		self.blackbird.set_zone_power(1, '')
		self.assertEqual(0, len(self.responses))

	def test_set_source(self):
		self.responses[b'1B1.\r'] = b'AV:01->01\r'
		self.blackbird.set_source(1,1)
		self.responses[b'8B1.\r'] = b'AV:08->05\r'
		self.blackbird.set_source(1,100)
		self.responses[b'1B1.\r'] = b'AV:01->01\r'
		self.blackbird.set_source(1,-100)
		self.responses[b'2B2.\r'] = b'AV:02->02\r'
		self.blackbird.set_source(2,2)
		self.assertEqual(0, len(self.responses))

	def test_timeout(self):
		with self.assertRaises(serial.SerialTimeoutException):
			self.blackbird.set_source(6,6)



class TestAsyncBlackbird(TestBlackbird):

    def setUp(self):
        self.responses = {}
        loop = asyncio.get_event_loop()
        blackbird = loop.run_until_complete(get_async_blackbird(create_dummy_port(self.responses), loop))

        # Dummy blackbird that converts async to sync
        class DummyBlackbird():
            def __getattribute__(self, item):
                def f(*args, **kwargs):
                    return loop.run_until_complete(blackbird.__getattribute__(item)(*args, **kwargs))
                return f
        self.blackbird = DummyBlackbird()

    def test_timeout(self):
        with self.assertRaises(asyncio.TimeoutError):
            self.blackbird.set_source(6, 6)

if __name__ == '__main__':
	unittest.main()