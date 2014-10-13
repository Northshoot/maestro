'''
These functions can analyze  process performance file 
and compute peak values, average and standard deviaton
for al metrics
'''

import ast
import math

# compute variance for a sery 
# we use the formula :V(X) = E(X*X)-E(X)*E(X)
def get_variance(input_list):
	
	sq_sum = 0
	for value in input_list:
		sq_sum += float(value)*float(value)
	sq_avg = sq_sum / len(input_list)
	avg = float(sum(input_list))/len(input_list)
	return (sq_avg - (avg*avg))
 #this function analyses a process performance fileand compute peak values, average 
 #and standard deviaton for al metrics
def getMeasures(perf_file):
	f_in = open(perf_file,'r')
	txt = f_in.read()
	values = {}
	nb_errors = 0
    # first we gather each value for each value for each metric in the 'values' dict
	for current_measures in txt.split('\n'):
		#print current_measures
		try:
			measures = ast.literal_eval(current_measures)
			for metric in measures.keys():
				if not 'Time' in metric: 
					if metric in values.keys():
						sery = values[metric]
						sery.append(float(measures[metric]))
						values[metric] = sery
					else:           
                                                sery = []
                                                sery.append(float(measures[metric]))
                                                values[metric] = sery 
		except:
			#print 'error with line : ', current_measures
			nb_errors+=1
	print nb_errors,'/',(len(txt.split('\n')))		
	analysis = {}
    # then we compute all the key values we chose
	for metric in values.keys():
            if 'CPU' not in str(metric):
                current_analysis = {}
                current_analysis['average']= float(sum(values[metric]))/len(values[metric])
                current_analysis['maximum'] = max(values[metric])
                current_analysis['minimum'] = min(values[metric])
                current_analysis['standard_deviation'] = math.sqrt(get_variance(values[metric]))
                analysis[metric]=current_analysis
            else:
		current_analysis = {}
                current_analysis['average'] = (values[metric])[len(values[metric])-1]
                analysis[metric] = current_analysis
	f_in.close()
	return analysis	
