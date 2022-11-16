import shutil

from s4py.package import *

from definitions import LANGS
from libs import helpers
from libs.stbl import readStbl


class App:
    APP_NAME = "map_view_demo.py"

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.DATA = []
        self.lang = 'FRA_FR'
        self.filepath = 'test.package'

    def readPackage(self):
        dbfile = open_package(self.filepath)
        shutil.copyfile(self.filepath, self.filepath.replace('.package', '_new.package'))
        dbfile2 = open_package(self.filepath.replace('.package', '_new.package'), 'w')

        self.KEYS = {}
        self.DATA = []

        for entry in dbfile.scan_index(None):
            idx = dbfile[entry]
            type = "%08x" % idx.id.type
            instance = "%016x" % idx.id.instance
            lang = instance[:2]

            if type != "220557da" or (lang != LANGS[self.lang] and lang != LANGS['ENG_US']):
                continue

            content = idx.content

            current_lang = list(LANGS.keys())[list(LANGS.values()).index(lang)]
            stbl = readStbl(content, self.DATA)

            self.KEYS = stbl[0]
            self.DATA = stbl[1]

            if lang == LANGS[self.lang]:
                f = helpers.BinPacker(bytes())
                f.put_strz('STBL')
                print(len(self.KEYS))

                f.put_uint16(5)  # Version
                f.put_uint8(0)  # Compressed
                f.put_uint64(808)  # numEntries
                f.put_uint16(0)  # Flag
                f.put_uint32(55621)  # mnStringLength

                i = 0
                for key in self.KEYS:
                    nbChar = len("DATA TEST")
                    f.put_uint32(key)  # HASH
                    f.put_uint8(0)  # FLAG
                    f.put_uint16(nbChar)  # NB CHAR
                    f.put_strz("DATA TEST")  # DATA

                    i = i + 1

                f.raw.seek(0)
                print(content)
                print(f.raw.getvalue())

                dbfile2.put(idx.id, f.raw.getvalue())
                dbfile2.commit()

    def start(self):
        self.readPackage()


app = App()
app.start()
