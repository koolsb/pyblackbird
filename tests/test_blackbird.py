import unittest

import serial

from pyblackbird import (get_blackbird, get_async_blackbird, ZoneStatus)
from tests import (create_dummy_port, create_dummy_socket)
import asyncio


class TestZoneStatus(unittest.TestCase):

    def test_zone_status_broken(self):
        self.assertIsNone(ZoneStatus.from_string(None, None))
        self.assertIsNone(ZoneStatus.from_string(1, 'VA: 09-<01\r'))
        self.assertIsNone(ZoneStatus.from_string(10, '\r\n\r\n'))

class TestBlackbird(unittest.TestCase):
    def setUp(self):
        self.responses = {}
        self.blackbird = get_blackbird(create_dummy_port(self.responses))

    def test_zone_status(self):
        self.responses[b'Status1.\r'] = b'AV: 02->01\r\nIR: 02->01\r'
        status = self.blackbird.zone_status(1)
        self.assertEqual(1, status.zone)
        self.assertTrue(status.power)
        self.assertEqual(2, status.av)
        self.assertEqual(2, status.ir)
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

    def test_set_zone_source(self):
        self.responses[b'1B1.\r'] = b'AV:01->01\r'
        self.blackbird.set_zone_source(1,1)
        self.responses[b'8B1.\r'] = b'AV:08->05\r'
        self.blackbird.set_zone_source(1,100)
        self.responses[b'1B1.\r'] = b'AV:01->01\r'
        self.blackbird.set_zone_source(1,-100)
        self.responses[b'2B2.\r'] = b'AV:02->02\r'
        self.blackbird.set_zone_source(2,2)
        self.assertEqual(0, len(self.responses))

    def test_set_all_zone_source(self):
        self.responses[b'1All.\r'] = b'01 To All.\r'
        self.blackbird.set_all_zone_source(1)
        self.assertEqual(0, len(self.responses))

    def test_lock_front_buttons(self):
        self.responses[b'/%Lock;\r'] = b'System Locked!\r'
        self.blackbird.lock_front_buttons()
        self.assertEqual(0, len(self.responses))


    def test_unlock_front_buttons(self):
        self.responses[b'/%Unlock;\r'] = b'System UnLock!\r'
        self.blackbird.unlock_front_buttons()
        self.assertEqual(0, len(self.responses))

    def test_front_button_status(self):
        self.responses[b'%9961.\r'] = b'System Locked!\r'
        status = self.blackbird.lock_status()
        self.assertTrue(status)
        self.responses[b'%9961.\r'] = b'System UnLock!\r'
        status = self.blackbird.lock_status()
        self.assertFalse(status)
        self.assertEqual(0, len(self.responses))

    def test_timeout(self):
        with self.assertRaises(serial.SerialTimeoutException):
           self.blackbird.set_zone_source(6,6)



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
            self.blackbird.set_zone_source(6, 6)

if __name__ == '__main__':
   unittest.main()
