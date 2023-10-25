#    
#    iscsi protocol(RFC3720) defines.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#

ISCSI_DRAFT20_VERSION                       = 0x00
ISCSI_LISTEN_PORT                           = 3260
ISCSI_BHS_SIZE                              = 48

# Opcode encoding bits 
ISCSI_OP_RETRY                              = 0x80
ISCSI_OP_IMMEDIATE                          = 0x40
ISCSI_OPCODE_MASK                           = 0x3F

def OPCODE(pdu):
    return (pdu.bhs[0] & ISCSI_OPCODE_MASK)

def IS_IMMEDIATE(pdu):
    return (pdu.bhs[0] & ISCSI_OP_IMMEDIATE)

def SCSI_CODE(pdu):
    return pdu.bhs[32]

#
# Initiator Opcode values
#
ISCSI_OP_NOOP_OUT                           = 0x00
ISCSI_OP_SCSI_CMD                           = 0x01
ISCSI_OP_SCSI_TMFUNC                        = 0x02
ISCSI_OP_LOGIN                              = 0x03
ISCSI_OP_TEXT                               = 0x04
ISCSI_OP_SCSI_DATA_OUT                      = 0x05
ISCSI_OP_LOGOUT                             = 0x06
ISCSI_OP_SNACK                              = 0x10

ISCSI_OP_VENDOR1_CMD                        = 0x1c
ISCSI_OP_VENDOR2_CMD                        = 0x1d
ISCSI_OP_VENDOR3_CMD                        = 0x1e
ISCSI_OP_VENDOR4_CMD                        = 0x1f

#
# Target Opcode values
#
ISCSI_OP_NOOP_IN                            = 0x20
ISCSI_OP_SCSI_CMD_RSP                       = 0x21
ISCSI_OP_SCSI_TMFUNC_RSP                    = 0x22
ISCSI_OP_LOGIN_RSP                          = 0x23
ISCSI_OP_TEXT_RSP                           = 0x24
ISCSI_OP_SCSI_DATA_IN                       = 0x25
ISCSI_OP_LOGOUT_RSP                         = 0x26
ISCSI_OP_R2T                                = 0x31
ISCSI_OP_ASYNC_EVENT                        = 0x32
ISCSI_OP_REJECT                             = 0x3f

#
# Login error class & detail
#
# Login Status response classes
ISCSI_STATUS_CLS_SUCCESS                    = 0x00
ISCSI_STATUS_CLS_REDIRECT                   = 0x01
ISCSI_STATUS_CLS_INITIATOR_ERR              = 0x02
ISCSI_STATUS_CLS_TARGET_ERR                 = 0x03

# Login Status response detail codes
# Class-0 (Success)
ISCSI_LOGIN_STATUS_ACCEPT                   = 0x00

# Class-1 (Redirection)
ISCSI_LOGIN_STATUS_TGT_MOVED_TEMP           = 0x01
ISCSI_LOGIN_STATUS_TGT_MOVED_PERM           = 0x02

# Class-2 (Initiator Error)
ISCSI_LOGIN_STATUS_INIT_ERR                 = 0x00
ISCSI_LOGIN_STATUS_AUTH_FAILED              = 0x01
ISCSI_LOGIN_STATUS_TGT_FORBIDDEN            = 0x02
ISCSI_LOGIN_STATUS_TGT_NOT_FOUND            = 0x03
ISCSI_LOGIN_STATUS_TGT_REMOVED              = 0x04
ISCSI_LOGIN_STATUS_NO_VERSION               = 0x05
ISCSI_LOGIN_STATUS_ISID_ERROR               = 0x06
ISCSI_LOGIN_STATUS_MISSING_FIELDS           = 0x07
ISCSI_LOGIN_STATUS_CONN_ADD_FAILED          = 0x08
ISCSI_LOGIN_STATUS_NO_SESSION_TYPE          = 0x09
ISCSI_LOGIN_STATUS_NO_SESSION               = 0x0a
ISCSI_LOGIN_STATUS_INVALID_REQUEST          = 0x0b

# Class-3 (Target Error)
ISCSI_LOGIN_STATUS_TARGET_ERROR             = 0x00
ISCSI_LOGIN_STATUS_SVC_UNAVAILABLE          = 0x01
ISCSI_LOGIN_STATUS_NO_RESOURCES             = 0x02

#ISCSI_AHSTYPE_CDB                           = 1
#ISCSI_AHSTYPE_RLENGTH                       = 2
#ISCSI_CDB_SIZE                              = 16

# Command PDU flags
ISCSI_FLAG_CMD_FINAL                        = 0x80
ISCSI_FLAG_CMD_READ                         = 0x40
ISCSI_FLAG_CMD_WRITE                        = 0x20
ISCSI_FLAG_CMD_ATTR_MASK                    = 0x07    # 3 bits

# SCSI Command Attribute values
ISCSI_ATTR_UNTAGGED                         = 0
ISCSI_ATTR_SIMPLE                           = 1
ISCSI_ATTR_ORDERED                          = 2
ISCSI_ATTR_HEAD_OF_QUEUE                    = 3
ISCSI_ATTR_ACA                              = 4

# iSCSI Chap type
CHAP_MD5                                    = 5
CHAP_SHA1                                   = 7

# iSCSI CHAP State
CHAP_STATE_CHAP                             = 1
CHAP_STATE_CHAP_A                           = 2
CHAP_STATE_CHAP_I                           = 3
CHAP_STATE_FINISH                           = 4

# iSCSI digest type
DIGEST_NONE                                 = 0x00
DIGEST_HEAD                                 = 0x01
DIGEST_DATA                                 = 0x02
DIGEST_ALL                                  = (DIGEST_HEAD | DIGEST_DATA)


#
# iSCSI opcode descriptor
#
__ISCSI_CODE_DESCRIPTOR = {
    # Initiator opcode
    ISCSI_OP_NOOP_OUT:                  'Nopout',
    ISCSI_OP_SCSI_CMD:                  'SCSI Request',
    ISCSI_OP_SCSI_TMFUNC:               'Task Management Request',
    ISCSI_OP_LOGIN:                     'Login Request',
    ISCSI_OP_TEXT:                      'Text Request',
    ISCSI_OP_SCSI_DATA_OUT:             'DataOut',
    ISCSI_OP_LOGOUT:                    'Logout Request',
    ISCSI_OP_SNACK:                     'SNACK Request',
    ISCSI_OP_VENDOR1_CMD:               'Vendor Cmd1',
    ISCSI_OP_VENDOR2_CMD:               'Vendor Cmd2',
    ISCSI_OP_VENDOR3_CMD:               'Vendor Cmd3',
    ISCSI_OP_VENDOR4_CMD:               'Vendor Cmd4',

    # Target opcode
    ISCSI_OP_NOOP_IN:                   'NopIn',
    ISCSI_OP_SCSI_CMD_RSP:              'SCSI Cmd Response',
    ISCSI_OP_SCSI_TMFUNC_RSP:           'Task Management Response',
    ISCSI_OP_LOGIN_RSP:                 'Login Response',
    ISCSI_OP_TEXT_RSP:                  'Test Response',
    ISCSI_OP_SCSI_DATA_IN:              'DataIn',
    ISCSI_OP_LOGOUT_RSP:                'Logout Response',
    ISCSI_OP_R2T:                       'R2T',
    ISCSI_OP_ASYNC_EVENT:               'Asynchronous',
    ISCSI_OP_REJECT:                    'Reject' 
}

ISCSI_LEADING_KEY = (
    'SessionType',
    'MaxConnections',
    'MaxBurstLength', 
    'FirstBurstLength',
    'DefaultTime2Wait',
    'DefaultTime2Retain',
    'MaxOutstandingR2T',
    'ErrorRecoveryLevel',
    'InitialR2T',
    'ImmediateData',
    'DataPDUInOrder',
    'DataSequenceInOrder',
    'TaskReporting'
)

ISCSI_DISCOVERY_IRRELEVANT_KEY = (
    'MaxConnections',
    'InitialR2T',
    'ImmediateData',
    'MaxBurstLength',
    'FirstBurstLength',
    'MaxOutstandingR2T',
    'DataPDUInOrder',
    'DataSequenceInOrder',
    'TaskReporting'
)

ISCSI_TARGET_ONLY_KEY = {
    'TargetAlias' : None,
    'TargetAddress' : None,
    'TargetPortalGroupTag' : None,
}

def ISCSI_DESC(code):
    '''
    get iscsi opcode descriptor
    @param code: iscsi opcode
    @return: string of descriptor
    '''
    if code in __ISCSI_CODE_DESCRIPTOR:
        return __ISCSI_CODE_DESCRIPTOR[code]
    return 'Unknown iscsi opcode'
