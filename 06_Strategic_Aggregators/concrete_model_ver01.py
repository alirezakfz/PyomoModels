# -*- coding: utf-8 -*-
"""
Created on Wed Mar 17 20:30:53 2021

@author: alire
"""
import random
import pandas as pd
from samples_gen import generate_price, generate_temp

from pyomo.environ import *
from pyomo.opt import SolverFactory


#Setting the random seed
random.seed(20)

# Random amount of generation for time slots
def random_generation(n,min_g, max_g):
    temp=[]
    for i in range(0,n):
        temp.append(random.randint(min_g,max_g))
    return temp

# Random price 
def random_price(n,min_g, max_g):
    temp=[]
    for i in range(0,n):
        temp.append(random.randint(min_g,max_g))
    return temp

"""
Sets included in the power system model
"""
time=24

ref_angel=1

# Time Horizon
H = range(16,time+16)            

#Set of competing DAs participating in the day ahead energy market
DA = ['DA3','DA4']  

# Dictionary of competitor DAs participating in day ahead energy market
dic_DA ={'bus3':['DA3'],
         'bus4':['DA4']}

# Set of transmission network busses
N  = ['bus1','bus2','bus3','bus4','bus5','bus6']    

# Dictionary of generators participating in the day ahead energy market
dic_G  = {'bus1':['G1'],
          'bus2':['G2'], 
          'bus6':['G3','G4']}

dic_G_bus ={'G1':'bus1',
           'G2':'bus2',
           'G3':'bus6',
           'G4':'bus6'}

dic_DA_bus ={'DAS':'bus5',
             'DA3':'bus3',
             'DA4':'bus4'}

dic_line_bus = {1:'bus1',
                2:'bus2',
                3:'bus3',
                4:'bus4',
                5:'bus5',
                6:'bus6'}
              
# Set of generators participating in the day ahead energy market
G=['G1','G2','G3','G4']                           



#Set of transmission network lines
#L  = {1:[2,4], 2:[1,3,4], 3:[2,6], 4:[1,2,5], 5:[4,6], 6:[3,5]} 
L=[(1,2),(1,4),(2,3),(2,4),(3,6),(4,5),(5,6)]
nodes=[1,2,3,4,5,6]

"""
Defining Parameters
"""
bigM =100000
bigF = 100000

#Price bid of generator i in time t
c_g = { 'G1':random_price(time,12,20),
        'G2':random_price(time,20,30),
        'G3':random_price(time,50,70),
        'G4':random_price(time,100,110)}  
c_g['G1']=[12 for x in range(0,time)]
c_g['G2']=[20 for x in range(0,time)]
c_g['G3']=[50 for x in range(0,time)]
c_g['G4']=[100 for x in range(0,time)]


#Price bid for supplying power of competing DA  i in time t
c_d_o = {'DAS':random_price(time,12,20),
         'DA3':random_price(time,12,20),
         'DA4':random_price(time,12,20)}

# Price bid for buying power of competing DA  i in time t
c_d_b = {'DAS':random_price(time,12,110),
         'DA3':random_price(time,12,110),
         'DA4':random_price(time,12,110)}

# Price bid for supplying power of strategic DA in time t
c_DA_o = c_d_o['DAS'] # random_price(time)

# Price bid for buying power of strategic DA in time t
c_DA_b = c_d_b['DAS'] # random_price(time)

# Admittance of transmission line ij (connecting bus  i to bus j)
y = {(1,2):5.882352941,
     (1,4):3.875968992,
     (2,3):27.02702703,
     (2,4):5.076142132,
     (3,6):55.55555556,
     (4,5):27.027002703,
     (5,6):7.142857143,}

# Supply offer of generator i in time t
g_s = { 'G1':random_generation(time,70, 100),
        'G2':random_generation(time,50, 75),
        'G3':random_generation(time,1, 50),
        'G4':random_generation(time,1, 50)}


# Supply offer of competing DA i in time t
def random_offer(DA_list, time):
    pivot=0.10
    offer_dict=dict()
    bid_dict=dict()
    for competitor in DA_list:
        temp_offer=[]
        temp_bid=[]
        for t in range(0,time):
            if random.random() >= pivot:
                temp_offer.append(0)
                temp_bid.append(random.randint(5, 100)/1000)  # Mega Watt
            else:
                temp_bid.append(0)
                temp_offer.append(random.randint(2, 10)/1000) # Mega Watt
        offer_dict[competitor]=temp_offer
        bid_dict[competitor]=temp_bid
    
    return offer_dict, bid_dict

# Supply offer of competing DA i in time t
# Demand bid of competing DA i in time t
F_d_o , F_d_b = random_offer(DA, time)

# Capacity limit of transmission line ij (connecting bus  i to bus j)
T = {(1,2):150, (1,4):150, (2,3):150, (2,4):33, (3,6):150, (4,5):150, (5,6):150}



"""
Day ahead aggregator data for prosumers.
    Inflexible loads,
    Flexible loads, 
    Thermostatically loads,
    Electric Vehicles
"""

IN_loads = pd.read_csv('inflexible_profiles_scen_1.csv').round(3)
profiles = pd.read_csv('prosumers_profiles_scen_1.csv')

# EVs properties 
arrival = profiles['Arrival']
depart  = profiles['Depart']
charge_power = profiles['EV_Power']
EV_soc_low   = profiles['EV_soc_low']
EV_soc_up   = profiles['EV_soc_up']
EV_soc_arrive = profiles['EV_soc_arr']
EV_demand = profiles['EV_demand']

#Constant Values
delta_t= 1
ch_rate = 0.93



# Shiftable loads
SL_loads=[]
SL_loads.append(profiles['SL_loads1'])
SL_loads.append(profiles['SL_loads2'])
SL_low   = profiles['SL_low']
SL_up    = profiles['SL_up']
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
    
# Day Ahead price for NOV-15 2019
price=[70,69.99,67.99,68.54,66.1,74.41,74.43,70,68.89,65.93,59.19,59.19,65.22,66.07,70.41,75.15,84.4,78.19,74.48,69.24,69.32,69.31,68.07,70.06]



# defining the model
model = ConcreteModel(name='bilevel')

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
Strategic Aggregator
"""



"""
Lower Level Variables
    Binary variables
    Dual variables
"""
# Generators set
model.G = Set(initialize=G)

# Transmission network busses
model.bus = Set(initialize=N)

# Network Lines
model.lines = Set(initialize=L)

# DAs competitors
model.DA = Set(initialize=DA)

# Generators production power at time t
model.g = Var(model.G, model.T, within=NonNegativeIntegers, initialize=0)

# DAs competitor supply offer
model.d_o = Var(model.DA, model.T, within=NonNegativeIntegers, initialize=0)

# DAs competitor demand bid
model.d_b = Var(model.DA, model.T, within=NonNegativeIntegers, initialize=0)

# voltage phase angle
model.teta = Var(nodes, model.T, within=NonNegativeIntegers, initialize=0)

# Dual price 
model.Lambda = Var(model.bus, model.T, within=NonNegativeReals, initialize=0)

"""
Dual Variables
"""
# Generators dual variable lower 
model.w_g_low = Var(model.G, model.T, within=NonNegativeIntegers, initialize=0)
#Generators dual variable upper
model.w_g_up = Var(model.G, model.T, within=NonNegativeIntegers, initialize=0)

#Competetive aggregators supply offer dual
model.w_do_low = Var(model.DA, model.T, within=NonNegativeIntegers, initialize=0)
#Competetive aggregators supply offer dual
model.w_do_up = Var(model.DA, model.T, within=NonNegativeIntegers, initialize=0)

#Competetive aggregators demand bid dual
model.w_db_low = Var(model.DA, model.T, within=NonNegativeIntegers, initialize=0)
#Competetive aggregators demand bid dual
model.w_db_up = Var(model.DA, model.T, within=NonNegativeIntegers, initialize=0)

#Strategic aggregators supply offer dual
model.w_DAo_low = Var( model.T, within=NonNegativeIntegers, initialize=0)
#Strategic aggregators supply offer dual
model.w_DAo_up = Var( model.T, within=NonNegativeIntegers, initialize=0)

#Strategic aggregators demand bid dual
model.w_DAb_low = Var( model.T, within=NonNegativeIntegers, initialize=0)
#Strategic aggregators demand bid dual
model.w_DAb_up = Var( model.T, within=NonNegativeIntegers, initialize=0)

# Transmission line duals
# model.w_line_low = Var( model.lines, model.T, within=NonNegativeIntegers, initialize=0)
# model.w_line_up = Var( model.lines, model.T, within=NonNegativeIntegers, initialize=0)
model.w_line_low = Var( nodes, model.T, within=NonNegativeIntegers, initialize=0)
model.w_line_up = Var( nodes, model.T, within=NonNegativeIntegers, initialize=0)

"""
Binary Variables
"""
#Generators binary coontrol variables
model.u_g_low = Var(model.G, model.T, within= Binary, initialize=0)
model.u_g_up = Var(model.G, model.T, within= Binary, initialize=0)

#DA competitors supply offer binary coontrol variables
model.u_do_low = Var(model.DA, model.T, within= Binary, initialize=0)
model.u_do_up = Var(model.DA, model.T, within= Binary, initialize=0)

#DA competitors demand bids binary coontrol variables
model.u_db_low = Var(model.DA, model.T, within= Binary, initialize=0)
model.u_db_up = Var(model.DA, model.T, within= Binary, initialize=0)

#Strategic aggregator binary control variable
model.u_DAs_o_low = Var(model.T,  within= Binary, initialize=0)
model.u_DAs_o_up = Var(model.T,  within= Binary, initialize=0)

model.u_DAs_b_low = Var(model.T,  within= Binary, initialize=0)
model.u_DAs_b_up = Var(model.T,  within= Binary, initialize=0)

# Transmission line binary control variable
# model.u_line_low = Var(model.lines, model.T, within= Binary, initialize=0)
# model.u_line_up = Var(model.lines, model.T, within= Binary, initialize=0)
model.u_line_low = Var(nodes, model.T, within= Binary, initialize=0)
model.u_line_up = Var(nodes, model.T, within= Binary, initialize=0)
    
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
           sum(model.E_EV_CH[i,t]-model.E_EV_DIS[i,t]+ model.POWER_TCL[i,t]+ model.POWER_SL[i,t]+ IN_loads.loc[i-1,str(t)] for i in model.N)/1000
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
    pos = N.index(i)+1
    
    sum1=0
    if i in dic_G.keys():
        sum1=sum(-model.g[x,t] for x in dic_G[i])
        
    sum3=0
    sum2=0
    if i in dic_DA.keys():
        sum3 = sum(model.d_b[x,t] for x in dic_DA[i])
        sum2 = sum(-model.d_o[x,t] for x in dic_DA[i])
    
    return sum1 + sum2 - model.E_DA_G[t] + sum3 + model.E_DA_L[t] + sum(y[L]*(model.teta[L[0],t]-model.teta[L[1],t]) for L in model.lines if L[0]!=pos)==0
model.network_power_balance_con = Constraint(model.bus, model.T, rule=network_power_balance_rule)


# Constraint (C.1) generators dual price
def generator_dual_price_rule(model, i, t):
    bus=dic_G_bus[i]        
    return c_g[i][t-16]+model.Lambda[bus,t] - model.w_g_low[i,t]+model.w_g_up[i,t]==0
model.generator_dual_price_con=Constraint(model.G, model.T, rule=generator_dual_price_rule)

# Constrint (C.2) competitor suuply to grid offer
def competitor_offer_dual_rule(model, i, t):
    bus=dic_DA_bus[i]
    return c_d_o[i][t-16]-model.Lambda[bus,t] - model.w_do_low[i,t] + model.w_do_up[i,t] ==0 
model.competitor_offer_dual_con = Constraint(model.DA, model.T, rule=competitor_offer_dual_rule)

# Constraint (C.3) competitors demand bid
def competitor_demand_dual_rule(model, i, t):
    bus=dic_DA_bus[i]
    return -c_d_b[i][t-16] - model.Lambda[bus,t] - model.w_do_low[i,t] + model.w_do_up[i,t] == 0
model.competitor_demand_dual_con = Constraint(model.DA, model.T, rule=competitor_demand_dual_rule)

# Constraint (c.4) Strategic Aggregator supply into grid offer
def strategic_offer_dual_rule(model,t):
    bus=dic_DA_bus['DAS']
    return c_DA_o[t-16]-model.Lambda[bus,t]-model.w_DAo_low[t] + model.w_DAo_up[t] == 0
model.strategic_offer_dual_con= Constraint(model.T, rule=strategic_offer_dual_rule)

# Constraint (C.5) Strategic aggregator demand bid from grid
def strategic_demand_dual_rule(model, t):
    bus=dic_DA_bus['DAS']
    return -c_DA_b[t-16]-model.Lambda[bus,t]-model.w_DAb_low[t] + model.w_DAb_up[t] == 0
model.strategic_demand_dual_con = Constraint(model.T, rule=strategic_demand_dual_rule)

# Constraint (C.6) Transmission Line constraint
def transmission_line_dual_rule(model, i ,t):
    # line = N.index(i)+1
    bus = dic_line_bus[i]
    
    check=True
    for L in model.lines:
        if L[0]==i:
            check=False
    if check:
        return Constraint.Skip
    
    sum1= sum(y[L]*(model.Lambda[bus,t]-model.Lambda[dic_line_bus[L[1]],t]) for L in model.lines if L[1] != i and L[0]==i)
    
    sum2= sum(y[L]*(model.w_line_low[i,t]-model.w_line_up[L[1],t]) for L in model.lines if L[1]>i and L[0]==i)
    
    sum3= sum(y[L]*(model.w_line_low[i,t]-model.w_line_up[L[1],t]) for L in model.lines if L[1]<i and L[0]==i)
    
    return sum1-sum2+sum3==0
model.transmission_line_dual_con = Constraint(nodes, model.T, rule=transmission_line_dual_rule)
    

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
model.KKT_DAs_supply_offer_low_con = Constraint(model.DA, model.T, rule=KKT_DAs_supply_offer_low_rule)

# KKT Constraint(D.6)
def KKT_DAs_supply_offer_low_2_rule(model, i ,t):
    return model.w_do_low[i,t] <= (1-model.u_do_low[i,t]) * bigM
model.KKT_DAs_supply_offer_low_2_con = Constraint(model.DA, model.T, rule=KKT_DAs_supply_offer_low_2_rule)

# KKT Constraint (D.7)
def KKT_DAs_supply_offer_up_rule (model, i, t):
    return F_d_o[i][t-16] - model.d_o[i,t] <= model.u_do_up[i,t] * bigM
model.KKT_DAs_supply_offer_up_con = Constraint(model.DA, model.T, rule=KKT_DAs_supply_offer_up_rule )

# KKT Constraint (D.8)
def KKT_DAs_supply_offer_up_2_rule(model, i, t):
    return model.w_do_up[i,t] <= (1-model.u_do_up[i,t]) * bigM
model.KKT_DAs_supply_offer_up_2_con = Constraint(model.DA, model.T, rule=KKT_DAs_supply_offer_up_2_rule)

#KKT Constraint (D.9)
def KKT_DAs_demand_bid_low_rule(model, i, t):
    return model.d_b[i,t] <= model.u_db_low[i,t] * bigM
model.KKT_DAs_demand_bid_low_con = Constraint(model.DA, model.T, rule=KKT_DAs_demand_bid_low_rule)

# KKT Constraint (D.10)
def KKT_DAs_demand_bid_low_2_rule (model, i, t):
    return model.w_db_low[i,t] <= (1-model.u_db_low[i,t]) * bigM
model.KKT_DAs_demand_bid_low_2_con = Constraint(model.DA, model.T, rule=KKT_DAs_demand_bid_low_2_rule)

#KKT Constraint (D.11)
def KKT_DAs_demand_bid_up_rule (model, i, t):
    return F_d_b[i][t-16] - model.d_b[i,t] <= model.u_db_up[i,t] * bigM
model.KKT_DAs_demand_bid_up_con = Constraint(model.DA, model.T, rule=KKT_DAs_demand_bid_up_rule)

# KKT Constraint (D.12)
def KKT_DAs_demand_bid_up_2_rule (model, i , t):
    return model.w_db_up[i,t] <= (1-model.u_db_up[i,t]) * bigM
model.KKT_DAs_demand_bid_up_2_con = Constraint(model.DA, model.T, rule=KKT_DAs_demand_bid_up_2_rule)

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
def KKT_transmission_low_rule (model, i, j, t):
    p=(i,j)
    if i < j and p in T.keys():        
        return y[p] * (model.teta[i,t] - model.teta[j,t]) + T[p] <= model.u_line_low[i,t] * bigM
    else:
        return Constraint.Skip
model.KKT_transmission_low_con = Constraint (nodes, nodes, model.T, rule=KKT_transmission_low_rule)

# KKT Transmission line Constraint (D.22)
def KKT_transmission_low_2_rule (model, i, j, t):
    p=(i,j)
    if i < j and p in T.keys():
        return model.w_line_low[i,t] <= model.u_line_low[i,t] * bigM
    else:
        return Constraint.Skip
model.KKT_transmission_low_2_con = Constraint(nodes, nodes, model.T, rule=KKT_transmission_low_2_rule)

# KKT Transmission line Constraint (D.23)
def KKT_transmission_up_rule(model, i, j, t):
    p=(i,j)
    if i < j and p in T.keys():
        return T[p] - (model.teta[i,t] - model.teta[j,t])*y[p] <= model.u_line_up[i,t] * bigM
    else:
        return Constraint.Skip
model.KKT_transmission_up_con = Constraint(nodes, nodes, model.T, rule=KKT_transmission_up_rule)

# KKT Transmission line Constraint (D.24)
def KKT_transmission_up_2_rule(model, i, j, t):
    p=(i,j)
    if i < j and p in T.keys():
        return model.w_line_up[i,t] <= (1-model.u_line_up[i,t]) * bigM
    else:
        return Constraint.Skip
model.KKT_transmission_up_2_con = Constraint(nodes, nodes, model.T, rule=KKT_transmission_up_2_rule)


## ***************************************
# Custome refrense angel set
def set_ref_angel_rule(model, t):
    return model.teta[ref_angel,t]==0
model.set_ref_angel_con = Constraint(model.T, rule=set_ref_angel_rule)



"""
Objective Functioon
"""

def social_welfare_optimization_rule(model):
    return sum(sum(c_g[i][t-16]*model.g[i,t] for i in model.G) +\
                sum(c_d_o[i][t-16]*model.d_o[i,t] for i in model.DA ) +\
                    sum(c_d_b[i][t-16]*model.d_b[i,t] for i in model.DA) +\
                        sum(model.w_g_up[i,t] * model.g[i,t] for i in model.G) +\
                            sum(model.w_do_up[i,t]* model.d_o[i,t] for i in model.DA) +\
                                sum(model.w_db_up[i,t]*model.d_b[i,t] for i in model.DA) +\
                                    sum(T[i]*model.w_line_low[i[0],t] for i in model.lines if i[0]<i[1]) +\
                                        sum(T[i]*model.w_line_up[i[0],t] for i in model.lines if i[0] <i[1]) for t in model.T )
model.obj = Objective(rule=social_welfare_optimization_rule, sense=minimize)




"""
Solve the model
"""



SOLVER_NAME="gurobi"  #'gurobi'

# SOLVER_NAME="cplex"

solver=SolverFactory(SOLVER_NAME)
results = solver.solve(model)
        