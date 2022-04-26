#!/usr/bin/env python3
''' シグマ光機 SHOT-304GS コントロールプログラム
'''

import sys
import logging
import argparse
from socket import gethostname
import time

from PyQt5.QtWidgets import QWidget, QMainWindow, qApp, QApplication, QHBoxLayout, QVBoxLayout, QStyle
from PyQt5.QtWidgets import QPushButton, QLabel, QLCDNumber, QLineEdit, QCheckBox
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QTableWidgetSelectionRange
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt

import stage
import portSettingDialog
import positionController
import ioMonitor
import program
import config

logger = logging.getLogger(__name__)


class MyWindow(QMainWindow):
    ''' メインウィンドウ '''
    QUERY_INTERVAL = 250

    # unit of DURATION is [ms]
    OSCI_TRIGGER_DURATION = 100
    OSCI_TRIGGER_CHANNEL = 1

    def __init__(self, conf):
        super().__init__()

        self.title = 'SHOT-304GS Controller'
        self.width = 800
        self.height = 600
        self.device_name = None
        self.flag_prog_run = False

        self.stage = stage.stage()
        self.program = program.stageProgram()

        self.initUI()

        dlg_port = portSettingDialog.portSettingDialog(self,
                candidate_device=conf['device_name'])
        if dlg_port.exec_() == QDialog.Accepted:
            self.device_name = dlg_port.selectedPort()
            conf['device_name'] = self.device_name
        else:
            self.device_name = None

        self.query_timer = QtCore.QTimer()
        self.query_timer.timeout.connect(self.queryInfo)
        self.interval_timer = QtCore.QTimer()
        self.interval_timer.timeout.connect(self.intervalTimeup)
        self.trigger_timer = QtCore.QTimer()
        self.trigger_timer.timeout.connect(self.triggerTimeup)

    def initUI(self):
        ''' UIの初期化 '''
        self.setWindowTitle(self.title)
        self.setGeometry(0, 0, self.width, self.height)
        win = QWidget()
        # 全体はQVBoxLayout
        # posi_con : positionController
        # io_monitor : ioMonitor
        # prog_table : QTableWidget
        layout = QVBoxLayout(win)


        self.posi_con = positionController.positionController()
        layout.addWidget(self.posi_con, 0)
        self.io_monitor = ioMonitor.ioMonitor(output_num=4)
        layout.addWidget(self.io_monitor)
        self.io_monitor.buttonPressed.connect(self.actionOutputOn)
        self.io_monitor.buttonReleased.connect(self.actionOutputOff)

        self.prog_table = QTableWidget()
        layout.addWidget(self.prog_table)
        self.prog_table.cellClicked.connect(self.tableSelectRow)
        self.prog_table.currentCellChanged.connect(
                self.actionCurrentCellChanged)
        self.prog_table.cellChanged.connect(self.actionCurrentCellValueChanged)

        self.setCentralWidget(win)

        act_quit = QAction(
                self.style().standardIcon(QStyle.SP_DialogCloseButton),
                '&Quit', self)
        act_quit.setShortcut('Ctrl+Q')
        act_quit.setToolTip('Quit application')
        act_quit.setStatusTip('Quit application')
        act_quit.triggered.connect(qApp.quit)

        act_query = QAction(
                self.style().standardIcon(QStyle.SP_MessageBoxInformation),
                '&Status', self)
        act_query.setShortcut('Ctrl+I')
        act_query.setToolTip('Query info.')
        act_query.setStatusTip('Query info.')
        act_query.triggered.connect(self.queryInfo)

        act_go = QAction(
                self.style().standardIcon(QStyle.SP_DialogApplyButton),
                '&Go', self)
        act_go.setShortcut('Ctrl+G')
        act_go.setToolTip('Go to destinate position')
        act_go.setStatusTip('Go')
        act_go.triggered.connect(self.go)

        act_stop = QAction(
                self.style().standardIcon(QStyle.SP_BrowserStop),
                '&Stop', self)
        act_stop.setShortcut('Ctrl+T')
        act_stop.setToolTip('Stop immediately')
        act_stop.setStatusTip('Stop')
        act_stop.triggered.connect(self.stageStop)

        act_prog_next = QAction(
                self.style().standardIcon(QStyle.SP_ArrowDown),
                '&Next', self)
        act_prog_next.setShortcut('Ctrl+N')
        act_prog_next.setToolTip('Next position')
        act_prog_next.setStatusTip('Next')
        act_prog_next.triggered.connect(self.progNextStep)

        act_prog_prev = QAction(
                self.style().standardIcon(QStyle.SP_ArrowUp),
                '&Previous', self)
        act_prog_prev.setShortcut('Ctrl+P')
        act_prog_prev.setToolTip('Previous position')
        act_prog_prev.setStatusTip('Previous')
        act_prog_prev.triggered.connect(self.progPrevStep)

        act_prog_open = QAction(
                self.style().standardIcon(QStyle.SP_DialogOpenButton),
                '&Open', self)
        act_prog_open.setShortcut('Ctrl+O')
        act_prog_open.setStatusTip('Open program file')
        act_prog_open.triggered.connect(self.actionOpenProgram)

        act_prog_save = QAction(
                self.style().standardIcon(QStyle.SP_DialogSaveButton),
                '&Save', self)
        act_prog_save.setShortcut('Ctrl+S')
        act_prog_save.setStatusTip('Save program as ...')
        act_prog_save.triggered.connect(self.actionSaveProgram)

        act_prog_new = QAction(
                self.style().standardIcon(QStyle.SP_FileIcon),
                '&New', self)
        # act_prog_new.setShortcut('Ctrl+N')
        act_prog_new.setToolTip('Create new program')
        act_prog_new.setStatusTip('Create new program')
        act_prog_new.triggered.connect(self.actionNewProgram)

        self.act_prog_run = QAction(
                self.style().standardIcon(QStyle.SP_MediaPlay),
                '&Run', self)
        self.act_prog_run.setToolTip('Run program')
        self.act_prog_run.setStatusTip('Run program')
        self.act_prog_run.triggered.connect(self.actionRun)

        self.act_prog_stop = QAction(
                self.style().standardIcon(QStyle.SP_MediaStop),
                '&Stop', self)
        self.act_prog_stop.setToolTip('Stop program')
        self.act_prog_stop.setStatusTip('Stop program')
        self.act_prog_stop.triggered.connect(self.actionStopProgram)
        self.act_prog_stop.setEnabled(False)

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
        self.toolbar.addSeparator()
        self.toolbar.addAction(act_prog_new)
        self.toolbar.addAction(act_prog_open)
        self.toolbar.addAction(act_prog_save)
        self.toolbar.addSeparator()  # -------
        self.toolbar.addAction(act_query)
        self.toolbar.addAction(act_stop)
        self.toolbar.addAction(act_go)
        self.toolbar.addAction(act_prog_prev)
        self.toolbar.addAction(act_prog_next)
        self.toolbar.addSeparator()  # -------
        self.toolbar.addAction(self.act_prog_stop)
        self.toolbar.addAction(self.act_prog_run)

        self.show()

    def showStatus(self, msg=""):
        ''' status bar に情報表示 '''
        msgs = []
        if self.device_name is None:
            msgs.append('Port:None')
        else:
            msgs.append(self.device_name)

        msg = '|'.join(msgs)
        self.statusBar().showMessage(msg)

    def stageMove(self, pos_x, pos_y, pos_z):
        '''指定された位置にステージを移動'''
        logging.debug(
                "MoveTo: pos_x:%d, pos_y:%d, pos_z:%d", pos_x, pos_y, pos_z)
        self.stage.moveTo(pos_x, pos_y, pos_z)
        self.query_timer.start(self.QUERY_INTERVAL)

    def stageStop(self):
        ''' ステージを止める '''
        logging.debug("Stop")
        self.stage.stop()
        self.query_timer.stop()
        self.queryInfo()

    def queryInfo(self):
        ''' ステージの状態を取得し，posi_con を更新

        ステージ移動時にquery_timerがtimeup したとき呼ばれる．
        ステージがreadyとなればquery_timerを停止
        このときプログラムが run 中であれば
        目的位置まで移動完了したことになるので次のステップを
        実行する．
        '''
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
                if ((self.flag_prog_run is True) and (self.trigger_timer.isActive() is not True)):
                    # interval_timer を開始
                    cur_row = self.prog_table.currentRow()
                    param = self.program.paramByIndex(cur_row)
                    interval = param['interval'] * 1000
                    logging.debug("\tcur_row: %d: interval:%f",
                                  cur_row, interval)
                    self.interval_timer.start(interval)
            else:
                self.showStatus('Busy')

    def intervalTimeup(self):
        ''' インターバルタイマーがTimeupしたときに呼ばれる。
            ポストインターバル処理の開始
        '''
        logger.debug("intervalTimer()")
        self.interval_timer.stop()

        # オシロ用のトリガを出力
        self.trigger_timer.start(int(self.OSCI_TRIGGER_DURATION))
        self.outputOn(self.OSCI_TRIGGER_CHANNEL)

    def triggerTimeup(self):
        '''トリガ信号用のTimeup処理
            ポストインターバル処理終了
        '''
        logger.debug("triggerTimeup()")
        self.trigger_timer.stop()

        self.outputOff(self.OSCI_TRIGGER_CHANNEL)

        if self.flag_prog_run is True:
            self.progNextStep()
            self.go()

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
        '''ステージプログラムをセット'''
        self.program = prog

        self.prog_table.cellChanged.disconnect(
                self.actionCurrentCellValueChanged)

        self.prog_table.setColumnCount(self.program.df.shape[1])
        self.prog_table.setRowCount(self.program.df.shape[0])
        logging.debug("setProgramData(): row:%d  column:%d",
                      self.program.df.shape[0], self.program.df.shape[1])
        self.prog_table.setHorizontalHeaderLabels(
                self.program.df.columns.to_list())
        for r in range(self.program.df.shape[0]):
            for c in range(self.program.df.shape[1]):
                item = QTableWidgetItem(f"{self.program.df.iat[r, c]:.3f}")
                flags = item.flags()
                # flags = flags & (~ (Qt.ItemFlag.ItemIsEditable ))
                item.setFlags(flags)
                self.prog_table.setItem(r, c, item)

        self.prog_table.setVerticalHeaderLabels(
                [f"{idx}" for idx in self.program.df.index.to_list()])

        self.prog_table.cellChanged.connect(self.actionCurrentCellValueChanged)

    def progNextStep(self):
        '''プログラムを次のステップに進める'''
        cur_row = self.prog_table.currentRow()
        cur_col = 0
        logger.debug("progNextStep: currentRow:%d", cur_row)
        if cur_row+1 < self.prog_table.rowCount():
            cur_row = cur_row + 1
        elif self.flag_prog_run is True:
            self.actionStopProgram()
        # cur_row = min(cur_row + 1, self.prog_table.rowCount() - 1)
        self.prog_table.setCurrentCell(cur_row, cur_col)
        self.tableSelectRow(cur_row, 0)

    def progPrevStep(self):
        '''プログラムを前のステップに戻す'''
        cur_row = self.prog_table.currentRow()
        cur_col = 0
        logger.debug("progPrevStep: currentRow:%d", cur_row)
        cur_row = max(cur_row - 1, 0)
        self.prog_table.setCurrentCell(cur_row, cur_col)
        self.tableSelectRow(cur_row, 0)

    def tableSelectRow(self, row, col=0):
        '''テーブル内の行を選択する'''
        logger.debug(
                "tableSelectRow: row:%d, col:%d"
                "  currentRow:%d currentColumn:%d columnCount:%d",
                row, col,
                self.prog_table.currentRow(), self.prog_table.currentColumn(),
                self.prog_table.columnCount())
        for r in self.prog_table.selectedRanges():
            logger.debug("tableSelectRow: SelectedRange.topRow:%d", r.topRow())
            self.prog_table.setRangeSelected(r, False)
        if self.prog_table.currentRow() != row:
            self.prog_table.setCurrentCell(row, col)
        self.prog_table.setRangeSelected(
                QTableWidgetSelectionRange(
                    row, self.prog_table.columnCount()-1, row, 0), True)
        param = self.program.paramByIndex(row)
        self.posi_con.setPresetValue(
                param['pos_x'], param['pos_y'], param['pos_z'], relative=False)
        logger.debug(
                "x:%f y:%f z:%f int:%f",
                param['pos_x'], param['pos_y'],
                param['pos_z'], param['interval'])

    def actionCurrentCellChanged(self, cur_row, cur_col, prev_row, prev_col):
        ''' current cell（の位置）が変更されたときのaction '''
        logger.debug("actionCurrentCellChanged: cur_row: %d", cur_row)
        self.tableSelectRow(cur_row)

    def actionCurrentCellValueChanged(self, row, column):
        ''' current cellの内容が変更されたときのaction '''
        logger.debug(
                "actionCurrentCellValueChanged: row:%d, column:%d",
                row, column)
        new_celltext = self.prog_table.item(row, column).text()
        new_cellvalue = float(new_celltext)
        new_celltext = f"{float(new_cellvalue):.3f}"
        self.program.df.iloc[row, column] = new_cellvalue
        self.prog_table.cellChanged.disconnect(
                self.actionCurrentCellValueChanged)
        self.prog_table.item(row, column).setText(new_celltext)
        self.prog_table.cellChanged.connect(self.actionCurrentCellValueChanged)
        self.tableSelectRow(row, column)

    def actionNewProgram(self):
        ''' 新規プログラムの action '''
        logger.debug("actionNewProgram()")

    def actionOpenProgram(self):
        ''' open が選ばれたときの action '''
        logger.debug("actionOpenProgram()")
        fname = QFileDialog.getOpenFileName(
                self, caption='Open Program File', filter="CSV (*.csv)")
        if fname[0] != '':
            logger.debug("    fname: %s", fname[0])
            prog_opened = program.stageProgram()
            prog_opened.read_csv(fname[0])
            self.setProgramData(prog_opened)

    def actionSaveProgram(self):
        ''' save が選ばれたときの action '''
        logger.debug("actionSaveProgram()")
        fname = QFileDialog.getSaveFileName(self, 'Save Program File')
        if fname[0] != '':
            logger.debug("    fname: %s", fname[0])
            self.program.to_csv(fname[0])

    def actionRun(self):
        ''' run '''
        logger.debug("actionRun()")
        if self.flag_prog_run is False:
            self.flag_prog_run = True
            self.act_prog_run.setEnabled(False)
            self.act_prog_stop.setEnabled(True)
            cur_row = max(self.prog_table.currentRow(), 0)
            self.tableSelectRow(cur_row)
            logger.debug("actionRun(): cur_row:%d", cur_row)
            self.posi_con.go()

    def actionStopProgram(self):
        ''' stop program '''
        logger.debug("actionStopProgram")
        if self.flag_prog_run is True:
            self.interval_timer.stop()
            self.flag_prog_run = False
            self.act_prog_run.setEnabled(True)
            self.act_prog_stop.setEnabled(False)

    def outputOn(self, ch):
        ''' 指定されたチャネルの出力をON '''
        logger.debug("outputOn: %d", ch)
        self.stage.digitalWrite(ch, stage.IO_ON)
        self.io_monitor.btn_lamp_on(ch)

    def outputOff(self, ch):
        ''' 指定されたチャネルの出力をOff '''
        logger.debug("outputOn: %d", ch)
        self.stage.digitalWrite(ch, stage.IO_OFF)
        self.io_monitor.btn_lamp_off(ch)

    def actionOutputOn(self, ch):
        ''' Output Button is presssed '''
        logger.debug("actionOutputOn: %d", ch)
        self.outputOn(ch)

    def actionOutputOff(self, ch):
        ''' Output Button is released '''
        logger.debug("actionOutputOff: %d", ch)
        self.outputOff(ch)

def main():
    ''' メイン関数 '''
    entire_conf = config.readFile()
    conf = entire_conf[gethostname()]

    app = QApplication(sys.argv)
    gui = MyWindow(conf)
    if gui.device_name is None:
        sys.exit()
    else:
        gui.stage.openSerial(gui.device_name)
        gui.showStatus()

        gui.stage.getInfo()

    gui.initPreset()

    gui.setProgramData(program.test_data())

    status = app.exec_()
    config.updateFile(entire_conf)
    sys.exit(status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-v", "--verbose", help="increase verbosity level",
            action="count", default=0)
    args = parser.parse_args()

    if args.verbose > 0:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    main()
