import json
import sys
import os
import PyQt6
from PyQt6 import QtGui, QtWidgets, QtCore
from PyQt6.QtCore import QDir, QFile, QFileInfo, QSortFilterProxyModel
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import QSettings


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
        self.browseButton.clicked.connect(self.setDirPath)
        self.browseButton.setText('...')
        self.horizontalLayout.addWidget(self.browseButton)

        self.verticalLayout.addLayout(self.horizontalLayout)

        ##LABEL
        self.label = QtWidgets.QLabel(self)
        self.label.setText('Source directory')
        self.verticalLayout.addWidget(self.label)

        ##HORIZONTAL LAYOUT
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(0, 0, -1, 9)

        self.lineEdit2 = QtWidgets.QLineEdit(self)
        self.lineEdit2.setText(self.settings.value("SourcePath"))

        self.horizontalLayout.addWidget(self.lineEdit2)
        self.browseButton = QtWidgets.QToolButton(self)
        self.browseButton.clicked.connect(self.setSourcePath)
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

    def setDirPath(self):
        self.dirpath = QFileDialog.getExistingDirectory(self, 'Select the database folder',
                                                        self.settings.value("DatabasePath"))

        if self.dirpath != '':
            self.lineEdit.setText(self.dirpath)

        self.settings.setValue("DatabasePath", self.dirpath)

    def setSourcePath(self):
        self.sourcePath = QFileDialog.getExistingDirectory(self, 'Select the packages folder',
                                                           self.settings.value("SourcePath"))

        if self.sourcePath != '':
            self.lineEdit2.setText(self.sourcePath)

        self.settings.setValue("SourcePath", self.sourcePath)
