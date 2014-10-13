'''
Created on 1st of may 2013

Script that gives credentials to a CCMD when it starts

@author: dgourillon
'''
import socket


config_file_for_credentials = 'cfgFiles/credentials.cfg'

address_CCMD = ('130.240.231.18', 9998)
mySocket = socket.socket()
mySocket.connect(address_CCMD)

file_credentials = open(config_file_for_credentials, 'r')
str_credentials = file_credentials.read()

mySocket.send(str_credentials)
print 'SERVER >>', mySocket.recv(1024)


print 'the CCMD has been connected to EC2 instances '
    
raw_input('press OK to quit')
    
    
