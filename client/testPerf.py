'''
Created on 1 maj 2013

@author: dgourillon
'''
import socket
import string
import os

config_file_for_instances = 'cfgFiles/instances.cfg'
config_file_for_commands = 'cfgFiles/commands.cfg'
config_file_for_performance_monitoring = 'cfgFiles/performance_monitoring.cfg'

address_CCMD = ('ec2-54-216-178-11.eu-west-1.compute.amazonaws.com', 22085)
mySocket = socket.socket()
mySocket.connect(address_CCMD)

file_instances = open(config_file_for_instances, 'rb')
str_instances = file_instances.read()
file_commands = open(config_file_for_commands, 'rb')
str_commands = file_commands.read()
file_perf = open(config_file_for_performance_monitoring, 'rb')
str_perf = file_perf.read()

mySocket.send(str_instances)
print 'SERVER >>', mySocket.recv(1024)

mySocket.send(str_commands)
print 'SERVER >>', mySocket.recv(1024)

mySocket.send(str_perf)
print 'SERVER >>', mySocket.recv(1024)


print 'simulation has been started, results will be dumped in EC2 server ', address_CCMD[0]
    
raw_input('press OK to quit')
    
    
