# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 13:42:52 2020

@author: Ali
"""

import sys
import time
from pyomo.environ import *
from pyomo.opt import SolverFactory
import matplotlib.pyplot as plt



from ConcreteModel_ver12_spyder_03 import createModel
from CreateData2 import dataFile
from chart import gant_chart
from save_data import save_scenario
from save_data import save_model


"""
Defining the scenario parameters
"""

slot=2     #Add more time slot for more accurate result

number_of_EVs=25

number_of_Chargers=0  #took it from dataFile output later

number_of_scenarios=1
           
number_of_timeslot=24*slot

Charger_Type=[4, 8, 19, 50]     #type of chargers to install

charger_cost=[1000,1500,2200, 50000]  #cost of installation

start_time= time.time()


#save model data
model_data=[]

list_row=[]
list_data=[]

#save scenario data
list_header=["senario","Number_of_EVs","EV","Arrival","Depart","Type","BatteryCapacity","Distance","Demand","alloc_charger","delay"]
list_row.append(list_header)

row=["scenario","obj_value","number_of_EVs","Demand"]

for ch in Charger_Type:
    row.append('Type_'+str(ch))
    row.append('Installed_'+str(ch))

    
model_data.append(row)

"""
Start Scenario Creation and execution
"""
# solver=SolverFactory("cplex")

for scenario in range(1,number_of_scenarios+1):
    """
    clling function detaFile and using it's output for model creation
    """
    
    arrival, depart, distance, demand, charge_power,\
     installed_chargers, installed_cost, TFC,\
     EV_samples = dataFile(number_of_EVs,
                           number_of_timeslot,
                           Charger_Type,
                           charger_cost,
                           slot)
    
    
    """
    Calling the model creator function based on generated data
    """
    number_of_Chargers=len(installed_chargers)
    model=createModel(number_of_EVs, number_of_Chargers, number_of_timeslot,
                      installed_chargers, installed_cost, arrival,depart, TFC)
    
    
    """
    solve the model
    """
        
    solver=SolverFactory("gurobi")
    results = solver.solve(model)
    
    while True:
        if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
            # Do something when the solution in optimal and feasible
#            print(results)
                        
            "Add result from the solver to store in SCV file"  
            
            list_data=save_scenario(number_of_EVs,
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
                              scenario) 
            if list_data:
                break
            else:
                print("******* Feasibility Problem in Senario {}, INITIALIZING new model********".format(scenario))
                arrival, depart, distance, demand, charge_power,\
                      installed_chargers, installed_cost, TFC,\
                          EV_samples = dataFile(number_of_EVs,
                                                number_of_timeslot,
                                                Charger_Type,
                                                charger_cost,
                                                slot)
                         
                number_of_Chargers=len(installed_chargers)
                model=createModel(number_of_EVs, number_of_Chargers, number_of_timeslot,
                      installed_chargers, installed_cost, arrival,depart, TFC)
                results = solver.solve(model)
            
            
            
        elif (results.solver.termination_condition == TerminationCondition.infeasible or results.solver.status != SolverStatus.ok ):
            # Do something when model in infeasible
            print("******** Infeasible Problem ************")  
            
            arrival, depart, distance, demand, charge_power,\
                      installed_chargers, installed_cost, TFC,\
                          EV_samples = dataFile(number_of_EVs,
                                                number_of_timeslot,
                                                Charger_Type,
                                                charger_cost,
                                                slot)
                         
            number_of_Chargers=len(installed_chargers)
            model=createModel(number_of_EVs, number_of_Chargers, number_of_timeslot,
                  installed_chargers, installed_cost, arrival,depart, TFC)
            results = solver.solve(model)
                
                
    

    "Add result from the solver to store in SCV file"  
    # list_data=save_scenario(number_of_EVs,
    #                   number_of_Chargers,
    #                   arrival, 
    #                   depart, 
    #                   distance, 
    #                   demand, 
    #                   charge_power,
    #                   installed_chargers, 
    #                   installed_cost, 
    #                   TFC,
    #                   model,
    #                   EV_samples,
    #                   scenario) 
    for row in list_data:
        list_row.append(row)
    
    
    row=[scenario,value(model.obj),number_of_EVs,sum(demand)]
    available_dict={i:0 for i in Charger_Type}
    chargers_dict={i:0 for i in Charger_Type}
    for j in model.M:
        #Count number of chargers of each type in the scenario before solving the model
        available_dict[installed_chargers[j-1]] +=1 
        #Count the number of installed chargers after solving model
        if model.q[j]==1:
            chargers_dict[installed_chargers[j-1]]+=1 
        
    for i in Charger_Type:
        row.append(available_dict[i])
        row.append(chargers_dict[i])
    model_data.append(row)
    
    if scenario % 200 ==0:
        number_of_EVs +=5
        # print("solved scenarios:",scenario)
    
    if scenario % 10 ==0:
        print("solved scenarios:",scenario)
    
    # gant_chart(model)

 

print(">>>>>>>>>  time taken:{:0.3f} <<<<<<<".format(time.time()-start_time))
# print(results)

#
#print("Objective cost:",value(model.obj))
#print("\n\n")
#
gant_chart(model)
# save_model(model_data,list_row)




