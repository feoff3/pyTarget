#    
# file that implements IO operations for Windows device media  
#

from comm.dev_file import *

# Windows-only imports
import win32file
import win32event
import win32con
import win32security
import win32api
import pywintypes
import ctypes
import winioctlcon
import struct
import ntsecuritycon

import traceback

class WinDev():
    '''
        windows device (disk,volume,partition) for device.
    '''
    def __init__(self, path, diskdev=True):
        '''
        initialize and open file
        @param path: file path
        '''
        self.handle = None
        self.path = path
        self.diskdev = diskdev
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
        if self.handle:
            return True
        try:
            self.handle = win32file.CreateFile( self.path , ntsecuritycon.GENERIC_READ|  ntsecuritycon.FILE_WRITE_DATA, win32con.FILE_SHARE_READ|win32con.FILE_SHARE_WRITE, None,   win32con.OPEN_EXISTING, win32con.FILE_FLAG_NO_BUFFERING , 0 )
            return True
        except:
            DBG_WRN('open device %s FAILED' % self.path)
            DBG_EXC()
        return False


    def close(self):
        '''
        close file
        '''
        if self.handle:
            self.dev_unlock()
            win32api.CloseHandle(self.handle)
            self.handle = None


    def dev_lock(self):
        '''
            Windows extension to lock volumes/disks
        '''
        try:
            if self.diskdev:
                #for windows disks also do disk offline for safety
                versionsize = struct.calcsize('=IIqqIIII')
                attributes = struct.pack('=IIqqIIII',versionsize,0,1,1,0,0,0,0)
                IOCTL_DISK_SET_DISK_ATTRIBUTES = 0x7c0f4
                outbuffer = win32file.DeviceIoControl(self.handle,  IOCTL_DISK_SET_DISK_ATTRIBUTES ,  attributes, None, None )
            else:
                outbuffer = win32file.DeviceIoControl(self.handle,  winioctlcon.FSCTL_LOCK_VOLUME,  None, None, None )
            return True
        except:
            DBG_WRN('lock device %s FAILED' % self.path)
            return False
    
    def dev_unlock(self):
        '''
            Windows extension to unlock volumes/disks
        '''
        try:
            if self.diskdev:
                versionsize = struct.calcsize('=IIqqIIII')
                attributes = struct.pack('=IIqqIIII',versionsize,0,0,1,0,0,0,0)
                IOCTL_DISK_SET_DISK_ATTRIBUTES = 0x7c0f4
                outbuffer = win32file.DeviceIoControl(self.handle,  IOCTL_DISK_SET_DISK_ATTRIBUTES ,  attributes, None, None )
            else:
                # for Windows volumes, do lock instead
                outbuffer = win32file.DeviceIoControl(self.handle,  winioctlcon.FSCTL_UNLOCK_VOLUME,  None, None, None )
            return True
        except:
            DBG_WRN('unlock device %s FAILED' % self.path)
            return False

    def size(self):
        '''
        get file current size
        @return: size in bytes
        '''
        try:
            IOCTL_DISK_GET_LENGTH_INFO = 0x7405c
            outbuffersize = 8
            outbuffer = win32file.DeviceIoControl(self.handle, IOCTL_DISK_GET_LENGTH_INFO , None , outbuffersize , None )
            return struct.unpack("@q" , outbuffer)[0]
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
            win32file.SetFilePointer(self.handle, offset, win32con.FILE_BEGIN)
            rc, bwr = win32file.WriteFile(self.handle,buf,None)
            if rc != 0:
                DBG_WRN('win32file.WriteFile (%s) write FAILED(offset=%d, length=%d) win32err code = %d' % (self.path, offset, len(buf) , rc))
                return False
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
            win32file.SetFilePointer(self.handle, offset, win32con.FILE_BEGIN)
            (rc , buf) = win32file.ReadFile(self.__hfile,length,None)
            if len(buf) != length or rc != 0:
                DBG_WRN('file (%s) read FAILED(offset=%d, length=%d) win32 error code = %d' % (self.path, offset, length, rc))
                buf = None
            return buf
        except:
            DBG_WRN('raw read read buffer FAILED(offset=%d, length=%d)' % (offset, length))
            return None


    def flush(self):
        '''
        flush cache buffer
        '''
        pass

