#!/usr/bin/env python3

import sys
import re
import logging

from PyQt5.QtWidgets import QWidget, QMainWindow, qApp, QApplication, QHBoxLayout, QVBoxLayout, QStyle
from PyQt5.QtWidgets import QPushButton, QLabel, QLCDNumber, QLineEdit, QCheckBox
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QTableWidgetSelectionRange
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt

import stage
import portSettingDialog
import positionController
import program

logger = logging.getLogger(__name__)


class MyWindow(QMainWindow):
    ''' メインウィンドウ '''
    QUERY_INTERVAL = 250
    def __init__(self):
        super().__init__()

        self.title = 'SHOT-304GS Controller'
        self.width = 800
        self.height = 600
        self.device_name = None

        self.stage = stage.stage()
        self.program = program.stageProgram()

        self.initUI()

        dlg_port = portSettingDialog.portSettingDialog(self)
        if dlg_port.exec_() == QDialog.Accepted:
            self.device_name = dlg_port.selectedPort()
        else:
            self.device_name = None

        self.query_timer = QtCore.QTimer()
        self.query_timer.timeout.connect(self.queryInfo)

    def initUI(self):
        ''' UIの初期化 '''
        self.setWindowTitle(self.title)
        self.setGeometry(0, 0, self.width, self.height)
        win = QWidget()
        layout = QVBoxLayout(win)

        self.posi_con = positionController.positionController()
        layout.addWidget(self.posi_con, 0)

        self.prog_table = QTableWidget()
        layout.addWidget(self.prog_table)
        self.prog_table.cellClicked.connect(self.tableSelectRow)

        self.setCentralWidget(win)

        act_quit = QAction(self.style().standardIcon(QStyle.SP_DialogCancelButton), '&Quit', self)
        act_quit.setShortcut('Ctrl+Q')
        act_quit.setStatusTip('Quit application')
        act_quit.triggered.connect(qApp.quit)

        act_query = QAction(self.style().standardIcon(QStyle.SP_MessageBoxInformation), '&Status', self)
        act_query.setShortcut('Ctrl+I')
        act_query.setStatusTip('Query info.')
        act_query.triggered.connect(self.queryInfo)

        act_go = QAction(self.style().standardIcon(QStyle.SP_DialogApplyButton), '&Go', self)
        act_go.setShortcut('Ctrl+G')
        act_go.setStatusTip('Go')
        act_go.triggered.connect(self.go)

        act_stop = QAction(self.style().standardIcon(QStyle.SP_BrowserStop), '&Stop', self)
        act_stop.setShortcut('Ctrl+T')
        act_stop.setStatusTip('Stop')
        act_stop.triggered.connect(self.stageStop)

        act_prog_next = QAction(self.style().standardIcon(QStyle.SP_ArrowDown), '&Next', self)
        act_prog_next.setShortcut('Ctrl+N')
        act_prog_next.setStatusTip('Next')
        act_prog_next.triggered.connect(self.progNextStep)

        act_prog_prev = QAction(self.style().standardIcon(QStyle.SP_ArrowUp), '&Previous', self)
        act_prog_prev.setShortcut('Ctrl+P')
        act_prog_prev.setStatusTip('Previous')
        act_prog_prev.triggered.connect(self.progPrevStep)

        self.posi_con.actionMoveTo.connect(self.stageMove)
        self.posi_con.actionStop.connect(self.stageStop)
        self.posi_con.actionResetOrigin.connect(self.resetOrigin)
        self.posi_con.actionMechanicalOrigin.connect(self.gotoMechanicalOrigin)

        # Status Bar
        self.showStatus('Ready')

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
        self.toolbar.addAction(act_prog_prev)
        self.toolbar.addAction(act_prog_next)

        self.show()

    def showStatus(self, msg=""):
        msgs = []
        if self.device_name is None:
            msgs.append('Port:None')
        else:
            msgs.append(self.device_name)

        msg = '|'.join(msgs)
        self.statusBar().showMessage(msg)

    def stageMove(self, pos_x, pos_y, pos_z):
        '''指定された位置にステージを移動'''
        logging.debug(f"MoveTo: {pos_x}, {pos_y}, {pos_z}")
        self.stage.moveTo(pos_x, pos_y, pos_z)
        self.query_timer.start(self.QUERY_INTERVAL)

    def stageStop(self):
        ''' ステージを止める '''
        logging.debug("Stop")
        self.stage.stop()
        self.query_timer.stop()
        self.queryInfo()

    def queryInfo(self):
        ''' ステージの状態を取得し，posi_con を更新'''
        buf = self.stage.query()
        logging.debug("queryInfo: %s", buf)
        if isinstance(buf, dict):
            self.posi_con.lcd_x.setCounterValue(buf['pos_x'])
            self.posi_con.lcd_y.setCounterValue(buf['pos_y'])
            self.posi_con.lcd_z.setCounterValue(buf['pos_z'])
            if buf['ack3'] == 'R':
                self.showStatus('Ready')
                if self.query_timer.isActive():
                    self.query_timer.stop()
            else:
                self.showStatus('Busy')

    def go(self):
        '''プリセット位置にステージを移動'''
        logger.debug("go:")
        self.posi_con.go()
        self.query_timer.start(self.QUERY_INTERVAL)

    def initPreset(self):
        '''現在位置をプリセットカウンタにセット'''
        self.queryInfo()
        self.posi_con.cancelPreset()

    def resetOrigin(self):
        '''現在位置を電気（論理）原点に設定'''
        self.stage.resetOrigin()
        self.queryInfo()
        self.initPreset()

    def gotoMechanicalOrigin(self):
        '''機械原点に移動し，カウンタをリセット'''
        self.stage.gotoMechanicalOrigin()
        if self.query_timer.isActive() is not True:
            self.query_timer.start(self.QUERY_INTERVAL)
        self.queryInfo()

    def setProgramData(self, prog):
        self.program = prog

        self.prog_table.setColumnCount(self.program.df.shape[1])
        self.prog_table.setRowCount(self.program.df.shape[0])

        self.prog_table.setHorizontalHeaderLabels(self.program.df.columns.to_list())
        for r in range(self.program.df.shape[0]):
            for c in range(self.program.df.shape[1]):
                item = QTableWidgetItem(f"{self.program.df.iat[r, c]:.3f}")
                flags = item.flags()
                flags = flags & (~ (Qt.ItemFlag.ItemIsEditable ))
                item.setFlags(flags)
                self.prog_table.setItem(r, c, item)

        self.prog_table.setVerticalHeaderLabels(
                [f"{idx}" for idx in self.program.df.index.to_list()])

    def progNextStep(self):
        cur_row = self.prog_table.currentRow()
        cur_col = 0
        logger.debug("progNextStep: currentRow:%d", cur_row)
        cur_row = cur_row + 1
        self.tableSelectRow(cur_row, 0)

    def progPrevStep(self):
        cur_row = self.prog_table.currentRow()
        cur_col = 0
        logger.debug("progPrevStep: currentRow:%d", cur_row)
        cur_row = cur_row - 1
        if cur_row < 0:
            cur_row = 0
        self.tableSelectRow(cur_row, 0)

    def tableSelectRow(self, row, col=0):
        logger.debug("cell_clicked: row:%d, col:%d", row, col)
        for r in self.prog_table.selectedRanges():
            self.prog_table.setRangeSelected(r, False)
        self.prog_table.setCurrentCell(row, col)
        self.prog_table.setRangeSelected(
                QTableWidgetSelectionRange(row, 3, row, 0), True)

def main():
    ''' メイン関数 '''
    app = QApplication(sys.argv)
    gui = MyWindow()
    if gui.device_name is None:
        sys.exit()
    else:
        gui.stage.openSerial(gui.device_name)
        gui.showStatus()

    gui.initPreset()

    gui.setProgramData(program.test_data())
    sys.exit(app.exec_())


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
