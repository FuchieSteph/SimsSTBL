import sys
import PyQt6
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QDir, QThreadPool
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import QSettings

from classes.app_actions import App_Actions
from classes.package import Package
from helpers.definitions import *
from classes.tables import CustomQTableView, TableModel, MyProxyModel
from helpers.helpers import relative_path


class App(QMainWindow, App_Actions):
    APP_NAME = "map_view_demo.py"
    loaded = False

    def __init__(self, *args, **kwargs):
        """
        The __init__ function is called when an instance of the class is created. 
        It initializes variables that are common to all instances of the class, and it 
        is used to pass parameters into the object. The __init__ function also creates 
        the layout for each instance of a class.
        
        :param self: Refer to the object instance itself
        :param *args: Pass a non-keyworded, variable-length argument list
        :param **kwargs: Pass a variable number of keyword arguments to a function
        :return: None
        :doc-author: Trelent
        """
        super(App, self).__init__(*args, **kwargs)  # forward to 'super' __init__()
        self.setWindowTitle("Sims 4 Mod Translator")

        ##PARAMETERS
        self.settings = self.init_settings()
        self.dirpath = self.settings.value("DatabasePath")
        self.sourcepath = self.settings.value("SourcePath")
        self.dbfolder = relative_path("database")

        self.params = None
        self.search = None
        self.search_dict_w = None
        self.proxy_model = None
        self.buttons = {}
        self.menus = {}
        self.first_load = 1
        self.table = None
        self.logs = []
        self.threadpool = QThreadPool()
        self.visible = False
        self.load_ui()

        for arg in sys.argv:
            if arg.endswith(".package"):
                self.load_package(arg)

    def createButton(self, frame, text, func):
        """
        The createButton function creates a button with the given text and function.
        It is added to the left_container of the main window.
        
        :param self: Access the class attributes and methods
        :param frame: Specify the frame that the button will be placed in
        :param text: Set the text of the button
        :param func: Pass the function that is called when the button is pressed
        :return: A qpushbutton object
        :doc-author: Trelent
        """
        button = QtWidgets.QPushButton(frame)
        button.setText(text)
        button.clicked.connect(func)
        button.setObjectName(text)
        button.setProperty('class', 'big_button')

        self.left_container.addWidget(button)

    def createMenuElement(self, name, icon, text, shortcut, desc, action, menu, checkable=False, disabled=True,
                          separator=False):
        """
        The createMenuElement function creates a menu element in the GUI.
        It takes as input the name of the menu element, its icon, text, shortcut key (if any), description (for status bar), 
        the action to be performed when clicked and which menu it should be added to. It returns nothing.
        
        :param self: Access the class attributes
        :param name: Create a unique name for the button
        :param icon: Specify the icon to be displayed in the menu
        :param text: Set the text of the menu item
        :param shortcut: Set a keyboard shortcut for the menu item
        :param desc: Describe the action of the button
        :param action: Pass the function that is called when the button is clicked
        :param menu: Specify which menu the action should be added to
        :param checkable: Determine if the button is checkable or not
        :param disabled: Disable the menu element
        :return: A qaction object
        :doc-author: Trelent
        """
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

            if separator:
                menu.addSeparator()

    def enableButtons(self):
        """
        The enableButtons function enables the buttons in the left frame of the GUI.
        
        
        :param self: Access the class object
        :return: A dictionary of all the buttons in the gui
        :doc-author: Trelent
        """
        self.createButton(self.left_frame, "Load Translation", self.load_translation)
        self.createButton(self.left_frame, "Export Translation", self.export_csv)
        self.createButton(self.left_frame, "Export Package", self.export_package)

        for button in self.buttons:
            self.buttons[button].setDisabled(False)

    def init_settings(self):
        """
        The init_settings function initializes the settings object with default values if they are not already set.
        The function returns a QSettings object that can be used to access the settings.
        
        :param self: Refer to the object itself
        :return: The settings object
        :doc-author: Trelent
        """
        settings = QSettings("SimsStbl", "settings")

        if settings.value("DatabasePath") == None:
            settings.setValue("DatabasePath", QDir().currentPath() + '/database')

        if settings.value("SourcePath") == None:
            settings.setValue("SourcePath", QDir().currentPath())

        return settings

    def load_ui(self):
        """
        The load_ui function loads the menu and base layout of the application.
        It also maximizes the window and shows it to the user.
        
        :param self: Access the attributes and methods of the class in python
        :return: A qmainwindow object
        :doc-author: Trelent
        """
        self.load_menu()
        self.load_base_layout()
        self.showMaximized()
        self.show()
        self.write_logs('Waiting for a file...')

    def load_base_layout(self):
        """
        The load_base_layout function creates the base layout of the application.
        It is called in __init__ and contains all of the widgets that are used throughout
        the program.
        
        :param self: Access the variables and methods of the class
        :return: The main_grid layout, which is the central widget
        :doc-author: Trelent
        """
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
        self.table.signal_enter.connect(self.arrowkey)

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

    def initTable(self):
        package = Package('', '', True, True, [[], []])
        self.package.model = self.load_table(package)

    def arrowkey(self, num):
        """
        The arrowkey function is used to navigate between the rows of the table.
        The function takes in a number, which corresponds to either - 1 or + 1. 
        This allows for navigation up and down through the table using arrow keys.
        
        :param self: Reference the object instance of the class
        :param num: Determine whether the function should move up or down
        :return: The value of the selected cell
        :doc-author: Trelent
        """
        try:
            if num != 0:
                index = (self.table.selectionModel().currentIndex())
                value = index.sibling(index.row(), index.column()).data()
                current_row = index.row()

                if (current_row == 0 and num == -1) or (num == 1 and current_row == len(self.package.model._data) - 1):
                    return

                self.table.clearSelection()
                self.table.selectRow(current_row + num)

                model_index = index.sibling(current_row + num, TRANSLATION_INDEX)
                self.table.setCurrentIndex(model_index)

            self.print_selection()

            return

        except UnboundLocalError:
            pass

    def load_menu(self):
        """
        The load_menu function creates the file menu and adds it to the menubar.
        It also creates all of the elements that are in this menu, including their callbacks.
        
        :param self: Access the attributes and methods of the class in python
        :return: The menu bar
        :doc-author: Trelent
        """
        menubar = self.menuBar()
        self.menus['fileMenu'] = menubar.addMenu('&File')
        self.menus['translationsMenu'] = menubar.addMenu('&Translation')
        self.menus['settingsMenu'] = menubar.addMenu('&Settings')

        self.createMenuElement('loadpackage', 'exit.png', '&Load Package', 'Ctrl+O', 'Open package',
                               self.load_package,
                               'fileMenu', False, False)

        self.createMenuElement('openfolder', 'exit.png', '&Open folder', '',
                               'Open folder',
                               self.open_folder,
                               'fileMenu', False, False, True)

        self.createMenuElement('import', 'exit.png', '&Load Translation', '',
                               'Import', None, 'fileMenu')

        self.createMenuElement('savetranslation', 'exit.png', '&Save Translation', 'Ctrl+S', 'Save Translation',
                               self.save_translation,
                               'fileMenu')

        self.createMenuElement('savetranslationas', 'exit.png', '&Save Translation as...', '',
                               'Save Translation as...',
                               self.save_translation_as,
                               'fileMenu', True, False, True)

        self.createMenuElement('search', 'exit.png', '&Search and Replace', 'Ctrl+F', 'Search and replace',
                               self.search_replace,
                               'fileMenu')

        self.createMenuElement('search_dict', 'exit.png', '&Search in dictionnaries', '',
                               'Search in dictionnaries',
                               self.search_dict,
                               'fileMenu', False, False, True)

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

        self.createMenuElement('exportpackage', 'exit.png', '&Save package', '',
                               'Save package',
                               self.export_replace_package,
                               'exportMenu')

        self.createMenuElement('exportseparate', 'exit.png', '&Save as a separate package', '',
                               'Export to a separate package',
                               self.export_package,
                               'exportMenu')

        self.createMenuElement('exit', 'exit.png', '&Exit', 'Ctrl+Q',
                               'Exit',
                               self.close,
                               'fileMenu', False, False)

        self.createMenuElement('settings', 'exit.png', '&Settings', 'Ctrl+Q', 'Settings',
                               self.show_settings,
                               'settingsMenu', False, False)

        self.createMenuElement('translate', 'exit.png', '&Translate with Google translate', '',
                               'Translate with Google Translate',
                               self.translate_google,
                               'translationsMenu', True)

        self.createMenuElement('validate', 'exit.png', '&Set Selection as Validated', 'F10',
                               'Validate selection',
                               self.validate_selection,
                               'translationsMenu')

        self.createMenuElement('revision', 'exit.png', '&Set Selection as Revision', 'F11',
                               'revision selection',
                               self.revision_selection,
                               'translationsMenu')

        self.createMenuElement('unvalidate', 'exit.png', '&Set Selection as Unvalidated', 'F12',
                               'un validate selection',
                               self.unvalidate_selection,
                               'translationsMenu')
        self.statusBar()

    def load_table(self, package):
        """
        The load_table function loads the table with the data from DATA.
        It also sets up a TableModel and ProxyModel to filter out rows that are not in view.
        
        :param self: Reference the class instance from within the class
        :param package: Pass the data from the main window to this class
        :return: The model of the table
        :doc-author: Trelent
        """
        header = ['ID', 'ID', 'Instance', 'Original Text', 'Translated Text', 'State', 'Source', 'Source']
        package.model = TableModel(package.flatten(package.DATA, []), header)

        self.table.setModel(package.model)
        self.table.horizontalHeader().setSectionResizeMode(0, PyQt6.QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, PyQt6.QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, PyQt6.QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, PyQt6.QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, PyQt6.QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, PyQt6.QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, PyQt6.QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, PyQt6.QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.setColumnHidden(1, True)
        self.table.setColumnHidden(6, True)

        self.table.setSelectionBehavior(PyQt6.QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

        self.visible = True
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested['QPoint'].connect(self.show_table_menu)

        if not package.isQuick:
            loadTranslation = self.checkDatabase()

            if loadTranslation:
                self.load_translation(loadTranslation)
                self.package.database_path = loadTranslation

        self.proxy_model = MyProxyModel()
        self.proxy_model.setFilterKeyColumn(STATE_INDEX)

        self.proxy_model.setSourceModel(package.model)
        self.table.setModel(self.proxy_model)

        self.table.clicked.connect(self.print_selection)
        self.table.selectionModel().currentChanged.connect(self.print_selection)

        if not self.loaded and not package.isQuick:
            self.enableButtons()
            self.loaded = True

        self.setCentralWidget(self.centralwidget)

        if self.first_load == 1 and not package.isQuick:
            self.load_toolbar()
            self.first_load = 0

            self.label_total.setText(str(len(package.model._data)))
            self.label_count.setText(str(self.proxy_model.rowCount()))

            self.search_instance.blockSignals(True)
            self.search_instance.clear()
            self.search_instance.addItem('-- All Instances --')
            self.search_instance.blockSignals(False)

            self.search_file.blockSignals(True)
            self.search_file.clear()
            self.search_file.addItem('-- All Files --')
            self.search_file.addItems(package.DATA.keys())
            self.search_file.blockSignals(False)

    def print_selection(self):
        """
        The print_selection function prints the selected row in the table.
        
        
        :param self: Access variables that belongs to the class
        :return: The value of the selected row
        :doc-author: Trelent
        """
        try:
            index = self.proxy_model.mapToSource(self.table.selectionModel().currentIndex())

            value = index.sibling(index.row(), index.column()).data()
            row = self.package.model._data[index.row()]

            self.base_zone.setPlainText(row[BASE_INDEX])
            self.translate_zone.blockSignals(True)
            self.translate_zone.setPlainText(row[TRANSLATION_INDEX])
            self.translate_zone.blockSignals(False)

        except:
            pass

    def update_data(self):
        """
        The update_data function updates the data in the table.
        It takes no arguments and returns nothing.
        
        :param self: Access the class attributes
        :return: The text that is in the translation zone
        :doc-author: Trelent
        """
        index = self.proxy_model.mapToSource(self.table.selectionModel().currentIndex())
        text = self.translate_zone.toPlainText()
        base_text = self.base_zone.toPlainText()

        if base_text == self.package.model._data[index.row()][BASE_INDEX] and text != \
                self.package.model._data[index.row()][TRANSLATION_INDEX]:
            self.package.model._data[index.row()][TRANSLATION_INDEX] = text
            self.package.model._data[index.row()][STATE_INDEX] = TO_VALIDATE_STATE

    def load_toolbar(self):
        """
        The load_toolbar function creates a toolbar menu and adds three buttons to it.
        The buttons are created by calling the createMenuElement function, which is defined later in this file.
        
        
        :param self: Access the class attributes and methods
        :return: A qtoolbar object
        :doc-author: Trelent
        """
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

        self.search_bar = QtWidgets.QLineEdit(self)
        self.search_bar.setMaximumWidth(150)
        self.search_bar.textChanged.connect(self.filterData)

        self.search_in = QComboBox()
        self.search_in.addItem('Source', BASE_INDEX)
        self.search_in.addItem('Translation', TRANSLATION_INDEX)
        self.search_in.addItem('Key', FKEY_INDEX)
        self.search_in.currentTextChanged.connect(self.filterData)

        self.search_instance = QComboBox()
        self.search_instance.addItem('-- All Instances --', '')
        self.search_instance.currentTextChanged.connect(self.filterInstance)

        self.search_file = QComboBox()
        self.search_file.addItem('-- All Files --', '')
        self.search_file.currentTextChanged.connect(self.filterFile)

        self.label_count = QLabel('0')
        self.label_slash = QLabel('/')
        self.label_total = QLabel('0')

        self.menus['toolbarMenu'].addWidget(self.search_bar)
        self.menus['toolbarMenu'].addWidget(self.search_in)
        self.menus['toolbarMenu'].addWidget(self.search_instance)
        self.menus['toolbarMenu'].addWidget(self.search_file)

        self.menus['toolbarMenu'].addWidget(self.label_count)
        self.menus['toolbarMenu'].addWidget(self.label_slash)
        self.menus['toolbarMenu'].addWidget(self.label_total)

    def filterFile(self):
        search_file = self.search_file.currentText()

        if search_file != '-- All Files --' and search_file != '':
            self.search_instance.blockSignals(True)
            self.search_instance.clear()
            self.search_instance.addItem('-- All Instances --')
            self.search_instance.addItems(self.package.DATA[search_file].keys())
            self.search_instance.blockSignals(False)

            self.proxy_model.removeFilter(None, INSTANCE_INDEX)
            self.proxy_model.setFilter(search_file, FILENAME_INDEX, True)

        else:
            self.proxy_model.removeFilter(None, FILENAME_INDEX)
            self.proxy_model.removeFilter(None, INSTANCE_INDEX)

            self.search_instance.blockSignals(True)
            self.search_instance.clear()
            self.search_instance.addItem('-- All Instances --')
            self.search_instance.addItems(self.allInstances)
            self.search_instance.blockSignals(False)

        self.label_count.setText(str(self.proxy_model.rowCount()))

    def filterInstance(self):
        search_instance = self.search_instance.currentText()

        if search_instance != '-- All Instances --' and search_instance != '':
            self.proxy_model.setFilter(search_instance, INSTANCE_INDEX, True)

        else:
            self.proxy_model.removeFilter(None, INSTANCE_INDEX)

        self.label_count.setText(str(self.proxy_model.rowCount()))

    def filterData(self):
        text = self.search_bar.text()
        column = self.search_in.itemData(self.search_in.currentIndex())

        self.proxy_model.clearFilters(column)

        if text != '':
            self.proxy_model.setFilter(text, column, True)

        self.label_count.setText(str(self.proxy_model.rowCount()))

    def filterValidate(self, action):
        """
        The filterValidate function filters the data in the table to only show rows that have been validated.
        The filterValidate function is called when a user clicks on the Validated button.
        
        :param self: Access the class attributes
        :param action: Determine whether the user is filtering or not
        :return: True if the filtervalidated button is checked, and false otherwise
        :doc-author: Trelent
        """
        if not self.buttons['fvalidated'].isChecked():
            self.proxy_model.removeFilter(STATE_LIST[VALIDATED_STATE], STATE_INDEX)

        else:
            self.proxy_model.setFilter(STATE_LIST[VALIDATED_STATE], STATE_INDEX, False)

        self.label_count.setText(str(self.proxy_model.rowCount()))

    def filterUnknown(self, action):
        """
        The filterUnknown function filters the data in the table by removing all rows that have a state of &quot;Unknown&quot;.
        The filterUnknown function is called when the user checks or unchecks the &quot;Filter Unknown&quot; checkbox.


        :param self: Access the class variables
        :param action: Determine which button was clicked
        :return: The proxy model
        :doc-author: Trelent
        """
        if not self.buttons['funknown'].isChecked():
            self.proxy_model.removeFilter(STATE_LIST[NO_STATE], STATE_INDEX)

        else:
            self.proxy_model.setFilter(STATE_LIST[NO_STATE], STATE_INDEX, False)

        self.label_count.setText(str(self.proxy_model.rowCount()))

    def filterUnvalidated(self, action):
        """
        The filterUnvalidated function filters the data in the table to only show unvalidated functions.
        
        
        :param self: Access the class attributes
        :param action: Determine which button was clicked
        :return: The filterfixedstring of the proxy model
        :doc-author: Trelent
        """
        if not self.buttons['funvalidated'].isChecked():
            self.proxy_model.removeFilter(STATE_LIST[TO_VALIDATE_STATE], STATE_INDEX)

        else:
            self.proxy_model.setFilter(STATE_LIST[TO_VALIDATE_STATE], STATE_INDEX, False)

        self.label_count.setText(str(self.proxy_model.rowCount()))

    def write_logs(self, log=None, erase=False):
        """
        The write_logs function writes the logs to the log zone.
        
        :param self: Make the function a method of the class
        :param log: Pass the logs to be written in the log zone
        :param erase: Clear the log zone
        :return: The logs
        :doc-author: Trelent
        """
        if erase:
            self.logs = []

        if log is not None:
            self.logs.append(log)

        logs = self.logs[::-1]
        self.log_zone.setPlainText("\n".join(logs))

    def raiseMessage(self, message, informativeMessage, error):
        """
        The raiseMessage function is used to display a message box with two buttons.
        The first button is the &quot;Yes&quot; button and it returns True when clicked. The second 
        button is the &quot;No&quot; button and it returns False when clicked.

        :param self: Access the class attributes
        :param message: Display a message to the user
        :param informativeMessage: Provide additional information to the user
        :param error: Determine whether the message box should be a warning or an error
        :return: A qmessagebox object
        :doc-author: Trelent
        """
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
        """
        The show_table_menu function creates a menu that allows the user to select 
        the state of the selected string. The function takes two arguments, pos and self. 
        The pos argument is used to determine where on the screen the menu will be displayed, 
        and self is used to access variables in this class.
        
        :param self: Access the class variables
        :param pos: Determine the position of the menu
        :return: The menu that is displayed when the user right-clicks on a row in the table
        :doc-author: Trelent
        """
        if self.table.selectionModel().selection().indexes():
            menu = QMenu()
            validateAction = menu.addAction("Set strings as Validated")
            unvalidatedAction = menu.addAction("Set strings as Unvalidated")
            revisionAction = menu.addAction("Set strings as Revision")
            resetAction = menu.addAction("Reset translation")

            state = -1

            action = menu.exec(self.mapToGlobal(pos))

            if action == validateAction:
                state = VALIDATED_STATE

            elif action == unvalidatedAction:
                state = NO_STATE

            elif action == revisionAction:
                state = TO_VALIDATE_STATE

            elif action == resetAction:
                self.resetSelection()

            if state > -1:
                self.changeSelectionState(state)

    def validate_selection(self):
        self.changeSelectionState(VALIDATED_STATE)

    def revision_selection(self):
        self.changeSelectionState(TO_VALIDATE_STATE)

    def unvalidate_selection(self):
        self.changeSelectionState(NO_STATE)

    def changeSelectionState(self, state):
        for i in self.table.selectionModel().selectedRows():
            index = self.proxy_model.mapToSource(i)
            self.package.model.updateState(index.row(), state)

    def resetSelection(self):
        for i in self.table.selectionModel().selectedRows():
            index = self.proxy_model.mapToSource(i)
            self.package.model.resetTranslation(index.row())


try:

    from ctypes import windll  # Only exists on Windows.

    myappid = 'mycompany.myproduct.subproduct.version'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

if __name__ == "__main__":
    with open(relative_path("style.qss"), "r") as f:
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(relative_path('icon.ico')))
        app.setStyle('Fusion')
        app.setStyleSheet(f.read())
        # apply_stylesheet(app, theme='theme.xml')

        # apply_stylesheet(app, theme='theme.xml', invert_secondary=True, css_file=relative_path('styles.css'))
        ex = App()

        sys.exit(app.exec())
