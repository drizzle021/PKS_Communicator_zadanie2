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
    crc = None
    if flag == Flag.FILE.value.to_bytes(1, byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)
        data = messageParts[3:]
    elif flag == Flag.MESSAGE.value.to_bytes(1, byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)
        crc = int("".join(messageParts[-2:]), 16)
        data = messageParts[3:-2]
    elif flag == Flag.NACK.value.to_bytes(1, byteorder="big").hex() or flag == Flag.ACK.value.to_bytes(1, byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)

    return Message(flag,data,seq,crc)


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
        self.calculator = Calculator(Crc16.CCITT,optimized=True)

        self.messageQueue = []

        self.status = 0

    def listen(self):
        while self.connected:
            try:
                self.data, address = self.socket.recvfrom(65000)

                message = analyseMessage(self.data)
                # TODO if verified send ACK and output else send NACK
                if message.flag == Flag.MESSAGE.value.to_bytes(1,byteorder="big").hex():
                    verification = self.calculator.verify(bytes.fromhex(' '.join(message.data)),message.crc)
                    print(verification)
                    print()
                    print(f"{address}: {bytes.fromhex(' '.join(message.data)).decode()}")

                elif message.flag == Flag.SWITCH.value.to_bytes(1,byteorder="big").hex():
                    self.switch()

                elif message.flag == Flag.FILE.value.to_bytes(1,byteorder="big").hex():
                    self.receiveFile(message,address)

                if message.flag != Flag.K_ALIVE.value.to_bytes(1,byteorder="big").hex() or len(self.lookup(Flag.K_ALIVE.value)) < 1:
                    self.messageQueue.append(message)
            except Exception as e:
                print(e)
                print("error")

    def sendMessage(self, message):
        self.socket.sendto(message.encode(), self.client)

    def receiveFile(self, file, address):
        separatorIndex = file.data.index("00")
        filename = file.data[:separatorIndex]
        filename = bytes.fromhex(" ".join(filename))

        filename = filename.decode()
        file = file.data[separatorIndex+1:]
        file = bytes.fromhex(" ".join(file))

        print(f"{address}\nFile Received: {filename}")

        with open(f"{filename}", mode="wb") as f:
            f.write(file)
        #self.messageQueue.remove(file)

    def checkAlive(self):
        timeout = 15
        while self.connected:
            #print(self.messageQueue)
            #print(len(self.lookup(Flag.K_ALIVE.value)))
            if len(self.lookup(Flag.K_ALIVE.value)) > 0 :
                #print("<INFO> ALIVE")
                self.messageQueue = [message for message in self.messageQueue if message.flag != Flag.K_ALIVE.value.to_bytes(1,byteorder="big").hex()]
                self.socket.sendto(formatHeader(Flag.K_ALIVE.value), self.client)
                timeout = 15
            elif timeout == 0:
                self.quit(2)
            else:
                #print("<INFO> ALIVE SKIP")
                timeout -= 5
            time.sleep(5)

    def switch(self):
        self.status = 45
        self.connected = False

    def lookup(self,flag):
        return [message for message in self.messageQueue if message.flag == flag.to_bytes(1, byteorder="big").hex()]

    def start(self):
        try:
            while not self.connected:
                try:
                    self.data, self.client = self.socket.recvfrom(1024)
                    parts = self.data.hex(" ").split()
                    if parts[0] == Flag.CONNECT.value.to_bytes(1,byteorder="big").hex():
                        self.socket.sendto(formatHeader(Flag.CONNECT.value), self.client)
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
        except s.error as e:
            print(e)
            self.quit(1)


        return self.status

    def quit(self, status):
        self.status = status
        self.connected = False
