from s4py.package import *


def readStbl(content, data):
    f = utils.BinPacker(content)

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

    keys = []

    i = 0
    char_count = 0

    for _ in range(numEntries):
        keyHash = f.get_uint32()
        flags = f.get_uint8()  # What is in this? It's always 0.
        length = f.get_uint16()
        val = f.get_raw_bytes(length).decode('utf-8')
        keys.append(keyHash)
        char_count += len(val)

        try:
            data[i].append(val)
        except:
            data.append([val])

        i = i + 1

    return keys, data
