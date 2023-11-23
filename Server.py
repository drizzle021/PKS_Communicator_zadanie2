import socket as s

class Server:
    def __init__(self, ip, port):
        self.socket = s.socket(s.AF_INET, s.SOCK_DGRAM)
        self.socket.bind((ip,port))

    