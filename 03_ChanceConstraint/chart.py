# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 14:37:19 2020

@author: Ali
"""

import matplotlib.pyplot as plt
from pyomo.environ import *

def gant_chart(model):
    params = {'legend.fontsize': 'x-large',
          'figure.figsize': (15, 5),
         'axes.labelsize': 'x-large',
         'axes.titlesize':'x-large',
         'xtick.labelsize':'x-large',
         'ytick.labelsize':'x-large'}
    plt.rcParams.update(params)
    clr=["blue","green","red","magenta","yellow"]
    bw = 0.3
    plt.figure(figsize=(12, 0.7*(len(model.N))))
    idx = 0
    
    for i in model.N:
        x = model.arrival[i]
        y=  model.depart[i]
        plt.fill_between([x,y],[idx-bw,idx-bw],[idx+bw,idx+bw], color='cyan', alpha=0.6)
        
        # for i in model.M:
        #     for t in model.T:
        #         if model.x[i,j,t]==1:
        #             x=t
        #             y=value(model.C[j])                    
        #             plt.fill_between([x,y],[idx-bw,idx-bw],[idx+bw,idx+bw], color=clr[i%5], alpha=0.5)
        #             plt.plot([x,y,y,x,x], [idx-bw,idx-bw,idx+bw,idx+bw,idx-bw],color='k')
        for j in model.M:
            for t in model.T:
                if round(value(model.p[i,j,t])) > 0:
                    y=value(t+1)
                    x=value(t)
                    plt.fill_between([x,y],[idx-bw,idx-bw],[idx+bw,idx+bw], color=clr[i%5], alpha=0.5)
                    plt.plot([x,y,y,x,x], [idx-bw,idx-bw,idx+bw,idx+bw,idx-bw],color='k')
                    
                    plt.text((x+y)/2.0,idx,
                             'P' + str(round(value(model.p[i,j,t]))), color='white', weight='bold',
                             horizontalalignment='center', verticalalignment='center')
                    
                    
        # plt.text((x+y)/2.0,idx,
        #     'EV' + str(j), color='white', weight='bold',
        #     horizontalalignment='center', verticalalignment='center')
        idx += 1
        
    plt.ylim(-0.5, idx-0.5)
    plt.title(' Electric vehicle Schedules')
    plt.xlabel('Time')
    plt.ylabel('Electric Vehicles in scenario')
    plt.yticks(range(len(model.N)))
    # 
    plt.xticks(range(len(model.T)+1))
    plt.grid()
    xlim = plt.xlim()
    
    
    
    
    plt.figure(figsize=(12, len(model.M)))

    # for i in model.M:
    #     x=1
    #     y=0
    #     for j in model.N:
    #         idx=i-1            
    #         for t in model.T:
    #             if(model.x[i,j,t]==1):
    #                 if (x==1):                        
    #                     y=1
    #                 y+= model.TFC[i,j]
    #                 plt.fill_between([x,y],[idx-bw,idx-bw],[idx+bw,idx+bw], color=clr[i%5], alpha=0.5)
    #                 plt.plot([x,y,y,x,x], [idx-bw,idx-bw,idx+bw,idx+bw,idx-bw],color='k')
    #                 plt.text((x+y)/2.0,idx,
    #                         'EV' + str(j), color='white', weight='bold',
    #                         horizontalalignment='center', verticalalignment='center')
    #                 x=y
    

    for j in model.M:
        x=1
        y=0
        for t in model.T:
            temp=""
            x=value(t)
            y=value(t+1)
            for i in model.N:
                idx=j-1
                if round(value(model.p[i,j,t])) > 0:
                    temp+=str(i)+","
                    # y= value(model.C[j])
                    # x= y- value(model.TFC[j,i])
            if(temp):    
                plt.fill_between([x,y],[idx-bw,idx-bw],[idx+bw,idx+bw], color=clr[i%5], alpha=0.5)
                plt.plot([x,y,y,x,x], [idx-bw,idx-bw,idx+bw,idx+bw,idx-bw],color='k')
                plt.text((x+y)/2.0,idx,
                        temp, color='white', weight='bold',
                        horizontalalignment='center', verticalalignment='center')
                x=y
        
    
    
    # plt.xlim(xlim)
    # xlim = plt.xlim()
    # plt.ylim(-0.5, len(model.Ch)-0.5)
    plt.ylim(-0.5, idx+0.5)
    plt.title('Electric vehicle chargers assignment')
    plt.yticks(range(len(model.M)))
    plt.ylabel('Cahargers in scenario')
    
    plt.xlabel('Time')
    plt.xticks(range(25))
    plt.grid()

def gant_chart_X(model):
    params = {'legend.fontsize': 'x-large',
          'figure.figsize': (15, 5),
         'axes.labelsize': 'x-large',
         'axes.titlesize':'x-large',
         'xtick.labelsize':'x-large',
         'ytick.labelsize':'x-large'}
    plt.rcParams.update(params)
    clr=["blue","green","red","magenta","yellow"]
    bw = 0.3
    plt.figure(figsize=(12, 0.7*(len(model.N))))
    idx = 0
    
    for j in model.N:
        x = model.arrival[j]
        y=  model.depart[j]
        plt.fill_between([x,y],[idx-bw,idx-bw],[idx+bw,idx+bw], color='cyan', alpha=0.6)
        
        for i in model.M:
            for t in model.T:
                if model.x[j,i,t]==1:
                    x=t
                    y=value(model.C[j])                    
                    plt.fill_between([x,y],[idx-bw,idx-bw],[idx+bw,idx+bw], color=clr[i%5], alpha=0.5)
                    plt.plot([x,y,y,x,x], [idx-bw,idx-bw,idx+bw,idx+bw,idx-bw],color='k')
        
                    
                    
        plt.text((x+y)/2.0,idx,
            'EV' + str(j), color='white', weight='bold',
            horizontalalignment='center', verticalalignment='center')
        idx += 1
        
    plt.ylim(-0.5, idx-0.5)
    plt.title(' Electric vehicle Schedules')
    plt.xlabel('Time')
    plt.ylabel('Electric Vehicles in scenario')
    plt.yticks(range(len(model.N)))
    # 
    plt.xticks(range(len(model.T)+1))
    plt.grid()
    xlim = plt.xlim()
    
    
    
    
    plt.figure(figsize=(12, len(model.M)))

    for i in model.M:
        x=1
        y=0
        for j in model.N:
            idx=i-1            
            for t in model.T:
                if(model.x[j,i,t]==1):
                    # if (x==1):                        
                    #     y=1
                    x=t
                    y= value(model.C[j])
                    plt.fill_between([x,y],[idx-bw,idx-bw],[idx+bw,idx+bw], color=clr[i%5], alpha=0.5)
                    plt.plot([x,y,y,x,x], [idx-bw,idx-bw,idx+bw,idx+bw,idx-bw],color='k')
                    plt.text((x+y)/2.0,idx,
                            'EV' + str(j), color='white', weight='bold',
                            horizontalalignment='center', verticalalignment='center')
                    x=y
    
    
    
    
    # plt.xlim(xlim)
    # xlim = plt.xlim()
    # plt.ylim(-0.5, len(model.Ch)-0.5)
    plt.ylim(-0.5, idx+0.5)
    plt.title('Electric vehicle chargers assignment')
    plt.yticks(range(len(model.M)))
    plt.ylabel('Cahargers in scenario')
    
    plt.xlabel('Time')
    plt.xticks(range(len(model.T)+1))
    plt.grid()
