'''

Function that uses the perl script provided by Amazon to get Global performances about the instance
'''
import os
from datetime import datetime
import logging
import inspect
logging.basicConfig(filename='/home/ubuntu/instance.log',level=logging.DEBUG)

def caller_name():
	frame=inspect.currentframe()
	frame=frame.f_back.f_back
	code=frame.f_code
	return code.co_filename

def getPerfServer():
	caller = caller_name()
	logging.info('called from [%s] ' % caller )
	result = os.popen("sudo /home/ubuntu/aws-scripts-mon/mon-put-instance-data.pl  --aws-credential-file=/home/ubuntu/ccmd/worker/awscreds.template --mem-util --mem-used --mem-avail --swap-util --swap-used --verbose --verify").read()
	if result is not None:
		str_result = "time="+str(datetime.now())+'\n'+ result[:-35].split('Payload')[0]
		logging.debug(str_result)
		return str_result
	else: 
		file_perf = open('results_perf','r')
		def_perf = str(file_perf.read())[:-10]
		logging.debug( "error default output is sent: %s" %def_perf)
		return def_perf
	return

#if __name__ == '__main__':
	#print getPerfServer()
