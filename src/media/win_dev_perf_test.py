import media.win_dev
import time
from comm.delayed_buffer import *

def test():
    path = r'\\.\PhysicalDrive4'
    dev = media.win_dev.WinDev(path, True, True, True)
    dev.open()
    time_start = time.perf_counter()
    dev_size = dev.size()
    io_complete = 0
    offset = 0
    while 1:
        len = 4096
        offset = (offset + 1024*1024*1024) % dev_size
        buf = dev.read(offset , len)
        if isinstance(buf, DelayedBuffer):
            buf_list = [buf]
            buf.wait_for_one(buf_list)
        io_complete += 1
        time_end = time.perf_counter()
        if time_end - time_start > 1:
            time_start = time_end
            io_complete = 0
            print("IOs per second = " + str(io_complete))
