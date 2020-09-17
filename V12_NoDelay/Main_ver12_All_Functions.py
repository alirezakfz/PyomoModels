# -*- coding: utf-8 -*-
"""
Created on Sun Sep  6 13:11:01 2020

@author: alire
"""

from numpy.random import randint
from numpy.random import seed
from pyomo.environ import *
import numpy as np
import math
from csv import writer
from numpy.random import seed
from numpy.random import rand

import sys
import time
from pyomo.opt import SolverFactory
import matplotlib.pyplot as plt


"""
Function to create data for simulation
Parameters include arrival_time, departure_time, ditance drived by EVs, Demand for the particular EV based on it's specification.
Normal distribution function from numpy used to generate random numbers with specified mean and variance

""" 
def dataFile(ev_no=20,time_slot=24,Charger_Type=[11,20,30],charger_cost=[300,1000,5000], slot=1):
    
    seed=np.random.randint(1,1000)
    np.random.seed(seed)
    """
    statistical driving pattern parameters
    """    
#     u_arrival   = 8.5#7
#     std_arrival = 2.2#1.73
#     alow=6
#     ahigh=11
#     #    arrival_time=np.random.rand(ev_no)*std_arrival+u_arrival
# #    arrival_time=np.random.normal(u_arrival,std_arrival,ev_no).round()
#     arrival_time=np.random.uniform(alow,ahigh,ev_no).round()
    
    
    
#     u_depart    = 18.5#18
#     std_depart  = 3.2#1.73  
    
#     dlow=15
#     dhigh=22
# #    depart_time=np.random.normal(u_depart,std_depart,ev_no).round()
#     depart_time=np.random.uniform(dlow,dhigh,ev_no).round()
#     depart_time*=slot
    
    
    
#     """
#     Distance, Dialy milage statistics
#     """
#     u_mile=40
#     std_mile=15
    
#     low_mile=25
#     high_mile=55
# #    distance=np.random.normal(u_mile,std_mile,ev_no).round()
#     distance=np.random.uniform(low_mile,high_mile,ev_no).round()
    
    
    
    """
    EVs specification
    """    
    EV_list=['small','sedan','suv','truck']
    # data from paper 06 and 02
    
    EV_types={   
            "small":{
                    "energy_consumption":0.3790,
                    "capacity":16,  
                    "max_distance":42.2163,
                    "charge_rate":8/slot
                    },
            "sedan":{
                    "energy_consumption":0.4288,
                    "capacity":24,
                    "max_distance":55.9701,
                    "charge_rate":19/slot
                    },
            "suv":{
                    "energy_consumption":0.5740,
                    "capacity":54,
                    "max_distance":94.0766,
                    "charge_rate":50/slot
                    },
            "truck":{
                    "energy_consumption":0.8180,
                    "capacity":70,
                    "max_distance":85.5745,
                    "charge_rate":50/slot
                    }
            }
    
    
    parking_share = [0.4,0.3,0.2,0.1]  #Probability of EV 
    
    EV_samples=np.random.choice(EV_list,ev_no,parking_share)
    
    
    """
    Demand for each EV
    """
    u_mile=40
    std_mile=15
    distance=[]
    
    demand=[]
    
    u_arrival   = 8.5#7
    std_arrival = 2.2#1.73
    arrival_time=[]
    
    u_depart    = 18.5#18
    std_depart  = 3.2#1.73  
    depart_time=[]
    
    check=True
    count=0
    
    min_charge=min(Charger_Type)
    
    for ev in EV_samples:
        
        charge_rate=EV_types[ev]["charge_rate"]
        
        while check:
            arrive=round(np.random.normal(u_arrival,std_arrival))
            while arrive < 1 or arrive > time_slot*slot:
                arrive=round(np.random.normal(u_arrival,std_arrival))
                                
            depart=round(np.random.normal(u_depart,std_depart))
            while depart<0 or depart>time_slot*slot:
                depart=round(np.random.normal(u_depart,std_depart))
                
                        
            dist=np.random.normal(u_mile,std_mile)
            while dist < 10 or dist > 70:
                dist=np.random.normal(u_mile,std_mile)
                               
            if dist > EV_types[ev]["max_distance"]:
                dem=round(EV_types[ev]["capacity"])
                # demand.append(round(EV_types[ev]["capacity"]))
            else:
                
                dem=round(1.0*dist*EV_types[ev]["energy_consumption"])
                # demand.append(round(1.0*distance[count]*EV_types[ev]["energy_consumption"]))
            
            if math.ceil(dem/charge_rate) < (depart-arrive):
                check=False
        
        distance.append(dist)
        arrival_time.append(arrive)
        depart_time.append(depart)
        demand.append(dem)
        check=True    
        count+=1
    

    
    
    """
    Assumption for Number of each required chrager based on the demand
    """
    total_demand=sum(demand)
    installed_chargers=[]
    installed_cost=[]
    for i in range(len(Charger_Type)):
        ch=Charger_Type[i]
        cost=charger_cost[i]
        no=math.ceil((total_demand/(ch*time_slot))) + int(total_demand/(ev_no*10))
        for i in range(no):
            installed_chargers.append(ch)
            installed_cost.append(cost)
    
    """
    Power to charge each EV in each Charger
    """
#    Charger_Type=[11,20,30]
#    charger_cost=[300, 1000, 5000]
    charge_power=np.empty((ev_no,len(installed_chargers)))
    for i in range(ev_no):
        for j in range(len(installed_chargers)):
            charge_power[i,j]=min(EV_types[EV_samples[i]]["charge_rate"],installed_chargers[j]/slot)
            
    
    """
    Time needed to complete charging EV based on charger
    """
    TFC=np.empty((ev_no,len(installed_chargers)))
    for i in range(ev_no):
        for j in range(len(installed_chargers)):
            TFC[i,j]=math.ceil(demand[i]/charge_power[i,j])
            # #check the validity of the test
            # while(TFC[i,j] > (depart_time[i]-arrival_time[i])):
            #     distance[i]=round(np.random.uniform(low_mile,high_mile))
            #     if distance[i] > EV_types[EV_samples[i]]["max_distance"]:
            #         demand[i]=(round(EV_types[EV_samples[i]]["capacity"]))
            #     else:
            #         demand[i]=(round(1.0*distance[i]*EV_types[EV_samples[i]]["energy_consumption"]))
            #     TFC[i,j]=math.ceil(demand[i]/charge_power[i,j])
    
        
    return arrival_time, depart_time, distance, demand, charge_power, installed_chargers, installed_cost, TFC, EV_samples

"""
After generating data we need to create model for the MIP.
The model created by PYOMO and could be solved by different availabel solvers.
Tested with Gurobi 9.0.3 and cplex 12.9 
"""

def createModel(number_of_EVs=5,
                number_of_Chargers=2,
                number_of_timeslot=24,
                installed_chargers=[11,20], 
                installed_cost=[11,20], 
                arrival=[3,5,6,8,9], 
                depart=[18,19,18,19,20], 
                TFC=[[1,1],[1,1],[1,1],[1,1],[1,1]]):
    
    
    bigM=10**10
    delay=0
    prf=0
    
    """
    Model Creation
    """
    model=ConcreteModel()
    model.N=RangeSet(number_of_EVs)
    model.M=RangeSet(number_of_Chargers)
    model.T=RangeSet(0,number_of_timeslot)
    
    """
    Model Parmeters
    """
    
    #randomly choose arrival time between 1 to half of the Horizon
    def arrival_init(model,j):
        return  int(arrival[j-1])
    model.arrival  = Param(model.N, initialize=arrival_init)
    
 
    
    def TFC_rule(model,i,j):
        return int(TFC[j-1,i-1])
    model.TFC = Param(model.M, model.N, rule= TFC_rule )
    
    
    #EV deparure time
    def depart_init(model,j):
        return int(depart[j-1])
    model.depart=Param(model.N, initialize=depart_init, default=number_of_timeslot)
    
     
    
    """
    Decision Variables
    """
            
    # #Variable to store relation between EV and Time slot
    # model.u   =   Var(model.M, model.N, model.T,  within=Binary, initialize=0) # The J parameter Removed in Version 09
    
    # #Varible to miantain Makespan for all EVs in fleet
    # model.v   =   Var(within=Integers, initialize=0) #within=NonNegativeIntegers,
    
    
    """
    Model Decision Variables
    """
    
    model.x=Var(model.M,model.N,model.T,within=Binary,initialize=0)
    
    
    model.C=Var(model.N,within=NonNegativeIntegers,initialize=0)
    
    #Binary variable to select charger. If charger i selected then its 1 otherwise zero
    model.q = Var (model.M, within=Binary, initialize=0)
    
    #Variable to strore the delay from the schedule
    model.d = Var (model.N, within=NonNegativeIntegers,initialize=0)
    
#    #Variable to store the total occuring delay
#    model.X = Var(within=NonNegativeIntegers,initialize=0)
#    
#    #Binary variable for delay existence
#    model.isdelay = Var(model.N, within=Binary, initialize=0)
    
    #Binary variable for limiting delay occurance in each charge station
    model.z   = Var(model.N, within=Binary, initialize=0)


    """
    model objective
    """
    # def obj_rule(model):
    #     return model.v
    # model.obj=Objective(rule=obj_rule,sense=minimize)   
    
    #Objective to minimize the cost for chrging evs
    model.obj=Objective(expr=sum(model.q[i]*installed_cost[i-1] for i in model.M), sense=minimize)

    """
    Model Constraints
    """
    #each job can start only at exactly one particular time on exactly one machine.
    def one_job_rule(model,j):
        sumj=[]
        for i in model.M:
            time=range(model.arrival[j], number_of_timeslot - model.TFC[i,j]) #model.TFC[i,j]+2
            sumj.append(sum(model.x[i,j,t] for t in time))
        return sum(sumj)==1
    model.one_job_con=Constraint(model.N, rule=one_job_rule)
            
    #ensures that at any given time on each machine at
    #most one job can be processed.
    def machine_rule(model,i,t):
        sumj=[]
        for j in model.N:
            s=max(model.arrival[j],t-model.TFC[i,j])  #model.TFC[i,j]+1
            if s>t :
#                if s > number_of_timeslot:
#                    s=number_of_timeslot
                time=range(t,s) #s+1
            else:
#                if t> number_of_timeslot:
#                    t=number_of_timeslot
                time=range(s,t) #t+1           
            sumj.append(sum(model.x[i,j,h] for h in time))
        return sum(sumj)<=1
    #    return sum(model.x[i,j,t] for j in model.ev for t in model.T )<=1
    model.machine_con=Constraint(model.M,model.T,rule=machine_rule)
   
    
   #each job cannot be processed before it is released.
    def release_rule(model,j):
        time=range(0,model.arrival[j])
        return sum(model.x[i,j,t] for i in model.M for t in time)==0
    model.release_con=Constraint(model.N,rule=release_rule)
    
    
    #the completion time of a job j can
    def span_rule(model,j):
        sumj=[]
        for i in model.M:
            time=range(0,number_of_timeslot-model.TFC[i,j]) #model.TFC[i,j]+2
            sumj.append(sum(model.x[i,j,t]*(t+model.TFC[i,j]) for t in time))
        return model.C[j]==sum(sumj)
    model.span_con=Constraint(model.N,rule=span_rule)
    
    def span_limit_rule(model,j):
        return model.C[j]<=len(model.T)
    model.span_limit_con=Constraint(model.N,rule=span_limit_rule)
    
    def cost_rule(model,i,j,t):
        # return model.q[i] <= sum(model.x[i,j,t] for j in model.ev for t in model.T)
        return   model.x[i,j,t] <= model.q[i]
    model.cost_con = Constraint(model.M, model.N, model.T, rule=cost_rule)
    
    def select_rule(model,i):
        return model.q[i]<=1
    model.select_con=Constraint(model.M, rule=select_rule)
    
   
    
    """
    version 8 constraints
    """
    def performance_rule(model):
        return sum(model.z[j] for j in model.N ) <= prf
    model.performance_con=Constraint( rule=performance_rule)
    
    def disjuctive1_rule(model,j):
#        p=sum(model.d[j] for j in model.N)
        return model.C[j] - model.depart[j] + (1-model.z[j])*bigM >= 0
    model.disjuctive1_con=Constraint(model.N, rule=disjuctive1_rule)
    
    def disjuctive2_rule(model,j):
#        p=sum(model.s[i,t]*t for t in model.T)
        return model.C[j] - model.depart[j]  - model.z[j] <= 0   #model.z[i,k]*bigM
    model.disjuctive2_con=Constraint(model.N, rule=disjuctive2_rule)
    
    """
    Version 12 constraints
    """
    def satisfy_rule(model,j):
        return sum(model.x[i,j,t] for i in model.M for t in model.T)==1
    model.satisfy_con=Constraint(model.N, rule=satisfy_rule)
    
    return model

"""
After Solving the model we can save the data used in simulation for further analysis.
Data converted into CSV and saved
"""
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
    
    list_header=["senario","Number_of_EVs","EV","Arrival","Depart","Type","BatteryCapacity","Distance","Demand","alloc_charger","delay"]
    
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
            alloc_charger.append('NAN')
                    
    
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
    with open(file_name, 'a+', newline='') as file:
            csv_writer = writer(file)
            for rw in list_element:
                csv_writer.writerow(rw)
                
    file_name='EVs_Info_No_Delay'+timestr+'.csv'
    with open(file_name, 'w', newline='') as file:
            csv_writer = writer(file)
            for rw in list_data:
                csv_writer.writerow(rw)

"""
To visualize the optimal schedule of the solved scenario following function
will do it.
To use it just stand alone scenario like the last one could be put as imput.

In the main body when solving the model could be put to visualize some selected 
solved models. for example each 500 show the solved model.
"""
def gant_chart(model):
    params = {'legend.fontsize': 'x-large',
          'figure.figsize': (15, 5),
         'axes.labelsize': 'x-large',
         'axes.titlesize':'x-large',
         'xtick.labelsize':'x-large',
         'ytick.labelsize':'x-large'}
    plt.rcParams.update(params)
    clr=["blue","green","red","magenta","yellow"]
    bw = 0.3
    plt.figure(figsize=(12, 0.7*(len(model.N))))
    idx = 0
    
    for j in model.N:
        x = model.arrival[j]
        y=  model.depart[j]
        plt.fill_between([x,y],[idx-bw,idx-bw],[idx+bw,idx+bw], color='cyan', alpha=0.6)
        
        for i in model.M:
            for t in model.T:
                if model.x[i,j,t]==1:
                    x=t
                    y=value(model.C[j])                    
                    plt.fill_between([x,y],[idx-bw,idx-bw],[idx+bw,idx+bw], color=clr[i%5], alpha=0.5)
                    plt.plot([x,y,y,x,x], [idx-bw,idx-bw,idx+bw,idx+bw,idx-bw],color='k')
                    
                    
        plt.text((x+y)/2.0,idx,
            'Job ' + str(j), color='white', weight='bold',
            horizontalalignment='center', verticalalignment='center')
        idx += 1
        
    plt.ylim(-0.5, idx-0.5)
    plt.title('Job Schedule')
    plt.xlabel('Time')
    plt.ylabel('Jobs')
    plt.yticks(range(len(model.N)))
    plt.xticks(range(len(model.T)))
    plt.grid()
    xlim = plt.xlim()
    
    
    
    
    plt.figure(figsize=(12, len(model.M)))

    for i in model.M:
        x=1
        y=0
        for j in model.N:
            idx=i-1            
            for t in model.T:
                if(model.x[i,j,t]==1):
                    if (x==1):                        
                        y=1
                    y+= model.TFC[i,j]
                    plt.fill_between([x,y],[idx-bw,idx-bw],[idx+bw,idx+bw], color=clr[i%5], alpha=0.5)
                    plt.plot([x,y,y,x,x], [idx-bw,idx-bw,idx+bw,idx+bw,idx-bw],color='k')
                    plt.text((x+y)/2.0,idx,
                            'Job ' + str(j), color='white', weight='bold',
                            horizontalalignment='center', verticalalignment='center')
                    x=y
    # plt.xlim(xlim)
    # xlim = plt.xlim()
    # plt.ylim(-0.5, len(model.Ch)-0.5)
    plt.ylim(-0.5, idx+0.5)
    plt.title('Machine Schedule')
    plt.yticks(range(len(model.M)))
    plt.ylabel('Machines')
    
    plt.xlabel('Time')
    plt.xticks(range(len(model.T)))
    plt.grid()

"""
Main body to call for solving model and creating scenario.
"""

def solve_model(number_of_EVs,number_of_Chargers,number_of_scenarios, number_of_timeslot, Charger_Type,charger_cost, slot):
    #save model data
    model_data=[]
    
    list_row=[]
    
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
    solver=SolverFactory("gurobi")
    
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
        # results = solver.solve(model)
        
        while True:
            if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
                # Do something when the solution in optimal and feasible
    #            print(results)
                
        
                break
            elif (results.solver.termination_condition == TerminationCondition.infeasible or results.solver.status != SolverStatus.ok ):
                # Do something when model in infeasible
                print("******** Infeasible Problem ************")  
                model=createModel(number_of_EVs,number_of_Chargers,number_of_timeslot,Charger_Type,active_chargers, cost, slot)
                
                # solver=SolverFactory("gurobi")
                results = solver.solve(model)
        
    
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
        
        if scenario % 20 ==0:
            number_of_EVs +=5
            print("Reached to scenario:",scenario)
    
    return model_data, list_row

"""
The main part of the program
"""

"""
Defining the scenario parameters
"""

slot=2     #Add more time slot for more accurate result

number_of_EVs=20

number_of_Chargers=0  #took it from dataFile output later

number_of_scenarios=100
           
number_of_timeslot=24*slot

Charger_Type=[4, 8, 19, 50]     #type of chargers to install

charger_cost=[1000,1500,2200, 50000]  #cost of installation

start_time= time.time()

#start to solve it for different scenarios
model_data,list_row =solve_model(number_of_EVs,number_of_Chargers,number_of_scenarios, number_of_timeslot, Charger_Type,charger_cost, slot)

print(">>>>>>>>>  time taken:{:0.3f} <<<<<<<".format(time.time()-start_time))

save_model(model_data,list_row)


