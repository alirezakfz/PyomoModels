# -*- coding: utf-8 -*-
"""
Created on Tue May 25 16:05:41 2021

@author: alire
"""

import random
import pandas as pd
import numpy as np
import collections
from samples_gen import generate_price, generate_temp

from pyomo.environ import *
from pyomo.opt import SolverFactory



def dictionar_bus(GenBus, CDABus, DABus):
    """
    This function creates dictionary mapping BUS and DAs on that bus
    Inputs: 
        list of each Generator bus location index=Generator  Value= Bus number
        List of each DA bus location. index=DA   Value= Bus number
        DABus is the bus number for the strategic DA which solves the MPEC
    """
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
    return dic_CDA_Bus, dic_Bus_CDA


def load_data(file_index):
    df1 = pd.read_csv('inflexible_profiles_scen_'+file_index+'.csv').round(3)/1000
    df2 = pd.read_csv('prosumers_profiles_scen_'+file_index+'.csv')
    return df1 , df2








gen_capacity =[50,50,50]

# Time Horizon
H = range(16,time+16)    
MVA = 1  # Power Base
PU_DA = 1/(1000*MVA)


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


# 2019 November 15 forecasted temprature
outside_temp=[16.784803,16.094803,15.764802,14.774801,14.834802,14.184802,14.144801,15.314801,16.694803,19.734802,24.414803,25.384802,26.744802,27.144802,27.524803,27.694803,26.834803,26.594803,25.664803,22.594803,21.394802,20.164803,19.584803,20.334803]


for n in range(100):
    for j in range(1,ncda+1):
        
        IN_loads, profiles = load_data(j)
        
        # EVs properties 
        arrival = profiles['Arrival']
        depart  = profiles['Depart']
        charge_power = profiles['EV_Power']
        EV_soc_low   = profiles['EV_soc_low']
        EV_soc_up   = profiles['EV_soc_up']
        EV_soc_arrive = profiles['EV_soc_arr']
        EV_demand = profiles['EV_demand']
        
                
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





mpec_model(ng, nb, nl, ncda,
               arrival, depart, charge_power,EV_soc_arrive,EV_soc_low, EV_soc_up, 
               TCL_Max, TCL_TEMP, TCL_R, TCL_Beta, TCL_temp_low, outside_temp, 
               SL_low, SL_up, SL_cycle, SL_loads,
               dic_G, dic_Bus_CDA, DABus, B, Y_line, dic_G_Bus, 
               c_g, c_d_o, c_d_b, 
               dic_CDA_Bus, g_s, F_d_o, F_d_b, FMAX)