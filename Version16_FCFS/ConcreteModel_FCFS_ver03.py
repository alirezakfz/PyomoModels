# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 19:42:59 2020

@author: Ali
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
                depart=list([18,19,18,19,20]), 
                TFC=[[1,1],[1,1],[1,1],[1,1],[1,1]],
                priority=[[1,1,1,1,1],[0,1,1,1,1],[0,0,1,1,1],[0,0,0,1,1],[0,0,0,0,1]]):
    
    
    bigM=10**10
    
    
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
    
 
    
    def TFC_rule(model,i,m):
        return int(TFC[i-1,m-1])
    model.TFC = Param(model.N, model.M, rule= TFC_rule )
    
    
    #EV deparure time
    def depart_init(model,j):
        return int(depart[j-1])
    model.depart=Param(model.N, initialize=depart_init, default=number_of_timeslot)
    
    # #EVs charfing priority:FCFS
    # def priority_init(model,i,j):
    #     return int(priority[i-1,j-1])
    # model.pr=Param(model.N, model.N, initialize=priority_init)
    
    """
    Model Decision Variables
    """
    
    model.x=Var(model.N,model.M,model.T,within=Binary,initialize=0)
    
    
    model.C=Var(model.N,within=NonNegativeIntegers,initialize=0)
    
    #Binary variable to select charger. If charger i selected then its 1 otherwise zero
    model.q = Var (model.M, within=Binary, initialize=0)
    
        
    #Binary variable to assign each EV to one charger
    # model.y = Var(model.N, model.M, within=Binary, initialize=0)
    
    
    
    """
    model objective
    """   
    model.obj=Objective(expr=sum(model.q[i]*installed_cost[i-1] for i in model.M), sense=minimize)
    
    
    """
    Model Constraints
    """
    """
    Version 12 constraints
    """
    #each job can start only at exactly one particular time on exactly one machine.
    def one_job_rule(model,j):
        sumj=[]
        for m in model.M:
            time=range(model.arrival[j], number_of_timeslot - model.TFC[j,m]+1) #model.TFC[i,j]+2
            sumj.append(sum(model.x[j,m,t] for t in time))
        return sum(sumj)==1
    model.one_job_con=Constraint(model.N, rule=one_job_rule)
    
    
    #ensures that at any given time on each machine at
    #most one job can be processed.
    def machine_rule(model,m,t):
        sumj=[]
        for j in model.N:
            s=max(model.arrival[j],t-model.TFC[j,m]+1)  #model.TFC[i,j]+1
            if s>t :
#                if s > number_of_timeslot:
#                    s=number_of_timeslot
                time=range(t,s+1) #s+1
            else:
#                if t> number_of_timeslot:
#                    t=number_of_timeslot
                time=range(s,t+1) #t+1           
            sumj.append(sum(model.x[j,m,h] for h in time))
        return sum(sumj)<=1
    #    return sum(model.x[i,j,t] for j in model.ev for t in model.T )<=1
    model.machine_con=Constraint(model.M,model.T,rule=machine_rule)
    
    
    #each job cannot be processed before it is released.
    # def release_rule(model,j):
    #     time=range(0,model.arrival[j])
    #     return sum(model.x[j,m,t] for m in model.M for t in time)==0
    # model.release_con=Constraint(model.N,rule=release_rule)
    
    #the completion time of a job j can
    def span_rule(model,j):
        sumj=[]
        for m in model.M:
            time=range(0,number_of_timeslot-model.TFC[j,m]+1) #model.TFC[i,j]+2
            sumj.append(sum(model.x[j,m,t]*(t+model.TFC[j,m]) for t in time))
        return model.C[j]==sum(sumj)
    model.span_con=Constraint(model.N,rule=span_rule)
    
    def span_limit_rule(model,j):
        # return model.C[j]<=len(model.T)
        return model.C[j] <= model.depart[j]
    model.span_limit_con=Constraint(model.N,rule=span_limit_rule)
    
    def cost_rule(model,j,m,t):
        # return model.q[i] <= sum(model.x[i,j,t] for j in model.ev for t in model.T)
        return  model.x[j,m,t] <= model.q[m]
        # return model.y[j,m]<=model.q[m]
    model.cost_con = Constraint(model.N, model.M, model.T, rule=cost_rule)
    
    
    
    """
    version FCFS_03 constraints
    """
    
    # def charger_rule(model,j,m,t):
    #     return model.x[j,m,t]<=model.y[j,m]
    # model.charger_con=Constraint(model.N, model.M, model.T, rule=charger_rule)
    
    # def install_rule(model,j):
    #     return sum(model.y[j,m] for m in model.M)==1
    # model.install_con=Constraint(model.N, rule=install_rule)
    
    """
    New idea
    """
    # def disjuctive1_rule(model,i,j,m):
    #     if i!=j and j > i and i<len(model.N):
    #         return model.C[j]-model.C[i]+bigM*(3-model.y[j,m]-model.y[i,m]-model.pr[i,j]) >= model.TFC[j,m]
    #     else:
    #         return Constraint.Skip
    # model.disjuctive1_con=Constraint(model.N,model.N,model.M, rule=disjuctive1_rule)
    
    
    # def disjuctive2_rule(model,i,j,m):
    #     if i!=j and j > i and i<len(model.N):
    #         return model.C[j] - model.C[i] + bigM*(2-model.y[j,m]-model.y[i,m]+model.pr[i,j]) >= model.TFC[j,m]
    #     else:
    #         return Constraint.Skip
    # model.disjuctive2_con=Constraint(model.N,model.N,model.M, rule=disjuctive2_rule)
    
    
    
    """
    new idea
    """
    # def disjuctive1_rule(model,i,j,m):
    #     if i!=j and j > i and i<len(model.N):
    #         t1=sum(model.x[i,m,t] for t in model.T)
    #         t2=sum(model.x[j,m,t] for t in model.T)
    #         return model.C[j] - model.C[i] + bigM*(1-t1)+ bigM*(1-t2) + bigM*(1-model.pr[i,j]) >= model.TFC[j,m]
    #     else:
    #         return Constraint.Skip
    # model.disjuctive1_con=Constraint(model.N,model.N,model.M, rule=disjuctive1_rule)
    
    # def disjuctive2_rule(model,i,j,m):
    #     if i!=j and j > i and i<len(model.N):
    #         t1=sum(model.x[i,m,t] for t in model.T)
    #         t2=sum(model.x[j,m,t] for t in model.T)
    #         return model.C[j] - model.C[i] + bigM*(1-t1)+ bigM*(1-t2) + bigM*(model.pr[i,j]) >= model.TFC[j,m]
    #     else:
    #         return Constraint.Skip
    # model.disjuctive2_con=Constraint(model.N,model.N,model.M, rule=disjuctive2_rule)
    
    """
    new idea
    """
    def priority_rule(model,i,j):
        if i!=j and j > i and i < len(model.N):
            # return sum(model.x[i,m,t]*t  for t in model.T) <= sum(model.x[j,m,t]*t  for t in model.T)
            return sum(model.x[i,m1,t]*t for m1 in model.M for t in model.T) <= sum(model.x[j,m2,t]*t for m2 in model.M for t in model.T)
        else:
            return Constraint.Skip
    model.priority_con=Constraint(model.N,model.N, rule=priority_rule)
    
    def one_charge_rule(model,i):
        return sum(model.x[i,m,t] for m in model.M for t in model.T)==1
    model.one_charge_con=Constraint(model.N, rule=one_charge_rule)
    
    def release_rule(model,j,m,t):
        if t < model.arrival[j]:
            return model.x[j,m,t]==0
        else:
            return Constraint.Skip
    model.release_con=Constraint(model.N, model.M, model.T, rule=release_rule)
    
    
    return model
    
    
    
    
    
    
    