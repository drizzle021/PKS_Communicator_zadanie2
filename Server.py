import socket as s
import threading
import time
from HeaderFormat import formatHeader, Flag
from Message import Message
from crc import Calculator, Crc16
from pynput import keyboard
import os


def analyseMessage(message):
    messageParts = message.hex(" ").split()
    flag = messageParts[0]
    data = None
    seq = None
    crc = None
    if flag == Flag.FILE.value.to_bytes(1, byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)
        data = messageParts[3:-2]
        crc = int("".join(messageParts[-2:]), 16)
    elif flag == Flag.MESSAGE.value.to_bytes(1, byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)
        crc = int("".join(messageParts[-2:]), 16)
        data = messageParts[3:-2]
    elif flag == Flag.NACK.value.to_bytes(1, byteorder="big").hex() or flag == Flag.ACK.value.to_bytes(1,
                                                                                                       byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)
    elif flag == (Flag.MESSAGE.value | Flag.IS_FRAGMENT.value).to_bytes(1, byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)
        crc = int("".join(messageParts[-2:]), 16)
        data = messageParts[3:-2]
    elif flag == (Flag.FILE.value | Flag.IS_FRAGMENT.value).to_bytes(1, byteorder="big").hex():
        seq = int("".join(messageParts[1:3]), 16)
        crc = int("".join(messageParts[-2:]), 16)
        data = messageParts[3:-2]

    return Message(flag, data=data, seq=seq, crc=crc)


class Server:
    def __init__(self, ip="0.0.0.0", port=9000):
        print("Entering Receiver mode")
        self.socket = s.socket(s.AF_INET, s.SOCK_DGRAM)
        self.socket.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
        # self.socket.bind((ip,port))
        self.socket.bind((ip, port))
        self.connected = False
        self.data = None
        self.client = None
        self.calculator = Calculator(Crc16.CCITT, optimized=True)
        self.filename = ""

        self.isReceivingMessageFragments = False
        self.dataFragments = []
        self.fragmentSize = 512
        self.missing = float("inf")
        self.gotLastFrag = False
        self.requesting = False

        self.messageQueue = []

        self.savePath = ""
        self.status = 0

    def listen(self):
        while self.connected:
            try:
                self.data, address = self.socket.recvfrom(2000)

                message = analyseMessage(self.data)
                #print(message.flag)
                if self.isReceivingMessageFragments and message.flag == Flag.MESSAGE.value.to_bytes(1,
                                                                                                    byteorder="big").hex():
                    self.receiveFragmentedMessage(message)
                    continue
                if self.isReceivingMessageFragments and message.flag == Flag.FILE.value.to_bytes(1,byteorder="big").hex():
                    #print("CASCACAS")
                    self.receiveFragmentedFile(message)
                    continue

                # TODO if verified send ACK and output else send NACK
                if message.flag == Flag.MESSAGE.value.to_bytes(1, byteorder="big").hex():
                    verification = self.calculator.verify(bytes.fromhex(' '.join(message.data)), message.crc)
                    # print(verification)
                    # print()
                    if verification:
                        self.socket.sendto(formatHeader([Flag.ACK.value], message.seq), self.client)
                        print(f"{address}: {bytes.fromhex(' '.join(message.data)).decode()}")

                    else:
                        print("faulty message")
                        self.socket.sendto(formatHeader([Flag.NACK.value], message.seq), self.client)

                elif message.flag == Flag.SWITCH.value.to_bytes(1, byteorder="big").hex():
                    self.switch()

                elif message.flag == Flag.FILE.value.to_bytes(1, byteorder="big").hex():
                    self.receiveFile(message, address)


                elif message.flag == (Flag.MESSAGE.value | Flag.IS_FRAGMENT.value).to_bytes(1, byteorder="big").hex():
                    self.fragmentSize = len(bytes.fromhex(' '.join(message.data)).decode())
                    print(f"Receiving fragments with fragment size {self.fragmentSize}")
                    self.isReceivingMessageFragments = True
                    self.receiveFragmentedMessage(message)

                elif message.flag == (Flag.FILE.value | Flag.IS_FRAGMENT.value).to_bytes(1, byteorder="big").hex():
                    self.missing = float("inf")
                    print(f"Receiving file fragments with fragment size {self.fragmentSize}")
                    self.isReceivingMessageFragments = True

                    separatorIndex = message.data.index("00")
                    self.filename = message.data[:separatorIndex]
                    self.filename = bytes.fromhex(" ".join(self.filename))

                    self.fragmentSize = len(bytes.fromhex(' '.join(message.data)))-len(self.filename)-1

                    self.filename = self.filename.decode()

                    message.data = message.data[separatorIndex + 1:]

                    self.receiveFragmentedFile(message)

                if message.flag != Flag.K_ALIVE.value.to_bytes(1, byteorder="big").hex() or len(
                        self.lookup(Flag.K_ALIVE.value)) < 1:
                    self.messageQueue.append(message)

            except Exception as e:
                #print(e)
                pass

    def receiveFile(self, file, address):
        try:
            separatorIndex = file.data.index("00")

            filename = file.data[:separatorIndex]
            filename = bytes.fromhex(" ".join(filename))

            filename = filename.decode()

            if os.path.splitext(filename)[1] == "":
                return


            file = file.data[separatorIndex + 1:]
            file = bytes.fromhex(" ".join(file))

            print(f"{address}\nFile Received: {filename}")
            self.saveFile(filename, file)

            # self.messageQueue.remove(file)
        except UnicodeError:
            return
        except ValueError:
            return


    def receiveFragmentedFile(self, message):
        verification = self.calculator.verify(bytes.fromhex(' '.join(message.data)), message.crc)

        if hasattr(message, "acknowledged") and verification:
            message.acknowledged = True
            self.socket.sendto(formatHeader([Flag.ACK.value], message.seq), self.client)
            print(f"{message.seq} - acknowledged")
            self.dataFragments.append(message)


        #print(bytes.fromhex(' '.join(message.data)))

        if len(bytes.fromhex(' '.join(message.data))) < self.fragmentSize or self.gotLastFrag:
            self.dataFragments = sorted(self.dataFragments, key=lambda x: x.seq)
            self.gotLastFrag = True
            if len(missing := self.checkSequenceNumbers()) > 0:
                if not self.requesting:
                    self.missing = missing

                    tRequestMissing = threading.Thread(target=lambda: self.requestMissing(missing))
                    tRequestMissing.start()

            else:
                #print(len(self.dataFragments))
                #print([fragment.acknowledged for fragment in self.dataFragments])
                #print(all([fragment.acknowledged for fragment in self.dataFragments]))
                self.dataFragments= self.handleDups(self.dataFragments)
                print(len(self.dataFragments))
                self.isReceivingMessageFragments = False
                self.gotLastFrag = False

                self.saveFile(self.filename, self.dataFragments, fragmented=True)
                self.dataFragments = []

    def requestMissing(self, missing):
        self.requesting = True
        #print(missing)
        for seq in missing:
            #print(f"{seq} - missing, sent NACK")
            self.socket.sendto(formatHeader([Flag.NACK.value], seq), self.client)
        self.requesting = False

    def handleDups(self, fragments):
        s = []
        newfragments = []

        for fragment in fragments:
            if fragment.seq not in s:
                s.append(fragment.seq)
                newfragments.append(fragment)

        newfragments = sorted(newfragments, key=lambda x: x.seq)

        return newfragments




    def saveFile(self, filename, file, fragmented=False):
        try:
            if not fragmented:
                if os.path.isdir(self.savePath):
                    try:
                        with open(f"{self.savePath}/{filename}", mode="wb") as f:
                            f.write(file)
                            print(f"File saved at {self.savePath}")
                    except PermissionError:
                        print("Permission denied or path wasnt set :(")
                        with open(f"{os.path.dirname(os.path.abspath(__file__))}/{filename}", mode="wb") as f:
                            f.write(file)
                            print(f"File saved at {os.path.dirname(os.path.abspath(__file__))}")

                else:
                    print("Invalid save path.. saving at default directory..")
                    with open(f"{os.path.dirname(os.path.abspath(__file__))}/{filename}", mode="wb") as f:
                        f.write(file)
                        print(f"File saved at {os.path.dirname(os.path.abspath(__file__))}")
            else:
                if os.path.isdir(self.savePath):
                    try:
                        with open(f"{self.savePath}/{filename}", mode="wb") as f:
                            for fragment in file:
                                f.write(bytes.fromhex(' '.join(fragment.data)))
                            print(f"File saved at {self.savePath}")
                    except PermissionError:
                        print("Permission denied or path wasnt set :(")
                        with open(f"{os.path.dirname(os.path.abspath(__file__))}/{filename}", mode="wb") as f:
                            for fragment in file:
                                f.write(bytes.fromhex(' '.join(fragment.data)))
                            print(f"File saved at {os.path.dirname(os.path.abspath(__file__))}")

                else:
                    print("Invalid save path.. saving at default directory..")
                    with open(f"{os.path.dirname(os.path.abspath(__file__))}/{filename}", mode="wb") as f:
                        for fragment in file:
                            f.write(bytes.fromhex(' '.join(fragment.data)))
                        print(f"File saved at {os.path.dirname(os.path.abspath(__file__))}")
        except UnicodeError as e:
            return


    def receiveFragmentedMessage(self, message):
        #print(message)
        verification = self.calculator.verify(bytes.fromhex(' '.join(message.data)), message.crc)

        if hasattr(message, "acknowledged") and verification:
            message.acknowledged = True

        self.dataFragments.append(message)

        if len(bytes.fromhex(' '.join(message.data)).decode()) < self.fragmentSize:
            print([fragment.acknowledged for fragment in self.dataFragments])
            print(all([fragment.acknowledged for fragment in self.dataFragments]))
            self.isReceivingMessageFragments = False
            self.dataFragments = [bytes.fromhex(' '.join(fragment.data)).decode() for fragment in self.dataFragments]

            print("".join(self.dataFragments))
            self.dataFragments = []

    def checkAlive(self):
        timeout = 15
        while self.connected:
            # print(self.messageQueue)
            # print(len(self.lookup(Flag.K_ALIVE.value)))
            if len(self.lookup(Flag.K_ALIVE.value)) > 0 or self.isReceivingMessageFragments:
                # print("<INFO> ALIVE")
                self.messageQueue = [message for message in self.messageQueue if
                                     message.flag != Flag.K_ALIVE.value.to_bytes(1, byteorder="big").hex()]
                self.socket.sendto(formatHeader([Flag.K_ALIVE.value]), self.client)
                timeout = 15
            elif timeout == 0:
                self.quit(2)
            else:
                # print("<INFO> ALIVE SKIP")
                timeout -= 5
            time.sleep(5)

    def requestSwitch(self):
        try:
            if not self.isReceivingMessageFragments:
                self.socket.sendto(formatHeader([Flag.SWITCH.value]), self.client)
            else:
                print("currently receiving data, try again later")
        except s.error:
            print("Try again :'( UwU")

    def switch(self):
        # print("Sender ending messages. Requesting switch....")
        self.socket.sendto(formatHeader([Flag.SWITCH.value]), self.client)
        self.status = 45
        self.connected = False

    def lookup(self, flag):
        return [message for message in self.messageQueue if message.flag == flag.to_bytes(1, byteorder="big").hex()]

    def start(self):
        try:
            while not self.connected:
                try:
                    self.data, self.client = self.socket.recvfrom(1024)
                    parts = self.data.hex(" ").split()
                    if parts[0] == Flag.CONNECT.value.to_bytes(1, byteorder="big").hex():
                        self.socket.sendto(formatHeader([Flag.CONNECT.value]), self.client)
                        self.connected = True
                        self.status = 1

                except Exception as e:
                    pass
                    # print(e)

            tCheckAlive = threading.Thread(target=self.checkAlive, daemon=True)
            tCheckAlive.start()

            tListening = threading.Thread(target=self.listen, daemon=True)
            tListening.start()

            tKeyListen = threading.Thread(target=self.keyListen, daemon=True)
            tKeyListen.start()

            while self.connected:
                pass

        except s.error as e:
            # print(e)
            self.quit(1)

        return self.status

    def keyListen(self):
        while self.connected:
            inp = input("(/q to quit; /s to switch; /p to change save path): ")
            parts = inp.split(" ")
            if inp.strip() == "/s" or inp.strip() == "/switch":
                self.requestSwitch()
            if inp.strip() == "/q" or inp.strip() == "/quit":
                self.quit(1)
            if len(parts) > 1 and parts[0] == "/p":
                self.savePath = parts[1]
                if not os.path.isdir(self.savePath):
                    print("invalid save path")

    def quit(self, status):
        self.status = status
        self.connected = False

    def checkSequenceNumbers(self):
        seqs = {fragment.seq for fragment in self.dataFragments}
        missing = {n for n in range(max(seqs)+1)}.difference(seqs)

        return missing
