#
#    isns main function.
#
#    Modify history:
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-05-12)
#

from tagt.config import read_config
from isns.isns_client import iSNSClient
from comm.debug import *

def IsnsService(isStop = None):
    '''
    iSNS serveice
    '''

    #
    # read config file for isns
    #
    config = read_config('config.xml')
    if config == None or config.isns.enable == False:
        return

    #
    # initialize isns client
    #
    server_ip = config.isns.server_ip
    server_port = config.isns.server_port
    client_port = config.isns.client_port
    client = iSNSClient(server_ip, server_port)
    if client.initial() == False:
        DBG_WRN('iSNS service initialize FAILED')
        return

    #
    # register each isns target.
    #
    for item in config.isns.target:
        target = config.get_target(item[0])
        if target == None:
            continue

        client.initial()
        client.SCNReg(target.name)
        client.DeregDev(target.name, None, target.ip, target.port)
        client.DevAttrReg(target.name, None, target.ip,
                          target.port, client_port, target.portal, target.name)
        DBG_PRN('iSNS reigster iscsi target(%s).' % target.name)
    client.Stop()

    #
    # run isns scn/esi daemon for scn/esi event.
    #
    client.SCN_ESI_Run(client_port)
