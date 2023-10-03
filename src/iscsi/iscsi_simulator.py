#    
#    simulate all kinds of iscai/scsi device error for iscsi/scsi test.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-02-5)
#

from comm.debug import DBG_INF, DBG_WRN

__MAX_ISCSI_RULE = 65536
__ISCSI_RULE = [False] * __MAX_ISCSI_RULE

def ADD_RULE(id):
    if id < len(__ISCSI_RULE):
        __ISCSI_RULE[id] = True
        DBG_INF('Add iscsi rule:', id)
    else:
        DBG_WRN('Add rule FAILED(out of range)')

def DEL_RULE(id):
    if id < len(__ISCSI_RULE):
        __ISCSI_RULE[id] = False

def IS_RULE(id):
    if id < len(__ISCSI_RULE):
        return __ISCSI_RULE[id]
    return False

def CHK_RULE(id):
    if IS_RULE(id):
        DEL_RULE(id)
        DBG_WRN('Simulator iscsi rule-', id)
        return True
    return False
