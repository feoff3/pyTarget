#    
#    iscsi session implementation code.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#
import copy, threading
import tagt.cache as cah
from iscsi.iscsi_negotiate import new_key
from comm.debug import DBG_WRN, DBG_PRN


class Session():
    '''
    Class Iscsi session
    '''

    def __init__(self, sid):
        '''
        Session constructor
        @param sid: session id
        '''

        #
        # Session attribute
        # target/host/leading etc...
        #
        self.target = None
        self.host = None
        self.leading = None
        self.sid = copy.deepcopy(sid)

        #
        # some parameter for session negotiation
        # update automatically in negotiation
        #
        self.InitiatorAlias         = new_key('InitiatorAlias')
        self.MaxConnections         = new_key('MaxConnections')
        self.MaxBurstLength         = new_key('MaxBurstLength')
        self.FirstBurstLength       = new_key('FirstBurstLength')
        self.DefaultTime2Wait       = new_key('DefaultTime2Wait')
        self.DefaultTime2Retain     = new_key('DefaultTime2Retain')
        self.MaxOutstandingR2T      = new_key('MaxOutstandingR2T')
        self.ErrorRecoveryLevel     = new_key('ErrorRecoveryLevel')
        self.InitialR2T             = new_key('InitialR2T')
        self.ImmediateData          = new_key('ImmediateData')
        self.DataPDUInOrder         = new_key('DataPDUInOrder')
        self.DataSequenceInOrder    = new_key('DataSequenceInOrder')
        self.TaskReporting          = new_key('TaskReporting')

        #
        # Sequence number for session
        #
        self.ExpCmdSn = 0
        self.exp_cmd_lock = threading.Lock()
        self.MaxCmdSn = 30
        self.TTT = 0
        self.ttt_lock = threading.Lock()

        #
        # connection list
        #
        self.conn_list = []
        self.conn_list_lock = threading.Lock()

        #
        # iscsi / scsi command list
        #
        self.scsi_cmd_list = cah.TagtCache()
        self.iscsi_cmd_list = cah.TagtCache()

        DBG_PRN('create session %s.' % str(sid))

    
    def __del__(self):
        '''
        session destroy
        '''
        DBG_PRN('destroy session %s.' % str(self.sid))


    def next_ttt(self):
        '''
        Get a new Target task tag.
        '''
        self.ttt_lock.acquire()
        self.TTT += 1
        if self.TTT == 0xFFFFFFFF:
            self.TTT = 1
        result = self.TTT
        self.ttt_lock.release()
        return result

        
    def next_exp_cmdsn(self):
        '''
        Get a new ExpCmdSn
        '''
        self.exp_cmd_lock.acquire()
        self.ExpCmdSn += 1
        if self.ExpCmdSn == 0x100000000:
            self.ExpCmdSn = 0
        self.exp_cmd_lock.release()
        return self.ExpCmdSn

        
    def cmd_wnd_size(self):
        '''
        Current command windows size
        '''
        return self.MaxCmdSn - len(self.scsi_cmd_list.list)

    def add_conn(self, conn, isLeading):
        '''
        Add connect
        @param conn: connect
        @param isLeading: is leading connect
        @return: True for success, False for failed
        '''
        result = True
        if self.find_conn(conn.cid):
            result = False
            DBG_WRN('session %s add connect %d FAILED.' % (str(self.sid), conn.cid))
        else:
            self.conn_list_lock.acquire()
            self.conn_list.append(conn)
            if isLeading:
                self.leading = conn
            self.conn_list_lock.release()
            DBG_PRN('session %s add connect %d.' % (str(self.sid), conn.cid))
        return result


    def del_conn(self, cid):
        '''
        Delete connect
        @param cid: connect id
        @return: True for success, Failed for failed
        '''
        result = False
        connect = self.find_conn(cid)
        if connect != None:
            self.conn_list_lock.acquire()
            self.conn_list.remove(connect)
            self.conn_list_lock.release()
            result = True
            DBG_PRN('session %s add connect %d.' % (str(self.sid), cid))
        return result


    def find_conn(self, cid):
        '''
        Find connect
        @param cid: connect id
        @return: specific connect for success, None for failed
        '''
        conn = None
        self.conn_list_lock.acquire()
        for i in self.conn_list:
            if i.cid == cid:
                conn = i
                break
        self.conn_list_lock.release()
        return conn
