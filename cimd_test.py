""" Unit test for cimd.py"""

import cimd
import unittest

class CIMDTestCase(unittest.TestCase):
    def setUp(self):
        self.cimd = cimd.CIMD()
    def tearDown(self):
        self.cimd = None
    def testGetPacketNo(self):
        """ Check for correct packet number reading """
        self.assertEqual(self.cimd.getPacketNumber(),self.cimd.packetNumber)
    def testResetPacketNo(self):
        """ Check for correct packet number reset """
        self.cimd.resetPacketNumber()
        self.assertEqual(self.cimd.getPacketNumber(),1)
    def testSetPacketNo(self):
        """ Check for correct packet number setting """        
        self.cimd.setPacketNumber(11)
        self.assertEqual(self.cimd.getPacketNumber(),11)
        self.assertRaises(cimd.CIMDError,self.cimd.setPacketNumber,8)
    def testIncPacketNo(self):
        """ Check for correct packet number increment """
        self.cimd.setPacketNumber(253)
        self.cimd.incPacketNumber()
        self.assertEqual(self.cimd.getPacketNumber(),255)
        self.cimd.incPacketNumber()
        self.assertEqual(self.cimd.getPacketNumber(),1)
    def testChecksum(self):
        """ Check for correct checksum computation """
        self.assertEqual(self.cimd.calcChecksum("abc123"),188)
    def testCodec(self):
        """ Check for correct encoding & decoding of CIMD messages """
        tstStr = chr(0)+chr(2)+chr(3)+'abc123'+chr(9)+chr(0)
        resultStr = self.cimd.decode(tstStr)
        self.assertEqual(resultStr,'{NUL}{STX}{ETX}abc123{TAB}{NUL}')
        self.assertEqual(self.cimd.encode(resultStr),tstStr)
    def testCreateHeader(self):
        """ Check for correct header generation """
        self.cimd.resetPacketNumber()
        tstStr = self.cimd.decode(self.cimd.createHeader(5))
        self.assertEqual(tstStr,'{STX}05:001{TAB}')
        tstStr = self.cimd.decode(self.cimd.createHeader(55))
        self.assertEqual(tstStr,'{STX}55:003{TAB}')
        tstStr = self.cimd.decode(self.cimd.createHeader(55,9))
        self.assertEqual(tstStr,'{STX}55:009{TAB}')
    def testCreateParamBlock(self):
        """ Check for correct parameter block generation """
        tstStr = self.cimd.decode(self.cimd.createParamBlock(10,20))
        self.assertEqual(tstStr,'010:20{TAB}')
        tstStr = self.cimd.decode(self.cimd.createParamBlock(15,'abc'))
        self.assertEqual(tstStr,'015:abc{TAB}')
    def testCreateTrailer(self):
        """ Check for correct message trailer generation """
        tstStr = self.cimd.decode(self.cimd.createTrailer())
        self.assertEqual(tstStr,'{ETX}')
        tstStr = self.cimd.decode(self.cimd.createTrailer("abc123"))
        self.assertEqual(tstStr,'BC{ETX}')
        self.assertRaises(cimd.CIMDError,self.cimd.createTrailer,1)
    def testExtractParamValue(self):
        """ Check for correct parameter value extraction from message """
        tstStr = self.cimd.decode(self.cimd.extractParamValue('',''))
        self.assertEqual(tstStr,None)
        tstMsg = "{STX}01:001{TAB}010:partone{TAB}100:parttwo{TAB}{ETX}"
        tstMsg = self.cimd.encode(tstMsg)
        tstStr = self.cimd.decode(self.cimd.extractParamValue(tstMsg,''))
        self.assertEqual(tstStr,None)
        tstStr = self.cimd.decode(self.cimd.extractParamValue(tstMsg,'15'))
        self.assertEqual(tstStr,None)
        tstStr = self.cimd.decode(self.cimd.extractParamValue(tstMsg,'10'))
        self.assertEqual(tstStr,'partone')
        tstStr = self.cimd.decode(self.cimd.extractParamValue(tstMsg,100))
        self.assertEqual(tstStr,'parttwo')
        tstDic = self.cimd.extractAllParamValues(tstMsg)
        self.assertEqual(tstDic,[('010','partone'),('100','parttwo')])
    def testCreateMessage(self):
        """ Check for correct complete message building """
        expectedStr = "{STX}01:001{TAB}{ETX}"
        currentStr = self.cimd.decode(self.cimd.createMessage(1))
        self.assertEqual(currentStr,expectedStr)
        expectedStr = "{STX}02:001{TAB}010:partone{TAB}{ETX}"
        self.cimd.resetPacketNumber()
        currentStr = self.cimd.decode(self.cimd.createMessage(2,[('010','partone')]))
        self.assertEqual(currentStr,expectedStr)
        self.cimd.resetPacketNumber()
        currentStr = self.cimd.decode(self.cimd.createMessage(2,[(10,'partone')]))
        self.assertEqual(currentStr,expectedStr)
        expectedStr = "{STX}05:001{TAB}010:partone{TAB}100:parttwo{TAB}{ETX}"
        self.cimd.resetPacketNumber()
        currentStr = self.cimd.decode(self.cimd.createMessage(5,[(10,'partone'),(100,'parttwo')]))
        self.assertEqual(currentStr,expectedStr)
        expectedStr = "{STX}05:021{TAB}010:partone{TAB}100:parttwo{TAB}EF{ETX}"
        currentStr = self.cimd.decode(self.cimd.createMessage(5,[(10,'partone'),(100,'parttwo')],21,True))
        self.assertEqual(currentStr,expectedStr)

class SMSCTestCase(unittest.TestCase):
    def setUp(self):
        self.smsc = cimd.SMSC()
    def tearDown(self):
        self.smsc = None
    def testSetChecksumUsage(self):
        """ Check for correct setting of checksum usage flag """
        self.assertRaises(cimd.CIMDError,self.smsc.setChecksumUsage,'10')
        self.smsc.setChecksumUsage(True)
        self.assertEqual(self.smsc.useChecksum,True)
        self.smsc.setChecksumUsage(False)
        self.assertEqual(self.smsc.useChecksum,False)
    def testLogin(self):
        """ Check login message generator """
        self.smsc.cimd.resetPacketNumber()
        expectedStr = self.smsc.cimd.encode("{STX}01:001{TAB}010:name{TAB}011:password{TAB}{ETX}")
        currentStr = self.smsc.login('name','password')
        self.assertEqual(currentStr,expectedStr)
        self.smsc.setChecksumUsage(True)
        expectedStr = "{STX}01:003{TAB}010:name{TAB}011:password{TAB}"
        expectedStr += "012:3{TAB}019:3{TAB}0F{ETX}"
        expectedStr = self.smsc.cimd.encode(expectedStr)
        currentStr = self.smsc.login('name','password',3,3)
        self.assertEqual(currentStr,expectedStr)
        self.assertRaises(cimd.CIMDError,self.smsc.login,'ukrutanskyDlouheLmenoDelsiNez32ZnakuJakoAleOpravdu','pass')
    def testLogout(self):
        """ Check logout message generator """
        expectedStr = self.smsc.cimd.encode("{STX}02:001{TAB}{ETX}")
        currentStr = self.smsc.logout()
        self.assertEqual(currentStr,expectedStr)
    def testEncodeTextMsgParams(self):
        """ Check for correct message params encoding """
        expectedList = [('021', '123456789')]
        currentList = self.smsc.encodeTextMsgParams(destAddr="123456789")
        self.assertEqual(currentList,expectedList)
        expectedList = [('021', '123456789'),('033', 'msgtxt')]
        currentList = self.smsc.encodeTextMsgParams(destAddr="123456789",userData='msgtxt')
        self.assertEqual(currentList,expectedList)
    def testSubmitMessage(self):
        """ Check for correct format of submitted message """
        encodedParamList = self.smsc.encodeTextMsgParams(destAddr="123456789",userData="sometext")
        submitResult = self.smsc.submitMessage(encodedParamList)
        expectedResult = "{STX}03:001{TAB}021:123456789{TAB}033:sometext{TAB}{ETX}"
        expectedResult = self.smsc.cimd.encode(expectedResult)
        self.assertEqual(submitResult,expectedResult)
        self.assertRaises(cimd.CIMDError,self.smsc.submitMessage,[])
    def testEnquireMessageStatus(self):
        """ Check for message status enquiry """
        enquireResult = self.smsc.enquireMessageStatus("987654321","060904140021")
        expectedResult = "{STX}04:001{TAB}021:987654321{TAB}060:060904140021{TAB}{ETX}"
        expectedResult = self.smsc.cimd.encode(expectedResult)
        self.assertEqual(enquireResult,expectedResult)
    def testDeliveryRequest(self):
        """ Check for correct delivery request """
        requestResult = self.smsc.deliveryRequest()
        expectedResult = "{STX}05:001{TAB}068:1{TAB}{ETX}"
        expectedResult = self.smsc.cimd.encode(expectedResult)
        self.assertEqual(requestResult,expectedResult)
        requestResult = self.smsc.deliveryRequest(0)
        expectedResult = "{STX}05:003{TAB}068:0{TAB}{ETX}"
        expectedResult = self.smsc.cimd.encode(expectedResult)
        self.assertEqual(requestResult,expectedResult)
        requestResult = self.smsc.deliveryRequest("2")
        expectedResult = "{STX}05:005{TAB}068:2{TAB}{ETX}"
        expectedResult = self.smsc.cimd.encode(expectedResult)
        self.assertEqual(requestResult,expectedResult)
        self.assertRaises(cimd.CIMDError,self.smsc.deliveryRequest,3)
    def testCancelMessage(self):
        """ Check for correct [message cancel request] """
        cancelResult = self.smsc.cancelMessage(1)
        expectedResult = "{STX}06:001{TAB}059:1{TAB}{ETX}"
        expectedResult = self.smsc.cimd.encode(expectedResult)
        self.assertEqual(cancelResult,expectedResult)
        self.assertRaises(cimd.CIMDError,self.smsc.cancelMessage,0)
        self.assertRaises(cimd.CIMDError,self.smsc.cancelMessage,2)
        self.assertRaises(cimd.CIMDError,self.smsc.cancelMessage,3)
        cancelResult = self.smsc.cancelMessage(0,'111222333')
        expectedResult = "{STX}06:003{TAB}059:0{TAB}021:111222333{TAB}{ETX}"
        expectedResult = self.smsc.cimd.encode(expectedResult)
        self.assertEqual(cancelResult,expectedResult)
    def testDeliverMessage(self):
        """ Check for correct [deliver message request] """
        self.assertRaises(cimd.CIMDError,self.smsc.deliverMessage,None)
        encodedParamList = self.smsc.encodeTextMsgParams(destAddr="123456789",origAddr="999999999")
        self.assertRaises(cimd.CIMDError,self.smsc.deliverMessage,encodedParamList)
        encodedParamList = self.smsc.encodeTextMsgParams(destAddr="123456789",
                            origAddr="999999999",servCentreTimestamp="060904212000")
        deliverResult = self.smsc.deliverMessage(encodedParamList)
        expectedResult =  "{STX}20:001{TAB}021:123456789{TAB}023:999999999"
        expectedResult += "{TAB}060:060904212000{TAB}{ETX}"
        expectedResult = self.smsc.cimd.encode(expectedResult)
        self.assertEqual(deliverResult,expectedResult)
    def testDeliverStatusReport(self):
        """ Check for correct [deliver status report] """
        self.assertRaises(cimd.CIMDError,self.smsc.deliverStatusReport,None)
        encodedParamList = self.smsc.encodeTextMsgParams(destAddr="123456789",
                            servCentreTimestamp="060927094900")
        self.assertRaises(cimd.CIMDError,self.smsc.deliverStatusReport,encodedParamList)
        encodedParamList = self.smsc.encodeTextMsgParams(destAddr="123456789",
                            servCentreTimestamp="060927094900", statusCode="1",
                            dischargeTime="060927104900")
        deliverResult = self.smsc.deliverStatusReport(encodedParamList)
        expectedResult =  "{STX}23:001{TAB}021:123456789{TAB}060:060927094900"
        expectedResult += "{TAB}061:1{TAB}063:060927104900{TAB}{ETX}"
        expectedResult = self.smsc.cimd.encode(expectedResult)
        self.assertEqual(deliverResult,expectedResult)
    def testSetParam(self):
        """ Check for correct [set] message """
        self.assertRaises(cimd.CIMDError,self.smsc.setParam,None,None)
        setResult = self.smsc.setParam(10,11)
        expectedResult = "{STX}08:001{TAB}010:11{TAB}{ETX}"
        expectedResult = self.smsc.cimd.encode(expectedResult)
        self.assertEqual(setResult,expectedResult)
        setResult = self.smsc.setParam("10","11")
        expectedResult = "{STX}08:003{TAB}010:11{TAB}{ETX}"
        expectedResult = self.smsc.cimd.encode(expectedResult)
        self.assertEqual(setResult,expectedResult)
    def testGetParam(self):
        """ Check for correct [get] message """
        self.assertRaises(cimd.CIMDError,self.smsc.getParam,None)
        getResult = self.smsc.getParam(501)
        expectedResult = "{STX}09:001{TAB}500:501{TAB}{ETX}"
        expectedResult = self.smsc.cimd.encode(expectedResult)
        self.assertEqual(getResult,expectedResult)
    def testAlive(self):
        """ Check for correct [alive] message """
        aliveResult = self.smsc.alive()
        expectedResult = "{STX}40:001{TAB}{ETX}"
        expectedResult = self.smsc.cimd.encode(expectedResult)
        self.assertEqual(aliveResult,expectedResult)

        

if __name__ == "__main__":
    unittest.main()
