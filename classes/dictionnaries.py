import json
import os

from PyQt6 import QtGui, QtWidgets, QtCore
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QSettings, pyqtSignal, Qt

from classes.tables import CustomQTableView, TableModel
from helpers.definitions import INSTANCE_INDEX
from helpers.helpers import relative_path


class DictionnariesWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    submitClicked = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.initUi()
        self.db = {}

    def getDictionnaries(self):
        for file in os.listdir(relative_path("database")):
            if file.endswith('json'):
                self.dictionnary.addItem(file)

    def initUi(self):
        form_layout = QtWidgets.QFormLayout(self)
        self.setLayout(form_layout)

        self.resize(1000, 500)
        self.setWindowTitle("Search in dictionnaries")

        ##DICTIONNARY
        self.dictionnary = QComboBox()
        self.getDictionnaries()

        ##LABEL
        self.search_field = QLineEdit(self)
        self.search_field.textChanged.connect(self.search)

        form_layout.addRow('Dictionnary', self.dictionnary)
        form_layout.addRow('Search', self.search_field)

        self.table = CustomQTableView()
        self.table.setFrameStyle(QtWidgets.QFrame.Shape(0x0001))
        self.table.setAlternatingRowColors(True)

        form_layout.addRow(self.table)

    def search(self):

        search = self.search_field.text()

        if self.dictionnary.currentText() not in self.db:
            with open(relative_path("database") + '/' + self.dictionnary.currentText()) as db_file:
                file_contents = db_file.read()
                self.db[self.dictionnary.currentText()] = json.loads(file_contents)

        matches = list(filter(lambda x: search in x['base'], self.db[self.dictionnary.currentText()]['strings']))

        if len(matches) > 0:
            data = []

            for match in matches:
                base = match['base']
                translation = match['translation']
                d = [base, translation]
                data.append(d)

        else:
            data = [['No result', 'No result']]

        model = SimpleTableModel(data, ['Base', 'Translation'])

        self.table.setModel(model)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)


class SimpleTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, header):
        super(SimpleTableModel, self).__init__()
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
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._header[col]

        elif orientation == Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return col + 1

        return None

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
