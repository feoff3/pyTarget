#    
#    iscsi error recovery implementation Code.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-02-8)
#
from iscsi.iscsi_comm import *
from comm.debug import *

# pdu state type
PDU_STATE_GOOD                              = 0x00
PDU_STATE_SOCK_FAILED                       = 0x01
PDU_STATE_HEAD_FAILED                       = 0x02
PDU_STATE_DATA_FAILED                       = 0x03
PDU_STATE_PADDING_FAILED                    = 0x04
PDU_STATE_FORMAT_FAILED                     = 0x05


def iscsi_do_recovery(conn, req):
    '''
    process iscsi error recover
    @param conn: iscsi connection
    @param req: iscsi pdu or error number.
    @return: True for ER success, need to continue receive
             False, will terminate connection.
    '''
    from iscsi import iscsi_lib as isc

    #
    # initiator socket failed (exit connect)
    # return False for terminate corrent connection.
    #
    if req.state == PDU_STATE_SOCK_FAILED:
#        DBG_WRN('Peer socket is invalid.')
        return False
    #
    # header receive/digest failed(ignore request)
    # return True and go on receive iscsi pdu.
    #
    elif req.state == PDU_STATE_HEAD_FAILED:
        DBG_WRN('detect header digest error, ignore this request')
        return True
    #
    # data receive/digest failed(reject pdu)
    # if data_out pdu, need to do r2c recover
    #
    elif req.state == PDU_STATE_DATA_FAILED:
        rsp = isc.PDU()
        if conn.Digest & DIGEST_DATA:
            isc.Reject(conn, req, rsp, isc.REJECT_DATA_DIGEST_ERROR, True)
        else:
            isc.Reject(conn, req, rsp, isc.REJECT_PROTOCOL_ERROR, True)
        DBG_WRN('detect iscsi pdu data invaild, reject request')
        conn.send(rsp)
        if OPCODE(req) == ISCSI_OP_SCSI_DATA_OUT:
            cmd = conn.session.scsi_cmd_list.find(req.get_itt())
            if cmd and cmd.r2t_sn:
                iscsi_r2t_rsecovery(conn, cmd)
        return True
    #
    # iscsi pdu padding failed (reject pdu)
    # if data_out pdu, need to do r2c recover
    #
    elif req.state == PDU_STATE_PADDING_FAILED:
        rsp = isc.PDU()
        isc.Reject(conn, None, rsp, isc.REJECT_PROTOCOL_ERROR)
        DBG_WRN('detect iscsi pdu padding error, reject request')
        conn.send(rsp)
        return True
    #
    # bhs format failed(exit connect)
    # stop current connect and wait for reset.
    #
    elif req.state == PDU_STATE_FORMAT_FAILED:
        conn.state = isc.ISCSI_LOGOUT_PHASE
        conn.clear_task()
        conn.Stop()
        DBG_WRN('detect pdu format error, reset current connect(%d)' % conn.cid)
        return False


def iscsi_data_recovery(conn, cmd, beg_run, run_len):
    '''
    retransmit data pdu. maybe call by snack.
    '''
    from iscsi.iscsi_lib import PDU, DataIn

    # run_len is 0 should retransmit all data-ins.
    buf = cmd.out_buf
    length = len(buf)
    limit = conn.PerMaxRecvDataSegmentLength.value
    if run_len == 0:
        run_len = (length + limit - 1) // limit
    offset = beg_run * limit
    residual = get_residual(conn, cmd)
    length -= offset
    DBG_WRN('Snack for retransmit DataIn(RegRun=%d, RunLength=%d) form task(%d)' % (beg_run, run_len, cmd.id))

    # backup StatSN
    stat_sn = conn.StatSN

    while run_len > 0:
        rsp = PDU()
        DataIn(conn, cmd.pdu, rsp, buf[offset : offset+min(limit,length)],
               length<=limit, offset, residual)
        if length <= limit:
            rsp.set_statsn(cmd.pdu.get_exp_statsn())
        conn.sock.send(rsp, conn.Digest)                # do not backup these pdus
        offset += min(length, limit)
        length -= min(length, limit)
        run_len -= 1

    # recover StatSN
    conn.StatSN = stat_sn
    if run_len != 0:
        DBG_WRN('detect RunLen field of sanck data invalid.')


def iscsi_data_ack_recovery(conn, cmd):
    from iscsi.iscsi_lib import PDU, DataIn

    buf = cmd.out_buf
    length = len(buf)
    limit = conn.PerMaxRecvDataSegmentLength.value
    data_sn = (length + limit - 1) // limit - 1
    if data_sn < 0:
        data_sn = 0
    offset = data_sn * limit
    residual = get_residual(conn, cmd)
    length -= offset
    DBG_WRN('Snack for retransmit DataAck form task(%d)' % cmd.id)
    rsp = PDU()
    DataIn(conn, cmd.pdu, rsp, buf[offset : offset+length],
           True, offset, residual)
    rsp.set_statsn(cmd.pdu.get_exp_statsn())
    conn.sock.send(rsp, conn.Digest)                # do not backup these pdus


def iscsi_status_recovery(conn, beg_run, run_len):
    '''
    process snack status
    '''
    from iscsi import iscsi_lib as isc
    lst = conn.pdu_list
    rsp_cnt  = 0

    if run_len:
        rsp = lst.find_statsn(beg_run)
        if rsp == None:
            DBG_WRN('snack status(StatSN=%d) not exist.' % beg_run)
        else:
            conn.sock.send(rsp, conn.Digest)
    else:
        lst.lock()
        for item in lst.list:
            if item.get_statsn() >= beg_run:
                conn.sock.send(item, conn.Digest)
                rsp_cnt += 1
        lst.unlock()
        if rsp_cnt == 0:
            rsp = isc.PDU()
            isc.Reject(conn, None, rsp, isc.REJECT_SNACK_REJECT)
            conn.sock.send(rsp, conn.Digest)


def iscsi_task_recovery(conn, itt, sn):
    '''
    process task recovery or task reassign.
    call by task management.
    '''
    from tagt import cache as ch
    from iscsi import iscsi_lib as isc
    from scsi import scsi_lib as sc

    lst = conn.session.scsi_cmd_list
    cmd = lst.find(itt)

    if cmd == None:
        DBG_WRN('Task recover FAILED(not found cmd(%d))' % itt)
        return False
    else:
        cmd.state = ch.SCSI_TASK_RECOVERY

    if sc.IS_IN_IOCMD(cmd.cdb[0]):
        buf = cmd.out_buf
        limit = conn.PerMaxRecvDataSegmentLength.value
        offset = sn * limit
        length = len(buf) - offset
        residual = get_residual(conn, cmd)

        # task management can about scsk task, and set
        # cmd.state to SCSI_TASK_FREE.
        while (length > 0 and
               cmd.state != ch.SCSI_TASK_FREE):
            rsp = isc.PDU()
            isc.DataIn(conn, cmd.pdu, rsp, buf[offset:offset+min(limit,length)], length<=limit, offset, residual)
            conn.sock.send(rsp, conn.Digest)    # needn't backup these pdus
            offset += min(length, limit)
            length -= min(length, limit)
        cmd.state = ch.SCSI_TASK_FREE
    elif sc.IS_OUT_IOCMD(cmd.cdb[0]):
        # roll back task buffer, and continue receiving data.
        r2t_roll_back(conn, cmd, cmd.r2t_sn)
        rsp = isc.PDU()
        isc.R2TRsp(conn, rsp, cmd)
        conn.sock.send(rsp, conn.Digest)        # needn't backup this pdu
    else:
        pass
    return True

def iscsi_r2t_rsecovery(conn, cmd):
    '''
    r2t recovery
    '''
    from iscsi.iscsi_lib import PDU, R2TRsp
    r2t_roll_back(conn, cmd, cmd.r2t_sn - 1)
    rsp = PDU()
    R2TRsp(conn, rsp, cmd)
    conn.send(rsp)

def set_retain_time(conn):
    '''
    set task retain time, when logout connect for recovery, 
    remember to invoke me!
    '''
    import datetime
    lst = conn.session.scsi_cmd_list
    lst.lock()
    for item in lst.list:
        if item.connect == conn:
            item.retain_time = datetime.datetime.now()
    lst.unlock()
    
def is_active(conn, cmd):
    '''
    if task still active,
    '''
    import datetime
    #
    # if a connect logout for recovery, 
    # all cmds that belong to it will set retain_time
    #
    if cmd.retain_time == None:
        return False

    limit = conn.session.DefaultTime2Retain.value
    start = cmd.retain_time 
    now = datetime.datetime.now()
    if (now - start).seconds <= limit:
        return True
    return False
