#!/usr/bin/python
'''
Created on 10 august 2013

Parses a configuration file to start a large scale simulation

@author: dgourillon
'''

import os, sys
import ConfigParser
import thread
from threading import Lock
import shutil
import time
from request_sender import send_simulation_request

from ccmd.tools.defines import CLIENT_DIR
CCMD_HOSTNAME = '130.240.231.18'  # the address of the instance where the CCMD is running has to be written here

CONFIGURATION_FILE_INPUT = CLIENT_DIR+'EBS-opt-Simulation.cfg'
SIM_DIR = CLIENT_DIR+'simulations_config_directory'
print_lock = Lock()  # we use multithread to start the simulations, so we need to use a lock to have clean output for the print function 

def log(txt):
	print_lock.acquire()
	print txt
	print_lock.release()

# returns a section a config file as a dict
def configSectionMap(section, config):
	dict1 = {}
	options = config.options(section)
	for option in options:		
		try:
			dict1[option] = config.get(section, option)
			if dict1[option] == -1:
				log ("skip: %s" % option)
		except:
			log("exception on %s!" % option)
			print "Error exiting"
			sys.exit()
	return dict1
	
# parses a configuration file to create a command configuration file
def get_instances_and_cmds(configFile):
	config = ConfigParser.ConfigParser()
	try:
		config.read(configFile)		
	except Exception as e:
		print e
		sys.exit(-1)

	#create new config files	
	try:
		counter = 0
		for section in config.sections():
			if ('instance' in str(section)):
				instance = configSectionMap(section, config)
				directory_simulation = SIM_DIR+'/simulation_' + str(counter)
				os.makedirs(directory_simulation)
				counter += 1
				f_instances = open(directory_simulation + '/instances.cfg', 'w')
				f_instances.write('[instance_1]\n')
				f_instances.write('nb_of_instances: ' + instance['nb_of_instances'] + '\n')
				f_instances.write('ami_id: ' + instance['ami_id'] + '\n')
				f_instances.write('instance_type: ' + instance['instance_type'] + '\n')
				f_instances.write('security_groups: ' + instance['security_groups'] + '\n')
				f_instances.write('key_pair: ' + instance['key_pair'])
				f_instances.close()
				
				f_cmd = open(directory_simulation + '/commands.cfg', 'a')
				f_cmd.write('[command_1]\n')
				f_cmd.write('cmd: ' + instance['cmd'] + '\n')
				f_cmd.write('nb_of_execution: ' + instance['nb_of_execution'])
				f_cmd.close()
	except Exception as e:
		print "error line 60"
		print e
		sys.exit()
	

# parses the configuration file to create a performance monitoring configuration file
def get_performance_monitoring(configFile):
	config = ConfigParser.ConfigParser()
	try:
		config.read(configFile)
		perf_monitoring = configSectionMap('monitoring', config)
	except ConfigParser.NoSectionError as e:
		print "Section Monitoring"
		print e
		sys.exit(-1)
	for folder in os.listdir(CLIENT_DIR+'simulations_config_directory'):
		f_perf = open(CLIENT_DIR+'simulations_config_directory/' + str(folder) + '/performance_monitoring.cfg', 'w')
		f_perf.write('[monitoring]\n')
		f_perf.write('performance_monitoring_enabled: ' + str(perf_monitoring['performance_monitoring_enabled']) + '\n')
		f_perf.write('frequency: ' + str(perf_monitoring['frequency']) + '\n')
		f_perf.write('simulation_id: ' + str(perf_monitoring['simulation_id']) + '\n')
		f_perf.write('mail_destination: ' + str(perf_monitoring['mail_destination']))
		f_perf.close()
	
# creates directories with configuration files for simulation requests to send
def generate_config_files_for_requests(configFile):			
	#clean up previous resources
	try:
		if os.path.isdir(SIM_DIR):
			print shutil.rmtree(SIM_DIR)
	except Exception as e:
		print e
	get_instances_and_cmds(configFile)
	get_performance_monitoring(configFile)

def simulationStarter():
	import multiprocessing
	generate_config_files_for_requests(CONFIGURATION_FILE_INPUT)
	simulation_directories = os.listdir(CLIENT_DIR+'simulations_config_directory')
	log(str(len(simulation_directories)) + ' simulations will be started so you will receive as many end of simulation mails')

	args =((CLIENT_DIR+ \
		'simulations_config_directory/' + \
		 str(current_directory), counter, CCMD_HOSTNAME) \
		 	for current_directory , counter in \
		 	zip(simulation_directories,range(len(simulation_directories))))
# 		print 'args ::: ', current_directory
# 		thread.start_new_thread(send_simulation_request, (CLIENT_DIR+
# 			'simulations_config_directory/' + str(current_directory),
# 			 counter, CCMD_HOSTNAME, print_lock))
# 		counter += 1
	try:
		pool = multiprocessing.Pool(len(simulation_directories))   
		pids = pool.map_async(send_simulation_request, args)
		pool.close()
		
	except Exception as nc:
		print "135: error Aborting!!!! %s" %nc
		error = True
		

	pool.join()

	input('  ')
	sys.exit()
	
if __name__ == '__main__':
	simulationStarter()
	
