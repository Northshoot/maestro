'''
Created on 22 maj 2013
python program to start for the master server 
@author: didier gourillon
'''

import socket
import threading
from instanceRunner import instanceRunner
import ConfigParser
import io
from results_thread import get_all_results
from mail_sender import mail
from analyze_results import analyze_performances
import os, sys
from ccmd.tools.helpers import configSectionMap, getLocalIp, removeDir, \
                    list_child_processes,kill_child_processes

from ccmd.tools.defines import RESULT_WITH_MON, RESULT_WITHOUT_MON, \
                        BUFFER_SIZE, SERVER_PORT, CREDENTIALS_PORT, \
                        BUFFER_SIZE_BIG,MASTER_DIR, AWS_PUB_META

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/home/lauril/workspace/ccmd.srv.log',
                    filemode='w+')
boto_log = logging.getLogger('boto')
boto_log.setLevel(logging.WARNING)
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

# Now, we can log to the root logger, or any other logger. First the root...


# Now, define a couple of other loggers which might represent areas in your
# application:

logger = logging.getLogger('CCMD.SRV.MSTR')
logclth = logging.getLogger('CCMD.SRV.MSTR.CLIENT_THR')
logobj = logging.getLogger('CCMD.SRV.MSTR.CLIEN_OBJ')
def log(msg):
    logger.debug(msg)

ip_addresses = getLocalIp()
# parses a config file about instances to gather all data to start the instances
def get_instances_data(configFile):
    config = ConfigParser.ConfigParser()
    config.read(configFile)
    log( config.sections())
    instances=[]
    for section in config.sections():
        if ('instance' in str(section)):
            instance = configSectionMap(section,config)
            instances.append(instance)
    return instances


''' 
class that handles all the clientObject objects 
that have been created by the Server
'''
class clientThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.clientList = [] # list of clientObject objects that all correspond to a request that needs to be handled
        self.running = True
        self.pid = os.getpid() 
        self.pids = " $%s$ " %self.pid
        logclth.debug(self.pids + "Client thread created. . .")
        
    def run(self):
        logclth.debug(self.pids + "Beginning client thread loop. . .")
        client_done = []
        while self.running:
            #list of clientObject objects whose handling request 
            #thread has already been started
            
            for client in self.clientList:
                # reads the request content of a client (instance configuration file)
                message = client.sock.recv(BUFFER_SIZE) 
                
                if message != None and message != "":
                    logclth.debug(self.pids +  "MSG: " + message)
                    logclth.debug(self.pids +  "CLIENT LIST: " + str(len(self.clientList)))
                    # the clientThread actually handles the request here
                    client.set_msg(message) # records the request's content
                    # start the thread that will handle a client's request
                    client.start() 
                    logclth.debug(' start new simulation thread ')
                    client_done.append(client)
                    
            for client in client_done: 
                self.clientList.remove(client) 
        logclth.debug(self.pids +  "exit while" )         


# Class used to handle every request that is received by the server
class clientObject(threading.Thread):

    def __init__(self,main_server,clientInfo, clientAddress, credentials):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()
        self.sock = clientInfo # socket to communicate with the client
        self.address = clientAddress # address of the client
        self.main_server=main_server
        self.running = True
        self.instanceRunner = instanceRunner(credentials, self.sock) # instanceRunner connects AWS	
        self.msg = '' # first message received as the  request (will contain instance config file)
        self.pid = str(os.getpid())
        self.pids = " $%s$ " %self.pid 
        self.instance_config = MASTER_DIR+'instances_%s_%s.cfg' %(self.pid,str(clientAddress))
        
    def set_msg(self,msg): 
        self.msg = msg
        
    # runs a simulation
    def run(self):
        while(self.running):
            # first the clientobject receives all the configuration file it needs and use them
            config_data = self.sock.recv(BUFFER_SIZE)
            f_instance = open(self.instance_config,'wb') # write down the instance con fig file to parse it
            f_instance.write(config_data)
            f_instance.close()
            self.sock.send('instances cfg received - starting instances') # send back and ACK
            instances_data = get_instances_data(self.instance_config)
            ip_addresses = []
            # the clientObject start the worker instances
            for current_instance in instances_data:
                try : 
                    ip_addresses+=self.instanceRunner.start_instance(
                                      instance_type=current_instance['instance_type'],
                                      ami_image_id=current_instance['ami_id'],
                                      nb_of_instances_to_run=current_instance['nb_of_instances'],
                                      security_groups_tab=current_instance['security_groups'].split(','),
                                      key_name_instance=current_instance['key_pair']
                                      )
                                        
                except Exception as e: # this part handles all exceptions that can be raised by Amazon when we try to start instances (maximum number of instances exceeded for example)
                    error = 'ERROR@while starting instance '+ \
                        current_instance['instance_type']+ ' ==> '+str(e)
                    logobj.debug(self.pids + error)
                    self.sock.send(error) #sends an error message to the client
                    self.sock.recv(BUFFER_SIZE) # wait for ACK
            logobj.debug(self.pids + "instance IP: " + str(ip_addresses))
            # sends an ACK message when all instances have been started
            self.sock.send('NOTE@Started %d instances' %len(instances_data))
            strg = self.sock.recv(BUFFER_SIZE) # wait for an ACK
            if strg != "ACK":
                logobj.debug(self.pids + "ERROR: got not ACK! GOT %s" %strg)
                #strg = self.sock.recv(BUFFER_SIZE)

            self.sock.send('Ready for CMD') # sends an ACK to empty the socket content
            rx = self.sock.recv(BUFFER_SIZE_BIG)  # downloads the command config file
            logobj.debug(self.pids + "RX: %s" %rx)
            str_commands = rx.split('@')
            if str_commands[0] != 'COMMANDS':
                log(self.pids + "Error RX commands, got %s:: %s" %(str_commands[0],str_commands[1]) )
            
            self.sock.send('ACK@COMMANDS') # sends an ACK to empty the socket content 
            rx = self.sock.recv(BUFFER_SIZE_BIG) # receives the perforlance monitoring config file
            str_perf = rx.split('@')
            if str_perf[0] != 'MONITORING':
                logobj.debug(self.pids + "Error RX monitoring, got %s:: %s" %(str_perf[0],str_perf[1]) )
            if str_perf[1]:
                simulation_id = str_perf[1].split('simulation_id: ')[1].split('\n')[0]
            mail_destination = 'lauril@ltu.se' #str_perf.split('mail_destination: ')[1].split('\n')[0] # reads the performance configuration file to get the e-mail that it will have to send the message of ending of simulation
            # sends an ACK to the client to tell him that the simulation starts
            self.sock.send("ACK@MONITORING") 
            self.sock.send("NOTE@Starting simulations")    
            results_files = get_all_results(ip_addresses,str_commands[1],
                                            str_perf[1],
                                            self.instanceRunner.instances_types) # does the simulation an get the results 
            self.instanceRunner.stop() # terminate all instances that were involved into the simulation
            #read a file to know which node died unexpectively during the simulation
            str_file_death_nodes ='NOT MONITORED'
            
            try:
                file_death_nodes = open('dead_nodes','r')
                str_file_death_nodes = file_death_nodes.read()
                file_death_nodes.close()
            except Exception:
                #no dead nodes
                pass
            # erases a default debugging file
            try: 
                os.remove(RESULT_WITH_MON+'default_output') 
            except OSError:
                #file does not exist
                pass
            # gets the ip of the CCMD
            public_hostname = os.popen(AWS_PUB_META).read() 

            if 'True' in str_perf:
                # prepares the analyzis of performances files that will be sent back to the user
                analyze_performances(results_files)
                # sends a feedback to the mail the client indicated 
                mail(mail_destination,
                     "CCMD : end of a simulation with the id "+ str(simulation_id),
                     "a simulation has ended please check attached file for more details \n you can access the results on the following link \n ftp://"+str(public_hostname) + '\n\nfollowing instances died during the simulation : ' + str_file_death_nodes,'performances_analysis_'+str(os.getpid())+'.txt')  
                return 'simulation done'
            else :
#                 attached_file = open('no_perfs.txt','a') #creates a default file to send back to the user
#                 attached_file.write('No performance analysis was required')
#                 attached_file.close()
                # sends a feedback mail to the client's mail address
                mail(mail_destination,
                     "CCMD : end of simulation with the id "+ 
                     str(simulation_id),
                     "a simulation has ended please check attached file \
                     for more details \n you can access the results on \
                     the following link \n ftp://"+str(public_hostname) + \
                     '\nfollowing instances died during the simulation : ' + \
                     str_file_death_nodes,'no_perfs.txt') 
                
            logobj.debug(self.pids + "Closing" )
            os.remove(self.instance_config)
            self.sock.send("SIMULATION Completed")
            self.main_server.instanceWorkCompleted(self)
            
            


    def stop(self):
        self.running = False
        self._stopevent.set()
        logobj.debug(self.pids +  "Cleaned up")

'''server that handles connections from clients'''
class Server(threading.Thread):
    def __init__(self,credentials):
        threading.Thread.__init__(self)
        self._stope = threading.Event()
        self.myIp = getLocalIp() # private ip of the instance
        self.credentials = credentials  # credentials provided by a client
        self.myPort = SERVER_PORT
        self.BUFFSIZE = BUFFER_SIZE
        self.ADDRESS = (self.myIp,self.myPort)
        self.clientObjList = [] 
        self.running = True
        self.serverSock = socket.socket() # socket to communicate with clients
        self.serverSock.bind(self.ADDRESS)
        self.serverSock.listen(500) # maximum number of connection is set to 5
        #self.clientThread = clientThread() # Object that will handle every connection received by the client socket
        self.pids = " $%s$ " %os.getpid()
        removeDir(RESULT_WITH_MON) # clean up  results directories
        removeDir(RESULT_WITHOUT_MON) 
        
    def run(self):    
        log_data = "Starting master server IP %s:%s" %(self.myIp, self.myPort)
        log(log_data)
        #self.clientThread.start() 
        log(self.pids + "Awaiting connections. . .")
        while self.running:
            try :
                (clientsocket, address) = self.serverSock.accept()
                log(self.pids +"Client connected from {}.".format(address))
                
                 
                # when we receive a new request, 
                #we create a a new clientObject with it and
                # it is put on the clientThread's list that will handle it asap
                ct = clientObject(self,clientsocket,address,self.credentials)
                ct.start()
                self.clientObjList.append(ct)
            except KeyboardInterrupt:
                log(self.pids + "^C detected")
                self.stop()
                
            except Exception as e:
                clientsocket.send('error during simulation : '+ str(e))
        log("Still running")
        self.stop()

    def instanceWorkCompleted(self, clientObj):
        self.clientObjList.remove(clientObj)
        log(self.pids + "Instance Completed left: " + str(len(self.clientObjList)))
        clientObj.stop()
        
    def stop(self):
        log(self.pids +"STOPPING")
        self.running = False        
        self.serverSock.close()        
        log(self.pids +"- end -")


def mainServer():
    wait_for_credentials = False
    if wait_for_credentials:
        socket_credentials = socket.socket()
        socket_credentials.bind((getLocalIp(),CREDENTIALS_PORT))
        socket_credentials.listen(1)
        log(os.getpid() + ' waiting for credentials ' )    
        clientInfo = socket_credentials.accept()
        log(os.getpid() +  'new client :  ' + str(clientInfo) )    
        file_credentials = open(MASTER_DIR+'file_credentials','w')
        
        file_credentials.write(clientInfo[0].recv(BUFFER_SIZE))
        file_credentials.close()
        clientInfo[0].send('connection done')
        clientInfo.close()

    config = ConfigParser.ConfigParser()
    config.read(MASTER_DIR+'file_credentials')
    credentials = configSectionMap('credentials',config)
    
    
    serv = Server(credentials)
    serv.start()
    serv.join()
    list_child_processes(os.getpid())
    sys.exit(0)
# this part of the code handles the receiving of the credentials 	
#this needs to be fixed, credentials are not necessery to give every time
if __name__ == '__main__':
    mainServer()

