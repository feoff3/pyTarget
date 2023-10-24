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
from tagt.config import read_config
from comm.debug import *
from comm.dev_file import DevFile
import platform

# for media type mask (changes the behaviour of shared media)
# TODO: move to media.factory file
SOURCE_MEDIA_FILE                        = 0x0 
SOURCE_MEDIA_WINDEV_MASK                 = 0xF000
SOURCE_MEDIA_WINDRIVE                    = 0x1000
SOURCE_MEDIA_WINVOL                      = 0x2000
SOURCE_MEDIA_WINVOL_EMULATED_DISK_LAYOUT = 0x4000

#
# target pool
#
TM = TargetPool()

#
# returns DevFile object based on target media
# and lun xml description
#
def _create_target_media(l):
    windev = None
    if (l.media & SOURCE_MEDIA_WINDEV_MASK) > 0:
        if platform.system() == "Windows":
            import media.win_dev
            windev = media.win_dev.WinDev(l.path , l.media == SOURCE_MEDIA_WINDRIVE, True, True)
            if l.media == SOURCE_MEDIA_WINVOL_EMULATED_DISK_LAYOUT:
                import media.emulated_layout_dev
                #TODO: check parms format, return error
                filenames = l.parms.split(';')
                #TODO: check files are initialized
                header = DevFile(filenames[0])
                footer = DevFile(filenames[1])
                emulated_gpt = media.emulated_layout_dev.EmulatedLayoutDev(windev, header, footer)
                windev = emulated_gpt
        else:
            DBG_WRN('Windows device type specified for non-Windows system')
    if windev:
        d = windev
    else:
        d = DevFile(l.path) # generic file media
    d.dev_lock()
    tp = l.type & (~sp.TYPE_PROTECT_MASK)
    if tp == sp.TYPE_DISK:  ln = Disk(l.id, l.cap, d, l.physical_sector, l.logical_sector)
    elif tp == sp.TYPE_TAPE:    ln = Tape(l.id, l.cap, d)
    elif tp == sp.TYPE_ENCLOSURE:   ln = NEW_Enclosure(l.id, d)
    else:ln = Lun(l.id, l.type, d)
    return ln

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
                ln = _create_target_media(l)
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