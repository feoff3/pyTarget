#    
#    isns protocol(RFC4171 defines.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-05-12)
#

ISNS_DEFAULT_PORT                       = 3205
ISNS_PDU_SIZE                           = 12

# New scn types
ISNS_SCN_ALL                            = 0x1F
ISNS_SCN_MEMBER_ADDED                   = 0x01
ISNS_SCN_MEMBER_REMOVED                 = 0x02
ISNS_SCN_OBJ_ADDED                      = 0x04
ISNS_SCN_OBJ_REMOVED                    = 0x08
ISNS_SCN_OBJ_UPDATED                    = 0x10


# ISCSI TYPES
ISNS_ISCSI_TYPE_TARGET                  = 0x01
ISNS_ISCSI_TYPE_INITIATOR               = 0x02
ISNS_ISCSI_TYPE_CONTROL                 = 0x04
ISNS_ISCSI_TYPE_REMOTE                  = 0x08


#
# ISNS FUNCTION IDs
#

# Request 
ISNS_START_VALID_REQ_FUNC_ID            = 1
ISNS_REG_DEV_ATTR_REQ                   = 1
ISNS_DEV_ATTR_QRY_REQ                   = 2
ISNS_DEV_GET_NXT_REQ                    = 3
ISNS_DEREG_DEV_REQ                      = 4
ISNS_SCN_REG_REQ                        = 5
ISNS_SCN_DEREG_REQ                      = 6
ISNS_SCN_EVENT                          = 7
ISNS_SCN                                = 8
ISNS_REG_DD_REQ                         = 9
ISNS_DEREG_DD_REQ                       = 0x0a
ISNS_REG_DDS_REQ                        = 0x0b
ISNS_DEREG_DDS_REQ                      = 0x0c
ISNS_ESI                                = 0x0d
ISNS_HEART_BEAT                         = 0x0e
ISNS_REQ_SW_ID_REQ                      = 0x11,                          
ISNS_REL_SW_ID_REQ                      = 0x12
ISNS_GET_SW_ID_REQ                      = 0x13
ISNS_DDS_GET_NXT_MEMBER_REQ             = 0x14
ISNS_DD_GET_NXT_ISCSI_MEMBER_REQ        = 0x15
ISNS_ENTITY_GET_NXT_PORTAL_REQ          = 0x16
ISNS_END_VALID_REQ_FUNC_ID              = 0x17

# Response
ISNS_START_VALID_RES_FUNC_ID            = 0x8001
ISNS_REG_DEV_ATTR_RES                   = 0x8001
ISNS_DEV_ATTR_QRY_RES                   = 0x8002
ISNS_DEV_GET_NXT_RES                    = 0x8003
ISNS_DEREG_DEV_RES                      = 0x8004
ISNS_SCN_REG_RES                        = 0x8005
ISNS_SCN_DEREG_RES                      = 0x8006
ISNS_SCN_EVENT_RES                      = 0x8007
ISNS_SCN_RES                            = 0x8008
ISNS_REG_DD_RES                         = 0x8009
ISNS_DEREG_DD_RES                       = 0x800a
ISNS_REG_DDS_RES                        = 0x800b
ISNS_DEREG_DDS_RES                      = 0x800c
ISNS_ESI_RSP                            = 0x800d
ISNS_REQ_SW_ID_RES                      = 0x8011
ISNS_REL_SW_ID_RES                      = 0x8012
ISNS_GET_SW_ID_RES                      = 0x8013
ISNS_DDS_GET_NXT_MEMBER_RES             = 0x8014
ISNS_DD_GET_NXT_ISCSI_MEMBER_RES        = 0x8015
ISNS_ENTITY_GET_NXT_PORTAL_RES          = 0x8016
ISNS_END_VALID_RES_FUNC_ID              = 0x8017


# ISNS Tags
ISNS_DELIMITER                          = 0
ISNS_START_VALID_TAG                    = 1

# ENTITY tags
ISNS_ENTITY_ID                          = 1
ISNS_ENTITY_TYPE                        = 2
ISNS_MGMT_IP                            = 3
ISNS_TIMESTAMP                          = 4
ISNS_PROT_VER                           = 5
ISNS_ENTITY_PERIOD                      = 6
ISNS_ENTITY_IDX                         = 7
ISNS_ENTITY_NEXT_IDX                    = 8
ISNS_ENTITY_ISAKMP                      = 0x0b
ISNS_ENTITY_CERT                        = 0x0c

# PORT tags
ISNS_PORTAL_IP                          = 0x10
ISNS_PORTAL_PORT                        = 0x11
ISNS_PORTAL_SYM_NAME                    = 0x12
ISNS_ESI_INTERVAL                       = 0x13
ISNS_ESI_PORT                           = 0x14
ISNS_PORTAL_GROUP                       = 0x15
ISNS_PORTAL_IDX                         = 0x16
ISNS_SCN_PORT                           = 0x17
ISNS_PORTAL_NEXT_IDX                    = 0x18
ISNS_PORTAL_SECURITY_BITMAP             = 0x1b
ISNS_PORTAL_CERT                        = 0x1f

# ISCSI node tags
ISNS_ISCSI_NODE_ID                      = 0x20
ISNS_ISCSI_TYPE                         = 0x21
ISNS_ISCSI_ALIAS                        = 0x22
ISNS_ISCSI_SCN_BITMAP                   = 0x23
ISNS_ISCSI_IDX                          = 0x24
ISNS_WWNN_TOKEN                         = 0x25
ISNS_ISCSI_NEXT_IDX                     = 0x26
ISNS_ISCSI_CERT                         = 0x28

# PORTAL_GROUP tags
ISNS_PORTAL_GROUP_ISCSI_NAME            = 0x30
ISNS_PORTAL_GROUP_IP                    = 0x31
ISNS_PORTAL_GROUP_PORT                  = 0x32
ISNS_PORTAL_GROUP_TAG                   = 0x33
ISNS_PORTAL_GROUP_IDX                   = 0x34
ISNS_PORTAL_GROUP_NEXT_IDX              = 0x35

# FC
ISNS_PORT_NAME                          = 64
ISNS_PORT_ID                            = 65
ISNS_PORT_TYPE                          = 66
ISNS_PORT_SYM_NAME                      = 67
ISNS_FABRIC_PORT_NAME                   = 68
ISNS_FC_HARD_ADDR                       = 69
ISNS_FC_PORT_IP                         = 70
ISNS_FC_COS                             = 71
ISNS_FC4_TYPE                           = 71
ISNS_FC4_DESC                           = 73
ISNS_FC4_FEATURE                        = 74
ISNS_IFCP_SCN_BITMAP                    = 75
ISNS_IFCP_NODE_CERT                     = 80
iSNS_FC4_TYPE_QUERY_KEY                 = 95
ISNS_NODE_NAME                          = 96
ISNS_NODE_SYM_NAME                      = 97
ISNS_FC_NODE_IP                         = 98
ISNS_FC_NODE_IPA                        = 99
ISNS_FC_NODE_CERT                       = 100

# Server specific tags
ISNS_VENDOR_ID                          = 131
ISNS_VENDOR_REV                         = 132
ISNS_PRIMARY_VER                        = 133
ISNS_PRIMARY_IP                         = 134
ISNS_PRIMARY_TCP_PORT                   = 135
ISNS_PRIMARY_UDP_PORT                   = 136
ISNS_PRIMARY_MGMT_IP                    = 137
ISNS_COMPANY_OUI                        = 256

# Nishan vendor specific tags
ISNS_SCN_CALLBACK                       = 257
ISNS_DD_ACTIVE                          = 258
ISNS_NODE_ACTIVE                        = 259
ISNS_END_VALID_TAG                      = 260

# DDS tags
ISNS_DDS_ID                             = 2049
ISNS_DDS_SYM_NAME                       = 2050
ISNS_DDS_STATUS                         = 2051

# DD tags
ISNS_DD_ID                              = 2065
ISNS_DD_SYM_NAME                        = 2066
ISNS_DD_ISCSI_MEMBER_IDX                = 2067
ISNS_DD_ISCSI_MEMBER                    = 2068
ISNS_DD_IFCP_MEMBER                     = 2069
ISNS_DD_PORTAL_MEMBER_IDX               = 2070
ISNS_DD_PORTAL_IP_ADDR                  = 2071
ISNS_DD_PORTAL_TCPUDP                   = 2072
ISNS_DD_FEATURE_BITMAP                  = 2078
ISNS_DD_NEXT_ID                         = 2079

# ISNS Entity types
NO_PROTOCOL                             = 1
ENTITY_TYPE_ISCSI                       = 2
ENTITY_TYPE_IFCP                        = 3


# ISNS Flags
ISNS_FLAG_FIRST_PDU                     = 0x400
ISNS_FLAG_LAST_PDU                      = 0x800
ISNS_FLAG_REPLACE_REG                   = 0x1000
ISNS_FLAG_AUTH                          = 0x2000
ISNS_FLAG_SND_SERVER                    = 0x4000
ISNS_FLAG_SND_CLIENT                    = 0x8000

# ISNS Error Codes
ISNS_NO_ERR                             = 0x00
ISNS_UNKNOWN_ERR                        = 0x01
ISNS_MSG_FMT_ERR                        = 0x02
ISNS_INVALID_REG_ERR                    = 0x03
ISNS_ESI_TOO_SHORT                      = 0x04
ISNS_INVALID_QUERY_ERR                  = 0x05
ISNS_AUTH_UNKNOWN_ERR                   = 0x06
ISNS_AUTH_ABSENT_ERR                    = 0x07
ISNS_AUTH_FAILED_ERR                    = 0x08
ISNS_NO_SUCH_ENTRY_ERR                  = 0x09
ISNS_VER_NOT_SUPPORTED_ERR              = 0x0a
ISNS_INT_BUS_ERR                        = 0x0b
ISNS_BUSY_NOW_ERR                       = 0x0c
ISNS_OPTION_NOT_UNDERSTOOD_ERR          = 0x0d
ISNS_INVALID_REG_UPD_ERR                = 0x0e
ISNS_MSG_NOT_SUPPORTED_ERR              = 0x0f
ISNS_SCN_EVENT_REJECTED_ERR             = 0x10
ISNS_SCN_REG_REJECTED_ERR               = 0x11
ISNS_SW_ID_NOT_AVAIL                    = 0x12
ISNS_SW_ID_NOT_ALLOC                    = 0x13

