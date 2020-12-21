# -*- coding: utf-8 -*-
"""
Created on Thu Dec 10 23:50:53 2020

@author: alire
"""

# libraries and data
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math

def gant_chart(num_bulbs, activity_profile):
     
    # df=activity_profile
    
    # Initialize the figure
    plt.style.use('seaborn-darkgrid')
     
    # create a color palette
    palette = plt.get_cmap('Set1')
    
    
    columns = activity_profile.columns
    
    num_plot=len(columns) - num_bulbs + 3
    
    col=4
    row = math.ceil(num_plot/col)
    
    # multiple line plot
    num=0
    
    # for column in df.drop('x', axis=1):
    for i in range(num_bulbs+3,len(columns)):
        
        num+=1
        column=columns[i]
        # Find the right spot on the plot
        plt.subplot(row,col, num)
        
     
        # Plot the lineplot
        plt.plot(activity_profile['Minute_of_day'], activity_profile[column], marker='', color=palette(num%4), linewidth=1.9, alpha=0.9, label=column)
        
        # plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=None)
        plt.subplots_adjust(bottom=0.1,  wspace=0.1, hspace=0.8)
     
        # # Same limits for everybody!
        # plt.xlim(0,10)
        # plt.ylim(-2,22)
     
        # Not ticks everywhere
        if num in range(7) :
            plt.tick_params(labelbottom='off')
        if num not in [1,4,7] :
            plt.tick_params(labelleft='off')
        
        
     
        # Add title
        plt.title(column, loc='left', fontsize=8, fontweight=0, color=palette(num%4) )
     
    # general title
    plt.suptitle("How is the appliance loads?", fontsize=13, fontweight=0, color='black', style='italic', y=1.02)
     
    # Axis title
    # plt.text(0.5, 0.5, 'Time', ha='center', va='center')
    # plt.text(0.06, 0.5, 'Note', ha='center', va='center', rotation='vertical')
