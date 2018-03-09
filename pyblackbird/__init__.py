import asyncio
import functools
import logging
import re
import serial
from functools import wraps
from serial_asyncio import create_serial_connection
from threading import RLock

_LOGGER = logging.getLogger(__name__)
ZONE_PATTERN = re.compile('\D\D\D\s(\d\d)\D\D(\d\d)\s')

EOL = b'\r'
LEN_EOL = len(EOL)
TIMEOUT = 2 # Number of seconds before serial operation timeout

class ZoneStatus(object):
	def __init__(self,
				 av: int,
				 zone: int,):
				 #ir: int):
		self.av = av
		self.zone = zone
		#self.ir = ir

	@classmethod
	def from_string(cls, string: str):
		if not string:
			return None
		match = re.search (ZONE_PATTERN, string)
		if not match:
			return None
		return ZoneStatus(*[int(m) for m in match.groups()])

class Blackbird(object):
	"""
	Monoprice blackbird amplifier interface
	"""

	def zone_status(self, zone: int):
		"""
		Get the structure representing the status of the zone
		:param zone: zone 1..8
		:return: status of the zone or None
		"""
		raise NotImplemented()

# Helpers

def _format_zone_status_request(zone: int) -> bytes:
	return 'Status{}.\r'.format(zone).encode()

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
		def zone_status(self, zone: int):
			# 
			return ZoneStatus.from_string(self._process_request(_format_zone_status_request(zone), skip=6))

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
			self._protocol = monoprice_protocol

		@locked_coro
		@asyncio.coroutine
		def zone_status(self, zone: int):
			# 
			string = yield from self._protocol.send(_format_zone_status_request(zone), skip=6)
			return ZoneStatus.from_string(string)

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