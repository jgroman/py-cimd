""" Unit test for SMSCClient.py """

import SMSCClient
import unittest,logging
import socket,asyncore

class fakeSMSCChannel(asyncore.dispatcher):
    
    def __init__(self, channel, log, testcase):
        self.log = log
        self.test_callback = []
        self.test_callback.append(testcase)
        self.test_phase = 0
        asyncore.dispatcher.__init__(self,channel)
        self.log.info("{Channel spawned}")
        self.banner = "FakeCIMD2-A ConnectionInfo: SessionId = 1234567 PortId = 123 Time = 061006131036 AccessType = TCPIP_SOCKET PIN = 99999\n"
        self.sendBuffer = self.banner
        self.recBuffer = ""
        
    def handle_read(self):
        self.log.debug("{Read callback}")
        self.recBuffer = self.recv(2048)
        if len(self.recBuffer)>0:
            print "SMSC Received:" + self.recBuffer
            cb_fun = self.test_callback.pop (0)
            if cb_fun:
                cb_fun(self,self.recBuffer)
            
    
    def writable(self):
        return (len(self.sendBuffer)>0)

    def handle_write(self):
        sent = self.send(self.sendBuffer)
        if sent > 0:
            self.log.debug("{Sent "+repr(sent)+" bytes:} "+self.sendBuffer[:sent])
        self.sendBuffer = self.sendBuffer[sent:]
        
    def handle_close(self):
        pass
        
    def handle_expt(self):
        print "Exception"

    def test_banner(self, data):
        print "Tested: " + data

class fakeSMSC(asyncore.dispatcher):
    """ Incomplete SMSC implementation for testing purposes """
    def __init__(self, port=9971, testcase=0):
        # Logging setup
        logItemFormat = "%(asctime)-15s,%(msecs)d %(levelname)s:%(message)s"
        logDateFormat = "%d.%m.%y %H:%M:%S"
        logging.basicConfig(filename="server.log",filemode ='a',format=logItemFormat,
                             datefmt=logDateFormat,level=logging.DEBUG)
        self.log = logging.getLogger("SMSCServer")
        self.log.addHandler(logging.StreamHandler())
        self.log.debug("{SMSCServer started...}")

        asyncore.dispatcher.__init__(self)
        self.port = port
        self.testcase = testcase
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.bind(("",port))
        self.listen(5)
        print "SMSC listening on port ",self.port
        
    def handle_accept(self):
        channel, addr = self.accept()
        self.log.info("{Incoming connection from "+repr(addr)+"}")
        self.smscchan = fakeSMSCChannel(channel,self.log, self.testcase)


    # handle_close is called when the socket is closed or reset.
    def handle_close(self):
        self.close()
        self.connected = False
        self.log.warn("{Remote end closed connection}")
    
    # handle_expt is called when a connection fails (Windows), 
    # or when out-of-band data arrives (Unix)
    def handle_expt(self):
        self.close()
        print "Expt, waiting..."
        time.sleep(self.reconnectTimeout)
        self.connect((self.host,self.port))
        
    # handle_error(type, value, traceback) is called if a Python error occurs 
    # in any of the other callbacks. The default implementation prints 
    # an abbreviated traceback to sys.stdout.
        

class SMSCClientTestCase(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def testFakeSMSC(self):
        """ Testing fake SMSC sanity """
        fsmsc = fakeSMSC(testcase=fakeSMSCChannel.test_banner)
        smsccl = SMSCClient.SMSCClient('localhost',9971,'test31so','test31so')
        
        asyncore.loop()
        
   

if __name__ == "__main__":
    unittest.main()
