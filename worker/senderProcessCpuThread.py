'''
These functions and classes can get periodically performance data about a specific process
'''
import threading
from getMetrics import getPerfServer
from datetime import datetime
import os
import time
from ps_mem import getMemStats
import logging
#just hach to stop eclipse complaining

from ccmd.tools.defines import  WORKER_DIR
from ccmd.tools.helpers import logApp, get_all_processes




# returns a dictionnary with all performance metrics 
def get_perf_current_process(pid):
    processes = os.popen('ps aux u').read().split('\n') 
    result = {}
    try:
        mem_stats = getMemStats(pid) # we use another python code to get more accurate data about memory consumption 
    except Exception:
        return None
    for current_process in processes:
        if str(pid) in current_process:
            result['PID'] = pid
            result['Private memory (KiB)'] = mem_stats[0]
            result['Shared Memory (KiB)']= mem_stats[1]
            result['CPU (%)'] = current_process.split()[2]
            result['Memory (%)'] = current_process.split()[3]
            result['Time'] = str(datetime.now())
            return str(result)
    return None
    
# this python thread will write performance data periodically into files
# the lock we use here ensures that only one thread is using the command line output and the performance files,
# this prevents from errors
class senderProcessCpuThread(threading.Thread ):
    def __init__(self,frequency,command, pid, lock):
        threading.Thread.__init__(self)
        self.pid = pid
        self.Terminated = False
        self.frequency = frequency
        #time.sleep(1)
        self.lock = lock

        self.dir = WORKER_DIR + 'dir_process_perf_files'
        self.file_name = self.dir +'/'+str(command).replace('/','__').replace('.','')+'__'+str(pid)
        try:
            self.file_output = open(self.file_name,'w+')
        except Exception as e:
            logging.critical("Directory does not exist %s" %str(e))
            os.mkdir(self.dir)
            self.file_output = open(self.file_name,'a+')
            
        logApp('senderProcessCpuThread: f_output %s' %self.dir) 
       
    def run(self):
        curr_pid =self.pid
        c_pids =[]
        data =''
        while not self.Terminated:            
            try:
                
                time.sleep(float(self.frequency))
                c_pids = get_all_processes(self.pid)
                if c_pids is not None:
                    for cp in c_pids:
                        curr_pid = cp
                        pid_data = get_perf_current_process(cp)
                        #process may die before we manage to get perfm-data
                        if pid_data:
                            data = "%s\n%s" %(data,pid_data)
            except LookupError:
                if self.pid == curr_pid:                  
                    self.Terminated = True
                    logApp("#80 sender CPU thread ended")
        self.file_output.write(data + '\n')        
        self.file_output.close()


   
    def stop(self):
        self.Terminated = True   

