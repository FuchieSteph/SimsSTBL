import json
import ntpath
from functools import reduce

from s4py.package import *
from s4py.utils import BinPacker

from helpers import helpers
from classes.stbl import StblReader
from classes.tables import map_to_json
from helpers.definitions import *
from helpers.helpers import count_chars


class Package:
    def __init__(self, filepath, lang, isQuick):
        self.lang = lang
        self.filepath = filepath
        self.DATA = []
        self.isQuick = isQuick
        self.model = {}
        self.isLoaded = self.readPackage()
        self.database_path = None

    def getFilename(self):
        return ntpath.basename(self.filepath).replace('_' + self.lang, '').split('.')[0]

    def readPackage(self):
        dbfile = open_package(self.filepath)
        match = False

        self.DATA = []

        for entry in dbfile.scan_index(None):
            idx = dbfile[entry]
            type = "%08x" % idx.id.type
            instance = "%016x" % idx.id.instance
            lang = instance[:2]

            if type != "220557da" or (lang != LANGS[self.lang] and lang != LANGS['ENG_US']):
                continue

            if lang == LANGS[self.lang]:
                match = True

            content = idx.content
            stbl_reader = StblReader(content, self.DATA, lang == LANGS[self.lang], instance)
            self.DATA = stbl_reader.readStbl()
            self.id = idx.id

        dbfile.close()

        if len(self.DATA) == 0:
            return False

        elif not match and not self.isQuick:
            return 'choice'

        return True

    def loadEmptyStrings(self, choice):
        stbl_reader = StblReader(None, self.DATA, None)
        self.DATA = stbl_reader.loadEmptyStrings(choice)

    def load_translation(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
            try:
                for str in data['strings']:
                    self.model.replaceData(str['id'], str)
                return True
            except:
                raise
                return False

    def load_csv_translation(self, rows):
        next(rows)

        for data in rows:
            try:
                structure = {'id': int(data[KEY_INDEX]), 'instance': data[INSTANCE_INDEX], 'base': None,
                             'translation': data[TRANSLATION_INDEX], 'state': int(data[STATE_INDEX])}
                self.model.replaceData(int(data[KEY_INDEX]), structure)
            except:
                return False

        return True

    def load_package_translation(self, package):
        for data in package.DATA:
            structure = {'id': data[KEY_INDEX], 'instance': data[INSTANCE_INDEX], 'base': None,
                         'translation': data[TRANSLATION_INDEX], 'state': 2}
            self.model.replaceData(data[KEY_INDEX], structure)

        return True

    def save_translation(self, export_path):
        with open(export_path, 'w', newline='', encoding='utf-8') as f:
            data = {'lang': self.lang, 'strings': list(map(map_to_json, self.model._data))}
            f.seek(0)
            json.dump(data, f, sort_keys=True, indent=4)
            f.close()

    def export(self, replace, export_path):

        temp_name = self.filepath.replace('.package', '_new.package') if replace else export_path
        dbfile_old = open_package(self.filepath)
        dbfile_new = open_package(temp_name, 'w')

        for entry in dbfile_old.scan_index(None):
            idx = dbfile_old[entry]
            type = "%08x" % idx.id.type
            instance = "%016x" % idx.id.instance
            lang = instance[:2]

            if replace is True and (type != "220557da" or lang != LANGS[self.lang]):
                dbfile_new.put(idx.id, idx.content)

            elif lang == LANGS[self.lang]:
                self.writePackage(dbfile_new, idx.id, instance)

        dbfile_new.commit()

        dbfile_old.close()
        dbfile_new.close()

        # IF WE REPLACE WE RENAME THE OLD & NEW FILES
        if replace:
            os.rename(self.filepath, self.generate_name())
            os.rename(self.filepath.replace('.package', '_new.package'), self.filepath)

    def generate_name(self, i=0):
        new_path = self.filepath.replace('.package', '.package' + '.BAK' + str(i))
        if os.path.exists(new_path):
            return self.generate_name(i + 1)
        else:
            return new_path

    def writePackage(self, dbfile2, id, instance=None):
        data_list = list(filter(lambda x: x[INSTANCE_INDEX] == instance, self.DATA))
        file_totalchar = reduce(count_chars, data_list)

        f = BinPacker(bytes())
        f.put_strz('STBL')
        f.put_uint16(5)  # Version
        f.put_uint8(0)  # Compressed
        f.put_uint64(len(data_list))  # numEntries
        f.put_uint16(0)  # Flag
        f.put_uint32(file_totalchar)  # mnStringLength

        for data in data_list:
            nbChar = len(data[TRANSLATION_INDEX].encode('utf-8'))
            f.put_uint32(data[KEY_INDEX])  # HASH
            f.put_uint8(0)  # FLAG
            f.put_uint16(nbChar)  # NB CHAR
            f.put_strz(data[TRANSLATION_INDEX])  # DATA

        f.raw.seek(0)
        dbfile2.put(id, f.raw.getvalue())
        f.close()
