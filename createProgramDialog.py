''' プログラム設定用ダイアログ
'''

import sys
import logging

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QDialog, QMainWindow, QWidget, QApplication, QPushButton
from PyQt5.QtWidgets import QDialogButtonBox, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel, QRadioButton, QLineEdit
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import Qt

import stage

logger = logging.getLogger(__name__)

PROGRAM_MODE_LINE = 0
PROGRAM_MODE_SURFACE = 1
PROGRAM_MODE_CUBE = 2

class createProgramDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__()
        self.mode = PROGRAM_MODE_CUBE
        self.params = {}

        logger.debug('createProgramDialog.__init__(): candidate_divice: %s')
        self.setWindowTitle("Create program")

        buttonbox = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        self.label = QLabel('Dimension')
        self.rb_1d = QRadioButton('Line')
        self.rb_2d = QRadioButton('Surface', enabled=False)
        self.rb_3d = QRadioButton('Cube')

        self.rb_1d.pressed.connect(self.rb_1d_selected)
        self.rb_2d.pressed.connect(self.rb_2d_selected)
        self.rb_3d.pressed.connect(self.rb_3d_selected)

        self.rb_3d.toggle()

        layout_rb = QHBoxLayout()

        layout_rb.addWidget(self.label)
        layout_rb.addWidget(self.rb_1d)
        layout_rb.addWidget(self.rb_2d)
        layout_rb.addWidget(self.rb_3d)

        layout_axes = QGridLayout()
        layout_axes.addWidget(QLabel('x:'), 1, 0)
        layout_axes.addWidget(QLabel('y:'), 2, 0)
        layout_axes.addWidget(QLabel('z:'), 3, 0)
        layout_axes.addWidget(QLabel('start [mm]'), 0, 1)
        layout_axes.addWidget(QLabel('stop [mm]'), 0, 2)
        layout_axes.addWidget(QLabel('step [mm]'), 0, 3)

        self.le_x_start = QLineEdit()
        self.le_x_stop = QLineEdit()
        self.le_x_step = QLineEdit()

        self.le_y_start = QLineEdit()
        self.le_y_stop = QLineEdit()
        self.le_y_step = QLineEdit()

        self.le_z_start = QLineEdit()
        self.le_z_stop = QLineEdit()
        self.le_z_step = QLineEdit()

        #for le in (self.le_x_num, self.le_y_num, self.le_z_num):
            #le.setValidator(QtGui.QIntValidator(1, 1000))

        layout_interval = QHBoxLayout()
        layout_interval.addWidget(QLabel("Interval [s]:"))
        self.le_interval = QLineEdit()
        layout_interval.addWidget(self.le_interval)

        layout_axes.addWidget(self.le_x_start, 1, 1)
        layout_axes.addWidget(self.le_x_stop, 1, 2)
        layout_axes.addWidget(self.le_x_step, 1, 3)
        layout_axes.addWidget(self.le_y_start, 2, 1)
        layout_axes.addWidget(self.le_y_stop, 2, 2)
        layout_axes.addWidget(self.le_y_step, 2, 3)
        layout_axes.addWidget(self.le_z_start, 3, 1)
        layout_axes.addWidget(self.le_z_stop, 3, 2)
        layout_axes.addWidget(self.le_z_step, 3, 3)

        layout = QVBoxLayout(self)
        layout.addLayout(layout_rb)
        layout.addLayout(layout_axes)
        layout.addLayout(layout_interval)
        layout.addWidget(buttonbox)

        self.le_x_start.setFocusPolicy(Qt.StrongFocus)
        self.le_x_start.setFocus()

    def rb_1d_selected(self):
        logger.debug('createProgramDialog.rb_1d_selected()')

        self.le_x_step.setEnabled(True)
        self.le_y_step.setEnabled(False)
        self.le_z_step.setEnabled(False)
        self.mode = PROGRAM_MODE_LINE

    def rb_2d_selected(self):
        logger.debug('createProgramDialog.rb_2d_selected()')
        self.le_x_step.setEnabled(True)
        self.le_y_step.setEnabled(True)
        self.le_z_step.setEnabled(False)
        self.mode = PROGRAM_MODE_SURFACE

    def rb_3d_selected(self):
        logger.debug('createProgramDialog.rb_3d_selected()')
        self.le_x_step.setEnabled(True)
        self.le_y_step.setEnabled(True)
        self.le_z_step.setEnabled(True)
        self.mode = PROGRAM_MODE_CUBE

    def accept(self):
        logger.debug('createProgramDialog.accept()')
        super().accept()

        self.params['mode'] = self.mode
        self.params['x_start'] = float(self.le_x_start.text())
        self.params['x_stop'] = float(self.le_x_stop.text())
        self.params['x_step'] = float(self.le_x_step.text())
        self.params['y_start'] = float(self.le_y_start.text())
        self.params['y_stop'] = float(self.le_y_stop.text())
        self.params['y_step'] = float(self.le_y_step.text())
        self.params['z_start'] = float(self.le_z_start.text())
        self.params['z_stop'] = float(self.le_z_stop.text())
        self.params['z_step'] = float(self.le_z_step.text())
        self.params['interval'] = float(self.le_interval.text())

    def setPlaceHolder(self, mode=None,
            x_start=None, x_stop=None, x_step=None,
            y_start=None, y_stop=None, y_step=None,
            z_start=None, z_stop=None, z_step=None,
            interval=None):
        if mode == PROGRAM_MODE_LINE:
            self.rb_1d.toggle()
        elif mode == PROGRAM_MODE_SURFACE:
            self.rb_2d.toggle()
        elif mode == PROGRAM_MODE_CUBE:
            self.rb_3d.toggle()

        if x_start is not None:
            self.le_x_start.setText(str(x_start))
        if x_stop is not None:
            self.le_x_stop.setText(str(x_stop))
        if x_step is not None:
            self.le_x_step.setText(str(x_step))

        if y_start is not None:
            self.le_y_start.setText(str(y_start))
        if y_stop is not None:
            self.le_y_stop.setText(str(y_stop))
        if y_step is not None:
            self.le_y_step.setText(str(y_step))

        if z_start is not None:
            self.le_z_start.setText(str(z_start))
        if z_stop is not None:
            self.le_z_stop.setText(str(z_stop))
        if z_step is not None:
            self.le_z_step.setText(str(z_step))

        if interval is not None:
            self.le_interval.setText(str(interval))

class testWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Blank widget for test')
        win = QWidget()

        self.setCentralWidget(win)

        self.show()

    def mousePressEvent(self, ev):
        logger.debug("mousePressEvent()")
        dlg = createProgramDialog(self)

        dlg.setPlaceHolder(x_start=0.0, x_stop=10.0, x_step=1.0)
        dlg.setPlaceHolder(y_start=0.0, y_stop=10.0, y_step=1.0)
        dlg.setPlaceHolder(z_start=0.0, z_stop=10.0, z_step=1.0)
        dlg.setPlaceHolder(interval=1.0)

        ret = dlg.exec_()

        if ret == QDialog.Accepted:
            logger.debug("Accepted: ")
            logger.debug(f"mode: {dlg.mode}")
            logger.debug(f"params: {dlg.params}")
        else:
            logger.debug("Rejected")


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    app = QApplication(sys.argv)
    gui = testWindow()
    sys.exit(app.exec_())

