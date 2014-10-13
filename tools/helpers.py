import socket
import os
import shutil
import signal, psutil
import logging

from ccmd.tools.defines import  DEFAULT_LOG_FILE
from time import strftime
import datetime
# returns ip address


def getFileTime(filePath):
    t = os.path.getmtime(filePath)
    return datetime.datetime.fromtimestamp(t)


def initLogg(log_f= DEFAULT_LOG_FILE, log_lev=logging.DEBUG):
    try:
        f=open(log_f)
        f.close()
        f_time = getFileTime(log_f)
        from os import rename
        new_f='%s.%s' %(log_f,f_time)
        rename(log_f,new_f)
    except Exception:
        #no such file
        pass
    logging.basicConfig(filename=log_f,level=log_lev)
    
    
def logApp(string):
    logging.debug("%s :: %s" %(strftime("%Y-%m-%d %H:%M:%S"),string))
    
def getLocalIp() :
    try:
        return [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1][0]
    except Exception:
        #could not get localhost, get it other hack
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('google.com',0))
        return s.getsockname()[0]


    
#   this functions dumps string into a file    
def str_to_file(nameFile, text):
    try:
        text_file = open(nameFile, "w")
        text_file.write(text)
        text_file.close()
    except Exception as e:
        logging.critical("error creating file \
             %s with data %s ::: error %s" %(nameFile,text,e))
        
        
## return file content as string
def file_to_str(fileName):
    try:
        with open (fileName, "r") as myfile:
            data=myfile.read()
            return data 
    except Exception as e:
        logging.critical(" CCMD.HELPERS " + \
                         "file_to_str " + \
                         "Error reading %s :: ERROR %s" %(fileName,e))
    
def removeDir(dir_to_delete):
    try:
        if os.path.isdir(dir_to_delete):
            logging.debug( " CCMD.HELPERS " + shutil.rmtree(dir_to_delete) )
    except Exception as e:
        logging.critical("Error deleting %s :: ERROR %s" %(dir_to_delete,e))
    
# returns a section a config file as a dict
def configSectionMap(section,config):
    dict1 = {}
    options = config.options(section)
    for option in options:    
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                pass
        except:
            logging.critical("configSectionMap::exception on %s!" % option)
            dict1[option] = None
    return dict1

def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
        p = psutil.Process(parent_pid)
    except psutil.error.NoSuchProcess:
        return
    child_pid = p.get_children(recursive=True)
    logging.warning("KILLING child processes:")
    for pid in child_pid:
        pid.send_signal(sig)   
        logging.warning("Killing: %d" %pid.pid)
        
def get_child_processes(parent_pid):
    try:
        p = psutil.Process(parent_pid)
        return p.get_children(recursive=True)
    except psutil.error.NoSuchProcess:
        return None

#returns all processes including
#parent process        
def get_all_processes(parent_pid):
    try:
        p = psutil.Process(parent_pid)
        p_list =  p.get_children(recursive=True)
        #we need only pid not a whole object
        return map(lambda x : x.pid,([p]+p_list))
    except psutil.error.NoSuchProcess:
        return None


        
def list_child_processes(parent_pid, sig=signal.SIGTERM):
    child_pid = get_child_processes(parent_pid)
    if child_pid is not None:
        for pid in child_pid:
            print pid.pid
        