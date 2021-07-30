# -*- coding: utf-8 -*-
"""
Created on Fri Jul 16 17:09:00 2021

@author: Alireza
"""


import random
import time
import pandas as pd
import numpy as np
import collections
from collections import Counter

from MPEC_Concrete_Model_Smooth_Fictitious_Play import mpec_model
from MPEC_Concrete_Model_ver02 import mpec_model as diagonalization
from pyomo.environ import *
from pyomo.opt import SolverFactory





def solved_model_bids(model):
    new_d_o=[]
    new_d_b=[]
    for t in model.T:
        # new_d_b.append(value(model.E_DA_L[t]))
        # new_d_o.append(value(model.E_DA_G[t]))
        new_d_b.append(round(value(model.E_DA_L[t]),4))
        new_d_o.append(round(value(model.E_DA_G[t]),4))
    return new_d_o, new_d_b


        
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
    df1 = pd.read_csv('prosumers_data/inflexible_profiles_scen_'+file_index+'.csv').round(5)/1000
    # Just selecting some prosumers like 500 or 600 or 1000
    df1 = df1[:100]
    # print(df1.shape)
    df2 = pd.read_csv('prosumers_data/prosumers_profiles_scen_'+file_index+'.csv')
    df2 = df2[:100]
    return df1 , df2


gen_capacity =[50, 50, 50]
# gen_capacity =[50000, 50000, 50000]

random.seed(42)

# Time Horizon
horizon=24
H = range(16,horizon+16)    
MVA = 1  # Power Base
PU_DA = 1/(1000*MVA)

# Number of strategies
no_strategies = 20

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

FMAX = [50, 50, 50]
# FMAX = [50000, 50000, 50000] # Vector with Capacities of Network Lines in pu
FMAX = [i/MVA for i in FMAX]


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
            # if random.random() >= pivot:
            #     temp_offer.append(0)
            #     # temp_bid.append(random.randint(1, 4))
            #     temp_bid.append(round(random.random()/MVA, 3))  # Mega Watt
            # else:
            #     temp_bid.append(0)
            #     # temp_offer.append(random.randint(1, 4))
            #     temp_offer.append(round(random.random()/MVA,3)) # Mega Watt
            temp_bid.append(round(random.random()/MVA, 3))  # Mega Watt
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
            # print(i)
            temp_offer = offers_bid[i+1]
            temp_bid   = demand_bid[i+1]
            # for l in range(len(temp_offer)):
            #     if temp_offer[l] == 0 and temp_bid[l]==0 :
            #         temp_bid[l]= 0.11
            
            d_o[count] = temp_offer
            d_b[count] = temp_bid
            # d_o[count] = offers_bid[i+1]
            # d_b[count] = demand_bid[i+1]
            counter += 1
            count+=1
        else:
            counter +=1
    
    # print(pd.concat([pd.DataFrame(d_o), pd.DataFrame(d_b)], axis=1)) 
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

# Adding solar power to randomly selected houses.
def solar_power_generator(index_len):
    return [random.random()*0.5 for i in range(index_len)]


# This function adds solar power into inflexible loads
# It is raplaced by adding new variable as solar power into model
def random_solar_power_var(in_loads, j):
    random.seed((j+2)**2)
    length = len(in_loads)
    # Select 20 percent of households containt solar power
    random_index = [random.randrange(1, length, 1) for i in range(int(length/2))]
    
    selected_time = ['16','17','18','19','30','31','32','33','34','35','36','37','38','39']
    
    solar_power = np.zeros(in_loads.shape)
    
    for i in range(len(selected_time)):
        random_power = solar_power_generator(len(random_index))
        counter = 0
        for j in random_index:
            solar_power[j,i] = random_power[counter]
            counter +=1
    
    return solar_power

# List of solar powers
DA_solar_power =[]        
for j in range(1,ncda+2):
    IN_loads, profiles = load_data(str(j))
    DA_solar_power.append(random_solar_power_var(IN_loads, j))


"""
Solve once and find range for offers and bids
using diagonalization method
"""

check=False
no_iteration =3

print("Running diagonalization for calibrating offers and bids prediction")

for n in range(no_iteration):
    new_offers=dict()
    new_bids=dict()
    infeasibility_counter=0
    
    for j in range(1,ncda+2):
        
        
        IN_loads, profiles = load_data(str(j))
        
        # Adding random solar power
        # if j == 1:
        # IN_loads = random_solar_power(IN_loads, j)
        
        
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
        # offers_bid , demand_bid = random_offer(ncda, horizon)
        F_d_o, F_d_b = select_bid(j, offers_bid, demand_bid)
        
        #F_d_b = demand_bid[j-1]
        
        # Price bid for supplying power of strategic DA in time t
        c_DA_o = c_d_o[DABus-1]['DAS'] # random_price(time)
        
        # Price bid for buying power of strategic DA in time t
        c_DA_b = c_d_b[DABus-1]['DAS'] # random_price(time)
        
        ##Timer
        solver_time = time.time()
        
        model = diagonalization(ng, nb, nl, ncda,IN_loads, gen_capacity, 
                        arrival, depart, charge_power,EV_soc_arrive,EV_soc_low, EV_soc_up, 
                        TCL_Max, TCL_R, TCL_Beta, TCL_temp_low, outside_temp, 
                        SL_low, SL_up, SL_cycle, SL_loads,
                        dic_G, dic_Bus_CDA, DABus, B, Yline, dic_G_Bus, 
                        c_g, c_d_o[j-1], c_d_b[j-1], 
                        dic_CDA_Bus, g_s, F_d_o, F_d_b, FMAX,
                        c_DA_o, c_DA_b, DA_solar_power[j-1])
       
        SOLVER_NAME= "gurobi" #"gurobi"  #'cplex'
        solver=SolverFactory(SOLVER_NAME)
        results = solver.solve(model)
        
        # To check constraint feasibility after solving problem
        # check_constraints(model, Yline, B,dic_G, dic_Bus_CDA, DABus, c_g, dic_G_Bus, dic_CDA_Bus, 
        #                   c_d_o[j-1], c_d_b[j-1], c_DA_o, c_DA_b, 1000, 1000, g_s, F_d_o, F_d_b, FMAX )
        
        #print(results)
        
        solver_time=time.time()-solver_time
        
        if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
            print('Model solved and is optimal for DA:',j,'   Time taken:', solver_time)
            # model_to_csv(model,IN_loads.sum(0))
            new_d_o, new_d_b = solved_model_bids(model)
        #     feasible_bid[j] =  new_d_b
        #     feasible_offer[j] = new_d_o
        # else:
        #     infeasibility_counter+=1
        #     infeasibility_counter_DA[j-1] += 1
        #     new_d_o = random_offer(ncda, horizon)[0][j]
        #     new_d_b = random_offer(ncda, horizon)[1][j]
        
        new_offers[j]=new_d_o
        new_bids[j]= new_d_b
        
        
        
        # model_to_csv(model, IN_loads.sum(0))
        
        # Finishing Step 3
    # 
    
    for key in new_offers:
        zipped_lists = zip(offers_bid[key], new_offers[key])
        sum_zip =  [(x + y)/2 for (x, y) in zipped_lists]
        offers_bid[key] = sum_zip
        
        zipped_lists = zip(demand_bid[key], new_bids[key])
        sum_zip =  [(x + y)/2 for (x, y) in zipped_lists]
        demand_bid[key] = sum_zip

# Double the values
for key in new_offers:
        # zipped_lists = zip(offers_bid[key], new_offers[key])
        # sum_zip =  [(x + y)/2 for (x, y) in zipped_lists]
        offers_bid[key] =  offers_bid[key]*2
        
        # zipped_lists = zip(demand_bid[key], new_bids[key])
        # sum_zip =  [(x + y)/2 for (x, y) in zipped_lists]
        demand_bid[key] = demand_bid[key] *2

"""
going for FICTITIOUS PLAY algortihm
"""
# Discretizing offers and bids
discrete_bid = dict()
discrete_offer = dict()

demand_probability=dict()
supply_probability=dict()
# Create dictionary for each strategic DA counting it's discrete value
def make_discrte_value(step):
    for i in range(1, ncda+2):
        discrete_bid[i]={}
        discrete_offer[i]={}
        
        offers_temp = dict()
        demand_temp= dict()
        
        demand_prob_temp=[]
        supply_prob_temp=[]
        for t in range(horizon):
            offers_temp[t] = {}
            demand_temp[t] = {}
            
            demand_p_temp=[]
            supply_p_temp=[]
            
            offers = np.linspace(0, offers_bid[i][t], step).tolist()
            offers = np.around(offers, 4)
            
            demands = np.linspace(0, demand_bid[i][t], step).tolist()
            demands = np.around(demands, 4)
            
            offers_temp[t][(0,0)] = 0
            demand_temp[t][(0,0)] = 0
            
            demand_p_temp.append(0)
            supply_p_temp.append(0)
            
            for value in range(step-1):
                offers_temp[t][(offers[value], offers[value+1])] = 0
                demand_temp[t][(demands[value], demands[value+1])] = 0
                supply_p_temp.append(round((offers[value]+offers[value+1])/2, 4))
                demand_p_temp.append(round((demands[value]+demands[value+1])/2, 4))
            
            demand_prob_temp.append(demand_p_temp)
            supply_prob_temp.append(supply_p_temp)
        
        discrete_bid[i] = demand_temp
        discrete_offer[i] = offers_temp
        
        demand_probability[i]= demand_prob_temp
        supply_probability[i]= supply_prob_temp
    pass
# Calling thins function to make values

make_discrte_value(no_strategies)

# After each iteration solving MPEC update discrete offers and bids by counting them
def check_boundry(new_d_o, new_d_b, j):
    for i in range(len(new_d_o)):
        for key in discrete_offer[j][i]:
            if new_d_o[i] == 0.0:
                discrete_offer[j][i][(0,0)] += 1
                break
            elif new_d_o[i] > key[0] and new_d_o[i]<= key[1]:
                discrete_offer[j][i][key] += 1
            
        
    for i in range(len(new_d_b)):
        for key in discrete_bid[j][i]:
            if new_d_b[i] == 0.0:
                discrete_bid[j][i][(0,0)] += 1
                break
            elif new_d_b[i] > key[0] and new_d_b[i]<= key[1]:
                discrete_bid[j][i][key] += 1         
    pass
                
# Update offers_bid, demand_bid dictionaries
def keywithmaxval(d):
     """ a) create a list of the dict's keys and values; 
         b) return the key with the max value"""  
     v=list(d.values())
     k=list(d.keys())
     return k[v.index(max(v))]
 
def update_offers_demands():
    
    for key in discrete_bid.keys():
        temp_d_o = [] #offers_bid[key]
        temp_d_b = [] #demand_bid[key]
        for i in range(horizon):
            max_key_d_b = keywithmaxval(discrete_bid[key][i])
            max_key_d_o = keywithmaxval(discrete_offer[key][i])
            temp_d_b.append((max_key_d_b[0]+max_key_d_b[1])/2)
            temp_d_o.append((max_key_d_o[0]+max_key_d_o[1])/2)
        
        # Updarte demand and offer bids
        offers_bid[key] = np.around(temp_d_o,4)
        demand_bid[key] = np.around(temp_d_b,4)
    pass


        
# Create two
average_demand_prob = dict()
average_supply_prob = dict()

total_demand_prob = dict()
total_supply_prob = dict()

for j in range(1,ncda+2):
    average_demand_prob[j] = np.zeros((horizon,no_strategies))
    average_supply_prob[j] = np.zeros((horizon,no_strategies))
    total_demand_prob[j] = np.zeros((horizon,no_strategies))
    total_supply_prob[j] = np.zeros((horizon,no_strategies))

# Updating probability values after solve
def load_bids_probs(model,j):
    temp_demand = np.zeros((horizon,no_strategies))
    temp_supply = np.zeros((horizon,no_strategies))
    
    for t in model.T:
        for s in model.S:
            temp_demand[t-16][s-1] = round(value(model.da_b_p[s,t]), 4)
            temp_supply[t-16][s-1] = round(value(model.da_o_p[s,t]), 4)
    
    average_demand_prob[j] = (temp_demand + average_demand_prob[j])/2
    average_demand_prob[j] =average_demand_prob[j].round(4)
    average_supply_prob[j] = (temp_supply + average_supply_prob[j])/2
    average_supply_prob[j] = average_supply_prob[j].round(4)
    
    total_demand_prob[j] += temp_demand
    total_supply_prob[j] += temp_supply
    pass


check=False
no_iteration =5

print("\n\n********** Starting FICTITIOUS PLAY algortihm ********")
for n in range(no_iteration):
    
    print("********************* round {} *******************".format(n+1))
    
    for j in range(1,ncda+2):
        
        IN_loads, profiles = load_data(str(j))
               
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
        # offers_bid , demand_bid = random_offer(ncda, horizon)
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
                        c_DA_o, c_DA_b, DA_solar_power[j-1],
                        no_strategies, demand_probability[j], supply_probability[j] )
       
        SOLVER_NAME="gurobi" # "gurobi"  #'cplex'
        solver=SolverFactory(SOLVER_NAME)
        results = solver.solve(model)
        
        # To check constraint feasibility after solving problem
        # check_constraints(model, Yline, B,dic_G, dic_Bus_CDA, DABus, c_g, dic_G_Bus, dic_CDA_Bus, 
        #                   c_d_o[j-1], c_d_b[j-1], c_DA_o, c_DA_b, 1000, 1000, g_s, F_d_o, F_d_b, FMAX )
        
        #print(results)
        
        solver_time=time.time()-solver_time

        if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
            print('Model solved and is optimal for DA:',j,'   Time taken:', solver_time)
            # model_to_csv(model,IN_loads.sum(0))
            new_d_o, new_d_b = solved_model_bids(model)
            check_boundry(new_d_o, new_d_b, j)
            load_bids_probs(model, j)
            
        #     feasible_bid[j] =  new_d_b
        #     feasible_offer[j] = new_d_o
        # else:
        #     infeasibility_counter+=1
        #     infeasibility_counter_DA[j-1] += 1
        #     new_d_o = random_offer(ncda, horizon)[0][j]
        #     new_d_b = random_offer(ncda, horizon)[1][j]
        
        # new_offers[j]=new_d_o
        # new_bids[j]= new_d_b        
        
        update_offers_demands()
        

# Supply probability
for t in model.T:
    for s in model.S:
        print(value(model.da_b_p[s,t]),' ',end="")
    print()

# demand probability
for t in model.T:
    for s in model.S:
        print(value(model.da_o_p[s,t]),' ',end="")
    print()
    
for t in model.T:
    print(value(model.DA_supply[t]))
    
    
for t in model.T:
    print(value(model.DA_demand[t]))