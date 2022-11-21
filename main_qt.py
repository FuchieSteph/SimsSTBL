import json
import sys

import PyQt6
from PyQt6 import QtGui, QtWidgets, QtCore
from PyQt6.QtCore import QDir, QFile, QFileInfo, QSortFilterProxyModel
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


class App(QMainWindow):
    APP_NAME = "map_view_demo.py"
    loaded = False

    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)  # forward to 'super' __init__()
        self.setWindowTitle("Sims 4 Mod Translator")

        self.DATA = {'keys': [], 'data': [], 'base': []}
        self.settings = self.initSettings()
        self.dirpath = self.settings.value("DatabasePath")
        self.filepath = None
        self.params = None
        self.proxy_model = None
        self.buttons = {}

        self.initUI()

    def initSettings(self):
        settings = QSettings("SimsStbl", "settings")

        if settings.value("DatabasePath") == None:
            settings.setValue("DatabasePath", QDir().currentPath() + '/database')

        return settings

    def checkDatabase(self):
        filename = QFileInfo(self.filepath).fileName().split('.')[0]

        if os.path.exists(self.dirpath + '/' + filename + '_' + self.lang + '.json'):
            choice = self.raiseMessage('A translation was detected in the database : ',
                                       'Would you like to load it ?', 0)

            if choice == 0:
                return False

            return self.dirpath + '/' + filename + '_' + self.lang + '.json'

        else:
            return False

    def createButton(self, frame, text, func):
        button = QtWidgets.QPushButton(frame)
        button.setText(text)
        button.clicked.connect(func)
        button.setObjectName(text)
        button.setStyleSheet("padding:10px")
        self.left_container.addWidget(button)

    def createMenuElement(self, name, icon, text, shortcut, desc, action, menu, checkable=False):
        self.buttons[name] = QAction(QIcon(icon), text, self)

        if shortcut:
            self.buttons[name].setShortcut(shortcut)

        if checkable:
            self.buttons[name].setCheckable(True)

        self.buttons[name].setStatusTip(desc)
        self.buttons[name].triggered.connect(action)
        menu.addAction(self.buttons[name])

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

        self.createMenuElement('loadpackage', 'exit.png', '&Load Package', 'Ctrl+O', 'Load a package file',
                               self.load_package,
                               self.fileMenu)

        self.createMenuElement('savetranslation', 'exit.png', '&Save Translation', 'Ctrl+S', 'Save Translation',
                               self.save_translation,
                               self.fileMenu)

        self.createMenuElement('loadtranslation', 'exit.png', '&Load Translation', 'Ctrl+S', 'Load Translation',
                               self.load_translation,
                               self.fileMenu)

        self.createMenuElement('loadpackage', 'exit.png', '&Load Package', 'Ctrl+Q', 'Load a package file',
                               QApplication.instance().quit,
                               self.fileMenu)

        self.createMenuElement('settings', 'exit.png', '&Settings', 'Ctrl+Q', 'Settings',
                               self.update_settings,
                               self.settingsMenu)

        self.statusBar()

    def load_package(self):
        self.filepath = QFileDialog.getOpenFileName(self, 'Open file', '', "Packages files (*.package)")[0]

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

        loadTranslation = self.checkDatabase()

        if loadTranslation:
            self.load_translation(loadTranslation)

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setFilterKeyColumn(3)

        self.proxy_model.setSourceModel(self.model)
        self.table.setModel(self.proxy_model)

        if not self.loaded:
            self.createButton(self.left_frame, "Load Translation", self.load_translation)
            self.createButton(self.left_frame, "Export Translation", self.export_translation)
            self.createButton(self.left_frame, "Export Package", self.export_package)
            self.loaded = True

        self.setCentralWidget(self.centralwidget)
        self.load_toolbar()

    def load_translation(self, path=None):
        if path is None:
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

    def load_toolbar(self):
        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)

        self.createMenuElement('fvalidated', None, 'Filter Validated', '', 'Filter Validated Strings',
                               self.filterValidate, toolbar,
                               True)
        self.createMenuElement('funvalidated', None, 'Filter UnValidated', '', 'Filter Unvalidated Strings',
                               self.filterUnvalidated,
                               toolbar, True)
        self.createMenuElement('funknown', None, 'Filter Unknown', '', 'Filter Unknown Strings', self.filterUnknown,
                               toolbar, True)

    def filterValidate(self, action):
        if not self.buttons['fvalidated'].isChecked():
            self.proxy_model.setFilterFixedString('')

        else:
            self.proxy_model.setFilterFixedString(STATE_LIST[2])

    def filterUnknown(self, action):
        if not self.buttons['funknown'].isChecked():
            self.proxy_model.setFilterFixedString('')

        else:
            self.proxy_model.setFilterFixedString(STATE_LIST[1])

    def filterUnvalidated(self, action):
        if not self.buttons['funvalidated'].isChecked():
            self.proxy_model.setFilterFixedString('')

        else:
            self.proxy_model.setFilterFixedString(STATE_LIST[0])

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
            self.messageBox.addButton("No", QMessageBox.ButtonRole.NoRole)
            self.messageBox.addButton("Yes", QMessageBox.ButtonRole.YesRole)

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
        if self.params is None:
            self.params = SettingsWindow()
        self.params.show()


class SettingsWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """

    def __init__(self):
        super().__init__()
        self.settings = QSettings("SimsStbl", "settings")
        self.initUi()

    def initUi(self):
        layout = QVBoxLayout()
        self.resize(602, 100)

        ##VERTICAL LAYOUT
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(9, 0, -1, 9)

        ##LABEL
        self.label = QtWidgets.QLabel(self)
        self.label.setText('Translations directory')
        self.verticalLayout.addWidget(self.label)

        ##HORIZONTAL LAYOUT
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(0, 0, -1, 9)

        self.lineEdit = QtWidgets.QLineEdit(self)
        self.lineEdit.setText(self.settings.value("DatabasePath"))

        self.horizontalLayout.addWidget(self.lineEdit)
        self.browseButton = QtWidgets.QToolButton(self)
        self.browseButton.clicked.connect(self.setDirectory)
        self.browseButton.setText('...')
        self.horizontalLayout.addWidget(self.browseButton)

        self.verticalLayout.addLayout(self.horizontalLayout)

        ##BUTTON BOX
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Save)
        self.buttonBox.clicked.connect(self.close)

        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

    def setDirectory(self):
        self.dirpath = QFileDialog.getExistingDirectory(self, 'Open file', self.settings.value("DatabasePath"))

        if self.dirpath != '':
            self.lineEdit.setText(self.dirpath)

        self.settings.setValue("DatabasePath", self.dirpath)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Material')
    ex = App()

    sys.exit(app.exec())
