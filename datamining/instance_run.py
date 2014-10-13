'''
Created on Oct 3, 2013

@author: lauril
'''
import os
import numpy as np
import ast
from defines import time_d,t_format, cpu

class InstanceData(object):
    '''
    classdocs
    '''


    def __init__(self,mainDir, directory, files):
        '''
        Constructor
        '''
        self.path=mainDir+'/'+directory
        self.directory= directory
        self.file_perf =''
        self.file_output=''
        self.file_out=''
        self.runtime=''
        self.instance_type = self.getDirName(directory)
        self.performance_dict = []
        self.output = []
        self.performance = []
        for f in files:
            if '__home__ubuntu__dev__symphony__' in f:
                self.file_perf = self.path +'/'+f
                self.getNiceCommandName(f)
                super(InstanceData, self).__setattr__('file_perf', self.file_perf)
                super(InstanceData, self).__setattr__('command', self.command)
            elif 'Output' in f:
                self.file_output = self.path +'/'+f
                super(InstanceData, self).__setattr__('output', self.file_output)
            elif 'Global' in f:
                self.file_out = self.path +'/'+f
                super(InstanceData, self).__setattr__('PerfOut', self.file_out)
            else:
                raise OSError(2, 'InstanceData.init_data No such file', f)

        self.getRuntime()

    
    def getOutput(self):
        if len(self.output) == 0:
            try:
                self.performance = np.genfromtxt(self.file_output,delimiter="\n")                
            except Exception:
                raise

        return self.performance  
            
    def getPerformanceList(self):
        if len(self.performance) == 0:
            try:
                zero_counter = 0
                with open(self.file_perf, "r") as f:
                    self.performance = [l for l in (line.strip().strip('\n') for line in f) if l]
                for p in  self.performance:
                    
                    self.performance_dict.append(ast.literal_eval(p))
            except Exception:
                raise
        
        return self.performance    
    
    def getPerformanceDict(self):
        if len(self.performance) == 0:
            try:
                self.getPerformanceList()                    
            except Exception:
                raise
        return self.performance_dict  
        
    def getNiceCommandName(self, f_name):
        #this is highly dependent on experiment and the set up
        words = f_name.split('ns-314')
        command = words[1].split('__')
        cmd = ''
        for c in command:
            if len(c) >0:
                cmd = "%s %s" %(cmd,c)
        self.command = cmd

    def getCmdName(self):
        return self.command

    def getDictionary(self):
        return self.__dict__
 
    def getRuntime(self):
        from datetime import datetime
        if len(self.performance) == 0:
            l=self.getPerformanceDict()
        else:
            l=self.performance_dict
        start = datetime.strptime(l[0][time_d],t_format)
        stop = datetime.strptime(l[len(l)-1][time_d],t_format)
        return stop-start
    
    def getDirName(self,dirn):
        splt = dirn.split('_')
        if len(splt) == 3:
            return splt[1]+'_'+splt[2]
        else:
            return splt[1]
#     def __str__(self):
#             return str(self.__dict__.values())
#         
#     def __unicode__(self):
#             return str(self.__dict__.values())
#        
#     def __repr__(self):
#         return '<InstanceData:%s>' %self.directory


    
    
    