# Form implementation generated from reading ui file 'test.ui'
#
# Created by: PyQt6 UI code generator 6.4.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1699, 977)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)
        self.centralwidget.setAutoFillBackground(False)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.main_grid = QtWidgets.QGridLayout()
        self.main_grid.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMaximumSize)
        self.main_grid.setObjectName("main_grid")
        self.right_menu = QtWidgets.QFrame(self.centralwidget)
        self.right_menu.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.right_menu.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.right_menu.setObjectName("right_menu")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.right_menu)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.table = QtWidgets.QTableView(self.right_menu)
        self.table.setMinimumSize(QtCore.QSize(256, 0))
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.table.setDragEnabled(True)
        self.table.setGridStyle(QtCore.Qt.PenStyle.DashDotLine)
        self.table.setSortingEnabled(True)
        self.table.setObjectName("table")
        self.table.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout_3.addWidget(self.table)
        self.pushButton = QtWidgets.QPushButton(self.right_menu)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout_3.addWidget(self.pushButton)
        self.pushButton_4 = QtWidgets.QPushButton(self.right_menu)
        self.pushButton_4.setObjectName("pushButton_4")
        self.verticalLayout_3.addWidget(self.pushButton_4)
        self.main_grid.addWidget(self.right_menu, 0, 1, 1, 1)
        self.left_menu = QtWidgets.QFrame(self.centralwidget)
        self.left_menu.setObjectName("left_menu")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.left_menu)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.pushButton_2 = QtWidgets.QPushButton(self.left_menu)
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(False)
        font.setUnderline(False)
        font.setWeight(50)
        self.pushButton_2.setFont(font)
        self.pushButton_2.setStyleSheet("padding:10px")
        self.pushButton_2.setObjectName("pushButton_2")
        self.verticalLayout_2.addWidget(self.pushButton_2)
        self.pushButton_3 = QtWidgets.QPushButton(self.left_menu)
        self.pushButton_3.setObjectName("pushButton_3")
        self.verticalLayout_2.addWidget(self.pushButton_3)
        self.load_package_button = QtWidgets.QPushButton(self.left_menu)
        self.load_package_button.setObjectName("load_package_button")
        self.verticalLayout_2.addWidget(self.load_package_button)
        self.main_grid.addWidget(self.left_menu, 0, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignTop)
        self.verticalLayout.addLayout(self.main_grid)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1699, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.actionOpen = QtGui.QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionLoad_Translation = QtGui.QAction(MainWindow)
        self.actionLoad_Translation.setObjectName("actionLoad_Translation")
        self.actionExport_to_CSV = QtGui.QAction(MainWindow)
        self.actionExport_to_CSV.setObjectName("actionExport_to_CSV")
        self.actionExport_to_Package = QtGui.QAction(MainWindow)
        self.actionExport_to_Package.setObjectName("actionExport_to_Package")
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionLoad_Translation)
        self.menuFile.addAction(self.actionExport_to_CSV)
        self.menuFile.addAction(self.actionExport_to_Package)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        self.table.customContextMenuRequested['QPoint'].connect(MainWindow.show) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton.setText(_translate("MainWindow", "PushButton"))
        self.pushButton_4.setText(_translate("MainWindow", "PushButton"))
        self.pushButton_2.setText(_translate("MainWindow", "PushButton"))
        self.pushButton_3.setText(_translate("MainWindow", "PushButton"))
        self.load_package_button.setText(_translate("MainWindow", "PushButton"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionOpen.setText(_translate("MainWindow", "Load Package"))
        self.actionLoad_Translation.setText(_translate("MainWindow", "Load Translation"))
        self.actionExport_to_CSV.setText(_translate("MainWindow", "Export to CSV"))
        self.actionExport_to_Package.setText(_translate("MainWindow", "Export to Package"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
