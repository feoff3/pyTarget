#
#    scsi enclosure device implementation code
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2010-03-18)
#

import random
from scsi.scsi_dev import *
from scsi.scsi_lib import *
from scsi.ses_lib import *


class Element():
    '''
    class for ses element device
    '''
    def __init__(self, type, descriptor = DEFAULT_ELEMENT_DESCRIPTOR):
        '''
        Element constructor
        @param type: element type
        @param descriptor: element descriptor
        '''
        self.type = type
        # element status
        self.status = SES_OK
        self.data = [0] * 3
        self.hight_critical_threshold = 0
        self.hight_warn_threshold = 0
        self.low_warn_threshold = 0
        self.low_critical_threshold = 0
        # descriptor
        self.descriptor = descriptor


class ElemType():
    '''
    class for element type
    '''
    def __init__(self, type, descriptor = DEFAULT_ELEMENT_TYPE_DESCRIPTOR):
        '''
        Element type constructor
        @param type: element type
        @param descriptor:  element type descriptor
        '''
        self.type = type
        self.descriptor = descriptor
        # overall status
        self.over_all_status = SES_OK
        self.over_all_data = [0] * 3
        self.over_all_hight_critical_threshold = 0
        self.over_all_hight_warn_threshold = 0
        self.over_all_low_warn_threshold = 0
        self.over_all_low_critical_threshold = 0
        # element list
        self.elem_list = []
        self.elem_lock = threading.Lock()
        
    def AddElement(self, el):
        '''
        Add a element into element type list
        @param el: element handle
        @return: True for success, False for failed
        '''
        self.elem_lock.acquire()
        self.elem_list.append(el)
        self.elem_lock.release()
        return True
        
        
class Enclosure(Lun):
    '''
    Class for virtual scsi enclosure device
    '''

    def __init__(self, id, dev, descriptor=DEFAULT_ENCLOSURE_DESCRIPTOR):
        '''
        initialize scsi enclosure device
        @param id: device id
        @param path: virtual device DevObj
        '''
        Lun.__init__(self, id, TYPE_ENCLOSURE, dev)
        # enclosure attribute
        self.enclosure_id = 0                                       # enclosure id
        self.local_id = [0] * 8                                     # local id
        self.process_count = 0                                      # Number of enclosure service process 
        self.relative_es_id = 0                                     # Relative enclosure service process identifier
        self.generation_code = 0                                    # Generation code
        # vender info
        self.vendor = DEVICE_VENDOR                                 # length 8 byte
        self.product = DEVICE_PRODUCT                               # length 16 byte
        self.reversion = DEVICE_VERSION                             # length 4 byte
        # string
        self.descriptor = descriptor                                # enclosure descriptor
        self.help_text = DEFAULT_HELP_TEXT                          # hex text
        self.string_text = DEFAULT_STRING_TEXT                      # string text
        # nick name
        self.nick_name = DEFAULT_NICK_NAME                          # length 32 bytes 
        self.nick_name_status = 0
        self.nick_name_addi_status = 0
        self.nick_name_language = 0 
        # down microcode & status
        self.microcode = do_pack([0] * 128)
        self.microcode_status = 0
        self.microcode_addi_status = 0

        # sub enclosure
        self.sub_enclosure_list = []
        self.sub_enclosure_lock = threading.Lock()
        
        # element type
        self.elemtype_list = []
        self.elemtype_list_lock = threading.Lock()

    def initial(self, descriptor=None):
        '''
        Initialize scsi enclosure device
        @param descriptor: enclosure descriptor
        @return: True for success, False for failed
        '''
        if descriptor:
            self.descriptor = descriptor
        DBG_PRN('Enclosure(%s)' % self.path, ': initialize finish!')
        return True
        
    def AddElementType(self, elt):
        '''
        Add element type into element type list
        @param elt: element type handle
        @return: True for success, False fur failed
        '''
        self.elemtype_list_lock.acquire()
        self.elemtype_list.append(elt)
        self.elemtype_list_lock.release()
        return True

    def GetElementType(self, type):
        '''
        Get element type
        @param type: element type
        @return: None for failed, other for success
        '''
        ret = None
        self.elemtype_list_lock.acquire()
        for elt in self.elemtype_list:
            if elt.type == type:
                ret = elt
                break
        self.elemtype_list_lock.release()
        return ret
        
    def DelElementType(self, _type):
        '''
        Remove element type
        @param type: element type
        @return: True for success, False for failed
        '''
        ret = False
        self.elemtype_list_lock.acquire()
        for elt in self.elemtype_list:
            if elt.type == type:
                self.elemtype_list.remove(elt)
                ret = True
                break
        self.elemtype_list_lock.release()
        return ret
    
    def AddSubEnclosure(self, es):
        '''
        Add sub enclosure device
        @param es: sub enclosure
        @return: True for success, False for failed
        '''
        #
        # update enclosure id & local id
        #
        self.sub_enclosure_lock.acquire()
        es.enclosure_id = GET_ENCLOSURE_ID()
        self.local_id = hex_2_array(len(self.sub_enclosure_list), 8)
        self.sub_enclosure_list.append(es)
        self.sub_enclosure_lock.release()
        return True

    def SetNickName(self, name):
        '''
        Set nick name
        @param name: enclosure nick name
        @return: True for success, False for failed
        '''
        if name and len(name) == 32:
            self.nick_name = name
            return True
        return False
    
    def SetHelpText(self, text):
        '''
        Set enclosure help text
        @param text: enclosure help text
        @return: True for success, False for failed
        '''
        if text:
            self.help_text = text
            return True
        return False

    def SetStringText(self, text):
        '''
        Set enclosure string text
        @param text: enclosure string text
        @return: True for success, False for failed
        '''
        if text:
            self.string_text = text
            return True
        return False

    
    def SubEnclosureCnt(self):
        '''
        Sub enclosure count
        '''
        cnt = len(self.sub_enclosure_list)
        self.sub_enclosure_lock.acquire()
        for es in self.sub_enclosure_list:
            cnt += es.SubEnclosureCnt()
        self.sub_enclosure_lock.release()
        return cnt

    def EnclosureDescriptorList(self):
        '''
        Enclosure descriptor list
        '''
        buf = do_pack([(((self.relative_es_id & 0x07)<<4)|(self.process_count & 0x07)) & 0xFF,
                          self.enclosure_id,
                          len(self.elemtype_list),
                          36])

        assert(len(self.local_id) == 8)
        assert(len(self.vendor) == 8)
        assert(len(self.product) == 16)
        assert(len(self.reversion) == 4)

        buf += do_pack(self.local_id) 
        buf += self.vendor
        buf += self.product
        buf += self.reversion

        self.sub_enclosure_lock.acquire()
        for es in self.sub_enclosure_list:
            buf += es.EnclosureDescriptorList()
        self.sub_enclosure_lock.release()

        return buf

    def ElemTypeHeadList(self):
        '''
        Element type head list
        '''
        buf = ''

        self.elemtype_list_lock.acquire()
        for elt in self.elemtype_list:
            buf += do_pack([ elt.type,
                                len(elt.elem_list),
                                self.enclosure_id,
                                len(elt.descriptor)])
        self.elemtype_list_lock.release()

        self.sub_enclosure_lock.acquire()
        for es in self.sub_enclosure_list:
            buf += es.ElemTypeHeadList()
        self.sub_enclosure_lock.release()

        return buf
    
    def ElemTypeDescriptorTextList(self):
        '''
        Element type descriptor text list
        '''
        buf = ''

        self.elemtype_list_lock.acquire()
        for elt in self.elemtype_list:
            buf += elt.descriptor
        self.elemtype_list_lock.release()

        self.sub_enclosure_lock.acquire()
        for es in self.sub_enclosure_list:
            buf += es.ElemTypeDescriptorTextList()
        self.sub_enclosure_lock.release()
        
        return buf
    
    def ElemTypeStatusList(self):
        '''
        Element type status list
        '''
        buf = ''

        self.elemtype_list_lock.acquire()
        for elt in self.elemtype_list:
            # over all status
            assert(len(elt.over_all_data) == 3)
            buf += do_pack([elt.over_all_status])
            buf += do_pack(elt.over_all_data) 

            # element status
            elt.elem_lock.acquire()
            for el in elt.elem_list:
                assert(len(el.data) == 3)
                buf += do_pack([el.status])
                buf += do_pack(el.data)
            elt.elem_lock.release()
        self.elemtype_list_lock.release()

        self.sub_enclosure_lock.acquire()
        for es in self.sub_enclosure_list:
            buf += es.ElemTypeStatusList()
        self.sub_enclosure_lock.release()

        return buf

    def ThresholdStatusDescriptor(self):
        '''
        Threshold status descriptor
        '''
        buf = ''

        self.elemtype_list_lock.acquire()
        for elt in self.elemtype_list:
            buf += do_pack([elt.over_all_hight_critical_threshold,
                               elt.over_all_hight_warn_threshold,
                               elt.over_all_low_warn_threshold,
                               elt.over_all_low_critical_threshold])
            elt.elem_lock.acquire()
            for el in elt.elem_list:
                buf += do_pack([el.hight_critical_threshold,
                                   el.hight_warn_threshold,
                                   el.low_warn_threshold,
                                   el.low_critical_threshold])
            elt.elem_lock.release()
        self.elemtype_list_lock.release()
        
        self.sub_enclosure_lock.acquire()
        for es in self.sub_enclosure_list:
            buf += es.ThresholdStatusDescriptor()
        self.sub_enclosure_lock.release()
        return buf
    
    def ElemDescriptorList(self):
        '''
        element descriptor list.
        '''
        buf = ''
        self.elemtype_list_lock.acquire()
        for elt in self.elemtype_list:
            # over all descriptor
            buf += do_pack([0, 0])                                   # Reserved
            buf += do_pack(hex_2_array(len(elt.descriptor), 2))        # Element type descriptor length
            buf += elt.descriptor                                       # Element type descriptor

            # element descriptor
            elt.elem_lock.acquire()
            for el in elt.elem_list:
                buf += do_pack([0, 0])                               # Reserved
                buf += do_pack(hex_2_array(len(el.descriptor), 2))     # Element descriptor length
                buf += el.descriptor                                    # Element type descriptor          
            elt.elem_lock.release()
        self.elemtype_list_lock.release()

        self.sub_enclosure_lock.acquire()
        for es in self.sub_enclosure_list:
            buf += es.ElemDescriptorList()
        self.sub_enclosure_lock.release()

        return buf
    
    def SubEnclosureHelpTextList(self):
        '''
        sub enclosure help text list
        '''
        buf = do_pack([0, self.enclosure_id])                # Sub enclosure identifier
        buf += do_pack(hex_2_array(len(self.help_text), 2))    # Sub enclosure help text length
        buf += self.help_text                                   # Sub enclosure help text

        self.sub_enclosure_lock.acquire()
        for es in self.sub_enclosure_list:
            buf += es.SubEnclosureHelpTextList()
        self.sub_enclosure_lock.release()

        return buf
    
    def SubEnclosureStringTextList(self):
        '''
        sub enclosure string text list
        '''
        buf = do_pack([0, self.enclosure_id])                # Sub enclosure identifier
        buf += do_pack(hex_2_array(len(self.string_text), 2))  # Sub enclosure string text length
        buf += self.string_text                                 # Sub enclosure string text

        self.sub_enclosure_lock.acquire()
        for es in self.sub_enclosure_list:
            buf += es.SubEnclosureStringTextList()
        self.sub_enclosure_lock.release()
        return buf
    
    def SubEnclosureMicrocodeStatusDescriptorList(self):
        '''
        Download microcode status descriptor list
        '''
        buf = do_pack([0,
                          self.enclosure_id,
                          self.microcode_status,
                          self.microcode_addi_status])
        buf += do_pack(hex_2_array(1024, 4))
        buf += do_pack([0, 0, 0])
        buf += do_pack([self.enclosure_id])
        buf += do_pack([0, 0, 0, 0])

        self.sub_enclosure_lock.acquire()
        for es in self.sub_enclosure_list:
            buf += es.SubEnclosureMicrocodeStatusDescriptorList()
        self.sub_enclosure_lock.release()

        return buf

    def SubEnclosureNicknameDescriptorList(self):
        '''
        Subenclosure nickname status descriptor list
        '''
        assert(len(self.nick_name) == 32)
        buf = do_pack([0,
                          self.enclosure_id,
                          self.nick_name_status,
                          self.nick_name_addi_status,
                          0,
                          0])
        buf += do_pack(hex_2_array(self.nick_name_language, 2))
        buf += self.nick_name

        self.sub_enclosure_lock.acquire()
        for es in self.sub_enclosure_list:
            buf += es.SubEnclosureNicknameDescriptorList()
        self.sub_enclosure_lock.release()
        return buf
    
    def EnclosureService(self, code):
        '''
        Enclosure service process
        @param code: ses page code
        @return: None for SES lib unsupported, other for success
        '''
        buf = None
        if IS_STATUS_PAGE(code):
            if SES_STATUS_PAGE_HANDLE_URL.has_key(code):
                buf = SES_STATUS_PAGE_HANDLE_URL[code](self)
            else:
                DBG_WRN('Unknown or obsolete page %02x' % code)
        else:
            pass
        return buf

#
# Simulator Hardware topology
#
def NEW_Enclosure(id, path):

    ###################################################################
    #                                Local
    ###################################################################
    bs = Enclosure(id, path)

    # local power
    elt = ElemType(ELEM_POWER_SUPPLY, 'local power support')
    for i in range(2):
        el = Element(ELEM_POWER_SUPPLY, 'Power support %d' % i)
        elt.AddElement(el)
    bs.AddElementType(elt)

    # local slot
    elt = ElemType(ELEM_ARRAY_DEVICE, 'local array device')
    for i in range(12):
        el = Element(ELEM_ARRAY_DEVICE, 'Slot#%d' % i)
        elt.AddElement(el)
    bs.AddElementType(elt)

    # local fan
    elt = ElemType(ELEM_COOLING, 'local cooling device')
    for i in range(3):
        el = Element(ELEM_COOLING, 'Fan#%d' % i)
        elt.AddElement(el)
    bs.AddElementType(elt)

    # local temp
    elt = ElemType(ELEM_TEMPERATURE_SENSOR, 'local temperature sensor')
    for i in range(3):
        el = Element(ELEM_TEMPERATURE_SENSOR, 'Temperature#%d' % i)
        elt.AddElement(el)
    bs.AddElementType(elt)

    # local voltage
    elt = ElemType(ELEM_VOLTAGE_SENSOR, 'local voltage sensor')
    for i in range(5):
        el = Element(ELEM_VOLTAGE_SENSOR, 'voltage#%d' % i)
        elt.AddElement(el)
    bs.AddElementType(elt)

    exp = bs

    ###################################################################
    #                                Jbod
    ###################################################################
    for id in range(1,4):
        jb = Enclosure(0, 'jbod_enclosure_%d' % id, 'jbod enclosure device %d' %id)
        # power
        elt = ElemType(ELEM_POWER_SUPPLY, 'Destoryer power support')
        for i in range(2):
            el = Element(ELEM_POWER_SUPPLY, 'Power support %d' % i)
            elt.AddElement(el)
        jb.AddElementType(elt)

        # slot
        elt = ElemType(ELEM_ARRAY_DEVICE, 'Destoryer array device')
        for i in range(12):
            el = Element(ELEM_ARRAY_DEVICE, 'Slot#%d' % i)
            elt.AddElement(el)
        jb.AddElementType(elt)

        # fan
        elt = ElemType(ELEM_COOLING, 'Destoryer cooling device')
        for i in range(2):
            el = Element(ELEM_COOLING, 'Fan#%d' % i)
            elt.AddElement(el)
        jb.AddElementType(elt)

        # temp
        elt = ElemType(ELEM_TEMPERATURE_SENSOR, 'Destoryer temperature sensor')
        for i in range(3):
            el = Element(ELEM_TEMPERATURE_SENSOR, 'Temperature#%d' % i)
            elt.AddElement(el)
        jb.AddElementType(elt)

        # voltage
        elt = ElemType(ELEM_VOLTAGE_SENSOR, 'Destoryer voltage sensor')
        for i in range(5):
            el = Element(ELEM_VOLTAGE_SENSOR, 'voltage#%d' % i)
            elt.AddElement(el)
        jb.AddElementType(elt)

        exp.AddSubEnclosure(jb)
        jb = exp        
    return bs
