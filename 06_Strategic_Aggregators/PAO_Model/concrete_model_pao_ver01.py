# -*- coding: utf-8 -*-
"""
Created on Sun Jun 27 01:20:59 2021

@author: alire
"""

from pao.pyomo import *


from pyomo.environ import *
from pyomo.opt import SolverFactory



time=24

MVA = 1  # Power Base
PU_DA = 1/(1000*MVA)

 

"""
Defining Parameters
"""
NO_prosumers = len(IN_loads)

# defining the model
model = ConcreteModel(name='bilevel')

 # Horizon Set
model.T = RangeSet(16,time+15)

# Set of prosumers as customers for DA aggregator 
model.N = RangeSet(NO_prosumers)



"""
Upper Level problem variable
"""

# Energy bid as load from the grid
model.E_DA_L = Var(model.T, within=NonNegativeReals, initialize=0)

# Energy bid as inject into grid
model.E_DA_G = Var(model.T, within=NonNegativeReals, initialize=0)

# Energy bid demand by DA
model.DA_demand = Var(model.T,within=NonNegativeReals, initialize=0)

# Energy supply by DA
model.DA_supply = Var(model.T,within=NonNegativeReals, initialize=0)

# Binary control variable for demand and supply for DA
model.u_DA = Var(model.T,within=Binary, initialize=0)


# *******************************
#      EVs variables

# Energy when charging each EV
model.E_EV_CH = Var(model.N, model.T, within=NonNegativeReals, initialize=0)

# Energy from EV Discharge
model.E_EV_DIS = Var(model.N, model.T, within=NonNegativeReals, initialize=0)

# EVs battery State of 
model.SOC   = Var(model.N, model.T, within=NonNegativeReals, initialize=0)

# Binary control variable
model.u_EV   = Var(model.N, model.T, within=Binary, initialize=0)



# ***********************************
# Thermostatically appliances
model.POWER_TCL = Var(model.N, model.T, within=NonNegativeReals, initialize=0)

# Room temprature control variable
model.TCL_TEMP = Var(model.N, model.T, within=NonNegativeReals, initialize=0)


# ****************************************
#  Shiftable loads
model.POWER_SL = Var(model.N, model.T, within=NonNegativeReals, initialize=0)

# Binary control varible
model.u_SL     = Var(model.N, model.T, within=Binary, initialize=0)

# Dual price 
model.Lambda = Var(model.BUS, model.T, within=NonNegativeReals, initialize=0)


"""
Upper Level constraints
"""
#********************************************************
#                  EV Constraints
#********************************************************

# Constraint (a.2): Ensure that charging of EV don't exceed maximum value of EV_Power
def ev_charging_rule(model,i,t):
    if t >= arrival[i-1] and t < depart[i-1]:
        return model.E_EV_CH[i,t] <= model.u_EV[i,t] * charge_power[i-1]*delta_t
    else:
        return model.E_EV_CH[i,t]==0
        # return Constraint.Skip
model.ev_charging_con=Constraint(model.N, model.T, rule=ev_charging_rule)

# Constraint (a.3): Ensure that charging of EV don't exceed maximum value of EV_Power
def ev_discharging_rule(model,i,t):
    if t >= arrival[i-1] and t < depart[i-1]:
        return model.E_EV_DIS[i,t] <= (1-model.u_EV[i,t]) * charge_power[i-1]*delta_t
    else:
        return model.E_EV_DIS[i,t]==0
        # return Constraint.Skip
model.ev_discharging_con=Constraint(model.N, model.T, rule=ev_discharging_rule)

# Constraint (a.4): set the SOC 
def ev_soc_rule(model, i, t):
    if t >= arrival[i-1] and t < depart[i-1]: 
        return model.SOC[i,t+1] == model.SOC[i,t] + ch_rate*model.E_EV_CH[i,t] - model.E_EV_DIS[i,t]/ch_rate 
    else:
        return Constraint.Skip
model.ev_soc_con = Constraint(model.N, model.T, rule=ev_soc_rule)

# Constraint (a.4_1): Set the start soc to arrival soc
def EV_arrival_soc_rule(model, i):
    return model.SOC[i, arrival[i-1]]== EV_soc_arrive[i-1]
model.EV_arrival_soc_con = Constraint(model.N, rule= EV_arrival_soc_rule)

# Constraint (a.5_1): Limit the SOC, Lower Bound
def ev_soc_low_rule(model, i, t):
    if t >= arrival[i-1] and t < depart[i-1]: 
        return model.SOC[i,t] >=  EV_soc_low[i-1]
    else:
        return Constraint.Skip
model.ev_soc_low_con=Constraint(model.N, model.T, rule=ev_soc_low_rule)


# Constraint (a.5_2): Limit the SOC, Upper Bound
def ev_soc_low2_rule(model, i, t):
    if t >= arrival[i-1] and t < depart[i-1]: 
        return model.SOC[i,t] <=  EV_soc_up[i-1]
    else:
        return Constraint.Skip
model.ev_soc_low2_con=Constraint(model.N, model.T, rule=ev_soc_low2_rule)

# Constraint (a.6): Set the target SOC to be as desired(full charge) at departure time
def ev_traget_rule(model,i):
    return model.SOC[i,depart[i-1]] == EV_soc_up[i-1] #model.ev_demand[i]
model.ev_target_con = Constraint(model.N, rule=ev_traget_rule)

# Constraint (Custom_1): Set the binary variable to zero outside the [arrival, depart] boundary
def ev_binary_zero_rule(model,i,t):
    if t < arrival[i-1] or t >= depart[i-1]:
        return model.u_EV[i,t]==0
    else:
        return Constraint.Skip
model.ev_binary_zero_con = Constraint(model.N, model.T, rule=ev_binary_zero_rule)



#********************************************************
#                  TCL Constraints
#********************************************************

# Constraint (a.7): Limit TCL maximum load
def TCL_power_limit_rule(model,i,t):
    return model.POWER_TCL[i,t] <= TCL_Max[i-1] 
model.TCL_power_limit_con= Constraint(model.N, model.T, rule=TCL_power_limit_rule)

# Constraint (a.8): Set inside temprature for residence
def TCL_room_temp_rule(model,i,t):
    if t >= arrival[i-1] and t < depart[i-1]:                                                                 # model.TCL_occ[i,t]
        return model.TCL_TEMP[i,t+1]== TCL_Beta[i-1] * model.TCL_TEMP[i,t] + (1-TCL_Beta[i-1])*(outside_temp[t-16]+ TCL_R[i-1]*model.POWER_TCL[i,t])
    else:
        return model.POWER_TCL[i,t] == 0
        # return Constraint.Skip
model.TCL_room_temp_con= Constraint(model.N, model.T, rule=TCL_room_temp_rule)

# Constraint (a.9):
def TCL_low_preference_rule(model,i,t):
    if t >= arrival[i-1] and t < depart[i-1]:
        return model.TCL_TEMP[i,t] >= TCL_temp_low[i-1]
    else:
        return Constraint.Skip
model.TCL_low_preference_con = Constraint(model.N, model.T, rule=TCL_low_preference_rule)

# Constraint (a.9_1): Set the temperature of the room to the outside temp
def TCL_set_start_temp_rule(model, i):
        return model.TCL_TEMP[i,arrival[i-1]]== TCL_temp_low[i-1]# model.out_temp[model.arrival[i]]
model.TCL_set_start_temp_con= Constraint(model.N, rule=TCL_set_start_temp_rule)


#********************************************************
#             Shiftable load Constraints
#********************************************************

# Constraint (a.10): Electric power for shiftable loads SLs
def SL_power_load_rule(model, i, t):
    if t >= (SL_low[i-1]) and t < SL_up[i-1] :
        time = range(0,SL_cycle) # Cycle duration required to finish the assigned jop for SL 
        # time = range(16,SL_cycle + 16)
        return model.POWER_SL[i,t] ==  sum(SL_loads[w][i-1]* model.u_SL[i,t-w] for w in time if w+16<=t )
    else:
        return model.POWER_SL[i,t] == 0
        # return Constraint.Skip
model.SL_power_load_con = Constraint(model.N, model.T, rule=SL_power_load_rule)

# Constraint (a.11): The begining time for cycle
def SL_binary_rule(model,i):
    time = range(SL_low[i-1], SL_up[i-1])
    return sum(model.u_SL[i,t] for t in time) ==1
model.SL_binary_con = Constraint(model.N, rule=SL_binary_rule)

# Constraint (19_1): Zeros less than lower time to statrt
def SL_binary_zero_rule(model,i ,t):
    if t < SL_low[i-1]:
        return model.u_SL[i,t]==0
    elif t >= SL_up[i-1]:
        return model.u_SL[i,t]==0
    else:
        return Constraint.Skip
model.SL_binary_zero_con =Constraint(model.N, model.T, rule=SL_binary_zero_rule)



#********************************************************
#             DA Demand and Supply Constraints
#********************************************************

# Equality constraint (a.13) for power balance in strategic DA
def DA_power_balance_rule(model, t):
    return model.E_DA_L[t]-model.E_DA_G[t] == \
            sum(model.E_EV_CH[i,t]-model.E_EV_DIS[i,t]+ model.POWER_TCL[i,t]+ model.POWER_SL[i,t]+ IN_loads.loc[i-1,str(t)] for i in model.N) * PU_DA
model.DA_power_balance_con = Constraint(model.T, rule=DA_power_balance_rule)

# def DA_power_balance_rule(model, t):
#     return model.E_DA_L[t]-model.E_DA_G[t] == \
#             model.EV_PU[t] + model.TCL_PU[t]+ model.SL_PU[t]+ sum(IN_loads.loc[i-1,str(t)] for i in model.N)*PU_DA
# model.DA_power_balance_con = Constraint(model.T, rule=DA_power_balance_rule)


# DA demand will draw from grid (a.14)
def DA_demand_rule(model,t):
    return model.DA_demand[t] <= bigF*model.u_DA[t]
model.DA_demand_con = Constraint(model.T, rule= DA_demand_rule)

# DA supply to inject into grid (a.15)
def DA_supply_rule(model,t):
    return model.DA_supply[t] <= bigF*(1-model.u_DA[t])
model.DA_supply_con = Constraint(model.T, rule= DA_supply_rule)


"""
Lower level Constraints
"""


