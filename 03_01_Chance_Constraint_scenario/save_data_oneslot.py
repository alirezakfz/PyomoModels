# -*- coding: utf-8 -*-
"""
Created on Wed Jan  6 22:17:29 2021

@author: alire
"""

from pyomo.environ import *
from csv import writer
import time


def csv_files(model_data,list_row, scenario_model):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    
    model_file='Model_data_'+scenario_model+'_'+timestr+'.csv'
    with open(model_file, 'w', newline='') as file:
        csv_writer = writer(file)
        csv_writer.writerow(model_data)
    
    
    
    data_file='EVs_Info_'+scenario_model+timestr+'.csv'
    with open(data_file, 'w', newline='') as file:
        csv_writer = writer(file)
        csv_writer.writerow(list_row)
        
    return model_file,data_file

def create_scenario_dat(number_of_evs,number_of_chargers,time_slots, arrival, depart, demand, charge_power,installed_chargers, installed_cost, scenario):
    
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
    
    f.write("param demand := \n"  )
    for i in range(number_of_evs):
        f.write("    %d %d\n"%(i+1,demand[i]))
    f.write(" ;\n\n")
    
    f.write("param installed_chargers := \n" )
    for i in range(number_of_chargers):
        f.write(" %d %d\n"%(i+1,installed_chargers[i]))
    f.write(" ;\n\n")
    
    f.write("param installed_cost := \n" )
    for i in range(number_of_chargers):
        f.write(" %d %d\n"%(i+1,installed_cost[i]))
    f.write(" ;\n\n")
    
    f.write("param POWER := \n"  )
    for j in range(number_of_chargers):
        for i in range(number_of_evs):
            f.write("    %d %.d %d\n"%(i+1,j+1,charge_power[i,j]))
    f.write(" ;\n\n")
    
    
    f.close()
    
    pass

    
def save_scenario(number_of_EVs,
              number_of_Chargers,
              arrival, 
              depart, 
              distance, 
              demand, 
              charge_power,
              installed_chargers, 
              installed_cost, 
              instance,
              EV_samples,
              scenario,
              scenario_model
              ):
    
    # list_header=["senario","Number_of_EVs","EV_NO","Arrival","Depart","Type","BatteryCapacity","Distance","Demand","alloc_charger","delay"]
    
    EV_types={   
            "Small":{
                    "energy_consumption":0.3790,
                    "capacity":16,  
                    "max_distance":42.2163,
                    "charge_rate":8
                    },
            "Sedan":{
                    "energy_consumption":0.4288,
                    "capacity":24,
                    "max_distance":55.9701,
                    "charge_rate":19
                    },
            "SUV":{
                    "energy_consumption":0.5740,
                    "capacity":54,
                    "max_distance":94.0766,
                    "charge_rate":50
                    },
            "Truck":{
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
    
    for ev in instance.N:
        assigned_ch = 0
        sum_ch = sum(value(instance.p[ev,ch,t])  for ch in instance.M for t in instance.T)
        assigned_ch = sum(value(instance.y[ev,ch]*ch)  for ch in instance.M)
        assigned_ch = round(assigned_ch)
        alloc_charger.append(installed_chargers[assigned_ch-1])
        # if sum_ch >= demand[value(ev)-1]  :
        #     alloc_charger.append(installed_chargers[assigned_ch-1])
        # else:
        #     return False
                    
    
    # for ev in instance.N:
    #     sum_ch=sum(value(instance.x[ev,ch,t]*ch) for ch in instance.M for t in instance.T)
    #     sum_ch=int(sum_ch)
    #     if sum_ch > 0:
    #         alloc_charger.append(installed_chargers[sum_ch-1])
    #     else:
    #         # print("NAN")
    #         return False
            
    
    
    for i in range(number_of_EVs):
        delay = sum(value(instance.c[i+1,t]*t) for t in instance.T)
        delay=round(delay)
        if delay - depart[i] > 0  :
            delay= delay - depart[i]
        else:
            delay=0
        # list_header=["model","Scenario","Number_of_EVs","EV_No","Arrival","Depart","EV_Type","BatteryCapacity","Distance","Demand","Alloc_charger","Delay"] 
        row=[scenario_model,
             scenario,
             number_of_EVs,
             i+1,
             arrival[i],
             depart[i],
             EV_samples[i],
			 'NAN',
             distance[i],
             demand[i],
             alloc_charger[i],
             delay]
        
        list_row.append(row)
     
    return list_row  

def csv_files(model_data,list_row, scenario_model):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    
    model_file='Model_data_'+scenario_model+'_'+timestr+'.csv'
    with open(model_file, 'w', newline='') as file:
        csv_writer = writer(file)
        csv_writer.writerow(model_data)
    
    
    
    data_file='EVs_Info_'+scenario_model+timestr+'.csv'
    with open(data_file, 'w', newline='') as file:
        csv_writer = writer(file)
        csv_writer.writerow(list_row)
        
    return model_file,data_file
    
    
def save_model(model_data, list_row, model_file, data_file):
    
    with open(model_file, 'a+', newline='') as file:
            csv_writer = writer(file)
            for rw in model_data:
                csv_writer.writerow(rw)            

    with open(data_file, 'a+', newline='') as file:
            csv_writer = writer(file)
            for rw in list_row:
                csv_writer.writerow(rw)
    
    return True

def save_progress(progress):
    with open('progress.txt', 'a', newline='') as file:
        file.write(progress)
