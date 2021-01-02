# -*- coding: utf-8 -*-
"""
Created on Fri Jan  1 23:35:29 2021

@author: alire
"""

from pyomo.environ import *



def createModel(number_of_EVs=5,
                number_of_Chargers=2,
                number_of_timeslot=24,
                installed_chargers=[11,20], 
                installed_cost=[11,20], 
                arrival=[3,5,6,8,9], 
                depart=[18,19,18,19,20], 
                TFC=[[1,1],[1,1],[1,1],[1,1],[1,1]],
                demand=[10,12,14,16,12],
                max_rate=[8,8,24,24,50]):


    """
    Model Creation
    """
    model=ConcreteModel()
    model.N=RangeSet(number_of_EVs)
    model.M=RangeSet(number_of_Chargers)
    model.T=RangeSet(0,number_of_timeslot)
    
    bigM=10
    delay=0 #1
    prf=0 #round(0.2 * number_of_EVs)
    
      
    #randomly choose arrival time between 1 to half of the Horizon
    def arrival_init(model,i):
        return  int(arrival[i-1])
    model.arrival  = Param(model.N, initialize=arrival_init)
    
 
    
    def POWER_init(model,i,j):
        return min(max_rate[i], installed_chargers[j])
    model.POWER = Param(model.N, model.M, rule= POWER_init )
    
    
    #EV deparure time
    def depart_init(model,j):
        return int(depart[i-1])
    model.depart=Param(model.M, initialize=depart_init, default=number_of_timeslot)
    
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
    
    # Variable to store completion time of the EV i charging
    model.x = Var (model.N, within=NonNegativeIntegers, initialize=0)
    
    
    """
    model objective
    """
    #Objective to minimize the cost for chrging evs
    model.obj=Objective(expr=sum(model.q[i]*installed_cost[i-1] for i in model.M), sense=minimize)
    
    
    """
    Model Constraints
    """
    # Constraint (2): Whether EV i assigned to charger j
    def charger_rule(model, i):
        return sum(model.q[i,j] for j in model.M) == 1
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
        return sum(model.p[i,j,t] for i in model.N) <= model.q[j]*installed_chargers[j-1]
    model.concurrent_charge_con = Constraint(model.M, model.T, rule=concurrent_charge_rule)
    
    # Constraint (7): Completion time rule
    def completion_rule(model, i, t):
        time=range(1,t+1)
        return sum(model.p[i,j,tt] for j in model.M for tt in time) >= model.c[i,t]*demand[i-1]
    model.completion_con = Constraint(model.N, model.T, rule=completion_rule)
    
    # Constraint(8): One time stop rule
    def stop_rule(model,i):
        return sum(model.c[i,t] for t in model.T) == 1
    model.stop_con= Constraint(model.N, rule=stop_rule)
    
    
        
    """
    version 8 constraints
    """
    def performance_rule(model):
        return sum(model.z[i] for i in model.N ) <= prf
    model.performance_con=Constraint( rule=performance_rule)
    
    def disjuctive1_rule(model,j):
#        p=sum(model.d[j] for j in model.N)
        return model.x[i] - model.depart[i] + (1-model.z[i])*bigM >= 0
    model.disjuctive1_con=Constraint(model.N, rule=disjuctive1_rule)
    
    def disjuctive2_rule(model,j):
#        p=sum(model.s[i,t]*t for t in model.T)
        return model.x[i] - model.depart[i] - delay*model.z[i] <= 0   #model.z[i,k]*bigM
    model.disjuctive2_con=Constraint(model.N, rule=disjuctive2_rule)
    
    
    return model
    
    
    
    
    
    
   
