# clean.py

import os, shutil

from tagt.config import read_config

def __remove_file(path):
    '''
    remove a file.
    '''
    try:
        os.remove(path)
        print(path)
    except:
        pass

def __clean_pyc(path):
    '''
    clean all of *.pyc files
    '''
    for item in os.listdir(path):
        name = path + os.sep + item
        if os.path.isdir(name):
            if name.endswith('.svn'):
                shutil.rmtree(name)
                print(name)
            else:
                __clean_pyc(name)
        elif name.endswith('.pyc'):
            __remove_file(name)

def __clean_dev():
    '''
    clean virtual device file.
    '''
    cfg = read_config('config.xml')
    if not cfg:
        return
    for t in cfg.target_list:
        for h in t.host:
            for l in h.lun:
                __remove_file(l.path)
                __remove_file(l.path + '.hdr')
                __remove_file(l.path + '.fmk')

if __name__ == '__main__':
    __clean_dev()
    __clean_pyc(os.path.abspath('.'))
