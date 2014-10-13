def getCurrentDir():
   #this handles special case when the workers are used in 
   #developing computers
    import os, platform
    current_os = platform.system()
    if current_os == 'linux':
        c_dir = os.getcwd()
        if 'lauril' in c_dir:
            return c_dir
        if 'ubuntu' in c_dir:
            return '/home/ubuntu/'
    elif current_os == 'darwin':
        return os.getcwd()
        

#set up directories    
DEFAULT_DIR=getCurrentDir()
#hack for results so that files do not end up in git
DEFAULT_DIR_R=DEFAULT_DIR#'/home/ubuntu/'
DEFAULT_CCMD=DEFAULT_DIR+'ccmd/'
WORKER_DIR=DEFAULT_DIR+'ccmd/worker/'
MASTER_DIR=DEFAULT_DIR+'ccmd/master/'
CLIENT_DIR=DEFAULT_DIR+'ccmd/client/'
RESULT_WITH_MON = DEFAULT_DIR_R+'results/results_with_performance_monitoring/'
RESULT_WITHOUT_MON = DEFAULT_DIR_R+'results/result_without_performance_monitoring/'

COMMAND_FILE='commands.cfg'
PERFORMANCE_MON_FILE='performance_monitoring.cfg'
APP_PERF_FILE = WORKER_DIR+'dir_process_perf_files/'

DEFAULT_LOG_FILE = DEFAULT_DIR+'instance.log'
#communication part
BUFFER_SIZE = 1024  # buffer size for ACK messages
BUFFER_SIZE_BIG = 16384 # buffer size to transmit files
SERVER_PORT = 22087 # port used by clients to send simulation requests
CREDENTIALS_PORT = 9998 # port used to send credentials to the server

#AWS related
AWS_PUB_META = 'wget -qO- http://instance-data/latest/meta-data/public-hostname'