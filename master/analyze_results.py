'''
analyzes results of a benchmark to generate an analysis text file the will be sent as an attachment to the mail indicated in the configuration files
'''

import os
from analyze_processes_perf import getMeasures
def max(a,b):
	if a < b:
		return b
	else:
		return a

# this function analyses global performances messages from an EC2 instance that have been written in the input_dir/Global_Performances file .
# This function calculates the average and the highest value of the memory utilization of an instance during a simulation and dumps the results into the f_output file so that file can be put as an attachment to the mail to the user
def analyze_global_performances(f_output, input_dir):
	print os.listdir(input_dir)
	f_output.write('\t Global performances : \n')
	f_global_performances = open(input_dir+'/Global_Performances','r')
	measures = f_global_performances.read().split('\n\n')
	
    # first we intialize all the values we want to compute 
	memory_utilization_max = 0.0
	memory_used_max = 0.0
	memory_available_max = 0.0
	swap_utilization_max = 0.0
	swap_used_max = 0.0
	
	memory_utilization_avg = 0.0
	memory_used_avg = 0.0
	memory_available_avg = 0.0
	swap_utilization_avg = 0.0
	swap_used_avg = 0.0
	
	counter = 0
    # then for each measure, we compute the values
	for current_measure in measures:
		if not 'time' in current_measure:
			continue
		
		metrics = current_measure.split('\n')
		memory_utilization = float(metrics[1].split(':')[1].split('(')[0])
		memory_used = float(metrics[2].split(':')[1].split('(')[0])
		memory_available = float(metrics[3].split(':')[1].split('(')[0])
		swap_utilization = float(metrics[4].split(':')[1].split('(')[0])
		swap_used = float(metrics[5].split(':')[1].split('(')[0])
		
		memory_utilization_max = max(memory_utilization_max,memory_utilization)
		memory_used_max = max(memory_used_max,memory_used)
		memory_available_max = max(memory_available_max,memory_available)
		swap_utilization_max = max(swap_utilization_max,swap_utilization)
		swap_used_max = max(swap_used_max,swap_used)
	
		memory_utilization_avg = ((memory_utilization_avg * counter) + memory_utilization)/(counter+1)
		memory_used_avg = ((memory_used_avg * counter) + memory_used)/(counter+1)
		memory_available_avg = ((memory_available_avg * counter) + memory_available)/(counter+1)
		swap_utilization_avg = ((swap_utilization_avg * counter) + swap_utilization)/(counter+1)
		swap_used_avg = ((swap_used_avg * counter) + swap_used)/(counter+1)
		
		counter+=1
    # finally, we dump the results in the mail that will be sent back to the user
	f_output.write('\t\t Max memory utilization : '+str(memory_utilization_max)+' % \n')
	f_output.write('\t\t Max memory used: '+str(memory_used_max)+' Megabytes \n')
	f_output.write('\t\t Max memory available : '+str(memory_available_max)+' Megabytes \n')
	f_output.write('\t\t Max swap utilization : '+str(swap_utilization_max)+' % \n')
	f_output.write('\t\t Max swap used : '+str(swap_used_max)+' % \n')
	
	f_output.write('\t\t Average memory utilization : '+str(memory_utilization_avg)+' % \n')
	f_output.write('\t\t Average memory used: '+str(memory_used_avg)+' Megabytes \n')
	f_output.write('\t\t Average memory available : '+str(memory_available_avg)+' Megabytes \n')
	f_output.write('\t\t Average swap utilization : '+str(swap_utilization_avg)+' % \n')
	f_output.write('\t\t Average swap used : '+str(swap_used_avg)+' % \n')
	
	f_output.write('\n')
	f_global_performances.close()

# this function analyses a process performance file and calculate the average and the highest value of the CPU and the memory usage
# the results are dumped into a file that will be sent as an attachment to the user as a performance analysis document
def analyze_processes_performances(f_output,input_dir):
	processes_files = os.listdir(input_dir)
	processes_files.remove('Global_Performances')
	processes_files.remove('Output')
	for current_process_file in processes_files:
		pid = current_process_file.split('__')[len(current_process_file.split('__'))-1]
		f_output.write('\t'+current_process_file.replace('__'+pid,'').replace('__','/') + ' (pid='+pid+')\n')
		print 'input_dir ',input_dir+'/'+current_process_file
        # we dump here the results we have after the analysis of the process performance messages analysis
		f_output.write(str(getMeasures(input_dir+'/'+current_process_file)).replace('{','\n\t\t{\n\t\t').replace('}','\n\t\t}\n').replace(',','\n\t\t'))

# this function analyses a list of directories that have the results of a simulation and create a performance analysis file.	
# this will be named after its pid so resultThread's results are not mixed . Then it will be sent to the user
def analyze_performances(results_directories):
	print 'analyzing ', results_directories
	f_output = open('/home/ubuntu/results/performances_analysis_'+str(os.getpid())+'.txt','w') # we add the pid to the file name so every resultThread has a unique name
	for current_directory in results_directories:
		print 'directory  ', current_directory	
		type = current_directory.split('_')[len(current_directory.split('_'))-1]
		f_output.write(type+'\n')
		analyze_global_performances(f_output,'/home/ubuntu/results/results_with_performance_monitoring/' +current_directory)
		analyze_processes_performances(f_output,'/home/ubuntu/results/results_with_performance_monitoring/'+current_directory)
	f_output.close()
	
if __name__ == '__main__':
	files = os.listdir('/home/ubuntu/results/results_with_performance_monitoring/')
	analyze_performances(files)
