import os
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
    crc = None
    if flag == Flag.FILE.value.to_bytes(1, byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)
        data = messageParts[3:]
    elif flag == Flag.MESSAGE.value.to_bytes(1, byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)
        crc = int("".join(messageParts[-2:]), 16)
        data = messageParts[3:]
    elif flag == Flag.NACK.value.to_bytes(1, byteorder="big").hex() or flag == Flag.ACK.value.to_bytes(1, byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)

    elif flag == (Flag.MESSAGE.value|Flag.IS_FRAGMENT.value).to_bytes(1, byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)
        crc = int("".join(messageParts[-2:]), 16)
        data = messageParts[3:]

    return Message(flag, data=data, seq=seq, crc=crc)

def printHelp():
    print(f"{'HELP':_<40}")
    print("Sending a file: <PATH_TO_FILE> -f | -file")
    print("Simulate error on sent message: <MESSAGE> -e | -error")
    print("Simulate error on sent file: <PATH_TO_FILE> -e | -error  -f | -file")
    print("Change fragment size: /f | /fragment <FRAGMENT_SIZE> ")
    print("Switch mode: /s | /switch")
    print("Quit: /q | /quit")
    print(f"{'':_>40}")

class Client:
    def __init__(self, server: tuple):
        print("Entering Sender mode")
        print("Type /help or /h for help")
        self.socket = s.socket(s.AF_INET, s.SOCK_DGRAM)
        port = random.randint(5000, 8000)
        try:
            self.socket.bind(("0.0.0.0", port))
        except s.error:
            self.socket.bind((input("IP: "), int(input("PORT: "))))

        self.serverIP, self.serverPort = server
        self.fragmentSize = 1024
        self.messageQueue = []
        self.connected = False
        self.data = None
        self.status = 0
        self.calculator = Calculator(Crc16.CCITT, optimized=True)

    def sending(self):
        while self.connected:
            inp = input(": ")
            if inp.strip() == "":
                continue
            parts = inp.split(" ")
            parts = [part for part in parts if part.strip()!= ""]

            if len(parts) > 2 and ((parts[-2] in ("-file", "-f") and parts[-1] in ("-e", "-error")) or (parts[-1] in ("-file", "-f") and parts[-2] in ("-e", "-error"))):
                self.faultyFileSend()

            elif parts[-1] == "-file" or parts[-1] == "-f":
                # print(" ".join(parts[:-1]))
                self.sendFile(" ".join(parts[:-1]))

            elif parts[-1] == "-error" or parts[-1] == "-e":
                msg = " ".join(parts[:-1])
                if len(msg) > self.fragmentSize:
                    self.sendFragmentedMessage(msg,error=True)
                else:
                    self.faultySend(msg)

            elif parts[0] == "/f" or parts[0] == "/fragment":
                if len(parts) == 1:
                    print(f"Current Fragment size: {self.fragmentSize}")
                else:
                    try:
                        self.fragmentSize = int(parts[1])
                        print(f"fragment size changed to {self.fragmentSize}")

                    except ValueError:
                        print("Input a valid number for the fragment size")

            elif inp.strip() == "/help" or inp.strip() == "/h":
                printHelp()
            elif inp.strip() == "/switch" or inp.strip() == "/s":
                self.requestSwitch()

            elif inp.strip() == "/quit" or inp.strip() == "/q":
                self.quit(1)

            else:
                msg = " ".join(parts)
                if len(msg) > self.fragmentSize:
                    self.sendFragmentedMessage(msg)
                else:
                    self.sendMessage(msg)

    def lookup(self, flag):
        return [message for message in self.messageQueue if message.flag == flag.to_bytes(1, byteorder="big").hex()]

    def getIndex(self, seq):
        msg = [message for message in self.messageQueue if hasattr(message, "seq") and message.seq == seq]
        return self.messageQueue.index(msg[0])

    def sendMessage(self, message, seq=0):
        expected = self.calculator.checksum(message.encode())
        #print(expected)
        seq = seq #random.randint(0, 32768)
        self.messageQueue.append(Message(Flag.MESSAGE.value, message, seq, expected))
        self.socket.sendto(formatHeader([Flag.MESSAGE.value], seq, message, crc=expected), (self.serverIP, self.serverPort))

    def sendFragmentedMessage(self, message, error=False):
        fragments = []
        index = 0
        while index + self.fragmentSize < len(message):
            fragments.append(message[index:index + self.fragmentSize])
            index += self.fragmentSize

        fragments.append(message[index:])

        packets = [Message([Flag.MESSAGE.value,Flag.IS_FRAGMENT.value]
                           if k == 0 else [Flag.MESSAGE.value],
                           fragment,
                           k,
                           self.calculator.checksum((fragment+("aa" if k == len(fragments)-1 and error else "")).encode())) for k,fragment in enumerate(fragments)]
        for packet in packets:
            self.socket.sendto(formatHeader(packet.flag, packet.seq, packet.data, crc=packet.crc), (self.serverIP, self.serverPort))
        #print(packets)
        print(fragments)

    def sendFragmentedFile(self, filepath, error=False):
        fragments = []
        filename = ""

        try:
            f = open(f"{filepath}", mode="rb")

            byte = f.read(self.fragmentSize)

            while byte:
                fragments.append(byte)
                byte = f.read(self.fragmentSize)

            f.close()
        except FileNotFoundError:
            print("<ERROR> File not found")
            print("<ERROR> Check the path and try again")

        filename = filepath.split("/")[-1]


        packets = [Message([Flag.FILE.value,Flag.IS_FRAGMENT.value]
                   if k == 0 else [Flag.FILE.value],
                   fragment,
                   k,
                   self.calculator.checksum(fragment+bytes("aa") if k == len(fragments)-1 and error else fragment)) for k, fragment in enumerate(fragments)]
        print(len(packets))

        for packet in packets:
            print(packet.seq)
            if packet.seq == 0:
                self.socket.sendto(formatHeader(packet.flag, packet.seq, packet.data, crc=packet.crc, filename=filename), (self.serverIP, self.serverPort))
            else:
                self.socket.sendto(formatHeader(packet.flag, packet.seq, packet.data, crc=packet.crc), (self.serverIP, self.serverPort))
    def sendFile(self, filepath, error=False):
        try:
            if os.path.getsize(filepath) < self.fragmentSize:

                with open(f"{filepath}", mode="rb") as f:
                    data = f.read()

                # print(((b"f"+data).hex(" ").upper()))
                filename = filepath.split("/")[-1]
                self.socket.sendto(formatHeader([Flag.FILE.value], 0, data, filename),
                                   (self.serverIP, self.serverPort))

            else:
                self.sendFragmentedFile(filepath, error=error)

        except FileNotFoundError:
            print("<ERROR> File not found")
            print("<ERROR> Check the path and try again")

    def faultySend(self, message):
        expected = self.calculator.checksum(message.encode())
        # print(expected)
        seq = 0  # random.randint(0, 32768)
        self.messageQueue.append(Message(Flag.MESSAGE.value, message, seq, expected))
        message += "hehe"
        self.socket.sendto(formatHeader(Flag.MESSAGE.value, seq, message, crc=expected),
                           (self.serverIP, self.serverPort))

    def faultyFileSend(self):
        print("send file with error")

    def listen(self):
        while True:
            try:
                self.data, address = self.socket.recvfrom(1024)
                message = analyseMessage(self.data)
                if message.flag == Flag.ACK.value.to_bytes(1, byteorder="big").hex():
                    message.acknowledged = True
                    self.messageQueue.pop(self.getIndex(message.seq))

                elif message.flag == Flag.NACK.value.to_bytes(1, byteorder="big").hex():
                    msg = self.messageQueue[self.getIndex(message.seq)]
                    self.sendMessage(msg.data, msg.seq)

                elif message.flag == Flag.SWITCH.value.to_bytes(1, byteorder="big").hex():
                    self.messageQueue.append(message)
                    self.requestSwitch()
                else:
                    self.messageQueue.append(message)
            except Exception as e:
                pass
                #print(e)

    def keepAlive(self):
        timeout = 40
        while self.connected:
            self.socket.sendto(formatHeader([Flag.K_ALIVE.value]), (self.serverIP, self.serverPort))
            time.sleep(0.1)
            if len(self.lookup(Flag.K_ALIVE.value)) > 0:
                self.messageQueue = [message for message in self.messageQueue if
                                     message.flag != Flag.K_ALIVE.value.to_bytes(1, byteorder="big").hex()]
                timeout = 15
            elif timeout == 0:
                self.quit(2)
            else:
                timeout -= 5
            time.sleep(5)


    def requestSwitch(self):
        self.socket.sendto(formatHeader([Flag.SWITCH.value]), (self.serverIP, self.serverPort))
        timeout = 5
        while timeout > 0 and self.connected:
            #print(len(self.lookup(Flag.SWITCH.value)) > 0)
            if len(self.lookup(Flag.SWITCH.value)) > 0:
                print("Received acknowledgement from Receiver to switch...")
                self.messageQueue = [message for message in self.messageQueue if message.flag != Flag.SWITCH.value.to_bytes(1, byteorder="big").hex()]
                self.status = 45
                time.sleep(2)
                self.connected = False
                break
            else:
                time.sleep(1)
                timeout -= 1
        else:
            if self.connected:
                print("Timed out")


    def sendInit(self):
        self.socket.sendto(formatHeader([Flag.CONNECT.value]), (self.serverIP, self.serverPort))

    def start(self):
        tListening = threading.Thread(target=self.listen, daemon=True)
        tListening.start()
        timeout = 40
        while not self.connected:
            try:
                self.sendInit()
                time.sleep(0.5)
                if len(self.lookup(Flag.CONNECT.value)) > 0:
                    self.connected = True
                    self.messageQueue = []

                elif timeout == 0:
                    self.status = 3
                    break
                else:
                    timeout -= 1
                time.sleep(0.5)

            except Exception as e:
                print("server unreachable")
                self.status = 1
                break
                #print(e)

        tKeepAlive = threading.Thread(target=self.keepAlive, daemon=True)
        tKeepAlive.start()

        tSending = threading.Thread(target=self.sending, daemon=True)
        tSending.start()

        while self.connected:
            pass

        return self.status

    def quit(self, status):
        self.status = status
        self.connected = False
