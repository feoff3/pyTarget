#    
#    enclose a new class for iscsi socket.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#

import comm.crc32c as crc32c
from comm import comm_sock
from comm.comm_sock import CommSock
from iscsi.iscsi_lib import *

#
# Iscsi sock type
#
ISCSI_SERVER_TYPE = comm_sock.SOCKET_TCP_SERVER
ISCSI_CLIENT_TYPE = comm_sock.SOCKET_TCP_CLIENT

class IscsiSock(CommSock):
    '''
    Class iscsi socket
    @warning: iSCSI PDU crc32c digest just only occur in sending or receiving. 
    '''

    def __init__(self, ip, port, skt=comm_sock.SOCKET_TCP_SERVER):
        '''
        Iscsisock Constructor
        @param ip: socket ip address
        @param port: socket port
        @param skt: socket type (ISCSI_SERVER_TYPE, ISCSI_CLIENT_TYPE)
        '''
        CommSock.__init__(self, skt, ip, port)


    def __del__(self):
        '''
        Iscsisock destroy
        '''
        self.close(False)
    

    def close(self, isAll = False):
        '''
        Iscsisock close
        @param isAll: False for close client socket,
                      True for server & client socket
        '''
        if isAll:
            CommSock.close(self, 0)
        else:
            CommSock.close(self, ISCSI_CLIENT_TYPE)


    def recv(self, digest, limit):
        '''
        Receive a new iscsi PDU
        @param digest: head digest or data digest flags (DIGEST_HEAD | DIGEST_DATA | DIGEST_ALL)
        @param limit: iscsi pdu datasegment limit
        @return: pdu with state
        '''
        pdu = PDU()

        # BHS
        buf = CommSock.recv(self, ISCSI_BHS_SIZE)
        if buf is None:
            pdu.state = PDU_STATE_SOCK_FAILED
            return pdu
        elif len(buf) == 0:
            pdu.state = PDU_STATE_SOCK_TIMEOUT
            return pdu
        elif len(buf) != ISCSI_BHS_SIZE:
            pdu.state = PDU_STATE_HEAD_FAILED
            return pdu
        pdu.bhs = struct.unpack('B' * ISCSI_BHS_SIZE, buf)

        # AHS (current not support ahs)
        if pdu.bhs[4]:
            pdu.ahs = CommSock.recv(self, pdu.bhs[4])

        # Header Digest
        if digest & DIGEST_HEAD:
            ctx = crc32c.crc32c(buf)
            buf = CommSock.recv(self, 4)
            if ctx != buf:
                if pdu.state == PDU_STATE_GOOD:
                    pdu.state = PDU_STATE_HEAD_FAILED
                # DBG_WRN('Receive or digest header FAILED')
                # return pdu
        # Data
        length = pdu.get_data_len()
        if length > limit:
            DBG_WRN('detect data segment of pdu is too large(%d,%d).'%(length, limit))
            # return None

        if length > 0:
            pdu.data = CommSock.recv(self, length)
            if pdu.data is None or len(pdu.data) != length:
                if pdu.state == PDU_STATE_GOOD:
                    pdu.state = PDU_STATE_DATA_FAILED
                # DBG_WRN('Receive data segment FAILED')
                # return pdu

            # Data Digest
            if digest & DIGEST_DATA:
                if pdu.data:
                    ctx = crc32c.crc32c(pdu.data)
                    buf = CommSock.recv(self, 4)
                    if ctx != buf:
                        if pdu.state == PDU_STATE_GOOD:
                            pdu.state = PDU_STATE_DATA_FAILED
                        # DBG_WRN('Receive or digest data FAILED')
                        # return pdu

        # PADING
        length = align4(length)
        if  length > 0:
            buf = CommSock.recv(self, length)
            if buf is None:
                if pdu.state == PDU_STATE_GOOD:
                    pdu.state = PDU_STATE_PADDING_FAILED
                # DBG_WRN('Receive padding data FAILED')
                # return pdu

        return pdu


    def send(self, pdu, digest):
        '''
        Send a iscsi pdu
        @param pdu: iscsi pdu
        @param digest: head digest or data digest (DIGEST_HEAD | DIGEST_DATA)
        @return: True for success, False for failed
        '''
        buf = struct.pack('B' * ISCSI_BHS_SIZE, *pdu.bhs[:])
        if digest & DIGEST_HEAD:
            buf += crc32c.crc32c(buf)
        if pdu.data and len(pdu.data) > 0:
            data = pdu.data
            if align4(pdu.get_data_len()):
                data += b'\x00' * align4(pdu.get_data_len())
            if digest & DIGEST_DATA:
                data += crc32c.crc32c(data)
            buf += data
        return CommSock.send(self, buf)
