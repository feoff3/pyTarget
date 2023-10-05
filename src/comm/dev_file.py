#    
#    general file class, as base class for all kinds of devices.
#
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-02-18)
#

import os
from comm.debug import *

class DevFile():
    '''
    general file for device.
    '''

    def __init__(self, path):
        '''
        initialize and open file
        @param path: file path
        '''
        self.fd = None
        self.path = path
        self.__lock = threading.Lock()
        self.open()

    def __del__(self):
        self.close()

    def lock(self):
        self.__lock.acquire()
    
    def unlock(self):
        self.__lock.release()


    def open(self):
        '''
        open file
        @return: True for success, False for failed 
        '''
        if self.fd:
            return True
        try:
            if os.path.isfile(self.path):
                self.fd = open(self.path, 'r+b')
            else:
                self.fd = open(self.path, 'w+b')
            return True
        except:
            DBG_WRN('open device %s FAILED' % self.path)
        return False


    def close(self):
        '''
        close file
        '''
        if self.fd:
            self.fd.close()
            self.fd = None

    def dev_lock(self):
        '''
         locks file (not impl, it is always locked in Windows)
        '''
        return True

    def dev_unlock(self):
        '''
         unlocks the file (not impl)
        '''
        return False

    def size(self):
        '''
        get file current size
        @return: size in bytes
        '''
        try:
            stat = os.stat(self.path)
            return stat.st_size
        except:
            DBG_WRN('get file(%s) status FAILED.' % self.path);
            return 0


    def write(self, offset, buf):
        '''
        write file without lock
        @param offset: write offset
        @param buf: data buffer
        @return: True for success, False for failed
        '''
        try:
            self.fd.seek(offset, os.SEEK_SET)
            self.fd.write(buf)
            self.fd.flush()
            return True
        except:
            DBG_WRN('file (%s) write FAILED(offset=%d, length=%d)' % (self.path, offset, len(buf)))
            return False


    def read(self, offset, length):
        '''
        read file without lock
        @param offset: write offset
        @param length: read length in bytes
        @return: None for failed, other for success
        '''
        try:
            self.fd.seek(offset, os.SEEK_SET)
            buf = self.fd.read(length)
            if len(buf) != length:
                DBG_WRN('file (%s) read FAILED(offset=%d, length=%d)' % (self.path, offset, length))
                buf = None
            return buf
        except:
            DBG_WRN('raw read read buffer FAILED')
            DBG_EXC()
            return None


    def flush(self):
        '''
        flush cache buffer
        '''
        try:
            self.fd.flush()
        except:
            DBG_WRN('file flush FAILED')
