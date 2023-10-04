#
#    scsi tape device implementation code
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-03-18)
#

from comm.stdlib import *
from scsi.scsi_dev import *


# block type
BLOCK_EOD                       = 1
BLOCK_FILEMARK                  = 2
BLOCK_DATA                      = 3

# block/inode 
BLOCK_ADDR_SIZE                 = 4
DATA_ADDR_SIZE                  = 8
INODE_OFFSET                    = BLOCK_ADDR_SIZE + DATA_ADDR_SIZE
INODE_SIZE                      = 1 + BLOCK_ADDR_SIZE + BLOCK_ADDR_SIZE + DATA_ADDR_SIZE
TAPE_BLOCK_SIZE                 = 65536


class FileMark(DevFile):
    '''
    class for tape filemark
    '''
    def __init__(self, path):
        '''
        initialize filemark
        @param path: tape file path
        '''
        DevFile.__init__(self, path + '.fmk')
        self.list = []
        self.initial()

    def initial(self):
        '''
        initialize filemark
        @return: True for success, False for failed
        '''
        if self.size() < BLOCK_ADDR_SIZE:
            return self.flush_filemark()
        else:
            buf = self.read(0, BLOCK_ADDR_SIZE)
            if not buf:
                return False
            count = buf_u32(buf)
            if count > 0:
                buf = self.read(BLOCK_ADDR_SIZE, count * BLOCK_ADDR_SIZE)
                if not buf:
                    DBG_WRN('read filemarks list FAILED')
                    return False
                for i in range(count):
                    self.list.append(buf_u32(buf, i * BLOCK_ADDR_SIZE))
            return True

    def add_filemark(self, blk_nr):
        '''
        add a filemark into filemark list
        @param blk_nr: block number
        @return: True for success, False for failed
        '''
        self.lock()
        self.list.append(blk_nr)
        self.unlock()
        return self.flush_filemark()

    def flush_filemark(self):
        '''
        flush filemark list to file
        @return: True for success, False for failed
        '''
        self.lock()
        buf = u32_buf(len(self.list))
        for item in self.list:
            buf += u32_buf(item)
        ret = self.write(0, buf)
        self.unlock()
        return ret

    def cut_filemarks(self, blk_end):
        '''
        cut off filemark list from blk_end to the end
        @param blk_end: block number
        @return: True for success, False for failed
        '''
        find = False
        self.lock()
        for i in range(len(self.list)):
            if self.list[i] > blk_end:
                self.list = self.list[:i]
                find = True
                break
        self.unlock()
        if find:
            return self.flush_filemark()
        return True


class Block(DevFile):
    '''
    class for tape block inode.
    '''

    def __init__(self, path):
        '''
        initialize tape block
        @param path: block file path
        '''
        DevFile.__init__(self, path + '.hdr')
        self.block_type = 0                     # 1 byte                    
        self.block_number = 0                   # 4 bytes
        self.block_size = 0                     # 4 bytes
        self.block_base = 0                     # 8 bytes
        self.current_offset = 0                 
        self.current_end_block = 0
        self.current_end_data = 0
        self.initial()

    def initial(self):
        '''
        initialize tape block
        @return: True for success, False for failed
        '''
        size = INODE_OFFSET + INODE_SIZE
        if self.size() < size:
            self.set_eod()
        else:
            buf = self.read(0, size)
            if not buf:
                return False
            self.current_offset = 0
            self.current_end_block = buf_u32(buf)
            self.current_end_data = buf_u64(buf, BLOCK_ADDR_SIZE)
            self.block_type = buf_u8(buf, INODE_OFFSET)
            self.block_number = buf_u32(buf, INODE_OFFSET + 1)
            self.block_size = buf_u32(buf, INODE_OFFSET + 5)
            self.block_base = buf_u64(buf, INODE_OFFSET + 9)
        return True

    def set_eod(self):
        '''
        set current block to end block,
        and update block file.
        @return: True for success, False for failed
        '''
        self.lock()
        self.block_type = BLOCK_EOD
        self.current_end_block = self.block_number
        self.current_end_data = self.block_base + self.block_size
        buf = u32_buf(self.current_end_block)
        buf += u64_buf(self.current_end_data)
        ret = self.write(0, buf)
        self.unlock()
        if not ret:
            DBG_WRN('set eod block FAILED')
        return ret

    def alloc_block(self, type):
        '''
        allocate a new block as current active block.
        @param type: block type
        '''
        self.lock()
        self.block_type = type
        self.block_number += 1
        self.block_base += self.block_size
        self.block_size = 0
        self.current_offset = 0
        self.unlock()

    def read_block(self, blk_nr):
        '''
        load this block as current active block.
        @param blk_nr: block number
        @return: True for success, False for failed
        '''
        if blk_nr > self.current_end_block:
            DBG_WRN('read block FAILED, block number out of range(%d, %d)' % (blk_nr, self.current_end_block))
            return False
        else:
            self.lock()
            offset = blk_nr * INODE_SIZE + INODE_OFFSET
            buf = self.read(offset, INODE_SIZE)
            self.unlock()
            if not buf:
                DBG_WRN('read block FAILED, block number out of range(%d, %d)' % (blk_nr, self.current_end_block))
                return False
            else:
                self.lock()
                self.block_type = buf_u8(buf)
                self.block_number = buf_u32(buf, 1)
                self.block_size = buf_u32(buf, 5)
                self.block_base = buf_u64(buf, 9)
                self.current_offset = 0
                self.unlock()
                return True

    def write_block(self, blk_nr):
        '''
        write current block to block file
        @param blk_nr: block index
        @return: True for success, False for failed
        '''
        self.lock()
        buf = ''
        buf += u8_buf(self.block_type)
        buf += u32_buf(self.block_number)
        buf += u32_buf(self.block_size)
        buf += u64_buf(self.block_base)
        ret = self.write(blk_nr * INODE_SIZE + INODE_OFFSET, buf) and self.set_eod()
        self.unlock()
        if not ret:
            DBG_WRN('write block FAILED')
        return ret

    def write_filemark_block(self):
        '''
        set current block as filemark block, and write to block file.
        @return: True for success, False for failed
        '''
        self.alloc_block(BLOCK_FILEMARK)
        if self.write_block(self.block_number):
            self.set_eod()
            self.block_type = BLOCK_FILEMARK
            return True
        return False

    def get_block(self):
        '''
        get current active block
        '''
        return self.block_number


    def debug(self):
        DBG_PRN('Block: block_type=%d' % self.block_type,
                  'block_number=%d' % self.block_number,
                  'block_size=%d' % self.block_size,
                  'block_base=%d' % self.block_base,
                  'current_offset=%d' % self.current_offset,
                  'current_end_block=%d' % self.current_end_block,
                  'current_end_data=%d' % self.current_end_data)

    def debug_list(self):
        for i in range(self.current_end_block + 1):
            buf = self.read(i * INODE_SIZE + INODE_OFFSET, INODE_SIZE)
            if buf == None: continue
            DBG_PRN('Block-%d: block_type=%d' % (i, buf_u8(buf)),
                      'block_number=%d' % buf_u32(buf, 1),
                      'block_size=%d' % buf_u32(buf, 5),
                      'block_base=%d' % buf_u64(buf, 9))
 

class Tape(Lun):
    '''
    class for scsi tape
    '''

    def __init__(self, id, cap, dev):
        '''
        Initialize scsi tape
        @param id: scsi lun id
        @param cap: tape capacity (align in block)
        @param dev: tape file DevFile
        '''
        Lun.__init__(self, id, TYPE_TAPE, dev)
        self.capacity = cap << BLOCK_SHIFT          # tape capacity in bytes
        # Note: only works with original "DevFile" devices
        self.filemark = FileMark(dev.path)              # tape filemark list
        self.block = Block(dev.path)                    # tape block list
        self.block_size = TAPE_BLOCK_SIZE           # tape block size

    def initial(self):
        '''
        Initialize scsi tape (do nothing)
        '''
        return True

    def is_load(self, tio=None):
        '''
        check if tape is load
        @param tio: target i/o request
        @return: True for ready, False for notready
        '''
        if self.ready == False:
            if tio:
                tio.set_sense(NOT_READY, 0x3A00)
            DBG_WRN('tape (%s) is not ready' % self.path)
        return self.ready
    
    def is_filemark(self):
        '''
        check if tape position is filemark
        @return: True for Yes, False for No
        '''
        return self.block.block_type == BLOCK_FILEMARK
    
    def is_eod(self):
        '''
        check if tape position is end-of-data
        '''
        return (self.block.block_number == self.block.current_end_block and
                self.block.current_offset == self.block.block_size)
        
    def is_eob(self):
        '''
        check if tape position is end-of-block
        '''
        return not (self.block.block_number < self.block.current_end_block)

    def is_data(self):
        '''
        check if tape position is data block
        '''
        return self.block.block_type == BLOCK_DATA

    def load(self):
        '''
        load tape to slot
        '''
        DBG_PRN('load tape(%s)')
        self.ready = True

    def unload(self):
        '''
        remove tape from slot
        '''
        #self.ready = False (not need to set False)
        DBG_PRN('unload tape(%s)')
        pass

    def is_bop(self):
        '''
        check if current is at beginning of partition
        @return: True for bop, False for not bop
        '''
        return self.block.block_number == 0 and self.block.current_offset == 0

    def pos_end(self, tio):
        '''
        position to the end of data
        @param tio: target i/o request
        @return: True for success, False for failed
        '''
        if not self.block.read_block(self.block.current_end_block):
            DBG_WRN('position eod FAILED, read_block failed')
            tio.set_sense(MEDIUM_ERROR, 0x1100)
            return False
        return True

    def pos_block(self, tio):
        '''
        position to the specificy block
        @param tio: target i/o request
        @return: True for success, False for failed
        '''
        blk_nr = tio.length
        if blk_nr == 0:
            return self.Rewind(tio)
        elif blk_nr <= self.block.current_end_block:
            if not self.block.read_block(blk_nr):
                tio.set_sense(MEDIUM_ERROR, 0x1100)
                DBG_WRN('position block FAILED, read_block(%d) failed' % blk_nr)
                return False
            return True
        else:
            ret = self.pos_end(tio)
            tio.set_sense(BLANK_CHECK, 0x0005)
            DBG_WRN('position block out of range (%d)' % blk_nr)
            return ret

    def pos_blk_forward(self, tio):
        '''
        position block forward
        @param tio: target i/o request
        @return: True for success, False for failed
        '''
        count = tio.length
        while (count > 0 and
               self.block.block_type != BLOCK_FILEMARK and
               self.block.block_number < self.block.current_end_block):
            tio.length = self.block.block_number + 1
            if not self.pos_block(tio):
                break
            count -= 1
        if count > 0:
            if self.is_filemark():
                tio.set_sense(SCSI_RSP_EOF, 0x0001)
                self.pos_block(TIO(self.block.block_number + 1))
            else:
                tio.set_sense(BLANK_CHECK, 0x0005)
            return False
        else:
            return True

    def pos_blk_backward(self, tio):
        '''
        position block backward
        @param tio: target i/o request
        @return: True for success, False for failed
        '''
        count = tio.length
        while (count > 0 and
               self.block.block_type != BLOCK_FILEMARK and
               self.block.block_number > 0):
            tio.length = self.block.block_number - 1
            if self.pos_block(tio) == False:
                break
            count -= 1

        if count > 0:
            if self.is_filemark():
                tio.set_sense(SCSI_RSP_EOF, 0x0001)
                self.pos_block(TIO(self.block.block_number - 1))
            else:
                tio.set_sense(SCSI_RSP_EOF, 0x0002)
            return False
        else:
            return True

    def pos_fmk_forward(self, tio):
        '''
        position filemark forward
        @param tio: target i/o request
        @return: True for success, False for failed
        '''
        count = tio.length
        lst = self.filemark.list

        if len(lst) == 0:
            tio.set_sense(BLANK_CHECK, 0x0005, tio.length)
            if self.block.block_number < self.block.current_end_block:
                self.pos_end(tio)
            return False

        for i in range(len(lst)):
            if lst[i] > self.block.block_number:
                break
        if i + count - 1 < len(lst):
            tio.length = lst[i + count - 1]
            return self.pos_block(tio)
        else:
            res = i + count - len(lst)
            self.pos_end(tio)
            tio.set_sense(BLANK_CHECK, 0x0005, res)
            return False

    def pos_fmk_backward(self, tio):
        '''
        position filemark backup
        @param tio: target i/o request
        @return: True for success, False for failed
        '''
        count = tio.length
        lst = self.filemark.list

        if len(lst) == 0:
            tio.set_sense(SCSI_RSP_EOM, 0x0004)
            self.Rewind(tio)
            return False
        for i in range(len(lst))[::-1]:
            if lst[i] < self.block.block_number:
                break
        if i + 1 >= count:
            tio.length = lst[i - count + 1]
            return self.pos_block(tio)
        else:
            self.Rewind(tio)
            res = count - i - 1
            tio.set_sense(SCSI_RSP_EOM, 0x0004, res)
            return False

    def get_position(self):
        '''
        get current position
        '''
        return self.block.get_block()

    def get_block_size(self):
        '''
        get tape block size
        '''
        return self.block_size

    def set_block_size(self, size):
        '''
        set tape block size
        '''
        self.block_size = size


    def Format(self, tio):
        '''
        tape format
        @param tio: target i/o request
        @return: True for success, False for failed
        '''
        if self.is_protect():
            DBG_WRN('Write protected tape')
            tio.set_sense(DATA_PROTECT, 0x2700)
            return False

        ret = self.filemark.cut_filemarks(self.block.block_number) and \
              self.block.set_eod()
        if not ret:
            tio.set_sense(MEDIUM_ERROR, 0x0C00)
        return ret


    def Space(self, tio):
        '''
        tape space
        @param tio: target i/o request
        @return: True for success, False for failed
        '''
        code = tio.offset
        count = tio.length
        if tio.length < 0:
            tio.length = -tio.length
        if code == 0:
            if count >= 0:
                ret = self.pos_blk_forward(tio)
            else:
                ret = self.pos_blk_backward(tio)
        elif code == 1:
            if count >= 0:
                ret = self.pos_fmk_forward(tio)
            else:
                ret = self.pos_fmk_backward(tio)
        elif code == 3:
            ret = self.pos_end(tio)
        else:
            ret = False
            tio.set_sense(ILLEGAL_REQUEST, 0x2400)
        return ret
    

    def Read(self, tio):
        '''
        tape read
        @param tio: target i/o request
        @return: True for success, False for failed
        '''
        block = self.block
        length = tio.length

        if self.is_filemark(): 
            tio.set_sense(SCSI_RSP_EOF, 0x0001)
            if not self.is_eob():
                self.pos_blk_forward(TIO(1))
            return False

        base = block.block_base + block.current_offset
        size = block.block_size - block.current_offset
        size = min(size, length)
        block.current_offset += size

        size = length - size
        while (size > 0 and
               not self.is_filemark() and
               not self.is_eob()):
            if not block.read_block(block.block_number + 1):
                tio.set_sense(BLANK_CHECK, 0x0005)
                break
            block.current_offset += min(size, block.block_size)
            size -= min(size, block.block_size)
        tio.buffer = self.read(base, length - size)

        if size > 0:
            if self.is_filemark():
                tio.set_sense(SCSI_RSP_EOF, 0x0001)
                self.pos_blk_forward(TIO(1))
            else:
                tio.set_sense(BLANK_CHECK, 0x0005)
        else:
            if (self.is_data() and
                block.current_offset == block.block_size and
                block.block_number < block.current_end_block):
                block.read_block(block.block_number + 1)         
        return True


    def Write(self, tio):
        '''
        tape write
        @param tio: target i/o request
        @return: True for success, False for failed
        '''
        block = self.block
        buf = tio.buffer
        size = len(buf)
        offset = 0

        if self.is_protect():
            DBG_WRN('Write protected tape')
            tio.set_sense(DATA_PROTECT, 0x2700)
            return False
        
        if self.block_size:
            if size % self.block_size:
                tio.set_sense(SCSI_RSP_ILI, 0, size)
                DBG_WRN('ILI FAILED: requested length did not match the logical block length')
                return False            
            while size > 0:
                if not self.is_bop():
                    block.alloc_block(BLOCK_DATA)
                addr = block.block_base + block.current_offset
                length = min(size, self.block_size)
                if not self.write(addr, buf[offset:offset+length]):
                    tio.set_sense(MEDIUM_ERROR, 0x0C00)
                    return False
                block.current_offset += length
                block.block_size = block.current_offset
                block.block_type = BLOCK_DATA
                block.write_block(block.block_number)
                if not self.filemark.cut_filemarks(block.block_number):
                    tio.set_sense(MEDIUM_ERROR, 0x0C00)
                    return False
                size -= length
                offset += length
            return True
        else:
            if (block.block_type == BLOCK_FILEMARK or
                block.current_offset >= TAPE_BLOCK_SIZE):
                block.alloc_block(BLOCK_DATA)
            if not self.write(block.block_base + block.current_offset, tio.buffer):
                tio.set_sense(MEDIUM_ERROR, 0x0C00)
                return False
            block.current_offset += len(tio.buffer)
            block.block_size = block.current_offset
            block.block_type = BLOCK_DATA
            if (not block.write_block(block.block_number) or
                not self.filemark.cut_filemarks(block.block_number)):
                tio.set_sense(MEDIUM_ERROR, 0x0C00)
                return False
            return True


    def Rewind(self, tio):
        '''
        tape rewind
        @param tio: target i/o request
        @return: True for success, False for failed
        '''
        if self.block.block_number == 0:
            self.block.current_offset = 0
        else:
            if not self.block.read_block(0):
                tio.set_sense(MEDIUM_ERROR, 0x0C00)
                return False
        return True


    def Locate(self, tio):
        '''
        tape locate
        @param tio: target i/o request
        @return: True for success, False for failed
        '''
        tio.length += 1       
        return self.pos_block(tio)


    def WriteFilemark(self, tio):
        '''
        tape write filemarks
        @param tio: target i/o request
        @return: True for success, False for failed
        '''
        count = tio.length

        if self.is_protect():
            DBG_WRN('Write protected tape')
            tio.set_sense(DATA_PROTECT, 0x2700)
            return False

        while count > 0:
            if not self.block.write_filemark_block():
                return False
            if not self.filemark.add_filemark(self.block.block_number):
                return False
            count -= 1
        return True