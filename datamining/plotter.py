'''
Created on Oct 3, 2013

@author: lauril
'''

import numpy as np
from decimal import Decimal
from matplotlib.font_manager import FontProperties
from mpltools import layout
from mpltools import color
import matplotlib.pyplot as plt
from defines import colors_5

test={'waf -j1 build': 
          {'m1.medium': 2291.236293, 'm1.large': 1187.426631, 
           'c1.xlarge': 1197.131102, 'm1.small': 4273.953239, 
           'c1.medium': 1089.704519, 't1.micro': 9562.986263, 
           'm2.2xlarge': 932.794513, 'm3.xlarge': 899.447764}, 
      'testpy': 
            {'m1.medium': 618.797922, 'm1.large': 267.934309, 
             'c1.xlarge': 131.587043, 'm1.small': 1113.327836, 
             'c1.medium': 241.908725, 't1.micro': 1857.73153, 
             'm2.2xlarge': 149.485824, 'm3.xlarge': 132.177655}, 
      'waf build': {
            'm1.medium': 2275.524822, 'm1.large': 823.556256, 
            'c1.xlarge': 246.00472, 'm1.small': 4718.251552, 
            'c1.medium': 791.189263,  't1.micro': 9665.026566,
            'm2.2xlarge': 654.306618, 'm3.xlarge': 364.797739}}

def autolabel(rects, ax):
    for rect in rects:
        h = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*h, '%d'%int(h),
                ha='center', va='bottom')
        
def barGroups(data=test, 
              title="Test",
              f_name="test.png",
              y_label="Run time in seconds"):

#     fig = plt.figure()
#     plt.bar(range(len(data)), data.values(), align='center')
#     plt.xticks(range(len(data)), data.keys())
    
    N = 3
    ind = np.arange(N)  # the x locations for the groups
    width = 0.06      # the width of the bars
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    values = {}
    
    for keys in data:
        for key, value in data[keys].iteritems():
            values.setdefault(key, []).append(value)

    rects = []


    for i, key, colr in zip(range(len(values)),values,colors_5):
        rect = ax.bar(ind+width*i, [Decimal(x) for x in values[key]],
                       width, color=colr,align='center')
        rects.append(rect)
        
#     yvals = [236293, 797922,524822]
#     rects1 = ax.bar(ind, yvals, width, color='r')
#     zvals = [177655,177655,797739]
#     rects2 = ax.bar(ind+width, zvals, width, color='g')
#     kvals = [953239,327836,251552]
#     rects3 = ax.bar(ind+width*2, kvals, width, color='b')
    
    ax.set_ylabel(y_label)
    ax.set_xticks(ind+width*3.5,)
    
    ax.set_xticklabels( tuple(data.keys()) )  
    fontP = FontProperties()
    fontP.set_size('small')
    ax.legend( tuple([x[0] for x in rects]), 
               tuple(values.keys()),prop = fontP,
               loc='upper center', 
               bbox_to_anchor=(0.5, 1.12),
               ncol=3, fancybox=True, 
               shadow=True )



#     autolabel(rects1,ax)
#     autolabel(rects2, ax)
#     autolabel(rects3,ax)
    fig.savefig(f_name, dpi=600)
    #fig.show()
def plotCurve(data,f_name):
    fig, ax = plt.subplots()
    x = np.linspace(0,10,len(data))
    y =np.array( data, dtype=np.float )
    #y.cumsum(out=y) 
    
    # Wrap the array into a 2D array of chunks, truncating the last chunk if 
    # chunksize isn't an even divisor of the total size.
    # (This part won't use _any_ additional memory)
    chunksize = 10
    numchunks = y.size // chunksize 
    ychunks = y[:chunksize*numchunks].reshape((-1, chunksize))
    xchunks = x[:chunksize*numchunks].reshape((-1, chunksize))
    
    # Calculate the max, min, and means of chunksize-element chunks...
    max_env = ychunks.max(axis=1)
    min_env = ychunks.min(axis=1)
    ycenters = ychunks.mean(axis=1)
    xcenters = xchunks.mean(axis=1)
    
    # Now plot the bounds and the mean...
    ax.fill_between(xcenters, min_env, max_env, color='gray', 
                    edgecolor='none', alpha=0.5)
    ax.plot(xcenters, ycenters) 
    fig.savefig('%s.png' %f_name, dpi=600)
         
if __name__ == '__main__':
    barGroups(test)
