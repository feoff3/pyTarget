#    
#    general socket class for TCP/UDP/SERVER/CLIENT.
#
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#

import socket as socket_module
from socket import *
from comm.debug import DBG_ERR, DBG_WRN
import select

SOCKET_TCP_SERVER = 1
SOCKET_TCP_CLIENT = 2
SOCKET_UDP_SERVER = 3
SOCKET_UDP_CLIENT = 4


class CommSock():
    '''
    common socket class
    '''

    def __init__(self, type, ip, port):
        '''
        CommSock constructor
        @param type: socket type (SOCKET_TCP_SERVER ...)
        @param ip: socket ip address
        @param port: socket port
        '''
        self.ip = ip
        self.type = type
        self.port = port
        self.__srv_sock = None
        self.__cli_sock = None
        self.__cli_addr = None

        assert(type == SOCKET_TCP_SERVER or type == SOCKET_TCP_CLIENT or
               type == SOCKET_UDP_SERVER or type == SOCKET_UDP_CLIENT)


    def __del__(self):
        self.close()


    def initial(self):
        '''
        initialize socket
        @return: True for success, False for failed
        '''
        try:
            if self.type == SOCKET_TCP_SERVER:
                self.__srv_sock = socket(AF_INET, SOCK_STREAM)
                self.__srv_sock.bind((self.ip, self.port))
                self.__srv_sock.listen(SOMAXCONN)
            elif self.type == SOCKET_TCP_CLIENT:
                self.__cli_sock = socket(AF_INET, SOCK_STREAM)
                self.__cli_sock.connect((self.ip, self.port))
            elif self.type == SOCKET_UDP_SERVER:
                self.__cli_sock = socket(AF_INET, SOCK_DGRAM)
                self.__cli_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                self.__cli_sock.bind((self.ip, self.port))
            elif self.type == SOCKET_UDP_CLIENT:
                self.__cli_addr = (self.ip, self.port)
                self.__cli_sock = socket(AF_INET, SOCK_DGRAM)
            return True
        except:
            DBG_ERR('socket initialize FAILED.')
            return False


    def accept(self):
        '''
        tcp socket accept
        @return: True for success, False for failed
        '''
        if self.type != SOCKET_TCP_SERVER:
            DBG_WRN('socket accept FAILED')
            return False
        try:
            self.__srv_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.__cli_sock, self.__cli_addr = self.__srv_sock.accept()
            return True
        except:
            DBG_WRN('socket accept FAILED')
            return False


    def client_addr(self):
        '''
        get client ip address
        @return: client ip address
        '''
        return self.__cli_addr


    def send(self, buf):
        '''
        send data
        @param buf: data buffer
        @return: True for success, False for failed
        '''
        try:
            if (self.type == SOCKET_TCP_SERVER or
                self.type == SOCKET_TCP_CLIENT):
                self.__cli_sock.send(buf)
            elif (self.type == SOCKET_UDP_SERVER or
                  self.type == SOCKET_UDP_CLIENT):
                self.__cli_sock.sendto(buf, self.__cli_addr)
            return True
        except:
            return False


    def recv(self, length):
        '''
        receive data
        @param length: receive data length
        @return: data buffer for success,
                 None for failed
        '''
        buf = ''
        while (len(buf) < length):
            try:
                if (self.type == SOCKET_TCP_SERVER or
                    self.type == SOCKET_TCP_CLIENT):
                    rcv = self.__cli_sock.recv(length - len(buf))
                    if rcv != None and len(rcv) == 0:
                        return None  # close socket
                    buf += rcv
                elif (self.type == SOCKET_UDP_SERVER or
                      self.type == SOCKET_UDP_CLIENT):
                    buf += self.__cli_sock.recvfrom(length - len(buf))
            except socket_module.timeout:
                return buf
            except:
                return None
        return buf


    def close(self, which = 0):
        ''' 
        close socket
        @param which: which socket to close
                      0 for all (default)
                      SOCKET_TCP_SERVER or SOCKET_UDP_SERVER for __srv_sock
                      SOCKET_TCP_CLIENT or SOCKET_UDP_CLIENT fir __cli_sock
        '''
        if which == 0 or which == SOCKET_TCP_SERVER or which == SOCKET_UDP_SERVER:
            if self.__srv_sock:
                self.__srv_sock.close()
                self.__srv_sock = None
        if which == 0 or which == SOCKET_TCP_CLIENT or which == SOCKET_UDP_CLIENT:
            if self.__cli_sock:
                self.__cli_sock.close()
                self.__cli_sock = None


    def time_out(self, sec):
        '''
        set socket timeout
        @param sec: timeout in second
        '''
        self.__cli_sock.settimeout(sec)

    def has_pending_data(self):
        '''
        gets if data is available to be read
        '''
        rlist=[self.__cli_sock]
        read_sockets, write_sockets, error_sockets = select.select(rlist, [], [], 0)
        if read_sockets:
            if self.__cli_sock in read_sockets:
                return True
        return False