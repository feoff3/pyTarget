#    
#    Initiator implementation code
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-11-3)
#

from iscsi.iscsi_lib import *
from intr.session import Session
from comm.comm_sock import CommSock, SOCKET_TCP_CLIENT
from comm.debug import *

class Initiator():
    '''
    Class initiator
    '''

    def __init__(self, name, tg_pwd=None, itr_pwd=None):
        '''
        Initiator constructiator
        @param name: initiator qualify name(iqn)
        @param tg_pwd: secret for target chap
        @param itr_pwd: secret for initiator chap
        @note: both tg_pwd and itr_pwd are None for None chap
        '''

        # initiator attribute
        self.name = name
        self.target_pwd = tg_pwd
        self.initiator_pwd = itr_pwd

        # target name/address
        self.target_name = ''
        self.target_addr = []   # support multi-address
        
        # session list
        self.session_list = []
        self.session_list_lock = threading.Lock()

        # device list
        self.device_list = []
        self.device_list_lock = threading.Lock()

        DBG_PRN('create a new initiator %s' % self.name)

    def __del__(self):
        self.session_list_lock.acquire()
        for session in self.session_list:
            session.stop()
        self.session_list_lock.release()
        DBG_PRN('stop initiator ', str(self))

    def __str__(self):
        return self.name

    def __detect_ip(self, ip, port): 
        '''
        assert ip address availability.
        @param ip: ip address
        @param port: tcp port
        @return: True for success, False for failed
        '''
        ret = False
        sock = CommSock(SOCKET_TCP_CLIENT, ip, port)
        if sock.initial():
            sock.close()
            ret = True
        return ret


    def add_session(self, type):
        '''
        Add session
        @param type: session type
        @return: session pointer for success, None for failed
        '''
        if (type != SESSION_DISCOVERY and
            type != SESSION_NORMAL):
            DBG_WRN('add session FAILED(unknown session type)')
            return None

        session = Session(self, type)
        self.session_list_lock.acquire()
        self.session_list.append(session)
        self.session_list_lock.release()
        DBG_PRN('initiator %s add session %s ' % (str(self), str(session)))
        return session


    def find_session(self, sid):
        '''
        Get session
        @param sid: session id
        @return: certain session pointer for success, None for failed
        '''
        ret = None
        self.session_list_lock.acquire()
        for item in self.session_list:
            if str(item.sid) == str(sid):
                ret = item
                break
        self.session_list_lock.release()
        return ret


    def del_session(self, sid):
        '''
        Delete session
        @param sid: session id
        @return: True for success, False for failed
        '''
        ret = False
        sess = self.find_session(sid)
        if sess:
            ret = sess.stop()
        DBG_PRN('Remove session(%s) from initiator(%s)' % (str(sid), str(self)), ret)
        return ret


    def discovery(self, ip, port):
        '''
        Discovery & update target name/address fields
        @param ip: discovery target ip
        @param port: discovery target port
        @return: True for success, False for failed
        '''
        result = False
        session = self.add_session(SESSION_DISCOVERY);
        connect = session.add_conn(ip, port)
        if connect:
            result = connect.discovery()
            connect.Logout(0)
            connect.stop()
        session.stop()
        DBG_PRN('Discovery target(initiator:%s ip:%s,port:%d)' % (str(self), ip, port), result)
        return result

