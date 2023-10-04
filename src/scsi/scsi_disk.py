#
#    scsi disk device implementation code
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-03-18)
#

import random
from scsi.scsi_dev import *

class Disk(Lun):
    '''
    Class for virtual scsi disk device
    '''

    def __init__(self, id, cap, dev):
        '''
        initialize scsi disk device
        @param id: device id
        @param cap: device capacity
        @param dev: virtual device object DevFile
        '''
        Lun.__init__(self, id, TYPE_DISK, dev)
        self.capacity = cap
        self.__defect_list_init()


    def __defect_list_init(self):
        '''
        initialize scsi disk glist
        '''
        cnt = random.randint(0, 0xff)
        self.glist_max = 4096
        self.plist = []
        self.glist = []
        for i in range(0, cnt):
            self.plist.append(random.randint(0, self.capacity))


    def is_outrange(self, lba, len):
        '''
        check if address out of range.
        '''
        return (lba + len > self.capacity)


    def initial(self, force=False):
        '''
        Initialize disk
        @param force: force to initialize disk
        @return: True for success, False for failed
        '''
        if force or self.dev.size() < (long(self.capacity) << BLOCK_SHIFT):
            #TODO: now it works for files, fix that for non-expandable devices
            buf = '\x00' * BLOCK_SIZE
            i = long(0)
            while i < self.capacity + 1:
                if self.dev.write(long(i) << BLOCK_SHIFT, buf) == False: 
                    return False
                i = i + 1
        DBG_PRN('Disk(%s)' % self.path, ': initialize finish!')
        return True


    def Write(self, tio):
        '''
        write data to scsi disk
        @param tio: target io request
        @return: True for success, False for failed
        '''
        if self.is_protect():
            DBG_WRN('Write protected disk')
            tio.set_sense(DATA_PROTECT, 0x2700)
            return False
        buf = tio.buffer
        lba = tio.offset
        if tio.buffer == None or len(tio.buffer) == 0:
            return True
        if self.is_outrange(lba, (len(buf) >> BLOCK_SHIFT)):
            tio.set_sense(ILLEGAL_REQUEST, 0x2400)
            DBG_WRN('disk(%s) write FAILED, overflow(offset=%d, length=%d, cap=%d)' % (self.path, lba, len(buf) >> BLOCK_SHIFT, self.capacity))
            ret = False
        else:
            self.lock()
            ret = self.dev.write(long(lba) << BLOCK_SHIFT, buf)
            self.unlock()
            if not ret:
                tio.set_sense(MEDIUM_ERROR, 0x0C00)
                DBG_WRN('disk(%s) write FAILED(offset=%d, length=%d, cap=%d)' % (self.path, lba, len(buf) >> BLOCK_SHIFT, self.capacity))
        return ret


    def Read(self, tio):
        '''
        read data from scsi disk
        @param tio: target io request
        @return: True for success, False for failed
        '''
        lba = tio.offset
        nr = tio.length
        if self.is_outrange(lba, nr):
            tio.set_sense(ILLEGAL_REQUEST, 0x2400)
            DBG_WRN('disk(%s) read FAILED, overflow(offset=%d, length=%d, cap=%d)' % (self.path, lba, nr, self.capacity))
            return False
        self.lock()
        tio.buffer = self.dev.read(long(lba) << BLOCK_SHIFT, nr<<BLOCK_SHIFT)
        if not tio.buffer:
            tio.set_sense(MEDIUM_ERROR, 0x1100)
            DBG_WRN('disk(%s) read FAILED(offset=%d, length=%d, cap=%d)' % (self.path, lba, nr, self.capacity))
        self.unlock()
        return not not tio.buffer 

    def AddGlist(self, lba):
        '''
        Add logical block address into glist
        @param lba: logical block address
        '''
        if len(self.glist) >= self.glist_max or lba >= self.capacity:
            DBG_WRN('Reassign block:', lba, 'FAILED')
            return False
        else:
            self.glist.append(lba)
            DBG_PRN('Reassign block:', lba)
            return True