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
        self.phantom_port = False

    def openSerial(self, portname):
        logger.debug(f"stage.open(): {portname}")
        self.serport = portname
        self.ser = serial.Serial()
        self.ser.port = portname
        self.ser.baudrate = 9600
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.timeout = 5

        try:
            self.ser.open()
            self.phantom_port = False

        except:
            logger.info(f"stage.open(): {portname} cannot open. Phoantom port will be used.")
            self.phantom_port = True

    def toPulses(self, length_mm):
        '''パルスに換算'''
        return int(self.npulses_per_mm * length_mm)

    def toMM(self, npulses):
        '''長さ[mm]に換算'''
        return npulses / self.npulses_per_mm

    def sendCommand(self, cmd):
        logger.debug(f"sendCommand: {cmd}")
        if self.phantom_port is True:
            buf = 'OK'
        else:
            self.ser.write((cmd + '\r\n').encode('utf-8'))
            buf = self.ser.readline()
            buf = buf.strip().decode('utf-8')

        return buf

    def cmd_go(self):
        cmd = "G:"
        self.sendCommand(cmd)

    def moveTo(self, pos_x, pos_y, pos_z):
        logger.debug(f"moveTo: {pos_x} {pos_y} {pos_z}")
        cmd = f"A:W{self.toPulses(pos_x):+d}{self.toPulses(pos_y):+d}{self.toPulses(pos_z):+d}"
        cmd = re.sub(r'([+-])', r'\1P', cmd)
        self.sendCommand(cmd)
        self.cmd_go()
    
    def stop(self):
        cmd = "L:W"
        self.sendCommand(cmd)

    def query(self):
        ret = self.sendCommand("Q:")
        logger.debug(f"query(): {ret}")
        ret = re.sub('\s', '', ret)
        res = re.split(',', ret)
        if len(res) == 7:
            qres = {
                    'pos_x':self.toMM(int(res[0])),
                    'pos_y':self.toMM(int(res[1])),
                    'pos_z':self.toMM(int(res[2])),
                    'ack1':res[4],
                    'ack2':res[5],
                    'ack3':res[6],
                }
        else:
            qres = ret

        return qres

def get_device_list():
    '''シリアルポートのdevice名のリストを得る'''

    device_list = []
    ports = serial.tools.list_ports.comports()
    for p in ports:
        device_list.append(p.device)
    return device_list

