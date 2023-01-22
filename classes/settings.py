import os

from PyQt6 import QtGui, QtWidgets, QtCore
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QSettings, pyqtSignal

from classes.dictionnaries import SimpleTableModel
from classes.tables import CustomQTableView
from helpers.definitions import LANGS
from helpers.helpers import relative_path


class SettingsWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    submitClicked = pyqtSignal(str, str)
    buildClicked = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.settings = QSettings("SimsStbl", "settings")
        self.initUi()

    def initUi(self):
        self.resize(602, 600)

        ##VERTICAL LAYOUT
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(9, 0, -1, 9)

        ##LABEL
        self.label = QtWidgets.QLabel(self)
        self.label.setText('Translations directory')
        self.verticalLayout.addWidget(self.label)

        ##LABEL = Directory
        ##HORIZONTAL LAYOUT
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(0, 0, -1, 9)

        self.DirField = QtWidgets.QLineEdit(self)
        self.DirField.setText(self.settings.value("DatabasePath"))

        self.horizontalLayout.addWidget(self.DirField)
        self.browseButton = QtWidgets.QToolButton(self)
        self.browseButton.clicked.connect(self.setDirPath)
        self.browseButton.setText('...')
        self.horizontalLayout.addWidget(self.browseButton)

        self.verticalLayout.addLayout(self.horizontalLayout)

        ##LABEL = Source directory
        self.label = QtWidgets.QLabel(self)
        self.label.setText('Source directory')
        self.verticalLayout.addWidget(self.label)

        ##HORIZONTAL LAYOUT
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(0, 0, -1, 9)

        self.SourceField = QtWidgets.QLineEdit(self)
        self.SourceField.setText(self.settings.value("SourcePath"))

        self.horizontalLayout.addWidget(self.SourceField)
        self.browseButton = QtWidgets.QToolButton(self)
        self.browseButton.clicked.connect(self.setSourcePath)
        self.browseButton.setText('...')
        self.horizontalLayout.addWidget(self.browseButton)

        self.verticalLayout.addLayout(self.horizontalLayout)

        ##SOURCE LANG
        self.langLabel = QLabel("Source lang")
        self.source_lang = QComboBox()
        self.source_lang.addItems(LANGS)
        self.source_lang.currentIndexChanged.connect(self.checkDictionnaries)
        self.verticalLayout.addWidget(self.langLabel)
        self.verticalLayout.addWidget(self.source_lang)

        ##TRANSLATION LANG
        self.langLabel = QLabel("Translation lang")
        self.lang = QComboBox()
        self.lang.addItems(LANGS)
        self.lang.currentIndexChanged.connect(self.checkDictionnaries)

        self.verticalLayout.addWidget(self.langLabel)
        self.verticalLayout.addWidget(self.lang)

        ##BUTTON BOX
        self.langLabel = QLabel("Database")

        self.buildBox = QtWidgets.QPushButton()
        self.buildBox.setText('Build database')
        self.buildBox.clicked.connect(self.build_signal)

        self.verticalLayout.addWidget(self.langLabel)
        self.verticalLayout.addWidget(self.buildBox)

        # TABLE
        self.table = CustomQTableView()
        self.table.setFrameStyle(QtWidgets.QFrame.Shape(0x0001))
        self.table.setAlternatingRowColors(True)
        self.verticalLayout.addWidget(self.table)

        ##BUTTON BOX
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Save)
        self.buttonBox.clicked.connect(self.submit_signal)

        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.checkDictionnaries()

    def checkDictionnaries(self):
        data = []

        for subdir, dirs, files in os.walk(relative_path("database")):
            match_source = False
            match_trans = False

            for file in files:
                if file.endswith(".package") and self.source_lang.currentText() in file:
                    match_source = True

                if file.endswith(".package") and self.lang.currentText() in file:
                    match_trans = True

            ep_name = subdir.split('\\').pop()

            if ep_name != 'database':
                data.append([ep_name, match_source, match_trans])

        model = SimpleTableModel(data, ['EP', 'Source', 'Translation'])

        self.table.setModel(model)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)

    def setDirPath(self):
        self.dirpath = QFileDialog.getExistingDirectory(self, 'Select the database folder',
                                                        self.settings.value("DatabasePath"))

        if self.dirpath != '':
            self.DirField.setText(self.dirpath)

        self.settings.setValue("DatabasePath", self.dirpath)

    def setSourcePath(self):
        self.sourcePath = QFileDialog.getExistingDirectory(self, 'Select the packages folder',
                                                           self.settings.value("SourcePath"))

        if self.sourcePath != '':
            self.SourceField.setText(self.sourcePath)

        self.settings.setValue("SourcePath", self.sourcePath)

    def submit_signal(self):
        self.submitClicked.emit(self.DirField.text(), self.SourceField.text())
        self.close()

    def build_signal(self):
        self.buildClicked.emit(self.source_lang.currentText(), self.lang.currentText())
