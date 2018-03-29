import threading
import os
import pty
import socket


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

def create_dummy_socket(responses):
    HOST = '127.0.0.1'
    PORT = 4001

    

    def listener():

        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.bind((HOST, PORT))
        conn.listen(10)

        while 1:
            conn, addr = s.accept()
        
        conn.send('Please Input Your Command :\r')

        while True:
            # Receive data
            res = conn.recv(1024)
            print("command: %s" % res)

            # write back the response
            if res in responses:
                resp = responses[res]
                del responses[res]
                conn.sendall(resp)

            if not res:
                break

    #while 1:
        
    #    start_new_thread(listener ,(conn,))

    thread = threading.Thread(target=listener, daemon=True)
    thread.start()

    return HOST