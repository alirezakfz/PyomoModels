# -*- coding: utf-8 -*-
"""
Created on Thu Dec  3 18:37:35 2020

@author: alire
"""

from pyomo.environ import *
from pyomo.opt import SolverFactory
import numpy as np

from CreateData import dataFile, create_scenario
from scenarioFile import scenario_File
from RefrenceModel import createModel
from chart import gant_chart


"""
Defining the scenario parameters
"""

slot=1   #Add more time slot for more accurate result

number_of_EVs=10

number_of_Chargers=0  #took it from dataFile output later

number_of_scenarios=4000
           
number_of_timeslot=24*slot

Charger_Type=[4, 8, 19]     #type of chargers to install

charger_cost=[1000,1500,2200]  #cost of installation



"""
Initializing required data for creating scenario files
"""

#Find the max number of requiredd chargers as CS capacity
count=np.zeros(len(Charger_Type),dtype=np.int8)

for i in range(500):
    installed_chargers = dataFile(number_of_EVs,
                            number_of_timeslot,
                            Charger_Type,
                            charger_cost,
                            slot)
             
    for i in range(len(Charger_Type)):
        max_i= installed_chargers.count(Charger_Type[i])
        if count[i] < max_i:
            count[i]=max_i


#using next two variables for creating scenarios data files
number_of_Chargers = sum(count)

chargers_cost = []
installed_chargers=[]
for i in range(len(Charger_Type)):
    for j in range(count[i]):
        chargers_cost.append(charger_cost[i])
        installed_chargers.append(Charger_Type[i])
        




#creating single scenario
arrival, depart, distance, demand, charge_power,TFC, EV_samples = create_scenario(number_of_EVs,
                                                        number_of_timeslot,
                                                        Charger_Type,
                                                        charger_cost,
                                                        slot,
                                                        installed_chargers)




"""
Single scenario running and execution
This step is to check if the model mofification gives true answer or not
"""

#storing it to .dat file for abstract model
scenario_File(number_of_EVs, number_of_Chargers,chargers_cost, number_of_timeslot, arrival, depart, TFC)            


#Solve a unique scenario
SOLVER_NAME="gurobi"
TIME_LIMIT=10800
model=createModel(number_of_timeslot)
solver=SolverFactory(SOLVER_NAME)

if SOLVER_NAME == 'cplex':
    solver.options['timelimit'] = TIME_LIMIT
elif SOLVER_NAME == 'glpk':         
    solver.options['tmlim'] = TIME_LIMIT
elif SOLVER_NAME == 'gurobi':           
    solver.options['TimeLimit'] = TIME_LIMIT

data=DataPortal(model=model)
data.load(filename="data.dat")
instance = model.create_instance(data)
results = solver.solve(instance)

print(results)

gant_chart(instance)



