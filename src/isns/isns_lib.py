#    
#    isn library, implement isns functions.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-05-12)
#
import socket
from isns.isns_proto import *
from comm.stdlib import *

class ISNS_PDU():
    '''
    isns message pdu
    '''

    def __init__(self, fun=0, flags=0, xid=0):
        '''
        isns pdu initialize
        @param fun: isns function id
        @param flags: isns flags
        @param xid: transaction id    
        '''
        self.version = 0x0001
        self.fun = fun
        self.len = 0
        self.flags = flags
        self.xid = xid
        self.sid = 0
        self.data = ''

    def AddAttributeTag(self, tag, buf):
        '''
        isns pdu add attribute tag
        @param tag: isns attribute tag
        @param buf: isns tag buffer
        '''
        length = len(buf) + align4(len(buf))
        self.data += u32_buf(tag)
        self.data += u32_buf(length)
        self.data += buf + '\0' * align4(len(buf))
        self.len += length + 8


    def AddDelimiter(self):
        self.AddAttributeTag(ISNS_DELIMITER, '')

    def AddIscsiName(self, iqn):
        self.AddAttributeTag(ISNS_ISCSI_NODE_ID, iqn)
        
    def AddEntityID(self, name=None):
        if name == None: name = socket.gethostname()
        self.AddAttributeTag(ISNS_ENTITY_ID, name)
        
    def AddEntryProtocol(self, proto):
        self.AddAttributeTag(ISNS_ENTITY_TYPE, u32_buf(proto))

    def AddPortalIP(self, ip):
        buf = ip.split('.')
        buf = [atoi(buf[0]), atoi(buf[1]), atoi(buf[2]), atoi(buf[3])]
        buf = [0] * 10 + [0xff] * 2 + buf
        self.AddAttributeTag(ISNS_PORTAL_IP, do_pack(buf))

    def AddPortalPort(self, port):
        self.AddAttributeTag(ISNS_PORTAL_PORT, u16_buf(0) + u16_buf(port))
        
    def AddSCNPort(self, port):
        self.AddAttributeTag(ISNS_SCN_PORT, u16_buf(0) + u16_buf(port))
        
    def AddESIPort(self, port):
        self.AddAttributeTag(ISNS_ESI_PORT, u16_buf(0) + u16_buf(port))
        
    def AddPortalGroupTag(self, portal):
        self.AddAttributeTag(ISNS_PORTAL_GROUP_TAG, u32_buf(portal))
        
    def AddPortalGroupIscsiName(self, iqn):
        self.AddAttributeTag(ISNS_PORTAL_GROUP_ISCSI_NAME, iqn)
        
    def AddIscsiNodeType(self, type):
        self.AddAttributeTag(ISNS_ISCSI_TYPE, u32_buf(type))
        
    def AddIscsiAlias(self, alias):
        self.AddAttributeTag(ISNS_ISCSI_ALIAS, alias)
       
