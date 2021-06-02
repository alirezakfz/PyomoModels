# -*- coding: utf-8 -*-
"""
Created on Tue May 25 16:05:41 2021

@author: alire
"""

import random
import time
import pandas as pd
import numpy as np
import collections
from samples_gen import generate_price, generate_temp
#from MPEC_Concrete_Model_ver01 import mpec_model
from MPEC_Concrete_Model_ver02 import mpec_model
from pyomo.environ import *
from pyomo.opt import SolverFactory

from Model_to_CSV import model_to_csv



def solved_model_bids(model):
    new_d_o=[]
    new_d_b=[]
    for t in model.T:
        new_d_b.append(round(value(model.E_DA_L[t]),6))
        new_d_o.append(round(value(model.E_DA_G[t]),6))
    return new_d_o, new_d_b



def compare_lists(old, new):
    check=[]
    for i in range(len(old)):
        if abs(old[i]-new[i]) < 0.01:
            check.append(True)
    return check
        

def check_bids(old, new):
    check=False
    for key in old.keys():
        compare = compare_lists(old[key], new[key])
        if np.sum(compare) == len(old[key]):
            check=True
        else:
            return False
    return check
            
      
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
    for i in range(len(CDABus[DABus-1])):
        dic_CDA_Bus[i+1]=CDABus[DABus-1][i]
        dic_Bus_CDA[CDABus[DABus-1][i]] = i+1
    
    dic_CDA_Bus['DAS']=DABus     # Strategic Aggregator
    dic_Bus_CDA[DABus] = 'DAS'   # Strategic Aggregator
    return dic_CDA_Bus, dic_Bus_CDA, dic_G, dic_G_Bus


def load_data(file_index):
    df1 = pd.read_csv('prosumers_data/inflexible_profiles_scen_'+file_index+'.csv').round(3)/1000
    # Just selecting some prosumers like 500 or 600 or 1000
    df1 = df1[:600]
    # print(df1.shape)
    df2 = pd.read_csv('prosumers_data/prosumers_profiles_scen_'+file_index+'.csv')
    df2 = df2[:600]
    return df1 , df2


gen_capacity =[50, 50, 50]
random.seed(42)

# Time Horizon
horizon=24
H = range(16,horizon+16)    
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
CDABus = [[2, 3], [1,3], [1,2]]      # Vector with competing DAs Buses
DABus = 1           # DA Bus

FMAX = [50, 50, 50] # Vector with Capacities of Network Lines in pu
FMAX = [i/MVA for i in FMAX]


# # Matrix (nb x ng) indicating the network location of generators
# GenLoc = np.zeros((nb,ng))
# for gg in range(0, ng):
#     GenLoc[GenBus[gg]-1,gg] = 1

# # Matrix (nb x ncda) indicating the network location of competing DAs
# CDALoc = np.zeros((nb,ncda))
# for dd in range(0,ncda):
#     CDALoc[CDABus[dd]-1,dd] = 1
    
# #Vector (nb x 1) indicating the network location of the DA
# DALoc = np.zeros((nb,1))
# DALoc[DABus-1] = 1


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



offers_bid=[]
demand_bid=[]
def random_offer(NO_CDA, horizon):
    pivot=0.10
    offer_dict=dict()
    bid_dict=dict()
    for competitor in range(1,NO_CDA+2):
        temp_offer=[]
        temp_bid=[]
        for t in range(0,horizon):
            if random.random() >= pivot:
                temp_offer.append(0)
                temp_bid.append(round(random.random()/MVA, 3))  # Mega Watt
            else:
                temp_bid.append(0)
                temp_offer.append(round(random.random()/MVA,3)) # Mega Watt
        offer_dict[competitor]=temp_offer
        bid_dict[competitor]=temp_bid
    
    return offer_dict, bid_dict

offers_bid , demand_bid = random_offer(ncda, horizon)

def select_bid(j, offers_bid, demand_bid):
    counter= 1
    count=1
    
    d_o=dict()
    d_b=dict()
    for i in range(len(offers_bid)):
        if counter != j:
            print(i)
            d_o[count] = offers_bid[i+1]
            d_b[count] = demand_bid[i+1]
            counter += 1
            count+=1
        else:
            counter +=1
    
       
    return d_o, d_b
        

"""
Supply and demand Random
"""
# Random amount of generation for horizon slots
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


#Price bid of generator i in horizon t
c_g = { 1:random_price(horizon,12,20),
        2:random_price(horizon,20,30),
        3:random_price(horizon,50,70),
        4:random_price(horizon,100,110)}  
c_g[1]=[16 for x in range(0,horizon)]
c_g[2]=[19 for x in range(0,horizon)]
c_g[3]=[25 for x in range(0,horizon)]
c_g[4]=[100 for x in range(0,horizon)]



#Price bid for supplying power of competing DA  i in time t
c_d_o = [{'DAS':random_price(horizon,1,16), 1:random_price(horizon,1,16), 2:random_price(horizon,1,16)},
         {'DAS':random_price(horizon,1,16), 1:random_price(horizon,1,16), 2:random_price(horizon,1,16)},
          {'DAS':random_price(horizon,1,16), 1:random_price(horizon,1,16), 2:random_price(horizon,1,16)}]

# c_d_o = {'DAS':random_price(horizon,1,2),
#           1:random_price(horizon,1,2),
#           2:random_price(horizon,1,2)}

# Price bid for buying power of competing DA  i in horizon t
c_d_b = [{'DAS':random_price(horizon,70,110),1:random_price(horizon,70,110), 2:random_price(horizon,70,110)},
         {'DAS':random_price(horizon,70,110),1:random_price(horizon,70,110), 2:random_price(horizon,70,110)},
         {'DAS':random_price(horizon,70,110),1:random_price(horizon,70,110), 2:random_price(horizon,70,110)}]

# c_d_b = {'DAS':random_price(horizon,1,2),
#           1:random_price(horizon,1,2),
#           2:random_price(horizon,1,2)}


# Price bid for supplying power of strategic DA in horizon t
c_DA_o = c_d_o[DABus-1]['DAS'] # random_price(horizon)

# Price bid for buying power of strategic DA in horizon t
c_DA_b = c_d_b[DABus-1]['DAS'] # random_price(horizon)

# Supply offer of generator i in time t
g_s = { 1:random_generation(horizon,10, 12),
        2:random_generation(horizon,5, 10),
        3:random_generation(horizon,15, 20),
        4:random_generation(horizon,1, 50)}


# 2019 November 15 forecasted temprature
outside_temp=[16.784803,16.094803,15.764802,14.774801,14.834802,14.184802,14.144801,15.314801,16.694803,19.734802,24.414803,25.384802,26.744802,27.144802,27.524803,27.694803,26.834803,26.594803,25.664803,22.594803,21.394802,20.164803,19.584803,20.334803]

feasible_bid = dict()
feasible_offer = dict()

# Adding solar power to randomly selected houses.
def solar_power_generator(index_len):
    return [random.random()*0.05 for i in range(index_len)]
    
    
    

def random_solar_power(in_loads, j):
    random.seed(j)
    length = len(in_loads)
    # Select 20 percent of households containt solar power
    random_index = [random.randrange(1, length, 1) for i in range(int(length/2))]
    
    selected_time = ['16','17','18','19','30','31','32','33','34','35','36','37','38','39']
    
    for i in range(len(selected_time)):
        random_power = solar_power_generator(len(random_index))
        in_loads.loc[random_index,selected_time[i]]= in_loads.loc[random_index,selected_time[i]]-random_power
        
    return in_loads



for n in range(3):
    new_offers=dict()
    new_bids=dict()
    for j in range(1,ncda+2):
        
        
        IN_loads, profiles = load_data(str(j))
        
        # Adding random solar power
        IN_loads = random_solar_power(IN_loads, j)
        
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

        # Creating dictionary mapping current DA as strategic in MPEC model
        dic_CDA_Bus, dic_Bus_CDA, dic_G, dic_G_Bus = dictionar_bus(GenBus, CDABus, j)

        DABus=j
        F_d_o, F_d_b = select_bid(j, offers_bid, demand_bid)
        
        #F_d_b = demand_bid[j-1]
        
        # Price bid for supplying power of strategic DA in time t
        c_DA_o = c_d_o[DABus-1]['DAS'] # random_price(time)
        
        # Price bid for buying power of strategic DA in time t
        c_DA_b = c_d_b[DABus-1]['DAS'] # random_price(time)
        
        ##Timer
        solver_time = time.time()
        
        model = mpec_model(ng, nb, nl, ncda,IN_loads, gen_capacity, 
                        arrival, depart, charge_power,EV_soc_arrive,EV_soc_low, EV_soc_up, 
                        TCL_Max, TCL_R, TCL_Beta, TCL_temp_low, outside_temp, 
                        SL_low, SL_up, SL_cycle, SL_loads,
                        dic_G, dic_Bus_CDA, DABus, B, Yline, dic_G_Bus, 
                        c_g, c_d_o[j-1], c_d_b[j-1], 
                        dic_CDA_Bus, g_s, F_d_o, F_d_b, FMAX,
                        c_DA_o, c_DA_b)
       
        SOLVER_NAME="gurobi"  #'cplex'
        solver=SolverFactory(SOLVER_NAME)
        results = solver.solve(model)
        #print(results)
        
        solver_time=time.time()-solver_time
        
        if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
            print('Model solved optimal DA:',j,'   Time taken:', solver_time)
            # model_to_csv(model,IN_loads.sum(0))
            new_d_o, new_d_b = solved_model_bids(model)
            feasible_bid[j] =  new_d_b
            feasible_offer[j] = new_d_o
        else:
            new_d_o = feasible_offer[j]
            new_d_b = feasible_bid[j]
        
        new_offers[j]=new_d_o
        new_bids[j]= new_d_b
        
        # model_to_csv(model, IN_loads.sum(0))
        
        # Finishing Step 3
    # Step 4 check if epsilon difference exist
        
    check=False
    if check_bids(offers_bid,new_offers) and check_bids(demand_bid,new_bids):
        check=True
        print("solution found in iteration:",n)
        break
    else:
        print('no EPEC, round:',n,'\n******************')
        
    # Step 6
    
    if not check:
        offers_bid = new_offers
        demand_bid = new_bids
    

if check:
    print('Solution is found:')
    print("Offers differences:")
    print(pd.DataFrame.from_dict(offers_bid) - pd.DataFrame.from_dict(new_offers))
    print("Bid Differences:")
    print(pd.DataFrame.from_dict(demand_bid) - pd.DataFrame.from_dict(new_bids))
else:
    print('No EPEC is found')
    print(pd.DataFrame.from_dict(offers_bid))
    print(pd.DataFrame.from_dict(demand_bid))

# """
# check strong duality
# """
# check =True

# print("\n************************\nChecking if strong duality holds")
# print("Left_Hand_Side    Right_Hand_Side\n")
# for t in model.T:
#     sum1=sum(c_g[i][t-16]*value(model.g[i,t]) for i in model.G)+\
#         sum(c_d_o[DABus-1][i][t-16]* value(model.d_o[i,t]) for i in model.NCDA) -\
#             sum(c_d_b[DABus-1][i][t-16]* value(model.d_b[i,t]) for i in model.NCDA) +\
#                 c_d_o[DABus-1]['DAS'][t-16]* value(model.E_DA_G[t]) -\
#                     c_d_b[DABus-1]['DAS'][t-16] * value(model.E_DA_L[t])
    
#     sum2=sum(value(model.w_g_up[i,t])*value(model.g[i,t]) for i in model.G)+\
#         sum( value(model.w_do_up[i,t]) * value(model.d_o[i,t]) for i in model.NCDA) +\
#             sum( value(model.w_db_up[i,t]) * value(model.d_b[i,t]) for i in model.NCDA) +\
#                 value(model.w_DAo_up[t]) * value(model.DA_supply[t]) +\
#                     value(model.w_DAb_up[t]) * value(model.DA_demand[t]) +\
#                         sum(value(model.w_line_low[i,t])*FMAX[i-1] for i in model.LINES) +\
#                             sum(value(model.w_line_up[i,t])*FMAX[i-1] for i in model.LINES)
#     print(sum1," ",sum2," ",round(sum1,4)==-round(sum2,4))