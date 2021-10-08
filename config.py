''' 設定ファイル関連の処理 '''

import configparser

from socket import gethostname


DEFAULT_CONFIG_FILE = 'config.ini'
DEFAULT_PARAMS = {
        'device_name': 'Unknown',
        }

def readFile(fname=DEFAULT_CONFIG_FILE):
    conf = configparser.ConfigParser(defaults=DEFAULT_PARAMS)
    hostname = gethostname()
    conf.read(fname)
    if conf.has_section(hostname) is False:
        conf.add_section(hostname)

    return conf

def updateFile(conf, fname=DEFAULT_CONFIG_FILE):
    with open(fname, 'w') as f:
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

