import asyncio
import functools
import logging
import re
import serial
from functools import wraps
from serial_asyncio import create_serial_connection
from threading import RLock

_LOGGER = logging.getLogger(__name__)
ZONE_PATTERN_ON = re.compile('\D\D\D\s(\d\d)\D\D(\d\d)\s\s\D\D\D\s(\d\d)\D\D\d\d\s')
ZONE_PATTERN_OFF = re.compile('\D\D\DOFF\D\D(\d\d)\s\s\D\D\D\D\D\D\D\D\d\d\s')
EOL = b'\r'
LEN_EOL = len(EOL)
TIMEOUT = 2 # Number of seconds before serial operation timeout

class ZoneStatus(object):
	def __init__(self,
				 power: bool,
				 av: int,
				 zone: int,
				 ir: int):
		self.power = power
		self.av = av
		self.zone = zone
		self.ir = ir

	@classmethod
	def from_string(cls, string: str):
		if not string:
			return None
		match_on = re.search (ZONE_PATTERN_ON, string)
		if not match_on:
			match_off = re.search (ZONE_PATTERN_OFF, string)
			if not match_off:
				return None
			return ZoneStatus(0,0,*[int(m) for m in match_off.groups()],0)
		return ZoneStatus(1,*[int(m) for m in match_on.groups()])

	@classmethod
	def power_off(cls, zone: int):
		return ZoneStatus(0,zone,0)

class Blackbird(object):
	"""
	Monoprice blackbird amplifier interface
	"""

	def system_power_status(self):
		"""
		Get the system power status
		:return: status of the system power
		"""
		raise NotImplemented()

	def zone_status(self, zone: int):
		"""
		Get the structure representing the status of the zone
		:param zone: zone 1..8
		:return: status of the zone or None
		"""
		raise NotImplemented()

	def set_system_power(self, power: int):
		"""
		Turn the system on, off, or to standby
		:param power: 1=on, 0=off, 3=standby
		"""
		raise NotImplemented()

	def set_zone_power(self, zone: int, power: bool):
		"""
		Turn zone on or off
		:param zone: Zone 1-8
		:param power: True to turn on, False to turn off
		"""
		raise NotImplemented()

	def set_source(self, zone: int, source: int):
		"""
		Set source for zone
		:param zone: Zone 1-8
		:param source: integer from 1-8
		"""
		raise NotImplemented()

# Helpers

def _format_zone_status_request(zone: int) -> bytes:
	return 'Status{}.\r'.format(zone).encode()

def _format_system_power_status_request() -> bytes:
	return '%9962.\r'.encode()

def _format_set_system_power(power: int) -> bytes:
	if power == 1:
		return 'PWON.\r'.encode()
	elif power == 0:
		return 'PWOFF.\r'.encode()
	elif power == 2:
		return 'STANDBY.\r'.encode()
	else:
		return None

def _format_set_zone_power(zone: int, power: bool) -> bytes:
	return '{}{}.\r'.format(zone, '@' if power else '$').encode()

def _format_set_source(zone: int, source: int) -> bytes:
	source = int(max(1, min(source,8)))
	return '{}B{}.\r'.format(source, zone).encode()



def get_blackbird(port_url):
	"""
	Return synchronous version of Blackbird interface
	:param port_url: serial port, i.e. '/dev/ttyUSB0'
	:return: synchronous implementation of Blackbird interface
	"""
	lock = RLock()

	def synchronized(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			with lock:
				return func(*args, **kwargs)
		return wrapper

	class BlackbirdSync(Blackbird):
		def __init__(self, port_url):
			self._port = serial.serial_for_url(port_url, do_not_open=True)
			self._port.baudrate = 9600
			self._port.stopbits = serial.STOPBITS_ONE
			self._port.bytesize = serial.EIGHTBITS
			self._port.parity = serial.PARITY_NONE
			self._port.timeout = TIMEOUT
			self._port.write_timeout = TIMEOUT
			self._port.open()

		def _process_request(self, request: bytes, skip=0):
			"""
			:param request: request that is sent to the blackbird
			:param skip: number of bytes to skip for end of transmission decoding
			:return: ascii string returned by blackbird
			"""
			_LOGGER.debug('Sending "%s"', request)
			# clear
			self._port.reset_output_buffer()
			self._port.reset_input_buffer()
			# send
			self._port.write(request)
			self._port.flush()
			# receive
			result = bytearray()
			while True:
				c = self._port.read(1)
				if c is None:
					break
				if not c:
					raise serial.SerialTimeoutException(
						'Connection timed out! Last received bytes {}'.format([hex(a) for a in result]))
				result += c
				if len(result) > skip and result [-LEN_EOL:] == EOL:
					break
			ret = bytes(result)
			_LOGGER.debug('Received "%s"', ret)
			return ret.decode('ascii')

		@synchronized
		def system_power_status(self):
			status = self._process_request(_format_system_power_status_request(), skip=5)
			if status.startswith('PW'):
				status = status[2:].rstrip()
			return status.rstrip()

		@synchronized
		def zone_status(self, zone: int):
			# First check if system power is on
			if "ON" in self.system_power_status():
				return ZoneStatus.from_string(self._process_request(_format_zone_status_request(zone), skip=20))
			else:
				return ZoneStatus.power_off(zone)

		@synchronized
		def set_system_power(self, power: int):
			# 0 = off, 1 = on, 2 = standby
			self._process_request(_format_set_system_power(power))

		@synchronized
		def set_zone_power(self, zone: int, power: bool):
			self._process_request(_format_set_zone_power(zone, power))

		@synchronized
		def set_source(self, zone: int, source: int):
			self._process_request(_format_set_source(zone, source))

	return BlackbirdSync(port_url)


@asyncio.coroutine
def get_async_blackbird(port_url, loop):
	"""
	Return asynchronous version of Blackbird interface
	:param port_url: serial port, i.e. '/dev/ttyUSB0'
	:return: asynchronous implementation of Blackbird interface
	"""

	lock = asyncio.Lock()

	def locked_coro(coro):
		@asyncio.coroutine
		@wraps(coro)
		def wrapper(*args, **kwargs):
			with (yield from lock):
				return (yield from coro(*args, **kwargs))
		return wrapper

	class BlackbirdAsync(Blackbird):
		def __init__(self, blackbird_protocol):
			self._protocol = blackbird_protocol

		@locked_coro
		@asyncio.coroutine
		def system_power_status(self):
			status = yield from self._protocol.send(_format_system_power_status_request(), skip=5)
			if status.startswith('PW'):
				status = status[2:]
			return status

		@locked_coro
		@asyncio.coroutine
		def zone_status(self, zone: int):
			# 
			string = yield from self._protocol.send(_format_zone_status_request(zone), skip=20)
			return ZoneStatus.from_string(string)

		@locked_coro
		@asyncio.coroutine
		def set_system_power(self, power: int):
			yield from self._protocol.send(_format_set_system_power(power))

		@locked_coro
		@asyncio.coroutine
		def set_zone_power(self, zone: int, power: bool):
			yield from self._protocol.send(_format_set_zone_power(zone, power))

		@locked_coro
		@asyncio.coroutine
		def set_source(self, zone: int, source: int):
			yield from self._protocol.send(_formst_set_source(zone, source))

	class BlackbirdProtocol(asyncio.Protocol):
		def __init__(self, loop):
			super().__init__()
			self._loop = loop
			self._lock = asyncio.Lock()
			self._transport = None
			self._connected = asyncio.Event(loop=loop)
			self.q = asyncio.Queue(loop=loop)

		def connection_made(self, transport):
			self._transport = transport
			self._connected.set()
			_LOGGER.debug('port opened %s', self._transport)

		def data_received(self, data):
			asyncio.ensure_future(self.q.put(data), loop=self._loop)

		@asyncio.coroutine
		def send(self, request: bytes, skip=0):
			yield from self._connected.wait()
			result = bytearray()
			# Only one transaction at a time
			with (yield from self._lock):
				self._transport.serial.reset_output_buffer()
				self._transport.serial.reset_input_buffer()
				while not self.q.empty():
					self.q.get_nowait()
				self._transport.write(request)
				try:
					while True:
						result += yield from asyncio.wait_for(self.q.get(), TIMEOUT, loop=self._loop)
						if len(result) > skip and result[-LEN_EOL:] == EOL:
							ret = bytes(result)
							_LOGGER.debug('Received "%s"', ret)
							return ret.decode('ascii')
				except asyncio.TimeoutError:
					_LOGGER.error("Timeout during receiving response for command '%s', received='%s'", request, result)
					raise

	_, protocol = yield from create_serial_connection(loop, functools.partial(BlackbirdProtocol, loop), port_url, baudrate=9600)

	return BlackbirdAsync(protocol)