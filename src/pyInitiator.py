#!/bin/env python
#
#    Main module, start all kinds of services.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-01-20)
#

from .intr.initiator import Initiator
from .iscsi.iscsi_lib import *
from .scsi.scsi_lib import *

###################################################################
#                          Initiator Main
###################################################################

iqn   = 'iqn.2006-11.1'
ip    = '10.0.0.1'
port  = 3260

def Initiator_Main():
    '''
    initiator main
    '''

    # create initiator
    client = Initiator(iqn)
    if not client.discovery(ip, port):
        DBG_WRN('initiator discovery FAILED')
        return False

    # create session/connect
    session = client.add_session(SESSION_NORMAL)
    connect = session.add_conn(ip, port)
    if not connect:
        DBG_WRN('add leading connection FAILED')
        return False

    # create multi-connects
    i = 1
    conn_list = [connect]
    while i < session.MaxConnections.value:
        connect = session.add_conn(ip, port)
        if connect:
            conn_list.append(connect)
        i += 1

    #------------------------------------------------------------------
    #                    SCSI TASK BEGIN
    #------------------------------------------------------------------

    # leading connect
    conn = conn_list[0]          

    # ReportLun
    cmd = ReportLunReq(conn)
    conn.ScsiTask(cmd)
    lun_list = lun_rep(cmd)
    if len(lun_list) == 0:
        return False
    DBG_PRN('Lun:', lun_list)
    lun = lun_list[0]

    # TUR
    cmd = TestUnitReadyReq(conn, lun)
    conn.ScsiTask(cmd)

    # Inquiry
    cmd = InquiryReq(conn, lun, 0, 0)
    conn.ScsiTask(cmd)
    cmd = InquiryReq(conn, lun, 1, 0)
    conn.ScsiTask(cmd)
    cmd = InquiryReq(conn, lun, 1, 0x83)
    conn.ScsiTask(cmd)
    cmd = InquiryReq(conn, lun, 1, 0x80)
    conn.ScsiTask(cmd)

    #------------------------------------------------------------------
    #                    END OF SCSI TASK
    #------------------------------------------------------------------    
    # logout / close
    for i in range(len(conn_list)):
        conn_list[i].Logout(ISCSI_LOGOUT_REASON_CLOSE_CONNECTION)
        conn_list[i].Stop()

if __name__ == '__main__':
    Initiator_Main()
