import sys
import PyQt6
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QDir, QSortFilterProxyModel, QThreadPool
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import QSettings

from classes.app_actions import App_Actions
from classes.package import Package
from helpers.definitions import STATE_LIST
from classes.tables import TableModel
from qt_material import apply_stylesheet

filePath = 'D:\\Code\\Github\\SimsInterface\\SimsSTBL\\test.package'

package = Package(filePath, 'FRA_FR', True)
print(package.DATA)

package.writePackage()
