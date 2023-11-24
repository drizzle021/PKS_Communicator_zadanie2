import socket as s
import threading


class Server:
    def __init__(self, ip, port):
        self.socket = s.socket(s.AF_INET, s.SOCK_DGRAM)
        #self.socket.bind((ip,port))
        self.connected = True
        self.data = None

        """t1 = threading.Thread(target=self.listen,daemon=True)
        t1.start()"""

    def listen(self):
        while self.connected:
            self.data = self.socket.recvfrom(1024)
            print(self.data)


