class Message:
    def __init__(self, flag, data=None, seq=None, crc=None):
        self.flag = flag
        if data is not None:
            self.data = data
        if seq is not None:
            self.seq = seq
        if crc is not None:
            self.crc = crc

