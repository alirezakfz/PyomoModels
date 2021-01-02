# -*- coding: utf-8 -*-
"""
Created on Fri Aug 28 19:19:13 2020

@author: alire
"""

from numpy.random import randint
from numpy.random import seed
from pyomo.environ import *
import numpy as np
import math
#
#(number_of_EVs, number_of_Chargers, number_of_timeslot,
#                  installed_chargers, installed_cost, arrival,depart, TFC)
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
    prf=0 #round(0.2 * number_of_EVs)
    
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
    """
    Version 12 constraints
    """
    # def satisfy_rule(model,j):
    #     return sum(model.x[i,j,t] for i in model.M for t in model.T)==1
    # model.satisfy_con=Constraint(model.N, rule=satisfy_rule)
    
    
    #each job can start only at exactly one particular time on exactly one machine.
    def one_job_rule(model,j):
        sumj=[]
        for i in model.M:
            time=range(model.arrival[j], number_of_timeslot - model.TFC[i,j]+1) #model.TFC[i,j]+2
            sumj.append(sum(model.x[i,j,t] for t in time))
        return sum(sumj)==1
    model.one_job_con=Constraint(model.N, rule=one_job_rule)
            
    #ensures that at any given time on each machine at
    #most one job can be processed.
    def machine_rule(model,i,t):
        sumj=[]
        for j in model.N:
            s=max(model.arrival[j],t-model.TFC[i,j]+1)  #model.TFC[i,j]+1
            if s>t :
#                if s > number_of_timeslot:
#                    s=number_of_timeslot
                time=range(t,s+1) #s+1
            else:
#                if t> number_of_timeslot:
#                    t=number_of_timeslot
                time=range(s,t+1) #t+1           
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
            time=range(0,number_of_timeslot-model.TFC[i,j]+1) #model.TFC[i,j]+2
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
#     def performance_rule(model):
#         return sum(model.z[j] for j in model.N ) <= prf
#     model.performance_con=Constraint( rule=performance_rule)
    
#     def disjuctive1_rule(model,j):
# #        p=sum(model.d[j] for j in model.N)
#         return model.C[j] - model.depart[j] + (1-model.z[j])*bigM >= 0
#     model.disjuctive1_con=Constraint(model.N, rule=disjuctive1_rule)
    
#     def disjuctive2_rule(model,j):
# #        p=sum(model.s[i,t]*t for t in model.T)
#         return model.C[j] - model.depart[j] - delay- model.z[j] <= 0   #model.z[i,k]*bigM
#     model.disjuctive2_con=Constraint(model.N, rule=disjuctive2_rule)
    
    
    
    
    
    return model
    


    