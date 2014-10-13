'''Created on 30 apr 2013
Python class that manages worker instances
@author: didier gourillon
'''

import boto.ec2
import time
import socket 
import os,datetime, sys

GROUPNAME = 'MAESTRO'
CLIENT_PORT = 9999

import logging

logger = logging.getLogger('CCMD.SRV.INSTRUN')

def log(msg):
    logger.debug(msg)



# This class handles instance Management
class instanceRunner:    
    def __init__(self,credentials, client_socket):
    
        self.conn = boto.ec2.connect_to_region(credentials['region'],aws_access_key_id=credentials['aws_access_key_id'], aws_secret_access_key=credentials['aws_secret_access_key'])
        self.other_instances = [] # ids of the other instances that were here before the
        self.instance_types = [
                            'hi1.4xlarge','c1.xlarge','c1.medium', 'm2.2xlarge',
                            'm2.xlarge','m2.4xlarge', 'm1.xlarge', 'm1.large',
                            'm1.medium','m1.small', 'm3.2xlarge', 'm3.xlarge',
                            't1.micro'
                            ]
        #ids of the instances that will be started by this instanceRunner
        self.my_instances = [] 
        self.running_reservation = [] # ids of the reservations made when instances are started with this instanceRunner
        self.ip_addresses = {} # dictionary that has the following form : {id of the instance : ip address of the instance} 
        self.instances_types = {} # dictionary that has the following form : { ip of the instance : type of instance}
        self.client_socket = client_socket # socket to communicate with the client that sent the simulation request
        self.init_other_instances() # the instnceRunner registers other instances to make sure it does not interact with it
        self.ami_name =''
        self.ebs_optimizible =['m1.large','m1.xlarge',
                               'm3.xlarge','m3.2xlarge',
                               'c1.xlarge','m2.2xlarge']
    
    # registers every current instances to avoid modifying them during the simulation  
    def init_other_instances(self):
        for current_reservation in self.conn.get_all_instances():
            for current_instance in current_reservation.instances:
                self.other_instances.append(current_instance.id)
                
        
    # tests if python instance programs have started running on each of the instances at the ip addresses given as arguments
    # to do that, each client opens a socket that waits for a message from the instanceRunner,
    # after that, the instanceRunner is sure that every instance is ready to start the simulation
    # args :
    # addresses : list of DNS names of the instances that will be tested
    def test_connection (self, addresses):
        for current_addresses in addresses :
            boolTest = True
            while boolTest:
                boolTest = False
                # if the connection with the instance did not raise an exception, the python server has started on it, if not, it still has to wait
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((current_addresses, CLIENT_PORT))
                    sock.send("test" + "\n")
                except :
                    boolTest = True
                    log(str( current_addresses)+ " is initiating python server")
                    time.sleep( 2 )

    # this function waits that started instances are in 'running state' and get each of their public DNS name       
    # finally, it update instances list of the instanceRunner object
    def update_Running_Instances(self): 
        
        boolean_pending = True 
        # this boolean will be set to True everytime an instance qith a 'pending state' is found 
        while boolean_pending:
            boolean_pending = False     
            for current_reservation in self.conn.get_all_instances():
                if current_reservation.id in self.running_reservation:
                    for current_instance in current_reservation.instances:
                        # if an instance has a pending state we still have to wait for it to have an ip address
                        if (current_instance.state == 'pending'):
                            log( " waiting for "+current_instance.instance_type+" booting instance " +current_instance.id)
                            boolean_pending = True
                            time.sleep(120)
                        # if an instance has a running state we can register its ip address
                        elif (current_instance.state == 'running') :
                            #print "dns ", current_instance.public_dns_name 
                            current_instance.add_tag('Name', 'Runner of ' + self.ami_name)
                            current_instance.add_tag('Started', datetime.datetime.now())
                            self.instances_types[current_instance.public_dns_name ] = current_instance.instance_type
                            self.ip_addresses[str(current_instance.id)] = current_instance.public_dns_name  
                            time.sleep(60)
                        # we will also register the id of the instance
                        if (current_instance.id not in self.my_instances) :
                            log("Current instances: %s" %str(self.my_instances))
                            log("Appending instance: %s" % current_instance.id)
                            self.my_instances.append(current_instance.id)
                            self.instances_types[current_instance.public_dns_name ] = current_instance.instance_type
                        
        
          
        self.test_connection(self.ip_addresses.values())
        new_ips = []
        for value in self.ip_addresses.values():
            new_ips.append(str(value))
          
        return new_ips        

    # start instances
    def start_instance (self, ami_image_id, nb_of_instances_to_run,instance_type,security_groups_tab,key_name_instance):
        log(str(nb_of_instances_to_run) +" "+ instance_type+ " instances to run wait lock  start_instance  " + str(os.getpid()))
        log('got lock start instance : '+str((os.getpid())))
        ebs_optimized = False
        if instance_type in self.ebs_optimizible:
            ebs_optimized = True
        log("Starting EBS optimize = %s" %str(ebs_optimized))
        try:
            reservation = self.conn.run_instances(ami_image_id, \
                                                  min_count=nb_of_instances_to_run,  \
                                                  max_count=nb_of_instances_to_run, \
                                                  security_groups= security_groups_tab, \
                                                  key_name=key_name_instance, \
                                                  instance_type=instance_type,
                                                  ebs_optimized= ebs_optimized,
                                                  dry_run=False
                                                  )
        except Exception as e:
            logger.critical("Can't start instance %s" %e)
            raise 
        self.ami_name = self.conn.get_image(ami_image_id).name
        time.sleep(180)
        #r_id = u'r-835784cc'
        self.running_reservation.append(reservation.id)
        result = self.update_Running_Instances()
        self.client_socket.send("start_instance@" \
                                +str(nb_of_instances_to_run)+' '+\
                                instance_type + ' started ')
        msg  = self.client_socket.recv(1024)
        log("Client response: %s " %msg)
        return result
    
    # stop all instances registered in the instanceRUnner object
    # we will use the ids of the instances we registered to stop the instances
    def stop (self):      
        log( "stopping " + str(len(self.my_instances)) + " instances")
        nb_instances = len(self.my_instances)
        self.conn.terminate_instances(self.my_instances)
        self.my_instances = []
        self.ip_addresses = {}
        return nb_instances
    
if __name__ == '__main__':
    credentials = {}
    credentials ['region']= 'eu-west-1'
    credentials['aws_access_key_id']= 'xxx'
    credentials['aws_secret_access_key']= 'xxx'
    conn = boto.ec2.connect_to_region(credentials['region'],aws_access_key_id=credentials['aws_access_key_id'], aws_secret_access_key=credentials['aws_secret_access_key'])    
        
                
    for current_reservation in conn.get_all_instances():
        for current_instance in current_reservation.instances:                    
            print current_instance.key_name 
        
    raw_input('press ok')
