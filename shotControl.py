#!/usr/bin/env python3

import sys
import re
import logging

from PyQt5.QtWidgets import QWidget, QMainWindow, qApp, QApplication, QHBoxLayout, QVBoxLayout, QStyle
from PyQt5.QtWidgets import QPushButton, QLabel, QLCDNumber, QLineEdit, QCheckBox
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QDialog
from PyQt5 import QtCore, QtGui

import stage
import portSettingDialog
import positionController

logger = logging.getLogger(__name__)


class MyWindow(QMainWindow):
    QUERY_INTERVAL = 500
    def __init__(self):
        super().__init__()

        self.title = 'SHOT Controller'
        self.width = 800
        self.height = 600

        self.stage = stage.stage()

        self.initUI()

        dlg_port = portSettingDialog.portSettingDialog(self)
        if dlg_port.exec_() == QDialog.Accepted:
            self.device_name = dlg_port.selectedPort()
        else:
            self.device_name = None

        self.query_timer = QtCore.QTimer()
        self.query_timer.timeout.connect(self.queryInfo)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(0, 0, self.width, self.height)
        win = QWidget()
        layout = QVBoxLayout(win)

        self.posi_con = positionController.positionController()
        layout.addWidget(self.posi_con, 0)

        layout.addWidget(QWidget())

        self.setCentralWidget(win)

        act_quit = QAction(self.style().standardIcon(QStyle.SP_DialogCancelButton), '&Quit', self)
        act_quit.setShortcut('Ctrl+Q')
        act_quit.setStatusTip('Quit application')
        act_quit.triggered.connect(qApp.quit)

        act_query = QAction(self.style().standardIcon(QStyle.SP_MessageBoxInformation), '&Status', self)
        act_query.setShortcut('Ctrl+I')
        act_query.setStatusTip('Query info.')
        act_query.triggered.connect(self.queryInfo)

        act_go = QAction(self.style().standardIcon(QStyle.SP_MediaPlay), '&Go', self)
        act_go.setShortcut('Ctrl+G')
        act_go.setStatusTip('Go')
        act_go.triggered.connect(self.go)

        act_stop = QAction(self.style().standardIcon(QStyle.SP_MediaStop), '&Stop', self)
        act_stop.setShortcut('Ctrl+P')
        act_stop.setStatusTip('Stop')
        act_stop.triggered.connect(self.stageStop)

        self.posi_con.actionMoveTo.connect(self.stageMove)
        self.posi_con.actionStop.connect(self.stageStop)

        self.statusBar().showMessage('Ready')

        # MENU BAR
        self.menubar = self.menuBar()
        fileMenu = self.menubar.addMenu('&File')
        fileMenu.addAction(act_quit)

        # TOOL BAR
        self.toolbar = self.addToolBar('Main toolbar')
        self.toolbar.addAction(act_quit)
        self.toolbar.addAction(act_query)
        self.toolbar.addAction(act_stop)
        self.toolbar.addAction(act_go)

        self.show()

    def stageMove(self, pos_x, pos_y, pos_z):
        logging.debug(f"MoveTo: {pos_x}, {pos_y}, {pos_z}")
        self.stage.moveTo(pos_x, pos_y, pos_z)
        self.query_timer.start(self.QUERY_INTERVAL)

    def stageStop(self):
        logging.debug("Stop")
        self.stage.stop()
        self.query_timer.stop()
        self.queryInfo()

    def queryInfo(self):
        buf = self.stage.query()
        logging.debug(f"queryInfo: {buf}")
        if isinstance(buf, dict):
            self.posi_con.lcd_x.setCounterValue(buf['pos_x'])
            self.posi_con.lcd_y.setCounterValue(buf['pos_y'])
            self.posi_con.lcd_z.setCounterValue(buf['pos_z'])

    def go(self):
        logger.debug("go:")
        self.posi_con.go()
        self.query_timer.start(self.QUERY_INTERVAL)

def main():
    app = QApplication(sys.argv)
    gui = MyWindow()
    if gui.device_name is None:
        sys.exit()
    else:
        gui.stage.openSerial(gui.device_name)
        gui.statusBar().showMessage(f"{gui.device_name}")

    gui.queryInfo()
    sys.exit(app.exec_())


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
