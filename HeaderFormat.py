from enum import Enum


class Flag(Enum):
    CONNECT = 1
    FILE = 2
    MESSAGE = 4
    K_ALIVE = 8
    NACK = 16
    ACK = 32
    SWITCH = 64
    IS_FRAGMENT = 128

def formatHeader(flags, fragment_seq=0, data="", filename="",crc=0):
    flag = 0
    for i in flags:
        flag+=i

    if flag == Flag.CONNECT.value:
        return flag.to_bytes(1, byteorder="big")

    elif flag == Flag.FILE.value:
        if filename != "":
            return flag.to_bytes(1, byteorder="big") + bytes(fragment_seq.to_bytes(2, byteorder="big")) + bytes(filename, "utf-8") + (0).to_bytes(1, byteorder="big") + data + crc.to_bytes(2, byteorder="big")
        else:
            return flag.to_bytes(1, byteorder="big") + bytes(fragment_seq.to_bytes(2, byteorder="big")) + data + crc.to_bytes(2, byteorder="big")


    elif flag == Flag.MESSAGE.value:
        # print((bytes(flag.to_bytes(1))+bytes(fragment_seq.to_bytes(2))+bytes(data, "utf-8")).hex(" ").split(" "))
        return flag.to_bytes(1, byteorder="big") + bytes(fragment_seq.to_bytes(2, byteorder="big")) + bytes(data, "utf-8") + crc.to_bytes(2, byteorder="big")

    elif flag == Flag.K_ALIVE.value:
        return flag.to_bytes(1, byteorder="big")

    elif flag == Flag.NACK.value:
        return flag.to_bytes(1, byteorder="big") + bytes(fragment_seq.to_bytes(2, byteorder="big"))

    elif flag == Flag.ACK.value:
        return flag.to_bytes(1, byteorder="big") + bytes(fragment_seq.to_bytes(2, byteorder="big"))

    elif flag == Flag.SWITCH.value:
        return flag.to_bytes(1, byteorder="big")

    elif flag == Flag.IS_FRAGMENT.value|Flag.MESSAGE.value:
        return flag.to_bytes(1, byteorder="big") + bytes(fragment_seq.to_bytes(2, byteorder="big")) + bytes(data, "utf-8") + crc.to_bytes(2, byteorder="big")

    elif flag == Flag.IS_FRAGMENT.value|Flag.FILE.value:
        return flag.to_bytes(1, byteorder="big") + bytes(fragment_seq.to_bytes(2, byteorder="big")) + bytes(filename, "utf-8") + (0).to_bytes(1, byteorder="big") + data + crc.to_bytes(2, byteorder="big")

