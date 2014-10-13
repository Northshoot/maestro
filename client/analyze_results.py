import os



def max_from_two(a, b):
	if a < b:
		return b
	else:
		return a

def analyze_global_performances(f_output, input_dir):
	print os.listdir(input_dir)
	f_output.write('\t Global performances : \n')
	f_global_performances = open(input_dir + '/Global_Performances', 'r')
	measures = f_global_performances.read().split('\n\n')
	
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
	for current_measure in measures:
		if not 'time' in current_measure:
			continue
		
		metrics = current_measure.split('\n')
		memory_utilization = float(metrics[1].split(':')[1].split('(')[0])
		memory_used = float(metrics[2].split(':')[1].split('(')[0])
		memory_available = float(metrics[3].split(':')[1].split('(')[0])
		swap_utilization = float(metrics[4].split(':')[1].split('(')[0])
		swap_used = float(metrics[5].split(':')[1].split('(')[0])
		
		memory_utilization_max = max_from_two(memory_utilization_max, memory_utilization)
		memory_used_max = max_from_two(memory_used_max, memory_used)
		memory_available_max = max_from_two(memory_available_max, memory_available)
		swap_utilization_max = max_from_two(swap_utilization_max, swap_utilization)
		swap_used_max = max_from_two(swap_used_max, swap_used)
	
		memory_utilization_avg = ((memory_utilization_avg * counter) + memory_utilization) / (counter + 1)
		memory_used_avg = ((memory_used_avg * counter) + memory_used) / (counter + 1)
		memory_available_avg = ((memory_available_avg * counter) + memory_available) / (counter + 1)
		swap_utilization_avg = ((swap_utilization_avg * counter) + swap_utilization) / (counter + 1)
		swap_used_avg = ((swap_used_avg * counter) + swap_used) / (counter + 1)
		
		counter += 1
	f_output.write('\t\t Max memory utilization : ' + str(memory_utilization_max) + ' % \n')
	f_output.write('\t\t Max memory used: ' + str(memory_used_max) + ' Megabytes \n')
	f_output.write('\t\t Max memory available : ' + str(memory_available_max) + ' Megabytes \n')
	f_output.write('\t\t Max swap utilization : ' + str(swap_utilization_max) + ' % \n')
	f_output.write('\t\t Max swap used : ' + str(swap_used_max) + ' % \n')
	
	f_output.write('\t\t Average memory utilization : ' + str(memory_utilization_avg) + ' % \n')
	f_output.write('\t\t Average memory used: ' + str(memory_used_avg) + ' Megabytes \n')
	f_output.write('\t\t Average memory available : ' + str(memory_available_avg) + ' Megabytes \n')
	f_output.write('\t\t Average swap utilization : ' + str(swap_utilization_avg) + ' % \n')
	f_output.write('\t\t Average swap used : ' + str(swap_used_avg) + ' % \n')
	
	f_output.write('\n')
	f_global_performances.close()

def analyze_processes_performances(f_output, input_dir):
	processes_files = os.listdir(input_dir)
	processes_files.remove('Global_Performances')
	processes_files.remove('Output')
	for current_process_file in processes_files:
		pid = current_process_file.split('__')[len(current_process_file.split('__')) - 1]
		f_output.write('\t' + current_process_file.replace('__' + pid, '').replace('__', '/') + ' (pid=' + pid + ')\n')
		f_process_file = open(input_dir + '/' + current_process_file, 'r')
		measures_str = f_process_file.read()
		measures_tab = []
		measures_tab = measures_str.split('\n')
			
		memory_utilization_max = 0.0
		cpu_utilization_max = 0.0
		
		memory_utilization_avg = 0.0
		cpu_utilization_avg = 0.0
		
		counter = 0.0
		for current_measure in measures_tab:
			try:
				
				line_values_id = 0 
				if not (('{' in current_measure) and ('}' in current_measure)):
					continue

				memory_utilization = current_measure.split(',')[2].split('\'')[3]
				cpu_utilization = current_measure.split(',')[1].split('\'')[3]
				# print current_measure.split('\n')[line_values_id].split()
				
				# print current_measure.split('\n')[line_values_id].split()
				memory_utilization_max = max_from_two(memory_utilization_max, memory_utilization)
				cpu_utilization_max = max_from_two(cpu_utilization_max, cpu_utilization)
				if not ('.' in memory_utilization_max and '.' in cpu_utilization_max):
					continue
				if (float(cpu_utilization_max) > 100):
					print 'line ', current_measure.split('\n')[line_values_id].split()
					raw_input('ok')
				
				memory_utilization_avg = ((memory_utilization_avg * counter) + float(memory_utilization)) / (counter + 1)
				cpu_utilization_avg = ((cpu_utilization_avg * counter) + float(cpu_utilization)) / (counter + 1) 
				counter = float(counter) + 1
			except:
				continue
		f_output.write('\t\t Max memory utilization : ' + str(memory_utilization_max) + ' % \n')
		f_output.write('\t\t Max cpu utilization: ' + str(cpu_utilization_max) + ' % \n')
	
		f_output.write('\t\t Average memory utilization : ' + str(memory_utilization_avg) + ' % \n')
		f_output.write('\t\t Average cpu utilization: ' + str(cpu_utilization_avg) + ' % \n')
		f_output.write('\n')

def analyze_performances(directory_results):
	results_directories = os.listdir(directory_results)	
	f_output = open('performances_analysis.txt', 'w')	
	for current_directory in results_directories:
	
		type = current_directory.split('_')[len(current_directory.split('_')) - 1]
		f_output.write(type + '\n')
		analyze_global_performances(f_output, directory_results + current_directory)
		analyze_processes_performances(f_output, directory_results + current_directory)
	f_output.close()
	
if __name__ == '__main__':
	analyze_performances('/home/ubuntu/results/')
