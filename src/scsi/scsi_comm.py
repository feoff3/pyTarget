#    
#    general scsi APIs.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#

from comm.stdlib import *
import scsi.scsi_proto as sp


def __to_cylinder(addr):
    return (addr // 0x1000000) & 0xff

def __to_head(addr):
    return (addr // 0x10000) & 0xff

def __to_sector(addr):
    return (addr % 0x10000) & 0xffff

def __to_index(addr):
    return (addr % 0x10000) & 0xffff

def fmt_addr(fmt, addr):
    '''
    format addr
    '''
    buf = ''
    if fmt == 0x00:
        buf = hex_2_byte('\x00'*4, 0, 4, addr)
    elif fmt == 0x03:
        buf = hex_2_byte('\x00'*8, 0, 8, addr)
    elif fmt == 0x04:
        buf = '\x00' * 8
        buf = hex_2_byte(buf, 0, 3, __to_cylinder(addr))
        buf = hex_2_byte(buf, 3, 1, __to_head(addr))
        buf = hex_2_byte(buf, 4, 4, __to_index(addr))
    elif fmt == 0x05:
        buf = '\x00' * 8
        buf = hex_2_byte(buf, 0, 3, __to_cylinder(addr))
        buf = hex_2_byte(buf, 3, 1, __to_head(addr))
        buf = hex_2_byte(buf, 4, 4, __to_sector(addr))
    return buf

def is_cmd_good(cmd):
    from scsi.scsi_lib import SAM_STAT_GOOD, INTR_SCSI_STATE_FINISH
    return (cmd.status == SAM_STAT_GOOD and
            cmd.state == INTR_SCSI_STATE_FINISH)

def is_cmd_buff(cmd, length):
    return (cmd.in_buf and len(cmd.in_buf) >= length)

def is_disk(lun):
    return lun.type == sp.TYPE_DISK

def is_changer(lun):
    return lun.type == sp.TYPE_MEDIUM_CHANGER

def is_tape(lun):
    return lun.type == sp.TYPE_TAPE

def is_enclosure(lun):
    return lun.type == sp.TYPE_ENCLOSURE