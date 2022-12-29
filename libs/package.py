import json
import sys
import os
import time
import ntpath

import PyQt6
from PyQt6 import QtGui, QtWidgets, QtCore
from PyQt6.QtCore import QDir, QFile, QFileInfo, QSortFilterProxyModel, QThread, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import QSettings

from s4py.package import *

import csv
from libs.definitions import LANGS, LANG_LIST, STATE_LIST
from libs import helpers
from libs.stbl import StblReader
from libs.tables import TableModel, get_translation, map_to_json


class Package:
    def __init__(self, filepath, lang, isQuick):
        self.lang = lang
        self.filepath = filepath
        self.DATA = {'keys': [], 'data': [], 'base': []}
        self.isQuick = isQuick
        self.model = {}
        self.isLoaded = self.readPackage()

    def getFilename(self):
        return ntpath.basename(self.filepath).replace('_' + self.lang, '').split('.')[0]

    def readPackage(self):
        dbfile = open_package(self.filepath)
        match = False

        self.DATA = {'keys': [], 'data': [], 'base': []}

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
            stbl_reader = StblReader(content, self.DATA, lang == LANGS[self.lang])
            self.DATA = stbl_reader.readStbl()
            self.id = idx.id

        if len(self.DATA['keys']) == 0:
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
                return False

    def save_translation(self, export_path):
        with open(export_path, 'w', newline='', encoding='utf-8') as f:
            data = {'lang': self.lang, 'strings': list(map(map_to_json, self.model._data))}
            f.seek(0)
            json.dump(data, f, sort_keys=True, indent=4)
            f.close()

    def export(self, export_path):
        dbfile2 = open_package(export_path, 'w')
        data = list(map(get_translation, self.model._data))

        i = 0
        totalchar = 0

        for key in self.DATA['keys']:
            totalchar += len(data[i].encode('utf-8'))
            i = i + 1

        f = helpers.BinPacker(bytes())
        f.put_strz('STBL')
        f.put_uint16(5)  # Version
        f.put_uint8(0)  # Compressed
        f.put_uint64(len(self.DATA['keys']))  # numEntries
        f.put_uint16(0)  # Flag
        f.put_uint32(totalchar)  # mnStringLength

        i = 0
        for key in self.DATA['keys']:
            nbChar = len(data[i].encode('utf-8'))
            f.put_uint32(key)  # HASH
            f.put_uint8(0)  # FLAG
            f.put_uint16(nbChar)  # NB CHAR
            f.put_strz(data[i])  # DATA

            i = i + 1

        f.raw.seek(0)
        dbfile2.put(self.id, f.raw.getvalue())
        dbfile2.commit()
        f.close()
