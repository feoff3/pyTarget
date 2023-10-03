#
#    general scsi device, as base class for all kinds of scsi devices.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-03-18)
#

from comm.dev_file import DevFile
from scsi.scsi_proto import *
from comm.debug import *


class TIO():
    '''
    target i/o request for scsi layer and scsi device communications
    '''
    def __init__(self, length=0, buffer='', offset=0):
        '''
        initialize request
        @param length: request length (in block/byte)
        @param buffer: data buffer
        '''
        self.offset = offset        # I/O offset
        self.length = length        # I/O rength
        self.buffer = buffer        # I/O buffer
        self.status = NO_SENSE      # scsi status
        self.sen_code = 0           # scsi sense code
        self.sen_info = 0           # sense info

    def set_sense(self, key, code, info=0):
        '''
        set tio sense 
        '''
        self.status = key
        self.sen_code = code
        self.sen_info = info


class Lun(DevFile):
    '''
    Class for virtual scsi lun device
    '''

    def __init__(self, id, type, path):
        '''
        Virtual scsi lun device constructor
        @param id: device id
        @param type: device type (refer file scsi_lib 'DEVICE TYPES') 
        @param path: virtual device file path in fs
        '''
        DevFile.__init__(self, path)
        self.id = id
        self.type = type
        self.protect = False
        self.path = path
        self.ready = True
        self.prevent = False
        self.test_case = []
        self.__tc_lock = threading.Lock()

        # 2010-11-24
        self.offline = False
        self.reset = False
        self.sense_buffer = [0] * SENSE_SIZE

    # 2010-11-24
    def set_sense(self, key, code):
        self.sense_buffer = [0] * SENSE_SIZE
        if True:
            self.sense_buffer[0] = 0x72   # descriptor, current
            self.sense_buffer[1] = key
            self.sense_buffer[2] = S_ASC(code)
            self.sense_buffer[3] = S_ASC(code)
        else:
            self.sense_buffer[0] = 0x70   # fixed, current
            self.sense_buffer[2] = key
            self.sense_buffer[12] = S_ASC(code)
            self.sense_buffer[13] = S_ASC(code)

    def initial(self):
        '''
        Initialize scsi device (do nothing)
        '''
        return True

    def is_protect(self):
        '''
        check if lun is protected
        '''
        return self.protect
    
    def set_protect(self):
        '''
        set protected type
        '''
        self.protect = True
        
    def set_not_protect(self):
        '''
        set non-protected type
        '''
        self.protect = False

    def is_ready(self):
        '''
        check if lun is ready
        '''
        return self.ready

    def set_ready(self):
        '''
        set lun ready
        '''
        self.ready = True

    def set_noready(self):
        '''
        set lun not ready
        '''
        #self.ready = False
        pass


    def AddTestCase(self, tc):
        '''
        Add scsi test case
        @param tc: scsi test case (refer scsi_simulator file) 
        '''
        self.tc_lock()
        tc.lun = self
        self.test_case.append(tc)
        self.tc_unlock()
        DBG_SIM('Add test case:', 'LUN:%d' % self.id, tc.type, tc.lba, tc.len, tc.count, tc.start_count)
        return True


    def ResetTestCase(self):
        '''
        Clear all scsi test case
        '''
        self.tc_lock()
        self.test_case = []
        self.tc_unlock()
        DBG_SIM("Reset LUN:%d clear all test case." % self.id)


    def tc_lock(self):
        '''
        Test case list lock
        '''
        self.__tc_lock.acquire()

    def tc_unlock(self):
        '''
        Test case list unlock
        '''
        self.__tc_lock.release()