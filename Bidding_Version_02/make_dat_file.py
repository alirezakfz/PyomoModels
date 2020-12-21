# -*- coding: utf-8 -*-
"""
Created on Sat Dec 19 12:06:03 2020

@author: alire
"""

"""
Get the name of files to create the .dat file for abstract model
"""

import pandas as pd
import numpy as np

def create_dat_files(f_inflexible, f_occupancy, f_prosumers, temperature, price, scenario):
    
    # f_inflexible="ScenarioData/inflexible_profiles.csv"
    # f_occupancy="ScenarioData/occupancy_profiles.csv"
    # f_prosumers="ScenarioData/prosumers_profiles.csv"
    
    
    # # For one case it is NOV 15 of 2019
    # nov_15=[16.784803,16.094803,15.764802,\
    #         14.774801,14.834802,14.184802,\
    #             14.144801,15.314801,16.694803,\
    #                 19.734802,24.414803,25.384802,26.744802,27.144802,\
    #                     27.524803,27.694803,26.834803,26.594803,\
    #                         25.664803,22.594803,21.394802,20.164803,\
    #                             19.584803,20.334803]
    
    # price_Nov_15 =[70,69.99,67.99,68.54,66.1,74.41,74.43,70,68.89,\
    #                65.93,59.19,59.19,65.22,66.07,70.41,75.15,84.4,\
    #                    78.19,74.48,69.24,69.32,69.31,68.07,70.06]
    
    
    # Rotate the price for 16 to 40
    array=np.array(price)
    array = np.roll(array,-15)  
    price = array.tolist()
        
    # Rotate the temprature from 16 to 24
    array=np.array(temperature)
    array = np.roll(array,-15)
    temperature = array.tolist()
    
    array=[]
    
    price =[round(x,2) for x in price]
    
    inl_loads= pd.read_csv(f_inflexible)
    occ = pd.read_csv(f_occupancy)
    profiles = pd.read_csv(f_prosumers)
    
    no_pr = len(inl_loads)
    
    # Name of the file to store data
    f_target = "scenariodata/Scenario"+str(scenario)+".dat"
    f= open(f_target,"w")
    
    
    f.write("set N := " )
    for i in range(len(inl_loads)):
        f.write(" %d"%(i+1))
    f.write(" ;\n\n")
    
    f.write("set T := " )
    for i in range(16,40):
        f.write(" %d"%(i))
    f.write(" ;\n\n")
    
    #****************************************
    #*** Electric Vehicle
    temp = profiles["Arrival"]
    f.write("param arrival := \n"  )
    for i in range(no_pr):
        f.write("    %d %d\n"%(i+1,temp[i]))
    f.write(" ;\n\n")
    
    temp = profiles["Depart"]
    f.write("param depart := \n"  )
    for i in range(no_pr):
        f.write("    %d %d\n"%(i+1,temp[i]))
    f.write(" ;\n\n")
    
    temp = profiles["EV_soc_low"]
    f.write("param soc_low := \n"  )
    for i in range(no_pr):
        f.write("    %d %.3f\n"%(i+1,temp[i]))
    f.write(" ;\n\n")
    
    temp = profiles["EV_soc_up"]
    f.write("param soc_up := \n"  )
    for i in range(no_pr):
        f.write("    %d %.3f\n"%(i+1,temp[i]))
    f.write(" ;\n\n")
    
    temp = profiles["EV_Power"]
    f.write("param ev_max_power := \n"  )
    for i in range(no_pr):
        f.write("    %d %d\n"%(i+1,temp[i]))
    f.write(" ;\n\n")
    
    temp = profiles["EV_demand"]
    f.write("param ev_demand := \n"  )
    for i in range(no_pr):
        f.write("    %d %.3f\n"%(i+1,temp[i]))
    f.write(" ;\n\n")
    
    temp = profiles["EV_soc_arr"]
    f.write("param soc_arr := \n"  )
    for i in range(no_pr):
        f.write("    %d %.3f\n"%(i+1,temp[i]))
    f.write(" ;\n\n")
    
    #*************************
    ##Bounding supply/demand bids to prosumers contract for load and generation
    f.write("param E_DA_low := %.3f ;"%(-13.8)  )
    f.write(" \n\n")
    
    f.write("param E_DA_up := %.3f;"%(138) )
    f.write(" \n\n")
    
    #Parameters for expected imbalace cost between DA and RT
    f.write("param L_DA_NEG := \n"  )
    for i in range(16,40):
        pr=price[i-16]*0.05+price[i-16]
        f.write("    %d %.3f\n"%(i,pr))
    f.write(" ;\n\n")
    
    f.write("param L_DA_POS := \n"  )
    for i in range(16,40):
        pr=price[i-16]-price[i-16]*0.05
        f.write("    %d %.3f\n"%(i,pr))
    f.write(" ;\n\n")

    # Day Ahead Energy price (First stage price).
    f.write("param L_DA := \n"  )
    for i in range(16,40):
        pr=price[i-16]
        f.write("    %d %.3f\n"%(i,pr))
    f.write(" ;\n\n")
    
    # Inflexible loads for each consumer at each time slot
    f.write("param INL := \n"  )
    for t in range(16,40):
        for i in range(no_pr):
            f.write("    %d %d  %.3f\n"%((i+1),t,inl_loads[str(t)][i]))
    f.write(" ;\n\n")
    
    
    #*******************************************
    # Parameters for Thermostatic load TCL
    temp = profiles["TCL_MAX"]
    f.write("param TCL_Max_P := \n"  )
    for i in range(no_pr):
        f.write("    %d %.3f\n"%(i+1,temp[i]))
    f.write(" ;\n\n")
    
    temp = profiles["TCL_COP"]
    f.write("param TCL_cop := \n"  )
    for i in range(no_pr):
        f.write("    %d %.3f\n"%(i+1,temp[i]))
    f.write(" ;\n\n")
    
    temp = profiles["TCL_R"]
    f.write("param TCL_R := \n"  )
    for i in range(no_pr):
        f.write("    %d %.3f\n"%(i+1,temp[i]))
    f.write(" ;\n\n")
    
    temp = profiles["TCL_C"]
    f.write("param TCL_C := \n"  )
    for i in range(no_pr):
        f.write("    %d %.3f\n"%(i+1,temp[i]))
    f.write(" ;\n\n")
    
    temp = profiles["TCL_temp_low"]
    f.write("param temp_low := \n"  )
    for i in range(no_pr):
        f.write("    %d %d\n"%(i+1,temp[i]))
    f.write(" ;\n\n")
    
    temp = profiles["TCL_temp_up"]
    f.write("param temp_up := \n"  )
    for i in range(no_pr):
        f.write("    %d %d\n"%(i+1,temp[i]))
    f.write(" ;\n\n")
    
    temp = profiles["TCL_Beta"]
    f.write("param TCL_beta := \n"  )
    for i in range(no_pr):
        f.write("    %d %.3f\n"%(i+1,temp[i]))
    f.write(" ;\n\n")
    
    f.write("param TCL_occ := \n"  )
    for t in range(16,40):
        for i in range(no_pr):
            f.write("    %d %d  %d\n"%(i+1, t, occ[str(t)][i]))
    f.write(" ;\n\n")
    

    f.write("param out_temp := \n"  )
    for i in range(16,40):
        f.write("    %d %.3f\n"%(i,temperature[i-16]))
    f.write(" ;\n\n")
    
    #**************************************************
    # Parameters for shiftable load
    
    f.write("param SL_cycle := \n"  )
    for i in range(no_pr):
        f.write("    %d %d\n"%(i+1,2))
    f.write(" ;\n\n")
    
        
    temp=np.zeros([no_pr,24])
    for i in range(no_pr):
        temp[i][0] = profiles["SL_loads1"][i]
        temp[i][1] = profiles["SL_loads2"][i]
        
    f.write("param SL_profile := \n"  )
    for t in range(16,40):
        for i in range(no_pr):
            f.write("    %d %d  %d\n"%(i+1, t, temp[i][t-16]))
    f.write(" ;\n\n")
    
    
    temp=profiles["SL_low"]
    f.write("param SL_low := \n"  )
    for i in range(no_pr):
        f.write("    %d %d \n"%(i+1, temp[i]))
    f.write(" ;\n\n")
    
    temp=profiles["SL_up"]
    f.write("param SL_up := \n"  )
    for i in range(no_pr):
        f.write("    %d %d \n"%(i+1, temp[i]))
    f.write(" ;\n\n")
    
    
    f.close()
    
    pass
    
    
    
    
    
    
    
        
    
    
    
    
    
    
    
    