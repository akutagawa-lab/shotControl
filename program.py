''' プログラム処理クラス
'''

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class stageProgram:
    '''ステージのプラグラムクラス'''
    def __init__(self):
        self.df = pd.DataFrame(columns=('pos_x', 'pos_y', 'pos_z', 'interval'))

    def setPosition(self, xxx, yyy, zzz, interval=1):
        '''meshgrid で生成された numpy.ndarray からプログラムを生成'''
        xs = xxx.flatten()
        ys = yyy.flatten()
        zs = zzz.flatten()
        self.df['pos_x'] = xs
        self.df['pos_y'] = ys
        self.df['pos_z'] = zs
        self.df['interval'] = np.ones_like(xs) * interval

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
        pos_step=1, interval=1):

    prog = stageProgram()

    xx = np.arange(range_x[0], range_x[1] + pos_step, pos_step)
    yy = np.arange(range_y[0], range_y[1] + pos_step, pos_step)
    zz = np.arange(range_z[0], range_z[1] + pos_step, pos_step)

    xxx, yyy, zzz = np.meshgrid(xx, yy, zz)

    prog.setPosition(xxx, yyy, zzz, interval=interval)

    return prog


def test():
    '''テストコード'''

    prog = test_data()
    prog.to_csv('prog.csv')
    prog.read_csv('prog.csv')

    print(prog)


if __name__ == '__main__':
    test()
