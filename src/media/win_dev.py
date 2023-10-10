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
    def __init__(self, path, diskdev=True, async_write_mode=False, async_cache_size_ops=16):
        '''
        initialize and open file
        @param path: file path
        '''
        self.handle = None
        self.path = path
        self.diskdev = diskdev
        self.async_write_mode = async_write_mode
        self.async_cache_size_ops = async_cache_size_ops
        self.__lock = threading.Lock()
        self.pending_io = dict()
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
            flags = win32con.FILE_FLAG_NO_BUFFERING
            if self.async_write_mode:
                flags |= win32con.FILE_FLAG_OVERLAPPED
            self.handle = win32file.CreateFile( self.path , ntsecuritycon.GENERIC_READ|  ntsecuritycon.FILE_WRITE_DATA, win32con.FILE_SHARE_READ|win32con.FILE_SHARE_WRITE, None,   win32con.OPEN_EXISTING, flags , 0 )
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
            self.flush()
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
                FSCTL_ALLOW_EXTENDED_DASD_IO = 0x00090083
                outbuffer = win32file.DeviceIoControl(self.handle,  FSCTL_ALLOW_EXTENDED_DASD_IO ,  None, None, None )
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

    def _clear_completed_io_list(self, wait=False):
        completed = list()
        duration = win32event.INFINITE
        if wait == False:
            duration = 0
        for k,v in self.pending_io.iteritems():
            if 0 == win32event.WaitForSingleObject(k.hEvent, duration):
                completed.append(k)
        for c in completed:
            self.pending_io.pop(c)

    def _wait_till_fits_in_cache(self, opsize):
        while True:
            current_count = 0
            wait_list = list()
            for k,v in self.pending_io.iteritems():
                if 0 == win32event.WaitForSingleObject(k.hEvent, 0):
                    continue
                current_count += 1
                wait_list.append(k.hEvent)
            if current_count < self.async_cache_size_ops:
                break
            # wait till at least one object is free
            if len(wait_list) > 0:
                # allows to wait on 64 handles max
                rc = win32event.WaitForMultipleObjects(wait_list[:64], 0, win32event.INFINITE)


    def write(self, offset, buf):
        '''
        write file without lock
        @param offset: write offset
        @param buf: data buffer
        @return: True for success, False for failed
        '''
        try:
            self._clear_completed_io_list()
            if not self.async_write_mode:
                win32file.SetFilePointer(self.handle, offset, win32con.FILE_BEGIN)
                rc, bwr = win32file.WriteFile(self.handle,buf,None)
                if rc != 0:
                    DBG_WRN('win32file.WriteFile (%s) write FAILED(offset=%d, length=%d) win32err code = %d' % (self.path, offset, len(buf) , rc))
                    return False
                return True
            else:
                self._wait_till_fits_in_cache(len(buf))
                writeOvlap = win32file.OVERLAPPED()
                writeOvlap.hEvent = win32event.CreateEvent(None, 1, 0, None)
                writeOvlap.Offset = offset
                writeOvlap.OffsetHigh = offset >> 32
                self.pending_io[writeOvlap] = buf
                rc, bwr = win32file.WriteFile(self.handle,buf,writeOvlap)
                return True
        except:
            DBG_WRN('raw win disk (%s) write FAILED(offset=%d, length=%d)' % (self.path, offset, len(buf)))
            DBG_EXC()
            return False


    def read(self, offset, length):
        '''
        read file without lock
        @param offset: write offset
        @param length: read length in bytes
        @return: None for failed, other for success
        '''
        try:
            self._clear_completed_io_list()
            if not self.async_write_mode:
                win32file.SetFilePointer(self.handle, offset, win32con.FILE_BEGIN)
                (rc , buf) = win32file.ReadFile(self.handle,length,None)
                if len(buf) != length or rc != 0:
                    DBG_WRN('win disk (%s) read FAILED(offset=%d, length=%d) win32 error code = %d' % (self.path, offset, length, rc))
                    buf = None
                return buf
            else:
                readOvlap = win32file.OVERLAPPED()
                readOvlap.hEvent = win32event.CreateEvent(None, 1, 0, None)
                readOvlap.Offset = offset
                readOvlap.OffsetHigh = offset >> 32
                (rc , buf) = win32file.ReadFile(self.handle,length,readOvlap)
                win32event.WaitForSingleObject(readOvlap.hEvent, win32event.INFINITE)
                return buf
        except:
            DBG_WRN('raw win disk read FAILED(offset=%d, length=%d)' % (offset, length))
            DBG_EXC()
            return None


    def flush(self):
        '''
        flush cache buffer
        '''
        self._clear_completed_io_list(True)

