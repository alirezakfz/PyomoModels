# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 12:35:51 2020

@author: alire
"""

from sample_generation import my_distribution
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def temperature_scenarios(forecast, data_df, samples=20):
    # f_name='November_2019.xlsx'
    # sheet_name='statistics'
    
    # data_df=pd.read_excel(f_name, sheet_name=sheet_name)
    
    time = len(data_df.columns)
    
    
    scenarios= np.zeros([samples,time-1])
    
    nov_15=[16.784803,16.094803,15.764802,\
            14.774801,14.834802,14.184802,\
                14.144801,15.314801,16.694803,\
                    19.734802,24.414803,25.384802,26.744802,27.144802,\
                        27.524803,27.694803,26.834803,26.594803,\
                            25.664803,22.594803,21.394802,20.164803,\
                                19.584803,20.334803]
                                
    for i in range(1,time):
        mean=data_df.iloc[0,i]
        mean = forecast[i-1]
        # min_val=data_df.iloc[1,i]
        min_val=mean-mean * 0.2    
        # max_val=data_df.iloc[2,i]
        max_val=mean+mean * 0.2
        std=data_df.iloc[3,i]
        dist=my_distribution(min_val, max_val, mean, std)
        scenarios[:,i-1]=dist.rvs(size=samples)
        
    
    scenarios = np.round(scenarios)
    
    return scenarios


    

def main():
    
    """
    Sample data for November 2019 day 15 temperature
    """

    nov_15=[16.784803,16.094803,15.764802,\
            14.774801,14.834802,14.184802,\
                14.144801,15.314801,16.694803,\
                    19.734802,24.414803,25.384802,26.744802,27.144802,\
                        27.524803,27.694803,26.834803,26.594803,\
                            25.664803,22.594803,21.394802,20.164803,\
                                19.584803,20.334803]
    
    
    f_name='November_2019.xlsx'
    sheet_name='statistics'
    
    data_df=pd.read_excel(f_name, sheet_name=sheet_name)
    
    time = len(data_df.columns)
    samples=20
    
    X=np.arange(time-1)

    ax = plt.subplot(111)
    plt.plot(X,nov_15,'g')
    
    scenarios=temperature_scenarios(nov_15,data_df, samples)

    for i in range(samples):
        plt.plot(X,scenarios[i],'r-')



if __name__ == "__main__":
    main()
        



