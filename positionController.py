''' positionController クラス
'''

import logging

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QLCDNumber
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QCheckBox
from PyQt5 import QtCore, QtGui

logger = logging.getLogger(__name__)

class presetForm(QWidget):
    ''' ポップアップウィンドウで数値入力
    '''
    valueChanged = QtCore.pyqtSignal(float)

    FONT_SIZE = 20

    def __init__(self, parent=None, value=0, pos=QtCore.QPoint(0, 0)):
        super().__init__(parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowFlags(QtCore.Qt.Popup)
        self.tbox = QLineEdit(f"{value}")

        font = QtGui.QFont()
        font.setPointSize(self.FONT_SIZE)
        self.tbox.setFont(font)
        self.tbox.setValidator(QtGui.QDoubleValidator(-300.0, 300.0, 3, self.tbox))
        self.tbox.selectAll()

        layout_h = QHBoxLayout()
        layout_h.addWidget(self.tbox)
        layout_h.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout_h)
        self.tbox.returnPressed.connect(self.procReturn)

        self.move(pos)
        self.show()

    def procReturn(self):
        '''リターンキーを押したとき'''
        logging.debug('%s', self.tbox.text())
        self.valueChanged.emit(float(self.tbox.text()))
        self.close()


class myLCDCounter(QLCDNumber):
    ''' カスタムLCDカウンタ

    クリックすると入力用のフォームが表示される
    '''
    SIZE_HINT_MINIMUM_HEIGHT = 50
    def __init__(self, enable_form=False):
        super().__init__()
        self.enable_form = enable_form
        self.setMinimumHeight(self.SIZE_HINT_MINIMUM_HEIGHT)

    def mouseReleaseEvent(self, ev):
        logging.debug(f"mouseReleaseEvent: {ev.x()},{ev.y()} {self.nativeParentWidget()} {self}")
        if self.enable_form:
            popup = presetForm(self.nativeParentWidget(), value=self.value(), pos=ev.globalPos())
            popup.valueChanged.connect(self.setValue)
            popup.tbox.setFocus()

    def setValue(self, val):
        self.display(f"{val:.3f}")


class presetCounter(QWidget):
    def __init__(self):
        super().__init__()
        layout_h = QHBoxLayout()

        layout_lcds = QVBoxLayout()

        self.digits = 7
        self.relative = False

        self.lcd_counter = myLCDCounter(enable_form=False)
        self.lcd_counter.setDigitCount(self.digits)
        self.lcd_counter.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.lcd_counter.setStyleSheet(
                "QWidget { color: rgb(255, 255, 0); background-color: rgb(0, 0, 0);}")
        self.lcd_counter.setSmallDecimalPoint(True)
        self.lcd_counter.display(123.456)

        self.lcd_preset = myLCDCounter(enable_form=True)
        self.lcd_preset.setDigitCount(self.digits)
        self.lcd_preset.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.lcd_preset.setStyleSheet(
                "QWidget { color: rgb(0, 255, 0); background-color: rgb(0, 0, 0);}")
        self.lcd_preset.setSmallDecimalPoint(True)
        self.lcd_preset.setValue(123.456)

        layout_lcds.addWidget(self.lcd_counter)
        layout_lcds.addWidget(self.lcd_preset)

        layout_h.addLayout(layout_lcds)
        self.setLayout(layout_h)

    def setCounterValue(self, val):
        self.lcd_counter.display(f"{val:.3f}")

    def setPresetValue(self, val):
        self.lcd_preset.setValue(val)

    def getPresetValue(self):
        cur_val = self.lcd_counter.value()
        preset_val = self.lcd_preset.value()
        if self.relative is True:
            ret = cur_val + preset_val
        else:
            ret = preset_val
        return ret

    def setRelative(self, flag):
        cur_val = self.lcd_counter.value()
        preset_val = self.lcd_preset.value()
        if (self.relative is True) and (flag is False):
            self.setPresetValue(preset_val + cur_val)
            self.relative = False
        if (self.relative is False) and (flag is True):
            self.setPresetValue(preset_val - cur_val)
            self.relative = True

    def cancelPreset(self):
        if self.relative is True:
            self.lcd_preset.setValue(0.0)
        else:
            self.lcd_preset.setValue(self.lcd_counter.value())

    # def mousePressEvent(self, ev):
    #     print("mouse pressed")


class positionController(QWidget):
    '''Position Controller Widget

    位置制御用のパネル一式
    '''
    actionMoveTo = QtCore.pyqtSignal(float, float, float)
    actionStop = QtCore.pyqtSignal()
    actionResetOrigin = QtCore.pyqtSignal()
    actionMechanicalOrigin = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        layout_base = QVBoxLayout()

        layout_counters = QHBoxLayout()
        layout_buttons = QHBoxLayout()

        layout_counters.addWidget(QLabel("X[mm]:"), 0)
        self.lcd_x = presetCounter()
        layout_counters.addWidget(self.lcd_x, 1)

        layout_counters.addWidget(QLabel("Y[mm]:"), 0)
        self.lcd_y = presetCounter()
        layout_counters.addWidget(self.lcd_y, 1)

        layout_counters.addWidget(QLabel("Z[mm]:"), 0)
        self.lcd_z = presetCounter()
        layout_counters.addWidget(self.lcd_z, 1)


        self.btn_cancel = QPushButton("Cancel")
        self.btn_resetOrigin = QPushButton("Reset Origin")
        self.btn_mechOrigin = QPushButton("ABS. Origin")
        self.chk_relative = QCheckBox("Relative")
        self.btn_stop = QPushButton("STOP")
        self.btn_go = QPushButton("GO")

        self.chk_relative.stateChanged.connect(self.relativeStateChanged)
        self.btn_cancel.pressed.connect(self.cancelPreset)
        self.btn_resetOrigin.pressed.connect(self.resetOrigin)
        self.btn_mechOrigin.pressed.connect(self.mechanicalOrigin)
        self.btn_go.pressed.connect(self.go)
        self.btn_stop.pressed.connect(self.stop)

        # 右側のパネル
        layout_right_panel = QVBoxLayout()
        layout_counters.addLayout(layout_right_panel, 0)

        layout_right_panel.addWidget(self.btn_mechOrigin)
        layout_right_panel.addWidget(self.btn_resetOrigin)
        layout_right_panel.addWidget(self.btn_cancel)
        layout_right_panel.addWidget(self.chk_relative)
        layout_buttons.addWidget(self.btn_stop)
        layout_buttons.addWidget(self.btn_go)

        layout_base.addLayout(layout_counters)
        layout_base.addLayout(layout_buttons)

        self.setLayout(layout_base)

    def relativeStateChanged(self):
        '''相対値表示切り替え用チェックボックス'''
        if self.chk_relative.isChecked() is True:
            # チェックされているとき，相対値表示
            self.lcd_x.setRelative(True)
            self.lcd_y.setRelative(True)
            self.lcd_z.setRelative(True)
        else:
            # 絶対値表示
            self.lcd_x.setRelative(False)
            self.lcd_y.setRelative(False)
            self.lcd_z.setRelative(False)

    def cancelPreset(self):
        self.lcd_x.cancelPreset()
        self.lcd_y.cancelPreset()
        self.lcd_z.cancelPreset()

    def resetOrigin(self):
        self.actionResetOrigin.emit()

    def mechanicalOrigin(self):
        self.actionMechanicalOrigin.emit()

    def go(self):
        self.actionMoveTo.emit(
                self.lcd_x.getPresetValue(),
                self.lcd_y.getPresetValue(),
                self.lcd_z.getPresetValue())

    def stop(self):
        self.actionStop.emit()


