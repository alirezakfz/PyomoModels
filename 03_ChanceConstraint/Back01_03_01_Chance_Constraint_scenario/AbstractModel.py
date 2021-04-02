# -*- coding: utf-8 -*-
"""
Created on Wed Jan  6 18:18:46 2021

@author: alire
"""

from pyomo.environ import *

def createModel(number_of_EVs, number_of_timeslot):
    
    electicity_price = [70,69.99,67.99,68.54,66.1,74.41,74.43,70,68.89,65.93,59.19,59.19,65.22,66.07,70.41,75.15,84.4,78.19,74.48,69.24,69.32,69.31,68.07,70.06]
    
    """
    Model Creation
    """
    model = AbstractModel()
    model.N = Set()
    model.M = Set()
    model.T = Set()
    
    bigM=2*number_of_timeslot
    delay=0
    prf=0#round(0.2 * number_of_EVs)
    w= 0.00001
    """
    Model Parameters
    """
    
    model.arrival  = Param(model.N)
    
    model.POWER = Param(model.N, model.M)
    
    model.depart=Param(model.N)    
    
    model.installed_chargers = Param (model.M)
    
    model.demand = Param(model.N)
    
    model.installed_cost = Param(model.M)
        
    """
    Model Decision Variables
    """
    #Binary variable to select charger. If charger i selected then its 1 otherwise zero
    model.q = Var (model.M, within=Binary, initialize=0)
    
    # Binary variable which is one if EV i assigned to charger j, otherwise zero
    model.y = Var(model.N, model.M, within=Binary, initialize=0)
    
    # Binary variable which is one if EV i reaches its demand at time t, otherwize zero
    model.c = Var(model.N, model.T, within=Binary, initialize=0)    
    
    #Variable to strore charging power of EV i at selected charger j in time t grater than arrival[i] 
    model.p = Var (model.N, model.M, model.T, within=NonNegativeReals,initialize=0)
    
    # Variable to store delay for each EV i
    model.z = Var (model.N, within=Binary, initialize=0)
    
       
    """
    model objective
    """
    #Objective to minimize the cost for chrging evs
    def objective_rule(model):
        sum1 = sum(model.q[i]*model.installed_cost[i] for i in model.M)
        sum2 = w*sum(sum(model.p[i,j,t] for i in model.N for j in model.M)*electicity_price[t-1] for t in model.T)
        return sum1+sum2
    model.obj = Objective( rule= objective_rule,  sense=minimize)               
    # model.obj=Objective(expr=sum(model.q[i]*model.installed_cost[i] for i in model.M) ,sense=minimize) #+\
                        # 0.1*sum(sum(model.p[i,j,t]*t for i in model.N for j in model.M) for t in model.T) , sense=minimize)
    
    
    """
    Model Constraints
    """
    # Constraint (2): Whether EV i assigned to charger j
    def charger_rule(model, i):
        return sum(model.y[i,j] for j in model.M) == 1
    model.charger_con = Constraint(model.N, rule=charger_rule)
    
    # Constraint (3): Just use installed chargers
    def charger_assign_rule(model, i, j):
        return model.y[i,j] <= model.q[j]
    model.charger_assign_con = Constraint(model.N, model.M, rule=charger_assign_rule)
    
    # Constraint (4): max power charge rule
    def max_power_rule(model, i, j, t):
        return model.p[i,j,t] <= model.y[i,j]*model.POWER[i,j]
    model.max_power_con = Constraint (model.N, model.M, model.T, rule=max_power_rule )
    
    # Constraint (5): Arrival limit rule for charging power
    def arrival_rule(model, i, j, t):
        if t < model.arrival[i]:
            return model.p[i,j,t]==0
        else:
            return Constraint.Skip
    model.arrival_con = Constraint(model.N, model.M, model.T, rule=arrival_rule)
    
    # Constraint (6): Concurrent charging
    def concurrent_charge_rule(model, j, t):
        return sum(model.p[i,j,t] for i in model.N) <= model.q[j]*model.installed_chargers[j]
    model.concurrent_charge_con = Constraint(model.M, model.T, rule=concurrent_charge_rule)
    
    # Constraint (7): Completion time rule
    def completion_rule(model, i, t):
        time=range(1,t) # t+1
        return sum(model.p[i,j,tt] for j in model.M for tt in time) >= model.c[i,t]*model.demand[i]
    model.completion_con = Constraint(model.N, model.T, rule=completion_rule)
    
    # Constraint(8): One time stop rule
    def stop_rule(model,i):
        return sum(model.c[i,t] for t in model.T) == 1
    model.stop_con= Constraint(model.N, rule=stop_rule)
    
    
        
    """
    version 8 constraints
    """
    def performance_rule(model,i):
        return sum(model.z[i] for i in model.N ) <= prf
    model.performance_con=Constraint(model.N, rule=performance_rule)
    
    def disjuctive1_rule(model,i):
        temp=sum(model.c[i,t]*t for t in model.T)
        return temp - model.depart[i] + (1-model.z[i])*bigM >= 0
    model.disjuctive1_con=Constraint(model.N, rule=disjuctive1_rule)
    
    def disjuctive2_rule(model,i):
        temp=sum(model.c[i,t]*t for t in model.T)
        return temp - model.depart[i] - delay*model.z[i] <= 0   #model.z[i,k]*bigM
    model.disjuctive2_con=Constraint(model.N, rule=disjuctive2_rule)
    
    
    return model
    
    
    
    
    
    
    