#    
#    SES protocol defines.
#    
#    Modify history:    
#    -----------------------------------------------------------------
#    Create by Wu.Qing-xiu (2009-11-21)
#
#
# element type
#
ELEM_UNSPECIFIED                                            = 0x00
ELEM_DEVICE                                                 = 0x01
ELEM_POWER_SUPPLY                                           = 0x02
ELEM_COOLING                                                = 0x03
ELEM_TEMPERATURE_SENSOR                                     = 0x04
ELEM_DOOR_LOCK                                              = 0x05
ELEM_AUDIBLE_ALARM                                          = 0x06
ELEM_ENCLOSURE_SERVICES_CONTROLLER                          = 0x07
ELEM_SCC_CONTROLLER_ELECTRONICS                             = 0x08
ELEM_NONVOLATILE_CACHE                                      = 0x09
ELEM_INVALID_OPERATION_REASON                               = 0x0A
ELEM_UNINTERRUPTIBLE_POWER_SUPPLY                           = 0x0B
ELEM_DISPLAY                                                = 0x0C
ELEM_KEY_PAD_ENTRY                                          = 0x0D
ELEM_ENCLOSURE                                              = 0x0E
ELEM_SCSI_PORT_TRANSCEIVER                                  = 0x0F
ELEM_LANGUAGE                                               = 0x10
ELEM_COMMUNICATION_PORT                                     = 0x11
ELEM_VOLTAGE_SENSOR                                         = 0x12
ELEM_CURRENT_SENSOR                                         = 0x13
ELEM_SCSI_TARGET_PORT                                       = 0x14
ELEM_SCSI_INITIATOR_PORT                                    = 0x15
ELEM_SIMPLE_SUBENCLOSURE                                    = 0x16
ELEM_ARRAY_DEVICE                                           = 0x17
ELEM_SAS_EXPANDER                                           = 0x18
ELEM_SAS_CONNECTOR                                          = 0x19
ELEM_RESERVED                                               = 0x1F 
    

#
# SES page code
#
SES_SUPPORTED_PAGE                                          = 0x00
SES_CONFIGURATION_PAGE                                      = 0x01
SES_ENCLOSURE_CONTROL_PAGE                                  = 0x02
SES_ENCLOSURE_STATUS_PAGE                                   = 0x02
SES_HELP_TEST_PAGE                                          = 0x03
SES_STRING_OUT_PAGE                                         = 0x04
SES_STRING_IN_PAGE                                          = 0x04
SES_THRESHOLD_OUT_PAGE                                      = 0x05
SES_THRESHOLD_IN_PAGE                                       = 0x05                          
SES_ELEMENT_DESCRIPTOR_PAGE                                 = 0x07
SES_SHORT_ENCLOSURE_STATUS_PAGE                             = 0x08
SES_ENCLOSURE_BUSY_PAGE                                     = 0x09
SES_ADDITIONAL_ELEMENT_STATUS_PAGE                          = 0x0A
SES_SUBENCLOSURE_HELP_TEXT_PAGE                             = 0x0B
SES_SUBENCLOSURE_STRING_OUT_PAGE                            = 0x0C
SES_SUBENCLOSURE_STRING_IN_PAGE                             = 0x0C
SES_SUPPORTED_SES_DIAGNOSTIC_PAGES_PAGE                     = 0x0D
SES_DOWNLOAD_MICROCODE_CONTROL_PAGE                         = 0x0E
SES_DOWNLOAD_MICROCODE_STATUS_PAGE                          = 0x0E    
SES_SUBENCLOSURE_NICKNAME_CONTROL_PAGE                      = 0x0F
SES_SUBENCLOSURE_NICKNAME_STATUS_PAGE                       = 0x0F
SES_OTHER_PAGE                                              = 0x10

#
# SES status
#
SES_UNSUPPORTED                                             = 0x00
SES_OK                                                      = 0x01
SES_CRITICAL                                                = 0x02
SES_NONCRITICAL                                             = 0x03
SES_UNRECOVERABLE                                           = 0x04
SES_NOTINSTALLED                                            = 0x05
SES_UNKNOWN                                                 = 0x06
SES_NOTAVAILABLE                                            = 0x07
SES_RESERVED                                                = 0x08

#
# Defect variable
#
DEFAULT_NICK_NAME = 'default enclosure nick name     '      # 32 bytes
DEFAULT_ENCLOSURE_DESCRIPTOR = 'Default enclosure descriptor'
DEFAULT_ELEMENT_TYPE_DESCRIPTOR = 'Default element type descriptor'
DEFAULT_ELEMENT_DESCRIPTOR = 'Default element descriptor'

DEFAULT_HELP_TEXT = 'Default scsi enclosure service help text'
DEFAULT_STRING_TEXT = 'Default scsi enclosure service primary string text'