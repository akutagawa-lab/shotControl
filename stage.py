''' ステージのクラス
'''

import sys
import re
import io
import logging

import serial
import serial.tools.list_ports

logger = logging.getLogger(__name__)


class stage():
    ''' XYZステージクラス

        シグマ光機 SHOT-304GS を想定
    '''

    DEFAULT_BAUDRATE = 9600
    DEFAULT_BYTESIZE = serial.EIGHTBITS
    DEFAULT_PARITY = serial.PARITY_NONE
    DEFAULT_STOPBIT = serial.STOPBITS_ONE
    DEFAULT_TIMEOUT = 1
    DEFAULT_WRITE_TIMEOUT = 1

    def __init__(self):
        self.npulses_per_mm = 500
        '''readlineを使うのが良い。
        io.TextIOWrapper を使うべき'''

    def openSerial(self, portname):
        logging.debug(f"stage.open(): {portname}")

    def toPulses(self, length_mm):
        '''パルスに換算'''
        return int(self.npulses_per_mm * length_mm)

    def toMM(self, npulses):
        '''長さ[mm]に換算'''
        return npulses / self.npulses_per_mm

    def sendCommand(self, cmd):
        logging.debug(f"sendCommand: {cmd}")

    def cmd_go(self):
        cmd = "G:"
        self.sendCommand(cmd)

    def moveTo(self, pos_x, pos_y, pos_z):
        logging.debug(f"moveTo: {pos_x} {pos_y} {pos_z}")
        cmd = f"A:W{self.toPulses(pos_x):+d}{self.toPulses(pos_y):+d}{self.toPulses(pos_z):+d}"
        cmd = re.sub(r'([+-])', r'\1P', cmd)
        self.sendCommand(cmd)
        self.cmd_go()
    
    def stop(self):
        cmd = "L:W"
        self.sendCommand(cmd)


def get_device_list():
    '''シリアルポートのdevice名のリストを得る'''

    device_list = []
    ports = serial.tools.list_ports.comports()
    for p in ports:
        device_list.append(p.device)
    return device_list

