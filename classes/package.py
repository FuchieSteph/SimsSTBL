import json
import ntpath
from functools import reduce

from s4py.package import *
from s4py.resource import Resource, ResourceID
from s4py.utils import BinPacker

from helpers import helpers
from classes.stbl import StblReader
from classes.tables import map_to_json
from helpers.definitions import *
from helpers.helpers import count_chars


class Package:
    def __init__(self, filepath, lang, isQuick, isMulti=False, data=None):
        self.lang = lang
        self.filepath = filepath
        self.DATA = data[0] if isMulti else []
        self.isQuick = isQuick
        self.multipath = data[1] if isMulti else None
        self.model = {}
        self.isMulti = isMulti

        if not self.isMulti:
            data = self.readPackage()
            self.isLoaded = data[0]
            self.createSTBL = data[1]
            self.flatten_data = self.flatten(self.DATA, [])
        else:
            self.isLoaded = True
            self.createSTBL = False
            self.flatten_data = self.flatten(self.DATA, [])

        self.database_path = None

    def getFilePath(self):
        return ntpath.dirname(self.filepath)

    def getFilename(self):
        return ntpath.basename(self.filepath).replace('_' + self.lang, '').split('.')[0]

    def getPackagename(self):
        return ntpath.basename(self.filepath).split('.')[0]

    def flatten(self, data, new_data):
        if isinstance(data, dict):
            for f in data.items():
                new_data = self.flatten(f[1], new_data)

        elif isinstance(data, list):
            if len(data) == 0:
                return []

            if data[BASE_INDEX] is None:
                data[BASE_INDEX] = data[TRANSLATION_INDEX]

            elif data[TRANSLATION_INDEX] is None:
                data[TRANSLATION_INDEX] = data[BASE_INDEX]

            new_data.append(data)

        return new_data

    def readPackage(self):
        dbfile = open_package(self.filepath)
        match = False

        self.DATA = {}

        try:
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

                stbl_reader = StblReader(content, self.DATA, lang == LANGS[self.lang], LANGS['ENG_US'] + instance[2:],
                                         self.filepath,
                                         self.getPackagename())
                self.DATA = stbl_reader.readStbl()
                self.id = idx.id

            dbfile.close()

            if len(self.DATA) == 0:
                return [False, False]

        except:
            return [False, False]

        return [True, not match]

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
        id_create = ''

        for entry in dbfile_old.scan_index(None):
            idx = dbfile_old[entry]
            type = "%08x" % idx.id.type
            instance = "%016x" % idx.id.instance
            group = "%08x" % idx.id.group
            lang = instance[:2]

            if type == "220557da" and lang == LANGS['ENG_US']:
                new_instance = LANGS[self.lang] + instance[2:]
                id_create = ResourceID(group=idx.id.group, instance=int(new_instance, 16), type=idx.id.type)

            if replace is True and (type != "220557da" or lang != LANGS[self.lang]):
                dbfile_new.put(idx.id, idx.content)

            elif lang == LANGS[self.lang]:
                self.writePackage(dbfile_new, idx.id, instance)

        if self.createSTBL:
            self.writePackage(dbfile_new, id_create, self.DATA[0][INSTANCE_INDEX])

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
        base_instance = LANGS['ENG_US'] + instance[2:]

        data_list = list(filter(lambda x: x[INSTANCE_INDEX] == base_instance, self.DATA))
        if len(data_list) == 0:
            return

        file_totalchar = reduce(count_chars, data_list)

        if type(file_totalchar) is not int:
            return

        f = BinPacker(bytes())
        f.put_strz('STBL')
        f.put_uint16(5)  # Version
        f.put_uint8(0)  # Compressed
        f.put_uint64(len(data_list))  # numEntries
        f.put_uint16(0)  # Flag
        f.put_uint32(file_totalchar + len(data_list))  # mnStringLength

        for data in data_list:
            nbChar = len(data[TRANSLATION_INDEX].encode('utf-8'))
            f.put_uint32(data[KEY_INDEX])  # HASH
            f.put_uint8(0)  # FLAG
            f.put_uint16(nbChar)  # NB CHAR
            f.put_strz(data[TRANSLATION_INDEX])  # DATA

        f.raw.seek(0)
        dbfile2.put(id, f.raw.getvalue())

        f.close()
