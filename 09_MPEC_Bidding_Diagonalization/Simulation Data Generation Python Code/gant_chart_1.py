# -*- coding: utf-8 -*-
"""
Created on Thu Dec 10 18:01:01 2020

@author: alire
"""
import math
import pandas as pd
import matplotlib.pyplot as plt

def gant_chart(num_bulbs, activity_profile):
    
    columns = activity_profile.columns
    
    
    num_plot=len(columns)- (num_bulbs + 2)
    
    col=4
    row = math.ceil(num_plot/col)
    
    figure, axes = plt.subplots(nrows=row,ncols=col)
    
    count_col=0
    count_row=0
    
    for i in range(num_plot,len(columns)):
        activity_profile[columns[i]].plot(ax=axes[count_row,count_col], legend=False)
        
                
        count_col += 1
        if count_col == col:
            count_col=0
            count_row +=1