from web.main import CMD_LINE, TB, TR, TD
from scsi.scsi_simulator import TestCase
from comm.stdlib import *

def Simulator_Page(server):
    from tagt.main import TM
    args = server.cmds
    ret = True
    buf = ''
    
    try:
        if args[1] == 'add':
            t = TM.find_target(args[2])
            h = t.find_host(args[3])
            l = h.find_lun(atoi(args[4])) 
            tc = TestCase(str_2_value(args[5]), str_2_value(args[6]), str_2_value(args[7]), str_2_value(args[8]), str_2_value(args[9]), str_2_value(args[10]))
            ret = l.AddTestCase(tc)
            buf = 'Add testcase(%s,%s,%s,%s,%s,%s) into scsi lun(%d) ' % (args[5],args[6],args[7],args[8],args[9],args[10],l.id)
            ret = True
        elif args[1] == 'delete':
            buf = 'Delete testcase (not supported now)'
            ret = False
        elif args[1] == 'clear':
            TM.lock()
            for t in TM.target_list:
                t.host_list_lock.acquire()
                for h in t.host_list:
                    h.lun_list_lock.acquire()
                    for l in h.lun_list:
                        l.ResetTestCase()
                    h.lun_list_lock.release()
                t.host_list_lock.release()
            TM.unlock() 
            buf = 'Clear all testcase'
        elif args[1] == 'ls':
            TM.lock()
            buf += CMD_LINE
            buf += TB(1)
            buf += TR(TD('Target', 1) + TD('Host', 1) + TD('Lun', 1) + TD('Simulator (type, lba, len, count, start_count), interval_count', 1))
            for t in TM.target_list:
                buf += TR(TD(t.name) + TD() + TD() + TD())
                t.host_list_lock.acquire()
                for h in t.host_list:
                    buf += TR(TD() + TD(h.name) + TD() + TD())
                    h.lun_list_lock.acquire()
                    for l in h.lun_list:
                        buf += TR(TD() + TD() + TD('%d'%l.id) + TD())
                        l.tc_lock()
                        for tc in l.test_case:
                            buf += TR(TD() + TD() + TD() + TD('0x%x,0x%x,%d,%d,%d,%d' % (tc.type, tc.lba, tc.len, tc.count, tc.start_count, tc.interval)))
                        l.tc_unlock()   
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