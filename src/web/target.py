#    
#    target web page
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-02-18)
#

from web.main import CMD_LINE, TB, TR, TD
from tagt.target import Target
from comm.stdlib import *

def Target_Page(server):
    '''
    handle target request
    '''
    from tagt.main import TM
    args = server.cmds
    ret = True
    buf = ''

    try:
        if args[1] == 'ls':
            TM.lock()
            buf = CMD_LINE
            buf += TB(1)
            buf += TR(TD('Target Name', 1) + TD('Target Address', 1))
            for item in TM.target_list:
                buf += TR(TD(item.name) + TD())
                for a in item.addr:
                    buf += TR(TD() + TD(a))
            buf += TB()
            TM.unlock()
            server.Send_HttpHeader()
            server.Send_Data(buf)
            return True

        elif args[1] == 'add':
            tg = Target(args[2], args[3], atoi(args[4]), atoi(args[5]))
            ret = TM.add_target(tg)
            buf = 'Add target %s ' % args[2]
    
        elif args[1] == 'delete':
            tg = TM.find_target(args[2])
            tg.Stop()
            ret = TM.del_target(args[2])
            buf = 'Remove target %s ' % args[2]
    
        elif args[1] == 'rename':
            tg = TM.find_target(args[2])
            tg.name = args[3]
            buf = 'Rename target from %s to %s ' % (args[2], args[3])
                    
        elif args[1] == 'stop':
            tg = TM.find_target(args[2])
            tg.Stop()
            buf = 'Stop target %s ' % args[2]
    
        elif args[1] == 'addaddress':
            tg = TM.find_target(args[2])
            tg.add_address(args[3], atoi(args[4]))
            addr = '%s:%s,%d' % (args[3], args[4], tg.portal)
            buf = 'Add target address (%s) into target (%s) ' % (addr, args[2])
    
        elif args[1] == 'deladdress':
            tg = TM.find_target(args[2])
            tg.del_address(args[3], atoi(args[4]))
            addr = '%s:%s,%d' % (args[3], args[4], tg.portal)
            buf = 'Delete target address (%s) from target (%s) ' % (addr, args[2])
    
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
