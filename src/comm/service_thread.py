#    
#    service thread class.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#

from comm.debug import *

class ServiceThread(threading.Thread):
    '''
    Class service thread
    '''

    def __init__(self, service_name, service_fn):
        '''
        Constructor, setting initial variables
        @param service_name: service thread name
        @param service fn: service call back fn
        '''
        self.__stopevent = threading.Event()
        self.__service_fn = service_fn
        threading.Thread.__init__(self, name = service_name)
        self.setDaemon(True)

    def run(self):
        '''
        Start to run service
        '''
        DBG_INF('start ' + self.getName() + ' ...')
        if self.__service_fn:
            self.__service_fn()

    def stop(self, timeout=0):
        '''
        Send stop single to terminate current thread
        @param timeout: timeout
        '''
        self.__stopevent.set()
        threading.Thread.join(self, timeout)

    def wait(self, period):
        '''
        Wait until current thread terminate
        @param period: sleep period
        '''
        while not self.__stopevent.isSet():
            self.__stopevent.wait(period)