#    
#    general scsi library
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#    Add tape for VTL(virtual tape library) by Wu.Qing-xiu (2010-02-18)
#

from scsi.scsi_comm import *
from scsi.scsi_proto import *
from scsi.scsi_dev import TIO
from comm.debug import *

#
# iSCSI device vendor 1info
#
DEVICE_VENDOR  = 'pyTarget'                     # SCSI device vendor info (8-byte)
DEVICE_PRODUCT = 'iSCSI-device    '             # SCSI device vendor info ('16-byte')
DEVICE_VERSION = '1.5 '                         # SCSI device reversion (4-byte)


#
# scsi request (for initiator)
#
INTR_SCSI_STATE_NEW      = 0
INTR_SCSI_STATE_PENDING  = 1
INTR_SCSI_STATE_FINISH   = 2
INTR_SCSI_STATE_FAILED   = -1

#
# create scsi sense
#
def new_sense(key, asc, info = 0x00):
    '''
    Create scsi sense data
    @param key: sense key
    @param asc: additional sense code/additional sense code qualifier 
    @param info: sense info
    '''
    sense = [0] * 0x28
    sense[1]    = 0x26                          # sense length-l
    sense[2]    = 0xf0                          # sense valid
    sense[4]    = key & 0xff                    # sense key
    sense[5:9]  = hex_2_array(info, 4)            # Sense Info
    sense[9]    = 0x1e                          # additional sense length:
    sense[14]   = S_ASC(asc)                    # additional sense code
    sense[15]   = S_ASCQ(asc)                   # additional sense code qualifier
    return do_pack(sense)


class ScsiReq():
    '''
    scsi request (for initiator)
    '''
    def __init__(self, conn, lun, cdb, exp_len):
        '''
        @param conn: connection
        @param lun: lun 
        @param cdb: scsi cdb
        @param exp_len: extect data length
        '''

        # scsi task attribute
        self.id = conn.session.next_itt()             # task id
        self.lun = lun                              # lun
        self.cdb = cdb                              # CDB
        self.in_buf = None                          # data in buffer
        self.out_buf = None                         # data out buffer
        self.exp_len = exp_len                      # expect data length
        self.sense = None                           # scsi sense
        self.status = SAM_STAT_GOOD                 # scsi status
        self.attr = 0                               # scsi attribute
        self.state = INTR_SCSI_STATE_NEW            # scsi task state

        # scsi task management
        self.connect = conn                         # connect
        self.tid = 0xffffffff                       # TTT
        self.all_len  = 0                           # scsi request length
        self.next_len = 0                           # iscsi next request length
        self.r2t_len  = 0                           # r2t solicit request length


#
# scsi command descriptor (for target)
#
class ScsiCmd():
    '''
    scsi command descriptor (for target)
    '''
    def __init__(self, conn, pdu):
        '''
        @param conn: connection
        @param pdu: iscsi pdu
        '''
        # scsi task attribute
        self.id      = pdu.get_itt()                # scsi task id
        self.tid     = conn.session.next_ttt()      # iscsi task id
        self.cdb     = pdu.bhs[32:48]               # CDB
        self.in_buf  = None                         # data in buffer
        self.out_buf = None                         # data out buffer
        self.sense   = None                         # scsi sense
        self.status  = SAM_STAT_GOOD                # scsi status (low layer status)
        self.state   = 0                            # scsi task state

        # scsi task management
        self.retain_time = None                     # for error recovery
        self.lun = conn.host.find_lun(pdu.bhs[9])     # Lun, maybe none, careful !!!
        self.connect  = conn                        # connect
        self.all_len  = pdu.get_exp_len()           # scsi request length
        self.next_len = 0                           # iscsi next request length
        self.r2t_sn   = 0                           # r2t sn
        self.pdu      = pdu                         # iscsi request pdu
        self.data_pdu = []                          # data pdu list

    def set_sense(self, status, key, asc, info = 0x00):
        '''
        Add scsi sense data into scsi_cmd
        @param status: scsi_cmd status
        @param key: sense key
        @param asc: additional sense code/additional sense code qualifier
        @param info: scsi sense info
        '''
        self.status = status
        self.sense = new_sense(key, asc, info)

    def check_lun(self, type=TYPE_DISK, status=False):
        '''
        check lun is exist and lun's type is the same as the special type
        @param type: None for all
        @param status: need to check lun stauus
        @return: True for success, False for failed
        '''
        if self.lun == None:
            self.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2009)
            return False
        elif type and self.lun.type != type:
            self.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2500)
            return False
        elif status and self.lun.is_ready() == False:
            self.set_sense(SAM_STAT_CHECK_CONDITION, NOT_READY, 0x3A00)
            return False
        return True

    def check_tio(self, tio):
        '''
        check tio, and update sense
        '''
        if tio.status != NO_SENSE:
            self.set_sense(SAM_STAT_CHECK_CONDITION,
                           tio.status,
                           tio.sen_code,
                           tio.sen_info)
# scsi read commands
def IS_READ(code):
    __list = (READ_6, READ_10, READ_12, READ_16)
    return (code in __list)

# scsi write commands
def IS_WRITE(code):
    __list = (WRITE_6, WRITE_10, WRITE_12, WRITE_16)
    return (code in __list)

# data in commands
def IS_IN_IOCMD(code):
    __list = (REPORT_LUNS, INQUIRY, READ_CAPACITY, MODE_SENSE,
              READ_DEFECT_DATA, RECEIVE_DIAGNOSTIC,
              READ_BLOCK_LIMITS, READ_POSITION, REQUEST_SENSE, SERVICE_ACTION_IN)
    return IS_READ(code) or (code in __list)

# data out commands
def IS_OUT_IOCMD(code):
    __list = (REASSIGN_BLOCKS, VERIFY, MODE_SELECT)
    return IS_WRITE(code) or (code in __list)

# non io commands
def IS_NOT_IOCMD(code):
    return (not IS_IN_IOCMD(code) and not IS_OUT_IOCMD(code))


def NEW_CDB(cmd):
    cdb = [0] * 16
    cdb[0] = cmd
    return cdb

#=======================================================
#                     Report Lun
#=======================================================
def ReportLunReq(conn):
    '''
    scsi report lun request
    '''
    length = 256 * 8
    cdb = NEW_CDB(REPORT_LUNS)
    cdb[6:10] = hex_2_array(length, 4)
    cmd = ScsiReq(conn, 0, cdb, length)
    return cmd

def lun_rep(cmd):
    '''
    get lun list from response
    '''
    lst = []
    if is_cmd_good(cmd) and is_cmd_buff(cmd, 4):
        cnt = byte_2_hex(cmd.in_buf, 0, 4) // 8
        for i in range(cnt):
            if (i + 2) * 8 <= len(cmd.in_buf):
                lun = byte_2_hex(cmd.in_buf, (i + 1) * 8 + 1, 1)
                lst.append(lun)
    return lst

def __ReportLunRsp(cmd):
    '''
    scsi report lun response
    '''
    lun_list = cmd.connect.host.lun_list
    lock = cmd.connect.host.lun_list_lock
    limit = ALLOCATE_LEN(cmd.cdb) 

    cnt = len(lun_list)
    buf = '\x00' * (cnt + 1) * 8
    buf = hex_2_byte(buf, 0, 4, cnt * 8)
    lock.acquire()
    for i in range(cnt):
        buf = hex_2_byte(buf, (i + 1) * 8 + 1, 1, lun_list[i].id)
    lock.release()
    cmd.out_buf = buf[:min(limit, len(buf))]
    cmd.status = SAM_STAT_GOOD


#=======================================================
#                         Inquiry 
#=======================================================
def InquiryReq(conn, id, vpd, page):
    '''
    scsi Inquiry lun request
    '''
    length = 255
    cdb = [0] * 16
    cdb[0] = INQUIRY
    if vpd:
        cdb[1] |= 0x01
        cdb[2] = page & 0xff
    cdb[3:5] = hex_2_array(length, 2)
    cmd = ScsiReq(conn, id, cdb, length)
    return cmd

def __InquiryRsp(cmd):
    '''
    scsi Inquiry lun response
    '''
    lun = cmd.lun
    cdb = cmd.cdb
    data = []
    cmd.status = SAM_STAT_GOOD

    if (cdb[1] & 0x3 == 0x03 or
        cdb[1] & 0x3 == 0x00 and cdb[2]):
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2400)
        return

    if not cmd.check_lun(None):
        return

    if (cdb[1] & 0x01):
        if cdb[2] == 0x00:
            data = [0] * 7
            data[0] = lun.type                      # Device Type
            data[3] = 7 - 4                         # Page Length: 3
            data[4] = 0x00                          # Supported Page: Supported Vital Product Data Pages
            data[5] = 0x80                          # Supported Page: Unit Serial Number Page
            data[6] = 0x83                          # Supported Page: Device Identification Page
        elif cdb[2] == 0x80:
            data = [0] * 20
            data[0] = lun.type                      # Device Type
            data[1] = 0x80                          # Page Code
            data[3] = 0x10                          # Page Length: 16
            data[4:20] = [0x30] * 16                # Product Serial Number
            data[7] = 0x31
            data[19] = lun.id
        elif cdb[2] == 0x83:
            data = [0] * 16
            data[0] = lun.type                      # Device Type
            data[1] = 0x83                          # Page Code: Device Identification Page
            data[3] = 0x0C                          # Page Length: 12
            data[4] = 0x01                          # Code Set: Identifier field contains binary values
            data[5] = 0x03                          # Association: Identifier is associated with addressed logical/physical device
            data[7] = 0x08                          # Identifier Length: 8
            data[9] = 0x01
            data[15] = lun.id                       # Identifier[8-15]
        else:
            cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2400)
    else:
        data = [0] * 58
        data[0] = lun.type                          # Peripheral
        data[4] = 58 - 5                            # Additional Length
        data[7] = 0x32                              # Flags: 0x32  Sync  CmdQue
        data[8:16]  = do_unpack(DEVICE_VENDOR)      # Vendor Id
        data[16:32] = do_unpack(DEVICE_PRODUCT)     # Product Id
        data[32:36] = do_unpack(DEVICE_VERSION)     # Product Revision Level

        if is_disk(lun):
            data[1] = 0x00                          # Flags
            data[2] = 0x04                          # Version: Compliance to SPC-2 (0x04)
            data[3] = 0x42                          # Flags: 0x42, TrmTsk, Response Data Format: SPC-2/SPC-3
        elif is_changer(lun):
            data[1] = 0x00
            data[2] = 0x02
            data[3] = 0x52
        elif is_tape(lun):
            data[1] = 0x80                          # Removable: This is a REMOVABLE device
            data[2] = 0x02                          # Version: Compliance to ANSI X3.131:1994 (0x02)
            data[3] = 0x12                          # Flags: 0x12, HiSup, Response Data Format: SPC-2/SPC-3

    if len(data):
        cmd.out_buf = do_pack(data)


#=======================================================
#                     Test Unit Ready
#=======================================================
def TestUnitReadyReq(conn, id):
    '''
    scsi test unit ready request
    '''
    cdb = NEW_CDB(TEST_UNIT_READY)
    cmd = ScsiReq(conn, id, cdb, 0)
    return cmd
    
def lun_tur(cmd):
    '''
    get lun status from tur command
    '''
    return is_cmd_good(cmd)

def __TestUnitReadyRsp(cmd):
    '''
    scsi test unit ready response
    '''
    cmd.status = SAM_STAT_GOOD
    if cmd.check_lun(None, True):
        if is_tape(cmd.lun) and not cmd.lun.is_load():
            cmd.set_sense(SAM_STAT_CHECK_CONDITION, NOT_READY, 0x3A00)


#=======================================================
#                     Read Capacity
#=======================================================
def ReadCapacityReq(conn, id):
    '''
    scsi read capacity request
    '''
    cdb = NEW_CDB(READ_CAPACITY)
    cmd = ScsiReq(conn, id, cdb, 8)
    return cmd

def lun_cap(cmd):
    '''
    get lun capacity and block size from cap response
    '''
    blk_cap  = 0
    blk_size = 0
    if (is_cmd_good(cmd) and is_cmd_buff(cmd, 8)):
        blk_cap = byte_2_hex(cmd.in_buf, 0, 4)
        blk_size = byte_2_hex(cmd.in_buf, 4, 4)
    return blk_cap, blk_size

def __ReadCapacityRsp(cmd):
    '''
    scsi read capacity response
    '''
    cmd.status = SAM_STAT_GOOD
    if cmd.check_lun(TYPE_DISK):
        if (cmd.lun.capacity > 0xffffffff):
            cmd.out_buf = u32_buf(0xffffffff)
        else:
            cmd.out_buf = u32_buf(cmd.lun.capacity - 1)
        cmd.out_buf += u32_buf(cmd.lun.sector_size)

def __ReadCapacity16Rsp(cmd):
    '''
    scsi read capacity response
    '''
    cmd.status = SAM_STAT_GOOD
    bytes_expected = cmd.cdb[13]
    if cmd.check_lun(TYPE_DISK):
        cmd.out_buf = u64_buf(cmd.lun.capacity - 1)
        cmd.out_buf += u32_buf(cmd.lun.sector_size)
        if bytes_expected > 12:
            cmd.out_buf += u8_buf(0)
            # here we get the physical sector alignment info
            # calc log of how many logical sectors are in one phys sector
            phys_sector_size = cmd.lun.physical_sector_size 
            logical_sectors_per_physical = phys_sector_size / cmd.lun.sector_size
            #print("logical_sectors_per_physical = " + str(logical_sectors_per_physical))
            logarithm = 0
            while logical_sectors_per_physical > 1:
                logical_sectors_per_physical >>= 1
                logarithm+=1
            #print("logarithm = " + str(logarithm))
            cmd.out_buf += u8_buf(logarithm)
        if bytes_expected > 14:
            cmd.out_buf += bytearray(bytes_expected - 14)

#=======================================================
#                Read Block Limits
#=======================================================
def ReadBlockLimitReq(conn, id):
    '''
    Read Block Limits request
    '''
    cdb = NEW_CDB(READ_BLOCK_LIMITS)
    cmd = ScsiReq(conn, id, 6)
    return cmd

def __ReadBlockLimitRsp(cmd):
    '''
    Read block limit response
    '''
    cmd.status = SAM_STAT_GOOD
    if cmd.check_lun(TYPE_TAPE):
        data = [0] * 6
        data[1:4] = hex_2_array(0xfffffc, 3)          # MAXIMUM BLOCK LENGTH LIMIT
        data[5] = 0x01                              # MINIMUM BLOCK LENGTH LIMIT
        cmd.out_buf = do_pack(data)


#=======================================================
#                     Request Sense
#=======================================================
def RequestSenseReq(conn, id):
    cdb = NEW_CDB(REQUEST_SENSE)
    cdb[4] = 0x1d
    return ScsiReq(conn, id, 0x1d)

def __RequestSenseRsp(cmd):
    '''
    scsi request sense response
    '''
    cmd.status = SAM_STAT_GOOD
    if cmd.check_lun(None):
        buf = [0] * 29
        if is_tape(cmd.lun):
            buf[2] = 0x40
        buf[0] = 0x70
        buf[7] = 0x16
        buf[18] = 0x86
        buf[19] = 0x11
        buf[20] = 0xdb
        buf[23] = 0x2a
        buf[24] = 0xc7
        buf[26] = 0x01
        cmd.out_buf = do_pack(buf)


#=======================================================
#                     Mode Sense
#=======================================================
def ModeSenseReq(conn, id, dbd, pc, page):
    '''
    scsi mode sense request
    '''
    length = 255
    cdb = NEW_CDB(MODE_SENSE)
    cdb[1] |= (dbd << 3) & 0xff
    cdb[2] |= ((pc << 6) | page) & 0xff
    cdb[4] = length
    cmd = ScsiReq(conn, id, cdb, length)
    return cmd

def __ModeSenseRsp(cmd):
    '''
    scsi mode sense response
    '''
    data = []
    cdb = cmd.cdb
    lun = cmd.lun
    cmd.status = SAM_STAT_GOOD
    dbd = cdb[1] & 0x08                                 # disable block descriptors field (1: must not return block address)

    if not cmd.check_lun(None):
        return

    if cdb[2] == 0x00:                              	# SPC-2 Page Code: Vendor Specific Page (0x00)
        if cmd.check_lun(TYPE_TAPE):
            block_size = lun.get_block_size()
            data = [0] * 12
            data[0] = 11                                # Mode Data Length: 11
            data[1] = 0x86                              # Medium Type: 0x86
            data[2] = 0x10                              # Device-Specific Parameter: 0x10
            data[3] = 8                                 # Block Descriptor Length: 8
            data[9:12] = hex_2_array(block_size, 3)       # Block Length
        else:
            cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2400)
    elif cdb[2] == 0x0f:                                # SSC-2 Page Code: Data Compression (0x0f)
        if cmd.check_lun(TYPE_TAPE):
            block_size = lun.get_block_size()
            if dbd == 0:                                # DBD = 0
                offset = 8
                data = [0] * 28
                data[0] = 27                            # Mode Data Length: 27
                data[3] = 0x08                          # Block Descriptor Length: 0
                data[9:12] = hex_2_array(block_size, 3)   # Block Length
            else:
                offset = 0
                data = [0] * 20
                data[0] = 19                            # Mode Data Length: 19
                data[3] = 0x00                          # Block Descriptor Length: 0
            data[1] = 0x86                              # Medium Type: 0x86
            data[2] = 0x10                              # Device-Specific Parameter: 0x10
            data[4 + offset] = 0x0f                     # SSC-2 Page Code: Data Compression (0x0f)
            data[5 + offset] = 0x0e                     # Page Length: 14
            data[6 + offset] = 0xc0                     # DCE: 1, DCC: 1
            data[7 + offset] = 0x80                     # DDE: 1, RED: 0            
            data[11 + offset] = 0x10                    # Compression algorithm: IBM IDRC
            data[15 + offset] = 0x10                    # Decompression algorithm: IBM IDRC
        else:
            cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2400)                                   
    elif cdb[2] == 0x10:                                # SSC-2 Page Code: Device Configuration (0x10)
        if cmd.check_lun(TYPE_TAPE):
            block_size = lun.get_block_size()
            if dbd == 0:                                # DBD = 0
                offset = 8
                data = [0] * 28
                data[0] = 27                            # Mode Data Length: 27
                data[3] = 0x08                          # Block Descriptor Length
                data[9:12] = hex_2_array(block_size, 3)   # Block Length
            else:
                offset = 0
                data = [0] * 20
                data[0] = 19                            # Mode Data Length: 19
                data[3] = 0x00                          # Block Descriptor Length
            data[1] = 0x86                              # Medium Type: 0x86
            data[2] = 0x10                              # Device-Specific Parameter                
            data[4 + offset] = 0x10                     # Page Code
            data[5 + offset] = 0x0e                     # Page Length: 14
            data[6 + offset] = 0x00                     # CAF: 0, Active Format: 0
            data[7 + offset] = 0x00                     # Active Partition: 0
            data[8 + offset] = 0x00                     # Write Object Buffer Full Ratio: 0
            data[9 + offset] = 0x00                     # Read Object Buffer Empty Ratio: 0
            data[11 + offset] = 0x64                    # Write Delay time: 100 100ms
            data[12 + offset] = 0x40                    # OBR: 0, LOIS: 1, RSMK: 0, AVC: 0, SOCF: 0, ROBO: 0, REW: 0
            data[13 + offset] = 0x00                    # Gap Size: 0
            data[14 + offset] = 0x18                    # EOD Defined: 0, EEG: 1, SEW: 1, SWP: 0, BAML: 0, BAM: 0
            data[17 + offset] = 0x00                    # Object Buffer Size At Early Warning: 0
            data[18 + offset] = 0x01                    # Select Data Compression Algorithm: 1
            data[19 + offset] = 0x00                    # OIR: 0, ReWind on Reset: 0, ASOCWP: 0, PERSWP: 0, PRMWP: 0
        else:
            cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2400)                 
    elif cdb[2] == 0x08:
        data = [0] * 4
        data[0] = 3
    elif cdb[2] == 0x1C:                                # SPC-2 Page Code: Informational Exceptions Control (0x1c)
        if cmd.check_lun(TYPE_DISK):
            data = [0] * 4
            data[0] = 3
            if lun.is_protect():
                data[2] = 0x80                          # protect
        else:
            cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2400)
    elif cdb[2] == 0x3f:                                # SPC-2 Page Code: Return All Mode Pages
        if cmd.check_lun(TYPE_DISK):
            data = [0] * 0x53
            data[0] = 0x52                              # Mode Data Length: 82
            data[4] = 0x03                              # SBC-2 Page Code: Format Device (0x03)
            data[5] = 0x16                              # Page Length: 22
            data[14] = 0x01                             # Sectors Per Track: 256
            data[16] = 0x02                             # Data Bytes Per Physical Sector: 512
            data[28] = 0x04                             # SBC-2 Page Code: Rigid Disk Geometry (0x04)
            data[29] = 0x16                             # Page Length: 22
            data[32] = 0x31                             # Number of Cylinders: 49
            data[33] = 0x10                             # Number of Heads: 16
            data[48] = 0x1c                             # Medium Rotation Rate: 7200
            data[49] = 0x20                             # Medium Rotation Rate: 7200
            data[52] = 0x08                             # SBC-2 Page Code: Caching (0x08)
            data[53] = 0x12                             # Page Length: 18
            data[71] = 0x0a                             # Non-Cache Segment Size: 10
            data[72] = 0x0a                             # SPC-2 Page Code: Control (0x0a)
            data[75] = 0x02                             # Disable Queuing: 0
            if lun.is_protect():
                data[2] = 0x80                          # protect
        else:
            cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2400)
    else:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2500)

    if len(data):
        cmd.out_buf = do_pack(data)


#=======================================================
#                         Verify
#=======================================================
def VerifyReq(conn, id, lba, len):
    cdb = NEW_CDB(VERIFY)
    return ScsiReq(conn, id, cdb, 0)

def __VerifyRsp(cmd):
    '''
    scsi varify response
    '''
    cmd.status = SAM_STAT_GOOD
    cmd.check_lun(TYPE_DISK, True)


#=======================================================
#                     SCSI Read
#=======================================================
def Read10Req(conn, id, lba, length):
    '''
    SBC4 Read10 request
    '''
    cdb = NEW_CDB(READ_10)
    cdb[2:6] = hex_2_array(lba, 4)
    cdb[7:9] = hex_2_array(length, 2)
    cmd = ScsiReq(conn, id, cdb, length * BLOCK_SIZE)
    return cmd

def SSC_Read10Req(conn, id, blk_size, length):
    '''
    SSC4 Read10 request
    '''
    cdb = NEW_CDB(READ_6)
    if length % blk_size == 0:
        size = length // blk_size
        cdb[1] |= 0x01
    else:
        size = length
    cdb[2:5] = hex_2_array(size, 3)
    cmd = ScsiReq(conn, id, cdb, length)
    return cmd

def __Read10Rsp(cmd):
    '''
    SBC/SSC4 Read6/10/12/16/etc response
    '''
    cdb = cmd.cdb
    lun = cmd.lun
    cmd.status = SAM_STAT_GOOD

    if not cmd.check_lun(None, True):
        return

    if is_disk(lun):
        tio = TIO(SBC_LEN(cdb), '', SCSI_LBA(cdb))
        lun.Read(tio)
        cmd.out_buf = tio.buffer
        cmd.check_tio(tio)
    elif is_tape(lun):
        tio = TIO(SSC_LEN(cdb))
        if cdb[1] & 0x01:
            tio.length *= lun.get_block_size()
        lun.Read(tio)
        cmd.out_buf = tio.buffer
        cmd.check_tio(tio)
    else:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2500)
 

#=======================================================
#                     SCSI Write
#=======================================================
def Write10Req(conn, id, lba, buf):
    '''
    SBC4 Write10 request
    '''
    length = len(buf)
    cdb = NEW_CDB(WRITE_10)
    cdb[2:6] = hex_2_array(lba, 4)
    cdb[7:9] = hex_2_array(length // BLOCK_SIZE, 2)
    cmd = ScsiReq(conn, id, cdb, length)
    cmd.out_buf = buf
    return cmd

def SSC_WriteReq(conn, id, blk_size, buf):
    '''
    SSC write request
    '''
    cdb = NEW_CDB(WRITE_6)
    if (len(buf) % blk_size):
        cdb[2:5] = hex_2_array(len(buf), 3)
    else:
        cdb[1] = 0x01
        cdb[2:5] = hex_2_array(len(buf) / blk_size, 3)
    cmd = ScsiReq(conn, id, cdb, len(buf))
    cmd.out_buf = buf
    return cmd

def __Write10Rsp(cmd):
    '''
    SBC/SSC4 Write6/10/12/16/etc response
    '''
    cdb = cmd.cdb
    lun = cmd.lun
    cmd.status = SAM_STAT_GOOD

    if not cmd.check_lun(None, True):
        return
    if is_disk(lun):
        tio = TIO(SBC_LEN(cdb), cmd.in_buf, SCSI_LBA(cdb))
        lun.Write(tio)
        cmd.check_tio(tio)
    elif is_tape(lun):           
        tio = TIO(len(cmd.in_buf), cmd.in_buf)
        lun.Write(tio)
        cmd.check_tio(tio)
    else:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2500)


#=======================================================
#                     synchronize cache
#=======================================================
def __SyncCacheRsp(cmd):
    '''
    scsi synchronize cache response
    '''
    cmd.status = SAM_STAT_GOOD
    cmd.check_lun(None, True)


#=======================================================
#                     Mode Select
#=======================================================
def ModeSelectReq(conn, id, list):
    cdb = NEW_CDB(MODE_SELECT)
    cdb[4] = len(list) & 0xff
    return ScsiReq(conn, id, cdb, 0x30)

def __ModeSelectRsp(cmd):
    '''
    scsi mode select response
    '''
    cmd.status = SAM_STAT_GOOD
    lun = cmd.lun
    length = cmd.cdb[4]

    if cmd.check_lun(TYPE_TAPE):
        if length >= 12:
            #
            # buf[0]    Mode Data Length: 0
            # buf[1]    Medium Type: Default
            # buf[2]    Device-Specific Parameter
            # buf[3]    Block Descriptor Length
            # buf[4-7]  No. of Blocks: 0
            # buf[9-12] Block Length: 1024
            #
            buf = do_unpack(cmd.in_buf)
            if buf[3] == 8:
                lun.set_block_size(array_2_hex(buf, 9, 3))
                DBG_PRN('tape set block size to', lun.get_block_size())


#=======================================================
#                     Read Defect Data
#=======================================================
def ReadDefectDataReq(conn, id, p, g, fmt):
    cdb = NEW_CDB(READ_DEFECT_DATA)
    cdb[2] |= fmt & 0x07
    if p: cdb[2] |= 0x10
    if g: cdb[2] |= 0x08
    cdb[7:9] = hex_2_array(0xff, 2)
    return ScsiReq(conn, id, cdb, 0xff)

def __ReadDefectDataRsp(cmd):
    '''
    read defect list response
    '''
    lun = cmd.lun
    cmd.status = SAM_STAT_GOOD

    if not cmd.check_lun(TYPE_DISK):
        return

    fmt = cmd.cdb[2] & 0x07
    rpl = (cmd.cdb[2] >> 4) & 0x01
    rgl = (cmd.cdb[2] >> 3) & 0x01

    if (fmt != 0x00 and fmt != 0x03 and
        fmt != 0x04 and fmt != 0x05):
        DBG_WRN('defect list format error!', lun.id)
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x0310)
    else:
        buf = do_pack([0, ((rpl<<4)&0x10) | ((rgl<<3)&0x08) | (fmt&0x07), 0, 0])    
        if rpl:
            for addr in lun.plist:
                buf += fmt_addr(fmt, addr)
        if rgl:
            for addr in lun.glist:
                buf += fmt_addr(fmt, addr)
        buf = hex_2_byte(buf, 2, 2, len(buf) - 4)
        cmd.out_buf = buf


#=======================================================
#                    Load unload Unit
#=======================================================
def LoadUnloadReq(conn, id, load):
    cdb = NEW_CDB(LOAD_UNLOAD)
    if load:
        cdb[4] |= 0x01
    return ScsiReq(conn, id, cdb, 0)

def __LoadUnloadRsp(cmd):
    '''
    scsi load unload unit
    '''
    cmd.status = SAM_STAT_GOOD
    cdb = cmd.cdb
    load = cdb[4] & 0x01

    if not cmd.check_lun(None):
        return
    if is_tape(cmd.lun):
        if load:
            cmd.lun.load()
        else:
            cmd.lun.unload()
    else:
        if load:
            cmd.lun.set_ready()
        else:
            cmd.lun.set_noready()


#=======================================================
#                     Reassign Block
#=======================================================
def ReassignBlockReq(conn, id):
    # careful to use this command, dangerous
    pass

def __ReassignBlockRsp(cmd):
    '''
    scsi reassign block
    '''
    lun = cmd.lun
    cmd.status = SAM_STAT_GOOD

    if not cmd.check_lun(TYPE_DISK):
        return

    llba = (4, 8)[(cmd.cdb[1] >> 1) & 0x01]
    if cmd.cdb[1] & 0x01:
        cnt = byte_2_hex(cmd.in_buf, 2, 2) // llba
    else:
        cnt = byte_2_hex(cmd.in_buf, 0, 4) // llba
    if len(cmd.in_buf) < llba * cnt + 4:
        DBG_WRN('Address list is invaild.', llba, cnt, len(cmd.in_buf))
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x1001)
    else:
        for i in range(0, cnt):
            addr = byte_2_hex(cmd.in_buf, 4 + i * llba, llba)
            if lun.AddGlist(addr) == False:
                cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2101)
                break


#=======================================================
#                   Diagnostic receive
#=======================================================
def __DiagnosticRecvRsp(cmd):
    '''
    Diagnostic receive response
    ''' 
    cmd.status = SAM_STAT_GOOD  
    if not cmd.check_lun(TYPE_ENCLOSURE):
        return
    code = cmd.cdb[2] & 0xff
    buf = cmd.lun.EnclosureService(code)
    if buf is None:
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x3502)
    else:
        cmd.out_buf = buf


#=======================================================
#                         Rewind
#=======================================================
def RewindReq(conn, id):
    '''
    scsi rewind request
    '''
    cdb = NEW_CDB(REWIND)
    return ScsiReq(conn, id, cdb, 0) 

def __RewindRsp(cmd):
    '''
    scsi rewind response
    '''
    cmd.status = SAM_STAT_GOOD
    if cmd.check_lun(TYPE_TAPE):
        tio = TIO()
        cmd.lun.Rewind(tio)
        cmd.check_tio(tio)


#=======================================================
#                     Write file marks
#=======================================================
def WriteFileMarkReq(conn, id, count=1):
    '''
    Write file marks request
    '''
    cdb = NEW_CDB(WRITE_FILEMARKS)
    cdb[2:5] = hex_2_array(count, 3)
    return ScsiReq(conn, id, cdb, 0) 

def __WriteFileMarkRsp(cmd):
    '''
    Write file marks
    '''
    cmd.status = SAM_STAT_GOOD
    if cmd.check_lun(TYPE_TAPE, True):
        count = array_2_hex(cmd.cdb, 2, 3)
        tio = TIO(count)
        cmd.lun.WriteFilemark(tio)
        cmd.check_tio(tio)


#=======================================================
#                    Service action in
#=======================================================
def __ServiceActionInRsp(cmd):
    '''
    service action in
    '''
    service_action_code = cmd.cdb[1]
    if service_action_code == SAI_READ_CAPACITY_16:
        __ReadCapacity16Rsp(cmd)
        return
    cmd.status = SAM_STAT_GOOD
    cmd.check_lun(None)


#=======================================================
#                        Erase 
#=======================================================
def EraseReq(conn, id):
    cdb = NEW_CDB(ERASE)
    cdb[1] = 0x01
    cmd = ScsiReq(conn, id, cdb, 0)
    return cmd

def __EraseRsp(cmd):
    '''
    service action in
    '''
    cmd.status = SAM_STAT_GOOD
    if cmd.check_lun(TYPE_TAPE, True):
        tio = TIO()
        cmd.lun.Rewind(tio)
        cmd.lun.Format(tio)
        cmd.check_tio(tio)


#=======================================================
#                    Read position
#=======================================================
def ReadPositionReq(conn, id):
    cdb = NEW_CDB(READ_POSITION)
    cdb[1] = 0x01       # Service Action: Short Form - Vendor-Specific
    cmd = ScsiReq(conn, id, cdb, 20)
    return cmd

def get_position(cmd):
    if cmd.in_buf and len(cmd.in_buf) >= 20:
        return byte_2_hex(cmd.in_buf, 4, 4)
    return -1

def __ReadPositionRsp(cmd):
    '''
    read position response
    '''
    cmd.status = SAM_STAT_GOOD
    lun = cmd.lun
    data = []

    if cmd.check_lun(TYPE_TAPE, None):
        action = cmd.cdb[1] & 0x1f
        if action == 0x00 or action == 0x01:
            data = [0] * 20
            if lun.is_bop():
                data[0] |= 0x80
            data[4:8] = hex_2_array(lun.get_position(), 4)
            # data[8:12] = hex_2_array(lun.get_position(), 4)
        else:
            cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2400)

    if len(data):
        cmd.out_buf = do_pack(data)


#=======================================================
#                         Locate
#=======================================================
def LocateReq(conn, id, position):
    '''
    locate request
    '''
    cdb = NEW_CDB(LOCATE)
    cdb[3:7] = hex_2_array(position, 4)
    cmd = ScsiReq(conn, id, cdb, 0)
    return cmd

def __LocateRsp(cmd):
    '''
    locate response
    '''
    cmd.status = SAM_STAT_GOOD
    if cmd.check_lun(TYPE_TAPE):
        if cmd.cdb[1] & 0x02 != 0x00:
            cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2400)
        else:
            tio = TIO(array_2_hex(cmd.cdb, 3, 4))
            cmd.lun.Locate(tio)            
            cmd.check_tio(tio)


#=======================================================
#                         Space 
#=======================================================
def SpaceReq(conn, id, code, count):
    '''
    scsi space request
    '''
    cdb = NEW_CDB(SPACE)
    cdb[1] = code & 0x0f
    if count < 0:
        count = 0xFFFFFF - (~(-count))
    cdb[2:5] = hex_2_array(count, 3)
    cmd = ScsiReq(conn, id, cdb, 0)
    return cmd

def __SpaceRsp(cmd):
    '''
    scsi space respose
    '''
    cmd.status = SAM_STAT_GOOD
    code = cmd.cdb[1] & 0x0F
    count = array_2_hex(cmd.cdb, 2, 3)
    if cmd.check_lun(TYPE_TAPE, None):
        tio = TIO(count, '', code)        
        if count >= 0x800000:
            tio.length = -(0xffffff - count + 1)
        cmd.lun.Space(tio)
        cmd.check_tio(tio)


#=======================================================
#                 Allow medium removal
#=======================================================
def __AllowMedimuRemovalRsp(cmd):
    '''
    scsi allow medimu removal
    '''
    cmd.status = SAM_STAT_GOOD
    if cmd.check_lun(TYPE_TAPE):
        prevent = cmd.cdb[4] & 0x03  
        if prevent == 0x00:
            cmd.lun.prevent = False
            DBG_PRN('tape enable removal')
        elif prevent == 0x01:
            cmd.lun.prevent = True
            DBG_PRN('tape disable removal')
        else:
            cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2100)


#=======================================================
#                   Read attribute
#=======================================================
def ReadAttributeReq(conn, id):
    '''
    Read attribute request
    '''
    cdb = NEW_CDB(READ_ATTRIBUTE)
    cdb[8:10] = hex_2_array(0x401, 2)
    cdb[10:14] = hex_2_array(0x4000, 4)
    return ScsiReq(conn, id, cdb, 0x4000)

def __ReadAttributeRsp(cmd):
    '''
    Read attribute response
    '''
    cdb = cmd.cdb
    cmd.status = SAM_STAT_GOOD
    if cmd.check_lun(TYPE_TAPE):
        attr = array_2_hex(cdb, 8, 2)
    cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2500)
        

#=======================================================
#                      Log Sense
#=======================================================
def LogSenseReq(conn, id):
    cdb = NEW_CDB(LOG_SENSE)
    cdb[2] = 66
    cdb[7] = 64
    return ScsiReq(conn, id, cdb, 0x4000)

def __LogSenseRsp(cmd):
    cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2400)

            
#=======================================================
#                   Diagnostic send
#=======================================================
def DiagnosticSend(cmd):
    # TODO
    pass

#
# All of current supported scsi command
#
__SCSI_CMD_URL = { WRITE_6:                 __Write10Rsp,
                   WRITE_10:                __Write10Rsp,
                   WRITE_12:                __Write10Rsp,
                   WRITE_16:                __Write10Rsp,
                   WRITE_BUFFER:            __Write10Rsp,
                   READ_6:                  __Read10Rsp,
                   READ_10:                 __Read10Rsp,
                   READ_12:                 __Read10Rsp,
                   READ_16:                 __Read10Rsp,
                   READ_BUFFER:             __Read10Rsp,
                   REPORT_LUNS:             __ReportLunRsp,
                   INQUIRY:                 __InquiryRsp,
                   READ_CAPACITY:           __ReadCapacityRsp,
                   MODE_SENSE:              __ModeSenseRsp,
                   TEST_UNIT_READY:         __TestUnitReadyRsp,
                   VERIFY:                  __VerifyRsp,
                   SYNCHRONIZE_CACHE:       __SyncCacheRsp,
                   LOAD_UNLOAD:             __LoadUnloadRsp,
                   REASSIGN_BLOCKS:         __ReassignBlockRsp,
                   READ_DEFECT_DATA:        __ReadDefectDataRsp,
                   RECEIVE_DIAGNOSTIC:      __DiagnosticRecvRsp,
                   READ_BLOCK_LIMITS:       __ReadBlockLimitRsp,
                   REWIND:                  __RewindRsp,
                   WRITE_FILEMARKS:         __WriteFileMarkRsp,
                   SERVICE_ACTION_IN:       __ServiceActionInRsp,
                   REQUEST_SENSE:           __RequestSenseRsp,
                   READ_POSITION:           __ReadPositionRsp,
                   ERASE:                   __EraseRsp,
                   LOCATE:                  __LocateRsp,
                   MODE_SELECT:             __ModeSelectRsp,
                   SPACE:                   __SpaceRsp,
                   ALLOW_MEDIUM_REMOVAL:    __AllowMedimuRemovalRsp,
#                  READ_ATTRIBUTE:          __ReadAttributeRsp,
#                  LOG_SENSE:               __LogSenseRsp,
                }

def exe_scsi_cmd(cmd):
    '''
    execute scsi command.
    '''
    from scsi.scsi_simulator import Check_EXE_Cmd
    code = cmd.cdb[0]

    # check if is simulate test case
    if Check_EXE_Cmd(cmd):
        return

    if __SCSI_CMD_URL.has_key(code):
        __SCSI_CMD_URL[code](cmd)
    else:
        DBG_WRN('Detect unsupported scsi command (%d)' % code)
        cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x2500)

def SCSI_DESC(cdb):
    '''
    get scsi cdb descriptor
    '''
    buf = scsi_code_desc[cdb[0] % len(scsi_code_desc)]

    if IS_READ(cdb[0]) or IS_WRITE(cdb[0]):
        buf += '  LBA:0x%x LEN:0x%x' % (SCSI_LBA(cdb), SBC_LEN(cdb))
    return buf
