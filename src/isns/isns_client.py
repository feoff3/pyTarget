#    
#    isns client code.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-05-12)
#

import copy
from isns.isns_lib import *
from isns.isns_sock import *
from comm.debug import *

# isns task status
ISNS_TASK_SEND_FAILED       = -1
ISNS_TASK_RECV_FAILED       = -2
ISNS_TASK_RSP_FAILED        = -3
ISNS_TASK_SUCCESS           = 0


class ITR():
    '''
    isns task request
    '''
    def __init__(self, req):
        self.req_pdu = req
        self.rsp_pdu = None
        self.status = ISNS_TASK_SUCCESS


class iSNSClient():
    '''
    isns client class
    '''

    def __init__(self, ip, port=ISNS_DEFAULT_PORT, type=ISNS_TCP_CLIENT):
        '''
        initialize isns client
        @param ip: isns server ip
        @param port: isns server port
        @param type: isns client socket type (ISNS_TCP_CLIENT or ISNS_UDP_CLIENT)
        '''
        self.ip = ip
        self.port = port
        self.type = type
        self.xid  = 0
        self.server_sock = None
        self.client_sock = iSnsSock(ip, port, type)

    def __xid(self):
        '''
        get next xid
        '''
        self.xid += 1
        return self.xid


    def initial(self):
        '''
        initialize isns client socket.
        @return: True for success, False for failed.
        '''
        return self.client_sock.initial()


    def DevAttrQry(self, iqn):
        '''
        Device Attribute Query Request
        '''
        flags = ISNS_FLAG_SND_CLIENT | ISNS_FLAG_REPLACE_REG | ISNS_FLAG_FIRST_PDU | ISNS_FLAG_LAST_PDU
        req = ISNS_PDU(ISNS_DEV_ATTR_QRY_REQ, flags, self.__xid())
        req.AddIscsiName(iqn)
        req.AddIscsiName(iqn)
        req.AddDelimiter()
        req.AddAttributeTag(ISNS_ISCSI_NODE_ID, "")
        req.AddAttributeTag(ISNS_ISCSI_TYPE, "")
        req.AddAttributeTag(ISNS_ISCSI_ALIAS, "")
        req.AddAttributeTag(ISNS_PORTAL_IP, "")
        req.AddAttributeTag(ISNS_PORTAL_PORT, "")
        req.AddAttributeTag(ISNS_PORTAL_SECURITY_BITMAP, "")
        req.AddAttributeTag(ISNS_PORTAL_SYM_NAME, "")
        req.AddAttributeTag(ISNS_PORTAL_GROUP_ISCSI_NAME, "")
        req.AddAttributeTag(ISNS_PORTAL_GROUP_IP, "")
        req.AddAttributeTag(ISNS_PORTAL_GROUP_PORT, "")
        req.AddAttributeTag(ISNS_PORTAL_GROUP_TAG, "")
        return self.Task(ITR(req))


    def SCNReg(self, iqn):
        '''
        SCN Register Request
        '''
        flags = ISNS_FLAG_SND_CLIENT | ISNS_FLAG_REPLACE_REG | ISNS_FLAG_FIRST_PDU  | ISNS_FLAG_LAST_PDU
        req = ISNS_PDU(ISNS_SCN_DEREG_REQ, flags, self.__xid())
        req.AddIscsiName(iqn)
        req.AddIscsiName(iqn)
        return self.Task(ITR(req))


    def DeregDev(self, iqn, entry, ip, port):
        '''
        Deregister Device Request
        '''
        flags = ISNS_FLAG_SND_CLIENT | ISNS_FLAG_REPLACE_REG | ISNS_FLAG_FIRST_PDU  | ISNS_FLAG_LAST_PDU
        req = ISNS_PDU(ISNS_DEREG_DEV_REQ, flags, self.__xid())
        req.AddIscsiName(iqn)
        req.AddDelimiter()
        req.AddEntityID(entry)
        req.AddPortalIP(ip)
        req.AddPortalPort(port)
        req.AddIscsiName(iqn)
        return self.Task(ITR(req))


    def DevAttrReg(self, iqn, entry, ip, port, scn_esi_port, pg_portal, pg_iqn):
        '''
        Register Device Attribute Request
        '''
        flags = ISNS_FLAG_SND_CLIENT | ISNS_FLAG_REPLACE_REG | ISNS_FLAG_FIRST_PDU  | ISNS_FLAG_LAST_PDU
        req = ISNS_PDU(ISNS_REG_DEV_ATTR_REQ, flags, self.__xid())
        req.AddIscsiName(iqn)
        req.AddDelimiter()
        req.AddEntityID(entry)
        req.AddEntryProtocol(ENTITY_TYPE_ISCSI)        
        req.AddPortalIP(ip)
        req.AddPortalPort(port)
        req.AddSCNPort(scn_esi_port)
        req.AddESIPort(scn_esi_port)
        req.AddPortalGroupTag(pg_portal)
        req.AddPortalGroupIscsiName(pg_iqn)
        req.AddIscsiName(iqn)
        req.AddIscsiNodeType(ISNS_ISCSI_TYPE_TARGET)
        # req.AddIscsiAlias('pyTarget-iSNS-Client')
        return self.Task(ITR(req))


    def Task(self, itr):
        '''
        do isns task
        @param itr: isns task request
        @return: True for success, other for abnormal
        '''
        if self.client_sock.send(itr.req_pdu) == False:
            itr.status = ISNS_TASK_SEND_FAILED
        else:
            itr.rsp_pdu = self.client_sock.recv()
            if not itr.rsp_pdu:
                itr.status = ISNS_TASK_RECV_FAILED
            elif itr.rsp_pdu.data[:4] != '\0' * 4:
                itr.status = ISNS_TASK_RSP_FAILED
            else:
                itr.status = ISNS_TASK_SUCCESS            
        return itr.status == ISNS_TASK_SUCCESS

    def Stop(self):
        '''
        close isns socket.
        '''
        if self.client_sock:
            self.client_sock.close()
            self.client_sock = None
        if self.server_sock:
            self.server_sock.close()
            self.server_sock = None


    def SCN_ESI_Handle(self, sock):
        '''
        handle scn/esi event.
        '''
        DBG_PRN('iSNS SCN/ESI event.')
        event = sock.recv()
        if event:
            flags = ISNS_FLAG_SND_CLIENT | ISNS_FLAG_FIRST_PDU  | ISNS_FLAG_LAST_PDU
            if event.fun == ISNS_ESI:
                pdu = ISNS_PDU(ISNS_ESI_RSP, flags, event.xid)
            elif event.fun == ISNS_SCN:
                pdu = ISNS_PDU(ISNS_SCN_RES, flags, event.xid)
            else:
                DBG_WRN('Unknow isns event. Function ID:', event.fun)
                return False
            pdu.len = event.len + 4
            pdu.data = '\0' * 4 + event.data
            res = sock.send(pdu)
            DBG_PRN('ESI event')
        else:
            res = False
            DBG_WRN('ESI receive FAILED')
        return res


    def SCN_ESI_Run(self, port):
        '''
        run isns scn/esi routing.
        '''
        sock = iSnsSock('', port, ISNS_TCP_SERVER)
        if not sock.initial():
            DBG_WRN('iSNS SCN/ESI daemon initialize FAILED')
            return

        DBG_INF('Start to run iSNS SCN/ESI daemon...')
        while sock.accept():
            self.SCN_ESI_Handle(sock)
            sock.close(SOCKET_TCP_CLIENT)
            
