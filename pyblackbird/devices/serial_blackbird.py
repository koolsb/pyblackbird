import serial

TIMEOUT = 2 # Number of seconds before serial operation timeout

class SerialBlackbird(object):
    """
    Serial interface for Monoprice Blackbird
    """
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