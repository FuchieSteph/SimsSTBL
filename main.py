import sys
import PyQt6
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QDir, QItemSelection, QSortFilterProxyModel, QThreadPool
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import QSettings

from classes.app_actions import App_Actions
from helpers.definitions import *
from classes.tables import CustomQTableView, TableModel
from qt_material import apply_stylesheet


class App(QMainWindow, App_Actions):
    APP_NAME = "map_view_demo.py"
    loaded = False

    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)  # forward to 'super' __init__()
        self.setWindowTitle("Sims 4 Mod Translator")

        ##PARAMETERS
        self.settings = self.init_settings()
        self.dirpath = self.settings.value("DatabasePath")
        self.sourcepath = self.settings.value("SourcePath")

        self.params = None
        self.search = None
        self.proxy_model = None
        self.buttons = {}
        self.menus = {}
        self.first_load = 1
        self.logs = []
        self.threadpool = QThreadPool()

        self.load_ui()

    def createButton(self, frame, text, func):
        button = QtWidgets.QPushButton(frame)
        button.setText(text)
        button.clicked.connect(func)
        button.setObjectName(text)
        button.setProperty('class', 'big_button')

        self.left_container.addWidget(button)

    def createMenuElement(self, name, icon, text, shortcut, desc, action, menu, checkable=False, disabled=True):
        menu = self.menus[menu]

        if action == None:
            self.menus[name + 'Menu'] = menu.addMenu(text)

        else:
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

    def enableButtons(self):
        self.createButton(self.left_frame, "Load Translation", self.load_translation)
        self.createButton(self.left_frame, "Export Translation", self.export_csv)
        self.createButton(self.left_frame, "Export Package", self.export_package)

        for button in self.buttons:
            self.buttons[button].setDisabled(False)

    def start_editing(self):
        index = (self.table.selectionModel().currentIndex())
        self.table.setCurrentIndex(index)
        self.table.edit(index)

    def init_settings(self):
        settings = QSettings("SimsStbl", "settings")

        if settings.value("DatabasePath") == None:
            settings.setValue("DatabasePath", QDir().currentPath() + '/database')

        if settings.value("SourcePath") == None:
            settings.setValue("SourcePath", QDir().currentPath())

        return settings

    def load_ui(self):
        self.load_menu()
        self.load_base_layout()
        self.showMaximized()
        self.show()
        self.write_logs('Waiting for a file...')

    def load_base_layout(self):
        # DEFINE CENTRAL WIDGET
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)
        self.centralwidget.setAutoFillBackground(True)

        # SET BASE LAYOUT
        self.baseLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.baseLayout.setSpacing(0)
        self.baseLayout.setContentsMargins(0, 0, 0, 0)

        # CREATE MAIN GRID
        self.main_grid = QtWidgets.QHBoxLayout()
        self.main_grid.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMaximumSize)

        # LEFT BLOCK
        self.left_frame = QtWidgets.QFrame(self.centralwidget)
        self.left_frame.setProperty('class', 'menu')
        self.left_container = QtWidgets.QVBoxLayout(self.left_frame)
        self.left_container.setSpacing(6)
        self.left_container.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        # RIGHT BLOCK
        self.right_frame = QtWidgets.QFrame(self.centralwidget)
        self.right_frame.setProperty('class', 'container')
        self.right_container = QtWidgets.QVBoxLayout(self.right_frame)

        self.table = CustomQTableView()
        self.table.setFrameStyle(QtWidgets.QFrame.Shape(0x0001))
        self.table.setAlternatingRowColors(True)
        self.table.signal_up.connect(lambda: self.arrowkey(-1))
        self.table.signal_down.connect(lambda: self.arrowkey(1))
        self.table.signal.connect(lambda: self.arrowkey(1))
        self.table.signal_key.connect(self.start_editing)

        self.right_container.addWidget(self.table)
        self.right_container.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        # BOTTOM LAYOUT
        self.bottom_zone = QGridLayout()

        self.log_zone = QPlainTextEdit()
        self.log_zone.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.NoTextInteraction)
        self.log_zone.setMaximumHeight(200)
        self.log_zone.setProperty('class', 'disabled')

        self.base_zone = QPlainTextEdit()
        self.base_zone.setMaximumHeight(200)
        self.base_zone.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.NoTextInteraction)
        self.base_zone.setProperty('class', 'disabled')

        self.translate_zone = QPlainTextEdit()
        self.translate_zone.setMaximumHeight(200)
        self.translate_zone.textChanged.connect(self.update_data)

        self.label_logs = QLabel("Logs")
        self.label_base = QLabel("Original")
        self.label_translation = QLabel("Translation")

        self.label_logs.setMaximumHeight(20)
        self.label_base.setMaximumHeight(20)
        self.label_translation.setMaximumHeight(20)

        self.bottom_zone.addWidget(self.label_base, 0, 0)
        self.bottom_zone.addWidget(self.label_translation, 0, 1)

        self.bottom_zone.addWidget(self.base_zone, 1, 0)
        self.bottom_zone.addWidget(self.translate_zone, 1, 1)

        self.right_container.addLayout(self.bottom_zone)
        self.right_container.addWidget(self.label_logs)
        self.right_container.addWidget(self.log_zone)

        ## LOAD BUTTONS
        self.createButton(self.left_frame, "Load Package", self.load_package)

        self.main_grid.addWidget(self.left_frame)
        self.baseLayout.addLayout(self.main_grid)

        self.main_grid.addWidget(self.right_frame)
        self.setCentralWidget(self.centralwidget)

    def arrowkey(self, num):
        try:
            self.table_select = self.table.selectionModel()
            selection = QItemSelection()

            index = (self.table.selectionModel().currentIndex())
            value = index.sibling(index.row(), index.column()).data()
            current_row = index.row()
            current_collumn = index.column()

            model = self.package.model  # get data model for indexes.

            if (current_row == 0 and num == -1) or (num == 1 and current_row == len(self.package.model._data) - 1):
                return

            model_index = self.package.model.index(current_row + num, current_collumn)

            mode = QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect
            self.table_select.setCurrentIndex(model_index, mode)
            self.table_select.select(model_index, mode)

            self.print_selection()
        except UnboundLocalError:
            pass

    def load_menu(self):
        menubar = self.menuBar()
        self.menus['fileMenu'] = menubar.addMenu('&File')
        self.menus['translationsMenu'] = menubar.addMenu('&Translation')
        self.menus['settingsMenu'] = menubar.addMenu('&Settings')

        self.createMenuElement('loadpackage', 'exit.png', '&Load Package', 'Ctrl+O', 'Open package',
                               self.load_package,
                               'fileMenu', False, False)

        self.createMenuElement('translatefolder', 'exit.png', '&Translate Folder with Google Translate', '',
                               'Translate a full folder automatically',
                               self.translate_folder,
                               'fileMenu')

        self.createMenuElement('savetranslation', 'exit.png', '&Save Translation', 'Ctrl+S', 'Save Translation',
                               self.save_translation,
                               'fileMenu')

        self.createMenuElement('savetranslationas', 'exit.png', '&Save Translation as...', '',
                               'Save Translation as...',
                               self.save_translation_as,
                               'fileMenu')

        self.createMenuElement('translate', 'exit.png', '&Translate with Google translate', '',
                               'Translate with Google Translate',
                               self.translate_google,
                               'translationsMenu', False, False)

        self.createMenuElement('search', 'exit.png', '&Search and Replace', 'Ctrl+F', 'Search and replace',
                               self.search_replace,
                               'fileMenu')

        self.createMenuElement('import', 'exit.png', '&Load Translation', '',
                               'Import', None, 'fileMenu')

        self.createMenuElement('loadtranslation', 'exit.png', '&Load save', '', 'Load Save',
                               self.load_translation,
                               'importMenu')

        self.createMenuElement('loadcsv', 'exit.png', '&Load CSV', '', 'Load CSV',
                               self.import_csv,
                               'importMenu')

        self.createMenuElement('loadpackage', 'exit.png', '&Load from Package', '',
                               'Load translation from Package',
                               self.load_from_package,
                               'importMenu')

        self.createMenuElement('export', 'exit.png', '&Export', '',
                               'Export', None, 'fileMenu')

        self.createMenuElement('exporttranslation', 'exit.png', '&Export to CSV', '',
                               'Export to Csv',
                               self.export_csv,
                               'exportMenu')

        self.createMenuElement('exportpackage', 'exit.png', '&Save Package', '',
                               'Save package',
                               self.export_replace_package,
                               'exportMenu')

        self.createMenuElement('exportseparate', 'exit.png', '&Export to a separate package', '',
                               'Export to a separate package',
                               self.export_package,
                               'exportMenu')

        self.createMenuElement('exit', 'exit.png', '&Exit', 'Ctrl+Q',
                               'Exit',
                               self.close,
                               'fileMenu', False, False)

        self.createMenuElement('settings', 'exit.png', '&Settings', 'Ctrl+Q', 'Settings',
                               self.update_settings,
                               'settingsMenu', False, False)

        self.statusBar()

    def load_table(self, package):
        header = ['ID', 'ID', 'Instance', 'Original Text', 'Translated Text', 'State']

        ##Table setup
        package.model = TableModel(package.DATA, header)

        self.table.setModel(package.model)
        self.table.horizontalHeader().setSectionResizeMode(0, PyQt6.QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, PyQt6.QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, PyQt6.QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, PyQt6.QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, PyQt6.QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, PyQt6.QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.setColumnHidden(1, True)

        self.table.setSelectionBehavior(PyQt6.QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems)
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested['QPoint'].connect(self.show_table_menu)

        self.table.clicked.connect(self.print_selection)
        self.table.selectionModel().currentChanged.connect(self.print_selection)

        if not package.isQuick:
            loadTranslation = self.checkDatabase()

            if loadTranslation:
                self.load_translation(loadTranslation)
                self.package.database_path = loadTranslation

            self.proxy_model = QSortFilterProxyModel()
            self.proxy_model.setFilterKeyColumn(STATE_INDEX)

            self.proxy_model.setSourceModel(package.model)
            self.table.setModel(self.proxy_model)

            if not self.loaded:
                self.enableButtons()
                self.loaded = True

        self.setCentralWidget(self.centralwidget)

        if self.first_load == 1 and not package.isQuick:
            self.load_toolbar()
            self.first_load = 0

    def print_selection(self):
        index = (self.table.selectionModel().currentIndex())

        value = index.sibling(index.row(), index.column()).data()
        row = self.package.model._data[index.row()]

        self.base_zone.setPlainText(row[BASE_INDEX])
        self.translate_zone.setPlainText(row[TRANSLATION_INDEX])

    def update_data(self):
        index = (self.table.selectionModel().currentIndex())
        text = self.translate_zone.toPlainText()

        if text != self.package.model._data[index.row()][TRANSLATION_INDEX]:
            self.package.model._data[index.row()][TRANSLATION_INDEX] = text
            self.package.model._data[index.row()][STATE_INDEX] = TO_VALIDATE_STATE

    def load_toolbar(self):
        self.menus['toolbarMenu'] = QToolBar("My main toolbar")

        self.addToolBar(self.menus['toolbarMenu'])

        self.createMenuElement('fvalidated', None, 'Validated', '', 'Validated',
                               self.filterValidate, 'toolbarMenu',
                               True, False)
        self.createMenuElement('funvalidated', None, 'To be checked', '', 'To be checked',
                               self.filterUnvalidated,
                               'toolbarMenu', True, False)
        self.createMenuElement('funknown', None, 'No state', '', 'No state',
                               self.filterUnknown,
                               'toolbarMenu', True, False)

    def filterValidate(self, action):
        if not self.buttons['fvalidated'].isChecked():
            self.proxy_model.setFilterFixedString('')

        else:
            self.proxy_model.setFilterFixedString(STATE_LIST[VALIDATED_STATE])

    def filterUnknown(self, action):
        if not self.buttons['funknown'].isChecked():
            self.proxy_model.setFilterFixedString('')

        else:
            self.proxy_model.setFilterFixedString(STATE_LIST[NO_STATE])

    def filterUnvalidated(self, action):
        if not self.buttons['funvalidated'].isChecked():
            self.proxy_model.setFilterFixedString('')

        else:
            self.proxy_model.setFilterFixedString(STATE_LIST[TO_VALIDATE_STATE])

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
    apply_stylesheet(app, theme='theme.xml', invert_secondary=True, css_file='styles.css')
    ex = App()

    sys.exit(app.exec())
