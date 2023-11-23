import socket as s
import threading
import time

class Client:
    def __init__(self, server: tuple):
        self.socket = s.socket(s.AF_INET, s.SOCK_DGRAM)
        self.serverIP, self.serverPort = server
        self.fragmentSize = 512
        self.connected = False
        self.data = None
        """t1 = threading.Thread(target=self.listen)
        t1.start()
        while not connected:
            self.sendMessage("init")
            if self.data == "ack":
                self.connected = True"""
        self.connected = True
        tKeepAlive = threading.Thread(target=self.keepAlive,daemon=True)
        tKeepAlive.start()



    def sendMessage(self, message):
        self.socket.sendto(bytes(message),(self.serverIP,self.serverPort))

    def listen(self):
        self.data = self.socket.recvfrom(1024)
        time.sleep(0.5)

    def keepAlive(self):
        while self.connected:
            print("alive")
            # self.socket.sendto(bytes("alive"),(self.serverIP,self.serverPort))
            print(threading.enumerate())
            time.sleep(5)

