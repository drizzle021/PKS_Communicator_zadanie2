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


def formatHeader(flag, fragment_seq, data, filename=""):
    if flag == Flag.CONNECT.value:
        return bytes(flag)
    elif flag == Flag.FILE.value:
        return f"{flag}{fragment_seq}{filename}00{data}"
    elif flag == Flag.MESSAGE.value:
        return bytes(flag)+bytes(fragment_seq)+bytes(data, "utf-8")
    elif flag == Flag.K_ALIVE.value:
        return f"{flag}"
    elif flag == Flag.NACK.value:
        return f"{flag}{fragment_seq}"
    elif flag == Flag.ACK.value:
        return f"{flag}{fragment_seq}"
    elif flag == Flag.SWITCH.value:
        return f"{flag}"
