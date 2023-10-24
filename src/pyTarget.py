#!/bin/env python
#
#    Main module, start all kinds of services.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#
import time
from .comm.service_thread import ServiceThread
from .tagt.main import iscsi_target_service
from .isns.main import IsnsService
from .web.main import WebService
from .comm.debug import DBG_INF


###################################################################
#                             Target Main
###################################################################

if __name__ == '__main__':

    from .comm.version import MY_NAME, MY_VERSION, MY_DATE
    DBG_INF(MY_NAME, MY_VERSION, MY_DATE)

    #
    # Start iscsi service
    #
    ServiceThread('iSCSI Service', iscsi_target_service).start()

    #
    # Start isns service
    #
    ServiceThread('iSNS Service', IsnsService).start()

    #
    # start http service
    #
    ServiceThread('Http Service', WebService).start()

    while True:
        time.sleep(1024)