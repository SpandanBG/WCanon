#!/usr/bin/python

#################### WCanon ####################
# Application to communicate with peers in the #
# network; encrypted with 2048 bit RSA         #
################################################

"""
This application provides a interface to communicate with users under the same
network.

It runs on two threads. The main thread and a server thread. The server thread
starts immediately when the app starts and starts to listent to the defined port.
If any connection is made the messages received are displayed along with the
IP address

The application also provides a RSA 2048 bit encrypted communication amongs the
the users. This means the messages will be communicated at max length of 256 bytes
To achive this, the application needs the PyCrypto library which can be added to
your python library using:
>>  pip install pycrypto

The main thread provides a CLI for users of the following functionalities
1> List all users in a wifi network that's using the application
2> Connect to a user
3> Send messages to the connected user
4> Shutdown the app

1> To know the list of users we first need to know our own IP address. To find
this run:

>>    import socket, fcntl, struct
>>    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
>>    return socket.inet_ntoa(fcntl.ioctl(
..        s.fileno(),
..        0x8915,  # SIOCGIFADDR
..        struct.pack('256s', *ifname*[:15])
..    )[20:24])

where *ifname* = in ['eth0', 'wlo1']

~~ Important! ~~
If app crashes, use `lsof -i tcp:4818` to get the PID (process ID) and then use
`kill -9 <PID>` to kill the process.
"""

import socket, fcntl, struct
import threading, os
import Crypto
from Crypto.PublicKey import RSA
from Crypto import Random
import ast

"""
        #### HELPER METHODS
>> get_my_ip() => Returns the wlo1 IPv4 address
>> banner() => String of app banner to be displayed
>> exitApp() => Starts exit sequence
"""
def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,
        struct.pack('256s', 'wlo1'[:15])
    )[20:24])

def banner():
    print '\t\t~WCanon~'
    print "Your IP: ",myIP
    print """Avaliable commands:
>>    list -> Lists all users avaliable under the network
>>    connect 0.0.0.0 -> Connect to the ip address
>>    exit -> Exit app"""
    print """To send a message simply type the message and hit ENTER!
Max Test length: 256\n"""

def exitApp():
    server._exit()

"""
        #### GLOBAL VARIABLES
"""
myIP = get_my_ip()
appPort = 4818
output = threading.Lock()

"""
        #### RSA HANDLER
This class generates a publicKey and a private key. The Public key is sent to
the client trying to send a message. The private key is used to decrypted the
message received from the client, which was encrypted by the public key. This
class is also responsible to store the public key of the presently connected
user in order to encrypt the text to be sent to them
"""
class RSAHandler:
    def __init__(self):
        self.rand_gen = Random.new().read
        # 2048 bits == 256 bytes
        self.privatekey = RSA.generate(2048, self.rand_gen)
        self.publickey = self.privatekey.publickey()
        self.otherPublicKey = self.publickey

    def setOtherPublicKey(self, key):
        try:
            self.otherPublicKey = RSA.importKey(key)
        except Exception as e:
            pass

    def getPublicKey(self):
        return self.publickey.exportKey()

    def encrypt(self, msg):
        try:
            return str(self.otherPublicKey.encrypt(msg,32))
        except Exception as e:
            return msg

    def decrypt(self, msg):
        try:
            return self.privatekey.decrypt(ast.literal_eval(str(msg)))
        except Exception as e:
            return msg

rsaToken = 'RSA##^1234'

"""
        #### USERS THREAD
Thread to get the list of users in the network and displaying them after retriving
the list.
"""
class UsersThead(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.user = []
        self.done = False

    def run(self):
        self.user = []
        srcUnit = myIP[ : myIP.rfind('.')+1]
        print '\nLooking for users. This might take sometime (1.27 mins approx).\nGo ahead, do something else...\n'
        for i in range(1,254):
            try:
                search = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                search.settimeout(0.3)      # 300 ms
                search.connect((srcUnit+str(i), appPort))
                search.settimeout(None)
                self.user.append(srcUnit+str(i))
            except Exception as e:
                pass
        self.showUsers()
        self.done = True

    def showUsers(self):
        output.acquire()
        print '\nList of users found: '
        for u in self.user:
            print u
        print '\n'
        output.release()

    def exit(self):
        self.done = True
        os._exit(0)

    def isDone(self):
        return self.done

"""
        #### SERVER THREAD
The server thread runs a server socket process on port = `appPort`. It listens
to all incoming messages on the port and displays it to the user.
"""
class ListenerServer(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.exit = False
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        try:
            self.server.bind((self.host,self.port))
            self.server.listen(5)
            while(self.exit == False):
                c, addr = self.server.accept()
                msg = c.recv(4096)
                if(msg == rsaToken):
                    c.send(rsa.getPublicKey())
                elif(len(msg)>0):
                    msg = rsa.decrypt(msg)
                    output.acquire()
                    print '\n',addr[0],' says: ',msg,'\n'
                    output.release()
                c.close()
        except Exception as e:
            print '\nServer not working\n'

    def _exit(self):
        self.exit = True
        self.server.close()
        os._exit(0)

"""
        #### CLIENT THREAD
The client thread runs the CLI and the process to send messages to the connected
user. Sends to self by default if no user is connected initially.
Commands:
>>    list -> Lists all users avaliable under the network
>>    connect 0.0.0.0 -> Connect to the ip address
>>    exit -> Exit app
"""
class ClientThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.connectCMD = "connect"
        self.listCMD = "list"
        self.exitCMD = "exit"
        self.client = None
        self.host = myIP
        self.port = appPort
        self.userList = None

    def run(self):
        output.acquire()
        banner()
        output.release()
        while True:
            cmd = raw_input()
            connectStr = cmd.split(' ')
            # list command
            if cmd == self.listCMD:
                self.listUser()
            # exit command
            elif cmd == self.exitCMD:
                self.exit()
                break
            # connect command
            elif len(connectStr) == 2 and connectStr[0] == self.connectCMD:
                self.connect(connectStr[1])
            # default
            else:
                self.send(cmd)

    def listUser(self):
        self.userList = UsersThead()
        self.userList.start()

    def exit(self):
        exitApp()
        try:
            if(self.userList.isDone() == False):
                self.userList.exit()
        except Exception as e:
            pass

    def connect(self, ip):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.host = ip
            self.client.connect((self.host, self.port))
            self.client.send(rsaToken)
            key = self.client.recv(4096)
            rsa.setOtherPublicKey(key)
            output.acquire()
            print 'Connected!\n'
            output.release()
            self.client.close()
        except Exception as e:
            output.acquire()
            print '\nFailed to connect to ',ip,'\n'
            output.release()

    def send(self, msg):
        try:
            if(len(msg)<257):
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.connect((self.host, self.port))
                msg = rsa.encrypt(msg)
                self.client.send(msg)
                self.client.close()
            else:
                output.acquire()
                print 'Messages length should be 256 chars max\n'
                output.release()
        except Exception as e:
            output.acquire()
            print '\nThe seems to be a problem with the connection\n'
            print e
            output.release()

"""
        #### MAIN
Start sever thread and client thread and Create RSA class object
"""
rsa = RSAHandler()

server = ListenerServer(host=myIP, port=appPort)
client = ClientThread()

server.start()
client.start()

serverThread = server
clientThread = client

serverThread.join()
clientThread.join()
