#    
#    SES(scsi enclosure service) library
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-11-18)
#    Add all SES2 protocol status page by Wu.Qing-xiu(2009-11-20) 
#

from comm.stdlib import *
from scsi.scsi_proto import *
from scsi.ses_proto import *

#
# Global variable
#
GLOBAL_ENCLOSURE_ID = 0                                     # global enclosure id

#
# SES status code
#
__SES_STATUS_CODE = ( SES_SUPPORTED_PAGE,
                      SES_CONFIGURATION_PAGE,
                      SES_ENCLOSURE_STATUS_PAGE,
                      SES_HELP_TEST_PAGE,
                      SES_STRING_IN_PAGE,
                      SES_THRESHOLD_IN_PAGE,
                      SES_ELEMENT_DESCRIPTOR_PAGE,
                      SES_SHORT_ENCLOSURE_STATUS_PAGE,
                      SES_ENCLOSURE_BUSY_PAGE,
                      SES_ADDITIONAL_ELEMENT_STATUS_PAGE,
                      SES_SUBENCLOSURE_HELP_TEXT_PAGE,
                      SES_SUBENCLOSURE_STRING_IN_PAGE,
                      SES_SUPPORTED_SES_DIAGNOSTIC_PAGES_PAGE,
                      SES_DOWNLOAD_MICROCODE_STATUS_PAGE,
                      SES_SUBENCLOSURE_NICKNAME_STATUS_PAGE)

def IS_STATUS_PAGE(code):
    return code in __SES_STATUS_CODE

def IS_CONTROL_PAGE(code):
    return not IS_STATUS_PAGE(code)

def SET_SES_LENGTH(buf, length):
    buf[2] = (length >> 8) & 0xFF
    buf[3] = length & 0xFF

def GET_ENCLOSURE_ID():
    '''
    Get unique enclosure id
    '''
    global GLOBAL_ENCLOSURE_ID
    GLOBAL_ENCLOSURE_ID += 1
    return GLOBAL_ENCLOSURE_ID


def Diagnostic_Supported_Page(elc):
    '''
    Supported Diagnostic Pages diagnostic page
    '''
    head = [0] * 4
    data = range(SES_OTHER_PAGE)
    SET_SES_LENGTH(head, len(data))                             # not include first 4 bytes
    head += data
    return do_pack(head)

def SES_Configuration_Page(elc):
    '''
    Configuration diagnostic page
    '''

    head = [0] * 4
    head[0] = SES_CONFIGURATION_PAGE
    head[1] = elc.SubEnclosureCnt()                             # Number of secondary subenclosures
    head += hex_2_array(elc.generation_code, 4)                   # Generation code

    buf = elc.EnclosureDescriptorList()                         # Enclosure descriptor list
    buf += elc.ElemTypeHeadList()                               # Element type head list
    buf += elc.ElemTypeDescriptorTextList()                     # element type descriptor text list

    SET_SES_LENGTH(head, len(head) + len(buf))
    return do_pack(head) + buf

def SES_Enclosure_Status_Page(elc):
    '''
    Enclosure Status diagnostic page
    '''
    head = [0] * 4
    head[0] = SES_ENCLOSURE_STATUS_PAGE
    head[1] = 0                                                 # TODO (INVOP INFO NON-CRIT CRIT UNRECOV)
    head += hex_2_array(elc.generation_code, 4)                   # Generation code
    buf = elc.ElemTypeStatusList()                              # Status descriptor list
    SET_SES_LENGTH(head, len(head) + len(buf))
    return do_pack(head) + buf

def SES_Help_Test_Page(elc):
    '''
    Help Text diagnostic page
    '''
    head = [0] * 4
    head[0] = SES_HELP_TEST_PAGE
    buf = elc.help_text
    SET_SES_LENGTH(head, len(head) + len(buf))
    return do_pack(head) + buf

def SES_String_In_Page(elc):
    '''
    String In diagnostic page
    '''
    head = [0] * 4
    head[0] = SES_STRING_IN_PAGE
    buf = elc.string_text
    SET_SES_LENGTH(head, len(head) + len(buf))
    return do_pack(head) + buf

def SES_Threshold_In_Page(elc):
    '''
    Threshold In diagnostic page
    '''
    head = [0] * 4
    head[0] = SES_THRESHOLD_IN_PAGE
    head[1] = 0                                                 # TODO
    head += hex_2_array(elc.generation_code, 4)                   # Generation code
    buf = elc.ThresholdStatusDescriptor()                       # Threshold status descriptor list
    SET_SES_LENGTH(head, len(head) + len(buf))
    return do_pack(head) + buf
    
def SES_Element_Descriptor_Page(elc):
    '''
    Element Descriptor diagnostic page
    '''
    head = [0] * 4
    head[0] = SES_ELEMENT_DESCRIPTOR_PAGE
    head += hex_2_array(elc.generation_code, 4)                   # Generation code
    buf = elc.ElemDescriptorList()                              # Element descriptor by type list
    SET_SES_LENGTH(head, len(head) + len(buf))
    return do_pack(head) + buf

def SES_Short_Enclosure_Status_Page(elc):
    '''
    Short Enclosure Status diagnostic page
    '''
    head = [0] * 4
    head[0] = SES_SHORT_ENCLOSURE_STATUS_PAGE
    head[1] = 0                                                 # TODO (SHORT ENCLOSURE STATUS)
    SET_SES_LENGTH(head, len(head))
    return do_pack(head)

def SES_Enclosure_Busy_Page(elc):
    '''
    Enclosure Busy diagnostic page
    '''
    head = [0] * 4
    head[0] = SES_ENCLOSURE_BUSY_PAGE
    head[1] = 0                                                 # TODO (Vendor specific)
    return do_pack(head)

def SES_Additional_Element_Status_Page(elc):
    '''
    Additional Element Status diagnostic page
    '''
    head = [0] * 4
    head[0] = SES_ADDITIONAL_ELEMENT_STATUS_PAGE
    head += hex_2_array(elc.generation_code, 4)                   # Generation code
                                                                # TODO (Additional Element Status descriptor list)
    SET_SES_LENGTH(head, len(head))
    return do_pack(head)

def SES_SubEnclosure_Help_Text_Page(elc):
    '''
    Subenclosure Help Text diagnostic page
    '''
    head = [0] * 4
    head[0] = SES_SUBENCLOSURE_HELP_TEXT_PAGE
    head[1] = elc.SubEnclosureCnt()
    head += hex_2_array(elc.generation_code, 4)                   # Generation code
    buf = elc.SubEnclosureHelpTextList()                        # Sub Enclosure help text list
    SET_SES_LENGTH(head, len(head) + len(buf))
    return do_pack(head) + buf
    
def SES_Subenclosure_String_In_Page(elc):
    '''
    Subenclosure String In diagnostic page
    '''
    head = [0] * 4
    head[0] = SES_SUBENCLOSURE_STRING_IN_PAGE
    head[1] = elc.SubEnclosureCnt()
    head += hex_2_array(elc.generation_code, 4)                   # Generation code
    buf = elc.SubEnclosureStringTextList()                      # Sub enclosure string in data list (use help text instead)
    SET_SES_LENGTH(head, len(head) + len(buf))
    return do_pack(head) + buf

def SES_Supported_SES_Diangostic_Page(elc):
    '''
    Supported SES Diagnostic Pages diagnostic page
    '''
    head = [0] * 4
    head[0] = SES_SUPPORTED_SES_DIAGNOSTIC_PAGES_PAGE
    head += range(1, SES_OTHER_PAGE)
    SET_SES_LENGTH(head, len(head))
    while len(head) % 4:
        head += [0]
    return do_pack(head)

def SES_Download_Microcode_Status_Page(elc):
    '''
    Download Microcode Status diagnostic page
    '''
    head = [0] * 4
    head[0] = SES_DOWNLOAD_MICROCODE_STATUS_PAGE
    head[1] = elc.SubEnclosureCnt()
    head += hex_2_array(elc.generation_code, 4)                   # Generation code
    buf = elc.SubEnclosureMicrocodeStatusDescriptorList()       # Download microcode status descriptor list
    SET_SES_LENGTH(head, len(head) + len(buf))
    return do_pack(head) + buf
    
def SES_SubEnclosure_Nickname_Status_Page(elc):
    '''
    Subenclosure Nickname Status diagnostic page
    '''
    head = [0] * 4
    head[0] = SES_SUBENCLOSURE_NICKNAME_STATUS_PAGE
    head[1] = elc.SubEnclosureCnt()
    head += hex_2_array(elc.generation_code, 4)                   # Generation code
    buf = elc.SubEnclosureNicknameDescriptorList()              # Sub enclosure nickname status descriptor list
    SET_SES_LENGTH(head, len(head) + len(buf))
    return do_pack(head) + buf

#
# Status page handle url
#
SES_STATUS_PAGE_HANDLE_URL = {SES_SUPPORTED_PAGE                        : Diagnostic_Supported_Page,            # OK
                              SES_CONFIGURATION_PAGE                    : SES_Configuration_Page,               # OK
                              SES_ENCLOSURE_STATUS_PAGE                 : SES_Enclosure_Status_Page,            # OK
                              SES_HELP_TEST_PAGE                        : SES_Help_Test_Page,                   # OK
                              SES_STRING_IN_PAGE                        : SES_String_In_Page,                   # OK
                              SES_THRESHOLD_IN_PAGE                     : SES_Threshold_In_Page,                # OK
                              SES_ELEMENT_DESCRIPTOR_PAGE               : SES_Element_Descriptor_Page,          # OK
                              SES_SHORT_ENCLOSURE_STATUS_PAGE           : SES_Short_Enclosure_Status_Page,      # OK
                              SES_ENCLOSURE_BUSY_PAGE                   : SES_Enclosure_Busy_Page,              # OK
                              SES_ADDITIONAL_ELEMENT_STATUS_PAGE        : SES_Additional_Element_Status_Page,   # TODO
                              SES_SUBENCLOSURE_HELP_TEXT_PAGE           : SES_SubEnclosure_Help_Text_Page,      # OK
                              SES_SUBENCLOSURE_STRING_IN_PAGE           : SES_Subenclosure_String_In_Page,      # OK
                              SES_SUPPORTED_SES_DIAGNOSTIC_PAGES_PAGE   : SES_Supported_SES_Diangostic_Page,    # OK
                              SES_DOWNLOAD_MICROCODE_STATUS_PAGE        : SES_Download_Microcode_Status_Page,   # OK
                              SES_SUBENCLOSURE_NICKNAME_STATUS_PAGE     : SES_SubEnclosure_Nickname_Status_Page}# OK
