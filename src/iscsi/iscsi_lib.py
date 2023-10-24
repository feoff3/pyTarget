#    
#    iscsi library, implement iscsi layer function.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-28)
#

import hashlib
import socket
import scsi.scsi_lib as slib
from iscsi.iscsi_comm import *
from iscsi.iscsi_negotiate import *
from iscsi.iscsi_erl import *


ISCSI_CMD_UNNEED_RSP            = 0x00
ISCSI_CMD_NEED_RSP              = 0x01
ISCSI_CMD_DELAYED_RSP           = 0x02

# iscsi session/connect type
SESSION_ERROR                   = 0x00
SESSION_DISCOVERY               = 0x01
SESSION_NORMAL                  = 0x02
SESSION_MCS                     = 0x03

class PDU():
    '''
    class for iscsi pdu
    '''
    def __init__(self):
        self.bhs = [0] * ISCSI_BHS_SIZE
        self.ahs = None
        self.data = ''
        self.state = PDU_STATE_GOOD

    # get ops
    def get_tsih(self):              return array_2_hex(self.bhs, 14, 2)
    def get_itt(self):               return array_2_hex(self.bhs, 16, 4)
    def get_ttt(self):               return array_2_hex(self.bhs, 20, 4)
    def get_cid(self):               return array_2_hex(self.bhs, 20, 2)
    def get_lun(self):               return self.bhs[9] & 0xFF
    def get_cmdsn(self):             return array_2_hex(self.bhs, 24, 4)
    def get_data_len(self):          return array_2_hex(self.bhs, 5, 3)
    def get_exp_len(self):           return array_2_hex(self.bhs, 20, 4)
    def get_statsn(self):            return array_2_hex(self.bhs, 24, 4)
    def get_exp_statsn(self):        return array_2_hex(self.bhs, 28, 4)
    def get_exp_cmdsn(self):         return array_2_hex(self.bhs, 28, 4)
    def get_max_cmdsn(self):         return array_2_hex(self.bhs, 32, 4)
    def get_data_sn(self):           return array_2_hex(self.bhs, 36, 4)
    def get_r2t_sn(self):            return array_2_hex(self.bhs, 36, 4)
    def get_data_offset(self):       return array_2_hex(self.bhs, 40, 4)    
    def get_res_cnt(self):           return array_2_hex(self.bhs, 44, 4)
    # set ops
    def set_tsih(self, val):         self.bhs[14:16] = hex_2_array(val, 2)
    def set_itt(self, val):          self.bhs[16:20] = hex_2_array(val, 4)
    def set_ttt(self, val):          self.bhs[20:24] = hex_2_array(val, 4)
    def set_cid(self, val):          self.bhs[20:22] = hex_2_array(val, 2)
    def set_lun(self, val):          self.bhs[9] = val & 0xFF
    def set_cmdsn(self, val):        self.bhs[24:28] = hex_2_array(val, 4)
    def set_data_len(self, val):     self.bhs[5:8] = hex_2_array(val, 3)
    def set_exp_len(self, val):      self.bhs[20:24] = hex_2_array(val, 4)
    def set_statsn(self, val):       self.bhs[24:28] = hex_2_array(val, 4) 
    def set_exp_statsn(self, val):   self.bhs[28:32] = hex_2_array(val, 4)
    def set_exp_cmdsn(self, val):    self.bhs[28:32] = hex_2_array(val, 4)
    def set_max_cmdsn(self, val):    self.bhs[32:36] = hex_2_array(min(val, 0xffffffff), 4)
    def set_data_sn(self, val):      self.bhs[36:40] = hex_2_array(val, 4)
    def set_r2t_sn(self, val):       self.bhs[36:40] = hex_2_array(val, 4)
    def set_data_offset(self, val):  self.bhs[40:44] = hex_2_array(val, 4)
    def set_res_cnt(self, val):      self.bhs[44:48] = hex_2_array(val, 4)

     
class SessionID():
    '''
    Class for session id
    '''
    def __init__(self):
        self.isid = [0x70,0x79,0x74,0x68,0x6f,0x6e]     # python
        self.tsih = 0
    def __str__(self):
        return ('%02x' * 6 % tuple(self.isid) + '-%04x' % self.tsih)


def __set_pdu_sn(conn, rsp, update=True):
    '''
    Update sequence number
    @param conn: connect
    @param rsp: response pdu
    @param update: update session ExpCmdSN
    '''
    s = conn.session
    if update:        
        cmd_sn = s.next_exp_cmdsn()
    else:
        cmd_sn = conn.CurExpCmdSn
    rsp.set_statsn(conn.next_statsn())
    rsp.set_exp_cmdsn(cmd_sn)
    rsp.set_max_cmdsn(cmd_sn + s.cmd_wnd_size())


# Login flags
ISCSI_FLAG_LOGIN_TRANSIT               = 0x80
ISCSI_FLAG_LOGIN_CONTINUE              = 0x40
ISCSI_FLAG_LOGIN_CURRENT_STAGE_MASK    = 0x0C    # 2 bits
ISCSI_FLAG_LOGIN_NEXT_STAGE_MASK       = 0x03    # 2 bits

# Login stage (phase) codes for CSG, NSG 
ISCSI_INITIAL_LOGIN_STAGE              = -1
ISCSI_SECURITY_STAGE                   = 0
ISCSI_OPTIONAL_STAGE                   = 1
ISCSI_FULL_FEATURE_PHASE               = 3
ISCSI_LOGOUT_PHASE                     = 4
ISCSI_TARGET_STOP                      = 5
ISCSI_CONNECT_STOP                     = 6
ISCSI_ERROR_PHASE                      = -1

def FLAGS_CSG(flags):
    return ((flags & ISCSI_FLAG_LOGIN_CURRENT_STAGE_MASK) >> 2)
def FLAGS_NSG(flags):
    return (flags & ISCSI_FLAG_LOGIN_NEXT_STAGE_MASK)
def ERR_CLS(pdu):
    return pdu.bhs[36]
def ERR_DTL(pdu):
    return pdu.bhs[37]
def VER_MAX(pdu):
    return pdu.bhs[2]
def VER_MIN(pdu):
    return pdu.bhs[3] 


#=======================================================
#                 Login request
#=======================================================
def LoginReq(conn, req, rsp):
    sess = conn.session
    req.bhs[0]     = (ISCSI_OP_LOGIN |ISCSI_OP_IMMEDIATE)   # opcode
    req.bhs[1]     = 0                                      # flags
    req.bhs[2]     = ISCSI_DRAFT20_VERSION                  # max version
    req.bhs[3]     = ISCSI_DRAFT20_VERSION                  # active version
    req.bhs[8:14]  = conn.session.sid.isid[:]               # ISID
    req.set_tsih(conn.session.sid.tsih)                     # TSIH
    req.set_itt(conn.CurITT)                                # ITT
    req.set_cid(conn.cid)                                   # CID
    req.set_cmdsn(conn.CurCmdSN)                            # CmdSN
    req.set_exp_statsn(conn.next_statsn())                  # ExpStatSn

    if conn.state == ISCSI_SECURITY_STAGE:
        if conn.initiator.target_pwd:
            if conn.chap_state == 0:
                conn.chap_state = CHAP_STATE_CHAP
            if conn.chap_state == CHAP_STATE_CHAP:
                # send CHAP
                set_key_val(req, 'InitiatorName', conn.initiator.name)
                set_key_val(req, 'AuthMethod', 'CHAP')
                if conn.type != SESSION_DISCOVERY:
                    set_key_val(req, 'SessionType', 'Normal')
                    set_key_val(req, 'TargetName', conn.initiator.target_name)                    
                else:
                    set_key_val(req, 'SessionType', 'Discovery')
            elif conn.chap_state == CHAP_STATE_CHAP_A:
                # check AuthMethod and send CHAP_A
                key = get_key_val(rsp, 'AuthMethod')
                DBG_NEG('AuthMethod =', key)
                if key != 'CHAP':
                    return False
                set_key_val(req, 'CHAP_A', '5')
            elif conn.chap_state == CHAP_STATE_CHAP_I:
                # check CHAP_A and send CHAP_N/R
                key = get_key_val(rsp, 'CHAP_A')
                DBG_NEG('CHAP_A =', key)
                if key != '5':
                    return False
                chap_i = get_key_val(rsp, 'CHAP_I')
                chap_c = get_key_val(rsp, 'CHAP_C')
                if chap_i == None or chap_i == 'Reject' or \
                   chap_c == None or chap_c == 'Reject':
                    return False
                DBG_NEG('CHAP_I =', chap_i)
                DBG_NEG('CHAP_C =', chap_c[:20] + '...')
                chap_c = get_challenge(chap_c[2:])
                chap_i = atoi(chap_i)
                ctx = hashlib.md5()
                ctx.update(do_pack([chap_i]))
                ctx.update(conn.initiator.target_pwd)
                ctx.update(chap_c)
                set_key_val(req, 'CHAP_N', conn.initiator.name)
                set_key_val(req, 'CHAP_R', '0x' + ctx.hexdigest())
                # set TRANSIT Bit
                req.bhs[1] |= ISCSI_FLAG_LOGIN_TRANSIT              # Flags
                req.bhs[1] |= (ISCSI_SECURITY_STAGE << 2) & 0x0C    # CSG
                req.bhs[1] |= ISCSI_OPTIONAL_STAGE & 0x03           # NSG 
        else:
            if conn.chap_state == 0:               
                set_key_val(req, 'AuthMethod', 'None')
                set_key_val(req, 'InitiatorName', conn.initiator.name)
                if conn.type != SESSION_DISCOVERY:
                    set_key_val(req, 'SessionType', 'Normal')
                    set_key_val(req, 'TargetName', conn.initiator.target_name)
                else:
                    set_key_val(req, 'SessionType', 'Discovery')
            req.bhs[1] |= ISCSI_FLAG_LOGIN_TRANSIT              # Flags
            req.bhs[1] |= (ISCSI_SECURITY_STAGE << 2) & 0x0C    # CSG
            req.bhs[1] |= ISCSI_OPTIONAL_STAGE & 0x03           # NSG
        conn.chap_state += 1            
    elif conn.state == ISCSI_OPTIONAL_STAGE:
        # Header/Data digest
        if conn.Digest & DIGEST_HEAD: key = 'CRC32C'
        else: key = 'None'
        set_key_val(req, 'HeaderDigest', key)
        if conn.Digest & DIGEST_DATA: key = 'CRC32C'
        else: key = 'None'
        set_key_val(req, 'DataDigest', key)
        # MaxRecvDataSegmentLength
        set_key_val(req, 'MaxRecvDataSegmentLength', MRDSL_VAL(conn))

        # leading connection negotiation only
        if conn.isLeading:
            set_key_val(req, 'ErrorRecoveryLevel', sess.ErrorRecoveryLevel.value)
            set_key_val(req, 'DefaultTime2Retain', sess.DefaultTime2Retain.value)          
            set_key_val(req, 'DefaultTime2Wait', sess.DefaultTime2Wait.value)

            # normal session negotiation only
            if conn.type != SESSION_DISCOVERY:
                set_key_val(req, 'MaxConnections', sess.MaxConnections.value)
                set_key_val(req, 'InitialR2T', sess.InitialR2T.value)
                set_key_val(req, 'ImmediateData', sess.ImmediateData.value)
                set_key_val(req, 'DataPDUInOrder', sess.DataPDUInOrder.value)
                set_key_val(req, 'DataSequenceInOrder', sess.DataSequenceInOrder.value)
                set_key_val(req, 'MaxBurstLength', sess.MaxBurstLength.value)
                set_key_val(req, 'FirstBurstLength', sess.FirstBurstLength.value)
                set_key_val(req, 'MaxOutstandingR2T', sess.MaxOutstandingR2T.value)
        req.bhs[1] |= ISCSI_FLAG_LOGIN_TRANSIT 
        req.bhs[1] |= (ISCSI_OPTIONAL_STAGE << 2) & 0x0C    # CSG
        req.bhs[1] |= ISCSI_FULL_FEATURE_PHASE & 0x03       # NSG

#=======================================================
#                 Login response
#=======================================================
def LoginRsp(conn, req, rsp, err_class, err_detail): 
    s = conn.session
    rsp.bhs[0]     = ISCSI_OP_LOGIN_RSP                 # Opcode
    rsp.bhs[1]     = req.bhs[1]                         # Flags
    rsp.bhs[2]     = ISCSI_DRAFT20_VERSION              # Max version
    rsp.bhs[3]     = ISCSI_DRAFT20_VERSION              # Active version
    rsp.bhs[8:15]  = req.bhs[8:15]                      # isid
    rsp.bhs[16:20] = req.bhs[16:20]                     # ITT

    t_bit = req.bhs[1] & ISCSI_FLAG_LOGIN_TRANSIT
    csg_bit = FLAGS_CSG(req.bhs[1])
    nsg_bit = FLAGS_NSG(req.bhs[1])
    finish = True

    # check opcode, flags, and authmethod
    if OPCODE(req) != ISCSI_OP_LOGIN:
        err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
        err_detail = ISCSI_LOGIN_STATUS_INVALID_REQUEST
        DBG_WRN('receive non login request pdu in login phase.')
    elif (csg_bit != ISCSI_SECURITY_STAGE and
          csg_bit != ISCSI_OPTIONAL_STAGE):
        err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
        err_detail = ISCSI_LOGIN_STATUS_INVALID_REQUEST
        DBG_WRN('flags of login request pdu is invalid(0x%x).' % req.bhs[1])
    elif (csg_bit != ISCSI_SECURITY_STAGE and
          conn.AuthMethod.value and
          conn.chap_state < CHAP_STATE_FINISH):
        err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
        err_detail = ISCSI_LOGIN_STATUS_AUTH_FAILED
        DBG_WRN('security negotiate failed')

    # login request pdu with (c_bit=1) 
    if err_class == 0 and err_detail == 0:
        id = req.get_itt()
        lst = s.iscsi_cmd_list
        prev = lst.find_pdu(id)

        if prev:
            prev.data += req.data
            if req.bhs[1] & ISCSI_FLAG_LOGIN_CONTINUE:
                finish = False
            else:
                lst.pop_pdu(id)
                req.data = prev.data
        else:
            if req.bhs[1] & ISCSI_FLAG_LOGIN_CONTINUE:
                lst.push_pdu(req)
                finish = False

    #
    # Login request pdu is ready,
    # we should analysis all key-value pairs now.
    #
    if (finish and
        err_class == 0 and err_detail == 0):
        key_pair = get_key_pair(req)

        # TargetPortalGroupTag 
        if not conn.TargetPortalGroupTag.is_ready() and \
           not 'TargetPortalGroupTag' in key_pair:
            conn.TargetPortalGroupTag.ready()
            set_key_val(rsp, 'TargetPortalGroupTag', conn.target.portal)
            DBG_NEG('TargetPortalGroupTag =', conn.target.portal)

            # TargetAlias
            if conn.type != SESSION_DISCOVERY:
                host_name = socket.gethostname()
                set_key_val(rsp, 'TargetAlias', host_name)
                DBG_NEG('TargetAlias =', host_name)

    #
    # (SNP) security negotiation phase
    #
    if (finish and 
        csg_bit == ISCSI_SECURITY_STAGE and
        err_class == 0 and err_detail == 0):

        # AuthMethod
        if conn.AuthMethod.negotiate(req, rsp) == 'Reject':
            err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
            err_detail = ISCSI_LOGIN_STATUS_AUTH_FAILED
            DBG_WRN('AuthMethod in login request pdu is failed.')
        # next state
        elif (t_bit and
              nsg_bit != ISCSI_OPTIONAL_STAGE and
              nsg_bit != ISCSI_FULL_FEATURE_PHASE):
            err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
            err_detail = ISCSI_LOGIN_STATUS_INVALID_REQUEST
            DBG_WRN('Flags of login request pdu is invalid: 0x%x.' % req.bhs[1])
        # need chap
        elif conn.AuthMethod.value:
            if conn.chap_state == CHAP_STATE_CHAP:
                pass
            elif conn.chap_state == CHAP_STATE_CHAP_A:
                identify = random.randint(0,0xFF)
                challenge = build_challenge()
                key = CHAP_A.check(req)
                if ('CHAP_I' in key_pair or
                    'CHAP_C' in key_pair or
                    'CHAP_N' in key_pair):
                    err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
                    err_detail = ISCSI_LOGIN_STATUS_AUTH_FAILED
                    DBG_WRN('detect CHAP_A/CHAP_C/CHAP_I/CHAP_N out of order')
                elif key == None:
                    err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
                    err_detail = ISCSI_LOGIN_STATUS_MISSING_FIELDS
                    DBG_WRN('CHAP_A is missing')
                elif key == '5':
                    conn.chap_alg = CHAP_MD5
                    ctx = hashlib.md5()
                else:
                    err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
                    err_detail = ISCSI_LOGIN_STATUS_AUTH_FAILED
                    set_key_val(rsp, 'CHAP_A', key)
                    DBG_WRN('CHAP_A is invalid:', key)
                if err_class == 0 and err_detail == 0:
                    ctx.update(do_pack([identify]))
                    ctx.update(conn.host.target_pwd)
                    ctx.update(do_pack(challenge))
                    conn.tagt_challenge = '0x' + '%02x'*len(challenge) % tuple(challenge)
                    conn.chap_value = '0x' + ctx.hexdigest()
                    set_key_val(rsp, 'CHAP_A', conn.chap_alg)
                    set_key_val(rsp, 'CHAP_I', identify)
                    set_key_val(rsp, 'CHAP_C', conn.tagt_challenge)
                    DBG_NEG('CHAP_A = %d' % conn.chap_alg)
                    DBG_NEG('CHAP_I = %d' % identify)
                    DBG_NEG('CHAP_C = ' + conn.tagt_challenge[:42] + '...')
            elif conn.chap_state == CHAP_STATE_CHAP_I:
                name = CHAP_N.check(req)
                key = CHAP_R.check(req)
                if name == None or name.isdigit() or len(name) > 255:
                    err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
                    err_detail = ISCSI_LOGIN_STATUS_MISSING_FIELDS
                    DBG_WRN('CHAP_N is invalid:', name)
                elif key == None:
                    err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
                    err_detail = ISCSI_LOGIN_STATUS_MISSING_FIELDS
                    DBG_WRN('CHAP_R is missing.')
                elif key.upper() != conn.chap_value.upper():
                    err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
                    err_detail = ISCSI_LOGIN_STATUS_AUTH_FAILED
                    DBG_WRN('CHAP_R is invalid:', key.lower())
                    DBG_WRN('CHAP_R should be:', conn.chap_value.lower())
                DBG_NEG('CHAP_R =', key)

                identify = CHAP_I.check(req)
                challenge = CHAP_C.check(req)
                name = CHAP_N.check(req)
                if identify and challenge and err_class == 0 and err_detail == 0:
                    if name == 'Reject':
                        err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
                        err_detail = ISCSI_LOGIN_STATUS_AUTH_FAILED
                        set_key_val(rsp, 'CHAP_N', identify)
                        DBG_WRN('CHAP_N is invalid:', name)
                    elif identify == 'Reject':
                        err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
                        err_detail = ISCSI_LOGIN_STATUS_AUTH_FAILED
                        set_key_val(rsp, 'CHAP_I', identify)
                        DBG_WRN('CHAP_I is invalid:', identify)
                    elif challenge == 'Reject':
                        err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
                        err_detail = ISCSI_LOGIN_STATUS_AUTH_FAILED
                        set_key_val(rsp, 'CHAP_C', challenge)
                        DBG_WRN('CHAP_C is invalid:', challenge)
                    else:
                        # check challenge is reuse
                        s.conn_list_lock.acquire()
                        for item in s.conn_list:
                            if challenge.upper() == item.intr_challenge.upper() or \
                               challenge.upper() == item.tagt_challenge.upper():
                                err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
                                err_detail = ISCSI_LOGIN_STATUS_MISSING_FIELDS
                                DBG_WRN('Challenge message has been used.')
                                break
                        s.conn_list_lock.release()
                        if err_class == 0 or err_detail == 0:
                            conn.intr_challenge = challenge
                            if conn.chap_alg == CHAP_MD5:
                                ctx = hashlib.md5()
                            else: 
                                ctx = hashlib.sha1()
                            ctx.update(do_pack([atoi(identify)]))
                            ctx.update(conn.host.initiator_pwd)
                            ctx.update(get_challenge(challenge[2:]))
                            set_key_val(rsp, 'CHAP_N', conn.host.name)
                            set_key_val(rsp, 'CHAP_R', '0x' + ctx.hexdigest())
                            DBG_NEG('CHAP_I =', identify)
                            DBG_NEG('CHAP_C =', challenge[:42]+'...')
            conn.chap_state += 1
            if conn.chap_state < CHAP_STATE_FINISH:
                rsp.bhs[1] = 0
        # end chap
    # end SNP    

    #
    # (ONP) optional negotiation phase
    #
    elif csg_bit == ISCSI_OPTIONAL_STAGE and \
         err_class == 0 and err_detail == 0 and finish:

        # check NotUnderstood/Reject key
        for key in ISCSI_TARGET_ONLY_KEY:
            if key in key_pair:
                if key_pair[key] == 'NotUnderstood' or \
                   key_pair[key] == 'Reject':
                    err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
                    err_detail = ISCSI_LOGIN_STATUS_INVALID_REQUEST
                set_key_val(rsp, key, 'Reject')
                DBG_WRN('detect invalid key: %s =' % key, key_pair[key])

        if t_bit and nsg_bit != ISCSI_FULL_FEATURE_PHASE:
            err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
            err_detail = ISCSI_LOGIN_STATUS_INVALID_REQUEST
            DBG_WRN('Flags of login request pdu is invalid: 0x%x.' % req.bhs[1])
        else:           
            conn.HeaderDigest.negotiate(req, rsp)
            conn.DataDigest.negotiate(req, rsp)
            conn.PerMaxRecvDataSegmentLength.negotiate(req, rsp)

            # MaxRecvDataSegmentLength is a declaration type key
            if not conn.MaxRecvDataSegmentLength.is_ready():
                conn.MaxRecvDataSegmentLength.ready()
                set_key_val(rsp, 'MaxRecvDataSegmentLength', conn.MaxRecvDataSegmentLength.value)
                DBG_NEG('TargetMaxRecvdataLength =', conn.MaxRecvDataSegmentLength.value)

            # leading connection negotiation only
            if conn.isLeading:
                s.ErrorRecoveryLevel.negotiate(req, rsp)
                s.DefaultTime2Retain.negotiate(req, rsp)
                s.DefaultTime2Wait.negotiate(req, rsp)

                conn.OFMarker.negotiate(req, rsp)
                conn.IFMarker.negotiate(req, rsp)
                conn.OFMarkInt.negotiate(req, rsp)
                conn.IFMarkInt.negotiate(req, rsp)

                if conn.type != SESSION_DISCOVERY:
                    s.TaskReporting.negotiate(req, rsp)
                    s.MaxConnections.negotiate(req, rsp)
                    s.InitialR2T.negotiate(req, rsp)
                    s.ImmediateData.negotiate(req, rsp)
                    s.DataPDUInOrder.negotiate(req, rsp)
                    s.DataSequenceInOrder.negotiate(req, rsp)
                    s.MaxOutstandingR2T.negotiate(req, rsp)
                    s.MaxBurstLength.negotiate(req, rsp)
                    s.FirstBurstLength.negotiate(req, rsp, s.MaxBurstLength.value)

                    # FirstBurstLength <= MaxBurstLength
                    if s.MaxBurstLength.t_ready and s.FirstBurstLength.t_ready:
                        if s.FirstBurstLength.value > s.MaxBurstLength.value:
                            err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
                            err_detail = ISCSI_LOGIN_STATUS_INVALID_REQUEST
                            DBG_WRN('detect FirstBurstLength(%d) is bigger than MaxBurstLength(%d)'%
                                     (s.FirstBurstLength.value, s.MaxBurstLength.value))
                    else:
                        if (t_bit and
                            s.MaxBurstLength.i_ready   == True and
                            s.FirstBurstLength.i_ready == False):
                            s.FirstBurstLength.i_ready = True
                            s.FirstBurstLength.t_ready = True
                            s.FirstBurstLength.value = min(s.FirstBurstLength.value, s.MaxBurstLength.value)
                            set_key_val(rsp, 'FirstBurstLength', s.FirstBurstLength.value)
                            DBG_NEG('FirstBurstLength =', s.FirstBurstLength.value)
                else:
                    for key in ISCSI_DISCOVERY_IRRELEVANT_KEY:
                        if key in key_pair:
                            set_key_val(rsp, key, 'Irrelevant')
            else:
                # leading connection key
                for key in ISCSI_LEADING_KEY:
                    if key in key_pair:
                        err_class = ISCSI_STATUS_CLS_INITIATOR_ERR
                        err_detail = ISCSI_LOGIN_STATUS_INVALID_REQUEST
                        set_key_val(rsp, key, 'Reject')
                        DBG_WRN('detect', key, 'negotiate in non-leading connect(%d)' % conn.cid)
 
    if err_class or err_detail:
        conn.state  = ISCSI_ERROR_PHASE
        rsp.bhs[1]  = 0
        rsp.bhs[36] = err_class
        rsp.bhs[37] = err_detail
        rsp.set_statsn(req.get_exp_statsn())
        rsp.set_exp_cmdsn(req.get_cmdsn())
        rsp.set_max_cmdsn(req.get_cmdsn())   
    else:
        # not understood key, and do not define in rfc3720
        # so we do not need to response login reject
        if finish:
            for key in key_pair:
                if not (key in ISCSI_KEY_PAIR.has_key):
                    set_key_val(rsp, key, 'NotUnderstood')

        # return tsih at the last login response pdu
        if (t_bit and
            (csg_bit == ISCSI_OPTIONAL_STAGE or
             csg_bit == ISCSI_FULL_FEATURE_PHASE )):
            rsp.set_tsih(s.sid.tsih)

        # in login phase, we set the command windows to 1
        rsp.set_statsn(conn.next_statsn())
        rsp.set_exp_cmdsn(conn.CurExpCmdSn)
        rsp.set_max_cmdsn(conn.CurExpCmdSn + 1)

#=======================================================
#                 Text request
#=======================================================
def TextReq(conn, req):
    req.bhs[0] = (ISCSI_OP_TEXT | ISCSI_OP_IMMEDIATE)  # Opcode
    req.bhs[1] = ISCSI_FLAG_CMD_FINAL                  # Flags
    req.set_itt(conn.session.next_itt())               # ITT
    req.set_ttt(0xffffffff)                            # TTT
    req.set_cmdsn(conn.session.next_cmdsn())           # CmdSN
    req.set_exp_statsn(conn.next_statsn())             # ExpStatSn

    if conn.type == SESSION_DISCOVERY:
        set_key_val(req, 'SendTargets', 'All')

def ISCSI_TEXT_F_BIT(flags):
    return (flags & 0x80) >> 7
def ISCSI_TEXT_C_BIT(flags):
    return (flags & 0x40) >> 6

#=======================================================
#                 Text response
#=======================================================
def TextRsp(conn, req, rsp):

    s = conn.session
    lst = s.iscsi_cmd_list
    reject = False
    rej_req = req
    ret = ISCSI_CMD_NEED_RSP
    
    f_bit = ISCSI_TEXT_F_BIT(req.bhs[1])
    c_bit = ISCSI_TEXT_C_BIT(req.bhs[1])
    itt = req.get_itt()
    ttt = req.get_ttt()

    rsp.bhs[0] = ISCSI_OP_TEXT_RSP                      # opcode
    rsp.set_itt(itt)                                    # itt
    rsp.set_statsn(conn.next_statsn())                  # StatSN

    #
    # Text negotiation task must be in sequential order.
    # so we need to find un-complete text request pdu,
    # and attach current pdu to previous one.
    #

    pre = None
    lst.lock()
    for pdu in lst.list:
        if OPCODE(pdu) == ISCSI_OP_TEXT:
            pre = pdu
            break
    lst.unlock()

    if c_bit and f_bit:
        DBG_WRN('Flags of text request pdu is invalid: 0x%x' % req.bhs[1])
        reject = True
    elif pre == None:
        if f_bit == 0:
            if ttt != 0xffffffff:
                DBG_WRN('ITT of first text request pdu is not 0xffffffff (0x%x)' % itt)
                reject = True
            else:
                conn.CurTTT = s.next_ttt()
                conn.CurExpCmdSn = s.next_exp_cmdsn()
                lst.push_pdu(req)
    else:
        if itt != pre.get_itt():
            DBG_WRN('ITT of sub text request pdu is invalid: 0x%x' % itt)
            reject = True
        else:
            pre.data += req.data
            if f_bit:
                lst.pop_pdu(itt)
                req = pre

    # check every text key in the text request pdu whether legal 
    if pre:
        key_pair = get_key_pair(pre)
    else:
        key_pair = get_key_pair(req)
    for key in key_pair:
        if key_pair[key] == 'Reject':
            DBG_WRN('detect multi-key in text request:', key)
            reject = True

    if not reject and f_bit:

        # text request pdu is ready,
        # we should analysis all key-value pairs now.
        key_pair = get_key_pair(req)

        # MaxRecvDataSegmentLength
        if 'MaxRecvDataSegmentLength' in key_pair.has_key:
            if conn.type == SESSION_DISCOVERY:
                DBG_WRN('detect text negotiating \'MaxRecvDataSegmentLength\' in discovery session')
                reject = True
            else:
                key = conn.PerMaxRecvDataSegmentLength.text_nego(req, rsp)
                if key == 'Reject':
                    reject = True
                    
        # HeaderDigest            
        if 'HeaderDigest' in key_pair:
            key = conn.HeaderDigest.text_nego(req, rsp)
            if key == 'Reject':
                reject = True
            elif key == 'CRC32C':
                conn.Digest |= DIGEST_HEAD
            elif key == 'None':
                conn.Digest &= ~DIGEST_HEAD
                
        # DataDigest
        if 'DataDigest' in key_pair:
            key = conn.DataDigest.text_nego(req, rsp)
            if key == 'Reject':
                reject = True
            elif key == 'CRC32C':
                conn.Digest |= DIGEST_DATA
            elif key == 'None':
                conn.Digest &= ~DIGEST_DATA

        # SendTargets        
        if 'SendTargets' in key_pair:
            key = key_pair['SendTargets']
            if key == 'All':
                if conn.type == SESSION_DISCOVERY:
                    set_key_val(rsp, 'TargetName', conn.target.name)
                    for addr in conn.target.addr:
                        set_key_val(rsp, 'TargetAddress', addr)
                else:
                    set_key_val(rsp, 'SendTargets', 'Reject')
                    f_bit = 0           
            elif key == conn.target.name:
                set_key_val(rsp, 'TargetName', conn.target.name)
                for addr in conn.target.addr:
                    set_key_val(rsp, 'TargetAddress', addr)
            elif not key:
                set_key_val(rsp, 'TargetName', conn.target.name)
                for addr in conn.target.addr:
                    set_key_val(rsp, 'TargetAddress', addr)
            else:
                set_key_val(rsp, 'SendTargets', 'Reject')
                f_bit = 0
       
    if reject:       
        # negotiate fail, remove all text pdu
        lst.lock()
        for pdu in lst.list:
            if OPCODE(pdu) == ISCSI_OP_TEXT:
                lst.list.remove(pdu)
        lst.unlock()
        Reject(conn, rej_req, rsp, REJECT_PROTOCOL_ERROR, True)      
    elif f_bit:
        # check not understood key
        for key in key_pair:
            if not ( key in ISCSI_KEY_PAIR):
                set_key_val(rsp, key, 'NotUnderstood')
        rsp.bhs[1] = ISCSI_FLAG_CMD_FINAL
        rsp.set_ttt(0xffffffff)
        rsp.set_exp_cmdsn(conn.CurExpCmdSn)
        rsp.set_max_cmdsn(conn.CurExpCmdSn + s.cmd_wnd_size())
    else:
        rsp.set_ttt(conn.CurTTT)
        rsp.set_exp_cmdsn(conn.CurExpCmdSn)
        rsp.set_max_cmdsn(conn.CurExpCmdSn)

    return ret


# logout reason_code mask & values
ISCSI_FLAG_LOGOUT_REASON_MASK           = 0x7F
ISCSI_LOGOUT_REASON_CLOSE_SESSION       = 0x00
ISCSI_LOGOUT_REASON_CLOSE_CONNECTION    = 0x01
ISCSI_LOGOUT_REASON_CLOSE_RECOVERY      = 0x02

# logout response
ISCSI_LOGOUT_RSP_SUCCESS                = 0x00
ISCSI_LOGOUT_RSP_CID_NOT_FOUND          = 0x01
ISCSI_LOGOUT_RSP_NOT_SUPPORTED          = 0x02
ISCSI_LOGOUT_RSP_CLEANUP_FAILED         = 0x03

def __LOGOUT_REASON(pdu):
    return (pdu.bhs[1] & ISCSI_FLAG_LOGOUT_REASON_MASK)

#=======================================================
#                 Logout request
#=======================================================
def LogoutReq(conn, req, reason):
    req.bhs[0] = (ISCSI_OP_LOGOUT | ISCSI_OP_IMMEDIATE) # Opcode
    req.bhs[1] = ISCSI_FLAG_CMD_FINAL | \
        (reason & ISCSI_FLAG_LOGOUT_REASON_MASK)        # Flags
    req.set_itt(conn.session.next_itt())                  # ITT
    req.set_cid(conn.cid)                               # CID
    req.set_cmdsn(conn.session.next_cmdsn())              # CmdSN
    req.set_exp_statsn(conn.next_statsn())                # ExpStatSn

#=======================================================
#                 Logout response
#=======================================================
def LogoutRsp(conn, req, rsp):
    s = conn.session
    rsp.bhs[0] = ISCSI_OP_LOGOUT_RSP                    # Opcode
    rsp.bhs[1] = ISCSI_FLAG_CMD_FINAL                   # Flags
    rsp.bhs[2] = ISCSI_LOGOUT_RSP_SUCCESS               # Response
    rsp.bhs[16:20] = req.bhs[16:20]                     # ITT
    __set_pdu_sn(conn, rsp, False)

    reason = __LOGOUT_REASON(req)
    
    # discovery session only allowed to close session
    if (conn.type == SESSION_DISCOVERY and
        reason != ISCSI_LOGOUT_REASON_CLOSE_SESSION):
        rsp.bhs[2] = ISCSI_LOGOUT_RSP_NOT_SUPPORTED
        DBG_WRN('detect invalid logout reason(%d) within discovery.' % reason)
        return

    #
    # connect logout order:
    # set connect state to logout firstly,
    # clear non-finish task secondly if necessary,
    # stop connect finally
    #
    if reason == ISCSI_LOGOUT_REASON_CLOSE_SESSION:
        # FIXME?
        # s.conn_list_lock.acquire()
        for item in s.conn_list:
            if item.cid != conn.cid:
                item.state = ISCSI_LOGOUT_PHASE
                item.clear_task()
                item.Stop()
        # s.conn_list_lock.release()
        conn.state = ISCSI_LOGOUT_PHASE
    elif reason == ISCSI_LOGOUT_REASON_CLOSE_CONNECTION:
        cid = req.get_cid()
        cn = s.find_conn(cid)
        if cn != None:
            cn.state = ISCSI_LOGOUT_PHASE
            cn.clear_task()
            # if close current connect, do not stop here,
            # we need to send logout response pdu.
            if cid != conn.cid:
                cn.Stop()
        else:
            rsp.bhs[2] = ISCSI_LOGOUT_RSP_CID_NOT_FOUND
            DBG_WRN('Logout connect FAILED: not found cid(%d)' % cid) 
    elif reason == ISCSI_LOGOUT_REASON_CLOSE_RECOVERY:
        # we should not clear task
        cid = req.get_cid()
        if cid == conn.cid:
            # set retain time for task reassign
            set_retain_time(conn)
            conn.state = ISCSI_LOGOUT_PHASE
            DBG_WRN('Logout connect %d for recovery' % cid)
        else:
            cn = s.find_conn(cid)
            if cn:
                # set retain time for task reassign
                set_retain_time(cn)
                cn.state = ISCSI_LOGOUT_PHASE
                cn.Stop()
            else:
                rsp.bhs[2] = ISCSI_LOGOUT_RSP_CID_NOT_FOUND
                DBG_WRN('Logout connect FAILED: not found cid(%d)' % cid)
    else:
        rsp.bhs[2] = ISCSI_LOGOUT_RSP_NOT_SUPPORTED
        DBG_WRN('Logout FAILED: unknown reason field(%d)' % reason)

#=======================================================
#                Task Management Response
#=======================================================
# Task management request function
ISCSI_TASK_FUN_ABORT_TASK                       = 0x01
ISCSI_TASK_FUN_ABORT_TASK_SET                   = 0x02
ISCSI_TASK_FUN_CLEAR_ACA                        = 0x03
ISCSI_TASK_FUN_CLEAR_TASK_SET                   = 0x04
ISCSI_TASK_FUN_LOGICAL_UNIT_RESET               = 0x05
ISCSI_TASK_FUN_TARGET_WARM_RESET                = 0x06
ISCSI_TASK_FUN_TARGET_COLD_RESET                = 0x07
ISCSI_TASK_FUN_TASK_REASSIGN                    = 0x08

# Task management response function
ISCSI_TASK_RSP_COMPLETE                         = 0x00
ISCSI_TASK_RSP_TASK_NOT_EXIST                   = 0x01
ISCSI_TASK_RSP_LUN_NOT_EXIST                    = 0x02
ISCSI_TASK_RSP_TASK_STILL_ALLEGIANT             = 0x03
ISCSI_TASK_RSP_ALLEGIANCE_NOT_SUPPORT           = 0x04
ISCSI_TASK_RSP_TASK_MANAGE_FUN_NO_SUPPORTED     = 0x05
ISCSI_TASK_RSP_FUN_AUTHOR_FAILED                = 0x06

def TASK_FUNC(pdu):
    return (pdu.bhs[1] & 0x7F)

def TaskManageRsp(conn, req, rsp):
    import tagt.cache as ch

    rsp.bhs[0] = ISCSI_OP_SCSI_TMFUNC_RSP               # Opcode
    rsp.bhs[1] = 0x80                                   # Reserved
    rsp.bhs[16:20] = req.bhs[16:20]                     # ITT
    rsp.bhs[2] = ISCSI_TASK_RSP_COMPLETE                # Response
    __set_pdu_sn(conn, rsp, False)
    
    lst = conn.session.scsi_cmd_list
    fun = TASK_FUNC(req)
    rtt = req.get_ttt()
    recovery = False

    #
    # about a task:
    # pop it up for session scsi_cmd_list,
    # and set cmd state to free
    # 

    if fun == ISCSI_TASK_FUN_ABORT_TASK:
        cmd = lst.pop(rtt)
        if cmd == None:
            rsp.bhs[2] = ISCSI_TASK_RSP_TASK_NOT_EXIST
            DBG_WRN('Task management about an exist task(%d)' % rtt)
        else:
            cmd.state = ch.SCSI_TASK_FREE
            DBG_WRN('Task management about task 0x%x' % rtt)
    elif (fun == ISCSI_TASK_FUN_ABORT_TASK_SET or
          fun == ISCSI_TASK_FUN_CLEAR_ACA or
          fun == ISCSI_TASK_FUN_CLEAR_TASK_SET or
          fun == ISCSI_TASK_FUN_LOGICAL_UNIT_RESET or
          fun == ISCSI_TASK_FUN_TARGET_WARM_RESET or
          fun == ISCSI_TASK_FUN_TARGET_COLD_RESET):        
        lun = req.get_lun()
        lst.lock()
        for item in lst.list:
            if item.lun == lun:
                DBG_WRN('About task 0x%x' % item.id)
                lst.list.remove(item)
                item.state = ch.SCSI_TASK_FREE 
        lst.unlock()
        # cold reset need close socket
        if fun == ISCSI_TASK_FUN_TARGET_COLD_RESET:
            conn.state = ISCSI_LOGOUT_PHASE
    elif fun == ISCSI_TASK_FUN_TASK_REASSIGN:
        cmd = lst.find(rtt)
        if cmd == None:
            rsp.bhs[2] = ISCSI_TASK_RSP_TASK_NOT_EXIST
            DBG_WRN('Task Management reassign an inexistent task(0x%x)' % rtt)            
        else:
            # previous connect must logout first,
            # otherwise not allow to reassign task.
            if cmd.connect.state == ISCSI_CONNECT_STOP:
                if is_active(conn, cmd):
                    cmd.connect = conn
                    recovery = True
                    DBG_WRN('Task Management reassign task(0x%x) to cid(%d)' % (rtt, conn.cid))
                else:
                    lst.pop(rtt)
                    cmd.state = ch.SCSI_TASK_FREE 
                    rsp.bhs[2] = ISCSI_TASK_RSP_TASK_NOT_EXIST
                    DBG_WRN('Task Management reassign an inactive task(0x%x)' % rtt)
            else:
                rsp.bhs[2] = ISCSI_TASK_RSP_TASK_STILL_ALLEGIANT
                DBG_WRN('Task Management reassign a still allegiant task(0x%x),' % rtt,
                         'but original connect do not logout)')
    else:
        rsp.bhs[2] = ISCSI_TASK_RSP_TASK_MANAGE_FUN_NO_SUPPORTED
        DBG_WRN('detect unknown task function(%d)' % fun)

    if recovery == False:
        return ISCSI_CMD_NEED_RSP
    else:
        conn.send(rsp)
        iscsi_task_recovery(conn, rtt, req.get_r2t_sn())
        return ISCSI_CMD_UNNEED_RSP


#=======================================================
#                Asynchronous Event
#=======================================================
ASYNC_EVENT_SENSE_DATA                          = 0x00
ASYNC_EVENT_TARGET_LOGOUT                       = 0x01
ASYNC_EVENT_TARGET_CLOSE_CURRENT_CONNECTION     = 0x02
ASYNC_EVENT_TARGET_CLOSE_ALL_CONNECTION         = 0x03
ASYNC_EVENT_TARGET_NEGOTIATION                  = 0x04

def AsynchronousEvent(conn, rsp, event, code=0, p1=0, p2=0, p3=0, lun=0):
    s = conn.session
    rsp.bhs[0]     = ISCSI_OP_ASYNC_EVENT               # Opcode
    rsp.bhs[1]     = 0x80                               # Reserved
    rsp.bhs[9]     = lun & 0xff                         # Lun
    rsp.bhs[16:20] = 0xff,0xff,0xff,0xff                # Reserved
    rsp.bhs[36]    = event & 0xff                       # AsyncEvent
    rsp.bhs[37]    = code & 0xff                        # AsyncVCode
    rsp.bhs[38:40] = hex_2_array(p1, 2)                 # Parameter1
    rsp.bhs[40:42] = hex_2_array(p2, 2)                 # Parameter2
    rsp.bhs[42:44] = hex_2_array(p3, 2)                 # Parameter3
    rsp.set_statsn(conn.next_statsn())
    rsp.set_exp_cmdsn(s.ExpCmdSn)
    rsp.set_max_cmdsn(s.ExpCmdSn + s.cmd_wnd_size())


#=======================================================
#                        Reject
#=======================================================

# Reject reason 
REJECT_DATA_DIGEST_ERROR                = 0x02
REJECT_SNACK_REJECT                     = 0x03
REJECT_PROTOCOL_ERROR                   = 0x04
REJECT_COMMAND_NOT_SUPPORTED            = 0x05
REJECT_IMMEDIATE_CMD_REJECT             = 0x06
REJECT_TASK_IN_PROGRESS                 = 0x07
REJECT_INVALID_DATA_ACK                 = 0x08
REJECT_INVALID_PDU_FIELD                = 0x09
REJECT_LONG_OPERATION_REJECT            = 0x0a
REJECT_NEGOTIATION_RESET                = 0x0B
REJECT_WARIING_FOR_LOGOUT               = 0x0C

def Reject(conn, req, rsp, reason, pack=False):
    rsp.bhs[0] = ISCSI_OP_REJECT                        # Opcode
    rsp.bhs[1] = 0x80                                   # Reserved
    rsp.bhs[2] = reason & 0xff                          # Reason
    rsp.set_itt(0xffffffff)                             # ITT
    __set_pdu_sn(conn, rsp, False)

    if pack:
        rsp.data = do_pack(req.bhs)
        rsp.set_data_len(len(rsp.data))


#=======================================================
#                        NopOut
#=======================================================
def NopOut(conn, req, rsp):
    req.bhs[0] = ISCSI_OP_NOOP_OUT                      # Opcode
    req.bhs[1] = 0x80                                   # Reserved

    req.set_itt(0xffffffff)                             # ITT                           
    req.set_ttt(rsp.get_ttt())                          # TTT
    req.set_cmdsn(conn.session.CmdSN)                   # CmdSN
    req.set_exp_statsn(rsp.get_statsn())                # ExpStatSN

    if rsp.get_data_len():
        req.data = rsp.data;                            # Ping data
        req.set_data_len(req.data)                      # Data length


#=======================================================
#                        NopIn
#=======================================================
def NopIn(conn, req, rsp):

    # Don't need to response initiator if itt=0xffffffff
    if req and req.get_itt() == 0xffffffff:
        conn.session.ExpCmdSn = req.get_cmdsn()
        return ISCSI_CMD_UNNEED_RSP

    rsp.bhs[0] = ISCSI_OP_NOOP_IN                       # Opcode
    rsp.bhs[1] = 0x80                                   # Reserved

    if req is None:
        rsp.set_itt(0xffffffff)                         # ITT
        rsp.set_ttt(conn.session.next_ttt())              # TTT
        rsp.set_statsn(conn.StatSN)                     # StatSN
        rsp.set_exp_cmdsn(conn.session.ExpCmdSn - 1)    # ExpCmdSN
        rsp.set_max_cmdsn(conn.session.ExpCmdSn +       # MaxCmdSN
                      conn.session.cmd_wnd_size())
    else:
        conn.StatSN = req.get_exp_statsn()
        cmd_sn = req.get_cmdsn()
        conn.session.ExpCmdSn = cmd_sn
        rsp.set_itt(req.get_itt())                      # ITT
        rsp.set_ttt(0xffffffff)                         # TTT
        rsp.set_statsn(conn.StatSN)                     # StatSN
        rsp.set_exp_cmdsn(cmd_sn)                       # ExpCmdSN
        rsp.set_max_cmdsn(cmd_sn +                      # MaxCmdSN
                          conn.session.cmd_wnd_size())
        conn.next_statsn()

        # attach ping data to response pdu
        if req.get_data_len():
            limit = min(len(req.data), conn.PerMaxRecvDataSegmentLength.value)
            rsp.data = req.data[:limit]
            rsp.set_data_len(len(rsp.data))

    return ISCSI_CMD_NEED_RSP


#=======================================================
#                    DataIn handle
#=======================================================

# Data Response PDU flags
 
ISCSI_FLAG_DATA_FINISH              = 0x80
ISCSI_FLAG_BIRESIDUAL_OVERFLOW        = 0x10
ISCSI_FLAG_BIRESIDUAL_UNDERFLOW        = 0x08
ISCSI_FLAG_RESIDUAL_OVERFLOW        = 0x04
ISCSI_FLAG_RESIDUAL_UNDERFLOW        = 0x02
ISCSI_FLAG_DATA_STATUS              = 0x01


def DataIn(conn, req, rsp, buf, finish = True, offset = 0, residual = 0, status=True):
    s = conn.session
    rsp.bhs[0] = ISCSI_OP_SCSI_DATA_IN                          # opcode
    rsp.bhs[16:20] = req.bhs[16:20]                             # ITT
    rsp.set_ttt(0xffffffff)                                     # TTT
    rsp.set_exp_cmdsn(conn.CurExpCmdSn)                         # ExpCmdSn
    rsp.set_max_cmdsn(conn.CurExpCmdSn + s.cmd_wnd_size())      # MaxCmdSn  

    data_sn = offset // conn.PerMaxRecvDataSegmentLength.value
    rsp.set_data_sn(data_sn)                                    # DataSn
    rsp.set_data_offset(offset)                                 # Offset
    exp_data_len = req.get_exp_len()

    # only last data-in pdu allow to set StatSN
    if finish :           
        rsp.bhs[1] = ISCSI_FLAG_CMD_FINAL
        if status:
            rsp.bhs[1] |= ISCSI_FLAG_DATA_STATUS
            rsp.set_statsn(conn.next_statsn())
            if residual < 0:
                rsp.bhs[1] |= ISCSI_FLAG_RESIDUAL_OVERFLOW
                rsp.set_res_cnt(abs(residual))
            elif residual > 0:
                rsp.bhs[1] |= ISCSI_FLAG_RESIDUAL_UNDERFLOW
                rsp.set_res_cnt(abs(residual))
    rsp.data = buf[:min(exp_data_len, len(buf))]
    rsp.set_data_len(min(exp_data_len, len(buf)))


#=======================================================
#                 R2T response
#=======================================================
def R2TRsp(conn, rsp, cmd):
    s = conn.session
    rsp.bhs[0] = ISCSI_OP_R2T                                   # opcode
    rsp.bhs[1] = 0x80                                           # Reserve
    rsp.set_itt(cmd.pdu.get_itt())                              # ITT
    rsp.set_ttt(cmd.tid)                                        # TTT
    rsp.set_r2t_sn(cmd.r2t_sn)                                  # R2TSN
    rsp.set_data_offset(len(cmd.in_buf))                        # Offset
    rsp.set_res_cnt(cmd.next_len)                               # Desired Length
    rsp.set_statsn(conn.StatSN)                                 # StatSN
    rsp.set_exp_cmdsn(conn.CurExpCmdSn)                         # ExpCmdSn
    rsp.set_max_cmdsn(conn.CurExpCmdSn + s.cmd_wnd_size())      # MaxCmdSn
    cmd.r2t_sn += 1

#
# Build scsi response BHS
#
def ScsiRsp(conn, req, rsp, status, residual=0):
    rsp.bhs[0] = ISCSI_OP_SCSI_CMD_RSP                          # opcode
    rsp.bhs[1] = ISCSI_FLAG_CMD_FINAL                           # flags
    rsp.bhs[3] = status                                         # status
    rsp.bhs[16:20] = req.bhs[16:20]                             # ITT
    code = req.bhs[32]
    if residual < 0:
        rsp.bhs[1] |= ISCSI_FLAG_RESIDUAL_OVERFLOW
        rsp.set_res_cnt(abs(residual))
    elif residual > 0:
        rsp.bhs[1] |= ISCSI_FLAG_RESIDUAL_UNDERFLOW
        rsp.set_res_cnt(abs(residual))
    __set_pdu_sn(conn, rsp, False)


#=======================================================
#                 DataOut request
#=======================================================
def DataOutReq(conn, req, cmd, data_sn, final):
    req.bhs[0] = ISCSI_OP_SCSI_DATA_OUT                         # Opcode
    req.bhs[1] = (0x00, 0x80)[final]                            # Flags
    req.set_lun(cmd.lun)                                        # Lun
    req.set_itt(cmd.id)                                         # ITT
    req.set_ttt(cmd.tid)                                        # TTT
    req.set_exp_statsn(conn.ExpStatSN)                          # ExpStatSn FIXME ??
    req.set_data_sn(data_sn)                                    # DataSN
    req.set_data_offset(cmd.all_len)                            # BufferOffset
    req.set_data_len(cmd.next_len)                              # DataSegmentLength
    req.data = cmd.out_buf[cmd.all_len : cmd.all_len + cmd.next_len]


#=======================================================
#                 DataOut handle
#=======================================================
def DataOutRsp(conn, req, rsp):
    import tagt.cache as cah

    ret = ISCSI_CMD_NEED_RSP

    #
    # attach data pdu to scsi_cmd_list,
    # if all data-out pdus of this task receive finish,
    # task will be executed.
    #
    cmd = conn.session.scsi_cmd_list.data_request(conn, req)

    if cmd is None:
        Reject(conn, req, rsp, REJECT_PROTOCOL_ERROR, True)
    elif cmd.state == cah.SCSI_TASK_FINISH:
        # task executed finish, response response and status  
        ScsiRsp(conn, req, rsp, cmd.status)
        if cmd.status:
            if cmd.sense:
                rsp.data = cmd.sense
                rsp.set_data_len(len(rsp.data))
        cmd.state = cah.SCSI_TASK_FREE
    elif cmd.state == cah.SCSI_TASK_R2T:
        R2TRsp(conn, rsp, cmd)
    elif cmd.state == cah.SCSI_TASK_RECEIVE:
        ret = ISCSI_CMD_UNNEED_RSP
    return ret


#=======================================================
#                 SNACK Response
#=======================================================

# snack type
SANCK_TYPE_DATA_OR_R2T              = 0
SANCK_TYPE_STATUS                   = 1
SANCK_TYPE_DATA_ACK                 = 2
SANCK_TYPE_R_DATA                   = 3

def SNACK_TYPE(pdu):
    return (pdu.bhs[1] & 0x0f)
    
def SnackRsp(conn, req, rsp):

    s = conn.session
    type = SNACK_TYPE(req)
    itt = req.get_itt()
    ret = ISCSI_CMD_NEED_RSP
    beg_run = req.get_data_offset()
    run_len = req.get_res_cnt()

    # data/r2t
    if type == SANCK_TYPE_DATA_OR_R2T:
        cmd = s.scsi_cmd_list.find(itt)
        # if task is a write command, snak for r2t
        if cmd and slib.IS_OUT_IOCMD(cmd.cdb[0]):
            if (cmd.r2t_sn == 0 or
                cmd.r2t_sn <= beg_run):
                Reject(conn, req, rsp, REJECT_PROTOCOL_ERROR, True)
                DBG_WRN('Snack for an nonexistent R2T (itt:0x%x RegRun:%d, RunLength:%d)' % (itt, beg_run, run_len))
            else:
                # recovery cmd data buffer if necessary
                r2t_roll_back(conn, cmd, beg_run)
                R2TRsp(conn, rsp, cmd)
                DBG_WRN('Snack for task(%d) R2T(%d)' % (itt, beg_run))
        # snack for data-in
        elif cmd and slib.IS_IN_IOCMD(cmd.cdb[0]) and cmd.out_buf:
            iscsi_data_recovery(conn, cmd, beg_run, run_len)
            ret = ISCSI_CMD_UNNEED_RSP
            DBG_WRN('Snack for task(%d) data(RegRun:%d, RunLength:%d)' % (itt, beg_run, run_len))
        else:
            Reject(conn, req, rsp, REJECT_SNACK_REJECT)
            DBG_WRN('Snack task FAILED, not find task(%d)' % itt)
    # status
    elif type == SANCK_TYPE_STATUS:
        iscsi_status_recovery(conn, beg_run, run_len)
        ret = ISCSI_CMD_UNNEED_RSP
        DBG_WRN('Snack for status(RegRun:%d, RunLength:%d)' % (beg_run, run_len))
    # data_ack
    elif type == SANCK_TYPE_DATA_ACK:
        cmd = s.scsi_cmd_list.find(itt)
        if cmd == None:
            Reject(conn, req, rsp, REJECT_SNACK_REJECT, True)
            DBG_WRN('Snack for an nonexistent DataAck (itt:0x%x)' % itt)
        else:
            iscsi_data_ack_recovery(conn, cmd)
            ret = ISCSI_CMD_UNNEED_RSP
    # r_data
    elif type == SANCK_TYPE_R_DATA:
        cmd = s.scsi_cmd_list.find(itt)
        if cmd == None:
            Reject(conn, req, rsp, REJECT_PROTOCOL_ERROR, True)
            DBG_WRN('Snack for an nonexistent R_Data (itt:0x%x RegRun:%d, RunLength:%d)' % (itt, beg_run, run_len))            
        else:
            # Initiator MaxRecvDagaSgementLength, FirstBurstLength, etc
            # may be change by text negotiation
            iscsi_data_recovery(conn, cmd, beg_run, run_len)
            ret = ISCSI_CMD_UNNEED_RSP
            DBG_WRN('snack for task(%d) R_data(RegRun:%d, RunLength:%d)' % (itt, beg_run, run_len))
    else:
        Reject(conn, req, rsp, REJECT_SNACK_REJECT, True)
        DBG_WRN('snack failed, unknown type(%d)' % type)  
    return ret


#=======================================================
#                 SCSI Request
#=======================================================
def ScsiCmdReq(conn, req, cmd):
    '''
    @param conn: connect
    @param req: iscsi req
    @param cmd: scsi request
    '''
    conn.CurCmdSN = conn.session.next_cmdsn()
    req.bhs[0] = ISCSI_OP_SCSI_CMD                              # opcode
    req.set_lun(cmd.lun)                                        # Lun
    req.set_itt(cmd.id)                                         # ITT
    req.set_exp_len(cmd.exp_len)                                # ExpDataLen
    req.set_cmdsn(conn.CurCmdSN)                                # CmdSN
    req.set_exp_statsn(conn.next_statsn())                        # ExpStatSN
    req.bhs[32:] = cmd.cdb[:]                                   # CDB

    if cmd.out_buf:
        req.data = cmd.out_buf[:cmd.next_len]
        req.set_data_len(cmd.next_len)
        req.bhs[1] = (0x80 | 0x01 << 5 | cmd.attr) & 0xFF       
    else:
        req.bhs[1] = (0x80 | 0x01 << 6 | cmd.attr) & 0xFF

#=======================================================
#                 SCSI response
#=======================================================
SCSI_RSP_FLA_READ_OVERFLOW   = 0x10
SCSI_RSP_FLA_READ_UNDERFLOW  = 0x80
SCSI_RSP_FLA_WRITE_OVERFLOW  = 0x40
SCSI_RSP_FLA_WRITE_UNDERFLOW = 0x20

def F_BIT(pdu):
    return (pdu.bhs[1] & 0x80)
def W_BIT(pdu):
    return (pdu.bhs[1] & 0x20)
def R_BIT(pdu):
    return (pdu.bhs[1] & 0x40)

def ScsiCmdRsp(conn, req, rsp):
    import tagt.cache as cah
    from scsi.scsi_lib import IS_READ, IS_WRITE
    cmd = None
    s = conn.session
    ret = ISCSI_CMD_NEED_RSP

    if check_cmd(conn, req) == False:
        DBG_WRN('scsi command check FAILED')
        return ISCSI_CMD_UNNEED_RSP

    # check read/write command & flags
    code = SCSI_CODE(req)
    if (IS_READ(code) and R_BIT(req) == 0) or \
       (IS_WRITE(code) and W_BIT(req) == 0):
        Reject(conn, req, rsp, REJECT_PROTOCOL_ERROR, True)
        DBG_WRN('detect flags invalid in scsi request pdu')
        return ret

    #---------------------------------------------------------------------------
    #
    # checking as following rules:
    #
    # 1. ImmediateData = No but receive ImmediateData, Reject it
    #    iol-ffp 16.3.4 SCSI Response Unexpected Unsolicited Data ask to set scsi sense 
    #    iol-mc 2.6.2 ImmediateData=No Across Two Connections  ask to reject 
    #    which one is suitable?
    # 
    # 2. ImmediateData = Yes but receive ImmediateData > FirstBurstLength, set scsi sense
    #    iol iol-ffp 16.3.2 SCSI Response Excess Immediate Data ask to set scsi sense
    #
    #---------------------------------------------------------------------------

    # ImmediateData
    if s.ImmediateData.value == False and req.data:

        # Reject(conn, req, rsp, REJECT_PROTOCOL_ERROR, True)
        # DBG_WRN('detect immediateData in session:%s, but not allowed.'%str(s.sid))
        # return ret

        cmd = slib.ScsiCmd(conn, req)
        cmd.set_sense(slib.SAM_STAT_CHECK_CONDITION, slib.ILLEGAL_REQUEST, 0x0C0C)
        cmd.state = cah.SCSI_TASK_FINISH
        DBG_WRN('detect immediateData in session:%s, but not allowed.'%str(s.sid))

    # FirstBurstLength
    elif (s.ImmediateData.value and 
          req.data and 
          len(req.data) > s.FirstBurstLength.value):

        # Reject(conn, req, rsp, REJECT_PROTOCOL_ERROR, True)
        # DBG_WRN('detect immediateData(%d) is large than FirstBurstLength(%d).' % (len(req.data), s.FirstBurstLength.value))
        # return ret

        cmd = slib.ScsiCmd(conn, req)
        cmd.set_sense(slib.SAM_STAT_CHECK_CONDITION, slib.ILLEGAL_REQUEST, 0x0C0C)
        cmd.state = cah.SCSI_TASK_FINISH
        DBG_WRN('detect immediateData(%d) is large than FirstBurstLength(%d).' %
                 (len(req.data), s.FirstBurstLength.value))

    # execute request
    else:
        # check read/write command & flags
        code = SCSI_CODE(req)
        if (IS_READ(code) and R_BIT(req) == 0) or (IS_WRITE(code) and W_BIT(req) == 0):
            Reject(conn, req, rsp, REJECT_PROTOCOL_ERROR, True)
            DBG_WRN('detect flags invalid in scsi request pdu')
            return ret

        # CmdSN are incremented by 1 for every non-immediate command 
        if IS_IMMEDIATE(req):
            conn.CurExpCmdSn = s.ExpCmdSn
        else:
            conn.CurExpCmdSn = s.next_exp_cmdsn()

        DBG_CMD(slib.SCSI_DESC(req.bhs[32:32 + 16]), 'LUN:%d' % req.bhs[9])
        cmd = s.scsi_cmd_list.cmd_request(conn, req)

    if cmd.state == cah.SCSI_TASK_RECEIVE or\
       cmd.state == cah.SCSI_TASK_FREE:
        ret = ISCSI_CMD_UNNEED_RSP
    elif cmd.state == cah.SCSI_TASK_R2T:
        R2TRsp(conn, rsp, cmd)
    elif cmd.state == cah.SCSI_TASK_FINISH:
        ScsiRsp(conn, req, rsp, cmd.status)
        if cmd.status:
            if cmd.sense:
                rsp.data = cmd.sense
                rsp.set_data_len(len(rsp.data))
        cmd.state = cah.SCSI_TASK_FREE
    else:
        raise 'scsi command execute abnormally!'

    return ret
