import json
import sys

import PyQt6
from PyQt6 import QtGui, QtWidgets, QtCore
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

from s4py.package import *

import csv
from libs.definitions import LANGS, LANG_LIST
from libs import helpers
from libs.stbl import StblReader
from libs.tables import TableModel, get_translation, map_to_json

import numpy as np


class App(QMainWindow):
    APP_NAME = "map_view_demo.py"
    loaded = False

    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)  # forward to 'super' __init__()

        self.DATA = {'keys': [], 'data': [], 'base': []}
        self.initUI()

    def createButton(self, frame, text, func):
        button = QtWidgets.QPushButton(frame)
        button.setText(text)
        button.clicked.connect(func)
        button.setObjectName(text)
        button.setStyleSheet("padding:10px")
        self.left_container.addWidget(button)

    def createMenuElement(self, icon, text, shortcut, desc, action, menu):
        loadAct = QAction(QIcon(icon), text, self)
        loadAct.setShortcut(shortcut)
        loadAct.setStatusTip(desc)
        loadAct.triggered.connect(action)
        menu.addAction(loadAct)

    def export_package(self):
        try:
            filename = self.filepath.replace('.package', '_' + self.lang + '.package')
        except:
            filename = "translation"

        export_path = QFileDialog.getSaveFileName(self, 'Open file', filename, "Package (*.package)")
        if export_path[0] == '':
            return

        dbfile2 = open_package(export_path[0], 'w')
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
        dbfile2.put(self.package.id, f.raw.getvalue())
        dbfile2.commit()
        f.close()

    def export_translation(self):
        try:
            filename = self.filepath.split('.')[0]
        except:
            filename = "translation"

        export_path = QFileDialog.getSaveFileName(self, 'Open file', filename + '.csv', "CSV (*.csv)")

        if export_path[0] == '':
            return

        with open(export_path[0], 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
            writer.writerow(['KEY', 'EN', 'FR'])
            writer.writerows(self.model._data)
            f.close()

    def initUI(self):
        self.load_menu()
        self.load_base_layout()
        self.load_ui()
        self.showMaximized()
        self.show()

    def load_base_layout(self):
        # DEFINE CENTRAL WIDGET
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)
        self.centralwidget.setAutoFillBackground(False)

        # SET BASE LAYOUT
        self.baseLayout = QtWidgets.QVBoxLayout(self.centralwidget)

        # CREATE MAIN GRID
        self.main_grid = QtWidgets.QGridLayout()
        self.main_grid.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMaximumSize)

        # RIGHT MENU
        self.right_frame = QtWidgets.QFrame(self.centralwidget)
        self.right_container = QtWidgets.QVBoxLayout(self.right_frame)

        # LEFT MENU
        self.left_frame = QtWidgets.QFrame(self.centralwidget)
        self.left_container = QtWidgets.QVBoxLayout(self.left_frame)
        self.left_container.setSpacing(6)

    def load_menu(self):
        menubar = self.menuBar()
        self.fileMenu = menubar.addMenu('&File')
        self.settingsMenu = menubar.addMenu('&Settings')

        self.createMenuElement('exit.png', '&Load Package', 'Ctrl+O', 'Load a package file', self.load_package,
                               self.fileMenu)

        self.createMenuElement('exit.png', '&Save Translation', 'Ctrl+S', 'Save Translation', self.save_translation,
                               self.fileMenu)

        self.createMenuElement('exit.png', '&Load Translation', 'Ctrl+S', 'Load Translation', self.load_translation,
                               self.fileMenu)

        self.createMenuElement('exit.png', '&Load Package', 'Ctrl+Q', 'Load a package file',
                               QApplication.instance().quit,
                               self.fileMenu)

        self.createMenuElement('exit.png', '&Settings', 'Ctrl+Q', 'Settings',
                               self.update_settings,
                               self.settingsMenu)

        self.statusBar()

    def load_package(self):
        self.filepath = QFileDialog.getOpenFileName(self, 'Open file', '', "Package sfiles (*.package)")[0]

        if self.filepath == '':
            return

        self.lang = QInputDialog.getItem(self, "select input dialog", "Select the lang", LANG_LIST, 5, False)[0]
        self.readPackage()

    def load_table(self):
        header = ['ID', 'Original Text', 'Translated Text', 'State']

        self.model = TableModel(self.DATA, header)
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(0, PyQt6.QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, PyQt6.QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, PyQt6.QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, PyQt6.QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(PyQt6.QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested['QPoint'].connect(self.show_table_menu)

        if not self.loaded:
            self.createButton(self.left_frame, "Load Translation", self.load_translation)
            self.createButton(self.left_frame, "Export Translation", self.export_translation)
            self.createButton(self.left_frame, "Export Package", self.export_package)
            self.loaded = True

        self.setCentralWidget(self.centralwidget)

    def load_translation(self):
        path = QFileDialog.getOpenFileName(self, 'Load Translation', '', "Json (*.json)")[0]

        if self.filepath == '':
            return

        with open(path, 'r') as f:
            data = json.load(f)
            try:
                for str in data['strings']:
                    self.model.replaceData(str['id'], str)
            except:
                self.raiseMessage('The file is invalid, please try with another file', '', 1)

    def load_ui(self):
        self.table = QtWidgets.QTableView(self.right_frame)
        self.right_container.addWidget(self.table)
        self.main_grid.addWidget(self.right_frame, 0, 1, 1, 1)

        ## LOAD BUTTONS
        self.createButton(self.left_frame, "Load Package", self.load_package)

        self.main_grid.addWidget(self.left_frame, 0, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignTop)
        self.baseLayout.addLayout(self.main_grid)

        self.setCentralWidget(self.centralwidget)

    def raiseMessage(self, message, informativeMessage, error):

        if error:
            self.messageBox = QtWidgets.QMessageBox.warning(self, "Error", message, QMessageBox.StandardButton.Ok)

        else:
            self.messageBox = QtWidgets.QMessageBox()
            self.messageBox.setText(message)

            if informativeMessage != '':
                self.messageBox.setInformativeText(informativeMessage)

            self.messageBox.setWindowTitle('Warning')
            self.messageBox.setIcon(QMessageBox.Icon.Warning)
            self.messageBox.addButton("Yes", QMessageBox.ButtonRole.YesRole)
            self.messageBox.addButton("No", QMessageBox.ButtonRole.NoRole)

        return self.messageBox.exec()

    def readPackage(self):
        dbfile = open_package(self.filepath)
        match = False

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
            current_lang = list(LANGS.keys())[list(LANGS.values()).index(lang)]
            stbl_reader = StblReader(content, self.DATA, lang == LANGS[self.lang])
            self.DATA = stbl_reader.readStbl()

            self.package = idx

        if not match:
            choice = self.raiseMessage('This package doesn\'t contain the following strings : ' + self.lang,
                                       'Would you like to copy the English strings ?', 0)

            stbl_reader = StblReader(None, self.DATA, None)
            self.DATA = stbl_reader.loadEmptyStrings(choice)

        self.load_table()

    def show_table_menu(self, pos):
        if self.table.selectionModel().selection().indexes():
            menu = QMenu()
            validateAction = menu.addAction("Set strings as Validated")
            unvalidatedAction = menu.addAction("Set strings as Unvalidated")
            revisionAction = menu.addAction("Set strings as Revision")
            state = -1

            action = menu.exec(self.mapToGlobal(pos))

            if action == validateAction:
                state = 2

            elif action == unvalidatedAction:
                state = 0

            elif action == revisionAction:
                state = 1

            if state > -1:
                for i in self.table.selectionModel().selectedRows():
                    self.model.updateState(i.row(), state)

    def save_translation(self):
        try:
            filename = self.filepath.split('.')[0]
        except:
            filename = "translation"

        export_path = QFileDialog.getSaveFileName(self, 'Save file', filename + '_' + self.lang + '.json',
                                                  "JSON (*.json)")

        if export_path[0] == '':
            return

        with open(export_path[0], 'w', newline='', encoding='utf-8') as f:
            data = {'lang': self.lang, 'strings': list(map(map_to_json, self.model._data))}
            f.seek(0)
            json.dump(data, f, sort_keys=True, indent=4)
            f.close()

    def update_settings(self):
        TestQFileDialog = QDialog()

        self.toolButtonOpenDialog = QToolButton(TestQFileDialog)

        self.lineEdit = QLineEdit(TestQFileDialog)
        self.lineEdit.setEnabled(False)

        QtCore.QMetaObject.connectSlotsByName(TestQFileDialog)


class SettingsWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel("Another Window")
        layout.addWidget(self.label)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec())
