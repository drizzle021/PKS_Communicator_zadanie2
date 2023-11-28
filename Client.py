import random
import socket as s
import threading
import time
from HeaderFormat import formatHeader, Flag

class Client:
    def __init__(self, server: tuple):
        print("Entering Sender mode")
        self.socket = s.socket(s.AF_INET, s.SOCK_DGRAM)
        port = random.randint(5000, 8000)
        self.socket.bind(("localhost", port))

        self.serverIP, self.serverPort = server
        self.fragmentSize = 512
        self.messageQueue = []
        self.connected = False
        self.data = None
        self.status = 0
    def sending(self):
        while self.connected:
            inp = input(": ")
            parts = inp.split(" ")
            if parts[-1] == "-file" or parts[-1] == "-f":
                print(" ".join(parts[:-1]))
                self.sendFile(" ".join(parts[:-1]))

            elif inp == "/switch" or inp == "/s":
                self.switch()

            else:
                self.sendMessage(" ".join(parts))

    def sendMessage(self, message):
        self.socket.sendto(formatHeader(Flag.MESSAGE.value, random.randint(0, 32768), message), (self.serverIP, self.serverPort))

    def sendFile(self, filename):
        with open(f"{filename}", mode="rb") as f:
            data = f.read()

        print(((b"f"+data).hex(" ").upper()))
        self.socket.sendto(b"f"+data, (self.serverIP, self.serverPort))
    def listen(self):
        while True:
            try:
                self.data, address = self.socket.recvfrom(1024)
                self.messageQueue.append(self.data.decode())
            except Exception as e:
                print(e)

    def keepAlive(self):
        while self.connected:
            self.sendMessage("alive")
            time.sleep(5)


    # TODO wait for ACK for switch
    def switch(self):
        self.socket.sendto("switch".encode(), (self.serverIP, self.serverPort))
        self.status = 45
        time.sleep(1.5)
        self.connected = False

    def start(self):
        tListening = threading.Thread(target=self.listen, daemon=True)
        tListening.start()

        while not self.connected:
            try:
                self.sendMessage("init")
                time.sleep(2)
                if "ack" in self.messageQueue:
                    self.connected = True

            except Exception as e:
                print(e)

        tKeepAlive = threading.Thread(target=self.keepAlive, daemon=True)
        tKeepAlive.start()

        tSending = threading.Thread(target=self.sending, daemon=True)
        tSending.start()

        while self.connected:
            pass

        return self.status

