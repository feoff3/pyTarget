from web.main import CMD_LINE, TB, TR, TD
from tagt.host import Host

def Host_Page(server):
    from tagt.main import TM
    args = server.cmds
    ret = True
    buf = ''

    try:
        if args[1] == 'add':
            tg = TM.find_target(args[2])
            h_name = args[3]
            if len(args) > 4:
                t_pwd = args[4]
            else:
                t_pwd = ''
            if len(args) > 5:
                i_pwd = args[5]
            else:
                i_pwd = ''
            h = Host(h_name, t_pwd, i_pwd)
            ret = tg.add_host(h)
            buf = 'Add host %s into target %s ' % (args[3], args[2])
    
        elif args[1] == 'setpassword':
            tg = TM.find_target(args[2])
            h = tg.find_host(args[3])
            if len(args) > 4:
                t_pwd = args[4]
            else:
                t_pwd = ''
            if len(args) > 5:
                i_pwd = args[5]
            else:
                i_pwd = ''
            h.target_pwd = t_pwd
            h.initiator_pwd = i_pwd
            buf = 'Modify host %s password ' % args[3]
    
        elif args[1] == 'delete':
            tg = TM.find_target(args[2])
            ret = tg.del_host(args[3])
            buf = 'Delete host %s from target %s ' % (args[3], args[2])
    
        elif args[1] == 'rename':
            tg = TM.find_target(args[2])
            if tg.find_host(args[3]):
                buf = 'host name %s exist'
                ret = False
            else:
                h = tg.find_host(args[3])
                buf = 'Rename host %s to %s ' % (h.name, args[4])
                h.name = args[4]
        
        elif args[1] == 'ls':
            TM.lock()        
            buf += CMD_LINE
            buf += TB(1)
            buf += TR(TD('Target', 1) + TD('Host', 1))
            for t in TM.target_list:
                buf += TR(TD(t.name) + TD())
                t.host_list_lock.acquire()
                for h in t.host_list:
                    buf += TR(TD() + TD(h.name))
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
