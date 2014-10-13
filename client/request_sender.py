#!/usr/bin/python
'''
Created on 1 may 2013

Script that send a simulation request to a CCMD server
Use this python program for the Benchmark oriented client 

@author: Laurynas Riliskis
'''
import socket

from threading import Lock
import sys

CCMD_PORT = 22087
DEFAULT_CONFIGURATION_FILES_DIRECTORY = 'cfgFiles'  # directory where the configuration files are when a benchmark oriented simulation is done

# the large scale simulation client uses multi thread, so we need to use a lock to prevent 2 threads to write at the same time
def log(txt, print_lock):
	#print_lock.acquire()
	print txt
	#print_lock.release()

def abort(msg):
	print '!'*80
	print "FATAL ERROR: %s \nCan't proceed exiting!" %msg
	print '!'*80
	sys.exit()
	
def getFileData(file_name):
	try:
		file_instances = open(file_name, 'r')
		str_instances = file_instances.read()
		file_instances.close()
		return str_instances , None
	except Exception as e:
		error = "getFileData: cant open file %s error: %s" %(file_name, e)
		return None , error 

def sendDataAndRxAck(mySocket, msg):
	try:	
		mySocket.send(msg)
		response = mySocket.recv(1024)  # wait for the ACK of the CCMD to clean the content of the socket
		return response, None
	except Exception as e:
		error = "sendDataAndRxAck: error communicating %s " %e
		return None, error
	
def sendData(mySocket, msg):
	try:	
		mySocket.send(msg)
	except Exception as e:
		error = "sendData: error communicating %s " %e
		return None, error
	
# Send a simulation request to the address CCMD_HOSTNAME with the configuration files in the 
# directory cfgFiles, the simulation will have the id simulation_number
# the lock is used to clean the output while using multi thread
def send_simulation_request(args):
	cfgFiles, simulation_number, CCMD_HOSTNAME = args
	print_lock = "___"
	log('simulation ' + str(simulation_number) + ' ==> simulation is starting', print_lock)
	# configuration files that will be sent to the CCMD
	config_file_for_instances = cfgFiles + '/instances.cfg'
	config_file_for_commands = cfgFiles + '/commands.cfg'
	config_file_for_performance_monitoring = cfgFiles + '/performance_monitoring.cfg'

	address_CCMD = (CCMD_HOSTNAME, CCMD_PORT) 
	
	try:
		mySocket = socket.socket()
		mySocket.connect(address_CCMD)
		strg, error = getFileData(config_file_for_instances)
		if error:
			abort(error)
		
		log("%d -- SENDING : %s" %(simulation_number,config_file_for_instances),print_lock)
		rx, error = sendDataAndRxAck(mySocket,strg)	
		if error:
			abort(error)
		if 'instances cfg received' in rx:
			rx = mySocket.recv(1024)
		else:
			abort("Wrong response from master %s" %rx)
			
		all_started = False
		try:
			while not all_started:				
				if 'NOTE@Started' in rx :
					#log('simulation ' + str(simulation_number) + ' ==> SERVER >>' + rx, print_lock)
					rx, error = sendDataAndRxAck(mySocket, 'ACK')
					#log('*'*80,print_lock)
					all_started = True
				elif "start_instance@" in rx:
					#log("instances Started %s" %rx)
					rx, error = sendDataAndRxAck(mySocket, "ACK")
				else:
					log("RX :: ERROR--got %s" %strg, print_lock)
		except Exception as e:
			abort(e)
			
		strg=rx
		

		if error:
			abort(error)
		elif strg != 'Ready for CMD':
			abort("wrong response: %s" % strg)
		else:
			log(strg,print_lock)
				
		strg, error = getFileData(config_file_for_commands)
		if error:
			abort(error)
		log("Sending: " + config_file_for_commands,print_lock)	
		log('*'*80,print_lock)
		rx , error = sendDataAndRxAck(mySocket, "COMMANDS@%s" %strg)	
		if error:
			abort(error)
		data = rx.split('@')
		if data[0] != 'ACK' and data[1] != 'CMD':
			abort("Error in ACK, got: %s :: %s" %(data[0],data[1]))
		
		log('simulation ' + str(simulation_number) + ' ==> SERVER >>' + rx, print_lock)
	
		strg, error = getFileData(config_file_for_performance_monitoring)
		if error:
			abort(error)
		log("Sending: " + config_file_for_performance_monitoring,print_lock)	
		rx , error = sendDataAndRxAck(mySocket, "MONITORING@%s" %strg)	
		if error:
			abort(error)
		data = rx.split('@')
		if data[0] != 'ACK' and data[1] != 'MONITORING':
			abort("Error in ACK, got: %s :: %s" %(data[0],data[1]))
		log('simulation ' + str(simulation_number) + ' ==> SERVER >>' + rx, print_lock)
		rx = mySocket.recv(1024)
		log(rx,print_lock)
		log('simulation ' + str(simulation_number) + ' ==> simulation has been started, performance and output results will be dumped in EC2 server ' + str(address_CCMD[0]), print_lock)
	

	
	
		mySocket.close()
	except Exception as e:
		print "******** Line 86 *********"
		print e
	return "Simulation Ended"
				
if __name__ == '__main__':
	send_simulation_request('cfgFiles', Lock())
	
