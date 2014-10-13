'''
Python server to run as a deamon when the instance boots
It will execute command lines and send data about its performances

'''
import socket 
import os, sys
import multiprocessing
import time
import ConfigParser
import threading

from datetime import datetime
from instance_parser_config import get_commands
from instance_parser_config import configSectionMap
from senderThread import senderThread
from senderProcessCpuThread import senderProcessCpuThread
import logging
from time import strftime
from ccmd.tools.helpers import list_child_processes, kill_child_processes, \
                    logApp, getLocalIp, str_to_file
from ccmd.tools.defines import WORKER_DIR, COMMAND_FILE, PERFORMANCE_MON_FILE, \
                            DEFAULT_CCMD, RESULT_WITHOUT_MON, DEFAULT_DIR

logging.basicConfig(filename=DEFAULT_DIR+'instance.log',level=logging.DEBUG) 
# this locker will be used to have a clean output to the command line we use to get process consumption data, if we do not use this we have many errors
locker = threading.Lock()   

class NoSuchCommandException(Exception):
    pass
# we will use this function for executing 
# each of the command line we have with multiprocessing
def process(command__list):
    command = command__list[0]
    frequency = command__list[1]
    boolPerf = command__list[2]


    import subprocess as sub
    import shlex
    try:
        #we split command and reconstruct it in order to execute
        cmd_list = command.split('./')
        #this is the working directory
        work_dir = cmd_list[0]
        #reconstruc the executable
        cmd_n = "./%s" %cmd_list[1]
        cmd=shlex.split(cmd_n)
        logging.debug("CMD %s WORKING_DIR %s" %(cmd,work_dir))
        #OBS! IMPORTANT OBS!
        #you must have shell=False otherwise
        #p.pid will return the pid of the SHELL not the process!
        p = sub.Popen(cmd,stdout=sub.PIPE,stderr=sub.PIPE, cwd=work_dir,shell=False)
        if boolPerf == 'True':
            logApp("starting process monitoring thread for %d" %p.pid)
            cpuPerfGet = senderProcessCpuThread(frequency,command, p.pid,locker)
            cpuPerfGet.start()
        logApp("starting process p.pid %s" %str(p.pid))
        dateTimeInit = datetime.now()
        out, error = p.communicate()
        dateTimeDone = datetime.now()
    except Exception as e:
        log_data = "#63: ERROR opening process: %s :: %s" %(command,e)
        logging.critical(log_data)
        raise NoSuchCommandException(log_data)
        
    result =''
    if not error:
        result = out
        logApp("OUTPUT sim :: %s" %result)
    else:
        logging.critical("ERROR: while executing command %s :::::: \n%s"%(command,error))
        result = error
        cpuPerfGet.stop()
    logApp('command %s done ' %command)

    if boolPerf == 'True':
        cpuPerfGet.stop() 
        cpuPerfGet.join()
    srt_return = str(str(command) + \
                ":"+str(dateTimeInit) +"TTT"+ str(dateTimeDone)+ \
                "\nProcess ="+ str(p.pid) + \
                "\nOutput :\n " + str(result))
    logApp("PROCESS: %s" %srt_return)
    return srt_return

def instanceRunner():
    from ccmd.tools.helpers import initLogg
    initLogg()
    os.chdir(WORKER_DIR)
    logApp("working dir: %s" %os.getcwd())
    # first the instance waits for an initialization message from the instanceRunner
    logApp("Started main thread")
    s_init = socket.socket()         
    host_init = getLocalIp() 
    port_init = 9999
    s_init.bind((host_init, port_init))       
    s_init.listen(5)                 
    c_init, addr_init = s_init.accept()
    c_init.recv(1024)

    s = socket.socket()         
    host = getLocalIp() 
    port = 12345            
    error = False
 
    logApp( 'Server initiated!')
    logApp( 'Waiting for cfg files...')
    try:
        s.bind((host, port))        
        s.listen(5)                 
        c, addr = s.accept()    
    except Exception as e:
        logApp("#114:Error opening socket %s" %e)
        sys.exit(-1)
        
    logApp( 'Got connection from'+str( addr))
    # first we download all the configuration files that we need and we parse them
    file_cfg = c.recv(1024)
    str_to_file(WORKER_DIR+COMMAND_FILE, file_cfg)
    logApp(file_cfg)
    c.send('ACK command.cfg')
    logApp('ACK command.cfg')
    commands = get_commands(WORKER_DIR+'commands.cfg')
    logApp("commands : "+str(commands))    

    file_perf_monitoring = c.recv(1024)
    str_to_file(WORKER_DIR+PERFORMANCE_MON_FILE, file_perf_monitoring)
    logApp(file_perf_monitoring)
    c.send('ACK@perf monitoring.cfg')
    config = ConfigParser.ConfigParser()
    logApp('ACK@perf monitoring.cfg')
    
    config.read(WORKER_DIR+PERFORMANCE_MON_FILE)
    dict_perf = configSectionMap('monitoring',config)    
    frequency = dict_perf['frequency']
    bool_monitoring = dict_perf['performance_monitoring_enabled']
    mypath=WORKER_DIR+'dir_process_perf_files/'
    if not os.path.isdir(mypath):
        os.makedirs(mypath)
        logApp("#141:Created dir: %s" %mypath)
    else:
        logApp("#143:Dir %s exists, deleting old files" %mypath)
        try:
            fileList = os.listdir(mypath)
            for fileName in fileList:
                os.remove(mypath+"/"+fileName)
        except Exception as e:
            logApp("#149:Error cleaning % directory. File % gave error %s" %(mypath. fileName,e))
            

    # the senderThread will send periodically messages to tell the master server this instance is still alive
    # those messages will also have data about global performance of the server
    thread_to_contact_master_server = senderThread(c,frequency)
    commands__frequency = []
    # we prepare here a list to give to the pool class that will do tasks with multi threading. Therefore, we need to give it all the data it needs for executing the command line and the performance data gathering
    for current_command in commands:
        string_command = []
        string_command.append(str(current_command))
        string_command.append(str(frequency))
        string_command.append(bool_monitoring)
        logApp(str(string_command))
        commands__frequency.append(string_command)
    
    thread_to_contact_master_server.start()
    logApp('perf monitoring enabled : '  + bool_monitoring)
    # the pool class will execute the command lines of the configuration file 
    try:
        pool = multiprocessing.Pool(len(commands__frequency))   
        pids = pool.map_async(func=process, iterable=commands__frequency, chunksize=1)
        pool.close()
        
        # we wait here for the command lines to be done
        while not pids.ready():
#             logApp( "waiting pids.ready()" )
            time.sleep(2)
        while not pids._success:
#             logApp( "%s waiting pids._success" %strftime("%Y-%m-%d %H:%M:%S"))
#             list_child_processes(os.getpid())
            time.sleep(2)
            pool._join_exited_workers()
        result = "RESULT@%s" %str(pids.get())
    except NoSuchCommandException as nc:
        logging.critical("Aborting!!!! %s" %s)
        error = True
        
    pool.terminate()
    pool.join()
    if not error:
        # when we have done all the configuration file, we have to send back the outputs of command lines and the process performance data files
        thread_to_contact_master_server.sendMsg('EndOfSimulation')
        msg = thread_to_contact_master_server.getAck()
        logApp(msg)       
        logApp(result)
        if msg != 'ACK@EndOfSimulation':
            logApp("ERROR: RX ACK: %s" %msg)
        # we send back here the output of the command lines 
        thread_to_contact_master_server.sendMsg(result) 
        thread_to_contact_master_server.sendMsg('EndOfOutput')
        msg = thread_to_contact_master_server.getAck()
        if msg != 'ACK@EndOfOutput':
            logApp("ERROR: RX ACK: %s" %msg)
    
        if bool_monitoring == 'True':
            #then we send back all processes performance data we collected
            files_processes = os.listdir(WORKER_DIR+'dir_process_perf_files/')
            for current_perf_file in files_processes:
                f_perf_process = open(WORKER_DIR+'dir_process_perf_files/' +current_perf_file,'r')
                msg = '<new file>'+current_perf_file+'</new file>'
                thread_to_contact_master_server.sendMsg(msg)
                logApp(thread_to_contact_master_server.getAck())
                thread_to_contact_master_server.sendMsg(f_perf_process.read())
            thread_to_contact_master_server.sendMsg('EndOfFile')
            logApp(thread_to_contact_master_server.getAck())
            thread_to_contact_master_server.sendMsg('EndOfSimulationResults') 

    thread_to_contact_master_server.stop()
    thread_to_contact_master_server.join()

    c_init.close()
    s_init.close()
    c.close()
    s.close()
    list_child_processes(os.getpid())
    kill_child_processes(os.getpid())
    logApp("Exiting simulation thread")

if __name__ == '__main__':
    try:
        instanceRunner()    
    except Exception as e:
        print e
