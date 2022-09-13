# -*- coding: utf-8 -*-
"""
Created on Tue Dec 15 15:31:44 2020

@author: alire
"""

from pyomo.environ import *


"""
Model Creation for bidding optimization 
in day ahead market
"""
#Constant Values
delta_t= 0.25
ch_rate = 0.93



model=AbstractModel()

model.T = Set()   # set for time horizon: 1,2,...,192 for 48 hours and delta_t is 15 minutes
model.N = Set()   # Set for number of prosumers 
model.M = Set()   # Set for Type of loads {EV, TCL, INL, SL}

"""
Model Parameters
"""

model.arrival = Param(model.N)  # Arrival time of EVs
model.depart  = Param(model.N)  # Depart time of EVs
model.soc_low = Param(model.N)  # Lower Bound for the state of the charge for each EV
model.soc_up  = Param(model.N)  # Upper Bound for the state of the charge for each EV
model.ev_max_power = Param(model.N) # maximum power to bound each EV charging and discharging at one hour
model.ev_demand    = Param(model.N)

#Parameters for expected imbalace cost between DA and RT
model.L_DA_NEG = Param(model.T) # Negative imbalance price {shortage of generation [I_GEN] <0} or { surplus of demand [I_DEM]> 0} / Second stage price
model.L_DA_POS = Param(model.T) # Positive imbalance price  {surplus of Generation [I_GEN] >0} or {shortage of demand [I_DEM] <0} / second stage price

#Bounding supply/demand bids to prosumers contract for load and generation
model.E_DA_low = Param(model.T) # Lower bound for Supply or Demand bids
model.E_DA_up  = Param(model.T) # Upper bound for Supply or Demand bids

model.L_DA     = Param(model.T)  # Day Ahead Energy price (First stage price)

model.INL      = Param(model.N, model.T) # Inflexible loads for each consumer at each time slot

model.loads    = Param(model.N)


# Parameters for Thermostatic load TCL
model.TCL_Max_P = Param(model.N)
model.out_temp  = Param(model.T) # Outside tempratuer
model.TCL_cop   = Param(model.N) # Coefficient of Performance COP
model.TCL_R     = Param(model.N) # Thermal Resistance
model.TCL_C     = Param(model.N) # capacitance
model.temp_low  = Param(model.N) # Temperature predefined by prosumers, Lower Bound
model.temp_up   = Param(model.N) # Temperature predefined by prosumers, Upper Bound
model.TCL_occ   = Param(model.N, model.T)      #Prosumers Occupancy Dwelling
model.TCL_beta  = Param(model.N)               # Room temp controller


# Parameters for shiftable load
model.SL_cycle   = Param(model.N)          # Length of cycle duration for using 
model.SL_profile = Param(model.N, model.T) # Usage profile of device during occupation
model.SL_low     = Param(model.N)          # Lower bound for starting using SL to do the job
model.SL_up     = Param(model.N)           # Upper bound for finishing cycle of the SL



"""
For two stage optimization
"""
model.FirstStageCost = Var()
model.SecondStageCost = Var()



"""
Model Variables
"""

#*******  Optimization General variables
model.E_DA  = Var(model.T, within=Reals, initialize=0)  # Demand and supply bids / First stage part
model.E_RT  = Var(model.T, within=Relas, initalize=0)   # Real time energy from all the loads and generation



# ********* Bound required
model.I_NEG = Var(model.T, within=NonNegativeReals, initialize=0)  # Negative load imbalance {shortage of generation [I_GEN_NEG] <0} or { surplus of demand [I_DEM]> 0}

model.I_POS = Var(model.T, within=NonNegativeReals, initialize=0)  # Positive load imbalance {surplus of Generation [I_GEN] >0} or {shortage of demand [I_DEM] <0}


#****** Electric Vehicle charging and discharging
model.E_EV_CH  = Var(model.N, model.T, within=NonNegativeReals, initialize=0 )        # Chargign energy of the EV as load demand
model.E_EV_DIS = Var(model.N, model.T, within=NonNegativeReals, initialize=0 )        # Discharging energy of the EV as generation
model.SOC      = Var(model.N, model.T, within=NonNegativeReals, initialize=0)   # EVs state of charge at each time step
model.X        = Var(model.N, model.T, within=Binary, initialize=0)             # Binary variable to decide of charging or discharging
model.POWER_EV = Var(model.N, model.T, within=Relas,  initialize=0)             # Electric Power (KW) of the EV


#****** Thermostatic load TCL Variables
model.POWER_TCL   = Var(model.N, model.T, within=NonNegativeReals, initialize=0 ) # Electric Power (KW) of the TCL
model.TCL_temp    = Var(model.N, model.T, within=Relas,  initialize=0)            # Room Temprature


#*****************************************************
#************ Shiftable Loads Varibles
model.POWER_SL   = Var(model.N, model.T, within=NonNegativeReals, initialize=0) # Power load used by SL device during it's usage
model.Y          = Var(model.N, model.T, within=Binary, initialize=0)           # Binary variable to decide of starting the usage of device


"""
Optimization Objective
"""

#
# Stage-specific cost computations
#

def first_stage_cost_rule(model):
    return (model.FirstStageCost - sum(model.L_DA[t]* model.E_DA[t] for t in model.T)) == 0.0     
model.ComputeFirstStageCost = Constraint(rule=first_stage_cost_rule)


def second_stage_cost_rule(model):
    return (model.SecondStageCost - sum(model.L_DA_NEG[t]*model.I_NEG[t] - model.L_DA_POS[t]*model.I_POS[t] for t in model.T )) == 0.0     
model.ComputeSecondStageCost = Constraint(rule=second_stage_cost_rule)

#
# Objective 
#
def total_cost_rule(model):
    return (model.FirstStageCost + model.SecondStageCost)
model.Total_Cost_Objective = Objective(rule=total_cost_rule, sense=minimize)


"""
Model Constraints
"""

# constarint 6: Defining energy imbalances
def en_imbalance_rule(model,t):
    return model.I_NEG[t] - model.I_POS[t] == model.E_RT[t] - model.E_DA[t]
model.imbalace_constraint=Constraint(model.T, rule=en_imbalance_rule)


# Constraint 7: Set limits for energy bids
def limit_en_bids_low_rule(model,t):
    return model.E_DA[t] <= model.E_DA_low
model.limit_en_bids_low_con=Constraint(model.T, rule=limit_en_bids_low_rule)

def limit_en_bids_up_rule(model,t):
    return model.E_DA[t] >= -model.E_DA_up
model.limit_en_bids_up_con=Constraint(model.T, rule=limit_en_bids_up_rule)


# Constraint (8): Set imbalance limits
def imbalance_pos_limit_rule(model,t):
    return model.I_POS[t] <= max(model.E_DA_low, model.E_DA_up)
model.imbalance_pos_limit_con=Constraint(model.T, imbalance_pos_limit_rule)

def imbalance_NEG_limit_rule(model,t):
    return model.I_NEG[t] <= max(model.E_DA_low, model.E_DA_up)
model.imbalance_NEG_limit_con=Constraint(model.T, imbalance_NEG_limit_rule)


# Constraint (9): Summing all the loads and generation from {EV,TCL,SL,INL}




#********************************************************************************
#************* Electric Vehicle Constraints

# Constraint (10): Ensure that charging of EV don't exceed maximum value of EV_Power
def ev_charging_rule(model,i,t):
    return model.E_EV_CH[i,t] <= model.X[i,t] * model.ev_max_power[i]*delta_t
model.ev_charging_con=Constraint(model.N, model.T, rule=ev_charging_rule)

# Constraint (11): Ensure that charging of EV don't exceed maximum value of EV_Power
def ev_discharging_rule(model,i,t):
    return model.E_EV_DIS[i,t] <= (1-model.X[i,t]) * model.ev_max_power[i]*delta_t
model.ev_discharging_con=Constraint(model.N, model.T, rule =ev_discharging_rule)

# Constraint (12): set the SOC 
def ev_soc_rule(model, i, t):
    if t < len(model.T): 
        return model.SOC[i,t+1] == model.SOC[i,t] + ch_rate*model.E_EV_CH[i,t] - model.E_EV_DIS[i,t]/ch_rate 
    else:
        return Constraint.Skip
model.ev_soc_con = Constraint(model.N, model.T, rule=ev_soc_rule)

# Constraint (13_1): Limit the SOC, Lower Bound
def ev_soc_low_rule(model, i, t):
    if t < len(model.T): 
        return model.SOC[i,t+1] >=  model.soc_low[i]
    else:
        return Constraint.Skip
model.ev_soc_low_con=Constraint(model.N, model.T, rule=ev_soc_low_rule)

# Constraint (13_2): Limit the SOC, Upper Bound
def ev_soc_low_rule(model, i, t):
    if t < len(model.T): 
        return model.SOC[i,t+1] <=  model.soc_up[i]
    else:
        return Constraint.Skip
model.ev_soc_low_con=Constraint(model.N, model.T, rule=ev_soc_low_rule)

# Constraint (13_3): EV power during time slot t {Net power of EV}
def ev_power_rule(model, i, t):
    return model.EV_Power[i,t] == (model.E_EV_CH[i,t]-model.E_EV_DIS[i,t])/delta_t
model.ev_power_con=Constraint(model.N, model.T, rule=ev_power_rule)

# Constraint (14): Set the target SOC at departure time
def ev_traget_rule(model,i):
    return model.SOC[i,model.depart[i]] == model.ev_demand[i]
model.ev_target_con = Constraint(model.N, rule=ev_traget_rule)


#********************************************************************************
#************* Thermostetically Constraint

# Constraint (15): Limit TCL maximum load
def TCL_power_limit_rule(model,i,t):
    return model.POWER_TCL[i,t] <= model.TCL_Max_P[i] 
model.TCL_power_limit_con= Constraint(model.N, model.T, rule=TCL_power_limit_rule)

# Constraint (16): Set inside temprature for residence
def TCL_room_temp_rule(model,i,t):
    if model.TCL_occ[i,t]==1 and t < len(model.T):
        return model.TCL_temp[i,t+1]== model.TCL_beta[i] * model.TCL_temp[i,t] + (1-model.TCL_beta[i])*(model.out_temp[t]+ model.TCL_cop[i]*model.TCL_R[i]*model.POWER_TCL[i,t])
    else:
        return Constraint.Skip
model.TCL_room_temp_con= Constraint(model.N, model.T, rule=TCL_room_temp_rule)


# Constraint (17_1): Guarantee the preferences of the prosumers, when the room or house id occupied
def TCL_up_preference_rule(model,i,t):
    if model.TCL_occ[i,t]==1 and t < len(model.T):
        return model.TCL_temp[i,t+1] <= model.temp_up[i]
    else:
        return Constraint.Skip
model.TCL_up_preference_con = Constraint(model.N, model.T, rule=TCL_up_preference_rule)

# Constraint (17_2):
def TCL_low_preference_rule(model,i,t):
    if model.TCL_occ[i,t]==1 and t < len(model.T):
        return model.TCL_temp[i,t+1] >= model.temp_low[i]
    else:
        return Constraint.Skip
model.TCL_low_preference_con = Constraint(model.N, model.T, rule=TCL_low_preference_rule)

 
#*********************************************************************************
#**************  Shiftable load constraint

# Constraint (18): Electric power for shiftable loads SLs
def SL_power_load_rule(model, i, t):
    if t >= model.SL_low[i] and t< model.SL_up[i]:
        time = range(1,model.SL_cycle+1) # Cycle duration required to finish the assigned jop for SL appliance
        return model.POWER_SL[i,t] ==  sum(model.SL_profile[i,w]* model.Y[i,t-w+1] for w in time)
    else:
        return Constraint.Skip

# Constraint (19): The begining time for cycle
def SL_binary_rule(model,i):
    time = range(model.SL_low, model.SL_up)
    return sum(model.Y[i,t] for t in time) ==1
model.SL_binary_con = Constraint(model.N, rule=SL_binary_rule)

# Constraint (19_1): Zeros less than lower time to statrt
def SL_binary_zero_rule(model,i ,t):
    if t < model.SL_low:
        return model.Y[i,t]==0
    elif t >= model.SL_up:
        return model.Y[i,t]==0
    else:
        return Constraint.Skip
model.SL_binary_zero_con =Constraint(model.N, model.T, rule=SL_binary_zero_rule)

