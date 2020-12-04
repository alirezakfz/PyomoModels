# -*- coding: utf-8 -*-
"""
Created on Thu Dec  3 17:53:40 2020

@author: alire
"""

from pyomo.environ import *

def createModel(number_of_timeslot):
    
    bigM=100
    delay=0 #1
    prf=2 #round(0.2 * number_of_EVs)
    
    
    """
    Model Creation
    """
    model=AbstractModel(name="AbstractEv")
    
    model.N = Set()
    model.M = Set()
    model.T = Set()
    
    
    
    
    """
    Model Parmeters
    """
    model.arrival  = Param(model.N)
    
    model.TFC = Param(model.N, model.M)
    
    model.depart = Param(model.N)
    
    model.installed_cost = Param(model.M)
    
    
    """
    Model Decision Variables
    """
    
    model.x=Var(model.N,model.M,model.T,within=Binary, initialize=0)
    
    
    model.C=Var(model.N,within=NonNegativeIntegers, initialize=0)
    
    #Binary variable to select charger. If charger i selected then its 1 otherwise zero
    model.q = Var (model.M, within=Binary, initialize=0)
    
    #Variable to strore the delay from the schedule
    model.d = Var (model.N, within=NonNegativeIntegers, initialize=0)
        
    #Binary variable for limiting delay occurance in each charge station
    model.z   = Var (model.N, within=Binary, initialize=0)
    
    
    model.FirstStageCost = Var()
    model.SecondStageCost = Var()
    
    """
    Model Constraints
    """
    """
    Version 12 constraints
    """
    
        #each job can start only at exactly one particular time on exactly one machine.
    def one_job_rule(model,j):
        sumj=[]
        for i in model.M:
            time=range(model.arrival[j], number_of_timeslot - model.TFC[j,i]+1) #model.TFC[i,j]+2
            sumj.append(sum(model.x[j,i,t] for t in time))
        return sum(sumj)==1
    model.one_job_con=Constraint(model.N, rule=one_job_rule)
            
    #ensures that at any given time on each machine at
    #most one job can be processed.
    def machine_rule(model,i,t):
        sumj=[]
        for j in model.N:
            s=max(model.arrival[j],t-model.TFC[j,i]+1)  #model.TFC[i,j]+1
            if s>t :
                time=range(t,s+1) #s+1
            else:
                time=range(s,t+1) #t+1           
            sumj.append(sum(model.x[j,i,h] for h in time))
        return sum(sumj)<=1
    model.machine_con=Constraint(model.M,model.T,rule=machine_rule)
   
    
    #each job cannot be processed before it is released.
    # def release_rule(model,j):
    #     time=range(0,model.arrival[j])
    #     return sum(model.x[i,j,t] for i in model.M for t in time)==0
    # model.release_con=Constraint(model.N,rule=release_rule)
    
    def release_rule(model,j,m,t):
        if t < model.arrival[j]:
            return model.x[j,m,t]==0
        else:
            return Constraint.Skip
    model.release_con=Constraint(model.N, model.M, model.T, rule=release_rule)
    
    #the completion time of a job j can
    def span_rule(model,j):
        sumj=[]
        for i in model.M:
            time=range(0,number_of_timeslot-model.TFC[j,i]+1) #model.TFC[i,j]+2
            sumj.append(sum(model.x[j,i,t]*(t+model.TFC[j,i]) for t in time))
        return model.C[j]==sum(sumj)
    model.span_con=Constraint(model.N,rule=span_rule)
    
    def span_limit_rule(model,j):
        return model.C[j]<=len(model.T)
    model.span_limit_con=Constraint(model.N,rule=span_limit_rule)
    
    def cost_rule(model,i,j,t):
        # return model.q[i] <= sum(model.x[i,j,t] for j in model.ev for t in model.T)
        return   model.x[i,j,t] <= model.q[j]
    model.cost_con = Constraint(model.N, model.M, model.T, rule=cost_rule)
    
    def select_rule(model,i):
        return model.q[i]<=1
    model.select_con=Constraint(model.M, rule=select_rule)
    
    
    """
    version 8 constraints
    """
    def performance_rule(model):
        return sum(model.z[j] for j in model.N ) <= prf
    model.performance_con=Constraint(rule=performance_rule)
    
    def disjuctive1_rule(model,j):
#        p=sum(model.d[j] for j in model.N)
        # return model.C[j] - model.depart[j] + (1-model.z[j])*bigM >= 0
        return model.C[j] - model.depart[j] + (1-model.z[j])*bigM >= 0
    model.disjuctive1_con=Constraint(model.N, rule=disjuctive1_rule)
    
    def disjuctive2_rule(model,j):
#        p=sum(model.s[i,t]*t for t in model.T)
        # return bigM*model.z[j] - model.C[j] + model.depart[j] <= 0   #model.z[i,k]*bigM
        return model.C[j] - model.depart[j] - model.z[j] <= 0
    model.disjuctive2_con=Constraint(model.N, rule=disjuctive2_rule)
    
    """
    Version 15
    """
    def charge_rule(model,j):
        return sum(model.x[j,i,t] for i in model.M for t in model.T)==1
    model.charge_con= Constraint(model.N, rule=charge_rule)
    
    #Objective to minimize the cost for chrging evs
    
    
    #
    # Stage-specific cost computations
    #
    
    def first_stage_cost_rule(model):
        return (model.FirstStageCost - sum(model.q[i]* model.installed_cost[i] for i in model.M)) == 0.0     
    model.ComputeFirstStageCost = Constraint(rule=first_stage_cost_rule)
    
    
    def second_stage_cost_rule(model):
        return (model.SecondStageCost - sum(model.z[j] for j in model.N )) == 0.0     
    model.ComputeSecondStageCost = Constraint(rule=second_stage_cost_rule)
    
    
    #
    # Objective
    #
    def total_cost_rule(model):
        return (model.FirstStageCost + model.SecondStageCost)
    model.Total_Cost_Objective = Objective(rule=total_cost_rule, sense=minimize)
    
    # def total_cost_rule(model):
    #     return sum(model.q[i]* model.installed_cost[i] for i in model.M)
    # model.Total_Cost_Objective = Objective(rule=total_cost_rule, sense=minimize)
    
    return model
    
