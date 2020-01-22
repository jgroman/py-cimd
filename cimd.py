""" Nokia SMS Center 8.0 CIMD protocol implementation
"""
# (C) JG 2006

import string
import re

class CIMDError(Exception):
    """Base class for exceptions in this module."""
    pass

class CIMD:

    # Variables
    packetNumber = 0

    # CIMD special characters
    specChar = {
        'nul' : '\x00',
        'stx' : '\x02',
        'etx' : '\x03',
        'tab' : '\x09'
    }

    
    # Class constructor
    def __init__(self):
        """ Class constructor """
        self.resetPacketNumber()
        
    def resetPacketNumber(self):
        """ Resets packet number to 1 """
        self.packetNumber = 1

    def incPacketNumber(self):
        """ Increment packet number by 2 and wrap around 255 """
        self.packetNumber += 2
        if self.packetNumber > 255:
            self.resetPacketNumber()

    def getPacketNumber(self):
        """ Returns current packet number """
        return self.packetNumber
    
    def setPacketNumber(self, newPacketNumber):
        """ Update internal packet number
        
        New packet number must be odd from 1 to 255 """
        npn = newPacketNumber
        if npn>0 and npn<256 and npn % 2 == 1:
            self.packetNumber = npn
        else:
            raise CIMDError('Invalid packet number')

    def calcChecksum(self, message):
        """ Returns 8-bit message checksum """
        checksum = 0
        for byte in message:
            checksum += ord(byte)
            checksum &= 0xFF
        return checksum

    def decode(self,message):
        """ Returns human-readable representation of CIMD message """
        output = ""
        if message is None:
            return None
        for byte in message:
            if ord(byte)>31:
                output += byte
            elif byte == self.specChar['nul']:
                output += '{NUL}'
            elif byte == self.specChar['stx']:
                output += '{STX}'
            elif byte == self.specChar['etx']:
                output += '{ETX}'
            elif byte == self.specChar['tab']:
                output += '{TAB}'
        return output

    def encode(self,message):
        """ Converts text to CIMD-compliant message """
        output = ""
        if message is None:
            return None
        ptr = 0
        while ptr < len(message):
            if message[ptr] != '{':
                output += message[ptr]
                ptr += 1
            else:
                specCharId = string.lower(message[ptr+1:ptr+4])
                output += self.specChar[specCharId]
                ptr += 5
        return output

    def createHeader(self, opcode, packet_no=None):
        """ Returns valid CIMD msg header and updates packet no """
        if type(opcode) is str:
            opcode = int(opcode)
        opcode = '%02d' % opcode
        message = self.specChar['stx'] + opcode + ':'
        if packet_no is None:              # Current packet_no is used...
            packet_no = self.packetNumber
            self.incPacketNumber()       # ... and updated
        message += '%03d' % packet_no   # 0-padded ASCII packet number
        message += self.specChar['tab']
        return message

    def createParamBlock(self,param_code,param_value):
        """ Returns CIMD compliant parameter block """
        if type(param_code) is not int:
            param_code = int(param_code)
        param_code = '%03d' % param_code
        if type(param_value) is int:
            param_value = repr(param_value)
        return param_code + ':' + param_value + self.specChar['tab']
    
    def createTrailer(self,message=None):
        """ Returns message trailer
        
        Checksum is computed only if message is given."""
        trailer = ""
        if message is not None and message != "":
            if type(message) is not str:
                raise CIMDError('Invalid createTrailer parameter')
            else:
                trailer = '%02X' % self.calcChecksum(message)
        return trailer + self.specChar['etx']
    
    def createMessage(self, opCode, listOfParamTuples=None, packetNo=None, useChecksum=False):
        """ Builds complete message from opcode and list of parameter tuples """
        
        output = self.createHeader(opCode,packetNo)
        if listOfParamTuples is not None:
            for tuple in listOfParamTuples:
                output += self.createParamBlock(tuple[0],tuple[1])
        if useChecksum:
            output += self.createTrailer(output)
        else:
            output += self.createTrailer()
        return output
        

    def extractParamValue(self, message, paramCode):
        """Extracts value of the given parameter from the msg.
        
        If the parameter is not present, None is returned."""

        if type(paramCode) is str:
            if len(paramCode) == 0:
                return None
            else:
                paramCode = int(paramCode)

        value = None
        paramCode = '%03d' % paramCode
        searchPattern = self.specChar['tab']+ paramCode + r":(?P<value>\w*)"
        reObj = re.compile(searchPattern)
        resultObj = reObj.search(message)
        if resultObj is not None:
            value = resultObj.groupdict()['value']
        return value

    def extractAllParamValues(self, message):
        """ Extracts all available parameters into dictionary """
        
        searchPattern = self.specChar['tab']+r"(?P<parID>\d{3}):(?P<value>\w*)"
        reObj = re.compile(searchPattern)
        return reObj.findall(message)
    

class SMSC:
    """ SMSC communication and status data """

    # CIMD opcodes and response codes
    opCode = {
        'login'                 : "01",
        'login_resp'            : "51",
        'logout'                : "02",
        'logout_resp'           : "52",
        'submit_msg'            : "03",
        'submit_msg_resp'       : "53",
        'enq_msg_status'        : "04",
        'enq_msg_status_resp'   : "54",
        'delivery_req'          : "05",
        'delivery_req_resp'     : "55",
        'cancel_msg'            : "06",
        'cancel_msg_resp'       : "56",
        'deliver_msg'           : "20",
        'deliver_msg_resp'      : "70",
        'deliver_status_rep'    : "23",
        'deliver_status_rep_resp' : "73",
        'set'                   : "08",
        'set_resp'              : "58",
        'get'                   : "09",
        'get_resp'              : "59",
        'alive'                 : "40",
        'alive_resp'            : "90",
        'general_error_resp'    : "98",
        'nack'                  : "99"
    }

    # CIMD Symbols
    symbol = {
        'user_id'               : "010",    # String, max 32 chars
        'password'              : "011",    # String, max 32 chars
        'subaddr'               : "012",    # Integer, max. length 3, values 0-9
        'window_size'           : "019",    # Integer, max. length 3, values 1-128
        'dest_addr'             : "021",
        'orig_addr'             : "023",
        'orig_imsi'             : "026",
        'alpha_orig_addr'       : "027",    # String, max.length 11, only alphanumeric chars and space allowed
        'orig_vmsc_addr'        : "028",
        'data_coding_scheme'    : "030",    # Integer, max. length 3, values 0-255
        'user_data_header'      : "032",
        'user_data'             : "033",
        'user_data_binary'      : "034",
        'transport_type'        : "041",    # Obsolete
        'msg_type'              : '042',    # Obsolete
        'more_msgs'             : '044',    # Integer, max.length 1, values 0-1
        'oper_timer'            : '045',    # Obsolete
        'dialogue_id'           : '046',    # Obsolete
        'ussd_phase'            : '047',    # Obsolete
        'service_code'          : '048',
        'validity_period_rel'   : '050',
        'validity_period_abs'   : '051',
        'protocol_id'           : '052',
        'first_deli_time_rel'   : '053',
        'fisrt_deli_time_abs'   : '054',
        'reply_path'            : '055',
        'status_report_req'     : '056',
        'cancel_enabled'        : '058',
        'cancel_mode'           : '059',
        'serv_centre_timestamp' : '060',    # Integer, max.length 12, 'yymmddhhmmss'
        'status_code'           : '061',    # Integer, max.length 2, values 0-9
        'status_error_code'     : '062',
        'discharge_time'        : '063',    # Integer, max.length 12, 'yymmddhhmmss'
        'tariff_class'          : '064',
        'service_descr'         : '065',
        'msg_count'             : '066',
        'priority'              : '067',
        'deli_req_mode'         : '068',
        'serv_center_addr'      : '069',
        'get_param'             : '500',
        'mc_time'               : '501',    # Integer, max. length 12, 'yymmddhhmmss'
        'error_code'            : "900",
        'error_text'            : "901"
    }

    # CIMD communication errors
    commError = {
        # GENERAL error codes
        0 : 'No error',
        1 : 'Unexpected operation',
        2 : 'Syntax error',
        3 : 'Unsupported parameter',
        4 : 'Connection to MC lost',
        5 : 'No response from MC',
        6 : 'General system error',
        7 : 'Cannot find information',
        8 : 'Parameter formatting error',
        9 : 'Requested operation failed',
        10: 'Temporary congestion error',
        # LOGIN error codes
        100 : 'Invalid login',
        101 : 'Incorrect access type',
        102 : 'Too many users with this login ID',
        103 : 'Login refused by SMSC',
        104 : 'Invalid window size',
        105 : 'Windowing disabled',
        106 : 'Virtual SMS Center-based barring',
        107 : 'Invalid subaddr',
        108 : 'Alias account, login refused',
        # SUBMIT MESSAGE error codes:
        300 : 'Incorrect destination address',
        301 : 'Incorrect number of destination addresses',
        302 : 'Syntax error in user data parameter',
        303 : 'Incorrect bin/head/normal user data parameter combination',
        304 : 'Incorrect dcs parameter usage',
        305 : 'Incorrect validity period parameters usage',
        306 : 'Incorrect originator address usage',
        307 : 'Incorrect PID parameter usage',
        308 : 'Incorrect first delivery parameter usage',
        309 : 'Incorrect reply path usage',
        310 : 'Incorrect status report request parameter usage',
        311 : 'Incorrect cancel enabled parameter usage',
        312 : 'Incorrect priority parameter usage',
        313 : 'Incorrect tariff class parameter usage',
        314 : 'Incorrect service description parameter usage',
        315 : 'Incorrect transport type parameter usage',
        316 : 'Incorrect message type parameter usage',
        318 : 'Incorrect MMs parameter usage',
        319 : 'Incorrect operation timer parameter usage',
        320 : 'Incorrect dialogue ID parameter usage',
        321 : 'Incorrect alpha originator address usage',
        322 : 'Invalid data for alphanumeric originator',
        323 : 'Online closed user group rejection',
        324 : 'Licence expired',
        # ENQUIRE MESSAGE STATUS error codes:
        400 : 'Incorrect address parameter usage',
        401 : 'Incorrect scts parameter usage',
        # DELIVERY REQUEST error codes:
        500 : 'Incorrect scts parameter usage',
        501 : 'Incorrect mode parameter usage',
        502 : 'Incorrect parameter combination',
        # CANCEL MESSAGE error codes:
        600 : 'Incorrect scts parameter usage',
        601 : 'Incorrect addresss parameter usage',
        602 : 'Incorrect mode parameter usage',
        603 : 'Incorrect parameter combination',
        # DELIVER MESSAGE error codes:
        700 : 'Delivery OK / waiting for delivery',
        710 : 'Generic failure',
        711 : 'Unsupported DCS',
        712 : 'Unsupported UDH',
        730 : 'Unknown subscriber',          
        # SET error codes
        800 : 'Changing password failed',
        801 : 'Changing password not allowed',
        # GET error codes
        900 : 'Unsupported item requested'
    }
    
    # CIMD status error codes
    statusError = {
        # SMSC error codes
        0 : 'No error',
        1 : 'Unknown subscriber',
        9 : 'Illegal subscriber',
        11 : 'Teleservice not provisioned',
        13 : 'Call barred',
        15 : 'OCUG reject',
        19 : 'No SMS support in MS',
        20 : 'Error in MS',
        21 : 'Facility not supported',
        22 : 'Memory capacity exceeded',
        29 : 'Absent subscriber',
        30 : 'MS busy for MT-SMS',
        36 : 'Network/Protocol failure',
        44 : 'Illegal equipment',
        60 : 'No paging response',
        61 : 'GMSC congestion',
        63 : 'HLR timeout',
        64 : 'MSC/SGSN_timeout',
        70 : 'SMRSE/TCP error',
        72 : 'MT congestion',
        75 : 'GPRS suspended',
        80 : 'No paging response via MSC',
        81 : 'IMSI detached',
        82 : 'Roaming restriction',
        83 : 'Deregistered in HLR for GSM',
        84 : 'Purged for GSM',
        85 : 'No paging response via SGSN',
        86 : 'GPRS detached',
        87 : 'Deregistered in HLR for GPRS',
        88 : 'The MS purged for GPRS',
        89 : 'Unidentified subscriber via MSC',
        90 : 'Inidentified subscriber via SGSN',
        112 : 'Originator missing credit on prepaid account',
        113 : 'Destination missing credit on prepaid account',
        114 : 'Error in prepaid system',
        # USSD center connection errors
        750 : 'Release, call barred',
        751 : 'Release, system failure',
        752 : 'Release, data missing',
        753 : 'Release, unexpected data value',
        754 : 'Release, absent subscriber',
        755 : 'Release, illegal subscriber',
        756 : 'Release, illegal equipment',
        757 : 'Release, unknown alphabet',
        758 : 'Release, USSD busy',
        759 : 'Relase, operation timer expired',
        760 : 'Release, unexpected primitive',
        761 : 'Release, wait timer expired',
        762 : 'Release, data error',
        763 : 'Release, too long USSD data',
        764 : 'Release, unknown MS address',
        765 : 'Release, network congestion',
        766 : 'Release, internal congestion',
        767 : 'Release, no network connection',
        768 : 'Release, USSD not supported'
    }

    def __init__(self):
        self.useChecksum = False
        self.cimd = CIMD()
        
    def setPacketNumber(self,newPacketNumber):
        self.cimd.setPacketNumber(newPacketNumber)

    def setChecksumUsage(self, newStatus):
        """ Sets checksum usage status."""
        if newStatus != True and newStatus != False:
            raise CIMDError('Invalid checksum usage status')
        self.useChecksum = newStatus

    def login(self, userID, password, subAddr=None, windowSize=None):
        """Creates login message.
        
            Parameters:
                userID --- login name
                password
                subaddr --- unique index for application instance
                windowSize --- window size used for submitting messages
        """
        opCode = self.opCode['login']
        if len(repr(userID))>32:
            raise CIMDError('User ID too long')
        paramList = [(self.symbol['user_id'],userID)]         # Username
        if len(repr(password))>32:
            raise CIMDError('Password too long')
        paramList.append((self.symbol['password'],password))  # Password
        if subAddr is not None:
            if len(repr(subAddr))>3:
                raise CIMDError('Subaddress too high')
            else:
                paramList.append((self.symbol['subaddr'],subAddr))
        if windowSize is not None:
            if type(windowSize) is str:
                windowSize = int(windowSize)
            if windowSize>128:
                raise CIMDError('Window size too high')
            else:
                paramList.append((self.symbol['window_size'],windowSize))
        return self.cimd.createMessage(opCode,paramList,None,self.useChecksum)

    def logout(self):
        """ Creates logout message """
        opCode = self.opCode['logout']
        return self.cimd.createMessage(opCode,[],None,self.useChecksum)

    def encodeTextMsgParams(self,destAddr=None,origAddr=None,origIMSI=None,alphaOrigAddr=None,
                                origVMSC=None,dataCoding=None,userDataHeader=None,userData=None,
                                userDataBinary=None,moreMsgs=None,validPeriodRel=None,
                                validPeriodAbs=None,protoID=None,firstDelivRel=None,
                                firstDelivAbs=None,replyPath=None,statusReport=None,
                                cancelEnabled=None,servCentreTimestamp=None,tariffClass=None,
                                servDescr=None,priority=None,servCentreAddr=None,
                                statusCode=None,dischargeTime=None):
        """ Creates list of tuples from text message parameters """

        # General dependency checks
        if userData is not None and userDataBinary is not None:
            raise CIMDError('Only one type of user data allowed.')
        if validPeriodRel is not None and validPeriodAbs is not None:
            raise CIMDError('Only one validity period type allowed.')
        if firstDelivRel is not None and firstDelivAbs is not None:
            raise CIMDError('Only one type of first delivery time allowed.')
        
        # Message buildup
        paramList=[]
        if destAddr is not None:
            paramList.append((self.symbol['dest_addr'],destAddr))
        if origAddr is not None:
            paramList.append((self.symbol['orig_addr'],origAddr))
        if origIMSI is not None:
            paramList.append((self.symbol['orig_imsi'],origIMSI))
        if alphaOrigAddr is not None:
            if type(alphaOrigAddr) is str and len(alphaOrigAddr)<12:
                paramList.append((self.symbol['alpha_orig_addr'],alphaOrigAddr))
            else:
                raise CIMDError('Invalid alpha originating address.')                
        if origVMSC is not None:
            paramList.append((self.symbol['orig_vmsc_addr'],origVMSC))
        if dataCoding is not None:
            if type(dataCoding) is not str:
                dataCoding = repr(dataCoding)
            if eval(dataCoding)>=0 and eval(dataCoding)<256:
                paramList.append((self.symbol['data_coding_scheme'],dataCoding))
            else:
                raise CIMDError('Invalid data coding scheme.')
        if userDataHeader is not None:
            paramList.append((self.symbol['user_data_header'],userDataHeader))
        if userData is not None:
            paramList.append((self.symbol['user_data'],userData))
        if userDataBinary is not None:
            paramList.append((self.symbol['user_data_binary'],userDataBinary))
        if moreMsgs is not None:
            paramList.append((self.symbol['more_msgs'],moreMsgs))
        if validPeriodRel is not None:
            paramList.append((self.symbol['validity_period_rel'],validPeriodRel))
        if validPeriodAbs is not None:
            paramList.append((self.symbol['validity_period_abs'],validPeriodAbs))
        if protoID is not None:
            paramList.append((self.symbol['protocol_id'],protoID))
        if firstDelivRel is not None:
            paramList.append((self.symbol['first_deli_time_rel'],firstDelivRel))
        if firstDelivAbs is not None:
            paramList.append((self.symbol['first_deli_time_abs'],firstDelivAbs))
        if replyPath is not None:
            paramList.append((self.symbol['reply_path'],replyPath))
        if statusReport is not None:
            paramList.append((self.symbol['status_report_req'],statusReport))
        if cancelEnabled is not None:
            paramList.append((self.symbol['cancel_enabled'],cancelEnabled))
        if servCentreTimestamp is not None:
            paramList.append((self.symbol['serv_centre_timestamp'],servCentreTimestamp))
        if tariffClass is not None:
            paramList.append((self.symbol['tariff_class'],tariffClass))
        if servDescr is not None:
            paramList.append((self.symbol['service_descr'],servDescr))
        if priority is not None:
            paramList.append((self.symbol['priority'],priority))
        if servCentreAddr is not None:
            paramList.append((self.symbol['serv_center_addr'],servCentreAddr))
        if statusCode is not None:
            paramList.append((self.symbol['status_code'],statusCode))
        if dischargeTime is not None:
            paramList.append((self.symbol['discharge_time'],dischargeTime))
        return paramList
    
    def isOpcodeInEncodedParams(self,Opcode,encodedParamList):
        if Opcode is None or encodedParamList is None:
            return False
        for tuple in encodedParamList:
            if tuple[0] == Opcode:
                return True
        return False

    def submitMessage(self, encodedMsgParams):
        """ Creates submit message packet. """
        opCode = self.opCode['submit_msg']

        # Checking for mandatory items
        # - at least 1 destination address has to be present
        if not self.isOpcodeInEncodedParams(self.symbol['dest_addr'],encodedMsgParams):
            raise CIMDError('Destination address missing')

        return self.cimd.createMessage(opCode,encodedMsgParams,None,self.useChecksum)

    def enquireMessageStatus(self, destAddr, servCentreTimestamp):
        """ Creates request for status report on submitted message """
        opCode = self.opCode['enq_msg_status']
        paramList = [(self.symbol['dest_addr'],destAddr)]
        paramList.append((self.symbol['serv_centre_timestamp'],servCentreTimestamp))
        return self.cimd.createMessage(opCode,paramList,None,self.useChecksum)

    def deliveryRequest(self, mode=1):
        """ Creates request for message delivery """
        opCode = self.opCode['delivery_req']
        if type(mode) is not int:
            mode = eval(mode)
        if mode < 0 or mode > 2:
            raise CIMDError('Invalid mode for delivery request')
        paramList = [(self.symbol['deli_req_mode'],mode)]
        return self.cimd.createMessage(opCode,paramList,None,self.useChecksum)

    def cancelMessage(self, mode, destAddr=None, servCentreTimestamp=None):
        """ Creates cancel request for earlier messages """
        opCode = self.opCode['cancel_msg']
        if type(mode) is not int:
            mode = eval(mode)
        if mode < 0 or mode > 2:
            raise CIMDError('Invalid mode for cancel message')
        paramList = [(self.symbol['cancel_mode'],mode)]
        if mode == 0 and destAddr is None:
            raise CIMDError('Missing destination address for this cancel mode')
        if mode == 2 and (destAddr is None or servCentreTimestamp is None):
            raise CIMDError('Missing parameter(s) for this cancel mode')
        if destAddr is not None:
            paramList.append((self.symbol['dest_addr'],destAddr))
        if servCentreTimestamp is not None:
            paramList.append((self.symbol['serv_centre_timestamp'],servCentreTimestamp))
        return self.cimd.createMessage(opCode,paramList,None,self.useChecksum)
        
    def deliverMessage(self, encodedMsgParams):
        """ Creates deliver message packet (used by SMSC) """
        opCode = self.opCode['deliver_msg']

        # Checking for mandatory items
        
        # - at least 1 destination address has to be present
        if not self.isOpcodeInEncodedParams(self.symbol['dest_addr'],encodedMsgParams):
            raise CIMDError('Destination address missing')

        # - originating address
        if not self.isOpcodeInEncodedParams(self.symbol['orig_addr'],encodedMsgParams):
            raise CIMDError('Originating address missing')
        
        # - service centre timestamp
        if not self.isOpcodeInEncodedParams(self.symbol['serv_centre_timestamp'],encodedMsgParams):
            raise CIMDError('Service centre timestamp missing')
        
        # Optional: User data header, User data/User data binary, Protocol id,
        #           Data coding scheme, Originated IMSI, Originated VMSC,
        #           Service center address
        
        return self.cimd.createMessage(opCode,encodedMsgParams,None,self.useChecksum)

    def deliverStatusReport(self, encodedMsgParams):
        """ Creates delivery status report (used by SMSC) """
        opCode = self.opCode['deliver_status_rep']

        # Checking for mandatory items

        # - destination address
        if not self.isOpcodeInEncodedParams(self.symbol['dest_addr'],encodedMsgParams):
            raise CIMDError('Destination address missing')
        
        # - service centre timestamp
        if not self.isOpcodeInEncodedParams(self.symbol['serv_centre_timestamp'],encodedMsgParams):
            raise CIMDError('Service centre timestamp missing')
        
        # - status code
        if not self.isOpcodeInEncodedParams(self.symbol['status_code'],encodedMsgParams):
            raise CIMDError('Status code missing')
        
        # - discharge time
        if not self.isOpcodeInEncodedParams(self.symbol['discharge_time'],encodedMsgParams):
            raise CIMDError('Discharge time missing')

        # Optional: Status error code, Originator address

        return self.cimd.createMessage(opCode,encodedMsgParams,None,self.useChecksum)
        
    def setParam(self, symbol, value):
        """ Creates [set parameter] message """
        opCode = self.opCode['set']
        
        if symbol is None or value is None:
            raise CIMDError('Missing parameter symbol or value')
        
        return self.cimd.createMessage(opCode,[(symbol,value)],None,self.useChecksum)
    
    def getParam(self, symbol):
        """ Creates [get parameter] message """
        opCode = self.opCode['get']

        if symbol is None:
            raise CIMDError('Missing parameter symbol')

        return self.cimd.createMessage(opCode,[(500,symbol)],None,self.useChecksum)

    def alive(self):
        """ Creates [alive] message """
        opCode = self.opCode['alive']
        return self.cimd.createMessage(opCode,None,None,self.useChecksum)

if __name__ == "__main__":
    pass
