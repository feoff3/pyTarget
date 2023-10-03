#
#    iscsi target main function.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#

import os, comm.debug as debug
from iscsi.iscsi_sock import IscsiSock
from tagt.target import Target, TargetPool
from tagt.host import Host
from tagt.connect import Connect
from scsi.scsi_dev import Lun
from scsi.scsi_disk import Disk
from scsi.scsi_tape import Tape
from scsi import scsi_proto as sp
from scsi.scsi_enclosure import NEW_Enclosure
from config import read_config
from comm.debug import *

#
# target pool
#
TM = TargetPool()

#
# config target
#
def read_target_config(config):
    '''
    Read configure and build target
    '''
    # update console debug level
    debug.CURRENT_DEBUG_LEVEL = config.debug_level

    # add target/host/lun
    for t in config.target_list:
        tg = Target(t.name, t.ip, t.port, t.portal)
        tg.config = t.para
        TM.add_target(tg)

        # scan target's host
        for h in t.host:
            ht = Host(h.name, h.pwd_t, h.pwd_i)
            tg.add_host(ht)
            
            # scan host's lun
            for l in h.lun:
                tp = l.type & (~sp.TYPE_PROTECT_MASK)
                if tp == sp.TYPE_DISK:  ln = Disk(l.id, l.cap, l.path)
                elif tp == sp.TYPE_TAPE:    ln = Tape(l.id, l.cap, l.path)
                elif tp == sp.TYPE_ENCLOSURE:   ln = NEW_Enclosure(l.id, l.path)
                else:ln = Lun(l.id, l.type, l.path)
                ln.initial()
                ht.add_lun(ln)
                # protect type
                if l.type & sp.TYPE_PROTECT_MASK:
                    ln.set_protect()
    DBG_PRN('configure target done')


def Run(ip, port):
    '''
    Start to run
    '''
    DBG_INF('initialize finish, start to run ...')

    sock = IscsiSock(ip, port)
    if sock.initial() == False:
        DBG_WRN('iscsi service start FAILED, check if port(%d) has been used' % port)
        return

    while True:
        if sock.accept() == False:
            DBG_WRN('accept a client FAILED')
            return

        #
        # Create a new thread to handle it.
        # 
        conn = Connect(sock)
        threading.Thread(None, conn.Start).start()

###################################################################
#                             Main
###################################################################

def iscsi_target_service(isStop = None):
    DBG_INF('initialize virtual device, please wait...')
    config = read_config('config.xml')
    if config:
        read_target_config(config)
        Run(config.ip, config.port)