''' ステージのクラス
'''

import re
# import sys
# import io
import logging

import serial
import serial.tools.list_ports

logger = logging.getLogger(__name__)

IO_ON = 1
IO_OFF = 0

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
        self.ser = None
        self.serport = None
        self.rom_version = "dummy"
        self.distance_per_pulse = [1.0, 1.0, 1.0, 1.0]
        self.divisions = [2, 2, 2, 2]
        self.last_move_to = [0, 0, 0]
        self.io_out = 0

    def openSerial(self, portname):
        ''' シリアルポートを開く '''
        logger.debug("stage.open(): %s", portname)
        self.serport = portname
        self.ser = serial.Serial()
        self.ser.port = portname
        self.ser.baudrate = 9600
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.timeout = 5

        s_devs = get_device_list()
        if portname in s_devs:
            try:
                self.ser.open()
                self.phantom_port = False

            except serial.SerialException:
                logger.info(
                        "stage.open():"
                        "%s cannot open. Phoantom port will be used.", portname)
                self.phantom_port = True
        else:
            self.phantom_port = True

    def toPulses(self, length_mm):
        '''パルスに換算'''
        return int(self.npulses_per_mm * length_mm)

    def toMM(self, npulses):
        '''長さ[mm]に換算'''
        return npulses / self.npulses_per_mm

    def sendCommand(self, cmd):
        '''コマンドを送出する

        もしファントムポートであれば（stage.phantom_port is True）
        何もしない

        Parameter
        ----------
        cmd: string
            送出コマンド

        Return
        ------
        status: string
            ステージからの返り値
        '''
        logger.debug("sendCommand: %s", cmd)
        if self.phantom_port is True:
            buf = 'OK'
        else:
            self.ser.write((cmd + '\r\n').encode('utf-8'))
            buf = self.ser.readline()
            buf = buf.strip().decode('utf-8')

        return buf

    def getInfo(self):
        ''' ステージの内部情報を取得する

        取得した結果は，
            stage.rom_version
            stage.distance_per_pulse
            stage.divisions
        に代入される．
        ファントムポートの場合は何もしない
        （適当なデフォルト値がセットされている）
        '''

        if self.phantom_port is not True:
            self.rom_version = self.sendCommand("?:V")
            buf = self.sendCommand("?:PW")
            dpp = re.split(r'\s*,\s*', buf)
            self.distance_per_pulse = [float(v) for v in dpp]
            buf = self.sendCommand("?:SW")
            div = re.split(r'\s*,\s*', buf)
            self.divisions = [int(d) for d in div]

        logger.debug("rom_version:%s", self.rom_version)
        logger.debug("distance_per_pulse: %s", f"{self.distance_per_pulse}")
        logger.debug("divisions: %s", f"{self.divisions}")

    def cmd_go(self):
        ''' G: を送出 '''
        cmd = "G:"
        self.sendCommand(cmd)

    def moveTo(self, pos_x, pos_y, pos_z):
        ''' 指定した位置に移動する '''
        logger.debug("moveTo: %f %f %f", pos_x, pos_y, pos_z)
        cmd = (f"A:W{self.toPulses(pos_x):+d}"
               f"{self.toPulses(pos_y):+d}"
               f"{self.toPulses(pos_z):+d}")
        cmd = re.sub(r'([+-])', r'\1P', cmd)
        self.sendCommand(cmd)
        self.cmd_go()
        self.last_move_to = [pos_x, pos_y, pos_z]

    def stop(self):
        ''' ステージの移動を停止する '''
        cmd = "L:W"
        self.sendCommand(cmd)

    def query(self):
        '''現在の状態を問い合わせる'''
        ret = self.sendCommand("Q:")
        logger.debug("query(): %s", ret)
        ret = re.sub(r'\s', '', ret)
        res = re.split(',', ret)
        if len(res) == 7:
            qres = {
                    'pos_x': self.toMM(int(res[0])),
                    'pos_y': self.toMM(int(res[1])),
                    'pos_z': self.toMM(int(res[2])),
                    'ack1': res[4],
                    'ack2': res[5],
                    'ack3': res[6],
                }
        else:
            qres = {
                    'pos_x': self.last_move_to[0],
                    'pos_y': self.last_move_to[1],
                    'pos_z': self.last_move_to[2],
                    'ack1': 'X',
                    'ack2': 'X',
                    'ack3': 'R'
                }

        return qres

    def resetOrigin(self):
        '''電気（論理）原点のリセット．現在位置を原点に設定'''
        cmd = "R:W"
        self.sendCommand(cmd)

    def gotoMechanicalOrigin(self):
        '''機械原点復帰．機械原点に移動'''
        cmd = "H:W"
        self.sendCommand(cmd)

    def isReady(self):
        '''Readyかどうか'''
        cmd = "!:"
        status = self.sendCommand(cmd)
        if self.phantom_port is True:
            ret = True
        else:
            ret = (status == "R")
        return ret

    def digitalWriteBulk(self, val:int=0):
        '''I/Oコネクタに出力状態を一括設定する

        Parameters:
        -----------
            val:
                 [OUT4][OUT3][OUT2][OUT1] のバイナリ表現
                 0 - 15 以外はビット演算により0になる
        '''
        logger.info("digitalWriteBulk(): val:%04x", val)
        self.io_out = val & 0b1111
        cmd = f"O:{self.io_out}"
        self.sendCommand(cmd)

    def digitalWrite(self, ch:int, on_off:int):
        '''I/Oコネクタへの出力状態を設定する

        Parameters:
        -----------
            ch:
                チャネル番号（1 | 2 | 3 | 4）
                OUT1 から OUT4 までが 1 から 4 に対応する
            on_off:
                stage.IO_ON または stage.IO_OFF
                stage.IO_ON は出力トランジスタが ON
                stage.IO_OFF は出力トランジスタが OFF
        '''
        logger.info("digitalWrite(): ch:%d  on_off:%d", ch, on_off)
        if ch < 0 or ch > 4:
            logger.error("digitalWrite(): ch is output of range:%d", ch )
            return
        mask = 1 << (ch - 1)
        if on_off == IO_ON:
            o_pattern = self.io_out | mask
        elif on_off == IO_OFF:
            o_pattern = self.io_out & (~mask & 0b1111)
        self.digitalWriteBulk(o_pattern)

def get_device_list():
    '''シリアルポートのdevice名のリストを得る'''

    device_list = []
    ports = serial.tools.list_ports.comports()
    for p in ports:
        device_list.append(p.device)
    return device_list
