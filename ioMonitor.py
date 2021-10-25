''' ioMonitor クラス
'''

import logging

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5 import QtCore, QtGui

logger = logging.getLogger(__name__)

class ioMonitor(QWidget):
    ''' IO の状態を表示，制御する Widget
    '''
    ST_BUTTON_ON = "color: rgb(255, 0, 0);"
    ST_BUTTON_OFF = "color: rgb(0, 0, 0);"

    buttonPressed = QtCore.pyqtSignal(int)
    buttonReleased = QtCore.pyqtSignal(int)

    def __init__(self, output_num=4):
        super().__init__()

        logger.debug('ioMonitor.__init__()')

        layout_base = QVBoxLayout()
        layout_base.setContentsMargins(0, 0, 0, 0)
        layout_out = QHBoxLayout()
        layout_out.setContentsMargins(50, 0, 50, 0)

        self.btn_out = {}
        for o in range(output_num):
            btn_id = o + 1
            self.btn_out[btn_id] = QPushButton(f"OUT{btn_id}")
            self.btn_out[btn_id].index = btn_id
            self.btn_out[btn_id].pressed.connect(self.btn_pressed)
            self.btn_out[btn_id].released.connect(self.btn_released)
            layout_out.addWidget(self.btn_out[btn_id])

        layout_base.addLayout(layout_out)

        self.setLayout(layout_base)

    def btn_pressed(self):
        '''ボタンが押された時'''
        btn = self.sender()
        self.btn_lamp_on(btn.index)
        self.buttonPressed.emit(btn.index)
        logger.debug("ioMonitor.btn_pressed(): %s %d", btn.text(), btn.index)

    def btn_released(self):
        '''ボタンが離された時'''
        btn = self.sender()
        self.btn_lamp_off(btn.index)
        self.buttonReleased.emit(btn.index)
        logger.debug("ioMonitor.btn_released(): %s %d", btn.text(), btn.index)

    def btn_lamp_on(self, btn_id):
        '''ボタンのランプをオンにする'''
        self.btn_out[btn_id].setStyleSheet(
                f"QPushButton {{{self.ST_BUTTON_ON}}}")

    def btn_lamp_off(self, btn_id):
        '''ボタンのランプをオフにする'''
        self.btn_out[btn_id].setStyleSheet(
                f"QPushButton {{{self.ST_BUTTON_OFF}}}")
