

class DelayedBuffer(object):
    
    def __init__(self, buf, size):
        self.buf = buf
        self.size = size

    def __len__(self):
        return self.size

    def __getitem__(self , item):
        return self.buf.__getitem__(item)

    def wait(self):
        '''waits till buffer is ready to be read'''
        return False

    def check(self):
        '''checks if buffer is ready to be read'''
        return False

    def check_for_one(self, wait_list):
        '''checks if one of the objects are ready'''
        for w in wait_list:
            if w.check():
                return w
        return None

    def wait_for_one(self, wait_list):
        '''waits till one of the objects are ready'''
        for w in wait_list:
            if w.wait():
                return w
        return None

    def error_code(self):
        '''return operation error code or 0 if success'''
        return 0

