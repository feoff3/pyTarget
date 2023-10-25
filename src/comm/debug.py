#    
#    general debug APIs, debug switch, etc
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#

import sys, time, threading
import traceback

#
# Debug switch
#
CURRENT_DEBUG_LEVEL    = 6          # current debug level
PRINT_TRACE            = 0

__DEBUG_LEVEL_ERR      = 0x00       # error conditions
__DEBUG_LEVEL_WARNING  = 0x01       # warning conditions
__DEBUG_LEVEL_SIMULATE = 0x02       # simulate scsi info
__DEBUG_LEVEL_INFO     = 0x03       # informational
__DEBUG_LEVEL_NEGO     = 0x04       # negotiation
__DEBUG_LEVEL_CMD      = 0x05       # iscsi/scsi command
__DEBUG_LEVEL_DEBUG    = 0x06       # debug

__console_lock = threading.Lock()   # for console lock

def line():
    try:
        raise Exception
    except:
        return sys.exc_info()[2].tb_frame.f_back.f_lineno

def __debug_info(level, *msg):
        if CURRENT_DEBUG_LEVEL < level:
            return
        if level <= __DEBUG_LEVEL_SIMULATE:
            fd = sys.stderr
        else:
            fd = sys.stdout
        __console_lock.acquire()
        for item in msg: 
            print(item,end=' ',file=fd)
        print("",file=fd)
        if PRINT_TRACE:
            traceback.print_stack(file=fd)
        __console_lock.release()

#
# Debug API
#
def DBG_ERR(*msg):      __debug_info(__DEBUG_LEVEL_ERR, 'ERROR:\t', *msg)
def DBG_WRN(*msg):      __debug_info(__DEBUG_LEVEL_WARNING, 'WARNING:\t', * msg)
def DBG_SIM(*msg):      __debug_info(__DEBUG_LEVEL_SIMULATE, 'SIMULATOR:\t', * msg)
def DBG_INF(*msg):      __debug_info(__DEBUG_LEVEL_INFO, 'INFO:\t', *msg)
def DBG_NEG(*msg):      __debug_info(__DEBUG_LEVEL_NEGO, 'NEGOTIATION:\t', *msg)
def DBG_CMD(*msg):      __debug_info(__DEBUG_LEVEL_CMD, 'COMMAND:\t', *msg)
def DBG_PRN(*msg):      __debug_info(__DEBUG_LEVEL_DEBUG, 'DEBUG:\t', *msg)
def DBG_EXC(*msg):      __debug_info(__DEBUG_LEVEL_WARNING, 'EXCEPTION:\t\n' + ''.join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])), *msg)
