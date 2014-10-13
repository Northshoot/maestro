'''
Created on 20 may 2013
Thes classes handle all the communications with a worker instance

@author: didier gourillon
'''

import socket			   
import threading
import os, sys
import time
from ccmd.tools.helpers import removeDir
from time import  strftime
import logging

logger = logging.getLogger('CCMD.SRV.RESULT')

def log(msg):
	logger.debug(msg)
		
# this class will help us know if we can consider that we lost contact with an instance
# every time we receive a message from an instance the boolDeath will be put to False
class testConnection(threading.Thread):
	def __init__(self, period):
		threading.Thread.__init__(self)
		self.period = period
		self.boolDeath = False # False if the instance is still alive
		self.boolRun = True

	def run(self):
		while self.boolRun :
			time.sleep(self.period)
			if self.boolDeath:
				print 'the node died'
				self.boolRun = False
			else:
				self.boolDeath = True

		
		
## handles a specific instance :
##   - send config files about commands and performance monitoring
##   - monitoring of the execution of the commands on instances
##   - gather performance and output messages
## args :
## ip_address : address of the instance
## command_file : config file to send to all instances about commands to execute
## perf_file : config file to send to all instances about performance messages to send
## instance_type : type of instance (t1.micro, m1.small...)

class resultThread(threading.Thread):
	def __init__(self,ip_address, command_file, perf_file, instance_type):
		threading.Thread.__init__(self)
		self.s = socket.socket()		 
		self.host = ip_address 
		self.port = 12345
		self.results_perf = []
		self.instance_type = instance_type
		self.command_file =command_file
		self.perf_file=perf_file
		self.pid = str(os.getpid())
		self.pids = " $%s$ " %self.pid
		try:
			frq = float(perf_file.split('frequency:')[1].split('\n')[0])
			log('%s frequency: %f' %(self.pids,frq))
			self.frequency = frq
		except IndexError:
			self.frequency = 1.0
			log("%s  indexError, setting default 1.0" %self.pids)
		#self.connectionTester = testConnection(5*self.frequency)
		
		self.bool_monitoring = False
		if 'True' in perf_file:
			self.bool_monitoring = True
		
		# Sending files to the worker instances
		
		log(self.pids + 'Connecting to '+str( self.host)+str( self.port))

		# Preparing directories and files for performance and outputs results
		
		
		self.dir_results = '/home/ubuntu/results/results_with_performance_monitoring/' \
		 +str(ip_address).replace('.eu-west-1.compute.amazonaws.com', '')+ \
		 "_"+ str(instance_type)+"_EBSO"
		self.result_file_name = self.dir_results + "/Global_Performances"
		self.output_file_name = self.dir_results + "/Output"
		if self.bool_monitoring:
			# creates directory for results
			os.makedirs(self.dir_results) 
			self.fileResult = open (self.result_file_name, "w+")
			self.current_perf_per_process_file = open( self.dir_results  + "/../default_output","a")
		else:
			# creates directory for results
			self.dir_results = '/home/ubuntu/results/results_without_performance_monitoring/' + str(ip_address).replace('.eu-west-1.compute.amazonaws.com', '')+"_"+ str(instance_type) 
			if not os.path.isdir(self.dir_results):
				os.makedirs(self.dir_results)
			else:
				log(self.pid+"Directory %s exist! Deleting all files!! " \
											%self.dir_results)
				removeDir(self.dir_results)
				os.makedirs(self.dir_results)
			self.output_file_name = self.dir_results + "/Output"		

		self.boolRun = True
		self.f_output = open ('default_output','a')
		self.state = 'simulationRunning'
		log(self.pids +'initdone')
	
	def run(self):
		connected = False
		attempt=1
		while not connected:
			try:
				self.s.connect((self.host, self.port))   
				self.s.send(self.command_file)
				log("WORKER Response: " + self.s.recv(1024))		# receives and Ack message after sent file
				self.s.send(self.perf_file)
				log("WORKER Response: " +  self.s.recv(1024))		# receives and Ack message after sent file
				connected = True
			except Exception as e:
				log(self.pids + "Connection error Attempt "+str(attempt)+ \
					str( self.host)+str( self.port) + " " + e)
				time.sleep(30)
		while self.boolRun:
			try:
				log_data = "%s ::resultThread: waiting for response" \
												 %strftime("%Y-%m-%d %H:%M:%S")
				log( log_data )
				msg = self.s.recv(40000)
				log(self.pids +"State: %s :::RX::: %d" %(self.state,len(msg)))
				# when the simulation is running the resultThread only receives global performances data
				if self.state == 'simulationRunning':
					if self.bool_monitoring :
						self.fileResult.write((msg.split('EndOfSimulation')[0])[:-4]+"\n\n")
					
					# when the simulation is done, we send an Ack to clean the socket and we start receiving the output
					if 'EndOfSimulation' in msg :
						self.state = 'gettingOutput'
						log(self.pids +"result TH::RX:: %s" %str(len(msg)))
						self.fileResult = open (self.output_file_name,'a')
						msg = self.s.send('ACK@EndOfSimulation')
					else:
						log(self.pids +"logic does not make sense")
						
				# we receive the output of the command lines until the 'EndofOutput' message	
				elif self.state == 'gettingOutput':
					self.fileResult.write((msg.split('EndOfOutput')[0].replace('\\n','\n')))
					if 'EndOfOutput' in msg :
						self.s.send('ACK@EndOfOutput')						
						if self.bool_monitoring:
							self.state = 'gettingPerformancePerProcess'
							continue
						else :
							
							self.boolRun = False
							self.stop()
				# 	we receive the process performance messages
				#   we know in wich process file to write with the <new file> messages which indicates in which file to write
				elif self.state == 'gettingPerformancePerProcess':
					if '<new file>' in msg:
						data = msg.split('<new file>')[1].replace('</new file>','')
						self.current_perf_per_process_file = open( \
											self.dir_results  + "/"+data,'w+')
						msg = self.s.send('Ack NewFile')
						continue
					else:
						self.current_perf_per_process_file.write((msg.split('EndOfFile')[0]).split('EndOfSimulationResults')[0])
						if('EndOfFile' in msg):
							msg = self.s.send('Ack ClosedFile')
							continue
						if ('EndOfSimulationResults' in msg):							
							log(self.pids +"result TH::RX:: %s" %len(msg))
							self.s.send('Ack@EndOfSimulation')
							self.boolRun = False
							self.stop()
				else:
					log('-'*80)
					log(self.pids +"ERROR: STATELESS result thread")
					log('-'*80)
			except KeyboardInterrupt:
				print "^C detected"
				self.stop()
				
	def stop(self):
		self.Terminated = True
		self.f_output.close()
		self.fileResult.close()
		self.s.close()


## launches threads to handle performance and output results for all instances
## args :
## ip_addresses : list of instances addresses
## command_file : config file to send to all instances about commands to execute
## perf_file : config file to send to all instances about performance messages to send
## instance_types : dict which form is : {ip_address_of instance:type of instance}
def get_all_results(ip_addresses,command_file, perf_file,instance_types):  
	threads = []
	log( str(os.getpid()) + " get_all_results: instances_types " + str(instance_types))
	for current_address in ip_addresses:
		log( "get_all_results: connecting to %s " %current_address)
		rTh = resultThread(current_address,command_file, perf_file,instance_types[current_address])
		rTh.start()
		threads.append(rTh)
	bool_running_result_thread = True
	while bool_running_result_thread:
		bool_running_result_thread = False
		for current_thread in threads:
			if current_thread.boolRun:
				bool_running_result_thread = True
	results_files = []
# 	file_death_nodes = open('dead_nodes','a')
# 	for current_thread in threads:
# 		if current_thread.connectionTester.boolDeath:
# 			file_death_nodes.write(str(current_thread.instance_type)+'\n')
# 		results_files.append(current_thread.dir_results)
# 	file_death_nodes.close()
	for current_thread in threads:
		results_files.append(current_thread.dir_results)


	return results_files			



