#    
#    general list for iscsi/scsi task.
#
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-02-18)
#

from comm.debug import *

class List():
    '''
    List class
    @warning: All of the items,
     pushed in list must hold an unique id
    '''
    def __init__(self):
        '''
        list constructor
        '''
        self.list = []
        self.__lock = threading.Lock()


    def lock(self):
        '''
        list lock
        '''
        self.__lock.acquire()
        
        
    def unlock(self):
        '''
        list unlock
        '''
        self.__lock.release()


    def find(self, id):
        '''
        find item from list by id
        @param id: item unique id (key)
        @return: None for failed, other for success
        '''
        result = None
        self.lock()
        for item in self.list:
            if item.id == id:
                result = item
                break
        self.unlock()
        return result
    
    
    def push(self, item):
        '''
        push an item into list
        @param item: item
        @return: True for success, False for fail.
        '''
        result = True
        if self.find(item.id):
            result = False
            DBG_WRN('push item FAILED, item exist already.')
        else:
            self.lock()
            self.list.append(item)
            self.unlock()
        return result


    def pop(self, id):
        '''
        find an item from list by id, and pop it out.
        @param id: item unique id (key)
        @return: None for failed, other for success.
        '''
        result = self.find(id)
        if result:
            self.lock()
            self.list.remove(result)
            self.unlock()
        return result


    def clear(self):
        '''
        clear list
        '''
        self.lock()
        self.list = None
        self.unlock()

