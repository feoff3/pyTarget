from comm.dev_file import *
import threading

class EmulatedLayoutDev():

    def __init__(self, main_dev, header_dev, footer_dev):
        '''
        initialize and open file
        @param path: file path
        '''
        self.path = main_dev.path
        self.main_dev = main_dev
        self.header_dev = header_dev
        self.footer_dev = footer_dev
        self.__lock = threading.Lock()
        self.open()
        print(("header dev size: " + str(header_dev.size())))
        print(("main dev size: " + str(main_dev.size())))
        print(("footer dev size: " + str(footer_dev.size())))

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
        return self.main_dev.open() and self.header_dev.open() and self.footer_dev.open()


    def close(self):
        '''
        close file
        '''
        self.main_dev.close()
        self.header_dev.close()
        self.footer_dev.close()

    def dev_lock(self):
        '''
         locks file (not impl, it is always locked in Windows)
        '''
        return self.main_dev.dev_lock() and self.header_dev.dev_lock() and self.footer_dev.dev_lock()

    def dev_unlock(self):
        '''
         unlocks the file (not impl)
        '''
        return self.main_dev.dev_unlock() and self.header_dev.dev_unlock() and self.footer_dev.dev_unlock()

    def size(self):
        '''
        get file current size
        @return: size in bytes
        '''
        return self.main_dev.size() + self.header_dev.size() + self.footer_dev.size()


    def write(self, offset, buf):
        '''
        write to a volume or gpt footer or header
        @param offset: write offset
        @param buf: data buffer
        @return: True for success, False for failed
        '''
        dev1 = None
        dev2 = None
        buf1 = ""
        buf2 = ""
        off1 = 0
        off2 = 0
        buflen = len(buf) 
        if offset < self.header_dev.size():
            dev1 = self.header_dev
            dev2 = self.main_dev
            off1 = offset
            l = min(self.header_dev.size() - off1 , buflen)
            buf1 = buf[0:l]
            buf2 = buf[l:]
        elif offset < self.header_dev.size() + self.main_dev.size():
            dev1 = self.main_dev
            dev2 = self.footer_dev
            off1 = offset - self.header_dev.size()
            l = min(self.main_dev.size() - off1 , buflen)
            buf1 = buf[0:l]
            buf2 = buf[l:]
        else:
            dev1 = self.footer_dev
            dev2 = self.footer_dev
            off1 = offset - self.header_dev.size() - self.main_dev.size()
            buf1 = buf
            buf2 = ""
        res = dev1.write(off1 , buf1)
        if not res:
            return False
        if len(buf2) > 0:
            res = dev2.write(0, buf2)
        return res

    def read(self, offset, length):
        '''
        read from a volume or gpt footer or header
        @param offset: write offset
        @param length: read length in bytes
        @return: None for failed, other for success
        '''
        dev1 = None
        dev2 = None
        buf1 = ""
        buf2 = ""
        off1 = 0
        off2 = 0
        buflen = length
        if offset < self.header_dev.size():
            dev1 = self.header_dev
            dev2 = self.main_dev
            off1 = offset
            l = min(self.header_dev.size() - off1 , buflen)
        elif offset < self.header_dev.size() + self.main_dev.size():
            dev1 = self.main_dev
            dev2 = self.footer_dev
            off1 = offset - self.header_dev.size()
            l = min(self.main_dev.size() - off1 , buflen)
        else:
            dev1 = self.footer_dev
            dev2 = self.footer_dev
            off1 = offset - self.header_dev.size() - self.main_dev.size()
            l = buflen
        buf1 = dev1.read(off1 , l)
        if l < buflen:
            buf2 = dev2.read(0, buflen-l)
            buf1.extend(buf2)
        return buf1


    def flush(self):
        '''
        flush cache buffer
        '''
        self.main_dev.flush()
        self.header_dev.flush()
        self.footer_dev.flush()
