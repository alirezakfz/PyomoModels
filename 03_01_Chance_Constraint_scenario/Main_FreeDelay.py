# -*- coding: utf-8 -*-
"""
Created on Wed Jan  6 18:40:17 2021

@author: alire
"""

import time
import numpy as np
from pyomo.environ import *
from pyomo.opt import SolverFactory


from AbstractModel_FreeDelay import createModel

from CreateData import dataFile

from save_data_oneslot import save_scenario
from save_data_oneslot import save_model
from save_data_oneslot import csv_files
from save_data_oneslot import save_progress
from save_data_oneslot import create_scenario_dat



# ##Timer
# _start_time = time.time()

# def tic():
#     global _start_time 
#     _start_time = time.time()

# def tac():
#     t_sec = round(time.time() - _start_time)
#     (t_min, t_sec) = divmod(t_sec,60)
#     (t_hour,t_min) = divmod(t_min,60) 
#     print('Time passed: {}hour:{}min:{}sec'.format(t_hour,t_min,t_sec))


"""
Defining the scenario parameters
"""

slot=1   #Add more time slot for more accurate result

number_of_EVs=20

number_of_Chargers=0  #took it from dataFile output later

number_of_scenarios=2830
           
number_of_timeslot=24*slot

Charger_Type=[4, 8, 19]     #type of chargers to install

charger_cost=[1000,1500,2200]  #cost of installation


"""
Stroing the result and scenarios in list
"""

#save model data
model_data=[]

#save EVs Info
list_row=[]
list_data=[]

#save scenario data
list_header=["Model","Scenario","Number_of_EVs","EV_No","Arrival","Depart","EV_Type","BatteryCapacity","Distance","Demand","Alloc_charger","Delay"]
#list_row.append(list_header)



#row to be add as aheader of model_data: store Scenarios information
row=["Model","scenario","obj_value","Installation_cost","load_price","number_of_EVs","Demand"]

for ch in Charger_Type:
    row.append('AvailabeType_'+str(ch))
    row.append('InstalledType_'+str(ch))

row.append('Time')




scenario_model="CC_FreeDelay"
SOLVER_NAME="gurobi"
TIME_LIMIT=7200


#Create CSV Files to store results
model_file, data_file = csv_files(row,list_header, scenario_model)


# #create a scenario data
# arrival, depart, distance, demand, charge_power,installed_chargers,\
#          installed_cost, EV_samples, soc = dataFile(number_of_EVs,
#                                                    number_of_timeslot,
#                                                    Charger_Type,
#                                                    charger_cost,
#                                                    slot)


#declaring variables
arrival=list()
depart=list()
distance=list()
demand=list()
charge_power=np.empty([10,4])
installed_chargers=list()
installed_cost=list()
# TFC=np.empty([10,4])
EV_samples=list()
list_data=list()


"""
Calling the model creator function based on generated data
"""
# number_of_Chargers=len(installed_chargers)
#create pyomo model
# model=createModel(number_of_EVs, number_of_timeslot*slot)
start_time = time.time()


for scenario in range(620,number_of_scenarios+1): #number_of_scenarios+1
    
    arrival.clear()
    depart.clear()
    distance.clear()
    demand.clear()
    charge_power=np.empty([1,1])
    installed_chargers.clear()
    installed_cost.clear()
    # TFC=np.empty([1,1])
    EV_samples.clear()
    list_data.clear()
    
    
    model=createModel(number_of_EVs, number_of_timeslot)
    
    """
    solve the model
    """    
    solver=SolverFactory(SOLVER_NAME)
    
    if SOLVER_NAME == 'cplex':
        solver.options['timelimit'] = TIME_LIMIT
    elif SOLVER_NAME == 'glpk':         
        solver.options['tmlim'] = TIME_LIMIT
    elif SOLVER_NAME == 'gurobi':           
        solver.options['TimeLimit'] = TIME_LIMIT
    
    
    
    solver_time=time.time()
    data=DataPortal(model=model)
    f_target = "scenariodata/Scenario"+str(scenario)+".dat"
    data.load(filename=f_target)
    instance = model.create_instance(data)
    results = solver.solve(instance)
    solver_time=time.time()-solver_time
    
    for i in instance.N:
        arrival.append(value(instance.arrival[i]))
        depart.append(value(instance.depart[i]))
        distance.append('NAN')
        demand.append(value(instance.demand[i]))
        
        EV_samples.append('NAN')
    
    for j in instance.M:
        installed_chargers.append(value(instance.installed_chargers[j]))
        installed_cost.append(value(instance.installed_cost[j]))
        
    
    
    number_of_Chargers=len(installed_chargers)
    
    charge_power=np.zeros((number_of_EVs,number_of_Chargers),dtype=int)
    
    
    list_data=save_scenario(number_of_EVs,
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
                              scenario_model)
    
    
    
    
    
    
    
    # #create a scenario data
    # arrival, depart, distance, demand, charge_power,installed_chargers,\
    #          installed_cost, EV_samples, soc = dataFile(number_of_EVs,
    #                                                    number_of_timeslot,
    #                                                    Charger_Type,
    #                                                    charger_cost,
    #                                                    slot)


    # """
    # Calling the model creator function based on generated data
    # """
    # number_of_Chargers=len(installed_chargers)
    # create_scenario_dat(number_of_EVs,number_of_Chargers,number_of_timeslot,\
    #                     arrival, depart, demand, charge_power,\
    #                     installed_chargers,installed_cost,scenario)
    
    # model=createModel(number_of_EVs, number_of_timeslot)
    
    
    # """
    # solve the model
    # """    
    # solver=SolverFactory(SOLVER_NAME)
    
    # if SOLVER_NAME == 'cplex':
    #     solver.options['timelimit'] = TIME_LIMIT
    # elif SOLVER_NAME == 'glpk':         
    #     solver.options['tmlim'] = TIME_LIMIT
    # elif SOLVER_NAME == 'gurobi':           
    #     solver.options['TimeLimit'] = TIME_LIMIT
    
    
    
    # solver_time=time.time()
    # data=DataPortal(model=model)
    # f_target = "scenariodata/Scenario"+str(scenario)+".dat"
    # data.load(filename=f_target)
    # instance = model.create_instance(data)
    # results = solver.solve(instance)
    # solver_time=time.time()-solver_time
    
    # while True:
    #     if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
    #         #if solver find an feasible solution
    #         list_data=save_scenario(number_of_EVs,
    #                           number_of_Chargers,
    #                           arrival, 
    #                           depart, 
    #                           distance, 
    #                           demand, 
    #                           charge_power,
    #                           installed_chargers, 
    #                           installed_cost, 
    #                           instance,
    #                           EV_samples,
    #                           scenario,
    #                           scenario_model) 
    #         #check if there is error in data
    #         if list_data:
    #             break
    #         else:
    #             #store the problem
    #             save_progress("Feasibility problem in:"+str(scenario)+"\n")
                
    #             #create a scenario data
    #             arrival, depart, distance, demand, charge_power,installed_chargers,\
    #                 installed_cost, EV_samples, soc = dataFile(number_of_EVs,
    #                                                                number_of_timeslot,
    #                                                                Charger_Type,
    #                                                                charger_cost,
    #                                                                slot)
                
    #             number_of_Chargers=len(installed_chargers)
    #             create_scenario_dat(number_of_EVs,number_of_Chargers,number_of_timeslot,\
    #                                 arrival, depart, demand, charge_power,\
    #                                     installed_chargers,installed_cost,scenario)
                
    #             model=createModel(number_of_EVs, number_of_timeslot)
                
    #             solver_time=time.time()
    #             data=DataPortal(model=model)
    #             f_target = "scenariodata/Scenario"+str(scenario)+".dat"
    #             data.load(filename=f_target)
    #             instance = model.create_instance(data)
    #             results = solver.solve(instance)
    #             solver_time=time.time()-solver_time
                
    #     #check for data           
    #     elif (results.solver.termination_condition == TerminationCondition.infeasible or results.solver.status != SolverStatus.ok ):
    #         # Do something when model in infeasible
    #         #print("******** Infeasible Problem ************")  
    #         progress="******** Infeasible Problem ************" +str(scenario) +"\n"
    #         save_progress(progress)
    #         #dt=time.time()
            
    #         #create a scenario data
    #         arrival, depart, distance, demand, charge_power,installed_chargers,\
    #             installed_cost, EV_samples, soc = dataFile(number_of_EVs,
    #                                                            number_of_timeslot,
    #                                                            Charger_Type,
    #                                                            charger_cost,
    #                                                            slot)
                                    
    #         number_of_Chargers=len(installed_chargers)
    #         create_scenario_dat(number_of_EVs,number_of_Chargers,number_of_timeslot,\
    #                             arrival, depart, demand, charge_power,\
    #                                 installed_chargers,installed_cost,scenario)
            
    #         model=createModel(number_of_EVs, number_of_timeslot)
            
    #         solver_time=time.time()
    #         data=DataPortal(model=model)
    #         f_target = "scenariodata/Scenario"+str(scenario)+".dat"
    #         data.load(filename=f_target)
    #         instance = model.create_instance(data)
    #         results = solver.solve(instance)
    #         solver_time=time.time()-solver_time
            
    "Add result from the solver to store in SCV file"
    for row in list_data:
        list_row.append(row)
    
    # row=["Model","scenario","obj_value","Installation_cost","load_price","number_of_EVs","Demand"]
    Installation_cost = sum( value(instance.q[i]*instance.installed_cost[i]) for i in instance.M)
    load_price = value(instance.obj) - value(Installation_cost)
    row=[scenario_model,scenario,value(instance.obj),Installation_cost,load_price,number_of_EVs,sum(demand)]
    
    available_dict={i:0 for i in Charger_Type}
    chargers_dict={i:0 for i in Charger_Type}
    
    for j in instance.M:
        #Count number of chargers of each type in the scenario before solving the model
        available_dict[installed_chargers[j-1]] +=1 
        #Count the number of installed chargers after solving model
        if sum(value(instance.y[i,j]) for i in instance.N) >=1 :
            chargers_dict[installed_chargers[j-1]]+=1 
    
    for i in Charger_Type:
        row.append(available_dict[i])
        row.append(chargers_dict[i])
    
    row.append(str(solver_time))
    model_data.append(row)
    
    
    check=save_model(model_data,list_row,model_file, data_file)
    model_data.clear()
    list_row.clear()
	
    if scenario % 10 ==0:
        # progress="solved Scenarios: "+str(scenario) +"\n"
        # save_progress(progress)
        # check=save_model(model_data,list_row,model_file, data_file)
        # model_data.clear()
        # list_row.clear()
        progress="Saved Scenarios: "+str(scenario) + "  Number of EVs: "+ str(number_of_EVs) +"\n"
        save_progress(progress)
    #     print("solved scenarios: ",scenario)
    
    #print infor about number of scenarios
    if scenario % 200 ==0:
        number_of_EVs +=5

    
    
    
    
chaeck=save_model(model_data,list_row,model_file, data_file)
progress="Saved Scenarios: "+str(scenario) + "  Number of EVs: "+ str(number_of_EVs) + "  Running Time: " + str(time.time()-start_time) +"\n"
save_progress(progress)
       


