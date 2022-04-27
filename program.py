''' プログラム処理クラス
'''

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class stageProgram:
    '''ステージのプログラムクラス'''
    def __init__(self):
        self.df = pd.DataFrame(
                columns=('pos_x', 'pos_y', 'pos_z', 'settling_time',
                    'repetitions', 'out2'))
        self.gen_condition = {}    # 生成条件

    def setPosition(self, xxx, yyy, zzz, repetitions=1, settling_time=1):
        '''meshgrid で生成された numpy.ndarray からプログラムを生成'''
        xs = xxx.flatten()
        ys = yyy.flatten()
        zs = zzz.flatten()
        self.df['pos_x'] = xs
        self.df['pos_y'] = ys
        self.df['pos_z'] = zs
        self.df['repetitions'] = np.ones_like(xs, dtype=int) * repetitions
        self.df['settling_time'] = np.ones_like(xs) * settling_time

    def setFlippingIndicator(self, inv_samples):
        ''' 反転指示値の生成。

        OUT2 の生成用

        Args:
            inv_period (int): 出力が反転するサンプル数'''

        colname = 'out2'
        self.df[colname] = 0
        one_flags = np.arange(len(self.df)) % (2 * inv_samples) > inv_samples
        self.df.loc[one_flags, colname] = 1

        
    def generateGridPosition(self, range_x, range_y, range_z,
            repetitions=1, settling_time=1.0):
        '''3次元格子状の位置を生成する。

        生成結果は stageProgram.df に収納される。
        range_x, range_y, range_z の3番目の step は省略可。デフォルトは1

        Args:
            range_x (list): x軸方向の範囲。[start, stop[, step]] の形のリスト
            range_y (list): y軸方向の範囲。[start, stop[, step]] の形のリスト
            range_z (list): z軸方向の範囲。[start, stop[, step]] の形のリスト
            repetitions (int, optional): 測定繰り返し回数 default=1
            settling_time (float): セトリングタイム default=1.0
        '''
        if len(range_x) < 3:
            range_x.append(1.0)
        if len(range_y) < 3:
            range_y.append(1.0)
        if len(range_z) < 3:
            range_z.append(1.0)
        xx = np.arange(range_x[0], range_x[1] + range_x[2], range_x[2])
        yy = np.arange(range_y[0], range_y[1] + range_y[2], range_y[2])
        zz = np.arange(range_z[0], range_z[1] + range_z[2], range_z[2])
        xxx, yyy, zzz = np.meshgrid(xx, yy, zz)
        self.setPosition(xxx, yyy, zzz, repetitions, settling_time)
        self.setFlippingIndicator(len(zz + 1))

    def paramByIndex(self, idx):
        '''インデックス指定でプログラムパラメータを取得'''
        return self.df.loc[idx]

    def to_csv(self, filename='prog.csv'):
        '''CSVの書き出し'''
        self.df.to_csv(filename, index_label='idx')

    def read_csv(self, filename='prog.csv'):
        '''CSVの読み込み'''
        self.df = pd.read_csv(filename, header=0, index_col=0)


def test_data(
        range_x=(10, 20), range_y=(100, 150), range_z=(30, 40),
        pos_step=1, settling_time=1):
    '''テストデータの作成'''

    prog = stageProgram()

    xx = np.arange(range_x[0], range_x[1] + pos_step, pos_step)
    yy = np.arange(range_y[0], range_y[1] + pos_step, pos_step)
    zz = np.arange(range_z[0], range_z[1] + pos_step, pos_step)

    xxx, yyy, zzz = np.meshgrid(xx, yy, zz)

    prog.setPosition(xxx, yyy, zzz, settling_time=settling_time)

    return prog


def test():
    '''テストコード'''

    prog = test_data()
    prog.to_csv('prog.csv')
    prog.read_csv('prog.csv')

    print(prog)


if __name__ == '__main__':
    test()
