#    
#    Configuration module.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#

import copy
import xml.sax.handler
from comm.debug import *


class _Node():
    '''
    Class for negotiation parameter configuration
    @note: if these items can't find in config.xml file,
           target will use default values as following.
    '''
    def __init__(self):
        self.MaxConnections = 8
        self.InitialR2T = True
        self.ImmediateData = True
        self.FirstBurstLength = 65536
        self.MaxBurstLength = 262144
        self.DefaultTime2Wait = 2
        self.DefaultTime2Retain = 20
        self.MaxOutstandingR2T = 128
        self.DataPDUInOrder = True
        self.DataSequenceInOrder = True
        self.ErrorRecoveryLevel = 0
        self.MaxRecvDataSegmentLength = 8192

class _Target():
    '''
    Class for target configuration
    '''
    def __init__(self):
        self.name = ''
        self.ip = ''
        self.port = 0
        self.portal = 0
        self.host = []
        self.para = _Node()

class _Host():
    '''
    Class for host configuration
    '''
    def __init__(self):
        self.name = ''
        self.pwd_i = ''
        self.pwd_t = ''
        self.lun = []

class _Lun():
    '''
    Class for lun configuration
    '''
    def __init__(self):
        self.id = 0
        self.path = ''
        self.cap = 0
        self.type = 0
        
class _iSNS():
    '''
    class for isns configuration
    '''
    def __init__(self):
        self.enable = False
        self.server_ip = ''
        self.server_port = 0
        self.client_port = 0
        self.target = []

class Config(xml.sax.handler.ContentHandler):
    '''
    Class for all configuration
    '''
    def __init__(self):
        self.ip = ''
        self.port = 0
        self.debug_level = 6
        self.target_list = []
        self.isns = _iSNS()
        self.__t = _Target()
        self.__h = _Host()
        self.__l = _Lun()
        self.flags = 0
        self.data = ''
        
    def get_target(self, name):
        '''
        get target config
        '''
        for item in self.target_list:
            if item.name == name:
                return item
        return None

    def startElement(self, name, attributes):
        from comm.stdlib import asc, str_2_value, str_2_bool

        if name == 'console':
            self.ip = asc(attributes['ip'])
            self.port = str_2_value(asc(attributes['port']))
            self.debug_level = str_2_value(asc(attributes['debug_level']))
        elif name == 'target':
            self.__t.name = asc(attributes['name'])
            self.__t.ip = asc(attributes['ip'])
            self.__t.port = str_2_value(asc(attributes['port']))
            self.__t.portal = str_2_value(asc(attributes['portal']))
        elif name == 'host':
            self.__h.name = asc(attributes['name'])
            self.__h.pwd_t = asc(attributes['target_pwd'])
            self.__h.pwd_i = asc(attributes['initiator_pwd'])
        elif name == 'lun':
            self.__l.id = str_2_value(asc(attributes['id']))
            self.__l.path = asc(attributes['path'])
            self.__l.cap = str_2_value(asc(attributes['capacity']))
            self.__l.type = str_2_value(asc(attributes['type']))
            self.__h.lun.append(copy.deepcopy(self.__l))
        elif name == 'item':
            key = asc(attributes['key'])
            value = asc(attributes['value'])
            if key == 'MaxConnections':
                self.__t.para.MaxConnections = str_2_value(value)
            elif key == 'InitialR2T':
                self.__t.para.InitialR2T = str_2_bool(value)
            elif key == 'ImmediateData':
                self.__t.para.ImmediateData = str_2_bool(value)
            elif key == 'FirstBurstLength':
                self.__t.para.FirstBurstLength = str_2_value(value)
            elif key == 'MaxBurstLength':
                self.__t.para.MaxBurstLength = str_2_value(value)
            elif key == 'DefaultTime2Retain':
                self.__t.para.DefaultTime2Retain = str_2_value(value)
            elif key == 'MaxOutstandingR2T':
                self.__t.para.MaxOutstandingR2T = str_2_value(value)
            elif key == 'DataPDUInOrder':
                self.__t.para.DataPDUInOrder = str_2_bool(value)
            elif key == 'DataSequenceInOrder':
                self.__t.para.DataSequenceInOrder = str_2_bool(value)
            elif key == 'ErrorRecoveryLevel':
                self.__t.para.ErrorRecoveryLevel = str_2_value(value)
            elif key == 'MaxRecvDataSegmentLength':
                self.__t.para.MaxRecvDataSegmentLength = str_2_value(value)
        elif name == 'isns':
            self.isns.enable = str_2_bool(asc(attributes['enable']))
            if self.isns.enable:
                self.isns.server_ip = asc(attributes['isns_server_ip'])
                self.isns.server_port = str_2_value(asc(attributes['isns_server_port']))
                self.isns.client_port = str_2_value(asc(attributes['isns_client_port']))
        elif name == 'isns_target':
            name = asc(attributes['name'])
            dd = asc(attributes['dd'])
            self.isns.target.append((name, dd))
        else:
            self.data = ''

    def characters(self, data):
        self.data += data

    def endElement(self, name):
        if name == 'target':
            self.target_list.append(copy.deepcopy(self.__t))
            self.__t.host = []
        elif name == 'host':
            self.__t.host.append(copy.deepcopy(self.__h))
            self.__h.lun = []

def read_config(path):
    '''
    Analyse config file for target configuration
    '''
    parser = xml.sax.make_parser( )
    config = Config()
    parser.setContentHandler(config)
    try:
        parser.parse(path)
    except:
        DBG_ERR(__file__, line(), 'Read %s FAILED' % path)
        return None
    return config