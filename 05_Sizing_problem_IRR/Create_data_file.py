# -*- coding: utf-8 -*-
"""
Created on Thu Dec 31 01:06:55 2020

@author: alire
"""

import pandas as pd
import numpy as np

def create_dat_files(number_of_evs, number_of_chargers, time_slots,arrival, depart, charger_power, soc_arr, soc_up, price, cost, scenario):
    
    price =[round(x,2) for x in price]
    
    
    # Name of the file to store data
    f_target = "scenariodata/Scenario"+str(scenario)+".dat"
    f= open(f_target,"w")
    
    f.write("set N := " )
    for i in range(number_of_evs):
        f.write(" %d"%(i+1))
    f.write(" ;\n\n")
    
    f.write("set M := " )
    for i in range(number_of_chargers):
        f.write(" %d"%(i+1))
    f.write(" ;\n\n")
    
    f.write("set T := " )
    for i in range(time_slots):
        f.write(" %d"%(i+1))
    f.write(" ;\n\n")
    
    f.write("param arrival := \n"  )
    for i in range(number_of_evs):
        f.write("    %d %d\n"%(i+1,arrival[i]))
    f.write(" ;\n\n")
    
    f.write("param depart := \n"  )
    for i in range(number_of_evs):
        f.write("    %d %d\n"%(i+1,depart[i]))
    f.write(" ;\n\n")
    
    f.write("param soc_arr := \n" )
    for i in range(number_of_evs):
        f.write(" %d %.3f\n"%(i+1, soc_arr[i]))
    f.write(" ;\n\n")
    
    f.write("param soc_up := \n" )
    for i in range(number_of_evs):
        f.write(" %d %.3f\n"%(i+1, soc_up[i]))
    f.write(" ;\n\n")
    
    f.write("param power := \n"  )
    for i in range(number_of_chargers):
        f.write("    %d %.2f\n"%(i+1,charger_power[i]))
    f.write(" ;\n\n")
    
    f.write("param price := \n"  )
    for i in range(time_slots):
        f.write("    %d %.3f\n"%(i+1,price[i]))
    f.write(" ;\n\n")
    
    f.write("param cost := \n"  )
    for i in range(number_of_chargers):
        f.write("    %d %.3f\n"%(i+1,cost[i]))
    f.write(" ;\n\n")
    
    
    f.close()
    
    pass
    
    
    
    
    
    
    