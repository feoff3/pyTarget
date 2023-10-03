#    
#    initiator session implementation code
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-11-3)
#

from iscsi.iscsi_lib import SESSION_MCS, SessionID
from iscsi.iscsi_negotiate import new_key
from intr.connect import Connect
from intr.cache import IntrCache
from comm.debug import *


class Session():
    '''
    Initiator session class
    '''
    def __init__(self, initiator, type):
        '''
        @param initiator: which initiator current session belong to
        @param type: session type
        '''
        # initiator/sid/leading
        self.sid = SessionID()
        self.type = type
        self.initiator = initiator
        self.leading = None
        self.cid_nr = 0

        # Sequence number for session
        self.CmdSN = 1
        self.__cmdsn_lock = threading.Lock()

        # Initiator task tag
        self.ITT = 1        
        self.itt_lock = threading.Lock()

        # connection list
        self.conn_list = []
        self.conn_list_lock = threading.Lock()

        # scsi/iscsi task list
        self.scsi_list = IntrCache()
        self.iscsi_list = IntrCache()

        #
        # some parameter for session negotiation
        # update automatically in negotiation
        #
        self.MaxConnections = new_key('MaxConnections');
        self.InitialR2T = new_key('InitialR2T');
        self.ImmediateData = new_key('ImmediateData');
        self.FirstBurstLength = new_key('FirstBurstLength');
        self.MaxBurstLength = new_key('MaxBurstLength');
        self.DefaultTime2Wait = new_key('DefaultTime2Wait');
        self.DefaultTime2Retain = new_key('DefaultTime2Retain');
        self.MaxOutstandingR2T = new_key('MaxOutstandingR2T');
        self.DataPDUInOrder = new_key('DataPDUInOrder');
        self.DataSequenceInOrder = new_key('DataSequenceInOrder');
        self.ErrorRecoveryLevel = new_key('ErrorRecoveryLevel');        

        DBG_PRN('create a new session(%s)' % str(self.sid))

    def __str__(self):
        return str(self.sid)


    def next_cmdsn(self):
        '''
        Get a new cmd_sn
        '''
        self.__cmdsn_lock.acquire()
        ret = self.CmdSN
        self.CmdSN += 1
        self.__cmdsn_lock.release()
        return ret
        
        
    def next_itt(self):
        '''
        Get a new initiator task tag
        '''
        self.itt_lock.acquire()
        ret = self.ITT
        self.ITT += 1
        self.itt_lock.release()
        return ret
    
    
    def next_cid(self):
        '''
        Get a new connect id
        '''
        self.cid_nr += 1
        return self.cid_nr


    def add_conn(self, ip, port):
        '''
        Add connect and start to run...
        @param ip: connect ip address
        @param port: connect port
        @return: connect for success, None for failed
        '''
        if len(self.conn_list) >= self.MaxConnections.value:
            DBG_WRN('add connection too much in session %s.' % str(self))
            return None

        # connect type
        type = self.type
        if self.leading:
            type = SESSION_MCS

        # create new connect and add into list
        connect = Connect(self.initiator, self, type, self.next_cid(), ip, port)
        self.conn_list_lock.acquire()
        self.conn_list.append(connect)
        if self.leading == None:
            self.leading = connect
        self.conn_list_lock.release()
        if  connect.start() == False:
            connect.stop()
            connect = None
        DBG_PRN('session %s add connect %s.' % (str(self), str(connect)), connect != None)
        return connect
    
 
    def find_conn(self, cid):
        '''
        Get connect
        @param cid: connect id
        @return: certain connect pointer for success, None for failed
        '''
        conn = None
        self.conn_list_lock.acquire()
        for item in self.conn_list:
            if item.cid == cid:
                conn = item
                break
        self.conn_list_lock.release()
        return conn

    
    def del_conn(self, cid):
        '''
        Delete connect
        @param cid: connect id
        @return: True for success, Failed for failed
        @Note: final connect will remove session.
        '''
        ret = False
        conn = self.find_conn(cid)
        if conn:
            ret = conn.stop()
        DBG_PRN('Remove connect(%d) from session(%s)' % (cid, str(self)), ret)
        return ret


    def stop(self):
        '''
        stop current session
        '''
        ret = False
        for item in self.conn_list:
            item.stop()
        if len(self.conn_list) == 0:
            ret = True
        DBG_PRN('stop session %s' % str(self.sid), ret)
        return ret
