#    
#    Host class for management initiator user.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#
import threading
from comm.debug import DBG_PRN, DBG_WRN

class Host():
    '''
    Class host
    '''

    def __init__(self, name, target_pwd = '', initiator_pwd = ''):
        '''
        Host constructor
        @param name: Initiator name
        @param target_pwd: target chap secret
        @param initiator_pwd: initiator chap secret
        @note: if initiator password or target password are are not NULL, 
            security negotiation must be done while login phase.
        '''
        self.name = name                     # initiator name for login
        self.target_pwd = target_pwd         # target chap password
        self.initiator_pwd = initiator_pwd   # initiator chap password
        self.session_list = []
        self.session_list_lock = threading.Lock()
        self.lun_list = []
        self.lun_list_lock = threading.Lock()
        DBG_PRN('create host %s' % name)
        

    def __del__(self):
        '''
        host destroy
        '''
        DBG_PRN('destroy host %s' % self.name)


    def add_lun(self, lun):
        '''
        Add a lun into host
        @param lun: lun device
        @warning: here do not need deepcopy
        @return: True for success, False for failed
        '''
        result = True
        if self.find_lun(lun.id) != None:
            DBG_WRN('host %s add lun %d FAILED.' % (self.nam, lun.id))
            result = False
        else:
            self.lun_list_lock.acquire()
            self.lun_list.append(lun)
            self.lun_list_lock.release()
            DBG_PRN('host %s add lun %d.' % (self.name, lun.id))
        return result


    def del_lun(self, id):
        '''
        Delete lun from host
        @param id: lun id
        @return: True for success, False for failed
        '''
        result = False
        lun = self.find_lun(id)
        if lun != None:
            self.lun_list_lock.acquire()
            self.lun_list.remove(lun)
            self.lun_list_lock.release()
            result = True
            DBG_PRN('host %s remove lun %d.' % (self.nam, id))
        return result


    def find_lun(self, id):
        '''
        Get lun
        @param id: lun id
        @return: specific lun for success, None for failed
        '''
        lun = None
        self.lun_list_lock.acquire()
        for item in self.lun_list:
            if id == item.id:
                lun = item
                break
        self.lun_list_lock.release()
        return lun


    def add_session(self, session):
        '''
        Add session
        @param sess: session
        @return: True for success, False for failed
        '''
        result = True
        if self.find_session(session.sid):
            result = False
            DBG_WRN('host %s add session %s FAILED.' % (self.name, str(session.sid)))
        else:
            self.session_list_lock.acquire()
            self.session_list.append(session)
            self.session_list_lock.release()
            DBG_PRN('host %s add session %s.' % (self.name, str(session.sid)))
        return result


    def del_session(self, sid):
        '''
        Delete session
        @param sid: session id
        @return: True for success, False for failed
        '''
        result = False
        session = self.find_session(sid)
        if session != None:
            self.session_list_lock.acquire()
            self.session_list.remove(session)
            self.session_list_lock.release()
            result = True       
            DBG_PRN('host %s remove session %s.' % (self.name, str(sid)))
        return result


    def find_session(self, sid):
        '''
        Get session
        @param sid: session id
        @return: specific session for success, None for failed
        '''
        result = None
        self.session_list_lock.acquire()
        for session in self.session_list:
            if str(session.sid) == str(sid):
                result = session
                break
        self.session_list_lock.release()
        return result


    def update_event(self, event, key, asc, info=0):
        '''
        Notice initiator/session/connect to update device list.
        '''
        self.session_list_lock.acquire()
        for sess in self.session_list:
            sess.conn_list_lock.acquire()
            for item in sess.conn_list:
                item.async_event(event, key, asc, info)
            sess.conn_list_lock.release()
        self.session_list_lock.release()
