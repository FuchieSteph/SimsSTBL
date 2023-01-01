from PyQt6 import QtGui, QtWidgets, QtCore
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QSettings, pyqtSignal


class SearchReplaceWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    submitClicked = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        form_layout = QtWidgets.QFormLayout(self)
        self.setLayout(form_layout)

        self.resize(602, 100)
        self.setWindowTitle("Search and Replace")

        ##LABEL
        self.search_field = QLineEdit(self)
        self.replace_field = QLineEdit(self)

        form_layout.addRow('Search', self.search_field)
        form_layout.addRow('Replace by', self.replace_field)

        self.confirm = QtWidgets.QPushButton()
        self.confirm.setText('Replace')
        self.confirm.clicked.connect(self.search)
        self.confirm.setDefault(True)

        form_layout.addRow(self.confirm)

    def search(self):
        self.submitClicked.emit(self.search_field.text(), self.replace_field.text())
        self.close()
