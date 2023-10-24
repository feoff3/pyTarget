#    
#    general iscsi APIs for iscsi_lib
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#

import random
from iscsi.iscsi_proto import *
from comm.stdlib import *
from comm.debug import *


def ERL_VAL(conn):
    return conn.session.ErrorRecoveryLevel.value
def MBL_VAL(conn):
    return conn.session.MaxBurstLength.value
def FBL_VAL(conn):
    return conn.session.FirstBurstLength.value
def MRDSL_VAL(conn):
    return conn.MaxRecvDataSegmentLength.value
def IMD_VAL(conn):
    return conn.session.ImmediateData.value


def get_key_val(pdu, key):
    '''
    @return: None for not exist
             Reject for detecting multiply same keys
             other for success
    '''
    beg = pdu.data.find(key)
    if beg < 0:
        return None
    end = pdu.data.find('\x00', beg + len(key) + 1)
    if end < 0:
        return pdu.data[beg + len(key) + 1:]
    if pdu.data[end:].find(key) >= 0:
        return 'Reject' 
    return pdu.data[beg + len(key) + 1:end]


def set_key_val(pdu, key, val):
    '''
    add key value pair into pdu
    '''
    buf = None
    if type(val) is type(''):
        buf = '%s=%s\0' % (key, val)
    elif type(val) is type(0):
        buf = '%s=%d\0' % (key, val)
    elif type(val) is type(True):
        buf = '%s=%s\0' % (key, bool_2_str(val))
    if buf:
        pdu.data += buf
        pdu.set_data_len(pdu.get_data_len() + len(buf))


def get_sid(pdu):
    '''
    get session id
    '''
    from iscsi.iscsi_lib import SessionID
    sid = SessionID()
    sid.isid = pdu.bhs[8:14]
    sid.tsih = array_2_hex(pdu.bhs, 14, 2)
    return sid


def build_challenge():
    '''
    build challenge message for chap
    '''
    ret = []
    for i in range(1024):
        ret.append(random.randint(0, 0xff));
    return ret


def get_challenge(s):
    '''
    decode challenge message
    '''
    lst = []
    for i in range(len(s)//2):
        lst.append(str_2_value(s[2*i])*16 + str_2_value(s[2*i+1]))
    if len(s) % 2:
        lst.append(str_2_value(s[-1]))
    return do_pack(lst)


def decode_address(addr):
    '''
    decode target address
    as: 10.0.0.1:3260,1
    '''
    off_a = addr.find(':')
    off_p = addr.find(',')

    if off_a == -1 or off_p == -1:
        return None, None, None
    else:
        return addr[:off_a], atoi(addr[off_a+1:off_p]), atoi(addr[off_p+1:])
   

def sid_decode(buf):
    '''
    session id decode
    as: 400001370000-0002
    '''
    from iscsi.iscsi_lib import SessionID
    sid = SessionID()
    i = 0
    isid = []
    while i < 12:
        isid.append(str_2_value('0x'+buf[i:i+2]))
        i += 2
    sid.isid = tuple(isid)
    sid.tsih = str_2_value('0x' + buf[13:])
    return sid


def find_key_list(lst, key):
    return key in lst.split(',')


def get_key_pair(pdu):
    '''
    get key value pair
    '''
    key_pair = {}
    pair = pdu.data.split('\0')
    for item in pair:
        if '=' in item:
            key, val = item.split('=')
            if key in key_pair:
                val = 'Reject'
        elif item:
            # test request is continue
            if (OPCODE(pdu) == ISCSI_OP_TEXT and pdu.bhs[1] & 0x40):
                continue
            else:
                key = item ; val = 'Reject'
        else:
            continue
        key_pair.update({key:val})
    return key_pair


def get_residual(conn, cmd):
    '''
    calculate scsi residual value
    '''
    import scsi.scsi_lib as slib

    residual = 0
    if cmd.out_buf:
        spdtl = len(cmd.out_buf)
        edtl = cmd.pdu.get_exp_len()
        residual = slib.ALLOCATE_LEN(cmd.cdb)
        if residual >= 0:
            residual = edtl - spdtl
        else:
            residual = 0
    return residual


def r2t_offset(conn, cmd, r2tsn):
    '''
    calculate r2t_offset by r2tsn
    '''
    s = conn.session
    if s.ImmediateData.value:
        if s.InitialR2T.value:
            fbl = len(cmd.pdu.data)
        else:
            fbl = s.FirstBurstLength.value
    else:
        if s.InitialR2T.value:
            fbl = 0
        else:
            fbl = s.FirstBurstLength.value
    offset = fbl + r2tsn * conn.session.MaxBurstLength.value 
    return offset


def r2t_roll_back(conn, cmd, r2tsn):
    '''
    roll back cmd with r2tsn
    '''
    limit = conn.session.MaxBurstLength.value
    offset = r2t_offset(conn, cmd, r2tsn)
    cmd.in_buf = cmd.in_buf[:offset]
    cmd.r2t_sn = r2tsn
    cmd.next_len = min(cmd.all_len - offset, limit)


def check_cmd(conn, req):
    '''
    check scsi request in range (exp_cmd_sn, max_cmd_sn), cmd_retry etc
    @return: True for a new test
             False for a exist task, ignore this request.  
    '''
    ret = True
    s = conn.session
    cmd_sn = req.get_cmdsn()
    exp_cmd_sn = s.ExpCmdSn
    limit = 3

    if exp_cmd_sn < 0:
        exp_cmd_sn = 0
    max_cmd_sn = exp_cmd_sn + s.cmd_wnd_size()

    # command is out of range.
    if max_cmd_sn > 0xffffffff:
        if (cmd_sn > (max_cmd_sn - 0xffffffff + limit) and
            cmd_sn < exp_cmd_sn + limit):
            DBG_WRN('scsi CmdSN(0x%x) out of range' % cmd_sn)
            return False
    else:
        if (cmd_sn < exp_cmd_sn - limit or
            cmd_sn > max_cmd_sn + limit):
            DBG_WRN('scsi CmdSN(0x%x) out of range' % cmd_sn)
            return False

    if IS_IMMEDIATE(req):
        return True

    # check retry command
    lst = s.scsi_cmd_list
    lst.lock()
    for item in lst.list:
        if item.pdu.get_cmdsn() == cmd_sn:
            DBG_WRN('detect duplicate scsi command CmdSN(0x%x)' % cmd_sn)
            ret = False
            break
    lst.unlock()
    return ret

