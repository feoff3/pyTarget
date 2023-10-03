from web.main import CMD_LINE, TB, TR, TD
from iscsi.iscsi_comm import sid_decode
from comm.stdlib import *

def Connect_Page(server):
    from tagt.main import TM
    args = server.cmds
    ret = True
    buf = ''

    try:
        if args[1] == 'delete':
            from iscsi.iscsi_lib import ISCSI_TARGET_STOP
            sid = sid_decode(args[4])
            cid = atoi(args[5])    
            t = TM.find_target(args[2])
            h = t.find_host(args[3])
            s = h.find_session(sid)
            c = s.find_conn(cid)
            c.state = ISCSI_TARGET_STOP
            c.Stop()
            buf = 'Delete connect(%s) from session(%s) ' %(args[5], args[3])

        elif args[1] == 'ls':
            TM.lock()
            buf += CMD_LINE
            buf += TB(1)
            buf += TR(TD('Target', 1) + TD('Host', 1) + TD('Session', 1) + TD('Connection (cid, address)', 1))
            for t in TM.target_list:
                buf += TR(TD(t.name) + TD() + TD() + TD())
                t.host_list_lock.acquire()
                for h in t.host_list:
                    buf += TR(TD() + TD(h.name) + TD() + TD())
                    h.session_list_lock.acquire()
                    for s in h.session_list:
                        buf += TR(TD() + TD() + TD(str(s.sid)) + TD())
                        s.conn_list_lock.acquire()
                        for c in s.conn_list:
                            buf += TR(TD() + TD() + TD() + TD('%d %s:%s' % (c.cid, c.sock.client_addr()[0],c.sock.client_addr()[1])))
                        s.conn_list_lock.release()
                    h.session_list_lock.release()
                t.host_list_lock.release()
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