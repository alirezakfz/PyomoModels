# -*- coding: utf-8 -*-
"""
Created on Mon May 31 16:17:08 2021

@author: Alireza
"""


import random
import pandas as pd
import numpy as np
import collections
# from samples_gen import generate_price, generate_temp
from Model_to_CSV import model_to_csv

from pyomo.environ import *
from pyomo.opt import SolverFactory


def mpec_model(ng, nb, nl, ncda, IN_loads, gen_capacity,
               arrival, depart, charge_power,EV_soc_arrive,EV_soc_low, EV_soc_up, 
               TCL_Max, TCL_R, TCL_Beta, TCL_temp_low, outside_temp, 
               SL_low, SL_up, SL_cycle, SL_loads,
               dic_G, dic_Bus_CDA, DABus, B, Yline, dic_G_Bus, 
               c_g, c_d_o, c_d_b, 
               dic_CDA_Bus, g_s, F_d_o, F_d_b, FMAX,
               c_DA_o, c_DA_b,solar_power,
               EVs_list, Solar_list):
    
    
    time=24
    ref_angel=1
    
    delta_t =1
    ch_rate = 0.94
    
    
    MVA = 30  # Power Base
    PU_DA = 1/(1000*MVA)
    load_multiply = 1
    

    """
    Defining Parameters
    """
    bigM =1000.0
    bigF = 1000.0
    NO_prosumers = len(IN_loads)
    
    
    contract = [100000 for x in range(NO_prosumers)]
    # defining the model
    model = ConcreteModel(name='bilevel')
    
    """
    Upper level Variables
    """
    # Horizon Set
    model.T = RangeSet(16,time+15)
    
    # Set of prosumers as customers for DA aggregator 
    model.N = RangeSet(NO_prosumers)
    
    # Set of EVs in the selected DA
    # model.M = frozenset(EVs_list)
    
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
    
    # Energy from discharging EV to home
    model.E_EV_DIS2H = Var(model.N, model.T, within=NonNegativeReals, initialize=0)
    
    # Energy from discharging EV to Grid
    model.E_EV_DIS2G = Var(model.N, model.T, within=NonNegativeReals, initialize=0)
    
    
    # # EV discharge power
    # model.P_EV_G = Var(model.N, model.T, within=NonNegativeReals, initialize=0)
    
    # # EV charge power
    # model.P_EV_L = Var(model.N, model.T, within=NonNegativeReals, initialize=0)
    
    
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
    
    
    # ****************************************
    #  Solar Power
    def solar_power_bounds(model, i, t):
        if i in Solar_list:
            return(0, solar_power[i-1,t-16])
        else:
            return (0,0)
    model.solar_power=Var(model.N, model.T,  within=NonNegativeReals, bounds=solar_power_bounds, initialize=0)
    
    # Energy from PV to use in appliance home
    model.E_PV_2H = Var(model.N, model.T, within=NonNegativeReals, initialize=0)
    
    # Energy from PV to inject into the grid
    model.E_PV_2G = Var(model.N, model.T, within=NonNegativeReals, initialize=0)
    
    #*****************************************
    # # Prosumers power supply and demand
    # model.supply_pros = Var(model.N, model.T, within=NonNegativeReals, initialize=0)
    
    # model.demand_pros = Var(model.N, model.T, within=NonNegativeReals, initialize=0)
    
    # # Binary control variable
    # model.u_PROS   = Var(model.N, model.T, within=Binary, initialize=0)
    
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
    def generator_bounds(model, i, t):
        return (0,gen_capacity[i-1])
    model.g = Var(model.G, model.T, within=NonNegativeReals, initialize=0, bounds=generator_bounds)
    
    # DAs competitor supply offer
    def supply_offer_bounds(model, i, t):
        return (0, F_d_o[i][t-16])
    model.d_o = Var(model.NCDA, model.T, within=NonNegativeReals, initialize=0)  # , bounds=supply_offer_bounds
    
    # DAs competitor demand 
    def demand_bid_bouds(model, i, t):
        return (0, F_d_b[i][t-16])
    model.d_b = Var(model.NCDA, model.T, within=NonNegativeReals, initialize=0) #, bounds=demand_bid_bouds
    
    # voltage phase angle
    model.teta = Var(model.BUS, model.T, within=Reals, initialize=0, bounds=(-180,180))
    
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
    PU power
    """
    # model.b2_1 = Var(model.BUS, model.T, within=NonNegativeReals, initialize=0)
    # model.b2_2 = Var(model.BUS, model.T, within=NonNegativeReals, initialize=0)
    
    # model.b8_1 = Var(model.LINES, model.T, within=NonNegativeReals, initialize=0)
    # model.b8_2 = Var(model.LINES, model.T, within=NonNegativeReals, initialize=0)
    
    # model.c1_1 = Var(model.G, model.T, within=NonNegativeReals, initialize=0)
    # model.c1_2 = Var(model.G, model.T, within=NonNegativeReals, initialize=0)
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
            return model.E_EV_CH[i,t]==0#Constraint.Skip
        # if i in EVs_list:
        #     if t >= arrival[i-1] and t < depart[i-1]:
        #         return model.E_EV_CH[i,t] <= model.u_EV[i,t] * charge_power[i-1]*delta_t  #model.P_EV_L[i,t] #charge_power[i-1]*delta_t
        #     else:
        #         return model.E_EV_CH[i,t]==0
        # else:
        #     return model.E_EV_CH[i,t]==0#Constraint.Skip
    model.ev_charging_con=Constraint(model.N, model.T, rule=ev_charging_rule)
    
    # Constraint (a.3): Ensure that charging of EV don't exceed maximum value of EV_Power
    def ev_discharging_rule(model,i,t):
        if i in EVs_list:
            if t >= arrival[i-1] and t < depart[i-1]:
                return model.E_EV_DIS[i,t] <= (1-model.u_EV[i,t]) *charge_power[i-1]*delta_t # model.P_EV_G[i,t]#charge_power[i-1]*delta_t
            else:
                return model.E_EV_DIS[i,t]==0
        else:
            return model.E_EV_DIS[i,t]==0 #Constraint.Skip
    model.ev_discharging_con=Constraint(model.N, model.T, rule=ev_discharging_rule)
    
    
    # Constraint (a.4): set the SOC 
    def ev_soc_rule(model, i, t):
        if t >= arrival[i-1] and t < depart[i-1] and (i in EVs_list) : 
            return model.SOC[i,t+1] == model.SOC[i,t] + ch_rate*model.E_EV_CH[i,t] - model.E_EV_DIS[i,t]/ch_rate 
        else:
            return Constraint.Skip
    model.ev_soc_con = Constraint(model.N, model.T, rule=ev_soc_rule)
    
    # Constraint (a.4_1): Set the start soc to arrival soc
    def EV_arrival_soc_rule(model, i):
        if i in EVs_list:
            return model.SOC[i, arrival[i-1]]== EV_soc_arrive[i-1]
        else:
            return Constraint.Skip
    model.EV_arrival_soc_con = Constraint(model.N, rule= EV_arrival_soc_rule)
    
    # Constraint (a.5_1): Limit the SOC, Lower Bound
    def ev_soc_low_rule(model, i, t):
        if t >= arrival[i-1] and t < depart[i-1] and (i in EVs_list): 
            return model.SOC[i,t] >=  EV_soc_low[i-1]
        else:
            return Constraint.Skip
    model.ev_soc_low_con=Constraint(model.N, model.T, rule=ev_soc_low_rule)
    
    
    # Constraint (a.5_2): Limit the SOC, Upper Bound
    def ev_soc_low2_rule(model, i, t):
        if t >= arrival[i-1] and t < depart[i-1] and (i in EVs_list): 
            return model.SOC[i,t] <=  EV_soc_up[i-1]
        else:
            return Constraint.Skip
    model.ev_soc_low2_con=Constraint(model.N, model.T, rule=ev_soc_low2_rule)
    
    # Constraint (a.6): Set the target SOC to be as desired(full charge) at departure time
    def ev_traget_rule(model,i):
        if (i in EVs_list):
            return model.SOC[i,depart[i-1]] == EV_soc_up[i-1] #model.ev_demand[i]
        else:
            return Constraint.Skip
    model.ev_target_con = Constraint(model.N, rule=ev_traget_rule)
    
    # Constraint (Custom_1): Set the binary variable to zero outside the [arrival, depart] boundary
    def ev_binary_zero_rule(model,i,t):
        if t < arrival[i-1] or t >= depart[i-1] and (i in EVs_list):
            return model.u_EV[i,t]==0
        else:
            return Constraint.Skip
    model.ev_binary_zero_con = Constraint(model.N, model.T, rule=ev_binary_zero_rule)
    
    
    # Constraint for EV 2 Home and EV 2 Grid power
    def EV_V2H_V2G_rule(model, i, t):
         return model.E_EV_DIS2H[i,t] + model.E_EV_DIS2G[i,t] ==  model.E_EV_DIS[i,t]
        # if t >= arrival[i-1] and t < depart[i-1] and (i in EVs_list):
        #     return model.E_EV_DIS2H[i,t] + model.E_EV_DIS2G[i,t] ==  model.E_EV_DIS[i,t]#model.P_EV_G[i,t]
        #     #return model.E_PV_2H[i,t] + model.E_PV_2G[i,t] == model.P_EV_G[i,t]
        # else:
        #     # return Constraint.Skip
        #     return model.E_EV_DIS2H[i,t] + model.E_EV_DIS2G[i,t] ==0
    model.EV_V2H_V2G_con = Constraint(model.N, model.T, rule=EV_V2H_V2G_rule)
    
    # # Constraint for EV charge power limit
    # def EV_charge_limit_rule(model, i, t):
    #       if t >= arrival[i-1] and t < depart[i-1] and (i in EVs_list):
    #           # return model.E_EV_DIS2H[i,t] <= charge_power[i-1]*delta_t
    #           return Constraint.Skip 
    #       else:
    #           return model.E_EV_DIS2H[i,t]==0  
    # model.EV_charge_limit_con = Constraint(model.N, model.T, rule=EV_charge_limit_rule)

    # # Constraint for EV discharging rule
    # def EV_discharge_limit_rule(model, i, t):
    #     if t >= arrival[i-1] and t < depart[i-1] and (i in EVs_list):
    #          # return model.E_EV_DIS2G[i,t] <= charge_power[i-1]*delta_t
    #          return Constraint.Skip 
    #     else:
    #          return model.E_EV_DIS2G[i,t]==0
    # model.EV_discharge_limit_con = Constraint(model.N, model.T, rule=EV_discharge_limit_rule)
    
        
 
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
    #             Solar Power Constraints
    #********************************************************
    def solar_power_balance_rule(model, i ,t):
        if i in Solar_list:
            return model.E_PV_2H[i,t] + model.E_PV_2G[i,t] == model.solar_power[i,t]
        else:
            return model.solar_power[i,t]==0
    model.solar_power_balance_con = Constraint(model.N, model.T, rule=solar_power_balance_rule)
    
    # If the prosumer dose not have solar panel then it's power is zero otherwise Skip
    def solar_power_2home_rule(model, i, t):
        if i in Solar_list:
            # return model.E_PV_2H[i,t] <= solar_power[i-1,t-16]
            return Constraint.Skip
        else:
            return model.E_PV_2H[i,t]==0
    model.solar_power_2home_con = Constraint(model.N, model.T, rule=solar_power_2home_rule)
    
    # If the prosumer dose not have solar panel then it's power is zero otherwise Skip
    def solar_power_2grid_rule(model, i, t):
        if i in Solar_list:
            # return model.E_PV_2G[i,t] <= solar_power[i-1,t-16]
            return Constraint.Skip
        else:
            return model.E_PV_2G[i,t]==0
    model.solar_power_2grid_con = Constraint(model.N, model.T, rule=solar_power_2grid_rule)
    
    
    
    #********************************************************
    #             prosumers supply and demand power balance
    #********************************************************
    # def prosumers_demand_balance_rule(model, i, t):
    #     return model.demand_pros[i,t] + model.E_PV_2H[i,t] + model.E_EV_DIS2H[i,t] == model.POWER_TCL[i,t]*load_multiply +model.POWER_SL[i,t] + IN_loads.loc[i-1,str(t)]
    # model.prosumers_demand_balance_con = Constraint(model.N, model.T, rule=prosumers_demand_balance_rule)
    
    # def prosumers_supply_balance_rule(model, i, t):
    #     return model.supply_pros[i,t] == model.E_PV_2G[i,t] + model.E_EV_DIS2G[i,t]
    # model.prosumers_supply_balance_con = Constraint(model.N, model.T, rule=prosumers_supply_balance_rule)
    
    # def prosumer_contract_load_rule(model, i, t):
    #     return model.demand_pros[i,t] <= contract[i-1]*model.u_PROS[i,t]
    # model.prosumer_contract_load_con = Constraint(model.N, model.T, rule=prosumer_contract_load_rule)
    
    # def prosumer_contract_supply_rule(model, i, t):
    #     return model.supply_pros[i,t] <= contract[i-1]*(1-model.u_PROS[i,t])
    # model.prosumer_contract_supply_con = Constraint(model.N, model.T, rule=prosumer_contract_supply_rule)
    
    #********************************************************
    #             DA Demand and Supply Constraints
    #********************************************************
    
    
        #         sum_total += model.E_EV_CH[i,t]-model.E_EV_DIS[i,t]
        #     if i in Solar_list:
        #         sum_total = sum_total - model.E_PV_2G[i,t] - model.# Equality constraint (a.13) for power balance in strategic DA
    # def DA_power_balance_rule(model, t):
        
    #     # return model.E_DA_L[t]-model.E_DA_G[t] == sum(model.POWER_TCL[i,t]*load_multiply +model.POWER_SL[i,t] + IN_loads.loc[i-1,str(t)] + 
    #                                                   # model.E_EV_CH[i,t]-model.E_EV_DIS[i,t] - model.solar_power[i,t] for i in model.N)* PU_DA
                                                      
    #     return model.E_DA_L[t]-model.E_DA_G[t] == sum(model.demand_pros[i,t] for i in model.N)*PU_DA - sum(model.supply_pros[i,t] for i in model.N)*PU_DA
    #     ##model.POWER_TCL[i,t]
        
    #     # sum_total = sum(model.POWER_SL[i,t] + IN_loads.loc[i-1,str(t)] + model.POWER_TCL[i,t]*load_multiply  for i in model.N)
        
    #     # for i in model.N:
    #     #     if i in EVs_list:E_PV_2G[i,t]#model.solar_power[i,t]
        
    #     # return model.E_DA_L[t]-model.E_DA_G[t] == sum_total * PU_DA
    
    #     # return model.E_DA_L[t]-model.E_DA_G[t] == \
    #     #         sum(model.E_EV_CH[i,t]-model.E_EV_DIS[i,t]+ model.POWER_TCL[i,t]+ model.POWER_SL[i,t]+ IN_loads.loc[i-1,str(t)] - model.solar_power[i,t] for i in model.N) * PU_DA    # + model.solar_power[i,t]
    # model.DA_power_balance_con = Constraint(model.T, rule=DA_power_balance_rule)
    
    def DA_power_balance_load_rule(model, t):
        # return model.E_DA_L[t] == sum(model.demand_pros[i,t] for i in model.N)*PU_DA
        return model.E_DA_L[t] == sum( model.POWER_TCL[i,t]*load_multiply + model.POWER_SL[i,t] + IN_loads.loc[i-1,str(t)] -model.E_PV_2H[i,t] - model.E_EV_DIS2H[i,t] for i in model.N)*PU_DA
    model.DA_power_balance_load_con = Constraint(model.T, rule=DA_power_balance_load_rule)
    
    
    def DA_power_balance_gen_rule(model, t):
        # return model.E_DA_G[t] == sum(model.supply_pros[i,t] for i in model.N)*PU_DA
        return model.E_DA_G[t] == sum( model.E_PV_2G[i,t] + model.E_EV_DIS2G[i,t] for i in model.N)*PU_DA
    model.DA_power_balance_gen_con = Constraint(model.T, rule=DA_power_balance_gen_rule)
    
    
        
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
        
        if i == dic_CDA_Bus['DAS']:
            sum2= -model.E_DA_G[t]
            sum3= model.E_DA_L[t]
            
        for key in dic_CDA_Bus.keys():
            if key != 'DAS' and dic_CDA_Bus[key] == i:
                sum3 += model.d_b[key,t]
                sum2 += -model.d_o[key,t]
        
        sumB = sum(B[i-1,j-1]*model.teta[j,t] for j in model.BUS)
        
        return sum1+sum2+sum3+sumB  == 0  #+ model.b2_1[i,t] - model.b2_2[i,t]
    model.network_power_balance_con = Constraint(model.BUS, model.T, rule=network_power_balance_rule)    
    
    
    
    # def network_power_balance_rule(model, t):
    #     sum_t=0
    #     for i in model.BUS:
    #         sum1=0
    #         if i in dic_G.keys():
    #             sum1=sum(-model.g[x,t] for x in dic_G[i])
            
    #         sum3=0
    #         sum2=0
    #         if i in dic_Bus_CDA.keys():
    #             if i == DABus:
    #                 sum2= -model.E_DA_G[t]
    #                 sum3= model.E_DA_L[t]
    #             else:
    #                 x=dic_Bus_CDA[i]
    #                 sum3 = model.d_b[x,t]   # Demand Load by competetive DA i     if x != 'DAs'
    #                 sum2 = -model.d_o[x,t]  # Supply offer by competetive DA i
            
    #         sumB = sum(B[i-1,j-1]*model.teta[j,t] for j in model.BUS)
            
    #         sum_t += sum1+sum2+sum3 +sumB 
        
    #     # sumB = sum(B[i-1,j-1]*model.teta[j,t] for j in model.BUS)
    #     # sum_t += sumB
     
    
    #     return sum_t  == 0  #+ model.b2_1[i,t] - model.b2_2[i,t]
    # model.network_power_balance_con = Constraint(model.T, rule=network_power_balance_rule)  
    
   
    
   # # Constraint (b.8), Line Flow Bounds (b.8)  ******************
    # def line_flow_lower_bound_rule(model, i, t):
    #     return sum(-Yline[i-1,j-1]*model.teta[j,t] for j in model.BUS) - model.b8_1[i,t] <= FMAX[i-1]
    # model.line_flow_lower_bound_con = Constraint(model.LINES, model.T, rule=line_flow_lower_bound_rule)
    
    # # Constraint (b.8.2) line Flows Bounds, Upper bound ***********
    # def line_flow_upper_bound_rule(model, i, t):
    #     return sum(Yline[i-1,j-1]*model.teta[j,t] for j in model.BUS) - model.b8_2[i,t] <= FMAX[i-1]
    # model.line_flow_upper_bound_con = Constraint(model.LINES, model.T, rule=line_flow_upper_bound_rule)
    
   
    
   # Constraint (C.1) generators dual price
    def generator_dual_price_rule(model, i, t):
        bus=dic_G_Bus[i]        
        return c_g[i][t-16]-model.Lambda[bus,t] - model.w_g_low[i,t]+model.w_g_up[i,t]  ==0  #+ model.c1_1[i,t] - model.c1_2[i,t]
    model.generator_dual_price_con=Constraint(model.G, model.T, rule=generator_dual_price_rule)
    
    
    #**********************************************
    #             Feasibility problem
    
    
    # Constrint (C.2) competitor suuply to grid offer
    def competitor_offer_dual_rule(model, i, t):
        bus=dic_CDA_Bus[i]
        return c_d_o[i][t-16]-model.Lambda[bus,t] - model.w_do_low[i,t] + model.w_do_up[i,t]  ==0  #c_d_o[i][t-16]
    model.competitor_offer_dual_con = Constraint(model.NCDA, model.T, rule=competitor_offer_dual_rule)
    
    # Constraint (C.3) competitors demand bid
    def competitor_demand_dual_rule(model, i, t):
        bus=dic_CDA_Bus[i]
        return  -c_d_b[i][t-16] + model.Lambda[bus,t] - model.w_db_low[i,t] + model.w_db_up[i,t] == 0 # -c_d_b[i][t-16]
    model.competitor_demand_dual_con = Constraint(model.NCDA, model.T, rule=competitor_demand_dual_rule)
    
    #////////////////////////////////////////////
    #********************************************
    
    
    #+ model.c2_1[t] - model.c2_2[t]
    
    # Constraint (c.4) Strategic Aggregator supply into grid offer
    def strategic_offer_dual_rule(model,t):
        bus=dic_CDA_Bus['DAS']
        return c_DA_o[t-16]-model.Lambda[bus,t]-model.w_DAo_low[t] + model.w_DAo_up[t]  == 0
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
        sum1= sum(B_T[i-1,j-1]*model.Lambda[j,t] for j in model.BUS )
        
        Yline_T = Yline.transpose()
        sum2= sum(Yline_T[i-1,j-1]*model.w_line_low[j,t] for j in model.LINES )
        
        sum3= sum(Yline_T[i-1, j-1]*model.w_line_up[j,t] for j in model.LINES )
        
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
        return  g_s[i][t-16]/MVA - model.g[i,t] <= model.u_g_up[i,t]*bigM
    model.KKT_gen_up_con = Constraint (model.G, model.T, rule= KKT_gen_up_rule)
    
    #KKT Constraint(D.3.2)
    def KKT_gen_up_3_2_rule (model, i, t):
        return  g_s[i][t-16]/MVA - model.g[i,t] >= 0
    model.KKT_gen_up_3_2_con = Constraint (model.G, model.T, rule= KKT_gen_up_3_2_rule)
    
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
    
    # KKT Constraint (D.7.2)
    def KKT_DAs_supply_offer_up_3_rule (model, i, t):
        return F_d_o[i][t-16] - model.d_o[i,t] >= 0
    model.KKT_DAs_supply_offer_up_3_con = Constraint(model.NCDA, model.T, rule=KKT_DAs_supply_offer_up_3_rule )
    
    
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
    
    # #KKT Constraint (D.11.2)   ### Test disabled and model worked
    def KKT_DAs_demand_bid_up_3_rule (model, i, t):
        return F_d_b[i][t-16] - model.d_b[i,t] >= 0
    model.KKT_DAs_demand_bid_up_3_con = Constraint(model.NCDA, model.T, rule=KKT_DAs_demand_bid_up_3_rule)
    
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
    
    
    # KKT Constraint (D.15.2)
    def KKT_stKrategic_DA_bid_up_3_rule (model,t):
        return model.DA_supply[t] - model.E_DA_G[t] >= 0
    model.KKT_stKrategic_DA_bid_up_3_con = Constraint (model.T, rule=KKT_stKrategic_DA_bid_up_3_rule)
    
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
    
    # KKT Constraint (D.19.2)
    def KKT_strategic_demand_up_3_rule (model,t):
        return model.DA_demand[t] - model.E_DA_L[t] >= 0
    model.KKT_strategic_demand_up_3_con = Constraint(model.T, rule=KKT_strategic_demand_up_3_rule)
    
    # KKT Constraint (D.20)
    def KKT_strategiv_demand_up_2_rule (model,t):
        return model.w_DAb_up[t] <=  (1-model.u_DAs_b_up[t]) * bigM
    model.KKT_strategiv_demand_up_2_con =Constraint(model.T, rule=KKT_strategiv_demand_up_2_rule)
    
    
    # KKT Transmission line Constraint (D.21)
    def KKT_transmission_low_rule (model, i, t):
        #Yline[i-1, j-1]
        return sum(Yline[i-1, j-1]*model.teta[j,t] for j in model.BUS ) + FMAX[i-1] <=   model.u_line_low[i,t] * bigM
    model.KKT_transmission_low_con = Constraint (model.LINES, model.T, rule=KKT_transmission_low_rule)
    
    # KKT Transmission line Constraint (D.21.2)
    def KKT_transmission_low_3_rule (model, i, t):
        #Yline[i-1, j-1]
        return sum(Yline[i-1, j-1]*model.teta[j,t] for j in model.BUS ) + FMAX[i-1] >= 0
    model.KKT_transmission_low_3_con = Constraint (model.LINES, model.T, rule=KKT_transmission_low_3_rule)
    
    # KKT Transmission line Constraint (D.22)
    def KKT_transmission_low_2_rule (model, i, t):
        return model.w_line_low[i,t] <= (1-model.u_line_low[i,t]) * bigM
    model.KKT_transmission_low_2_con = Constraint(model.LINES, model.T, rule=KKT_transmission_low_2_rule)
    
    # KKT Transmission line Constraint (D.23)
    def KKT_transmission_up_rule(model, i, t):
        return sum(-Yline[i-1,j-1]* model.teta[j,t] for j in model.BUS) + FMAX[i-1] <= model.u_line_up[i,t] * bigM
    model.KKT_transmission_up_con = Constraint(model.LINES, model.T, rule=KKT_transmission_up_rule)
    
    # KKT Transmission line Constraint (D.23.2)
    def KKT_transmission_up_3_rule(model, i, t):
        return sum(-Yline[i-1,j-1]* model.teta[j,t] for j in model.BUS) + FMAX[i-1] >= 0
    model.KKT_transmission_up_3_con = Constraint(model.LINES, model.T, rule=KKT_transmission_up_3_rule)
    
    
    # KKT Transmission line Constraint (D.24)
    def KKT_transmission_up_2_rule(model, i, t):
        return model.w_line_up[i,t] <= (1-model.u_line_up[i,t]) * bigM
    model.KKT_transmission_up_2_con = Constraint(model.LINES, model.T, rule=KKT_transmission_up_2_rule)
    
    
    #***************************************
    # refrense angel set
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
                    sum(c_d_o[i][t-16]*model.d_o[i,t] for i in model.NCDA ) -\
                        sum(c_d_b[i][t-16]*model.d_b[i,t] for i in model.NCDA) +\
                            sum(model.w_g_up[i,t] * g_s[i][t-16]/MVA for i in model.G) +\
                                sum(model.w_do_up[i,t]* F_d_o[i][t-16] for i in model.NCDA) +\
                                    sum(model.w_db_up[i,t]*F_d_b[i][t-16] for i in model.NCDA) +\
                                        sum(FMAX[i-1]*model.w_line_low[i,t] for i in model.LINES) +\
                                            sum(FMAX[i-1]*model.w_line_up[i,t] for i in model.LINES)  for t in model.T )
    model.obj = Objective(rule=social_welfare_optimization_rule, sense=minimize)
    
    return model