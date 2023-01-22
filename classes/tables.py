import PyQt6
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtGui import QColor
from PyQt6.QtCore import *

from helpers.definitions import *


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, header):
        super(TableModel, self).__init__()
        self._data = data
        self._header = header

    def rowCount(self, index=None):
        return len(self._data)

    def columnCount(self, index=None):
        if self.rowCount() == 0:
            return 0

        else:
            return len(self._data[0])

    def headerData(self, col, orientation, role):
        # section is the index of the column/row.
        if orientation == PyQt6.QtCore.Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._header[col]

        elif orientation == PyQt6.QtCore.Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return col + 1

        return None

    def search_position(self, data):
        def filter_data(v):
            if v[KEY_INDEX] == data['id'] and (
                    v[BASE_INDEX] == data['base'] or data['base'] is None or v[BASE_INDEX] == v[TRANSLATION_INDEX]):
                return True
            elif v[BASE_INDEX] == data['base']:
                return True
            else:
                return False

        result = list(filter(filter_data, self._data))

        return map(lambda x: self._data.index(x), result) if len(result) > 0 else None

    def search(self, string):
        result = list(filter(lambda x: string in x[TRANSLATION_INDEX], self._data))
        return map(lambda x: self._data.index(x), result) if len(result) > 0 else None

    def data(self, index, role):

        row = self._data[index.row()]
        cell = row[index.column()]

        if role == Qt.ItemDataRole.BackgroundRole:

            # print(row)

            if row[STATE_INDEX] == VALIDATED_STATE:
                return QVariant(QColor.fromRgb(44, 165, 141))
            elif row[STATE_INDEX] == TO_VALIDATE_STATE:
                return QVariant(QColor.fromRgb(244, 97, 151))
            elif row[STATE_INDEX] == AUTO_STATE:
                return QVariant(QColor.fromRgb(237, 221, 212))

        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == STATE_INDEX:
                return STATE_LIST[cell]

            return cell

        if role == Qt.ItemDataRole.EditRole:
            return cell

    def setData(self, index, value, role):

        base = self._data[index.row()][BASE_INDEX]

        if role == Qt.ItemDataRole.EditRole and index.column() == TRANSLATION_INDEX and value != '':
            indexes = self.search_position({'id': None, 'base': base})

            if indexes is not None:
                for key in indexes:
                    if key != index.row() and self._data[key][STATE_INDEX] == VALIDATED_STATE:
                        continue

                    self._data[key][index.column()] = value

                    if key == index.row():
                        self._data[key][STATE_INDEX] = TO_VALIDATE_STATE
                    else:
                        self._data[key][STATE_INDEX] = AUTO_STATE

            return True
        return False

    def search_replace(self, search, replace):
        matches = self.search(search)
        i = 0
        if matches is not None:
            i = i + 1
            for index in matches:
                self._data[index][TRANSLATION_INDEX] = self._data[index][TRANSLATION_INDEX].replace(search, replace)
                self._data[index][STATE_INDEX] = TO_VALIDATE_STATE

        return i if matches is not None else 0

    def replaceData(self, string, data):
        indexes = self.search_position(data)

        if indexes is not None:
            for index in indexes:
                self._data[index][TRANSLATION_INDEX] = data['translation']
                self._data[index][STATE_INDEX] = data['state']

    def updateState(self, row, state):
        self._data[row][STATE_INDEX] = state

    def resetTranslation(self, row):
        self._data[row][TRANSLATION_INDEX] = self._data[row][BASE_INDEX]
        self._data[row][STATE_INDEX] = NO_STATE

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable


def get_translation(n):
    return n[TRANSLATION_INDEX]


def map_to_json(n):
    return {"id": n[KEY_INDEX], 'instance': n[INSTANCE_INDEX], 'base': n[BASE_INDEX],
            'translation': n[TRANSLATION_INDEX], 'state': n[STATE_INDEX]}


class MyProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filters = dict()

    @property
    def filters(self):
        return self._filters

    def setFilter(self, expresion, column, erase=True):

        if not column in self.filters or erase:
            self.filters[column] = []

        if expresion:
            self.filters[column].append(expresion.lower())

        self.invalidateFilter()

    def clearFilters(self, column):
        ignore = [STATE_INDEX, INSTANCE_INDEX, FILENAME_INDEX]
        for key, regexes in list(self.filters.items()):
            if key not in ignore:
                del self.filters[key]

        self.invalidateFilter()

    def removeFilter(self, expresion, column):
        if expresion is not None:
            index = self.filters[column].index(expresion.lower())
            del self.filters[column][index]

            if len(self.filters[column]) == 0:
                del self.filters[column]

        else:
            try:
                print(self.filters)
                del self.filters[column]
            except:
                pass

        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):

        for key, regexes in self.filters.items():
            ix = self.sourceModel().index(source_row, key, source_parent)
            if ix.isValid():
                text = self.sourceModel().data(ix, QtCore.Qt.ItemDataRole.DisplayRole)
                match = False

                if len(regexes) == 0:
                    return True

                for regex in regexes:
                    if regex in text.lower():
                        match = True

                if not match:
                    return False

        return True


class CustomQTableView(QtWidgets.QTableView):
    signal_enter = QtCore.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        QtWidgets.QTableView.__init__(self, *args, **kwargs)
        self.ScrollHint(QtWidgets.QAbstractItemView.ScrollHint.EnsureVisible)

    def keyPressEvent(self, event):
        super(QtWidgets.QTableView, self).keyPressEvent(event)

        if event.key() == QtCore.Qt.Key.Key_Return:
            self.signal_enter.emit(1)

        elif event.key() == QtCore.Qt.Key.Key_Up or event.key() == QtCore.Qt.Key.Key_Down:
            self.signal_enter.emit(0)
