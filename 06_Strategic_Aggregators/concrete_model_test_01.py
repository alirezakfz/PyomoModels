# -*- coding: utf-8 -*-
"""
Created on Tue Mar 30 16:12:41 2021

@author: alire
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Mar 26 12:51:33 2021

@author: alire
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Mar 23 18:00:22 2021

@author: alire

"""
"""
% 6-Bus Network from EPSR paper
% Line No. | From Bus | To Bus | Susceptance (p.u.) | Capacity (MW)
%    1     |     1    |    2   |       100       |     50
%    1     |     3    |    4   |       125       |     50
%    2     |     3    |    3   |       150       |     50


% Generation Unit | Bus No | Capacity MW |  Production Cost ($/MWh)
%         1       |    1   |    20       |        16
%         2       |    2   |    10       |        19
%         3       |    6   |    25       |        25


%  Competing DA | Bus No. 
%       1       |    3    
%       2       |    4    
"""

import random
import pandas as pd
import numpy as np
import collections
from samples_gen import generate_price, generate_temp

from pyomo.environ import *
from pyomo.opt import SolverFactory


#Setting the random seed
random.seed(1000)




"""
Sets included in the power system model
"""
time=24
ref_angel=1

# Day Ahead price for NOV-15 2019
price=[70,69.99,67.99,68.54,66.1,74.41,74.43,70,68.89,65.93,59.19,59.19,65.22,66.07,70.41,75.15,84.4,78.19,74.48,69.24,69.32,69.31,68.07,70.06]


# Time Horizon
H = range(16,time+16)    
MVA = 1  # Power Base

nl = 3    # Number of network lines
nb = 3    # Number of network buses

FromBus = [1,1,2] # Vector with network lines' "sending buses"
ToBus = [2,3,3]   # Vector with network lines' "receiving buses"

LinesSusc = [100,125,150]  #Vector with per unit susceptance of the network 

ng = 3    # Number of Generators
ncda = 2  # Number of competing 

GenBus = [1,1,3]  # Vector with Generation Buses
CDABus = [2, 3]      # Vector with competing DAs Buses
DABus = 1           # DA Bus

FMAX = [50, 50, 50] # Vector with Capacities of Network Lines in pu
FMAX = [i/MVA for i in FMAX]

# Matrix (nb x ng) indicating the network location of generators
GenLoc = np.zeros((nb,ng))
for gg in range(0, ng):
    GenLoc[GenBus[gg]-1,gg] = 1

# Matrix (nb x ncda) indicating the network location of competing DAs
CDALoc = np.zeros((nb,ncda))
for dd in range(0,ncda):
    CDALoc[CDABus[dd]-1,dd] = 1
    
#Vector (nb x 1) indicating the network location of the DA
DALoc = np.zeros((nb,1))
DALoc[DABus-1] = 1


#1) Bus Admittance Matrix Construction
B = np.zeros((nb,nb)) # Initialize Bus Admittance Matrix as an all-zero nxn matrix
for kk in range (0,nl):
    # Off Diagonal elements of Bus Admittance Matrix
    B[FromBus[kk]-1,ToBus[kk]-1] = -LinesSusc[kk];
    B[ToBus[kk]-1,FromBus[kk]-1] =  B[FromBus[kk]-1,ToBus[kk]-1]


# Diagonal Elements of B Matrix
for ii in range(0,nb):
    B[ii,ii] = -sum(B[ii,x] for x in range(nb))

# LineFlows Matrix indicates the starting and ending nodes of each line
LineFlows = np.zeros((nl,nb))
for kk in range(0,nl):
    LineFlows[kk,FromBus[kk]-1] = 1
    LineFlows[kk,ToBus[kk]-1] = -1
    
Yline = (LineFlows.conj().transpose()*LinesSusc).conj().transpose()


# RAndom Supply and bid offer of competing DA i in time t
def random_offer(NO_CDA, time):
    pivot=0.10
    offer_dict=dict()
    bid_dict=dict()
    for competitor in range(1,NO_CDA+1):
        temp_offer=[]
        temp_bid=[]
        for t in range(0,time):
            if random.random() >= pivot:
                temp_offer.append(0)
                temp_bid.append(round(random.random()/MVA, 3))  # Mega Watt
            else:
                temp_bid.append(0)
                temp_offer.append(round(random.random()/MVA,3)) # Mega Watt
        offer_dict[competitor]=temp_offer
        bid_dict[competitor]=temp_bid
    
    return offer_dict, bid_dict

# Supply offer of competing DA i in time t
# Demand bid of competing DA i in time t
F_d_o , F_d_b = random_offer(ncda, time)

"Dictionary to speed up search"
dic_G_Bus=dict() # Dictionary of generators participating in the day ahead energy market
dic_G = collections.defaultdict(list)  # Dictionary of Bus Generators
for i in range(len(GenBus)):
    dic_G_Bus[i+1]=GenBus[i]
    dic_G[GenBus[i]].append(i+1)

dic_CDA_Bus=dict()
dic_Bus_CDA = dict()
for i in range(len(CDABus)):
    dic_CDA_Bus[i+1]=CDABus[i]
    dic_Bus_CDA[CDABus[i]] = i+1

dic_CDA_Bus['DAS']=DABus     # Strategic Aggregator
dic_Bus_CDA[DABus] = 'DAS'   # Strategic Aggregator


"""
Supply and demand Random
"""
# Random amount of generation for time slots
def random_generation(n,min_g, max_g):
    temp=[]
    for i in range(0,n):
        temp.append(random.randint(min_g,max_g)/MVA)
    return temp

# Random price 
def random_price(n,min_g, max_g):
    temp=[]
    for i in range(0,n):
        temp.append(random.randint(min_g,max_g))
    return temp


#Price bid of generator i in time t
c_g = { 1:random_price(time,12,20),
        2:random_price(time,20,30),
        3:random_price(time,50,70),
        4:random_price(time,100,110)}  
c_g[1]=[16 for x in range(0,time)]
c_g[2]=[19 for x in range(0,time)]
c_g[3]=[25 for x in range(0,time)]
c_g[4]=[100 for x in range(0,time)]


#Price bid for supplying power of competing DA  i in time t
c_d_o = {'DAS':random_price(time,12,20),
         1:random_price(time,12,20),
         2:random_price(time,12,20)}

# c_d_o = {'DAS':random_price(time,1,2),
#           1:random_price(time,1,2),
#           2:random_price(time,1,2)}

# Price bid for buying power of competing DA  i in time t
c_d_b = {'DAS':random_price(time,70,110),
         1:random_price(time,70,110),
         2:random_price(time,70,110)}

# c_d_b = {'DAS':random_price(time,1,2),
#           1:random_price(time,1,2),
#           2:random_price(time,1,2)}


# Price bid for supplying power of strategic DA in time t
c_DA_o = c_d_o['DAS'] # random_price(time)

# Price bid for buying power of strategic DA in time t
c_DA_b = c_d_b['DAS'] # random_price(time)

# Supply offer of generator i in time t
g_s = { 1:random_generation(time,10, 12),
        2:random_generation(time,5, 10),
        3:random_generation(time,15, 20),
        4:random_generation(time,1, 50)}



"""
Day ahead aggregator data for prosumers.
    Inflexible loads,
    Flexible loads, 
    Thermostatically loads,
    Electric Vehicles
"""

IN_loads = pd.read_csv('inflexible_profiles_scen_1.csv').round(3)/1000
# Throw away / Remove rows JUST FOR TEST
IN_loads.drop(index=[x for x in range(10,len(IN_loads))], inplace=True)

profiles = pd.read_csv('prosumers_profiles_scen_1.csv')
profiles.drop(index=[x for x in range(10,len(profiles))], inplace=True)

# EVs properties 
profiles['Arrival']=16
arrival = profiles['Arrival']

profiles['Depart']=time+15
depart  = profiles['Depart']


charge_power = profiles['EV_Power']
EV_soc_low   = profiles['EV_soc_low']
EV_soc_up   = profiles['EV_soc_up']
EV_soc_arrive = profiles['EV_soc_arr']
EV_demand = profiles['EV_demand']

#Constant Values
delta_t= 1
ch_rate = 0.95 # 0.93



# Shiftable loads
SL_loads=[]
SL_loads.append(profiles['SL_loads1'])
SL_loads.append(profiles['SL_loads2'])
SL_low   = profiles['SL_low']
# Make low to time 1
SL_low   = [16 for x in SL_low]

SL_up    = profiles['SL_up']
SL_up = [time+15 for x in SL_up]

SL_cycle = len(SL_loads)

# Thermostatically loads
TCL_R   = profiles['TCL_R']
TCL_C   = profiles['TCL_C']
TCL_COP = profiles['TCL_COP']
TCL_Max = profiles['TCL_MAX']
TCL_Beta= profiles['TCL_Beta']
TCL_temp_low = profiles['TCL_temp_low']
TCL_temp_up  = profiles['TCL_temp_up']

# 2019 November 15 forecasted temprature
outside_temp=[16.784803,16.094803,15.764802,14.774801,14.834802,14.184802,14.144801,15.314801,16.694803,19.734802,24.414803,25.384802,26.744802,27.144802,27.524803,27.694803,26.834803,26.594803,25.664803,22.594803,21.394802,20.164803,19.584803,20.334803]
    



# defining the model
model = ConcreteModel(name='bilevel')

"""
Defining Parameters
"""
bigM =100000
bigF = 100000
NO_prosumers = len(IN_loads)

"""
Upper level Variables
"""
# Horizon Set
model.T = RangeSet(16,time+15)

# Set of prosumers as customers for DA aggregator 
model.N = RangeSet(NO_prosumers)


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



"""
Lower Level Sets &Parameters
    Plus
Lower Level Variables
    Binary variables
    Dual variables
"""
# Generators set
model.G = RangeSet(ng)

# Transmission network busses
model.BUS = RangeSet(nb)

# Network Lines
model.LINES = RangeSet(nl)

# DAs competitors
model.NCDA = RangeSet(ncda)


# Generators production power at time t
model.g = Var(model.G, model.T, within=NonNegativeReals, initialize=0)

# DAs competitor supply offer
model.d_o = Var(model.NCDA, model.T, within=NonNegativeReals, initialize=0)

# DAs competitor demand bid
model.d_b = Var(model.NCDA, model.T, within=NonNegativeReals, initialize=0)

# voltage phase angle
model.teta = Var(model.BUS, model.T, within=NonNegativeReals, initialize=0)

# Dual price 
model.Lambda = Var(model.BUS, model.T, within=NonNegativeReals, initialize=0)

"""
Dual Variables
"""
# Generators dual variable lower 
model.w_g_low = Var(model.G, model.T, within=NonNegativeReals, initialize=0)
#Generators dual variable upper
model.w_g_up = Var(model.G, model.T, within=NonNegativeReals, initialize=0)

#Competetive aggregators supply offer dual
model.w_do_low = Var(model.NCDA, model.T, within=NonNegativeReals, initialize=0)
#Competetive aggregators supply offer dual
model.w_do_up = Var(model.NCDA, model.T, within=NonNegativeReals, initialize=0)

#Competetive aggregators demand bid dual
model.w_db_low = Var(model.NCDA, model.T, within=NonNegativeReals, initialize=0)
#Competetive aggregators demand bid dual
model.w_db_up = Var(model.NCDA, model.T, within=NonNegativeReals, initialize=0)

#Strategic aggregators supply offer dual
model.w_DAo_low = Var( model.T, within=NonNegativeReals, initialize=0)
#Strategic aggregators supply offer dual
model.w_DAo_up = Var( model.T, within=NonNegativeReals, initialize=0)

#Strategic aggregators demand bid dual
model.w_DAb_low = Var( model.T, within=NonNegativeReals, initialize=0)
#Strategic aggregators demand bid dual
model.w_DAb_up = Var( model.T, within=NonNegativeReals, initialize=0)

# Transmission line duals
# model.w_line_low = Var( model.lines, model.T, within=NonNegativeReals, initialize=0)
# model.w_line_up = Var( model.lines, model.T, within=NonNegativeReals, initialize=0)
model.w_line_low = Var( model.LINES, model.T, within=NonNegativeReals, initialize=0)
model.w_line_up = Var( model.LINES, model.T, within=NonNegativeReals, initialize=0)

"""
Binary Variables
"""
#Generators binary coontrol variables
model.u_g_low = Var(model.G, model.T, within= Binary, initialize=0)
model.u_g_up = Var(model.G, model.T, within= Binary, initialize=0)

#DA competitors supply offer binary coontrol variables
model.u_do_low = Var(model.NCDA, model.T, within= Binary, initialize=0)
model.u_do_up = Var(model.NCDA, model.T, within= Binary, initialize=0)

#DA competitors demand bids binary coontrol variables
model.u_db_low = Var(model.NCDA, model.T, within= Binary, initialize=0)
model.u_db_up = Var(model.NCDA, model.T, within= Binary, initialize=0)

#Strategic aggregator binary control variable
model.u_DAs_o_low = Var(model.T,  within= Binary, initialize=0)
model.u_DAs_o_up = Var(model.T,  within= Binary, initialize=0)

model.u_DAs_b_low = Var(model.T,  within= Binary, initialize=0)
model.u_DAs_b_up = Var(model.T,  within= Binary, initialize=0)

# Transmission line binary control variable
# model.u_line_low = Var(model.lines, model.T, within= Binary, initialize=0)
# model.u_line_up = Var(model.lines, model.T, within= Binary, initialize=0)
model.u_line_low = Var(model.LINES, model.T, within= Binary, initialize=0)
model.u_line_up = Var(model.LINES, model.T, within= Binary, initialize=0)

"""
Upper Level constraints
"""
#********************************************************
#                  EV Constraints
#********************************************************

# Constraint (a.2): Ensure that charging of EV don't exceed maximum value of EV_Power
def ev_charging_rule(model,i,t):
    if t >= arrival[i-1] and t < depart[i-1]:
        return model.E_EV_CH[i,t] <= model.u_EV[i,t] * charge_power[i-1] #*delta_t
    else:
        return model.E_EV_CH[i,t]==0
        # return Constraint.Skip
model.ev_charging_con=Constraint(model.N, model.T, rule=ev_charging_rule)

# Constraint (a.3): Ensure that charging of EV don't exceed maximum value of EV_Power
def ev_discharging_rule(model,i,t):
    if t >= arrival[i-1] and t < depart[i-1]:
        return model.E_EV_DIS[i,t] <= (1-model.u_EV[i,t]) * charge_power[i-1] #*delta_t
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

# # Constraint (Custom_1): Set the binary variable to zero outside the [arrival, depart] boundary
# def ev_binary_zero_rule(model,i,t):
#     if t < arrival[i-1] or t >= depart[i-1]:
#         return model.u_EV[i,t]==0
#     else:
#         return Constraint.Skip
# model.ev_binary_zero_con = Constraint(model.N, model.T, rule=ev_binary_zero_rule)



#********************************************************
#                  TCL Constraints
#********************************************************

# Constraint (a.7): Limit TCL maximum load
def TCL_power_limit_rule(model,i,t):
    return model.POWER_TCL[i,t] <= TCL_Max[i-1] 
model.TCL_power_limit_con= Constraint(model.N, model.T, rule=TCL_power_limit_rule)

# Constraint (a.8): Set inside temprature for residence
def TCL_room_temp_rule(model,i,t):
    if t >= arrival[i-1] and t < depart[i-1]:                                                                   # model.TCL_occ[i,t]
        return model.TCL_TEMP[i,t+1]== TCL_Beta[i-1] * model.TCL_TEMP[i,t] + (1-TCL_Beta[i-1])*(outside_temp[t-1-16]+ TCL_R[i-1]*model.POWER_TCL[i,t])
    else:
        return Constraint.Skip
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
    if t >= SL_low[i-1] and t < SL_up[i-1] :
        time = range(0,SL_cycle) # Cycle duration required to finish the assigned jop for SL appliance
        return model.POWER_SL[i,t] ==  sum(SL_loads[w][i-1]* model.u_SL[i,t-w] for w in time if w+16<=t )
    else:
        return Constraint.Skip
model.SL_power_load_con = Constraint(model.N, model.T, rule=SL_power_load_rule)

# Constraint (a.11): The begining time for cycle
def SL_binary_rule(model,i):
    time = range(SL_low[i-1], SL_up[i-1])
    return sum(model.u_SL[i,t] for t in time) ==1
model.SL_binary_con = Constraint(model.N, rule=SL_binary_rule)


#********************************************************
#             DA Demand and Supply Constraints
#********************************************************

# Equality constraint (a.13) for power balance in strategic DA
def DA_power_balance_rule(model, t):
    return model.E_DA_L[t]-model.E_DA_G[t] == \
           sum(model.E_EV_CH[i,t]-model.E_EV_DIS[i,t]+ model.POWER_TCL[i,t]+ model.POWER_SL[i,t]+ IN_loads.loc[i-1,str(t)] for i in model.N)/(1000*MVA)
model.DA_power_balance_con = Constraint(model.T, rule=DA_power_balance_rule)


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

# Constraint (b.2), power balance at each bus i of the power grid, that must hold at every timeslot t. 
def network_power_balance_rule(model, i, t):
    sum1=0
    if i in dic_G.keys():
        sum1=sum(-model.g[x,t] for x in dic_G[i])
    
    sum3=0
    sum2=0
    if i in dic_Bus_CDA.keys() :
        if i == DABus:
            sum2= -model.E_DA_G[t]
            sum3= model.E_DA_L[t]
        else:
            x=dic_Bus_CDA[i]
            sum3 = model.d_b[x,t]   # if x != 'DAs'
            sum2 = -model.d_o[x,t] 
    
    sumB = sum(B[i-1,j-1]*model.teta[j,t] for j in model.BUS)
    
    return sum1+sum2+sum3+sumB == 0
model.network_power_balance_con = Constraint(model.BUS, model.T, rule=network_power_balance_rule)    


# Constraint (b.8), Line Flow Bounds (b.8)
def line_flow_lower_bound_rule(model, i, t):
    return sum(-Yline[i-1,j-1]*model.teta[j,t] for j in model.BUS) <= FMAX[i-1]
model.line_flow_lower_bound_con = Constraint(model.LINES, model.T, rule=line_flow_lower_bound_rule)

# Constraint (b.8.2) line Flows Bounds, Upper bound
def line_flow_upper_bound_rule(model, i, t):
    return sum(Yline[i-1,j-1]*model.teta[j,t] for j in model.BUS) <= FMAX[i-1]
model.line_flow_upper_bound_con = Constraint(model.LINES, model.T, rule=line_flow_upper_bound_rule)

# Constraint (C.1) generators dual price
def generator_dual_price_rule(model, i, t):
    bus=dic_G_Bus[i]        
    return c_g[i][t-16]-model.Lambda[bus,t] - model.w_g_low[i,t]+model.w_g_up[i,t]==0
model.generator_dual_price_con=Constraint(model.G, model.T, rule=generator_dual_price_rule)


#**********************************************
#             Feasibility problem

# Constrint (C.2) competitor suuply to grid offer
def competitor_offer_dual_rule(model, i, t):
    bus=dic_CDA_Bus[i]
    return c_d_o[i][t-16]-model.Lambda[bus,t] - model.w_do_low[i,t] + model.w_do_up[i,t] ==0  #c_d_o[i][t-16]
model.competitor_offer_dual_con = Constraint(model.NCDA, model.T, rule=competitor_offer_dual_rule)

# Constraint (C.3) competitors demand bid
def competitor_demand_dual_rule(model, i, t):
    bus=dic_CDA_Bus[i]
    return  -c_d_b[i][t-16] + model.Lambda[bus,t] - model.w_db_low[i,t] + model.w_db_up[i,t] == 0 # -c_d_b[i][t-16]
model.competitor_demand_dual_con = Constraint(model.NCDA, model.T, rule=competitor_demand_dual_rule)

#////////////////////////////////////////////
#********************************************


# Constraint (c.4) Strategic Aggregator supply into grid offer
def strategic_offer_dual_rule(model,t):
    bus=dic_CDA_Bus['DAS']
    return c_DA_o[t-16]-model.Lambda[bus,t]-model.w_DAo_low[t] + model.w_DAo_up[t] == 0
model.strategic_offer_dual_con= Constraint(model.T, rule=strategic_offer_dual_rule)

# Constraint (C.5) Strategic aggregator demand bid from grid
def strategic_demand_dual_rule(model, t):
    bus=dic_CDA_Bus['DAS']
    return -c_DA_b[t-16]+model.Lambda[bus,t]-model.w_DAb_low[t] + model.w_DAb_up[t] == 0
model.strategic_demand_dual_con = Constraint(model.T, rule=strategic_demand_dual_rule)

# Constraint (C.6) Transmission Line constraint
def transmission_line_dual_rule(model, i ,t):
    B_T=B.transpose()
    # sum1= sum(B_T[i-1,j-1]*(model.Lambda[i,t]-model.Lambda[j,t]) for j in model.BUS if i != j)
    sum1= sum(B_T[i-1,j-1]*model.Lambda[j,t] for j in model.BUS)
    
    Yline_T = Yline.transpose()
    sum2= sum(Yline_T[i-1,j-1]*model.w_line_low[j,t] for j in model.LINES)
    
    sum3= sum(Yline_T[i-1, j-1]*model.w_line_up[j,t] for j in model.LINES)
    
    return sum1-sum2+sum3==0
model.transmission_line_dual_con = Constraint(model.BUS, model.T, rule=transmission_line_dual_rule)


"""
Karush-Kuhn-Tucker conditions
"""
# KKT constraint (D.1)
def KKT_gen_low_rule(model, i, t):
    return model.g[i,t]<= model.u_g_low[i,t] * bigM
model.KKT_gen_low_con = Constraint(model.G, model.T, rule=KKT_gen_low_rule)

#KKT Constrainr (D.2)
def KKT_gen_low_2_rule(model, i, t):
    return model.w_g_low[i,t] <= (1-model.u_g_low[i,t]) * bigM
model.KKT_gen_low_2_con = Constraint(model.G, model.T, rule=KKT_gen_low_2_rule)

#KKT Constraint (D.3)
def KKT_gen_up_rule (model, i, t):
    return  g_s[i][t-16] - model.g[i,t] <= model.u_g_up[i,t]*bigM
model.KKT_gen_up_rule = Constraint (model.G, model.T, rule= KKT_gen_up_rule)

# KKT Constraint (D.4)
def KKT_gen_up_2_rule (model, i, t):
    return model.w_g_up[i,t] <= (1-model.u_g_up[i,t]) * bigM
model.KKT_gen_up_2_con = Constraint(model.G, model.T, rule=KKT_gen_up_2_rule)

# KKT Constraint (D.5)
def KKT_DAs_supply_offer_low_rule (model, i, t):
    return model.d_o[i,t] <= model.u_do_low[i,t] * bigM
model.KKT_DAs_supply_offer_low_con = Constraint(model.NCDA, model.T, rule=KKT_DAs_supply_offer_low_rule)

# KKT Constraint(D.6)
def KKT_DAs_supply_offer_low_2_rule(model, i ,t):
    return model.w_do_low[i,t] <= (1-model.u_do_low[i,t]) * bigM
model.KKT_DAs_supply_offer_low_2_con = Constraint(model.NCDA, model.T, rule=KKT_DAs_supply_offer_low_2_rule)

# KKT Constraint (D.7)
def KKT_DAs_supply_offer_up_rule (model, i, t):
    return F_d_o[i][t-16] - model.d_o[i,t] <= model.u_do_up[i,t] * bigM
model.KKT_DAs_supply_offer_up_con = Constraint(model.NCDA, model.T, rule=KKT_DAs_supply_offer_up_rule )

# KKT Constraint (D.8)
def KKT_DAs_supply_offer_up_2_rule(model, i, t):
    return model.w_do_up[i,t] <= (1-model.u_do_up[i,t]) * bigM
model.KKT_DAs_supply_offer_up_2_con = Constraint(model.NCDA, model.T, rule=KKT_DAs_supply_offer_up_2_rule)

#KKT Constraint (D.9)
def KKT_DAs_demand_bid_low_rule(model, i, t):
    return model.d_b[i,t] <= model.u_db_low[i,t] * bigM
model.KKT_DAs_demand_bid_low_con = Constraint(model.NCDA, model.T, rule=KKT_DAs_demand_bid_low_rule)

# KKT Constraint (D.10)
def KKT_DAs_demand_bid_low_2_rule (model, i, t):
    return model.w_db_low[i,t] <= (1-model.u_db_low[i,t]) * bigM
model.KKT_DAs_demand_bid_low_2_con = Constraint(model.NCDA, model.T, rule=KKT_DAs_demand_bid_low_2_rule)


#KKT Constraint (D.11)
def KKT_DAs_demand_bid_up_rule (model, i, t):
    return F_d_b[i][t-16] - model.d_b[i,t] <= model.u_db_up[i,t] * bigM
model.KKT_DAs_demand_bid_up_con = Constraint(model.NCDA, model.T, rule=KKT_DAs_demand_bid_up_rule)

# KKT Constraint (D.12)
def KKT_DAs_demand_bid_up_2_rule (model, i , t):
    return model.w_db_up[i,t] <= (1-model.u_db_up[i,t]) * bigM
model.KKT_DAs_demand_bid_up_2_con = Constraint(model.NCDA, model.T, rule=KKT_DAs_demand_bid_up_2_rule)


# KKT Constraint (D.13)
def KKT_strategic_DA_bid_low_rule (model, t):
    return model.E_DA_G[t] <= model.u_DAs_o_low[t] * bigM
model.KKT_strategic_DA_bid_low_con = Constraint(model.T, rule=KKT_strategic_DA_bid_low_rule)

#KKT Constraint (D.14)
def KKT_strategic_DA_bid_low_2_rule (model, t):
    return model.w_DAo_low[t] <= (1-model.u_DAs_o_low[t]) * bigM
model.KKT_strategic_DA_bid_low_2_con = Constraint(model.T, rule=KKT_strategic_DA_bid_low_2_rule)

# KKT Constraint (D.15)
def KKT_stKrategic_DA_bid_up_rule (model,t):
    return model.DA_supply[t] - model.E_DA_G[t] <= model.u_DAs_o_up[t] * bigM
model.KKT_stKrategic_DA_bid_up_con = Constraint (model.T, rule=KKT_stKrategic_DA_bid_up_rule)

# KKT Constraint (D.16)
def KKT_strategic_DA_bid_up_2_rule (model,t):
    return model.w_DAo_up[t] <=  (1-model.u_DAs_o_up[t]) * bigM
model.KKT_strategic_DA_bid_up_2_con = Constraint(model.T, rule=KKT_strategic_DA_bid_up_2_rule)

# KKT Constraint (D.17)
def KKT_strategic_demand_low_rule (model, t):
    return model.E_DA_L[t] <= model.u_DAs_b_low[t] * bigM
model.KKT_strategic_demand_low_con = Constraint(model.T, rule=KKT_strategic_demand_low_rule)

# KKT Constraint (D.18)
def KKT_strategic_demand_low_2_rule (model, t):
    return model.w_DAb_low[t] <=(1-model.u_DAs_b_low[t]) * bigM
model.KKT_strategic_demand_low_2_con = Constraint(model.T, rule=KKT_strategic_demand_low_2_rule)

# KKT Constraint (D.19)
def KKT_strategic_demand_up_rule (model,t):
    return model.DA_demand[t] - model.E_DA_L[t] <= model.u_DAs_b_up[t] * bigM
model.KKT_strategic_demand_up_con = Constraint(model.T, rule=KKT_strategic_demand_up_rule)

# KKT Constraint (D.20)
def KKT_strategiv_demand_up_2_rule (model,t):
    return model.w_DAb_up[t] <=  (1-model.u_DAs_b_up[t]) * bigM
model.KKT_strategiv_demand_up_2_con =Constraint(model.T, rule=KKT_strategiv_demand_up_2_rule)


# KKT Transmission line Constraint (D.21)
def KKT_transmission_low_rule (model, i, t):
    return sum(Yline[i-1, j-1]*model.teta[j,t] for j in model.BUS ) + FMAX[i-1] <=   model.u_line_low[i,t] * bigM
model.KKT_transmission_low_con = Constraint (model.LINES, model.T, rule=KKT_transmission_low_rule)

# KKT Transmission line Constraint (D.22)
def KKT_transmission_low_2_rule (model, i, t):
    return model.w_line_low[i,t] <= (1-model.u_line_low[i,t]) * bigM
model.KKT_transmission_low_2_con = Constraint(model.LINES, model.T, rule=KKT_transmission_low_2_rule)

# KKT Transmission line Constraint (D.23)
def KKT_transmission_up_rule(model, i, t):
   return sum(-Yline[i-1,j-1]* model.teta[j,t] for j in model.BUS) + FMAX[i-1] <= model.u_line_up[i,t] * bigM
model.KKT_transmission_up_con = Constraint(model.LINES, model.T, rule=KKT_transmission_up_rule)

# KKT Transmission line Constraint (D.24)
def KKT_transmission_up_2_rule(model, i, t):
   return model.w_line_up[i,t] <= (1-model.u_line_up[i,t]) * bigM
model.KKT_transmission_up_2_con = Constraint(model.LINES, model.T, rule=KKT_transmission_up_2_rule)


## ***************************************
#  refrense angel set
def set_ref_angel_rule(model, t):
    return model.teta[ref_angel,t]==0
model.set_ref_angel_con = Constraint(model.T, rule=set_ref_angel_rule)

"""
Objective Functioon
"""

# def social_welfare_optimization_rule(model):
#     return sum(sum(c_g[i][t-16]*model.g[i,t] for i in model.G) +\
#                 sum(c_d_o[i][t-16]*model.d_o[i,t] for i in model.NCDA ) +\
#                     sum(c_d_b[i][t-16]*model.d_b[i,t] for i in model.NCDA) +\
#                         sum(FMAX[i-1]*model.w_line_low[i,t] for i in model.LINES) +\
#                                         sum(FMAX[i-1]*model.w_line_up[i,t] for i in model.LINES) for t in model.T )
# model.obj = Objective(rule=social_welfare_optimization_rule, sense=minimize)


def social_welfare_optimization_rule(model):
    return sum(sum(c_g[i][t-16]*model.g[i,t] for i in model.G) +\
                sum(c_d_o[i][t-16]*model.d_o[i,t] for i in model.NCDA ) +\
                    sum(c_d_b[i][t-16]*model.d_b[i,t] for i in model.NCDA) +\
                        sum(model.w_g_up[i,t] * g_s[i][t-16] for i in model.G) +\
                            sum(model.w_do_up[i,t]* F_d_o[i][t-16] for i in model.NCDA) +\
                                sum(model.w_db_up[i,t]*F_d_b[i][t-16] for i in model.NCDA) +\
                                    sum(FMAX[i-1]*model.w_line_low[i,t] for i in model.LINES) +\
                                        sum(FMAX[i-1]*model.w_line_up[i,t] for i in model.LINES) for t in model.T )
model.obj = Objective(rule=social_welfare_optimization_rule, sense=minimize)


"""
Solve the model
"""
# with open('DA_Bilevel.txt', 'w') as f:
#     f.write("Description of the Bilevel model for strategic day ahead aggregator:\n")
#     model.display(ostream=f)

SOLVER_NAME="gurobi"  #'cplex'

solver=SolverFactory(SOLVER_NAME)

# results = solver.solve(model, keepfiles=True, tee=True,  logfile = "name.csv")

results = solver.solve(model)
print(results)



OBJ=[]
for t in model.T:
    temp=sum(c_g[i][t-16]*value(model.g[i,t]) for i in model.G) +\
                sum(c_d_o[i][t-16]*value(model.d_o[i,t]) for i in model.NCDA ) +\
                    sum(c_d_b[i][t-16]*value(model.d_b[i,t]) for i in model.NCDA) +\
                        sum(value(model.w_g_up[i,t]) * value(model.g[i,t]) for i in model.G) +\
                            sum(value(model.w_do_up[i,t])* value(model.d_o[i,t]) for i in model.NCDA) +\
                                sum(value(model.w_db_up[i,t])*value(model.d_b[i,t]) for i in model.NCDA) +\
                                    sum(FMAX[i-1]*value(model.w_line_low[i,t]) for i in model.LINES) +\
                                        sum(FMAX[i-1]*value(model.w_line_up[i,t]) for i in model.LINES)
    OBJ.append(temp)
    
print(OBJ)



# with open('DA_Bilevel.txt', 'w') as f:
#     f.write("Description of the Bilevel model for strategic day ahead aggregator:\n")
#     model.display(ostream=f)