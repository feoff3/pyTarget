from web.main import CMD_LINE, TB, TR, TD
from scsi.scsi_disk import Lun, Disk
from scsi.scsi_tape import Tape
from scsi.scsi_comm import *
from comm.stdlib import *
from scsi.scsi_lib import UNIT_ATTENTION
from iscsi.iscsi_lib import ASYNC_EVENT_SENSE_DATA

def Lun_Page(server):
    from tagt.main import TM
    args = server.cmds
    ret = True
    buf = ''

    try:
        if (args[1] == 'adddisk' or
            args[1] == 'addtape' or
            args[1] == 'adddevice'):
            t = TM.find_target(args[2])
            h = t.find_host(args[3])
            if args[1] == 'adddisk':
                l = Disk(atoi(args[4]), atoi(args[5]), args[6])
                buf = 'Add disk(%s) into host(%s) ' % (args[4], args[3])
            elif args[1] == 'addtape':
                l = Tape(atoi(args[4]), atoi(args[5]), args[6])
                buf = 'Add Tape(%s) into host(%s) ' % (args[4], args[3])
            else:
                l = Lun(atoi(args[4]), atoi(args[5]), atoi(args[6]))
                buf = 'Add lun(%s) into host(%s) ' % (args[4], args[3])
            l.initial()
            ret = h.add_lun(l)
            h.update_event(ASYNC_EVENT_SENSE_DATA, UNIT_ATTENTION, 0x3F0E, 0)

        elif args[1] == 'delete':
            t = TM.find_target(args[2])
            h = t.find_host(args[3])
            ret = h.del_lun(atoi(args[4]))
            h.update_event(ASYNC_EVENT_SENSE_DATA, UNIT_ATTENTION, 0x3F0E, 0)
            buf = 'Remove lun(%s) from host(%s) ' % (args[4], args[3])

        elif args[1] == 'protect':
            t = TM.find_target(args[2])
            h = t.find_host(args[3])
            l = h.find_lun(atoi(args[4]))
            l.set_protect()
            h.update_event(ASYNC_EVENT_SENSE_DATA, UNIT_ATTENTION, 0x3F00, 0)
            buf = 'Change lun(%s) to protect at host(%s) ' % (args[4], args[3])

        elif args[1] == 'ls':
            TM.lock()
            buf += CMD_LINE
            buf += TB(1)
            buf += TR(TD('Target', 1) + TD('Host', 1) + TD('Lun (id,cap,path)', 1))
            for t in TM.target_list:
                buf += TR(TD(t.name) + TD() + TD())
                t.host_list_lock.acquire()
                for h in t.host_list:
                    buf += TR(TD() + TD(h.name) + TD())
                    h.lun_list_lock.acquire()
                    for l in h.lun_list:
                        if is_disk(l) or is_tape(l):
                            buf += TR(TD() + TD() + TD('%d,%d,%s'%(l.id, l.capacity, l.path)))
                        else:
                            buf += TR(TD() + TD() + TD('%d,%s'%(l.id, l.path)))
                    h.lun_list_lock.release()
                t.host_list_lock.release()
            buf += TB()
            TM.unlock()
            server.Send_HttpHeader()
            server.Send_Data(buf)
            return
        else:
            buf = 'unknown commands or parameters'
            ret = False
    except:
        server.Send_ErrData('unknown commands or parameters', '/')
        return
    if ret:
        server.Send_SuccData(buf, '/')
    else:
        server.Send_ErrData(buf, '/')
