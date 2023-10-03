#    
#    initiator scsi/iscsi task cache code.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-02-12)
#
from comm.comm_list import *

class IntrCache(List):
    '''
    class for initiator cache
    '''
    def __init__(self):
        '''
        initiator cache constructor
        '''
        List.__init__(self)


    def pop_conn_cmd(self, conn):
        '''
        find cache list with connnect, and then pop it out.
        @param conn: iscsi connect
        @return: None for not found, other for success.
        '''
        result = None
        self.lock()
        for item in self.list:
            if item.connect == conn:
                result = item
                self.list.remove(item)
                break
        self.unlock()
        return result
