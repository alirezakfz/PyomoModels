# -*- coding: utf-8 -*-
"""
Created on Fri Nov 12 12:01:33 2021

@author: alire
"""

from pyomo.environ import *
from pyomo.opt import SolverFactory

def SFP_prob_model(E_demand, E_supply, 
                   no_strategies, demand_strategy, supply_strategy):
    
    
    # defining the model
    model = ConcreteModel(name='SFP_prob')
    
    # Horizon Set
    model.T = RangeSet(16,time+15)
    
    # Set of prosumers as customers for DA aggregator 
    model.N = RangeSet(NO_prosumers)
    
    """
    Probability for Smooth Fictitious play
    
    """
    model.S = RangeSet(no_strategies)
    model.da_o_p = Var(model.S, model.T,  within= NonNegativeReals, initialize=0)
    model.da_b_p = Var(model.S, model.T,  within= NonNegativeReals, initialize=0)
    
    def sum_DAs_offer_probability_rule(model, t):
        return sum(model.da_o_p[s,t] for s in model.S) == 1.0
    model.sum_DAs_offer_probability_con = Constraint(model.T, rule=sum_DAs_offer_probability_rule)
    
    def sum_DAs_bid_probability_rule(model, t):
        return sum(model.da_b_p[s,t] for s in model.S) == 1.0
    model.sum_DAs_bid_probability_con = Constraint(model.T, rule=sum_DAs_bid_probability_rule)
    
    def demand_probability_rule(model, t):
        return E_demand[t-16] == sum(model.da_b_p[s,t] * demand_strategy[t-16][s-1] for s in model.S)
    model.demand_probability_con = Constraint(model.T, rule=demand_probability_rule)
    
    def offer_probability_rule(model, t):
        return  E_supply[t-16] == sum(model.da_o_p[s,t] * supply_strategy[t-16][s-1] for s in model.S)
    model.offer_probability_con = Constraint(model.T, rule=offer_probability_rule)
    
    
    def social_welfare_optimization_rule(model):
        return 1
    model.obj = Objective(rule=social_welfare_optimization_rule, sense=minimize)