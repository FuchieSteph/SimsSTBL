from s4py.package import *

from helpers.definitions import *


class StblReader:
    def __init__(self, content, data, isTrans, instance, filepath, filename):
        self.content = content
        self.instance = instance
        self.isTrans = isTrans
        self.DATA = data
        self.filepath = filepath
        self.filename = filename + '.package'

    def search_position(self, key):
        if key in self.DATA[self.instance]:
            return True

        else:
            return None

    def loadEmptyStrings(self, choice, base_index, to_index, lang):

        for data in self.DATA:
            if choice == 0:
                data[to_index] = ''

            else:
                data[to_index] = data[base_index]

            if to_index == TRANSLATION_INDEX:
                data[INSTANCE_INDEX] = data[INSTANCE_INDEX].replace('00', LANGS[lang])

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

            flags = f.get_uint8()
            length = f.get_uint16()
            val = f.get_raw_bytes(length).decode('utf-8')
            char_count += len(val)

            # FIRST TIME DATA IS LOADED = WE CREATE FILE
            if not self.filename in self.DATA:
                self.DATA[self.filename] = {}

            # FIRST TIME DATA IS LOADED = WE CREATE INSTANCE
            if not self.instance in self.DATA[self.filename]:
                self.DATA[self.filename][self.instance] = {}

            # NO KEY YET WE ADD IT
            if not keyHash in self.DATA[self.filename][self.instance]:
                self.DATA[self.filename][self.instance][keyHash] = ()
                self.DATA[self.filename][self.instance][keyHash] = [str("%08x" % keyHash).upper(), keyHash,
                                                                    self.instance, None, None,
                                                                    0, self.filepath, self.filename]

            if self.isTrans:
                self.DATA[self.filename][self.instance][keyHash][TRANSLATION_INDEX] = val
                self.DATA[self.filename][self.instance][keyHash][INSTANCE_INDEX] = self.instance
            else:
                self.DATA[self.filename][self.instance][keyHash][BASE_INDEX] = val

        return self.DATA
