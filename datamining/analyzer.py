'''
Created on Oct 3, 2013

@author: lauril
'''
from os import walk
from instance_run import InstanceData as ID
from datetime import datetime
from defines import time_d,t_format,cpu,pid,mem_p,mem_pr,mem_s 
from plotter import barGroups, plotCurve
from decimal import Decimal

def getDirName(dirn):
    splt = dirn.split('_')
    if len(splt) == 3:
        return splt[1]+'_'+splt[2]
    else:
        return splt[1]

def clean(file_name):
    pass

def listDirectories(directories):
    d = []
    for (dirpath, dirnames, filenames) in walk(directories):
        d.extend(dirnames)
        break
    return d
    
def getFileNames(directory):
    f = []

    for (dirpath, dirnames, filenames) in walk(directory):
        f.extend(filenames)
        break
    return f

def countTotalPerSecond(list_of_dict,dict_key):
    #Accumulates values per second
    date_object = datetime.strptime(list_of_dict[0][time_d],t_format)
    current_time = list_of_dict[0][time_d].split('.')[0]
    val_list = []
    key_value=Decimal(list_of_dict[0][dict_key])
    last = False
    for entry in list_of_dict[1:]:
        t_now = entry[time_d].split('.')[0]         
        if current_time == t_now:
            key_value+=Decimal(entry[dict_key])
            last =True
        else:    
            val_list.append('{0:.6g}'.format(key_value))
            key_value=Decimal(entry[dict_key])
            current_time = entry[time_d].split('.')[0]
            last =False
    if last:
        val_list.append('{0:.6g}'.format(key_value)) 
    return val_list

def countTotal(list_of_dict, dict_key):
    return sum(list_of_dict[dict_key])
        
 
def getDictNumOfSameVals(list_in):    
    return dict([(x, list_in.count(x)) for x in set(list_in)])    

runtimes = {'waf -j1 build':{},'testpy':{},'waf build':{}} 
import re
p=re.compile(r'\d{4}')
def updateRunTime(dirV,cmd,rt):
    runtimes[filter(None,p.split(cmd))[0].strip()][ \
                        getDirName(dirV)]='{0:.4g}'.format(Decimal(rt)) 


ebs_opt = ['m1.large_EBSO','m1.xlarge_EBSO',
           'm3.xlarge_EBSO','m3.2xlarge_EBSO',
           'c1.xlarge_EBSO','m2.2xlarge_EBSO'
                               ]


price={ 't1.micro': 0.020, 
       'm1.small': 0.065, 
       'm1.medium': 0.130, 
       'm1.large': 0.260, 
       'm1.large_EBSO': 0.260,
       'm1.xlarge_EBSO':0.550,
       'm2.xlarge':0.460,
       'm2.2xlarge': 0.165, 
       'm2.2xlarge_EBSO': 0.165,       
       'c1.medium': 0.165, 
       'c1.xlarge': 0.660, 
       'c1.xlarge_EBSO': 0.660,       
       'm3.xlarge': 0.520, 
       'm3.xlarge_EBSO': 0.520,
       'm3.2xlarge_EBSO': 0.165         

           }

runprices = {'waf -j1 build':{},'testpy':{},'waf build':{}}                                         
def updateRunPrice(dirV,cmd,rt):
        rt=  Decimal(rt)  
        itype= filter(None,p.split(cmd))[0].strip()
        idir = getDirName(dirV)
        runprices[itype][getDirName(dirV)]= '{0:.4g}'.format(Decimal(rt)
                                                 *Decimal(price[idir])/3600)
averageECU = {'waf -j1 build':{},'testpy':{},'waf build':{}} 
def updateAveraECU(dirV,iDir):
    itype= filter(None,p.split(iDir.getCmdName()))[0].strip()
    idir = getDirName(dirV)
    averageECU[itype][idir]= totalPerECUi(dirV,iDir,
                                           Decimal(iDir.getRuntime().total_seconds())
                                           )
     
def updateAll(dirV,iData):
    __rt = iData.getRuntime().total_seconds()
    rt= Decimal(__rt)
    updateRunPrice(dirV, iData.getCmdName(), rt)
    updateRunTime(dirV, iData.getCmdName(), rt)
    updateAveraECU(dirV, iData)
    
ecus={'t1.micro': 1, 
       'm1.small': 1, 
       'm1.medium': 2, 
       'm1.large': 4, 
       'm1.large_EBSO': 4,
       'm1.xlarge_EBSO':8,
       'm2.xlarge':6.5,
       'm2.2xlarge': 13, 
       'm2.2xlarge_EBSO': 13,       
       'c1.medium': 5, 
       'c1.xlarge': 20, 
       'c1.xlarge_EBSO': 20,       
       'm3.xlarge': 13, 
       'm3.xlarge_EBSO': 13,
       'm3.2xlarge_EBSO': 26   
       
       }

def totalPerECUi(dirV,iDir, rt):
    return totalPerECU(iDir.getPerformanceDict(),
                        cpu, rt,
                         iDir.instance_type)

def totalPerECU(data_l, keys, rt, iType):
    t_c = countTotalPerSecond(data_l,keys)
    #[Decimal(x[keys]) for x in data_l]
    return '{0:.4g}'.format( \
            (sum([Decimal(x) for x in t_c])/Decimal(rt)) \
            /Decimal(ecus[iType]))
        
def numberOfPids(list_in):
    return len(set(list_in))

shared_mem = {'waf -j1 build':{},'testpy':{},'waf build':{}} 
private_mem= {'waf -j1 build':{},'testpy':{},'waf build':{}} 

def updateMemory(iType, cmd, data_shared, data_private):
    cmd=p.split(cmd)[0].strip()
    shared_mem[cmd][iType]=sum([Decimal(x)*Decimal(0.0001220703125) for x in data_shared])
    private_mem[cmd][iType]=sum([Decimal(x) for x in data_private])
    
if __name__ == '__main__':
    #read directory
    main_dir = '/home/ubuntu/results/test-3'
    perf_file = 'Global_Performances'
    dir_list = listDirectories(main_dir)
    instanceRuns = []
    log_file = open('log_%s'%main_dir.replace('/','_'), 'w+')   
    
    for d in dir_list:
        
        f_list = getFileNames(main_dir + '/' +d)
        iData = ID(mainDir=main_dir, directory=d, files=f_list)
        print iData.instance_type
        instanceRuns.append(iData)
        

        #print pidl
#         print len(cpul)
#         print len(list_of_dict)
#         print numberOfPids(pidl)
        updateAll(d, iData)
        
     
    for ir in instanceRuns:
        __rt=ir.getRuntime().total_seconds()
        rt = Decimal(__rt)
        list_of_dict = ir.getPerformanceDict()
        log_file.write("Type: %s Command: %s\n" %(ir.instance_type,ir.getCmdName()))
        cpul = countTotalPerSecond(list_of_dict,cpu)
        mem_shared = countTotalPerSecond(list_of_dict,mem_s)
        mem_private=countTotalPerSecond(list_of_dict,mem_p)
        updateMemory(ir.instance_type, ir.getCmdName(), mem_shared, mem_private)
        pidl = [x[pid] for x in list_of_dict]
        av_cpu_util_ecu = totalPerECU(list_of_dict, cpu, rt, ir.instance_type)
        log_file.write("Average CPU Utilization per ECU %s" 
                       %av_cpu_util_ecu)
#         log_file.write("\n#Total CPU: \n" )
#         log_file.write(str(cpul))
        log_file.write('\n#PID\'s: ')
        log_file.write(str(numberOfPids(pidl))+'\n')
        log_file.write(str(rt)+'\n')
        plotCurve([x[cpu] for x in list_of_dict],ir.instance_type+ '_CPU_' +ir.getCmdName())
        plotCurve([x[mem_s] for x in list_of_dict],ir.instance_type+ '_MEM_SHARE_' +ir.getCmdName())
        plotCurve([x[mem_pr] for x in list_of_dict],ir.instance_type+ '_MEM_PRIV_' +ir.getCmdName())
        print ir.instance_type
        print av_cpu_util_ecu
        log_file.write('*'*80+'\n') 
    
    print "Plotting runtime"
    barGroups(data=runtimes, title="Varying runs", 
                            f_name="plots/runtime.pdf")
    print "Plotting run price"
    barGroups(data=runprices, title="Price per run comparison",
                             f_name="plots/runprice.pdf",
                             y_label="Price per run")
    print "Plotting average ECU"
    barGroups(data=averageECU, title ="Average CPU Utilization per ECU",
                            f_name="plots/averageecu.pdf",
                            y_label="ECU usage %")
    print "Plotting private memory"
    barGroups(data=shared_mem, title ="Shared Memory Usage",
                            f_name="plots/sharedmem.pdf",
                            y_label="RAM MB")
    
    print "Plotting shared memory"
    barGroups(data=private_mem, title ="Private Memory Usage",
                            f_name="plots/privatemem.pdf",
                            y_label="RAM MB")
    
    log_file.write("*** runtime ***")
    log_file.write(str(runtimes))
    log_file.write("*** runprice ***")
    log_file.write(str(runprices))
    log_file.write("*** ECU ***")
    log_file.write(str(averageECU))
    log_file.write("*** sharedmem ***")
    log_file.write(str(shared_mem))
    log_file.write("*** privatemem ***")
    log_file.write(str(private_mem))
    log_file.close()
    
