#    
#    iscsi text key negotiation implementation code.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-29)
#

from iscsi import iscsi_comm as lib
from comm.debug import DBG_WRN, DBG_NEG

#
# Default text key value
#
KEY_LST = 0x01
KEY_STR = 0x02
KEY_INT = 0x03
KEY_BOL = 0x04
KEY_ATH = 0x05

def __and(x, y):
    return (x and y)

def __or(x, y):
    return (x or y)


class KeyAttr():
    '''
    class for iscsi key attribute.
    '''

    def __init__(self, name, type, min, max, default, value, ops):
        '''
        Key attribute constructor
        @param name: key name
        @param type: key type
        @param min:  min value
        @param max:  max value
        @param default: default value
        @param value: current value
        @param ops: negotiate ops
        '''
        self.name    = name
        self.type    = type
        self.min     = min
        self.max     = max
        self.default = default
        self.value   = value
        self.t_ready = False
        self.i_ready = False
        self.ops     = ops

    def ready(self):
        self.t_ready = True

    def is_ready(self):
        return self.t_ready

    def check(self, pdu):
        '''
        check key
        @param pdu: iscsi pdu(login or text request)
        @return: Reject for invalid
                 None for not exist
                 other for success
        '''
        value = lib.get_key_val(pdu, self.name)
        if value == 'Reject' or value == None:
            return value
        if self.type == KEY_BOL:
            if value != self.min and value != self.max:
                value = 'Reject'
        elif self.type == KEY_INT:
            if not value.isdigit():
                value = 'Reject'
            else:
                if lib.atoi(value) < self.min or lib.atoi(value) > self.max:
                    value = 'Reject'
        elif self.type == KEY_STR:
            if (self.min and len(value) < self.min or
                self.max and len(value) > self.max):
                value = 'Reject'
        elif self.type == KEY_LST:
            lst_key = value.split(',')
            value = 'Reject'
            for item in lst_key:
                if (item == self.min or item == self.max):
                    value = item
                    break
        elif self.type == KEY_ATH:
            if self.value and lib.find_key_list(value, self.max):
                value = self.max
            elif self.value == False and lib.find_key_list(value, self.min):  
                value = self.min
            else:
                value = 'Reject'
        return value


    def negotiate(self, req, rsp, misc = None):
        '''
        negotiate text key value pair
        @param req: iscsi login request pdu
        @param rsp: iscsi login response pdu
        @return: Reject for invalid
                 None for not exist
                 other for success
        '''
        value = lib.get_key_val(req, self.name)

        if self.i_ready:
            if value != None:
                rsp.bhs[36] = lib.ISCSI_STATUS_CLS_INITIATOR_ERR
                rsp.bhs[37] = lib.ISCSI_LOGIN_STATUS_INIT_ERR
                DBG_WRN('%s has already negotiated.' % self.name)
                return 'Reject'
            return

        if value is None:
            return None
        elif value == 'Reject':
            rsp.bhs[36] = lib.ISCSI_STATUS_CLS_INITIATOR_ERR
            rsp.bhs[37] = lib.ISCSI_LOGIN_STATUS_INIT_ERR
            DBG_WRN('detect multiply text key %s.' % self.name)
        else:
#            assert(self.t_ready == False)
            self.i_ready = True
            self.t_ready = True

        if self.type == KEY_BOL:
            if value != self.min and value != self.max:
                value = 'Reject'
            else:
                self.value = self.ops(lib.str_2_bool(value), self.value)
                value = lib.bool_2_str(self.value)
        elif self.type == KEY_INT:
            if not value.isdigit():
                value = 'Reject'
            else:
                value = lib.atoi(value)
                if value < self.min or value > self.max:
                    value = 'Reject'
                else:
                    self.value = self.ops(value, self.value)
                    if misc:
                        self.value = self.ops(misc, self.value)
                    value = '%d' % self.value
        elif self.type == KEY_STR:
            if self.min and len(value) < self.min or \
               self.max and len(value) > self.max:
                value = 'Reject'
            else:
                self.value = value
        elif self.type == KEY_LST:
            if self.name == 'OFMarkInt' or self.name == 'IFMarkInt':
                value = self.min
            else:
                lst_key = value.split(',')
                value = 'Reject'
                for item in lst_key:
                    if (item == self.min or item == self.max):
                        self.value = item
                        value = item
                        break
        elif self.type == KEY_ATH:
            if self.value and lib.find_key_list(value, self.max):
                value = self.max
            elif self.value == False and lib.find_key_list(value, self.min):  
                value = self.min
            else:
                value = 'Reject'

        if self.name != 'MaxRecvDataSegmentLength': 
            lib.set_key_val(rsp, self.name, value)
#        if value == 'Reject':
#            rsp.bhs[36] = ISCSI_STATUS_CLS_INITIATOR_ERR
#            rsp.bhs[37] = ISCSI_LOGIN_STATUS_INIT_ERR
        DBG_NEG(self.name, '=', value)

        return value


    def text_nego(self, req, rsp, misc = None):
        '''
        negotiate text key value pair
        @param req: iscsi text request pdu
        @param rsp: iscsi text response pdu
        @return: Reject for invalid
                 None for not exist
                 other for success
        '''
        value = lib.get_key_val(req, self.name)

        if value is None:
            return None
        elif value == 'Reject':
            DBG_WRN('detect multiply text key %s.' % self.name)
            return value
        elif self.type == KEY_BOL:
            if value != self.min and value != self.max:
                value = 'Reject'
            else:
                self.value = self.ops(lib.str_2_bool(value), self.value)
                value = lib.bool_2_str(self.value)
        elif self.type == KEY_INT:
            if not value.isdigit():
                value = 'Reject'
            else:
                value = lib.atoi(value)
                if value < self.min or value > self.max:
                    value = 'Reject'
                else:
                    self.value = self.ops(value, self.value)
                    if misc:
                        self.value = self.ops(misc, self.value)
                    value = '%d' % self.value

        elif self.type == KEY_STR:
            if self.min and len(value) < self.min or \
               self.max and len(value) > self.max:
                value = 'Reject'
            else:
                self.value = value
        elif self.type == KEY_LST:
            lst_key = value.split(',')
            value = 'Reject'
            for item in lst_key:
                if (item == self.min or
                    item == self.max):
                    self.value = item
                    value = item
                    break
        elif self.type == KEY_ATH:
            if self.value and lib.find_key_list(value, 'CHAP'):
                value = 'CHAP'
            elif self.value == False and lib.find_key_list(value, 'None'):  
                value = 'None'
            else:
                value = 'Reject'

        if self.name != 'MaxRecvDataSegmentLength': 
            lib.set_key_val(rsp, self.name, value)
        DBG_NEG(self.name, '=', value)

        return value


    def final_nego(self, misc = None):
        '''
        finishing negotiation
        '''
        if self.t_ready == False:
            if self.default and self.ops:
                self.value = self.default
                DBG_NEG(self.name, '=', self.value)
        elif self.i_ready == False:
            if self.default and self.ops:
                value = self.default
                if self.type == KEY_BOL:
                    self.value = self.ops(lib.str_2_bool(value), self.value)
                    value = lib.bool_2_str(self.value)
                elif self.type == KEY_INT:
                    self.value = self.ops(value, self.value)
                    if misc:
                        self.value = self.ops(misc, self.value)
                    value = self.value
                DBG_NEG(self.name, '=', value)


ISCSI_KEY_PAIR = {
    # check
    'SessionType'             :KeyAttr('SessionType', KEY_BOL, 'Discovery', 'Normal', 'Normal',None, None),
    'SendTargets'             :KeyAttr('SendTargets', KEY_STR, 3, 3, None, None, None),
    'TargetName'              :KeyAttr('TargetName', KEY_STR, 1, 1024, 'NULL', None, None),
    'InitiatorName'           :KeyAttr('InitiatorName', KEY_STR, 1, 1024, 'NULL', None, None),
    'TargetAlias'             :KeyAttr('TargetAlias', KEY_STR, 1, 1024, 'NULL', None, None),
    'InitiatorAlias'          :KeyAttr('InitiatorAlias', KEY_STR, 1, 1024, 'NULL', None, None),
    'TargetAddress'           :KeyAttr('TargetAddress', KEY_STR, 14, 27, 'NULL', None, None),
    'TargetPortalGroupTag'    :KeyAttr('TargetPortalGroupTag', KEY_INT, 0, 65535, 1, 1, None),
    # chap
    'CHAP_A'                  :KeyAttr('CHAP_A', KEY_LST, '5', '5', None, None, None),
    'CHAP_R'                  :KeyAttr('CHAP_R', KEY_STR, 34, 34, None, None, None),
    'CHAP_I'                  :KeyAttr('CHAP_I', KEY_INT, 0, 255, None, None, None),
    'CHAP_C'                  :KeyAttr('CHAP_C', KEY_STR, 0, 2050, None, None, None),
    'CHAP_N'                  :KeyAttr('CHAP_N', KEY_STR, 1, 255, None, None, None),
    # negotiate
    'AuthMethod'              :KeyAttr('AuthMethod', KEY_ATH, 'None', 'CHAP', 'None', False, None),
    'HeaderDigest'            :KeyAttr('HeaderDigest', KEY_LST, 'None', 'CRC32C', 'None', False, None),
    'DataDigest'              :KeyAttr('DataDigest', KEY_LST, 'None', 'CRC32C', 'None', False, None),
    'MaxRecvDataSegmentLength':KeyAttr('MaxRecvDataSegmentLength', KEY_INT, 512, 16777215, 8192, 65536, min),
    'MaxConnections'          :KeyAttr('MaxConnections', KEY_INT, 1, 65535, 1, 8, min),
    'MaxBurstLength'          :KeyAttr('MaxBurstLength', KEY_INT, 512, 16777215, 262144, 262144, min),
    'FirstBurstLength'        :KeyAttr('FirstBurstLength', KEY_INT, 512, 16777215, 65536, 65536, min),
    'DefaultTime2Wait'        :KeyAttr('DefaultTime2Wait', KEY_INT, 0, 3600, 2, 2, max),
    'DefaultTime2Retain'      :KeyAttr('DefaultTime2Retain', KEY_INT, 0, 3600, 20, 2, min),
    'MaxOutstandingR2T'       :KeyAttr('MaxOutstandingR2T', KEY_INT, 1, 65535, 1, 16, min),
    'ErrorRecoveryLevel'      :KeyAttr('ErrorRecoveryLevel', KEY_INT, 0, 2, 0, 0, min),
    'InitialR2T'              :KeyAttr('InitialR2T', KEY_BOL, 'Yes', 'No', 'Yes', True, __or),
    'ImmediateData'           :KeyAttr('ImmediateData', KEY_BOL, 'Yes', 'No', 'Yes', True, __and),
    'DataPDUInOrder'          :KeyAttr('DataPDUInOrder', KEY_BOL, 'Yes', 'No', 'Yes', True, __or),
    'DataSequenceInOrder'     :KeyAttr('DataSequenceInOrder', KEY_BOL, 'Yes', 'No', 'Yes', True, __or),
    'OFMarker'                :KeyAttr('OFMarker', KEY_BOL, 'Yes', 'No', 'No', False, __and),
    'IFMarker'                :KeyAttr('IFMarker', KEY_BOL, 'Yes', 'No', 'No', False, __and),
    'OFMarkInt'               :KeyAttr('OFMarkInt', KEY_LST, 'Irrelevant', 'Irrelevant', 'Irrelevant', 'Irrelevant', None),
    'IFMarkInt'               :KeyAttr('IFMarkInt', KEY_LST, 'Irrelevant', 'Irrelevant', 'Irrelevant', 'Irrelevant', None),
    'TaskReporting'           :KeyAttr('TaskReporting', KEY_LST, 'RFC3720', 'RFC3720', None,'RFC3720', None), # RFC5048
}


def new_key(key):
    '''
    Create a iscsi text key
    '''
    import copy
    if key in ISCSI_KEY_PAIR:
        return copy.deepcopy(ISCSI_KEY_PAIR[key])
    return None


# global chap only for check
CHAP_A = new_key('CHAP_A')
CHAP_R = new_key('CHAP_R')
CHAP_I = new_key('CHAP_I')
CHAP_C = new_key('CHAP_C')
CHAP_N = new_key('CHAP_N')
