#    
#    iscsi target/target pool implementation code.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#
import threading
from comm.debug import DBG_ERR, DBG_WRN, DBG_PRN
from iscsi.iscsi_lib import ISCSI_FULL_FEATURE_PHASE, ISCSI_TARGET_STOP


class Target():
    '''
    Class for iscsi target
    '''

    def __init__(self, name, ip, port, portal):
        '''
        Target constructor
        @param name: target name
        @param ip: target ip
        @param port: target port
        @param portal: target portal
        '''
        self.name = name
        self.addr = ['%s:%d,%d' % (ip, port, portal)]
        self.portal = portal
        self.tsih = 0
        self.tsih_lock = threading.Lock()
        self.host_list = []
        self.host_list_lock = threading.Lock()
        self.config = None
        DBG_PRN('create target', name, ip, port, portal)

    def __del__(self):
        '''
        Target destroy
        '''
        DBG_PRN('destroy target', self.name)
        self.Stop()


    def next_tsih(self):
        '''
        Allocate a new tsih
        '''
        self.tsih_lock.acquire()
        self.tsih += 1
        if self.tsih == 0x10000:
            self.tsih = 1
        result = self.tsih
        self.tsih_lock.release()
        return result


    def add_address(self, ip, port):
        '''
        Add a target address
        '''
        result = True
        if self.find_address(ip, port):
            DBG_WRN('target %s add address %s:%d FAILED' % (self.name, ip, port))
            result = False
        else:
            self.addr.append('%s:%d,%d' % (ip, port, self.portal))
            DBG_PRN('target %s add address %s:%d' % (self.name, ip, port))
        return result


    def del_address(self, ip, port):
        '''
        Remove a target address
        '''
        address = self.find_address(ip, port)
        if address:
            self.addr.remove(address)
            DBG_PRN('target %s remove address %s' % (self.name, address))


    def find_address(self, ip, port):
        '''
        Find a target address
        '''
        address = '%s:%d,%d' % (ip, port, self.portal)
        for addr in self.addr:
            if addr == address:
                return addr
        return None


    def add_host(self, host):
        '''
        Add a host into target
        @param host: Target host
        @return: True for success, False for failed
        @warning: following do not use deepcopy for adding host 
        '''
        result = True
        if self.find_host(host.name):
            result = False
            DBG_WRN('target %s add host %s FAILED' % (self.name, host.name))
        else:
            self.host_list_lock.acquire()
            self.host_list.append(host)
            self.host_list_lock.release()
            DBG_PRN('target %s add host %s' % (self.name, host.name))
        return result


    def del_host(self, name):
        '''
        Delete a target host
        @param name: host name
        @return: True for success, False for failed
        '''
        result = False
        host = self.find_host(name)
        if host != None:
            self.host_list_lock.acquire()
            self.host_list.remove(host)
            self.host_list_lock.release()
            DBG_PRN('target %s remove host %s' % (self.name, name))
            result = True
        return result


    def find_host(self, name):
        '''
        Get target host
        @param name: host name
        @return: specific host for success, None for failed 
        '''
        result = None
        self.host_list_lock.acquire()
        for host in self.host_list:
            if host.name == name:
                result = host
                break
        self.host_list_lock.release()
        return result


    def Stop(self):
        '''
        Stop current target
        '''

        # FIXME? 
        for host in self.host_list:
            for session in host.session_list:
                for connect in session.conn_list:
                    if connect.state == ISCSI_FULL_FEATURE_PHASE:
                        connect.state = ISCSI_TARGET_STOP
                        connect.Stop()
        DBG_PRN('target %s stop' % self.name)


class TargetPool():
    '''
    Class target pool
    '''

    def __init__(self):
        '''
        initialize target pool.
        '''
        self.target_list = []
        self.__lock = threading.Lock()

    def lock(self):
        '''
        lock target pool.
        '''
        self.__lock.acquire()

    def unlock(self):
        '''
        unlock target pool.
        '''
        self.__lock.release()


    def find_target(self, name):
        '''
        Find a target by target name.
        @param name: target name
        @return: True for success, False for failed
        '''
        result = None
        self.lock()
        for target in self.target_list:
            if target.name == name:
                result = target
                break
        self.unlock()
        return result
        
    
    def add_target(self, target):
        '''
        Add a target into target pool.
        @param target: iscsi target
        @return: True for success, False for failed
        '''
        if self.find_target(target.name):
            DBG_ERR("add target %s FAILED" % target.name)
            return False
        self.lock()
        self.target_list.append(target)
        self.unlock()
        return True


    def del_target(self, name):
        '''
        Delete a target from target pool.
        @param name: target name
        @return: True for success, False for failed
        '''
        result = False
        target = self.find_target(name)
        if target:
            self.lock()
            self.target_list.remove(target)
            result = True
            self.unlock()
            DBG_PRN('remove target %s from pool' % name)
        return result