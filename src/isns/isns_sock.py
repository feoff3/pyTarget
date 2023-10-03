#    
#    enclose a new class for isns socket.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-05-12)
#

from comm.comm_sock import *
from isns.isns_lib import *


ISNS_TCP_SERVER = SOCKET_TCP_SERVER
ISNS_TCP_CLIENT = SOCKET_TCP_CLIENT
ISNS_UDP_SERVER = SOCKET_UDP_SERVER
ISNS_UDP_CLIENT = SOCKET_UDP_CLIENT


class iSnsSock(CommSock):
    '''
    isns socket class
    '''

    def __init__(self, ip, port, skt=ISNS_TCP_CLIENT):
        '''
        isnssock Constructor
        @param ip: socket ip address
        @param port: socket port
        @param skt: socket type
        '''
        CommSock.__init__(self, skt, ip, port)
        
    
    def send(self, pdu):
        '''
        send isns pdu
        @param pdu: isns pdu
        @return: True for success, False for failed
        '''
        assert(pdu.len == len(pdu.data))
        buf  = u16_buf(pdu.version)
        buf += u16_buf(pdu.fun)
        buf += u16_buf(pdu.len)
        buf += u16_buf(pdu.flags)
        buf += u16_buf(pdu.xid)
        buf += u16_buf(pdu.sid)
        buf += pdu.data
        return CommSock.send(self, buf) 

    def recv(self):
        '''
        recv isns pdu
        @return: None for failed, other for success
        '''
        pdu = ISNS_PDU()
        buf = CommSock.recv(self, ISNS_PDU_SIZE)
        if not buf:
            DBG_WRN('iSNS receive pdu FAILED')
            return None
        pdu.version = buf_u16(buf, 0)
        pdu.fun = buf_u16(buf, 2)
        pdu.len = buf_u16(buf, 4)
        pdu.flags = buf_u16(buf, 6)
        pdu.xid = buf_u16(buf, 8)
        pdu.sid = buf_u16(buf, 10)
        if pdu.len:
            pdu.data = CommSock.recv(self, pdu.len)
            if not pdu.data:
                DBG_WRN('iSNS receive data FAILED')
                return None
        return pdu

        
