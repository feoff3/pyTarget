#    
#    scsi protocol(SAM/SPC4/SBC4/SSC4) defines.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#

BLOCK_SHIFT                              = 9       # block shift
BLOCK_SIZE                               = 512     # default block size

#
# SCSI opcodes
#
TEST_UNIT_READY                          = 0x00
REWIND                                   = 0x01
REZERO_UNIT                              = 0x01
REQUEST_SENSE                            = 0x03
FORMAT_UNIT                              = 0x04
READ_BLOCK_LIMITS                        = 0x05
REASSIGN_BLOCKS                          = 0x07
INITIALIZE_ELEMENT_STATUS                = 0x07
READ_6                                   = 0x08
WRITE_6                                  = 0x0a
SEEK_6                                   = 0x0b
READ_REVERSE                             = 0x0f
WRITE_FILEMARKS                          = 0x10
SPACE                                    = 0x11
INQUIRY                                  = 0x12
RECOVER_BUFFERED_DATA                    = 0x14
MODE_SELECT                              = 0x15
RESERVE                                  = 0x16
RELEASE                                  = 0x17
COPY                                     = 0x18
ERASE                                    = 0x19
MODE_SENSE                               = 0x1a
START_STOP                               = 0x1b
LOAD_UNLOAD                              = 0x1b
RECEIVE_DIAGNOSTIC                       = 0x1c
SEND_DIAGNOSTIC                          = 0x1d
ALLOW_MEDIUM_REMOVAL                     = 0x1e
SET_WINDOW                               = 0x24
READ_CAPACITY                            = 0x25
READ_10                                  = 0x28
WRITE_10                                 = 0x2a
SEEK_10                                  = 0x2b
POSITION_TO_ELEMENT                      = 0x2b
LOCATE                                   = 0x2b
WRITE_VERIFY                             = 0x2e
VERIFY                                   = 0x2f
SEARCH_HIGH                              = 0x30
SEARCH_EQUAL                             = 0x31
SEARCH_LOW                               = 0x32
SET_LIMITS                               = 0x33
PRE_FETCH                                = 0x34
READ_POSITION                            = 0x34
SYNCHRONIZE_CACHE                        = 0x35
LOCK_UNLOCK_CACHE                        = 0x36
READ_DEFECT_DATA                         = 0x37
MEDIUM_SCAN                              = 0x38
COMPARE                                  = 0x39
COPY_VERIFY                              = 0x3a
WRITE_BUFFER                             = 0x3b
READ_BUFFER                              = 0x3c
UPDATE_BLOCK                             = 0x3d
READ_LONG                                = 0x3e
WRITE_LONG                               = 0x3f
CHANGE_DEFINITION                        = 0x40
WRITE_SAME                               = 0x41
UNMAP                                    = 0x42 #TODO: impl and do TRIM (or maybe SCSI pass-thru) on a physical drive
READ_TOC                                 = 0x43
LOG_SELECT                               = 0x4c
LOG_SENSE                                = 0x4d
XDWRITEREAD_10                           = 0x53
MODE_SELECT_10                           = 0x55
RESERVE_10                               = 0x56
RELEASE_10                               = 0x57
MODE_SENSE_10                            = 0x5a
PERSISTENT_RESERVE_IN                    = 0x5e
PERSISTENT_RESERVE_OUT                   = 0x5f
VARIABLE_LENGTH_CMD                      = 0x7f
REPORT_LUNS                              = 0xa0
MAINTENANCE_IN                           = 0xa3
MAINTENANCE_OUT                          = 0xa4
MOVE_MEDIUM                              = 0xa5
EXCHANGE_MEDIUM                          = 0xa6
READ_12                                  = 0xa8
WRITE_12                                 = 0xaa
WRITE_VERIFY_12                          = 0xae
SEARCH_HIGH_12                           = 0xb0
SEARCH_EQUAL_12                          = 0xb1
SEARCH_LOW_12                            = 0xb2
READ_ELEMENT_STATUS                      = 0xb8
SEND_VOLUME_TAG                          = 0xb6
WRITE_LONG_2                             = 0xea
READ_16                                  = 0x88
WRITE_16                                 = 0x8a
READ_ATTRIBUTE                           = 0x8c
VERIFY_16                                = 0x8f
SERVICE_ACTION_IN                        = 0x9e
#ERASE_16                                 = 0X93
SAI_READ_CAPACITY_16                     = 0x10     # values for service action in 
MI_REPORT_TARGET_PGS                     = 0x0a     # values for maintenance in
MO_SET_TARGET_PGS                        = 0x0a     # values for maintenance out

# Values for T10/04-262r7
ATA_16                                   = 0x85     # 16-byte pass-thru
ATA_12                                   = 0xa1     # 12-byte pass-thru

# SPC scsi cdb size
def CDB_SIZE(code):
    __cdb_size = (6, 10, 10, 12, 16, 12, 10, 10)
    return __cdb_size[(code >> 5) & 0x07]

# SBC scsi cdb lba
def SCSI_LBA(x):
    ret = -1
    y = CDB_SIZE(x[0])
    if y == 6:    ret = ((x[1] << 16) + (x[2] << 8) + x[3]) & 0x1fffff
    elif y == 10: ret = (x[2] << 24) + (x[3] << 16) + (x[4] << 8) + x[5]
    elif y == 12: ret = (int(x[2]) << 24) + (int(x[3]) << 16) + (x[4] << 8) + x[5]
    elif y == 16: ret = (int(x[2])<<56)+(int(x[3])<<48)+(int(x[4])<<40)+(int(x[5])<<32)+(int(x[6])<<24)+(x[7]<<16)+(x[8]<<8)+x[9]
    return ret

# SBC scsi blocks
def SBC_LEN(x):
    ret = -1
    y = CDB_SIZE(x[0])
    if y == 6:    ret = x[4]
    elif y == 10: ret = (x[7] << 8) + x[8]
    elif y == 12: ret = (x[6] << 24) + (x[7] << 16) + (x[8] << 8) + x[9]
    elif y == 16: ret = int(int(x[10]) << 24)+ (x[11] << 16)+ (x[12] << 8)+ x[13]
    return int(ret)

# SSC scsi blocks
def SSC_LEN(x):
    ret = -1
    y = CDB_SIZE(x[0])
    if y == 6:    ret = (x[2] << 16)+ (x[3] << 8)+ x[4]
    elif y == 10: ret = -1
    elif y == 12: ret = -1
    elif y == 16: ret = (x[12] << 16)+ (x[13] << 8)+ x[13]
    return int(ret)
    
SCSI_ALLOCATION_LEN_LIST = {
    REPORT_LUNS:(6, 4),
    INQUIRY	: (3, 2),
    MODE_SENSE:(4, 1),
    MODE_SENSE_10:(7, 2),
    READ_DEFECT_DATA:(7, 2),
    READ_POSITION:(7, 2),
    READ_ATTRIBUTE:(10, 4),
    LOG_SENSE:(7, 2),
}

def ALLOCATE_LEN(x):
    from comm.stdlib import array_2_hex
    if x[0] in SCSI_ALLOCATION_LEN_LIST:
        ran = SCSI_ALLOCATION_LEN_LIST[x[0]]
        return array_2_hex(x, ran[0], ran[1])
    return -1

#
#  SCSI Architecture Model (SAM) Status codes. Taken from SAM-3 draft
#  T10/1561-D Revision 4 Draft dated 7th November 2002.
#
SAM_STAT_GOOD                            = 0x00
SAM_STAT_CHECK_CONDITION                 = 0x02
SAM_STAT_CONDITION_MET                   = 0x04
SAM_STAT_BUSY                            = 0x08
SAM_STAT_INTERMEDIATE                    = 0x10
SAM_STAT_INTERMEDIATE_CONDITION_MET      = 0x14
SAM_STAT_RESERVATION_CONFLICT            = 0x18
SAM_STAT_COMMAND_TERMINATED              = 0x22    # obsolete in SAM-3
SAM_STAT_TASK_SET_FULL                   = 0x28
SAM_STAT_ACA_ACTIVE                      = 0x30
SAM_STAT_TASK_ABORTED                    = 0x40

#
#  SENSE KEYS
#
NO_SENSE                                 = 0x00
RECOVERED_ERROR                          = 0x01
NOT_READY                                = 0x02
MEDIUM_ERROR                             = 0x03
HARDWARE_ERROR                           = 0x04
ILLEGAL_REQUEST                          = 0x05
UNIT_ATTENTION                           = 0x06
DATA_PROTECT                             = 0x07
BLANK_CHECK                              = 0x08
COPY_ABORTED                             = 0x0a
ABORTED_COMMAND                          = 0x0b
VOLUME_OVERFLOW                          = 0x0d
MISCOMPARE                               = 0x0e

#
# Additional Sense Code (ASC) used
#
ASC_NO_ADDED_SENSE                       = 0x00
ASC_INVALID_FIELD_IN_CDB                 = 0x24
ASC_POWERON_RESET                        = 0x29
ASC_NOT_SELF_CONFIGURED                  = 0x3e

# 
# scsi sense
#
SENSE_SIZE                               = 38
def SENSE_CLASS(sense):  return (((sense) >> 4) & 0x7)
def SENSE_ERROR(sense):  return ((sense) & 0xf)
def SENSE_VALID(sense):  return ((sense) & 0x80)

def S_ASC(code):         return (code >> 8) & 0xff
def S_ASCQ(code):        return code & 0xff
#
#  DEVICE TYPES
#  Please keep them in 0x%02x format for $MODALIAS to work
#
TYPE_DISK                                = 0x00
TYPE_TAPE                                = 0x01
TYPE_PRINTER                             = 0x02
TYPE_PROCESSOR                           = 0x03    # HP scanners use this 
TYPE_WORM                                = 0x04    # Treated as ROM by our system 
TYPE_ROM                                 = 0x05
TYPE_SCANNER                             = 0x06
TYPE_MOD                                 = 0x07    # Magneto-optical disk -treated as TYPE_DISK */
TYPE_MEDIUM_CHANGER                      = 0x08
TYPE_COMM                                = 0x09    # Communications device
TYPE_RAID                                = 0x0c
TYPE_ENCLOSURE                           = 0x0d    # Enclosure Services Device
TYPE_RBC                                 = 0x0e
TYPE_OSD                                 = 0x11
TYPE_NO_LUN                              = 0x7f

# for protect type (read only)
TYPE_PROTECT_MASK                        = 0x80     
TYPE_PROTECT_DISK                        = TYPE_PROTECT_MASK | TYPE_DISK
TYPE_PROTECT_TAPE                        = TYPE_PROTECT_MASK | TYPE_TAPE

#
# SCSI protocols; these are taken from SPC-3 section 7.5
#
SCSI_PROTOCOL_FCP                        = 0 # Fibre Channel
SCSI_PROTOCOL_SPI                        = 1 # parallel SCSI
SCSI_PROTOCOL_SSA                        = 2 # Serial Storage Architecture - Obsolete
SCSI_PROTOCOL_SBP                        = 3 # firewire
SCSI_PROTOCOL_SRP                        = 4 # Infiniband RDMA
SCSI_PROTOCOL_ISCSI                      = 5
SCSI_PROTOCOL_SAS                        = 6
SCSI_PROTOCOL_ADT                        = 7 # Media Changers
SCSI_PROTOCOL_ATA                        = 8
SCSI_PROTOCOL_UNSPEC                     = 0xf # No specific protocol 

SCSI_RSP_EOF                             = 0x80 # scsi response eof bit
SCSI_RSP_EOM                             = 0x40 # scsi response eom bit
SCSI_RSP_ILI                             = 0x20 # scsi response ili bit

#
#  MESSAGE CODES
#
#COMMAND_COMPLETE                         = 0x00
#EXTENDED_MESSAGE                         = 0x01
#EXTENDED_MODIFY_DATA_POINTER             = 0x00
#EXTENDED_SDTR                            = 0x01
#EXTENDED_EXTENDED_IDENTIFY               = 0x02    # SCSI-I only
#EXTENDED_WDTR                            = 0x03
#EXTENDED_PPR                             = 0x04
#EXTENDED_MODIFY_BIDI_DATA_PTR            = 0x05
#SAVE_POINTERS                            = 0x02
#RESTORE_POINTERS                         = 0x03
#DISCONNECT                               = 0x04
#INITIATOR_ERROR                          = 0x05
#ABORT_TASK_SET                           = 0x06
#MESSAGE_REJECT                           = 0x07
#NOP                                      = 0x08
#MSG_PARITY_ERROR                         = 0x09
#LINKED_CMD_COMPLETE                      = 0x0a
#LINKED_FLG_CMD_COMPLETE                  = 0x0b
#TARGET_RESET                             = 0x0c

#
# Task Management Function
#
#ABORT_TASK                               = 0x01
#CLEAR_TASK_SET                           = 0x0e
#INITIATE_RECOVERY                        = 0x0f # SCSI-II only
#RELEASE_RECOVERY                         = 0x10 # SCSI-II only
#CLEAR_ACA                                = 0x16
#LOGICAL_UNIT_RESET                       = 0x17
#SIMPLE_QUEUE_TAG                         = 0x20
#HEAD_OF_QUEUE_TAG                        = 0x21
#ORDERED_QUEUE_TAG                        = 0x22
#IGNORE_WIDE_RESIDUE                      = 0x23
#ACA                                      = 0x24
#QAS_REQUEST                              = 0x55

#
# SCSI command description
#
scsi_code_desc = (
        "Test Unit Ready", "Rezero Unit/Rewind", '', "Request Sense",
        "Format Unit/Medium", "Read Block Limits", '', "Reasssign Blocks",
        "Read(6)", '', "Write(6)", "Seek(6)", '', '',
        '', "Read Reverse", "Write Filemarks", "Space", "Inquiry",
        "Verify(6)", "Recover Buffered Data", "Mode Select(6)", "Reserve(6)",
        "Release(6)", "Copy", "Erase", "Mode Sense(6)",
        "Start/Stop Unit", "Receive Diagnostic", "Send Diagnostic",
        "Prevent/Allow Medium Removal", '',
        '', '', '',
        "Read Format Capacities", "Set Window", "Read Capacity(10)", '', '', "Read(10)",
        "Read Generation", "Write(10)", "Seek(10)", "Erase(10)", "Read updated block",
        "Write Verify(10)", "Verify(10)", "Search High", "Search Equal",
        "Search Low", "Set Limits", "Prefetch/Read Position",
        "Synchronize Cache(10)", "Lock/Unlock Cache(10)", "Read Defect Data(10)",
        "Medium Scan", "Compare", "Copy Verify", "Write Buffer", "Read Buffer",
        "Update Block", "Read Long(10)", "Write Long(10)",
        "Change Definition", "Write Same(10)",
        "Read sub-channel", "Read TOC/PMA/ATIP", "Read density support",
        "Play audio(10)", "Get configuration", "Play audio msf",
        "Play audio track/index",
        "Play track relative(10)", "Get event status notification",
        "Pause/resume", "Log Select", "Log Sense", "Stop play/scan", '',
        "Xdwrite", "Xpwrite, Read disk info", "Xdread, Read track info",
        "Reserve track", "Send OPC info", "Mode Select(10)",
        "Reserve(10)", "Release(10)", "Repair track", "Read master cue",
        "Mode Sense(10)", "Close track/session",
        "Read buffer capacity", "Send cue sheet", "Persistent reserve in",
        "Persistent reserve out",
        '', '', '', '', '', '', '', '',
        '', '', '', '', '', '', '', '',
        '', '', '', '', '', '', '', '',
        '', '', '', '', '', '', '', "Variable length",
        "Xdwrite(16)", "Rebuild(16)", "Regenerate(16)", "Extended copy",
        "Receive copy results",
        "ATA command pass through(16)", "Access control in",
        "Access control out", "Read(16)", "Memory Export Out(16)",
        "Write(16)", '', "Read attributes", "Write attributes",
        "Write and verify(16)", "Verify(16)",
        "Pre-fetch(16)", "Synchronize cache(16)",
        "Lock/unlock cache(16)", "Write same(16)", '',
        '', '', '', '', '',
        '', '', '', '', "Service action in(16)",
        "Service action out(16)",
        "Report luns", "ATA command pass through(12)/Blank",
        "Security protocol in", "Maintenance in", "Maintenance out",
        "Move medium/play audio(12)",
        "Exchange medium", "Move medium attached", "Read(12)",
        "Play track relative(12)",
        "Write(12)", '', "Erase(12), Get Performance",
        "Read DVD structure", "Write and verify(12)",
        "Verify(12)", "Search data high(12)", "Search data equal(12)",
        "Search data low(12)", "Set limits(12)",
        "Read element status attached",
        "Security protocol out", "Send volume tag, set streaming",
        "Read defect data(12)", "Read element status", "Read CD msf",
        "Redundancy group (in), Scan",
        "Redundancy group (out), Set cd-rom speed", "Spare (in), Play cd",
        "Spare (out), Mechanism status", "Volume set (in), Read cd",
        "Volume set (out), Send DVD structure")
        


scsi_sense_addrition_desc = (
    (0x0000, "No additional sense information"),
    (0x0001, "Filemark detected"),
    (0x0002, "End-of-partition/medium detected"),
    (0x0003, "Setmark detected"),
    (0x0004, "Beginning-of-partition/medium detected"),
    (0x0005, "End-of-data detected"),
    (0x0006, "I/O process terminated"),
    (0x0007, "Programmable early warning detected"),
    (0x0011, "Audio play operation in progress"),
    (0x0012, "Audio play operation paused"),
    (0x0013, "Audio play operation successfully completed"),
    (0x0014, "Audio play operation stopped due to error"),
    (0x0015, "No current audio status to return"),
    (0x0016, "Operation in progress"),
    (0x0017, "Cleaning requested"),
    (0x0018, "Erase operation in progress"),
    (0x0019, "Locate operation in progress"),
    (0x001A, "Rewind operation in progress"),
    (0x001B, "Set capacity operation in progress"),
    (0x001C, "Verify operation in progress"),
    (0x001E, "Conflicting SA creation request"),
    (0x0087, "SAM-4 T10/1683-D revision 13"),
    (0x0100, "No index/sector signal"),
    (0x0200, "No seek complete"),
    (0x0300, "Peripheral device write fault"),
    (0x0301, "No write current"),
    (0x0302, "Excessive write errors"),
    (0x03E7, "SES-2 T10/1559-D revision 19"),
    (0x0400, "Logical unit not ready, cause not reportable"),
    (0x0401, "Logical unit is in process of becoming ready"),
    (0x0402, "Logical unit not ready, initializing cmd. required"),
    (0x0403, "Logical unit not ready, manual intervention required"),
    (0x0404, "Logical unit not ready, format in progress"),
    (0x0405, "Logical unit not ready, rebuild in progress"),
    (0x0406, "Logical unit not ready, recalculation in progress"),
    (0x0407, "Logical unit not ready, operation in progress"),
    (0x0408, "Logical unit not ready, long write in progress"),
    (0x0409, "Logical unit not ready, self-test in progress"),
    (0x040A, "Logical unit not accessible, asymmetric access state transition"),
    (0x040B, "Logical unit not accessible, target port in standby state"),
    (0x040C, "Logical unit not accessible, target port in unavailable state"),
    (0x040D, "Logical unit not ready, structure check required"),
    (0x0410, "Logical unit not ready, auxiliary memory not accessible"),
    (0x0413, "Logical unit not ready, SA creation in progress"),
    (0x0434, "MMC-5 ANSI INCITS 430-2007"),
    (0x04AA, "ADC-2 T10/1741-D revision 8"),
    (0x0500, "Logical unit does not respond to selection"),
    (0x0600, "No reference position found"),
    (0x0700, "Multiple peripheral devices selected"),
    (0x0800, "Logical unit communication failure"),
    (0x0801, "Logical unit communication time-out"),
    (0x0802, "Logical unit communication parity error"),
    (0x0803, "Logical unit communication CRC error (Ultra-DMA/32)"),
    (0x0804, "Unreachable copy target"),
    (0x0900, "Track following error"),
    (0x0901, "Tracking servo failure"),
    (0x0902, "Focus servo failure"),
    (0x0903, "Spindle servo failure"),
    (0x0904, "Head select fault"),
    (0x0A00, "Error log overflow"),
    (0x0B00, "Warning"),
    (0x0B01, "Warning - specified temperature exceeded"),
    (0x0B02, "Warning - enclosure degraded"),
    (0x0C00, "Write error"),
    (0x0C01, "Write error - recovered with auto reallocation"),
    (0x0C02, "Write error - auto reallocation failed"),
    (0x0C03, "Write error - recommend reassignment"),
    (0x0C04, "Compression check miscompare error"),
    (0x0C05, "Data expansion occurred during compression"),
    (0x0C06, "Block not compressible"),
    (0x0C07, "Write error - recovery needed"),
    (0x0C08, "Write error - recovery failed"),
    (0x0C09, "Write error - loss of streaming"),
    (0x0C0A, "Write error - padding blocks added"),
    (0x0C0B, "Auxiliary memory write error"),
    (0x0C0C, "Write error - unexpected unsolicited data"),
    (0x0C0D, "Write error - not enough unsolicited data"),
    (0x0C23, "SAS-2 T10/1760-D revision 14"),
    (0x0D00, "Error detected by third party temporary initiator"),
    (0x0D01, "Third party device failure"),
    (0x0D02, "Copy target device not reachable"),
    (0x0D03, "Incorrect copy target device type"),
    (0x0D04, "Copy target device data underrun"),
    (0x0D05, "Copy target device data overrun"),
    (0x0E29, "FC-LS ANSI INCITS 433-2007"),
    (0x1000, "Id CRC or ECC error"),
    (0x1100, "Unrecovered read error"),
    (0x1101, "Read retries exhausted"),
    (0x1102, "Error too long to correct"),
    (0x1103, "Multiple read errors"),
    (0x1104, "Unrecovered read error - auto reallocate failed"),
    (0x1105, "L-EC uncorrectable error"),
    (0x1106, "CIRC unrecovered error"),
    (0x1107, "Data re-synchronization error"),
    (0x1108, "Incomplete block read"),
    (0x1109, "No gap found"),
    (0x110A, "Miscorrected error"),
    (0x110B, "Unrecovered read error - recommend reassignment"),
    (0x110C, "Unrecovered read error - recommend rewrite the data"),
    (0x110D, "De-compression CRC error"),
    (0x110E, "Cannot decompress using declared algorithm"),
    (0x110F, "Error reading UPC/EAN number"),
    (0x1110, "Error reading ISRC number"),
    (0x1111, "Read error - loss of streaming"),
    (0x1112, "Auxiliary memory read error"),
    (0x1113, "Read error - failed retransmission request"),
    (0x1200, "Address mark not found for id field"),
    (0x1300, "Address mark not found for data field"),
    (0x1400, "Recorded entity not found"),
    (0x1401, "Record not found"),
    (0x1402, "Filemark or setmark not found"),
    (0x1403, "End-of-data not found"),
    (0x1404, "Block sequence error"),
    (0x1405, "Record not found - recommend reassignment"),
    (0x1406, "Record not found - data auto-reallocated"),
    (0x1407, "Locate operation failure"),
    (0x1500, "Random positioning error"),
    (0x1501, "Mechanical positioning error"),
    (0x1502, "Positioning error detected by read of medium"),
    (0x1600, "Data synchronization mark error"),
    (0x1601, "Data sync error - data rewritten"),
    (0x1602, "Data sync error - recommend rewrite"),
    (0x1603, "Data sync error - data auto-reallocated"),
    (0x1604, "Data sync error - recommend reassignment"),
    (0x1700, "Recovered data with no error correction applied"),
    (0x1701, "Recovered data with retries"),
    (0x1702, "Recovered data with positive head offset"),
    (0x1703, "Recovered data with negative head offset"),
    (0x1704, "Recovered data with retries and/or circ applied"),
    (0x1705, "Recovered data using previous sector id"),
    (0x1706, "Recovered data without ECC - data auto-reallocated"),
    (0x1707, "Recovered data without ECC - recommend reassignment"),
    (0x1708, "Recovered data without ECC - recommend rewrite"),
    (0x1709, "Recovered data without ECC - data rewritten"),
    (0x1800, "Recovered data with error correction applied"),
    (0x1801, "Recovered data with error corr. & retries applied"),
    (0x1802, "Recovered data - data auto-reallocated"),
    (0x1803, "Recovered data with CIRC"),
    (0x1804, "Recovered data with L-EC"),
    (0x1805, "Recovered data - recommend reassignment"),
    (0x1806, "Recovered data - recommend rewrite"),
    (0x1807, "Recovered data with ECC - data rewritten"),
    (0x1808, "Recovered data with linking"),
    (0x1900, "Defect list error"),
    (0x1901, "Defect list not available"),
    (0x1902, "Defect list error in primary list"),
    (0x1903, "Defect list error in grown list"),
    (0x1A00, "Parameter list length error"),
    (0x1B00, "Synchronous data transfer error"),
    (0x1C00, "Defect list not found"),
    (0x1C01, "Primary defect list not found"),
    (0x1C02, "Grown defect list not found"),
    (0x1D00, "Miscompare during verify operation"),
    (0x1E00, "Recovered id with ECC correction"),
    (0x1F00, "Partial defect list transfer"),
    (0x2000, "Invalid command operation code"),
    (0x2001, "Access denied - initiator pending-enrolled"),
    (0x2002, "Access denied - no access rights"),
    (0x2003, "Access denied - invalid mgmt id key"),
    (0x2004, "Illegal command while in write capable state"),
    (0x2005, "Obsolete"),
    (0x2006, "Illegal command while in explicit address mode"),
    (0x2007, "Illegal command while in implicit address mode"),
    (0x2008, "Access denied - enrollment conflict"),
    (0x2009, "Access denied - invalid LU identifier"),
    (0x200A, "Access denied - invalid proxy token"),
    (0x200B, "Access denied - ACL LUN conflict"),
    (0x2100, "Logical block address out of range"),
    (0x2101, "Invalid element address"),
    (0x2102, "Invalid address for write"),
    (0x2200, "Illegal function (use 20 00, 24 00, or 26 00)"),
    (0x2400, "Invalid field in cdb"),
    (0x2401, "CDB decryption error"),
    (0x2402, "Obsolete"),
    (0x2403, "Obsolete"),
    (0x2408, "Invalid XCDB"),
    (0x2500, "Logical unit not supported"),
    (0x2600, "Invalid field in parameter list"),
    (0x2601, "Parameter not supported"),
    (0x2602, "Parameter value invalid"),
    (0x2603, "Threshold parameters not supported"),
    (0x2604, "Invalid release of persistent reservation"),
    (0x2605, "Data decryption error"),
    (0x2606, "Too many target descriptors"),
    (0x2607, "Unsupported target descriptor type code"),
    (0x2608, "Too many segment descriptors"),
    (0x2609, "Unsupported segment descriptor type code"),
    (0x260A, "Unexpected inexact segment"),
    (0x260B, "Inline data length exceeded"),
    (0x260C, "Invalid operation for copy source or destination"),
    (0x260D, "Copy segment granularity violation"),
    (0x2700, "Write protected"),
    (0x2701, "Hardware write protected"),
    (0x2702, "Logical unit software write protected"),
    (0x2703, "Associated write protect"),
    (0x2704, "Persistent write protect"),
    (0x2705, "Permanent write protect"),
    (0x2706, "Conditional write protect"),
    (0x2800, "Not ready to ready change, medium may have changed"),
    (0x2801, "Import or export element accessed"),
    (0x2803, "Import/export element accessed, medium changed"),
    (0x2900, "Power on, reset, or bus device reset occurred"),
    (0x2901, "Power on occurred"),
    (0x2902, "Scsi bus reset occurred"),
    (0x2903, "Bus device reset function occurred"),
    (0x2904, "Device internal reset"),
    (0x2905, "Transceiver mode changed to single-ended"),
    (0x2906, "Transceiver mode changed to lvd"),
    (0x2907, "I_T nexus loss occurred"),
    (0x2A00, "Parameters changed"),
    (0x2A01, "Mode parameters changed"),
    (0x2A02, "Log parameters changed"),
    (0x2A03, "Reservations preempted"),
    (0x2A04, "Reservations released"),
    (0x2A05, "Registrations preempted"),
    (0x2A06, "Asymmetric access state changed"),
    (0x2A07, "Implicit asymmetric access state transition failed"),
    (0x2A0A, "Error history i_t nexus cleared"),
    (0x2A0B, "Error history snapshot released"),
    (0x2A0C, "Error recovery attributes have changed"),
    (0x2A0D, "Data encryption capabilities changed"),
    (0x2A14, "SA creation capabilities data has changed"),
    (0x2B00, "Copy cannot execute since host cannot disconnect"),
    (0x2C00, "Command sequence error"),
    (0x2C01, "Too many windows specified"),
    (0x2C02, "Invalid combination of windows specified"),
    (0x2C03, "Current program area is not empty"),
    (0x2C04, "Current program area is empty"),
    (0x2C05, "Illegal power condition request"),
    (0x2C06, "Persistent prevent conflict"),
    (0x2C07, "Previous busy status"),
    (0x2C08, "Previous task set full status"),
    (0x2C09, "Previous reservation conflict status"),
    (0x2D00, "Overwrite error on update in place"),
    (0x2E00, "Insufficient time for operation"),
    (0x2F00, "Commands cleared by another initiator"),
    (0x3000, "Incompatible medium installed"),
    (0x3001, "Cannot read medium - unknown format"),
    (0x3002, "Cannot read medium - incompatible format"),
    (0x3003, "Cleaning cartridge installed"),
    (0x3004, "Cannot write medium - unknown format"),
    (0x3005, "Cannot write medium - incompatible format"),
    (0x3006, "Cannot format medium - incompatible medium"),
    (0x3007, "Cleaning failure"),
    (0x3008, "Cannot write - application code mismatch"),
    (0x3009, "Current session not fixated for append"),
    (0x3010, "Medium not formatted"),
    (0x3011, "Incompatible volume type"),
    (0x3012, "Incompatible volume qualifier"),
    (0x3100, "Medium format corrupted"),
    (0x3101, "Format command failed"),
    (0x3102, "Zoned formatting failed due to spare linking"),
    (0x3200, "No defect spare location available"),
    (0x3201, "Defect list update failure"),
    (0x3300, "Tape length error"),
    (0x3400, "Enclosure failure"),
    (0x3500, "Enclosure services failure"),
    (0x3501, "Unsupported enclosure function"),
    (0x3502, "Enclosure services unavailable"),
    (0x3503, "Enclosure services transfer failure"),
    (0x3504, "Enclosure services transfer refused"),
    (0x3600, "Ribbon, ink, or toner failure"),
    (0x3700, "Rounded parameter"),
    (0x3800, "Event status notification"),
    (0x3802, "Esn - power management class event"),
    (0x3804, "Esn - media class event"),
    (0x3806, "Esn - device busy class event"),
    (0x3900, "Saving parameters not supported"),
    (0x3A00, "Medium not present"),
    (0x3A01, "Medium not present - tray closed"),
    (0x3A02, "Medium not present - tray open"),
    (0x3A03, "Medium not present - loadable"),
    (0x3A04, "Medium not present - medium auxiliary memory accessible"),
    (0x3B00, "Sequential positioning error"),
    (0x3B01, "Tape position error at beginning-of-medium"),
    (0x3B02, "Tape position error at end-of-medium"),
    (0x3B03, "Tape or electronic vertical forms unit not ready"),
    (0x3B04, "Slew failure"),
    (0x3B05, "Paper jam"),
    (0x3B06, "Failed to sense top-of-form"),
    (0x3B07, "Failed to sense bottom-of-form"),
    (0x3B08, "Reposition error"),
    (0x3B09, "Read past end of medium"),
    (0x3B0A, "Read past beginning of medium"),
    (0x3B0B, "Position past end of medium"),
    (0x3B0C, "Position past beginning of medium"),
    (0x3B0D, "Medium destination element full"),
    (0x3B0E, "Medium source element empty"),
    (0x3B0F, "End of medium reached"),
    (0x3B11, "Medium magazine not accessible"),
    (0x3B12, "Medium magazine removed"),
    (0x3B13, "Medium magazine inserted"),
    (0x3B14, "Medium magazine locked"),
    (0x3B15, "Medium magazine unlocked"),
    (0x3B16, "Mechanical positioning or changer error"),
    (0x3B18, "Element disabled"),
    (0x3B19, "Element enabled"),
    (0x3B1A, "Data transfer device removed"),
    (0x3B1B, "Data transfer device inserted"),
    (0x3D00, "Invalid bits in identify message"),
    (0x3E00, "Logical unit has not self-configured yet"),
    (0x3E01, "Logical unit failure"),
    (0x3E02, "Timeout on logical unit"),
    (0x3E03, "Logical unit failed self-test"),
    (0x3E04, "Logical unit unable to update self-test log"),
    (0x3F00, "Target operating conditions have changed"),
    (0x3F01, "Microcode has been changed"),
    (0x3F02, "Changed operating definition"),
    (0x3F03, "Inquiry data has changed"),
    (0x3F04, "Component device attached"),
    (0x3F05, "Device identifier changed"),
    (0x3F06, "Redundancy group created or modified"),
    (0x3F07, "Redundancy group deleted"),
    (0x3F08, "Spare created or modified"),
    (0x3F09, "Spare deleted"),
    (0x3F0A, "Volume set created or modified"),
    (0x3F0B, "Volume set deleted"),
    (0x3F0C, "Volume set deassigned"),
    (0x3F0D, "Volume set reassigned"),
    (0x3F0E, "Reported luns data has changed"),
    (0x3F0F, "Echo buffer overwritten"),
    (0x3F10, "Medium loadable"),
    (0x3F11, "Medium auxiliary memory accessible"),
#    (0x40NN, "Ram failure"),
#    (0x40NN, "Diagnostic failure on component nn"),
#    (0x41NN, "Data path failure"),
#    (0x42NN, "Power-on or self-test failure"),
    (0x4300, "Message error"),
    (0x4400, "Internal target failure"),
    (0x4500, "Select or reselect failure"),
    (0x4600, "Unsuccessful soft reset"),
    (0x4700, "Scsi parity error"),
    (0x4701, "Data phase CRC error detected"),
    (0x4702, "Scsi parity error detected during st data phase"),
    (0x4703, "Information unit CRC error detected"),
    (0x4704, "Asynchronous information protection error detected"),
    (0x4705, "Protocol service CRC error"),
    (0x4800, "Initiator detected error message received"),
    (0x4900, "Invalid message error"),
    (0x4A00, "Command phase error"),
    (0x4B00, "Data phase error"),
    (0x4C00, "Logical unit failed self-configuration"),
#    (0x4DNN, "Tagged overlapped commands (nn = queue tag)"),
    (0x4E00, "Overlapped commands attempted"),
    (0x5000, "Write append error"),
    (0x5001, "Write append position error"),
    (0x5002, "Position error related to timing"),
    (0x5100, "Erase failure"),
    (0x5101, "Erase failure - incomplete erase operation detected"),
    (0x5200, "Cartridge fault"),
    (0x5300, "Media load or eject failed"),
    (0x5301, "Unload tape failure"),
    (0x5302, "Medium removal prevented"),
    (0x5303, "Medium removal prevented by data transfer element"),
    (0x5304, "Medium thread or unthread failure"),
    (0x5400, "Scsi to host system interface failure"),
    (0x5500, "System resource failure"),
    (0x5501, "System buffer full"),
    (0x5502, "Insufficient reservation resources"),
    (0x5503, "Insufficient resources"),
    (0x5504, "Insufficient registration resources"),
    (0x5505, "Insufficient access control resources"),
    (0x5506, "Auxiliary memory out of space"),
    (0x5508, "Maximum number of supplemental decryption keys exceeded"),
    (0x5509, "Medium auxiliary memory not accessible"),
    (0x550A, "Data currently unavailable"),
    (0x5700, "Unable to recover table-of-contents"),
    (0x5800, "Generation does not exist"),
    (0x5900, "Updated block read"),
    (0x5A00, "Operator request or state change input"),
    (0x5A01, "Operator medium removal request"),
    (0x5A02, "Operator selected write protect"),
    (0x5A03, "Operator selected write permit"),
    (0x5B00, "Log exception"),
    (0x5B01, "Threshold condition met"),
    (0x5B02, "Log counter at maximum"),
    (0x5B03, "Log list codes exhausted"),
    (0x5C00, "Rpl status change"),
    (0x5C01, "Spindles synchronized"),
    (0x5C02, "Spindles not synchronized"),
    (0x5D00, "Failure prediction threshold exceeded"),
    (0x5D01, "Media failure prediction threshold exceeded"),
    (0x5D02, "Logical unit failure prediction threshold exceeded"),
    (0x5D03, "Spare area exhaustion prediction threshold exceeded"),
    (0x5D10, "Hardware impending failure general hard drive failure"),
    (0x5D11, "Hardware impending failure drive error rate too high"),
    (0x5D12, "Hardware impending failure data error rate too high"),
    (0x5D13, "Hardware impending failure seek error rate too high"),
    (0x5D14, "Hardware impending failure too many block reassigns"),
    (0x5D15, "Hardware impending failure access times too high"),
    (0x5D16, "Hardware impending failure start unit times too high"),
    (0x5D17, "Hardware impending failure channel parametrics"),
    (0x5D18, "Hardware impending failure controller detected"),
    (0x5D19, "Hardware impending failure throughput performance"),
    (0x5D1A, "Hardware impending failure seek time performance"),
    (0x5D1B, "Hardware impending failure spin-up retry count"),
    (0x5D1C, "Hardware impending failure drive calibration retry count"),
    (0x5D20, "Controller impending failure general hard drive failure"),
    (0x5D21, "Controller impending failure drive error rate too high"),
    (0x5D22, "Controller impending failure data error rate too high"),
    (0x5D23, "Controller impending failure seek error rate too high"),
    (0x5D24, "Controller impending failure too many block reassigns"),
    (0x5D25, "Controller impending failure access times too high"),
    (0x5D26, "Controller impending failure start unit times too high"),
    (0x5D27, "Controller impending failure channel parametrics"),
    (0x5D28, "Controller impending failure controller detected"),
    (0x5D29, "Controller impending failure throughput performance"),
    (0x5D2A, "Controller impending failure seek time performance"),
    (0x5D2B, "Controller impending failure spin-up retry count"),
    (0x5D2C, "Controller impending failure drive calibration retry count"),
    (0x5D30, "Data channel impending failure general hard drive failure"),
    (0x5D31, "Data channel impending failure drive error rate too high"),
    (0x5D32, "Data channel impending failure data error rate too high"),
    (0x5D33, "Data channel impending failure seek error rate too high"),
    (0x5D34, "Data channel impending failure too many block reassigns"),
    (0x5D35, "Data channel impending failure access times too high"),
    (0x5D36, "Data channel impending failure start unit times too high"),
    (0x5D37, "Data channel impending failure channel parametrics"),
    (0x5D38, "Data channel impending failure controller detected"),
    (0x5D39, "Data channel impending failure throughput performance"),
    (0x5D3A, "Data channel impending failure seek time performance"),
    (0x5D3B, "Data channel impending failure spin-up retry count"),
    (0x5D3C, "Data channel impending failure drive calibration retry count"),
    (0x5D40, "Servo impending failure general hard drive failure"),
    (0x5D41, "Servo impending failure drive error rate too high"),
    (0x5D42, "Servo impending failure data error rate too high"),
    (0x5D43, "Servo impending failure seek error rate too high"),
    (0x5D44, "Servo impending failure too many block reassigns"),
    (0x5D45, "Servo impending failure access times too high"),
    (0x5D46, "Servo impending failure start unit times too high"),
    (0x5D47, "Servo impending failure channel parametrics"),
    (0x5D48, "Servo impending failure controller detected"),
    (0x5D49, "Servo impending failure throughput performance"),
    (0x5D4A, "Servo impending failure seek time performance"),
    (0x5D4B, "Servo impending failure spin-up retry count"),
    (0x5D4C, "Servo impending failure drive calibration retry count"),
    (0x5D50, "Spindle impending failure general hard drive failure"),
    (0x5D51, "Spindle impending failure drive error rate too high"),
    (0x5D52, "Spindle impending failure data error rate too high"),
    (0x5D53, "Spindle impending failure seek error rate too high"),
    (0x5D54, "Spindle impending failure too many block reassigns"),
    (0x5D55, "Spindle impending failure access times too high"),
    (0x5D56, "Spindle impending failure start unit times too high"),
    (0x5D57, "Spindle impending failure channel parametrics"),
    (0x5D58, "Spindle impending failure controller detected"),
    (0x5D59, "Spindle impending failure throughput performance"),
    (0x5D5A, "Spindle impending failure seek time performance"),
    (0x5D5B, "Spindle impending failure spin-up retry count"),
    (0x5D5C, "Spindle impending failure drive calibration retry count"),
    (0x5D60, "Firmware impending failure general hard drive failure"),
    (0x5D61, "Firmware impending failure drive error rate too high"),
    (0x5D62, "Firmware impending failure data error rate too high"),
    (0x5D63, "Firmware impending failure seek error rate too high"),
    (0x5D64, "Firmware impending failure too many block reassigns"),
    (0x5D65, "Firmware impending failure access times too high"),
    (0x5D66, "Firmware impending failure start unit times too high"),
    (0x5D67, "Firmware impending failure channel parametrics"),
    (0x5D68, "Firmware impending failure controller detected"),
    (0x5D69, "Firmware impending failure throughput performance"),
    (0x5D6A, "Firmware impending failure seek time performance"),
    (0x5D6B, "Firmware impending failure spin-up retry count"),
    (0x5D6C, "Firmware impending failure drive calibration retry count"),
    (0x5DFF, "Failure prediction threshold exceeded (false)"),
    (0x5E00, "Low power condition on"),
    (0x5E01, "Idle condition activated by timer"),
    (0x5E02, "Standby condition activated by timer"),
    (0x5E03, "Idle condition activated by command"),
    (0x5E04, "Standby condition activated by command"),
    (0x5E41, "Power state change to active"),
    (0x5E42, "Power state change to idle"),
    (0x5E43, "Power state change to standby"),
    (0x5E45, "Power state change to sleep"),
    (0x5E47, "Power state change to device control"),
    (0x6000, "Lamp failure"),
    (0x6100, "Video acquisition error"),
    (0x6101, "Unable to acquire video"),
    (0x6102, "Out of focus"),
    (0x6200, "Scan head positioning error"),
    (0x6300, "End of user area encountered on this track"),
    (0x6301, "Packet does not fit in available space"),
    (0x6400, "Illegal mode for this track"),
    (0x6401, "Invalid packet size"),
    (0x6500, "Voltage fault"),
    (0x6600, "Automatic document feeder cover up"),
    (0x6601, "Automatic document feeder lift up"),
    (0x6602, "Document jam in automatic document feeder"),
    (0x6603, "Document miss feed automatic in document feeder"),
    (0x6700, "Configuration failure"),
    (0x6701, "Configuration of incapable logical units failed"),
    (0x6702, "Add logical unit failed"),
    (0x6703, "Modification of logical unit failed"),
    (0x6704, "Exchange of logical unit failed"),
    (0x6705, "Remove of logical unit failed"),
    (0x6706, "Attachment of logical unit failed"),
    (0x6707, "Creation of logical unit failed"),
    (0x6708, "Assign failure occurred"),
    (0x6709, "Multiply assigned logical unit"),
    (0x670A, "Set target port groups command failed"),
    (0x6800, "Logical unit not configured"),
    (0x6900, "Data loss on logical unit"),
    (0x6901, "Multiple logical unit failures"),
    (0x6902, "Parity/data mismatch"),
    (0x6A00, "Informational, refer to log"),
    (0x6B00, "State change has occurred"),
    (0x6B01, "Redundancy level got better"),
    (0x6B02, "Redundancy level got worse"),
    (0x6C00, "Rebuild failure occurred"),
    (0x6D00, "Recalculate failure occurred"),
    (0x6E00, "Command to logical unit failed"),
    (0x6F00, "Copy protection key exchange failure - authentication failure"),
    (0x6F01, "Copy protection key exchange failure - key not present"),
    (0x6F02, "Copy protection key exchange failure - key not established"),
    (0x6F03, "Read of scrambled sector without authentication"),
    (0x6F04, "Media region code is mismatched to logical unit region"),
    (0x6F05, "Drive region must be permanent/region reset count error"),
#    (0x70NN, "Decompression exception short algorithm id of nn"),
    (0x7100, "Decompression exception long algorithm id"),
    (0x7200, "Session fixation error"),
    (0x7201, "Session fixation error writing lead-in"),
    (0x7202, "Session fixation error writing lead-out"),
    (0x7203, "Session fixation error - incomplete track in session"),
    (0x7204, "Empty or partially written reserved track"),
    (0x7205, "No more track reservations allowed"),
    (0x7300, "Cd control error"),
    (0x7301, "Power calibration area almost full"),
    (0x7302, "Power calibration area is full"),
    (0x7303, "Power calibration area error"),
    (0x7304, "Program memory area update failure"),
    (0x7305, "Program memory area is full"),
    (0x7306, "RMA/PMA is almost full"),
    (0x740B, "Incorrect encryption parameters"),
    (0x740C, "Unable to decrypt parameter list"),
    (0x740D, "Encryption algorithm disabled"),
    (0x7410, "SA creation parameter value invalid"),
    (0x7411, "SA creation parameter value rejected"),
    (0x7412, "Invalid SA usage"),
    (0x7421, "Data encryption configuration prevented"),
    (0x7430, "SA creation parameter not supported"),
    (0x7440, "Authentication failed"),
    (0x7461, "External data encryption key manager access error"),
    (0x7462, "External data encryption key manager error"),
    (0x7463, "External data encryption key not found"),
    (0x7464, "External data encryption request not authorized"),
    (0x746E, "External data encryption control timeout"),
    (0x746F, "External data encryption control error "),
    (0x7479, "Security conflict in translated device"),
)