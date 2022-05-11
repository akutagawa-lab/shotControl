''' 設定ファイル関連の処理 '''

import configparser
import logging
#import sys
import os
from pathlib import Path

from socket import gethostname

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE = 'config.ini'
DEFAULT_PARAMS = {
        'device_name': 'Unknown',
        }

def configDirectoryPath(vender=None, appname=None):
    ''' config ファイルを格納するディレクトリを返す。

    OSにより慣習的に異なる。
    posix系は ~/.config/<vender>/<appname>
    win系は ~/AppData/<vender>/<appname>

    Args:
        vender (str): ベンダ名  default: None
        appname (str): アプリケーション名　default: None

    Returns:
        pathlib.Path: configファイル格納用ディレクトリ
    '''
    homedir = Path.home()
    config_dir = Path('.')
    if os.name == 'posix':
        config_dir = homedir / '.config'
    if os.name == 'nt':
        config_dir = homedir / 'AppData' / 'Local'
    if vender is not None:
        config_dir = config_dir / vender
    if appname is not None:
        config_dir = config_dir / appname

    return config_dir


def readFile(fname=DEFAULT_CONFIG_FILE, defaults=DEFAULT_PARAMS, vender=None, appname=None):
    '''configファイルを読み込む

    Args:
        fname (str): configファイルのファイル名 default: "config.ini"
        defaults (dict): デフォルトパラメータ
        vender (str): ベンダ名  default: None
        appname (str): アプリケーション名　default: None

    Returns:
        configparser.ConfigParser: 読み込んだConfigParserオブジェクト
        
    '''
    conf = configparser.ConfigParser(defaults=defaults)
    hostname = gethostname()
    dirpath = configDirectoryPath(vender=vender, appname=appname)
    conf.read(dirpath / fname)
    if conf.has_section(hostname) is False:
        conf.add_section(hostname)

    return conf

def updateFile(conf, fname=DEFAULT_CONFIG_FILE, vender=None, appname=None):
    ''' configファイルの更新（新規作成）

    Args:
        conf (configparser.ConfigParser): 設定内容
        defaults (dict): デフォルトパラメータ
        vender (str): ベンダ名  default: None
        appname (str): アプリケーション名　default: None
            
    Return:
        Nothing
    '''
    dirpath = configDirectoryPath(vender=vender, appname=appname)
    dirpath.mkdir(parents=True, exist_ok=True)
    with open(dirpath / fname, 'w') as f:
        conf.write(f)

if __name__ == '__main__':
    test_conf_fname = 'config_test.ini'
    conf = readFile(test_conf_fname)

    conf_s = conf['cetus.c4.ee.tokushima-u.ac.jp']
    print(conf_s['device_name'])
    conf_s['appended_item'] = 'Extra'

    print('sections')
    for s in conf.sections():
        print(f'[{s}]')
        for o in conf.options(s):
            print(f' {o}: {conf[s][o]}')


    updateFile(conf, test_conf_fname)

