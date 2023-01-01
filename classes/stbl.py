from s4py.package import *

from helpers.definitions import *


class StblReader:
    def __init__(self, content, data, isTrans, instance):
        self.content = content
        self.instance = instance
        self.isTrans = isTrans
        self.DATA = data

    def search_position(self, key):
        result = list(filter(lambda v: v[KEY_INDEX] == key and v[INSTANCE_INDEX][-8:] == self.instance[-8:], self.DATA))
        return self.DATA.index(result[0]) if len(result) > 0 else None

    def loadEmptyStrings(self, choice):
        i = 0

        for _ in range(len(self.DATA['keys'])):
            if choice == 0:
                self.DATA['data'][i][TRANSLATION_INDEX] = ''

            else:
                self.DATA['data'][i][TRANSLATION_INDEX] = self.DATA['data'][i][1]

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
        char_count = 0

        for _ in range(numEntries):
            keyHash = f.get_uint32()
            index = self.search_position(keyHash)

            flags = f.get_uint8()
            length = f.get_uint16()
            val = f.get_raw_bytes(length).decode('utf-8')
            char_count += len(val)

            # FIRST TIME DATA IS LOADED = WE CREATE DATA
            if index is None:
                self.DATA.append([str("%08x" % keyHash).upper(), keyHash, self.instance, None, None, 0])
                index = len(self.DATA) - 1

            if self.isTrans:
                self.DATA[index][TRANSLATION_INDEX] = val
                self.DATA[index][INSTANCE_INDEX] = self.instance
            else:
                self.DATA[index][BASE_INDEX] = val

        return self.DATA
