#    
#    Cache for target scsi task, iscsi task
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-26)
#    Modify by Wu.Qing-xiu (2010-4-10)
#

from scsi.scsi_lib import *
from iscsi.iscsi_lib import *
from comm.comm_list import *
import threading
from Queue import Queue
#
# scsi task status
#
SCSI_TASK_FINISH                        = 0x01  # task finish
SCSI_TASK_RECEIVE                       = 0x02  # task need to receive more data
SCSI_TASK_R2T                           = 0x03  # task need to send r2t and go on receive data
SCSI_TASK_RECOVERY                      = 0x04  # task need to do error recovery
SCSI_TASK_FREE                          = 0x05  # task resource can be free


class TagtCache(List):
    '''
    class for target scsi task and iscsi task cahce.
    @note: all scsi task item pushed into cache must hold an unique id
    '''
    def __init__(self , read_pool_numthreads = 16):
        '''
        cache constructor
        '''
        List.__init__(self)
        self.read_ready_list = list()
        self.read_pool_threads = list()
        self.read_pool_numthreads = read_pool_numthreads
        self.read_ops_queue = Queue(self.read_pool_numthreads*2)
        for i in range(0, self.read_pool_numthreads):
            thr = threading.Thread(target = self._read_worker)
            thr.start()
            self.read_pool_threads.append(thr)
        #self._handle_read , args=(conn,req,cmd,cmdsn,)

    def __del__(self):
        for i in range(0, self.read_pool_numthreads):
            self.read_ops_queue.put(None)

    def push_pdu(self, pdu):
        '''
        push a iscsi pdu into command_list
        @param pdu: iscsi pdu
        '''
        self.lock()
        self.list.append(pdu)
        self.unlock()


    def pop_pdu(self, id):
        '''
        find the iscsi pdu, and pop it.
        @param id: InitiatorTaskTag field of pdu
        @return: None for failed, other for success
        '''
        ret = None
        self.lock()
        for item in self.list:
            if item.get_itt() == id:
                ret = item
                self.list.remove(item)
                break
        self.unlock()
        return ret


    def find_pdu(self, id):
        '''
        find a iscsi pdu
        @param id: InitiatorTaskTag field of pdu
        @return: None for failed, other for success
        '''
        ret = None
        self.lock()
        for item in self.list:
            if item.get_itt() == id:
                ret = item
                break
        self.unlock()
        return ret


    def find_statsn(self, sn):
        '''
        find a iscsi pdu by stat_sn
        @param sn: pdu StatSN
        @return: None for failed, other for success
        '''
        ret = None
        self.lock()
        for item in self.list:
            if item.get_statsn() == sn:
                ret = item
                break
        self.unlock()
        return ret

    def _read_worker(self):
        while True:
            item = self.read_ops_queue.get()
            if not item:
                break
            self._handle_read(item[0], item[1], item[2], item[3])
            self.read_ops_queue.task_done()
        print("Read worker stopped")


    def _handle_read_buff(self, conn, req, cmd, cmdsn , buf):
        if cmd:
            if buf:
                spdtl = len(buf)
                edtl = req.get_exp_len()
                alloc = ALLOCATE_LEN(cmd.cdb)
                if alloc >= 0:
                    spdtl = min(alloc, spdtl)
                residual = edtl - spdtl
                length = min(edtl, spdtl, MBL_VAL(conn))
                limit = conn.PerMaxRecvDataSegmentLength.value
                offset = 0

                # if cmd status is not SAM_STAT_GOOD,
                # finial data pdu do not contain scsi status
                status = (cmd.status == SAM_STAT_GOOD)

                # task management can about scsk task, and set
                # cmd.state to SCSI_TASK_FREE.
                while (length > 0):
                    rsp = PDU()
                    pdu_len = min(length, limit)
                    DataIn(conn, req, rsp, buf[offset:offset+pdu_len], length<=limit, offset, residual, status)
                    #print("Passed ExpCmdSn:" +str(cmdsn)+ "PDU ExpCmdSn: " + str(rsp.get_exp_cmdsn()))
                    conn.send(rsp)
                    offset += pdu_len
                    length -= pdu_len
                #print("Read cmdsn " + str(cmdsn) + " result sent")

    def _handle_read(self, conn, req, cmd, cmdsn):
        try:
            exe_scsi_cmd(cmd)
            buf = cmd.out_buf
            #print("Read cmdsn " + str(cmdsn) + " complete")
            self.read_ready_list.append((conn, req, cmd, cmdsn , buf))
            return True
        except:
            DBG_EXC()
        return False

    def handle_read_async(self, conn, req, cmd, cmdsn):
        try:
            self.read_ops_queue.put((conn, req, cmd, cmdsn))
        except:
            DBG_EXC()
        self.process_async_read_requests()
        cmd.status = SAM_STAT_GOOD
        return True

    def handle_read_sync(self, conn, req, cmd, cmdsn):
        res = False
        try:
            res = self._handle_read(conn, req, cmd, cmdsn)
        except:
            DBG_EXC()
        if res:
            cmd.status = SAM_STAT_GOOD
        self.process_async_read_requests()
        return res

    def process_async_read_requests(self):
        # feoff: I belive this should be thread-safe
        temp_list = self.read_ready_list[:]
        for op in temp_list:
            if op[4]:
                self._handle_read_buff(op[0], op[1], op[2] , op[3] , op[4])
            else:
                conn = op[0]; req = op[1]; cmd = op[2]
                rsp = PDU()
                ScsiRsp(conn, req, rsp, cmd.status, 0)
                rsp.data = ''
                #
                # sense valid, set sense data
                #
                if cmd.status != SAM_STAT_GOOD:
                    if cmd.sense:
                        rsp.data = cmd.sense
                        rsp.set_data_len(len(rsp.data))
                conn.send(rsp)
                cmd.state = SCSI_TASK_FREE
        for op in temp_list:
            self.read_ready_list.remove(op)
        #print("Read list size " + str(len(self.read_ready_list)))

    def cmd_request(self, conn, req):
        '''
        process iscsi I/O command request
        @param conn: iscsi connect
        @param req: iscsi request pdu
        @return: scsi command (with cmd.state)
        '''

        # clear all scsi tasks which have been acked.
        self.cmd_ack(conn, req)

        # build scsi task
        sess = conn.session
        cmd = ScsiCmd(conn, req)
        self.push(cmd)
        residual = 0

        #
        # reading command task
        #
        if IS_IN_IOCMD(cmd.cdb[0]):
            if not IS_READ(cmd.cdb[0]):
                if self.handle_read_sync(conn, req, cmd, conn.CurExpCmdSn):
                    if cmd.status == SAM_STAT_GOOD:
                        cmd.state = SCSI_TASK_FREE
                    return cmd

            #TODO: go into async mode only if there are several requests inside of the socket
            #print("new read conn ExpCmdSn " + str(conn.CurExpCmdSn))
            if self.handle_read_async(conn, req, cmd, conn.CurExpCmdSn):
                #print("end read conn ExpCmdSn " + str(conn.CurExpCmdSn))
                # if cmd status is not SAM_STAT_GOOD,
                # scsi response will be send at the following code.
                if cmd.status == SAM_STAT_GOOD:
                    cmd.state = SCSI_TASK_FREE
                    return cmd

        #
        # writing command task
        #
        elif IS_OUT_IOCMD(cmd.cdb[0]):
            cmd.in_buf = req.data
            # not allow immediate data or first burst overflow
            if IMD_VAL(conn) == False and cmd.in_buf or \
               IMD_VAL(conn) == True  and cmd.in_buf and \
               FBL_VAL(conn) < len(cmd.in_buf):               
                cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x0C0C)
            elif cmd.all_len <= req.get_data_len():
                exe_scsi_cmd(cmd)
            else:
                if sess.InitialR2T.value:
                    cmd.next_len = min(cmd.all_len - len(cmd.in_buf), MBL_VAL(conn))
                    cmd.state = SCSI_TASK_R2T
                else:
                    if FBL_VAL(conn) <= len(cmd.in_buf):
                        cmd.next_len = min(cmd.all_len - len(cmd.in_buf), MBL_VAL(conn))
                        cmd.state = SCSI_TASK_R2T
                    else:
                        cmd.next_len = min(cmd.all_len - len(cmd.in_buf), FBL_VAL(conn) - len(cmd.in_buf))
                        cmd.state = SCSI_TASK_RECEIVE
                return cmd

        #
        # Not reading/writing command task
        #
        elif IS_NOT_IOCMD(cmd.cdb[0]):
            exe_scsi_cmd(cmd)           

        #
        # Finally handle 
        #
        rsp = PDU()
        ScsiRsp(conn, req, rsp, cmd.status, residual)
        rsp.data = ''

        #
        # sense valid, set sense data
        #
        if cmd.status != SAM_STAT_GOOD:
            if cmd.sense:
                rsp.data = cmd.sense
                rsp.set_data_len(len(rsp.data))
        conn.send(rsp)
        cmd.state = SCSI_TASK_FREE
        return cmd


    def data_request(self, conn, pdu):
        '''
        process scsi data request, if ready, execute it.
        @param conn: iscsi connect
        @param pdu: iscsi pdu
        @return: None for request not found (protocol error)
                 other for success
        '''
        id = pdu.get_itt()
        cmd = self.find(id)

        if cmd == None:
            DBG_WRN('Receive data-out pdu, but not found request (itt=0x%x)' % id)
            return None

        cmd.data_pdu.append(pdu)
        cmd.next_len -= pdu.get_data_len()

        cur_len = len(cmd.in_buf)
        for data in cmd.data_pdu:
            cur_len += data.get_data_len()

        if cur_len > cmd.all_len:
            self.pop(id)
            cmd.data_pdu = []
            cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x0C0D)
            cmd.state = SCSI_TASK_FINISH
            DBG_WRN('detect data buffer overflow(exp=%d, cur=%d)' % (cmd.all_len, cur_len))
        elif pdu.bhs[1] & 0x80 and cmd.next_len > 0:
            self.pop(id)
            cmd.data_pdu = []
            cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x0C0D)
            cmd.state = SCSI_TASK_FINISH
            DBG_WRN('receive final data-out pdu(itt=0x%x), but all of data is not enough.' % id)
        elif cmd.next_len < 0:
            self.pop(id)
            cmd.data_pdu = []
            cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x0C0D)
            cmd.state = SCSI_TASK_FINISH
            DBG_WRN('receive data-out pdu(itt=0x%x), but burst length is large than MaxBurstLentgh.' % id)
        elif cmd.next_len == 0:
            if self.data_offload(cmd) == False:
                # check fail:
                # 1. reject for iscsi response and 
                # 2. check condition for scsi response
                rsp = PDU()
                Reject(conn, None, rsp, REJECT_PROTOCOL_ERROR, False)
                conn.send(rsp)
                self.pop(id)
                cmd.data_pdu = []
                cmd.set_sense(SAM_STAT_CHECK_CONDITION, ILLEGAL_REQUEST, 0x0C0D)
                cmd.state = SCSI_TASK_FINISH
            else:
                cmd.data_pdu = []
                if cmd.all_len == len(cmd.in_buf):
                    self.pop(id)                
                    exe_scsi_cmd(cmd)
                    cmd.state = SCSI_TASK_FINISH 
                else:
                    cmd.next_len = min(MBL_VAL(conn), cmd.all_len - len(cmd.in_buf))
                    cmd.state = SCSI_TASK_R2T

        else:
            cmd.state = SCSI_TASK_RECEIVE
        return cmd

    def data_offload(self, cmd):
        '''
        offload all data-out pdu and
        check f_bit, data_sn, offset, etc... 
        @param md: scsi command
        @return: True for success
                 others need to reject and scsi response error.
        '''

        # check final data-out pdu
        f_bit = False
        for data in cmd.data_pdu:
            if data.bhs[1] & 0x80:
                f_bit = True
                break
        if f_bit == False:
            DBG_WRN('can not find final data-out pdu. (itt=%d)' % cmd.id)
            return False

        # check data_sn, offset
        find = True
        data_sn = 0
        offset = len(cmd.in_buf)
        while find and len(cmd.data_pdu):
            find = False
            for data in cmd.data_pdu:
                if data.get_data_sn() == data_sn:
                    if data.get_data_offset() != offset:
                        DBG_WRN('detect data-out invalid (data_sn=%d, offset=%d)' % (data_sn, data.get_data_offset()))
                        return False
                    cmd.in_buf += data.data
                    offset += len(data.data)
                    data_sn += 1
                    find = True
                    cmd.data_pdu.remove(data)
        if len(cmd.data_pdu) != 0:
            DBG_WRN('detect data-out losing (data_sn=%d, itt=%d)' % (data_sn, cmd.id))
            return False
        return True


    def cmd_ack(self, conn, req):
        '''
        Receive a acked pdu, 
        and free all scsi-tasks which have been acked.
        '''
        exp_statsn = req.get_exp_statsn()
        lst = conn.session.scsi_cmd_list
        lst.lock()
        for item in lst.list:
            if (item.pdu.get_exp_statsn() < exp_statsn and
                item.state == SCSI_TASK_FREE):
                lst.list.remove(item)
        lst.unlock()
