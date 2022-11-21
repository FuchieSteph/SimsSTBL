from s4py.package import *


class StblReader:
    def __init__(self, content, data, isTrans):
        self.content = content
        self.isTrans = isTrans
        self.DATA = data

    def loadEmptyStrings(self, choice):
        i = 0
        char_count = 0

        for _ in range(len(self.DATA['keys'])):
            if choice == 1:
                self.DATA['data'][i][2] = ''

            else:
                self.DATA['data'][i][2] = self.DATA['data'][i][1]

            i = i + 1

        return self.DATA

    def readStbl(self):
        f = utils.BinPacker(self.content)

        if f.get_raw_bytes(4) != b'STBL':
            raise utils.FormatException("Bad magic")

        version = f.get_uint16()
        if version != 5:
            raise utils.FormatException("We only support STBLv5")

        compressed = f.get_uint8()
        numEntries = f.get_uint64()
        unk = f.get_uint16()
        mnStringLength = f.get_uint32()

        entries = {}
        size = 0

        i = 0
        char_count = 0
        print(numEntries)

        for _ in range(numEntries):
            keyHash = f.get_uint32()

            try:
                index = self.DATA['keys'].index(keyHash)
                row = True
            except:
                row = None
                self.DATA['keys'].append(keyHash)

            flags = f.get_uint8()  # What is in this? It's always 0.
            length = f.get_uint16()
            val = f.get_raw_bytes(length).decode('utf-8')
            char_count += len(val)

            if row is None:
                self.DATA['data'].append([keyHash, None, None, 0])
                index = len(self.DATA['data']) - 1

            if self.isTrans:
                self.DATA['data'][index][2] = val
            else:
                self.DATA['data'][index][1] = val
                self.DATA['base'].append(val)

            i = i + 1

        return self.DATA
