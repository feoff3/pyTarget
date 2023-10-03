from web.main import CMD_LINE, TB, TR, TD
from tagt.session import Session

def Session_Page(server):
    from tagt.main import TM
    args = server.cmds
    ret = True
    buf = ''

    try:
        if args[1] == 'ls':
            TM.lock()
            buf += CMD_LINE
            buf += TB(1)
            buf += TR(TD('Target', 1) + TD('Host', 1) + TD('Session', 1))
            for t in TM.target_list:
                buf += TR(TD(t.name) + TD() + TD())
                t.host_list_lock.acquire()
                for h in t.host_list:
                    buf += TR(TD() + TD(h.name) + TD())
                    h.session_list_lock.acquire()
                    for s in h.session_list:
                        buf += TR(TD() + TD() + TD(str(s.sid)))
                    h.session_list_lock.release()
                t.host_list_lock.release()
            buf += TB()
            TM.unlock()
            server.Send_HttpHeader()
            server.Send_Data(buf)
            return

        elif args[1] == 'task':
            TM.lock()
            buf += CMD_LINE
            buf += TB(1)
            buf += TR(TD('Target', 1) + TD('Host', 1) + TD('Session', 1) + TD('Task', 1))
            
            for t in TM.target_list:
                buf += TR(TD(t.name) + TD() + TD() + TD())
                t.host_list_lock.acquire()
                for h in t.host_list:
                    buf += TR(TD() + TD(h.name) + TD() + TD())
                    h.session_list_lock.acquire()
                    for s in h.session_list:
                        buf += TR(TD() + TD() + TD(str(s.sid)) + TD())
                        s.scsi_cmd_list.lock()
                        for cmd in s.scsi_cmd_list.list:
                            buf += TR(TD() + TD() + TD() + TD('task(0x%x) %d' % (cmd.id, cmd.state)))
                        s.scsi_cmd_list.unlock()
                    h.session_list_lock.release()
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