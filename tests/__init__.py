import os
import pty
import socket
import threading

# Must match pyblackbird.PORT, which the library hardcodes for TCP connections.
DUMMY_SOCKET_HOST = '127.0.0.1'
DUMMY_SOCKET_PORT = 4001

# The matrix greets a TCP client before accepting commands; BlackbirdSync
# consumes this in its constructor.
GREETING = b'Please Input Your Command :\r'


def _serve(conn, responses):
    """Answer commands on an open connection until the peer goes away."""
    buffer = b''
    while True:
        data = conn.recv(1024)
        if not data:
            return
        buffer += data
        # Commands are \r-terminated and may arrive coalesced or split.
        while b'\r' in buffer:
            command, _, buffer = buffer.partition(b'\r')
            command += b'\r'
            print("command: %s" % command)
            if command in responses:
                conn.sendall(responses.pop(command))


def create_dummy_port(responses):
    def listener(port):
        # continuously listen to commands on the master device
        while 1:
            res = b''
            while not res.endswith(b"\r"):
                # keep reading one byte at a time until we have a full line
                res += os.read(port, 1)
            print("command: %s" % res)

            # write back the response
            if res in responses:
                resp = responses[res]
                del responses[res]
                os.write(port, resp)

    master, slave = pty.openpty()
    thread = threading.Thread(target=listener, args=[master], daemon=True)
    thread.start()
    return os.ttyname(slave)


# The library hardcodes the TCP port, so every test shares one server. Tests
# swap in their own response table; the server reads it at request time.
_socket_server = {'started': False, 'responses': {}}


def create_dummy_socket(responses):
    """Serve the Blackbird TCP protocol on a local socket.

    Returns the host to hand to get_blackbird(..., use_serial=False).
    """
    _socket_server['responses'] = responses

    if _socket_server['started']:
        return DUMMY_SOCKET_HOST

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((DUMMY_SOCKET_HOST, DUMMY_SOCKET_PORT))
    server.listen(5)

    def handle(conn):
        with conn:
            conn.sendall(GREETING)
            try:
                _serve(conn, _socket_server['responses'])
            except OSError:
                pass

    def listener():
        while True:
            conn, _ = server.accept()
            # BlackbirdSync never closes its socket, so earlier connections
            # stay open; serve each one independently.
            threading.Thread(target=handle, args=[conn], daemon=True).start()

    threading.Thread(target=listener, daemon=True).start()
    _socket_server['started'] = True
    return DUMMY_SOCKET_HOST
