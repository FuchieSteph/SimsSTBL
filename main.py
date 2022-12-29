import sys
import PyQt6
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QDir, QSortFilterProxyModel, QThreadPool
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import QSettings

from app_actions import App_Actions
from libs.definitions import STATE_LIST
from libs.tables import TableModel
from qt_material import apply_stylesheet


class App(QMainWindow, App_Actions):
    APP_NAME = "map_view_demo.py"
    loaded = False

    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)  # forward to 'super' __init__()
        self.setWindowTitle("Sims 4 Mod Translator")

        ##PARAMETERS
        self.settings = self.initSettings()
        self.dirpath = self.settings.value("DatabasePath")
        self.sourcepath = self.settings.value("SourcePath")

        self.params = None
        self.proxy_model = None
        self.buttons = {}
        self.first_load = 1
        self.logs = []
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.initUI()

    def initSettings(self):
        settings = QSettings("SimsStbl", "settings")

        if settings.value("DatabasePath") == None:
            settings.setValue("DatabasePath", QDir().currentPath() + '/database')

        if settings.value("SourcePath") == None:
            settings.setValue("SourcePath", QDir().currentPath())

        return settings

    def createButton(self, frame, text, func):
        button = QtWidgets.QPushButton(frame)
        button.setText(text)
        button.clicked.connect(func)
        button.setObjectName(text)
        button.setStyleSheet("padding:10px")
        button.setProperty('class', 'big_button')

        self.left_container.addWidget(button)

    def createMenuElement(self, name, icon, text, shortcut, desc, action, menu, checkable=False, disabled=True):
        self.buttons[name] = QAction(QIcon(icon), text, self)

        if shortcut:
            self.buttons[name].setShortcut(shortcut)

        if checkable:
            self.buttons[name].setCheckable(True)

        if disabled:
            self.buttons[name].setDisabled(True)

        self.buttons[name].setStatusTip(desc)
        self.buttons[name].triggered.connect(action)
        self.buttons[name].setShortcut(QKeySequence(shortcut))

        menu.addAction(self.buttons[name])

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
                               self.fileMenu, False, False)

        self.createMenuElement('translatefolder', 'exit.png', '&Translate Folder', 'Shift+T',
                               'Translate a full folder automatically',
                               self.translate_folder,
                               self.fileMenu, False, False)

        self.createMenuElement('savetranslation', 'exit.png', '&Save Translation', 'Ctrl+S', 'Save Translation',
                               self.save_translation,
                               self.fileMenu)

        self.createMenuElement('loadtranslation', 'exit.png', '&Load Translation', 'Ctrl+L', 'Load Translation',
                               self.load_translation,
                               self.fileMenu)

        self.createMenuElement('exporttranslation', 'exit.png', '&Export CSV', 'Ctrl+T',
                               'Export translation to csv',
                               self.export_translation,
                               self.fileMenu)

        self.createMenuElement('exportpackage', 'exit.png', '&Export Package', 'Ctrl+E',
                               'Export translation to package',
                               self.export_package,
                               self.fileMenu)

        self.createMenuElement('exit', 'exit.png', '&Exit', 'Ctrl+Q',
                               'Exit',
                               self.close,
                               self.fileMenu, False, False)

        self.createMenuElement('settings', 'exit.png', '&Settings', 'Ctrl+Q', 'Settings',
                               self.update_settings,
                               self.settingsMenu, False, False)

        self.statusBar()

    def load_table(self, package):
        header = ['ID', 'Original Text', 'Translated Text', 'State']

        ##Table setup
        package.model = TableModel(package.DATA, header)
        self.table.setModel(package.model)
        self.table.horizontalHeader().setSectionResizeMode(0, PyQt6.QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, PyQt6.QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, PyQt6.QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, PyQt6.QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(PyQt6.QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested['QPoint'].connect(self.show_table_menu)

        if not package.isQuick:
            loadTranslation = self.checkDatabase()

            if loadTranslation:
                self.load_translation(loadTranslation)

            self.proxy_model = QSortFilterProxyModel()
            self.proxy_model.setFilterKeyColumn(3)

            self.proxy_model.setSourceModel(package.model)
            self.table.setModel(self.proxy_model)

            if not self.loaded:
                self.enableButtons()
                self.loaded = True

        self.setCentralWidget(self.centralwidget)

        if self.first_load == 1 and not package.isQuick:
            self.load_toolbar()
            self.first_load = 0

    def enableButtons(self):
        self.createButton(self.left_frame, "Load Translation", self.load_translation)
        self.createButton(self.left_frame, "Export Translation", self.export_translation)
        self.createButton(self.left_frame, "Export Package", self.export_package)

        for button in self.buttons:
            self.buttons[button].setDisabled(False)

    def load_toolbar(self):
        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)

        self.createMenuElement('fvalidated', None, 'Filter Validated', '', 'Filter Validated Strings',
                               self.filterValidate, toolbar,
                               True, False)
        self.createMenuElement('funvalidated', None, 'Filter UnValidated', '', 'Filter Unvalidated Strings',
                               self.filterUnvalidated,
                               toolbar, True, False)
        self.createMenuElement('funknown', None, 'Filter Unknown', '', 'Filter Unknown Strings',
                               self.filterUnknown,
                               toolbar, True, False)

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
        self.table.setFrameStyle(QtWidgets.QFrame.Shape(0x0004))
        self.right_container.addWidget(self.table)

        self.log_zone = QPlainTextEdit()
        self.log_zone.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.NoTextInteraction)
        self.log_zone.setMaximumHeight(200)

        self.right_container.addWidget(self.log_zone)

        self.write_logs('Waiting for a file...')
        self.main_grid.addWidget(self.right_frame, 0, 1, 1, 1)

        ## LOAD BUTTONS
        self.createButton(self.left_frame, "Load Package", self.load_package)

        self.main_grid.addWidget(self.left_frame, 0, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignTop)
        self.baseLayout.addLayout(self.main_grid)

        self.setCentralWidget(self.centralwidget)

    def write_logs(self, log=None, erase=False):
        if erase:
            self.logs = []

        if log is not None:
            self.logs.append(log)

        logs = self.logs[::-1]
        self.log_zone.setPlainText("\n".join(logs))

    def raiseMessage(self, message, informativeMessage, error):

        if error:
            self.messageBox = QtWidgets.QMessageBox.warning(self, "Error", message,
                                                            QMessageBox.StandardButton.Ok)

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
                    self.package.model.updateState(i.row(), state)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='light_blue.xml', invert_secondary=True)

    ex = App()

    sys.exit(app.exec())
