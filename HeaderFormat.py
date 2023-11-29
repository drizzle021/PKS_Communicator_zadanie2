from enum import Enum


class Flag(Enum):
    CONNECT = 1
    FILE = 2
    MESSAGE = 4
    K_ALIVE = 8
    NACK = 16
    ACK = 32
    SWITCH = 64
    _ = 0


def formatHeader(flag, fragment_seq=0, data="", filename="",crc=0):
    if flag == Flag.CONNECT.value:
        return flag.to_bytes(1,byteorder="big")

    elif flag == Flag.FILE.value:
        return flag.to_bytes(1,byteorder="big") + bytes(fragment_seq.to_bytes(2,byteorder="big")) + bytes(filename, "utf-8") + (0).to_bytes(1,byteorder="big") + data

    elif flag == Flag.MESSAGE.value:
        # print((bytes(flag.to_bytes(1))+bytes(fragment_seq.to_bytes(2))+bytes(data, "utf-8")).hex(" ").split(" "))
        return flag.to_bytes(1,byteorder="big") + bytes(fragment_seq.to_bytes(2,byteorder="big")) + bytes(data, "utf-8") + crc.to_bytes(2,byteorder="big")

    elif flag == Flag.K_ALIVE.value:
        return flag.to_bytes(1,byteorder="big")

    elif flag == Flag.NACK.value:
        return flag.to_bytes(1,byteorder="big") + bytes(fragment_seq.to_bytes(2,byteorder="big"))

    elif flag == Flag.ACK.value:
        return flag.to_bytes(1,byteorder="big") + bytes(fragment_seq.to_bytes(2,byteorder="big"))

    elif flag == Flag.SWITCH.value:
        return flag.to_bytes(1,byteorder="big")
