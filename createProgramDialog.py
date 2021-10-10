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

import stage

logger = logging.getLogger(__name__)


class createProgramDialog(QDialog):
    phantomPort = 'Phantom Port'

    def __init__(self, parent=None):
        super().__init__()
    
        logger.debug('createProgramDialog.__init__(): candidate_divice: %s')
        self.setWindowTitle("Choose serial port")

        buttonbox = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        self.label = QLabel('Dimension')
        self.rb_1d = QRadioButton('Line')
        self.rb_2d = QRadioButton('Surface')
        self.rb_3d = QRadioButton('Cube')

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
        layout_axes.addWidget(QLabel('num'), 0, 3)

        self.le_x_start = QLineEdit()
        self.le_x_stop = QLineEdit()
        self.le_x_num = QLineEdit()

        self.le_y_start = QLineEdit()
        self.le_y_stop = QLineEdit()
        self.le_y_num = QLineEdit()

        self.le_z_start = QLineEdit()
        self.le_z_stop = QLineEdit()
        self.le_z_num = QLineEdit()

        layout_interval = QHBoxLayout()
        layout_interval.addWidget(QLabel("Interval [s]:"))
        self.le_interval = QLineEdit()
        layout_interval.addWidget(self.le_interval)

        layout_axes.addWidget(self.le_x_start, 1, 1)
        layout_axes.addWidget(self.le_x_stop, 1, 2)
        layout_axes.addWidget(self.le_x_num, 1, 3)
        layout_axes.addWidget(self.le_y_start, 2, 1)
        layout_axes.addWidget(self.le_y_stop, 2, 2)
        layout_axes.addWidget(self.le_y_num, 2, 3)
        layout_axes.addWidget(self.le_z_start, 3, 1)
        layout_axes.addWidget(self.le_z_stop, 3, 2)
        layout_axes.addWidget(self.le_z_num, 3, 3)
        
        layout = QVBoxLayout(self)
        layout.addLayout(layout_rb)
        layout.addLayout(layout_axes)
        layout.addLayout(layout_interval)
        layout.addWidget(buttonbox)


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
        ret = dlg.exec_()

        if ret == QDialog.Accepted:
            logger.debug("Accepted: ")
        else:
            logger.debug("Rejected")


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    app = QApplication(sys.argv)
    gui = testWindow()
    sys.exit(app.exec_())

