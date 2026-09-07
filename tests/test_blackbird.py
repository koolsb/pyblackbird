import unittest

import serialx
import socket

from pyblackbird import (get_blackbird, get_async_blackbird, ZoneStatus)
from pyblackbird.profiles import BLACKBIRD_4X4, BLACKBIRD_8X8
from tests import (create_dummy_port, create_dummy_socket)
import asyncio


class TestZoneStatus(unittest.TestCase):

    def test_zone_status_broken(self):
        self.assertIsNone(ZoneStatus.from_string(None, None))
        self.assertIsNone(ZoneStatus.from_string(1, 'VA: 09-<01\r'))
        self.assertIsNone(ZoneStatus.from_string(10, '\r\n\r\n'))

    def test_zone_status_no_ir(self):
        # Models without IR routing report only the AV line, terminated with
        # either \r or \r\n.
        for response in ('AV: 02->01\r', 'AV: 02->01\r\n'):
            status = ZoneStatus.from_string(1, response)
            self.assertEqual(1, status.zone)
            self.assertTrue(status.power)
            self.assertEqual(2, status.av)
            self.assertIsNone(status.ir)

        for response in ('AV:OFF->01\r', 'AV:OFF->01\r\n'):
            status = ZoneStatus.from_string(1, response)
            self.assertFalse(status.power)
            self.assertIsNone(status.av)
            self.assertIsNone(status.ir)

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
        with self.assertRaises(ValueError):
            self.blackbird.set_zone_source(1,100)
        with self.assertRaises(ValueError):
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
        with self.assertRaises(serialx.SerialTimeoutException):
           self.blackbird.set_zone_source(6,6)


class TestBlackbirdProfiles(unittest.TestCase):
    """Test profile-specific protocol range validation."""

    def setUp(self):
        self.responses = {}

    def test_4x4_profile_rejects_out_of_range_ids(self):
        blackbird = get_blackbird(
            create_dummy_port(self.responses), profile=BLACKBIRD_4X4
        )

        with self.assertRaises(ValueError):
            blackbird.zone_status(5)
        with self.assertRaises(ValueError):
            blackbird.set_zone_source(1, 5)
        with self.assertRaises(ValueError):
            blackbird.set_all_zone_source(5)

    def test_8x8_profile_accepts_maximum_ids(self):
        blackbird = get_blackbird(
            create_dummy_port(self.responses), profile=BLACKBIRD_8X8
        )
        self.responses[b'Status8.\r'] = b'AV: 08->08\r\nIR: 08->08\r'

        assert blackbird.zone_status(8).zone == 8



class TestBlackbirdNoIr(unittest.TestCase):
    """Model 24180 and friends: no IR routing, and 'V' selects the source."""

    def setUp(self):
        self.responses = {}
        self.blackbird = get_blackbird(
            create_dummy_port(self.responses), ir_control=False
        )

    def test_zone_status(self):
        self.responses[b'Status1.\r'] = b'AV: 02->01\r'
        status = self.blackbird.zone_status(1)
        self.assertEqual(1, status.zone)
        self.assertTrue(status.power)
        self.assertEqual(2, status.av)
        self.assertIsNone(status.ir)
        self.assertEqual(0, len(self.responses))

    def test_zone_status_off(self):
        self.responses[b'Status1.\r'] = b'AV:OFF->01\r'
        status = self.blackbird.zone_status(1)
        self.assertFalse(status.power)
        self.assertEqual(0, len(self.responses))

    def test_set_zone_source_uses_v_command(self):
        # 'B' on IR models, 'V' here.
        self.responses[b'1V1.\r'] = b'AV:01->01\r'
        self.blackbird.set_zone_source(1, 1)
        self.responses[b'2V2.\r'] = b'AV:02->02\r'
        self.blackbird.set_zone_source(2, 2)
        self.assertEqual(0, len(self.responses))

    def test_set_zone_power(self):
        self.responses[b'1@.\r'] = b'01 Open.\r'
        self.blackbird.set_zone_power(1, True)
        self.responses[b'1$.\r'] = b'01 Closed.\r'
        self.blackbird.set_zone_power(1, False)
        self.assertEqual(0, len(self.responses))


class TestAsyncBlackbirdNoIr(unittest.TestCase):
    """The no-IR flag has to reach the async client too."""

    def setUp(self):
        self.responses = {}
        loop = asyncio.new_event_loop()
        self.addCleanup(loop.close)
        blackbird = loop.run_until_complete(
            get_async_blackbird(
                create_dummy_port(self.responses), loop, ir_control=False
            )
        )

        class DummyBlackbird():
            def __getattribute__(self, item):
                def f(*args, **kwargs):
                    return loop.run_until_complete(
                        blackbird.__getattribute__(item)(*args, **kwargs)
                    )
                return f
        self.blackbird = DummyBlackbird()

    def test_zone_status(self):
        self.responses[b'Status1.\r'] = b'AV: 02->01\r'
        status = self.blackbird.zone_status(1)
        self.assertTrue(status.power)
        self.assertEqual(2, status.av)
        self.assertIsNone(status.ir)
        self.assertEqual(0, len(self.responses))

    def test_set_zone_source_uses_v_command(self):
        self.responses[b'1V1.\r'] = b'AV:01->01\r'
        self.blackbird.set_zone_source(1, 1)
        self.assertEqual(0, len(self.responses))


class TestBlackbirdSocket(TestBlackbird):
    """Run the same suite against the TCP transport instead of serial."""

    def setUp(self):
        self.responses = {}
        self.blackbird = get_blackbird(
            create_dummy_socket(self.responses), use_serial=False
        )

    def test_timeout(self):
        # socket.timeout only became an alias of TimeoutError in 3.10.
        with self.assertRaises(socket.timeout):
            self.blackbird.set_zone_source(6, 6)


class TestAsyncBlackbird(TestBlackbird):

    def setUp(self):
        self.responses = {}
        loop = asyncio.new_event_loop()
        self.addCleanup(loop.close)
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
