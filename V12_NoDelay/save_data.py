# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 16:59:58 2020

@author: Ali
"""
from pyomo.environ import *
from csv import writer
import time


def save_scenario(number_of_EVs,
              number_of_Chargers,
              arrival, 
              depart, 
              distance, 
              demand, 
              charge_power,
              installed_chargers, 
              installed_cost, 
              TFC,
              model,
              EV_samples,
              scenario,
              ):
    
    # list_header=["senario","Number_of_EVs","EV_NO","Arrival","Depart","Type","BatteryCapacity","Distance","Demand","alloc_charger","delay"]
    
    EV_types={   
            "small":{
                    "energy_consumption":0.3790,
                    "capacity":16,  
                    "max_distance":42.2163,
                    "charge_rate":8
                    },
            "sedan":{
                    "energy_consumption":0.4288,
                    "capacity":24,
                    "max_distance":55.9701,
                    "charge_rate":19
                    },
            "suv":{
                    "energy_consumption":0.5740,
                    "capacity":54,
                    "max_distance":94.0766,
                    "charge_rate":50
                    },
            "truck":{
                    "energy_consumption":0.8180,
                    "capacity":70,
                    "max_distance":85.5745,
                    "charge_rate":50
                    }
            }
    
    list_row=[]
    
#    if scenario==1:
#        list_row.append(list_header)
    
    alloc_charger=[]
    is_charged=False
    for ev in model.N:
        is_charged=False
        for ch in model.M:
            for t in model.T:
                if value(model.x[ch,ev,t])==1:
                    is_charged=True
                    # alloc_charger.append("Type_"+str(installed_chargers[ch-1]))
                    alloc_charger.append(installed_chargers[ch-1])
        if not is_charged:
            # alloc_charger.append("NAN")
            print("NAN")
            return False
                    
    
    for i in range(number_of_EVs):    
        if value(model.C[i+1])-value(model.depart[i+1]) >0 :
            delay=value(model.C[i+1])-value(model.depart[i+1])
        else:
            delay=0
         
        row=[scenario,
             number_of_EVs,
             i+1,
             arrival[i],
             depart[i],
             EV_samples[i],
             EV_types[EV_samples[i]]["capacity"],
             distance[i],
             demand[i],
             alloc_charger[i],
             delay]
        
        list_row.append(row)
     
    return list_row   
        
#    if scenario==1:
#        timestr = time.strftime("%Y%m%d-%H%M%S")
#        file_name='EVs_Info_'+timestr+'.csv'
#        
#        with open(file_name, 'w', newline='') as file:
#            csv_writer = writer(file)
#            for rw in list_row:
#                csv_writer.writerow(rw)
#    else:
#        file_name=name
#        with open(file_name, 'a+', newline='') as file:
#            csv_writer = writer(file)
#            for rw in list_row:
#                csv_writer.writerow(rw)
    
#    return file_name
    
def save_model(list_element, list_data):
    timestr = time.strftime("%Y%m%d-%H%M%S")
#    file_name='Model_data_'+timestr+'.csv'
    file_name='Model_data_NoDelay_'+timestr+'.csv'
    with open(file_name, 'w', newline='') as file:
            csv_writer = writer(file)
            for rw in list_element:
                csv_writer.writerow(rw)
                
    file_name='EVs_Info_No_Delay'+timestr+'.csv'
    with open(file_name, 'w', newline='') as file:
            csv_writer = writer(file)
            for rw in list_data:
                csv_writer.writerow(rw)
