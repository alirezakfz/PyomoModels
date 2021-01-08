# -*- coding: utf-8 -*-
"""
Created on Fri Jan  1 23:35:29 2021

@author: alireza

In this model binary variable X[i,j,t] is added for controling charges
The soc of EVs are also added to the model.

These additions increased solvation time more than expected.

Needs modification or finding better model
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
                charge_power=[8,8,24,24,50],
                soc=[0,1,2,3,0,2]):

    

    """
    Model Creation
    """
    model=ConcreteModel()
    model.N=RangeSet(number_of_EVs)
    model.M=RangeSet(number_of_Chargers)
    model.T=RangeSet(number_of_timeslot)
    # model.T=RangeSet(0,number_of_timeslot)
    
    bigM=10
    delay=0 #1
    prf=0 #round(0.2 * number_of_EVs)
    charge_rate = 0.93
      
    #randomly choose arrival time between 1 to half of the Horizon
    def arrival_init(model,i):
        return  int(arrival[i-1])
    model.arrival  = Param(model.N, initialize=arrival_init)
    
 
    
    def POWER_init(model,i,j):
        return charge_power[i-1,j-1]
    model.POWER = Param(model.N, model.M, rule= POWER_init )
    
    
    #EV deparure time
    def depart_init(model,i):
        return int(depart[i-1])
    model.depart=Param(model.N, initialize=depart_init, default=number_of_timeslot)
    
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
    model.p = Var (model.N, model.T, within=NonNegativeReals,initialize=0)
    
    # Variable to store delay for each EV i
    model.z = Var (model.N, within=Binary, initialize=0)
    
    # Variable to store completion time of the EV i charging
    model.x = Var (model.N, model.M, model.T, within=Binary, initialize=0)
    
    # State of the charge Variable
    model.soc = Var(model.N, model.T, within=NonNegativeReals,initialize=0)
    
    
    """
    model objective
    """
    #Objective to minimize the cost for chrging evs
    model.obj=Objective(expr=sum(model.q[i]*installed_cost[i-1] for i in model.M), sense=minimize)
    
    
    """
    Model Constraints
    """
    # # Constraint (2): Whether EV i assigned to charger j
    # def charger_rule(model, i):
    #     return sum(model.y[i,j] for j in model.M) == 1
    # model.charger_con = Constraint(model.N, rule=charger_rule)
    
    # Constraint (3): Just use installed chargers
    # def charger_assign_rule(model, i, j):
    #     return model.y[i,j] <= model.q[j]
    # model.charger_assign_con = Constraint(model.N, model.M, rule=charger_assign_rule)
    
    def charger_assign_rule(model, i, j, t):
        return model.x[i,j,t] <= model.q[j]
    model.charger_assign_con = Constraint(model.N, model.M, model.T, rule=charger_assign_rule)
    
    # Constraint (4): max power charge rule
    def max_power_rule(model, i, t):
        return model.p[i,t] <= sum(model.x[i,j,t]*model.POWER[i,j] for j in model.M)
    model.max_power_con = Constraint (model.N, model.T, rule=max_power_rule )
    
    # Constraint (5): Arrival limit rule for charging power
    def arrival_rule(model, i, j, t):
        if t < model.arrival[i]:
            return model.x[i,j,t]==0
        else:
            return Constraint.Skip
    model.arrival_con = Constraint(model.N, model.M, model.T, rule=arrival_rule)
    
    # # Constraint (6): Concurrent charging
    # def concurrent_charge_rule(model, j, t):
    #     return model.p[i,t] <= model.q[j]*installed_chargers[j-1]
    # model.concurrent_charge_con = Constraint(model.M, model.T, rule=concurrent_charge_rule)
    
    
    # Constraint (7): Completion time rule
    def completion_rule(model, i, t):
        if t>= model.arrival[i]:
            return model.soc[i,t] >= model.c[i,t]*demand[i-1]
        else:
            return Constraint.Skip
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
    
    """
    New Version 02
    """
    def one_charger_rule(model, i, j, t):
        return model.x[i,j,t] <= model.y[i,j]
    model.one_charger_con = Constraint(model.N, model.M, model.T, rule=one_charger_rule)
    
    def soc_set_rule(model,i):
        return model.soc[i,model.arrival[i]] == soc[i-1]
    model.soc_set_con = Constraint(model.N, rule=soc_set_rule)
    
    def soc_charge_rule(model,i,t):
        if  t < len(model.T) and t >= model.arrival[i]:
            return model.soc[i,t+1] == model.p[i,t]*charge_rate+model.soc[i,t]
        else:
            return Constraint.Skip
    model.soc_charge_con = Constraint(model.N, model.T, rule=soc_charge_rule)
    # def set_initialize_power(model,i)
   
    # At each time slot on each charger only one machine can charge it's battery
    def one_ev_rule(model,j,t):
        return sum(model.x[i,j,t] for i in model.N) <= 1
    model.one_ev_con = Constraint(model.M, model.T, rule=one_ev_rule)
    
    # Each ev can be assigned only to one charger type
    def charger_rule_2 (model, i,t):
        return sum(model.x[i,j,t] for j in model.M) <= 1
    model.charger_con_2 = Constraint(model.N, model.T, rule=charger_rule_2)
   
    return model
    
    
    
    
    
    
   
