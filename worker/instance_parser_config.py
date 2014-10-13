'''
function to get command lines from the command configuration file
'''
import ConfigParser

def log (txt):
    print txt
    
def configSectionMap(section,config):
    dict1 = {}
    options = config.options(section)
    for option in options:
        
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                log ("skip: %s" % option)
        except:
            log("exception on %s!" % option)
            dict1[option] = None
    return dict1
#parses a command configuration file to have a list of command lines 
def get_commands(configFile):
    config = ConfigParser.ConfigParser()
    config.read(configFile)
    log( config.sections())
    commands_result = []
    for section in config.sections():
        command = configSectionMap(section,config)
        for i in range(int(command['nb_of_execution'])):
            commands_result.append(command['cmd'])
    return commands_result
