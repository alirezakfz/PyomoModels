# -*- coding: utf-8 -*-
"""
Created on Sat Jan  2 11:53:39 2021

@author: alire
"""

import time
import numpy as np
from pyomo.environ import *
from pyomo.opt import SolverFactory


from ConcreteModel_ver01 import createModel
from CreateData import dataFile

"""
Defining the scenario parameters
"""

slot=1   #Add more time slot for more accurate result

number_of_EVs=15

number_of_Chargers=0  #took it from dataFile output later

number_of_scenarios=4000
           
number_of_timeslot=24*slot

Charger_Type=[4, 8, 19, 50]     #type of chargers to install

charger_cost=[1000,1500,2200, 50000]  #cost of installation

#declaring variables
arrival=list()
depart=list()
distance=list()
demand=list()
charge_power=np.empty([10,4])
installed_chargers=list()
installed_cost=list()
TFC=np.empty([10,4])
EV_samples=list()
list_data=list()


"""
Start Scenario Creation and execution
"""
start_time= time.time()

scenario_model="ChanceConstraint"
SOLVER_NAME="gurobi"
TIME_LIMIT=10800

#create a scenario data
arrival, depart, distance, demand, charge_power,installed_chargers,\
         installed_cost,TFC, EV_samples = dataFile(number_of_EVs,
                                                   number_of_timeslot,
                                                   Charger_Type,
                                                   charger_cost,
                                                   slot)

"""
Calling the model creator function based on generated data
"""
number_of_Chargers=len(installed_chargers)
#create pyomo model
model=createModel(number_of_EVs, number_of_Chargers, number_of_timeslot,
                  installed_chargers, installed_cost, arrival,depart, TFC, demand, charge_power)


  
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

results = solver.solve(model)

print("Execution time is:", time.time()- start_time)
