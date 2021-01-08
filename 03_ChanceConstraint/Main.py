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
# from ConcreteModel_ver02 import createModel
from CreateData import dataFile
from SaveResult import save_model
from chart import gant_chart

"""
Defining the scenario parameters
"""

slot=1   #Add more time slot for more accurate result

number_of_EVs=10

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
         installed_cost,TFC, EV_samples, soc = dataFile(number_of_EVs,
                                                   number_of_timeslot,
                                                   Charger_Type,
                                                   charger_cost,
                                                   slot)

electicity_price = [70,69.99,67.99,68.54,66.1,74.41,74.43,70,68.89,65.93,59.19,59.19,65.22,66.07,70.41,75.15,84.4,78.19,74.48,69.24,69.32,69.31,68.07,70.06]

"""
Calling the model creator function based on generated data
"""
number_of_Chargers=len(installed_chargers)
#create pyomo model
model=createModel(number_of_EVs, number_of_Chargers, number_of_timeslot,
                  installed_chargers, installed_cost, arrival,depart, TFC, demand, charge_power, soc, electicity_price)

  
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

ex_time=time.time()- start_time
print("Execution time is:",ex_time)

save_model(model, installed_chargers, demand,EV_samples,arrival, depart)
gant_chart(model)
