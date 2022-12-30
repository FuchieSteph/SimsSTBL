import PyQt6
from PyQt6 import QtCore
from PyQt6.QtGui import QColor
from PyQt6.QtCore import *

from helpers.definitions import STATE_LIST


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, header):
        super(TableModel, self).__init__()
        self._data = data['data']
        self._keys = data['keys']
        self._strings = data['base']
        self._header = header

    def headerData(self, col, orientation, role):
        if orientation == PyQt6.QtCore.Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._header[col]
        return None

    def data(self, index, role):
        row = self._data[index.row()]
        cell = row[index.column()]

        if role == Qt.ItemDataRole.BackgroundRole:
            if row[3] == 2:
                return QVariant(QColor.fromRgb(44, 165, 141))
            elif row[3] == 1:
                return QVariant(QColor.fromRgb(244, 97, 151))

        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 3:
                return STATE_LIST[cell]

            return cell

        if role == Qt.ItemDataRole.EditRole:
            return cell

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole and index.column() == 2 and value != '':
            self._data[index.row()][index.column()] = value
            return True
        return False

    def replaceData(self, string, data):

        if string in self._keys:
            row = self._keys.index(string)
            if self._data[row][1] == data['base'] or data['base'] is None:
                self._data[row][2] = data['translation']
                self._data[row][3] = data['state']

        elif data['base'] in self._strings:
            row = self._strings.index(data['base'])
            self._data[row][2] = data['translation']
            self._data[row][3] = data['state']

        else:
            pass

    def updateState(self, row, state):
        self._data[row][3] = state

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable


def get_translation(n):
    return n[2]


def map_to_json(n):
    return {"id": n[0], 'base': n[1], 'translation': n[2], 'state': n[3]}


class MyProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super(MyProxyModel, self).__init__()
        self.searchText = None

    def filterState(self, state):
        return
