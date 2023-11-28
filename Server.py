import socket as s
import threading
import time
from HeaderFormat import formatHeader, Flag


class Server:
    def __init__(self, ip, port):
        print("Entering Receiver mode")
        self.socket = s.socket(s.AF_INET, s.SOCK_DGRAM)
        # self.socket.bind((ip,port))
        self.socket.bind((ip, port))
        self.connected = False
        self.data = None
        self.client = None
        self.clientAlive = False

        self.messageQueue = []

        self.status = 0

    def listen(self):
        while self.connected:
            try:
                self.data, address = self.socket.recvfrom(65000)

                parts = self.data.hex(" ")

                if self.data.hex(" ").split(" ")[0] == "66":
                    self.receiveFile(self.data.hex(" ").split(" ")[1:])

                elif self.data.decode() == "switch":
                    self.switch()

                if self.data.decode() != "alive" or "alive" not in self.messageQueue:
                    self.messageQueue.append(self.data.decode())
                if parts[0] == bytes(Flag.MESSAGE.value).hex(" "):
                    print(self.data.decode())
            except Exception as e:
                print(e)
                print("error")

    def sendMessage(self, message):
        self.socket.sendto(message.encode(), self.client)

    def receiveFile(self, file):
        file = bytes.fromhex(" ".join(file))
        filename = "test.jpg"
        with open(f"{filename}", mode="wb") as f:
            f.write(file)

        self.messageQueue.remove("test/abc.txt")

    def checkAlive(self):
        timeout = 15
        while self.connected:
            #print(self.messageQueue)
            if "alive" in self.messageQueue:
                self.messageQueue = [message for message in self.messageQueue if message != "alive"]
                self.sendMessage("ack")
                timeout = 15
            elif timeout == 0:
                self.connected = False
            else:
                timeout -= 5
            time.sleep(5)

    def switch(self):
        self.status = 45
        self.connected = False

    def start(self):
        while not self.connected:
            try:
                self.data, self.client = self.socket.recvfrom(1024)
                if self.data.decode() == "init":
                    self.sendMessage("ack")
                    self.connected = True
                    self.clientAlive = True
                    self.status = 1
            except Exception as e:
                print(e)

        tCheckAlive = threading.Thread(target=self.checkAlive, daemon=True)
        tCheckAlive.start()

        tListening = threading.Thread(target=self.listen, daemon=True)
        tListening.start()

        while self.connected:
            pass

        return self.status