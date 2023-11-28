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


def formatHeader(flag, fragment_seq=0, data="", filename=""):
    if flag == Flag.CONNECT.value:
        return flag.to_bytes(1)

    elif flag == Flag.FILE.value:
        return flag.to_bytes(1) + bytes(fragment_seq.to_bytes(2)) + bytes(filename, "utf-8") + (0).to_bytes(1) + data

    elif flag == Flag.MESSAGE.value:
        # print((bytes(flag.to_bytes(1))+bytes(fragment_seq.to_bytes(2))+bytes(data, "utf-8")).hex(" ").split(" "))
        return flag.to_bytes(1) + bytes(fragment_seq.to_bytes(2)) + bytes(data, "utf-8")

    elif flag == Flag.K_ALIVE.value:
        return f"{flag}"

    elif flag == Flag.NACK.value:
        return f"{flag}{fragment_seq}"

    elif flag == Flag.ACK.value:
        return f"{flag}{fragment_seq}"

    elif flag == Flag.SWITCH.value:
        return flag.to_bytes(1)
