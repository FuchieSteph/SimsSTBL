import PyQt6
from PyQt6 import QtGui, QtWidgets, QtCore
from PyQt6.QtGui import QAction, QColor, QIcon, QFont
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from libs.definitions import STATE_LIST


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
        if role == Qt.ItemDataRole.BackgroundRole:
            if self._data[index.row()][3] == 2:
                return QVariant(QColor(Qt.GlobalColor.green))
            elif self._data[index.row()][3] == 1:
                return QVariant(QColor(Qt.GlobalColor.lightGray))

        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 3:
                return STATE_LIST[self._data[index.row()][index.column()]]
            else:
                return self._data[index.row()][index.column()]

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])

    def openAction(self, row, column):
        print('test')

    def deleteSelected(self):
        print('test')

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole and index.column() == 2 and value != '':
            self._data[index.row()][index.column()] = value
            return True
        return False

    def replaceData(self, string, data):
        if string in self._keys:
            row = self._keys.index(string)
            if self._data[row][1] == data['base']:
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
