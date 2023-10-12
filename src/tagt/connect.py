#    
#    iscsi target connection implementation code.
#    
#    Modify history:    
#    -----------------------------------------------------------------   
#
#    Create by Wu.Qing-xiu (2009-09-27)
#

import copy
import tagt.cache as ch
from iscsi.iscsi_lib import *
from scsi import scsi_lib as s_lib


class Connect():
    '''
    class iscsi connect 
    '''

    def __init__(self, sock):
        '''
        Connect constructor
        @param sock: connection socket
        '''
        # attribute
        self.cid = 0
        self.state = None                   # connection State
        self.type  = None                   # connection type
        self.isLeading = False              # is leading connection    
        self.Digest = DIGEST_NONE           # Header/Data digest
        self.target = None                  # target connect belong to
        self.host = None                    # host connect belong to 
        self.session = None                 # session connect belong to
        self.sock = copy.copy(sock)         # connect socket

        # for chap
        self.chap_alg = 0                   # chap algorithm   
        self.chap_value = None              # chap value
        self.tagt_challenge = ''            # target challenge message
        self.intr_challenge = ''            # initiator challenge message
        self.chap_state = 0                 # chap state

        # sequence number
        self.StatSN = 0                     # connect stat_sn
        self.CurTTT = 0                     # current task itt
        self.CurExpCmdSn = 0                # current task cmd_sn

        # for nopin
        self.enable_nopin = False           # enable target nopin
        self.nopin_interval = 10            # nopin interval
        
        # for error recover
        self.pdu_list = ch.TagtCache()       # pdu backup list

        # for negotiation
        self.SessionType                    = new_key('SessionType')
        self.AuthMethod                     = new_key('AuthMethod')
        self.TargetPortalGroupTag           = new_key('TargetPortalGroupTag')
        self.HeaderDigest                   = new_key('HeaderDigest')
        self.DataDigest                     = new_key('DataDigest')
        self.MaxRecvDataSegmentLength       = new_key('MaxRecvDataSegmentLength')
        self.PerMaxRecvDataSegmentLength    = new_key('MaxRecvDataSegmentLength')
        self.TargetName                     = new_key('TargetName')
        self.InitiatorName                  = new_key('InitiatorName')
        self.OFMarker                       = new_key('OFMarker')
        self.IFMarker                       = new_key('IFMarker')
        self.OFMarkInt                      = new_key('OFMarkInt')
        self.IFMarkInt                      = new_key('IFMarkInt')

        DBG_PRN('create connect')


    def __del__(self):
        '''
        connect destroy
        '''
        self.pdu_list.clear()
        DBG_PRN('destroy connect %d' % self.cid)


    def next_statsn(self):
        '''
        Get a new connection StatSN
        @return: new StatSN
        '''
        result = self.StatSN
        self.StatSN += 1
        if self.StatSN == 0x100000000:
            self.StatSN = 1
        return result

    
    def load_config(self):
        '''
        Load session/connect configuration
        '''
        #
        # Initialize session/connect negotiation parameters
        # all the parameters exist in target.config
        # config file path: tagt/config.xml
        #
        if self.target.config:
            sess = self.session
            conn = self.target.config
            if self.isLeading:
                sess.MaxConnections.value = conn.MaxConnections
                sess.InitialR2T.value = conn.InitialR2T
                sess.ImmediateData.value = conn.ImmediateData
                sess.FirstBurstLength.value = conn.FirstBurstLength
                sess.MaxBurstLength.value = conn.MaxBurstLength
                sess.DefaultTime2Wait.value = conn.DefaultTime2Wait
                sess.DefaultTime2Retain.value = conn.DefaultTime2Retain
                sess.MaxOutstandingR2T.value = conn.MaxOutstandingR2T
                sess.DataPDUInOrder.value = conn.DataPDUInOrder
                sess.DataSequenceInOrder.value = conn.DataSequenceInOrder
                if self.type == SESSION_NORMAL:
                    sess.ErrorRecoveryLevel.value = conn.ErrorRecoveryLevel
            self.MaxRecvDataSegmentLength.value = conn.MaxRecvDataSegmentLength


    def login_fail(self, req, err_class, err_detail, key_pair = {}):
        '''
        Process login failure.
        @param req: login request pdu
        @param err_class: error class
        @param err_detail: error detail
        @param key_pair: request pdu invalid key_value pair
        '''
        rsp = PDU()
        LoginRsp(self, req, rsp, err_class, err_detail)
        for item in key_pair:
            set_key_val(rsp, item, key_pair[item])
        self.sock.send(rsp, self.Digest)


    def login_handle(self):
        ''' 
        Process iSCSI login
        if is leading connection, create session and add to host.
        @return: True for success, False for failed
        '''
        from tagt.session import Session
        from tagt.main import TM

        self.type  = SESSION_ERROR
        self.state = ISCSI_INITIAL_LOGIN_STAGE
        err_class  = 0
        err_detail = 0

        DBG_INF("initiator %s:%d connect." %
                  (self.sock.client_addr()[0], self.sock.client_addr()[1]))

        # first request pdu must be a login request,
        # MaxRecvSegmentLength use default value.
        req = self.recv()
        if req == None or OPCODE(req) != ISCSI_OP_LOGIN:
            return False

        #==============================================================
        #                          PHASE 1
        #--------------------------------------------------------------
        #   Phase 1 check some fields of login request, such as 
        # TargetName, Initiator, CHAP etc (response login reject
        # if detect failed). And then create or find the specific
        # session within the host, add connect into session. 
        #==============================================================

        # session id & connect id
        sid = get_sid(req)
        self.cid = req.get_cid()

        # version_max & version_min
        if VER_MAX(req) or VER_MIN(req):
            self.login_fail(req,
                           ISCSI_STATUS_CLS_INITIATOR_ERR, 
                           ISCSI_LOGIN_STATUS_NO_VERSION)
            DBG_WRN('iscsi version(max=%d, min=%d) is INVAILD.' %
                    (VER_MAX(req), VER_MIN(req)))
            return False

        # get SessionType, default is Normal
        key = self.SessionType.check(req)
        if key == None or key == 'Normal':
            if sid.tsih:
                self.type = SESSION_MCS
                self.isLeading = False
            else:
                self.type = SESSION_NORMAL
                self.isLeading = True
        elif key == 'Discovery':
            self.type = SESSION_DISCOVERY
            self.isLeading = True
        else:
            self.login_fail(req,
                           ISCSI_STATUS_CLS_INITIATOR_ERR,
                           ISCSI_LOGIN_STATUS_NO_SESSION_TYPE,
                           {'SessionType':key})
            DBG_WRN('SessionType %s is INVAILD.' % key)
            return False
        DBG_NEG('SessionType =', key)

        #
        # TargetName
        #
        if self.type == SESSION_DISCOVERY:
            key = self.InitiatorName.check(req)
            TM.lock()
            for target in TM.target_list:
                if target.find_host(key):
                    self.target = target
                    break
            if self.target is None:
                self.target = TM.target_list[0]
                #err_class  = ISCSI_STATUS_CLS_INITIATOR_ERR
                #err_detail = ISCSI_LOGIN_STATUS_INIT_ERR
            TM.unlock()
        else:
            key = self.TargetName.check(req)
            self.target = TM.find_target(key)
            if self.target is None:
                err_class  = ISCSI_STATUS_CLS_INITIATOR_ERR
                err_detail = ISCSI_LOGIN_STATUS_MISSING_FIELDS
        if err_class or err_detail:
            self.login_fail(req, err_class, err_detail)
            DBG_WRN('initiator name or target name is INVAILD', key , err_class, err_detail)
            return False
        DBG_NEG('TargetName = %s' %self.target.name)

        #
        # InitiatorName
        #
        key = self.InitiatorName.check(req)
        self.host = self.target.find_host(key)
        if self.host is None:
            self.login_fail(req,
                           ISCSI_STATUS_CLS_INITIATOR_ERR,
                           ISCSI_LOGIN_STATUS_AUTH_FAILED,
                           {'InitiatorName':key})
            DBG_WRN('InitiatorName %s do not exist.', key)
            return False
        DBG_NEG('InitiatorName = %s' % key)

        #
        # find or create a session
        #
        if self.type == SESSION_MCS:
            self.session = self.host.find_session(sid)
            if self.session is None:
                err_class  = ISCSI_STATUS_CLS_INITIATOR_ERR
                err_detail = ISCSI_LOGIN_STATUS_NO_SESSION
                DBG_WRN('session %s do not exist.' % (str(sid)))
            elif self.session.MaxConnections.value <= len(self.session.conn_list):
                err_class  = ISCSI_STATUS_CLS_INITIATOR_ERR
                err_detail = ISCSI_LOGIN_STATUS_CONN_ADD_FAILED
                DBG_WRN('connect is too much in session %s.' % str(sid))
        else:
            sid.tsih = self.target.next_tsih()
            self.session = Session(sid)
            if self.host.add_session(self.session) == False:
                err_class  = ISCSI_STATUS_CLS_TARGET_ERR
                err_detail = ISCSI_LOGIN_STATUS_TARGET_ERROR
        if err_class or err_detail:
            self.login_fail(req, err_class, err_detail)
            return False
        DBG_INF('SessionID: %s' % str(sid))


        # Add connect
        if self.session.add_conn(self, self.isLeading) == False:
            self.login_fail(req,
                           ISCSI_STATUS_CLS_INITIATOR_ERR,
                           ISCSI_LOGIN_STATUS_CONN_ADD_FAILED)
            return False
        DBG_INF('ConnectID: %d' % self.cid)

        # Initial sequel number
        self.StatSN = 0
        if self.isLeading:
            self.session.ExpCmdSn = req.get_cmdsn()
            self.CurExpCmdSn = self.session.ExpCmdSn
        else:
            self.CurExpCmdSn = self.session.ExpCmdSn

        self.load_config()

        # check if target need chap 
        if self.host.target_pwd:
            self.AuthMethod.value = True
            self.chap_state = CHAP_STATE_CHAP
        else:
            self.AuthMethod.value = False    

        #
        # AuthMethod
        #
        key = self.AuthMethod.check(req)
        current_stage = FLAGS_CSG(req.bhs[1])
        if key == None:
            key = 'None'
        
        if current_stage == ISCSI_SECURITY_STAGE:
            if (key == 'CHAP' and self.AuthMethod.value == False or
                key == 'None' and self.AuthMethod.value):
                self.login_fail(req,
                               ISCSI_STATUS_CLS_INITIATOR_ERR,
                               ISCSI_LOGIN_STATUS_AUTH_FAILED,
                               {'AuthMethod':'Reject'})
                return False
            self.state = ISCSI_SECURITY_STAGE
        elif current_stage == ISCSI_OPTIONAL_STAGE:
            self.state = ISCSI_OPTIONAL_STAGE


        #==============================================================
        #                          PHASE 2
        #--------------------------------------------------------------
        #   Phase 2 start to process login phase, do security negotiation
        # and optional negotiation. 
        #==============================================================

        while (self.state == ISCSI_SECURITY_STAGE or
               self.state == ISCSI_OPTIONAL_STAGE):

            rsp = PDU()
            LoginRsp(self, req, rsp, 0, 0)

            if (self.sock.send(rsp, self.Digest) == False or
                self.state == ISCSI_ERROR_PHASE):
                return False

            if rsp.bhs[1] & ISCSI_FLAG_LOGIN_TRANSIT:
                self.state = self.state << 1 | 0x01

            if self.state == ISCSI_FULL_FEATURE_PHASE:
                DBG_PRN('connect %d login finish' % self.cid)
                break;

            req = self.recv()
            if req.state != PDU_STATE_GOOD:
                DBG_WRN('connect%d login FAILED' % self.cid)
                return False

        return True

    def login_finish(self):
        '''
        finish login, and fix some not negotiate key,
        maybe use protocol default value. 
        '''
        sess = self.session

        self.HeaderDigest.final_nego()
        self.DataDigest.final_nego()

        if self.HeaderDigest.value == 'CRC32C':
            self.Digest |= DIGEST_HEAD
        if self.DataDigest.value == 'CRC32C':
            self.Digest |= DIGEST_DATA

        # leading connection negotiation only
        if self.isLeading:
            sess.ErrorRecoveryLevel.final_nego()
            sess.DefaultTime2Retain.final_nego()
            sess.DefaultTime2Wait.final_nego()

            if self.type != SESSION_DISCOVERY:
                sess.MaxConnections.final_nego()
                sess.InitialR2T.final_nego()
                sess.ImmediateData.final_nego()
                sess.DataPDUInOrder.final_nego()
                sess.DataSequenceInOrder.final_nego()
                sess.MaxOutstandingR2T.final_nego()
        self.PerMaxRecvDataSegmentLength.final_nego(sess.MaxBurstLength.value)


    def Ping(self):
        '''
        Ping initiator
        @return: True for initiator still active
                 False for initiator inactive
        '''
        DBG_CMD('NopIn')

        pdu = PDU()
        NopIn(self, None, pdu)
        if (not self.send(pdu) or
            not self.recv()):
            DBG_WRN('Connect%d in %s is inactive' % (self.cid, self.host.name))
            return False
        return True


    def Start(self):
        '''
        Start to run this connect. 
        '''
        if self.login_handle():
            self.login_finish()
            #import cProfile
            #import pstats
            #cProfile.runctx("self.Task()" , globals() , locals(), "my_func_stats")
            #p = pstats.Stats("my_func_stats")
            #p.sort_stats("cumulative").print_callers()
            self.Task()
        self.Stop()


    def Task(self):
        '''
        Run under full feature phase, and handle 
        all kinds of task.
        '''

        # allow target to send NopIn if necessary
        if self.enable_nopin:
            self.sock.time_out(self.nopin_interval)

        while self.state == ISCSI_FULL_FEATURE_PHASE:

            # remember to check connection state,
            # current connect may be closed by other connect.
            req = None
            self.session.scsi_cmd_list.process_async_read_requests(wait=False)
            if not self.sock.has_pending_data():
                # we are going to block on recv so instead of waiting for recv, wait on disks
                self.session.scsi_cmd_list.process_async_read_requests(wait=True)
            try:
                req = self.recv()
            except:
                DBG_EXC()
            
            if self.state == ISCSI_LOGOUT_PHASE:
                return
            
            if not req:
                 DBG_WRN("Crticial problem within the session, aborting...")
                 break
            # check and do error recover if necessary.
            # (current support error recovery level = 2)
            if req.state != PDU_STATE_GOOD:
                if req.state == PDU_STATE_SOCK_TIMEOUT:
                    continue
                DBG_WRN("Problem within the session, recovering...")
                if iscsi_do_recovery(self, req):
                    continue
                else:
                    break
            
            # normal task request, clear acknowledged pdu. 
            self.ack_pdu(req)

            rsp = PDU()
            code = OPCODE(req)
            DBG_CMD(ISCSI_DESC(code))
            ret = ISCSI_CMD_NEED_RSP

            # discovery session only just allow few opcodes
            if (self.type == SESSION_DISCOVERY and
                code != ISCSI_OP_TEXT and
                code != ISCSI_OP_LOGOUT):
                Reject(self, req, rsp, REJECT_PROTOCOL_ERROR)
            elif code == ISCSI_OP_TEXT:
                ret = TextRsp(self, req, rsp)
            elif code == ISCSI_OP_SCSI_CMD:
                ret = ScsiCmdRsp(self, req, rsp)
            elif code == ISCSI_OP_SCSI_TMFUNC:
                ret = TaskManageRsp(self, req, rsp)
            elif code == ISCSI_OP_LOGIN:
                Reject(self, req, rsp, REJECT_LONG_OPERATION_REJECT)
            elif code == ISCSI_OP_SCSI_DATA_OUT:
                ret = DataOutRsp(self, req, rsp)
            elif code == ISCSI_OP_LOGOUT:
                LogoutRsp(self, req, rsp)
            elif code == ISCSI_OP_SNACK:
                ret = SnackRsp(self, req, rsp)
            elif code == ISCSI_OP_NOOP_OUT:
                ret = NopIn(self, req, rsp)
            elif (code == ISCSI_OP_VENDOR1_CMD or
                  code == ISCSI_OP_VENDOR2_CMD or
                  code == ISCSI_OP_VENDOR3_CMD or
                  code == ISCSI_OP_VENDOR4_CMD):
                Reject(self, req, rsp, REJECT_COMMAND_NOT_SUPPORTED)
            else:
                Reject(self, req, rsp, REJECT_COMMAND_NOT_SUPPORTED, True)

            if ret == ISCSI_CMD_NEED_RSP:
                self.send(rsp)


    def ack_pdu(self, req):
        '''
        receive initiator StatSN acknowledge,
        and clear unused pdu.   
        '''
        lst = self.pdu_list
        lst.lock()
        for item in lst.list:
            if (item.get_statsn() < req.get_exp_statsn()):
                lst.list.remove(item)
        lst.unlock()

    def clear_task(self):
        '''
        connection will be logout, clear all the tasks, 
        which belong to it.
        '''
        lst = self.session.scsi_cmd_list
        lst.lock()
        for item in lst.list:
            if item.connect == self:
                item.state = ch.SCSI_TASK_FREE
                lst.list.remove(item)
                DBG_PRN('clear task %d before connect logout' % item.id)
        lst.unlock()

    def Stop(self):
        '''
        Stop and remove connect from session,
        if the session is empty, remove it.
        '''
        # connect has been killed
        if self.state == ISCSI_CONNECT_STOP:
            return

        # target stop, notice initiator that target will logout.
        if self.state == ISCSI_TARGET_STOP:
            self.async_event(ASYNC_EVENT_TARGET_CLOSE_CURRENT_CONNECTION, None, None, None)
        if self.sock:
            self.sock.close()
            self.sock = None

        # remove connect from session
        if self.session:
            self.session.del_conn(self.cid)
            if len(self.session.conn_list) == 0:
                self.host.del_session(self.session.sid)
            self.session = None
        self.state = ISCSI_CONNECT_STOP
        DBG_PRN('connect %d finish.' % self.cid)


    def async_event(self, event, key, asc, info=0x00):
        '''
        Asyn notice initiator to update device list.
        (send asynchronous event to initiator)
        '''
        req = PDU()
        AsynchronousEvent(self, req, event)
        if event == ASYNC_EVENT_SENSE_DATA: 
            req.data = s_lib.new_sense(key, asc, info)
            req.set_data_len(len(req.data))
        self.send(req)


    def send(self, pdu):
        '''
        Backup pdu and send to initiator.
        '''
        #
        # for save memory space,
        # do not backup data-in pdu with (F_bit), when error recover, 
        # re-enclosure these pdus.
        #
        if not (OPCODE(pdu) == ISCSI_OP_SCSI_DATA_IN and pdu.bhs[1] & 0x80):
            self.pdu_list.push_pdu(pdu)
        return self.sock.send(pdu, self.Digest)


    def recv(self):
        '''
        Connect receive pdu.
        '''
        return self.sock.recv(self.Digest, MRDSL_VAL(self))
