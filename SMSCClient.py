"""SMSC Client application"""

import sys, time
import cimd
import logging
import socket,asyncore,asynchat

class SMSCClient(asynchat.async_chat):
    
    def __init__ (self, host, port, username, password):
        # Logging setup
        logItemFormat = "%(asctime)-15s,%(msecs)d %(levelname)s:%(message)s"
        logDateFormat = "%d.%m.%y %H:%M:%S"
        logging.basicConfig(filename="client.log",filemode ='a',format=logItemFormat,
                             datefmt=logDateFormat,level=logging.DEBUG)
        self.log = logging.getLogger("SMSCClientl")
        self.log.debug("[SMSCClient started...]")

        # Real constructor
        asynchat.async_chat.__init__(self)
        self.connection_phase = 0
        self.reconnectTimeout = 10
        self.terminatorBanner = "\n"
        self.terminatorCIMD = cimd.CIMD.specChar.get('etx')
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.smscc = cimd.SMSC()
        self.banner = ""
        self.ibuffer = ""
        self.callback = []
        self.obuffer = ""

        # Initial connect
        self.connect_now()
        
    def connect_now(self):
        self.set_terminator(self.terminatorBanner)
        try:
            self.create_socket (socket.AF_INET, socket.SOCK_STREAM)
            self.connect((self.host, self.port))
        except:
            self.handle_error()
            self.close()        

    # handle_connect is called when a connection is successfully established.
    def handle_connect(self):
        self.connection_phase = 1
        msg = "[Connected to "+self.host+":"+repr(self.port)+"]"
        print msg
        self.log.info(msg)
        #self.push('Connected...\r\n')

    # Push overriden for logging
    def push(self,data):
        self.log.debug("[Push]:"+data)
        asynchat.async_chat.push(self,data)

    def handle_error(self):
        print >>sys.stderr, self.host, sys.exc_info()[1]
        
    # handle_expt is called when a connection fails (Windows), 
    # or when out-of-band data arrives (Unix)
    def handle_expt(self):
        self.close()
        msg = "Failed connect to "+self.host+":"+repr(self.port)
        print >>sys.stderr, msg
        self.log.warn(msg)
        time.sleep(self.reconnectTimeout)
        self.connect_now()

    def collect_incoming_data(self, data):
        """ Incoming data buffering """
        self.ibuffer = self.ibuffer + data
        
    # handle_close is called when the socket is closed or reset.
    def handle_close (self):
        self.log.warn("[Remote connection closed or reset]")
        self.close()
        
    # Close overrriden
    def close(self):
        self.connection_phase = 0
        self.log.info("[Closed connection]")
        asynchat.async_chat.close(self)

    def found_terminator(self):
        print "Received: "+self.ibuffer

        if self.connection_phase == 1:
            # Received banner, sending login
            self.set_terminator(self.terminatorCIMD)
            self.connection_phase = 2
            self.banner = self.ibuffer
            self.log.info("[Banner] "+self.ibuffer)
            self.login()
        else:
            # process CIMD msgs here
            self.log.info("[CIMD] "+self.ibuffer)
            cb_fun = self.callback.pop (0)
            if cb_fun:
                cb_fun(self.ibuffer)
            else:
                default_cb(self.ibuffer)
            
            self.close()

        self.ibuffer = ""
        
    # Default callback
    def default_cb(self, msg):
        self.log.debug("Default callback")

    def login(self):
        self.push(self.smscc.login(userID=self.username,password=self.password))
        self.callback.append(self.login_cb)
    
    def login_cb(self, msg):
        self.log.debug("Login callback")
        
        

# 160.218.63.22:9971
# SO test31so/test31so
# SR test31sr/test31sr

if __name__ == "__main__":

    smsccl = SMSCClient('localhost',9971,'test31so','test31so')
    asyncore.loop()
    smsccl.log.debug("[...SMSCClient finished]\n")
