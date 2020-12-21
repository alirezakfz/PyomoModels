# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 18:51:26 2020

@author: alire
"""

import numpy as np
import scipy.stats
import pandas as pd
import matplotlib.pyplot as plt

def sample_distribution(min_val, max_val, mean, std):
    scale = max_val - min_val
    location = min_val
    # Mean and standard deviation of the unscaled beta distribution
    unscaled_mean = (mean - min_val) / scale
    unscaled_var = (std / scale) ** 2
    # Computation of alpha and beta can be derived from mean and variance formulas
    t = unscaled_mean / (1 - unscaled_mean)
    beta = ((t / unscaled_var) - (t * t) - (2 * t) - 1) / ((t * t * t) + (3 * t * t) + (3 * t) + 1)
    alpha = beta * t
    # Not all parameters may produce a valid distribution
    if alpha <= 0 or beta <= 0:
        raise ValueError('Cannot create distribution for the given parameters.')
    # Make scaled beta distribution with computed parameters
    return scipy.stats.beta(alpha, beta, scale=scale, loc=location)


def generate_sample(price, temp, samples):
    
    f_name= "Day_ahead_prices.xlsx"
    sheet = "Statistics"  
    
    data_df=pd.read_excel(f_name, sheet_name=sheet)
    
    time = len(data_df.columns)
    
    tempratures=np.zeros([samples,time-1])
    prices = np.zeros([samples,time-1])
    
    # samples of tempratures around forecasted temp
    for i in range(1,time):
        mean=data_df.iloc[0,i]
        mean = temp[i-1]
        # Select min and max around the forecasted temprature
        # to bound the samples around forecasted temprature
        min_val=mean-mean * 0.2
        max_val=mean+mean * 0.2
        
        std=data_df.iloc[3,i]
        dist=sample_distribution(min_val, max_val, mean, std)
        # Samples around the current temp at time i
        tempratures[:,i-1]=dist.rvs(size=samples)
        
    
    # samples of prices around forecasted price
    f_name= "November_2019.xlsx"
    sheet = "Statistics"
    
    data_df=pd.read_excel(f_name, sheet_name=sheet)
    
    for i in range(1,time):
        mean=data_df.iloc[0,i]
        mean = price[i-1]
        min_val=data_df.iloc[1,i]
        # min_val=mean-mean * 0.2    
        max_val=data_df.iloc[2,i]
        # max_val=mean+mean * 0.2
        std=data_df.iloc[3,i]
        dist=sample_distribution(min_val, max_val, mean, std)
        prices[:,i-1]=dist.rvs(size=samples)
    
    
    return tempratures, prices


    
    
    