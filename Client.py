import random
import socket as s
import threading
import time
from HeaderFormat import formatHeader, Flag
from Message import Message
from crc import Calculator, Crc16


def analyseMessage(message):
    messageParts = message.hex(" ").split()
    flag = messageParts[0]
    data = None
    seq = None
    if flag == Flag.FILE.value.to_bytes(1, byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)
        data = messageParts[3:]
    elif flag == Flag.MESSAGE.value.to_bytes(1, byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)
        data = messageParts[3:]
    elif flag == Flag.NACK.value.to_bytes(1, byteorder="big").hex() or flag == Flag.ACK.value.to_bytes(1, byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)

    return Message(flag,data,seq)


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
        self.calculator = Calculator(Crc16.CCITT,optimized=True)

    def sending(self):
        while self.connected:
            inp = input(": ")
            if inp.strip() == "":
                continue
            parts = inp.split(" ")
            if parts[-1] == "-file" or parts[-1] == "-f":
                #print(" ".join(parts[:-1]))
                self.sendFile(" ".join(parts[:-1]))

            elif parts[-1] == "-error" or parts[-1] == "-e":
                self.faultySend()

            elif inp.strip() == "/switch" or inp.strip() == "/s":
                self.switch()

            elif inp.strip() == "/quit" or inp.strip() == "/q":
                self.quit()

            else:
                self.sendMessage(" ".join(parts))

    def lookup(self,flag):
        return [message for message in self.messageQueue if message.flag == flag.to_bytes(1, byteorder="big").hex()]

    def sendMessage(self, message):
        expected = self.calculator.checksum(message.encode())
        print(expected)
        self.socket.sendto(formatHeader(Flag.MESSAGE.value, random.randint(0, 32768), message,crc=expected), (self.serverIP, self.serverPort))

    def sendFile(self, filename):
        try:
            with open(f"{filename}", mode="rb") as f:
                data = f.read()

            #print(((b"f"+data).hex(" ").upper()))
            filename = filename.split("/")[-1]
            self.socket.sendto(formatHeader(Flag.FILE.value, random.randint(0, 32768), data, filename), (self.serverIP, self.serverPort))
        except FileNotFoundError:
            print("<ERROR> File not found")
            print("<ERROR> Check the path and try again")

    def faultySend(self):
        print("send with error")

    def listen(self):
        while True:
            try:
                self.data, address = self.socket.recvfrom(1024)
                message = analyseMessage(self.data)

                self.messageQueue.append(message)
            except Exception as e:
                print(e)

    def keepAlive(self):
        while self.connected:
            self.socket.sendto(formatHeader(Flag.K_ALIVE.value), (self.serverIP, self.serverPort))
            time.sleep(5)


    # TODO wait for ACK for switch?
    def switch(self):
        self.socket.sendto(formatHeader(Flag.SWITCH.value), (self.serverIP, self.serverPort))
        self.status = 45
        time.sleep(2)
        self.connected = False

    def sendInit(self):
        self.socket.sendto(formatHeader(Flag.CONNECT.value), (self.serverIP, self.serverPort))


    def start(self):
        tListening = threading.Thread(target=self.listen, daemon=True)
        tListening.start()

        while not self.connected:
            try:
                self.sendInit()
                time.sleep(2)
                if len(self.lookup(Flag.CONNECT.value)) > 0:
                    self.connected = True
                    self.messageQueue = []

            except Exception as e:
                print(e)


        tKeepAlive = threading.Thread(target=self.keepAlive, daemon=True)
        tKeepAlive.start()

        tSending = threading.Thread(target=self.sending, daemon=True)
        tSending.start()

        while self.connected:
            pass


        return self.status

    def quit(self):
        self.status = 1
        self.connected = False


