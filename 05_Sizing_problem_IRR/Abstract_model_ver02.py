# -*- coding: utf-8 -*-
"""
Created on Wed Dec 30 22:11:24 2020

@author: alire
"""

from pyomo.environ import *


model = AbstractModel()

charge_rate =0.93

"""
Model Creation
"""
    
model.N = Set() #set of evs
model.M = Set() #set of chargers
model.T = Set() #Horizon time slot

"""
Model Parmeters
"""
model.arrival  = Param(model.N)    # EVs arrival time
model.depart   = Param(model.N)    # EVs Depart time
model.power    = Param(model.M)    # Chargers charging power
model.soc_arr  = Param(model.N)    # EVs Arrival state of charge
model.soc_up   = Param(model.N)    # EVs state of charge at department time


model.price    = Param(model.T)    # Electricity Price for each time slot
model.cost     = Param(model.M)    # Charger Cost if installed




"""
Decision Variables
"""
#Variable to store number of installed chargers
model.q   =   Var(model.M, within=NonNegativeIntegers, initialize=0)

#Variable to store relation between EV, chargers and Time slot
model.u   =   Var(model.N,model.M,model.T,within=Binary,initialize=0)

# Variable to choose charger for each EV
model.z   =  Var(model.N,model.M,within=Binary,initialize=0)

#Variable to store SOC of chargers at time t
model.SOC =   Var(model.N, model.T, within=NonNegativeReals, initialize=0)

#Variable for loaded energy at time t
model.E_EV = Var(model.N, model.T, within=NonNegativeReals, initialize=0)

# Variable for sum of the loads from the grid in each time slot
model.E_load = Var(model.T, within=NonNegativeReals, initialize=0)

# Variable to Store selling energy
model.SELL   = Var(model.T, within=NonNegativeReals, initialize=0) 

# Variable to store number of concurrent charging EVs
model.concurrent = Var(model.M, model.T, within=NonNegativeIntegers, initialize=0)



"""
model objective
"""

def obj_rule(model):
    return sum(model.cost[j]*model.q[j] for j in model.M)
model.obj=Objective(rule=obj_rule, sense=minimize)

"""
Model Constraints
"""

# At each time slot number of using chargers must be at most q[j]
def chargers_charge_rule(model, j, t):
    return sum(model.u[i,j,t] for i in model.N ) <= model.q[j]
model.EVS_charge_con=Constraint(model.M, model.T, rule=chargers_charge_rule)

# During charging period (horizon) number of EVs connected to chargers of type j must be at most q[j] 
def EVs_charge_rule(model, i, t):
    return model.concurrent[j,t] == sum(model.u[i,j,t] for i in model.N)
model.EVs_charge_con = Constraint(model.M, model.T, rule=EVs_charge_rule)

# Number of concurrent EVs charge at each time must be less than 

    
# Each EV must be connected to one charger
def one_charger_rule(model, i):
    return sum(model.z[i,j] for j in model.M) == 1
model.one_charger_con = Constraint(model.N, rule=one_charger_rule )

# Each EV can only charge at one charger at each time slot
def one_time_rule(model, i, j, t):
    return model.u[i,j,t] <= model.z[i,j]
model.one_time_con = Constraint(model.N, model.M, model.T, rule=one_time_rule)

# Control variable is zero before arrival time
def arrival_rule(model, i,j,t):
    if t < model.arrival[i] or t>= model.depart[i]:
        return model.u[i,j,t]==0
    else:
        return Constraint.Skip
model.arrival_con = Constraint(model.N, model.M, model.T, rule=arrival_rule)

# # EVs load electricity from grid during time t
# def load_rule(model,i , t):
#     if t >= model.arrival[i] and t < model.depart[i] :
#         return model.E_EV[i,t] == sum(model.u[i,j,t]*model.power[j] for j in model.M)
#     else:
#         return Constraint.Skip
# model.load_con = Constraint(model.N,model.M, rule=load_rule)



#*********** The SOC part *********

# Arrival SOC 
def set_soc_rule(model, i):
    return model.SOC[i,model.arrival[i]] == model.soc_arr[i]
model.set_soc_con = Constraint(model.N, rule=set_soc_rule)

# At depart the level 
def soc_depart_rule(model, i):
    return model.SOC[i, model.depart[i]] >= model.soc_up[i]
model.soc_depart_con= Constraint(model.N, rule=soc_depart_rule)

# the SOC at each time slot during presence in parking lot
def soc_increment_rule(model,i,t):
    if t >= model.arrival[i] and t < model.depart[i]:
        return model.SOC[i,t+1] ==  model.SOC[i,t] + model.E_EV[i,t]*charge_rate #sum(model.u[i,j,t] for j in model.M)*model.E_EV[i,t]*charge_rate
    else:
        return Constraint.Skip
model.soc_increment_con=Constraint(model.N, model.T, rule=soc_increment_rule)

# The soc bound rules
def soc_lower_bound_rule(model,i, t):
    if t >= model.arrival[i] and t <= model.depart[i]:
        return model.SOC[i,t] >= model.soc_arr[i]
    else:
        return Constraint.Skip
model.soc_lower_bound_con = Constraint(model.N, model.T, rule=soc_lower_bound_rule)



# Total Energy load from the grid at each time slot
def total_load_rule(model,t ):
    return model.E_load[t] == sum(model.E_EV[i,t] for i in model.N)
model.total_load_con=Constraint(model.T, rule=total_load_rule)

# number of required chargers to satisfy the Total Load Demand
def chargers_load_rule(model, t):
    return model.E_load[t] <= sum(model.q[j]*model.power[j] for j in model.M)
model.chargers_load_con = Constraint(model.T, rule=chargers_load_rule)

"""
version 02 rules
"""
def load_lower_limit_rule(model, i, t):
    if t >= model.arrival[i] and t< model.depart[i]:
        return model.E_EV[i,t] == sum(model.z[i,j]*model.power[j]*model.u[i,j,t] for j in model.M)
    else:
        return Constraint.Skip
model.load_lower_limit_con = Constraint(model.N, model.T, rule=load_lower_limit_rule)



#*************************************************************
# Solve the model 
# from save_result import results_to_csv
from EVs_simulation import electric_vehicles
from Create_data_file import create_dat_files
from chart import gant_chart
import random


number_of_EVs=10
number_of_timeslot=24
Charger_Type=[3,7]
cost=[1000, 2500]
price=[random.randint(1,number_of_timeslot) for x in range(number_of_timeslot)]
scenario=1
slot=1

# Random EVs cases
arrival_time, depart_time, distance , charge_power, EV_samples, demand, soc = electric_vehicles(number_of_EVs, 
                                                                                                number_of_timeslot, 
                                                                                                Charger_Type,
                                                                                                slot)



# Create test case 
create_dat_files(number_of_EVs, len(Charger_Type), number_of_timeslot,
                 arrival_time, depart_time, Charger_Type, demand, soc,
                 price, cost, scenario)


SOLVER_NAME="gurobi"

solver=SolverFactory(SOLVER_NAME)
data = DataPortal(model=model)
data.load(filename="scenariodata/Scenario"+str(scenario)+".dat")

instance = model.create_instance(data)
results = solver.solve(instance)



gant_chart(instance)


for i in instance.N:
    print(value(instance.z[i,1]),"  ",value(instance.z[i,2]))

for t in instance.T:
    print(value(t)," ",value(instance.u[1,2,t]))


for t in instance.T:
    print(value(instance.SOC[1,t]))

for j in instance.M:
    print(value(instance.q[j]))


for t in instance.T:
    print(value(t)," ",value(instance.E_EV[1,t]))