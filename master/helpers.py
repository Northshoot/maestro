import socket
import os
import shutil
import signal, psutil
# returns ip address
def getLocalIp() :
    try:
        return [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1][0]
    except Exception as e:
        print e
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('google.com',0))
        return s.getsockname()[0]
# prints a text
def log (txt):
    print txt
    
## return file content as string
def file_to_str(fileName):
    with open (fileName, "r") as myfile:
        data=myfile.read()
        return data 
    
def removeDir(dir_to_delete):
    try:
        if os.path.isdir(dir_to_delete):
            print shutil.rmtree(dir_to_delete)
    except Exception as e:
        print e

def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
        p = psutil.Process(parent_pid)
    except psutil.error.NoSuchProcess:
        return
    child_pid = p.get_children(recursive=True)
    log("KILLING child processes:")
    for pid in child_pid:
        pid.send_signal(sig)   

def list_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
        p = psutil.Process(parent_pid)
    except psutil.error.NoSuchProcess:
        return
    child_pid = p.get_children(recursive=True)
    log("LIST child processes:")
    for pid in child_pid:
        print pid.pid
        