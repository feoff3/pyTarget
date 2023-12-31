#    
#    general library, common APIs.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-09-27)
#

import os, struct
from string import *
import array
import string

def do_pack(ary):
    return struct.pack('B'*len(ary), *ary[:])

def do_unpack(buf):
    return list(struct.unpack('B'*len(buf), buf))

def str_2_bool(val):
    if val == 'Yes': return True
    else: return False

def bool_2_str(val):
    if val: return 'Yes'
    else: return 'No'

def str_2_value(buf):
    '''
    string to value
    e.g. 123, 0x123ab, -0x123ab, etc...
    '''
    ret = 0
    neg = 1
    base = 10
    buf = buf.lower()
    if buf[0] == '-':
        neg = -1
        buf = buf[1:]
    if buf[:2] == '0x':
        base = 16
        buf = buf[2:]
    for i in buf:
        ret *= base
        if i.isdigit():
            ret += ord(i) - 48
        else:
            ret += ord(i) - 87
    return ret * neg


def hex_2_byte(buf, offset, size, val):
    '''
    hex to byte
    '''
    offset += size - 1
    lst = do_unpack(buf)
    while val > 0:
        lst[offset] = val % 0x100
        val //= 0x100
        offset -= 1
    return do_pack(lst)

def byte_2_hex(buf, offset, length):
    '''
    byte to hex
    '''
    lst = do_unpack(buf)
    var = lst[offset]
    for i in lst[offset + 1: offset + length]:
        var = var * 0x100 + i
    return var

def array_2_hex(arry, offset, len):
    ''' 
    array to hex
    '''
    if len == 4:
        return (int(arry[offset]) << 24) + (int(arry[offset+1]) << 16) + (int(arry[offset+2]) << 8) + int(arry[offset+3]) 
    val = arry[offset]
    for i in arry[offset + 1: offset + len]:
        val = val * 0x100 + i
    return val

def hex_2_array(val, size):
    '''
    hex to array
    '''
    if size == 4:
        return [(val >> 24) & 0xFF, (val >> 16) & 0xFF, (val >> 8) & 0xFF , (val) & 0xFF] 
    if size == 2:
        return [(val >> 8) & 0xFF , (val) & 0xFF] 

    lst = []
    while val > 0:
        lst.append(val % 0x100)
        val //= 0x100
    while (len(lst) < size):
        lst.append(0)
    lst.reverse()
    return lst

def u8_buf(val):
    return do_pack(hex_2_array(val, 1))
def u16_buf(val):
    return do_pack(hex_2_array(val, 2))
def u24_buf(val):
    return do_pack(hex_2_array(val, 3))
def u32_buf(val):
    return do_pack(hex_2_array(val, 4))
def u64_buf(val):
    return do_pack(hex_2_array(val, 8))
def buf_u8(buf, off=0):
    return byte_2_hex(buf, off, 1)
def buf_u16(buf, off=0):
    return byte_2_hex(buf, off, 2)
def buf_u24(buf, off=0):
    return byte_2_hex(buf, off, 3)
def buf_u32(buf, off=0):
    return byte_2_hex(buf, off, 4)
def buf_u64(buf, off=0):
    return byte_2_hex(buf, off, 8)

def align4(val):
    if val & 0x03: return (4 - val & 0x03)
    return 0

def asc(string):
    return string


DIGITS = string.digits + string.ascii_lowercase
VALUES = {c: d for d, c in enumerate(DIGITS)}

def isdigit(s, base=10):
    return s in DIGITS[:base]

def atoi(x : str, base : int = 10):
    if not 2 <= base <= 36:
        raise ValueError("Only 2 <= base <= 36 currently supported")
    sign = 1
    if x.startswith(("+", "-")):
        if x[0] == "-":
            sign = -1
        x = x[1:]
    value = 0
    for exp, c in enumerate(reversed(x)):
        if c not in VALUES or VALUES[c] >= base:
            raise ValueError(f"{c} is not a valid digit in base {base}")
        value += VALUES[c] * base ** exp
    return sign * value
