#    
#    Module implementing a scsi simulator,
#    which can simulate all kinds of scsi device abnormal
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#

from scsi.scsi_proto import *
from comm.debug import *

#
# SCSI test case
#
class TestCase():
    '''
    class for scsi test case
    '''
    def __init__(self, tp, lba, nr, cnt, srt, interval = 100):
        self.lun    = None
        self.type   = tp            # which type to be simulated
        self.lba    = lba           # start logical block address
        self.len    = nr            # block length (-1 for the full range of device)
        self.count  = cnt           # how many time to be simulated (-1 for dead loop)
        self.start_count = srt      # start to simulate after this count
        # add for debug
        self.interval = 0           # interval count
        self.interval_back = interval # interval count

#
# All kinds of error types currently supported 
#
UNKNOW_ERROR_TYPE           = 0x00  # "Unknow error type"
CORRECT_READ_TRAN           = 0x01  # Correctable read, transient
CORRECT_READ_STICK          = 0x02  # Correctable read, sticky
UNCORRECT_READ_TRAN         = 0x03  # Uncorrectable read, transient
UNCORRECT_READ_STICK        = 0x04  # Uncorrectable read, sticky
CORRECT_WRITE_TRAN          = 0x05  # Correctable write, transient
CORRECT_WRITE_STICK         = 0x06  # Correctable write, sticky
UNCORRECT_WRITE_TRAN        = 0x07  # Uncorrectable write, transient
UNCORRECT_WRITE_STICK       = 0x08  # Uncorrectable write, sticky
HW_ERROR_TRAN               = 0x09  # Hardware error, transient
ILLEGAL_CMD_TRAN            = 0x0A  # Illegal command, transient
DISK_HANG_ON_READ           = 0x0B  # Disk hang on read
DISK_HANG_ON_WRITE          = 0x0C  # Disk hang on write
DISK_HANG_NOT_ON_CMD        = 0x0D  # Disk hang, not on a command
PWR_FAILURE                 = 0x0E  # Power failure during command
PHY_REMOVE_DISK             = 0x0F  # Physical removal of active disk
REQUEST_TIMEOUT_TRAN        = 0x10  # Request timeout, transient
REQUEST_TIMEOUT_STICK       = 0x11  # Request timeout, sticky

SCSI_CMD_BASE               = 0x12
SCSI_CMD_READ_6             = SCSI_CMD_BASE + READ_6            # Scsi read6 command
SCSI_CMD_READ_10            = SCSI_CMD_BASE + READ_10           # Scsi read10 command
SCSI_CMD_READ_12            = SCSI_CMD_BASE + READ_12           # Scsi read12 command
SCSI_CMD_READ_16            = SCSI_CMD_BASE + READ_16           # Scsi read16 command
SCSI_CMD_WRITE_6            = SCSI_CMD_BASE + WRITE_6           # Scsi write6 command
SCSI_CMD_WRITE_10           = SCSI_CMD_BASE + WRITE_10          # Scsi write10 command
SCSI_CMD_WRITE_12           = SCSI_CMD_BASE + WRITE_12          # Scsi write12 command
SCSI_CMD_WRITE_16           = SCSI_CMD_BASE + WRITE_16          # Scsi write16 command 
SCSI_CMD_VERIFY             = SCSI_CMD_BASE + VERIFY            # Scsi verify command
SCSI_CMD_REASSIGN_BLOCKS    = SCSI_CMD_BASE + REASSIGN_BLOCKS   # Scsi Reassign block command
#
# Error type description 
#
scsi_error_type_desc = {
    UNKNOW_ERROR_TYPE           : "Unknow-error-type",
    CORRECT_READ_TRAN           : "Correctable-read-transient",
    CORRECT_READ_STICK          : "Correctable-read-sticky",
    UNCORRECT_READ_TRAN         : "Uncorrectable-read-transient",
    UNCORRECT_READ_STICK        : "Uncorrectable-read-sticky",
    CORRECT_WRITE_TRAN          : "Correctable-write-transient",
    CORRECT_WRITE_STICK         : "Correctable-write-sticky",
    UNCORRECT_WRITE_TRAN        : "Uncorrectable-write-transient",
    UNCORRECT_WRITE_STICK       : "Uncorrectable-write-sticky",
    HW_ERROR_TRAN               : "Hardware-error-transient",
    ILLEGAL_CMD_TRAN            : "Illegal-command-transient",
    DISK_HANG_ON_READ           : "Disk-hang-on-read",
    DISK_HANG_ON_WRITE          : "Disk-hang-on-write",
    DISK_HANG_NOT_ON_CMD        : "Disk-hang-not-on-a-command",
    PWR_FAILURE                 : "Power-failure-during-command",
    PHY_REMOVE_DISK             : "Physical-removal-of-active-disk",
    REQUEST_TIMEOUT_TRAN        : "Request-timeout-transient",
    REQUEST_TIMEOUT_STICK       : "Request-timeout-sticky",
    SCSI_CMD_READ_6             : "Scsi-read6-command",
    SCSI_CMD_READ_10            : "Scsi-read10-command",
    SCSI_CMD_READ_12            : "Scsi-read12-command",
    SCSI_CMD_READ_16            : "Scsi-read16-command",
    SCSI_CMD_WRITE_6            : "Scsi-write6-command",
    SCSI_CMD_WRITE_10           : "Scsi-write10-command",
    SCSI_CMD_WRITE_12           : "Scsi-write12-command",
    SCSI_CMD_WRITE_16           : "Scsi-write16-command",
    SCSI_CMD_VERIFY             : "Scsi-verify-command",
    SCSI_CMD_REASSIGN_BLOCKS    : "Scsi-reassign-blocks-command"
}

def IS_TYPE(cmd, tc):
    '''
    check test case type
    '''
    __cmd_list = []

    # simulate scsi command
    if tc.type in scsi_error_type_desc and tc.type >= SCSI_CMD_BASE:
        return (tc.type - SCSI_CMD_BASE) == cmd.cdb[0]

    #    DISK_HANG_ON_READ
    #    DISK_HANG_ON_WRITE
    #    DISK_HANG_NOT_ON_CMD
    #    PWR_FAILURE
    #    PHY_REMOVE_DISK
    #    REQUEST_TIMEOUT_TRAN
    #    REQUEST_TIMEOUT_STICK

    if   tc.type == HW_ERROR_TRAN or \
         tc.type == ILLEGAL_CMD_TRAN:
        return True
    elif tc.type == CORRECT_READ_TRAN or\
         tc.type == CORRECT_READ_STICK or\
         tc.type == UNCORRECT_READ_TRAN or\
         tc.type == UNCORRECT_READ_STICK:
        __cmd_list = (READ_6, READ_10, READ_12, READ_16, READ_BUFFER)
    elif tc.type == CORRECT_WRITE_TRAN or \
         tc.type == CORRECT_WRITE_STICK or \
         tc.type == UNCORRECT_WRITE_TRAN or \
         tc.type == UNCORRECT_WRITE_STICK:
        __cmd_list = (WRITE_6, WRITE_10, WRITE_12, WRITE_VERIFY_12, WRITE_16, WRITE_VERIFY, WRITE_BUFFER)

    for i in __cmd_list:
        if cmd.cdb[0] == i:
            return True
    return False

def IS_RANGE(cmd, tc):
    '''
    check scsi block range
    '''
    ret = False
    lba = SCSI_LBA(cmd.cdb)
    nr = SBC_LEN(cmd.cdb) 
    begin = tc.lba
    end = min(tc.lba + tc.len, tc.lun.capacity)

    if tc.len == -1 or \
       (lba >= begin and lba < end) or \
       (lba + nr >= begin and lba + nr < end):
        ret = True
    return ret 

def IS_START(tc):
    '''
    check test case count
    '''
    if tc.start_count > 0:
        tc.start_count -= 1
        return False

    if tc.count == -1:
        return True

    if   tc.type >= SCSI_CMD_BASE:
        return tc.count > 0

    elif tc.type == DISK_HANG_ON_READ or \
         tc.type == DISK_HANG_ON_WRITE or \
         tc.type == DISK_HANG_NOT_ON_CMD:
        return tc.count > 0

    elif tc.type == CORRECT_READ_TRAN or \
         tc.type == UNCORRECT_READ_TRAN or \
         tc.type == CORRECT_WRITE_TRAN or \
         tc.type == UNCORRECT_WRITE_TRAN or \
         tc.type == HW_ERROR_TRAN or \
         tc.type == ILLEGAL_CMD_TRAN or \
         tc.type == REQUEST_TIMEOUT_TRAN:
        return tc.count > 0

    elif tc.type == CORRECT_READ_STICK or \
         tc.type == UNCORRECT_READ_STICK or \
         tc.type == CORRECT_WRITE_STICK or \
         tc.type == UNCORRECT_WRITE_STICK or \
         tc.type == REQUEST_TIMEOUT_STICK or \
         tc.type == PWR_FAILURE or \
         tc.type == PHY_REMOVE_DISK:
        return True

def IS_INTERVAL(tc):
    '''
    check interval count
    '''
    if tc.interval == 0:
        tc.interval = tc.interval_back
        return True
    else:
        tc.interval -= 1
        return False

def DEC_COUNT(tc):
    if tc.count > 0:
        tc.count -= 1

def Sim_SCSI_Error(cmd, tc):
    '''
    simulate scsi error
    @param cmd: scsi request
    @param tc: test case
    @return: True for success to simulate this test case
             False for Failed to simulate, need to run this command normally.
    '''

    ret = True

    if tc.type >= SCSI_CMD_BASE:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, HARDWARE_ERROR, 0x0900)
        DEC_COUNT(tc)
    elif  tc.type == HW_ERROR_TRAN:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, HARDWARE_ERROR, 0x5D10)
        DEC_COUNT(tc)
    elif tc.type == ILLEGAL_CMD_TRAN:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2008)
        DEC_COUNT(tc)
    # read
    elif tc.type == CORRECT_READ_TRAN:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x1000)
        DEC_COUNT(tc)
    elif tc.type == CORRECT_READ_STICK:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, MEDIUM_ERROR, 0x1000)
    elif tc.type == UNCORRECT_READ_TRAN:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x110A)
        DEC_COUNT(tc)
    elif tc.type == UNCORRECT_READ_STICK:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, MEDIUM_ERROR, 0x110A)
    # write
    elif tc.type == CORRECT_WRITE_TRAN:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x1000)
        DEC_COUNT(tc)
    elif tc.type == CORRECT_WRITE_STICK:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, MEDIUM_ERROR, 0x1000)
    elif tc.type == UNCORRECT_WRITE_TRAN:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x0C08)
        DEC_COUNT(tc)
    elif tc.type == UNCORRECT_WRITE_STICK:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, MEDIUM_ERROR, 0x0C08)
    # unknow
    else:
        DBG_WRN('Usage unknow test case type!')
        ret = False

    if ret:
        DBG_SIM('LUN:%d' % tc.lun.id, scsi_error_type_desc[tc.type])

    return ret

def Check_EXE_Cmd(cmd):
    '''
    check and simulate scsi request
    @param cmd: scsi request
    @return: Success, scsi request has been simulate, don't need to execute this request
             Failed, need to execute this request normally
    '''
    ret = False
    
    if not cmd.lun:
        return ret

    cmd.lun.tc_lock()
    for tc in cmd.lun.test_case:
        if IS_TYPE(cmd, tc) and \
           IS_RANGE(cmd, tc) and \
           IS_START(tc) and \
           IS_INTERVAL(tc):
            ret = Sim_SCSI_Error(cmd, tc)
            if ret: break
    cmd.lun.tc_unlock()
    return ret