''' ポート設定用ダイアログ
'''

import sys
import logging

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QDialog, QMainWindow, QWidget, QApplication, QPushButton
from PyQt5.QtWidgets import QDialogButtonBox, QVBoxLayout, QComboBox
from PyQt5.QtWidgets import QFileDialog

import stage

logger = logging.getLogger(__name__)


class portSettingDialog(QDialog):
    phantomPort = 'Phantom Port'

    def __init__(self, parent=None, candidate_device=None):
        super().__init__()
    
        logger.debug('portSettingDialog.__init__(): candidate_divice: %s',
                     candidate_device)
        self.setWindowTitle("Choose serial port")

        buttonbox = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        self.cbox = QComboBox()
        self.cbox.addItem(self.phantomPort)
        self.cbox.addItems(stage.get_device_list())
        matched_idx = self.cbox.findText(candidate_device)
        if matched_idx >= 0:
            self.cbox.setCurrentIndex(matched_idx)

        layout = QVBoxLayout(self)
        layout.addWidget(self.cbox)
        layout.addWidget(buttonbox)

    def selectedPort(self):
        return self.cbox.currentText()


class testWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Blank widget for test')
        win = QWidget()

        self.setCentralWidget(win)

        self.show()

    def mousePressEvent(self, ev):
        logger.debug("mousePressEvent()")
        dlg = portSettingDialog(self)
        ret = dlg.exec_()

        if ret == QDialog.Accepted:
            logger.debug(f"Accepted: {dlg.selectedPort()}")
        else:
            logger.debug("Rejected")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = testWindow()
    sys.exit(app.exec_())

