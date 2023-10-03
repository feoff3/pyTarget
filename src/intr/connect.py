#    
#    Initiator iscsi connection implementation code.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-11-3)
#

from scsi.scsi_lib import *
from iscsi.iscsi_lib import *
from iscsi.iscsi_sock import IscsiSock, ISCSI_CLIENT_TYPE
#from iscsi.iscsi_negotiate import new_key

class Connect():
    '''
    class for initiator iscsi connect.
    '''
    def __init__(self, intr, sess, type, cid, ip, port):
        '''
        Connect constructor
        @param intr: initiator which connect belong to
        @param sess: session which connect belong to
        @param type: connect type
        @param cid: connect id
        @param ip: target ip just only for discovery
        @param port: target port just only for discovery
        '''
        # socket
        self.sock = None
        self.ip   = ip
        self.port = port

        # connect attribute
        self.initiator  = intr
        self.session = sess
        self.type = type
        self.cid = cid
        self.state = None
        self.chap_state = 0

        # sequence number
        self.ExpStatSN = -1
        self.CurCmdSN = 0
        self.CurITT = 0

        # leading connection
        self.isLeading = (type != SESSION_MCS)

        # negotiation parameters for connect
        self.Digest = DIGEST_NONE
        self.MaxRecvDataSegmentLength = new_key('MaxRecvDataSegmentLength')
        self.PerMaxRecvDataLength = new_key('MaxRecvDataSegmentLength')

        # negotiate parameters for session
        self.__key_list = {self.PerMaxRecvDataLength: atoi,
                           sess.MaxConnections      : atoi,
                           sess.InitialR2T          : str_2_bool,
                           sess.ImmediateData       : str_2_bool,
                           sess.FirstBurstLength    : atoi,
                           sess.MaxBurstLength      : atoi,
                           sess.DefaultTime2Wait    : atoi,
                           sess.DefaultTime2Retain  : atoi,
                           sess.MaxOutstandingR2T   : atoi,
                           sess.DataPDUInOrder      : str_2_bool,
                           sess.DataSequenceInOrder : str_2_bool,
                           sess.ErrorRecoveryLevel  : atoi}

    def __str__(self):
        return '%d' % self.cid
    

    def next_statsn(self):
        '''
        Get a new StatSN
        '''
        self.ExpStatSN += 1
        return self.ExpStatSN


    def Login(self):
        '''
        Connect login to target
        @return: True for success, False for failed
        @note: refer to connect.type (discovery, normal, etc)
        '''
        assert(self.session and self.initiator and self.sock)
        sess = self.session
        ret = False
        req = None
        rsp = None

        self.state = ISCSI_SECURITY_STAGE
        self.CurCmdSN = self.session.CmdSN
        self.CurITT = self.session.next_itt()

        while (self.state == ISCSI_SECURITY_STAGE or
               self.state == ISCSI_OPTIONAL_STAGE):
#===============================================================================
            req = PDU()
            LoginReq(self, req, rsp)
            rsp = self.exchange(req)
            if rsp == None:
                break
            # check error_class & error_detail
            if ERR_CLS(rsp) or ERR_DTL(rsp):
                DBG_WRN('Login response FAILED(class=0x%x, detail=0x%x)' % (ERR_CLS(rsp), ERR_DTL(rsp)))
                break
            # check phase transit flags
            if rsp.bhs[1] & ISCSI_FLAG_LOGIN_TRANSIT:
                self.state = self.state << 1 | 0x01
            # login finish
            if self.state == ISCSI_FULL_FEATURE_PHASE:
                # update tsih
                if self.type != SESSION_MCS:
                    sess.sid.tsih = rsp.get_tsih()
                for item in self.__key_list:
                    key = item.check(rsp)
                    if key and key != 'Reject':
                        item.value = self.__key_list[item](key)
                        DBG_NEG(item.name, '=', key)
                ret = True
                break
#===============================================================================
        result = "finish"
        if ret == False:
            result = "FAILED"
        DBG_PRN('connect login %s (iqn=%s, sid=%s, cid=%s)' % 
               (result, self.initiator.name, str(sess), str(self), ))
        return ret


    def Logout(self, reason):
        '''
        Connect logout from target
        @param reason: logout reason
        @return: True for success, False for failed
        '''
        DBG_PRN('connect%d: logout reason 0x%x' % (self.cid, reason))

        req = PDU()
        LogoutReq(self, req, reason)
        rsp = self.exchange(req)
        if rsp == None:
            return False

        # logout response failed
        if rsp.bhs[2]:
            DBG_PRN('Logout FAILED (reason = %x)' % int(rsp.bhs[2]))
            return False

        # clean up connect
        if reason == ISCSI_LOGOUT_REASON_CLOSE_SESSION:
            session = self.session
            session.conn_list_lock.acquire()
            for connect in session.conn_list:
                if connect.cid != self.cid:
                    connect.state = ISCSI_LOGOUT_PHASE
                    connect.stop()
            session.conn_list_lock.release()
            self.state = ISCSI_LOGOUT_PHASE
        elif reason == ISCSI_LOGOUT_REASON_CLOSE_CONNECTION:
            self.state = ISCSI_LOGOUT_PHASE
        elif reason == ISCSI_LOGOUT_REASON_CLOSE_RECOVERY:
            # TODO  
            pass
        else:
            # TODO
            pass

        return True


    def discovery(self):
        '''
        discovery target name within full feature phase
        @return: True for success, False for failed
        '''
        req = PDU()
        rsp = None
        
        # text request/response
        TextReq(self, req)
        rsp = self.exchange(req)
        if rsp == None or OPCODE(rsp) != ISCSI_OP_TEXT_RSP:
            return False

        # get target name
        key = get_key_val(rsp, 'TargetName')
        if key == None or key == 'Reject':
            return False
        self.initiator.target_name = key
        DBG_NEG('TargetName =', key)

        # get target address (TODO: handle multi-address)
        key = get_key_val(rsp, 'TargetAddress')
        if key == None or key == 'Reject':
            return False
        self.initiator.target_addr.append(key)
        DBG_NEG('TargetAddress =', key)

        return True


    def start(self):
        '''
        start to connect target and login.
        @return: True for success, False for failed.
        '''
        self.sock = IscsiSock(self.ip, self.port, ISCSI_CLIENT_TYPE)
        result = self.sock.initial() and self.Login()
        if result == False:
            self.state = ISCSI_ERROR_PHASE
#            DBG_WRN('connect(%s/%s) start FAILED (%s)' % (self.initiator, self))
        return result


    def stop(self):
        '''
        Stop and remove connect from session,
        if the session is empty, remove it also.
        '''

        # close socket
        if self.sock:
            self.sock.close(True)
            self.sock = None

        # remove connect or session
        session = self.session
        initiator = self.initiator
        if self.session:
            session.conn_list_lock.acquire()
            session.conn_list.remove(self)
            if len(session.conn_list) == 0:
                initiator.session_list_lock.acquire()
                initiator.session_list.remove(session)
                DBG_PRN('stop session', str(session))
                initiator.session_list_lock.release()
            session.conn_list_lock.release()
            self.session = None
            self.initiator = None

        DBG_PRN('connect:%d finish' % self.cid)
        return True


    def ScsiTask(self, cmd):
        '''
        do all kinks of scsi task.
        @param cmd: scsi request
        '''
        req = PDU()
        rsp = None
        session = self.session
        dl = self.PerMaxRecvDataLength.value
        fl = FBL_VAL(self)
        ml = MBL_VAL(self)

        # write task request
        if cmd.out_buf:
            length = len(cmd.out_buf)
            if session.ImmediateData.value:
                cmd.next_len = min(fl, dl, length)

            # build scsi request pdu and send
            ScsiCmdReq(self, req, cmd)
            self.send(req)
            cmd.all_len += cmd.next_len

            # check first_burst_length and send first burst data_out pdus.
            data_sn = 0
            if (session.InitialR2T.value == False and
                cmd.all_len < length and
                cmd.all_len < fl):
                while (cmd.all_len < fl and cmd.all_len < length) :
                    cmd.next_len = min(dl, fl - cmd.all_len, length - cmd.all_len)
                    req = PDU()
                    cur_len = cmd.all_len + cmd.next_len
                    DataOutReq(self, req, cmd, data_sn, cur_len >= min(fl, length))
                    self.send(req)
                    cmd.all_len += cmd.next_len
                    data_sn += 1
            # the rest data need to be sent
            while (cmd.all_len < length):
                # need R2T request initiator receive buffer
                rsp = self.recv()
                cmd.r2t_len = rsp.get_res_cnt()
                cmd.tid = rsp.get_ttt()

                # check max_burst_length and send rest data
                data_sn = 0
                data_off = 0
                while (data_off < ml and
                       data_off < cmd.r2t_len and
                       cmd.all_len < length):
                    cmd.next_len = min(dl, ml - data_off, cmd.r2t_len - data_off,
                                       length - cmd.all_len)
                    cur_len = data_off + cmd.next_len 
                    DataOutReq(self, req, cmd, data_sn,
                               cur_len >= min(ml, length, cmd.r2t_len))
                    self.send(req)
                    cmd.all_len += cmd.next_len
                    data_off += cmd.next_len
                    data_sn += 1
            # receive response
            rsp = self.recv()
        # read task request
        else:
            ScsiCmdReq(self, req, cmd)
            self.send(req)
            cmd.in_buf = ''
            while True:
                rsp = self.recv()
                if rsp == None:
                    cmd.state = INTR_SCSI_STATE_FAILED
                else:
                    code = OPCODE(rsp)
                    if code == ISCSI_OP_SCSI_DATA_IN:
                        cmd.in_buf += rsp.data
                        if rsp.bhs[1] & 0x80 == 0x00:
                            continue
                        cmd.state = INTR_SCSI_STATE_FINISH
                        # data not contain scsi status
                        if rsp.bhs[1] & 0x01 == 0x00:
                            continue
                    elif code == ISCSI_OP_SCSI_CMD_RSP:
                        cmd.status = rsp.bhs[3]
                        if rsp.get_data_len():
                            if cmd.status != SAM_STAT_GOOD:
                                cmd.sense = rsp.data 
                        cmd.state = INTR_SCSI_STATE_FINISH
                    else:
                        cmd.state = INTR_SCSI_STATE_FAILED
                break
        cmd.state = INTR_SCSI_STATE_FINISH


    def Idle(self):
        '''
        connect idle itself
        '''
        self.sock.time_out(1)
        rsp = self.recv()
        if rsp:
            if OPCODE(rsp) == ISCSI_OP_NOOP_IN:
                req = PDU()
                DBG_CMD('NotIn')
                NopOut(self, req, rsp)
                self.send(req)
            else:
                DBG_WRN('handle other command', OPCODE(rsp))


    def Task(self):
        '''
        dispatch all scsi task.
        if no any task, idle.
        '''
        lst = self.session.scsi_list
        while self.state == ISCSI_FULL_FEATURE_PHASE:
            cmd = lst.pop_conn_cmd(self)
            if cmd != None:
                while cmd:
                    cmd.state = INTR_SCSI_STATE_PENDING
                    self.ScsiTask(cmd)
                    cmd = lst.pop_conn_cmd(self)
            else:
                self.Idle()


    def send(self, req):
        '''
        connect send an iscsi request pdu.
        @param req: iscsi request pdu
        @return: True for success, False for failed
        '''
        return self.sock.send(req, self.Digest)


    def recv(self):
        '''
        connect receive and iscsi pdu
        @return: None for failed, other for success.
        '''
        return self.sock.recv(self.Digest, MRDSL_VAL(self))
    
    def exchange(self, req):
        '''
        send request pdu and receive response pdu
        '''
        if self.send(req) == False:
            return False
        return self.recv()