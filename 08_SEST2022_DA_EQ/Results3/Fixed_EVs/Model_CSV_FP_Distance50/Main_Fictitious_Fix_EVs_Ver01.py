# -*- coding: utf-8 -*-
"""
Created on Mon Dec 13 17:33:21 2021

@author: Alireza
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Oct  4 10:35:15 2021

@author: Alireza
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Jul 15 16:29:32 2021

@author: Alireza
"""
"""
% 6-Bus Network from EPSR paper
% Line No. | From Bus | To Bus | Susceptance (p.u.) | Capacity (MW)
%    1     |     1    |    2   |       5.8824       |     150
%    2     |     1    |    4   |       3.8760       |     150
%    3     |     2    |    3   |       27.027       |     150
%    4     |     2    |    4   |       5.0761       |      33
%    5     |     3    |    6   |       55.5556      |     150
%    6     |     4    |    5   |       27.0270      |     150
%    7     |     5    |    6   |       7.1429       |     150

% Generation Unit | Bus No.  
%         1       |    1     
%         2       |    2    
%         3       |    6    
%         4       |    6    

%  Competing DA | Bus No. 
%       1       |    3    
%       2       |    3 
%       3       |    3 
%       4       |    4    
%       5       |    4 
%       6       |    4 
%       7       |    5 
%       8       |    5 
%       9       |    5 

MVA=30
"""

import random
import time
import pandas as pd
import numpy as np
import collections
from csv import writer
from collections import Counter
import hashlib


from MPEC_Concrete_Model_ver05 import mpec_model as diag_model
from MPEC_Concrete_Model_ver05 import mpec_model
from pyomo.environ import *
from pyomo.opt import SolverFactory
from Model_to_CSV import model_to_csv, model_to_csv_iteration




def solved_model_bids(model):
    new_d_o=[]
    new_d_b=[]
    for t in model.T:
        # new_d_b.append(value(model.E_DA_L[t]))
        # new_d_o.append(value(model.E_DA_G[t]))
        new_d_b.append(round(value(model.E_DA_L[t]),6))
        new_d_o.append(round(value(model.E_DA_G[t]),6))
    return new_d_o, new_d_b



def compare_lists(old, new, epsilon):
    check=[]
    for i in range(len(old)):
        if abs(old[i]-new[i]) <= epsilon:
            check.append(True)
    return check
        

def check_bids(old, new, epsilon):
    check=False
    for key in old.keys():
        compare = compare_lists(old[key], new[key], epsilon)
        if np.sum(compare) == len(old[key]):
            check=True
        else:
            return False
    return check

def check_bids_dis_prob(file_name, curr_iter,distance, epsilon):
    if curr_iter < 1.5*distance:
        return False
    
    check = []
    for key in file_name:
        df_bids = pd.read_csv(file_name[key])
        bool_prob_diff = abs(df_bids[curr_iter-distance+1:curr_iter+1].sum()/distance - df_bids[curr_iter-int(1.5*distance)+1:curr_iter-int(0.5*distance)+1].sum()/distance) <= epsilon
        if sum(bool_prob_diff) == len(bool_prob_diff):
            check.append(True)
            print("DA"+str(key)+" Is reached to EQ ")
        else:
            check.append(False)
    
    if sum(check) == len(file_name.keys()):
        return True
    return False


def results_to_csv(data_pd, j_iter):
    data_pd['Time'] =[x for x in range(16,16+24)]
    data_pd['Iteration'] = j_iter
    if j_iter==0:
        # f = open('diagonalizaton_results.csv', "w")
        # f.truncate()
        # f.close()
        data_pd.to_csv('diagonalizaton_results.csv', header=True, mode='w')
    else:
        data_pd.to_csv('diagonalizaton_results.csv', header=False, mode='a') 
    pass
        
def dictionar_bus(GenBus, CDABus, DAs):
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
    count=1
    for i in range(len(CDABus)):
        if i+1 != DAs:
            dic_CDA_Bus[count] = CDABus[i][1]
            dic_Bus_CDA[CDABus[i][1]] = count
            count+=1
        else:
            dic_CDA_Bus['DAS'] = CDABus[i][1]
            dic_Bus_CDA[CDABus[i][1]] = 'DAS'
        # dic_CDA_Bus[i+1]=CDABus[DABus-1][i]
        # dic_Bus_CDA[CDABus[DABus-1][i]] = i+1
    
    # dic_CDA_Bus['DAS']=DABus     # Strategic Aggregator
    # dic_Bus_CDA[DABus] = 'DAS'   # Strategic Aggregator
    return dic_CDA_Bus, dic_Bus_CDA, dic_G, dic_G_Bus


def load_data(file_index):
    df1 = pd.read_csv('prosumers_data/inflexible_profiles_scen_'+file_index+'.csv').round(5)*load_multiply/100 #/1000
    # Just selecting some prosumers like 500 or 600 or 1000
    df1 = df1[:NO_prosumers]
    # print(df1.shape)
    df2 = pd.read_csv('prosumers_data/prosumers_profiles_scen_'+file_index+'.csv')
    df2 = df2[:NO_prosumers]
    
    return df1 , df2


gen_capacity =[100, 75, 50, 50]
# gen_capacity =[50000, 50000, 50000]

random.seed(42)

# Time Horizon
NO_prosumers=500
horizon=24
H = range(16,horizon+16)    
MVA = 30 # Power Base
PU_DA = 1/(100*MVA)
load_multiply = 20

# Number of strategies
no_strategies = 100 

nl = 7    # Number of network lines
nb = 6    # Number of network buses

FromBus = [1,1,2,2,3,4,5] # Vector with network lines' "sending buses"
ToBus = [2,4,3,4,6,5,6]   # Vector with network lines' "receiving buses"

LinesSusc = [5.8824, 3.8760, 27.0270, 5.0761, 55.5556, 27.0270, 7.1429]  #Vector with per unit susceptance of the network 
# LinesSusc = [5,6,7]

ng = 4    # Number of Generators
ncda = 8  # Number of competing 
ndas = 9  # Number of participant DAs

GenBus = [1,2,3,3]  # Vector with Generation Buses
CDABus = [[1, 6], [2,6],[3,6],[4,4],[5,4],[6,4],[7,5],[8,5],[9,5]]      # Vector with competing DAs Buses
DABus = 6           # DA Bus

FMAX = [150,150,150,33,150,150,150]
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
# LinesSusc = np.array(LinesSusc).transpose()
# Yline=LineFlows*LinesSusc


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
            temp_bid.append(round(random.random()/MVA, 6))  # Mega Watt
            temp_offer.append(round(random.random()/MVA,6)) # Mega Watt
            
                
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
c_g[1]=[15 for x in range(0,horizon)]
c_g[2]=[30 for x in range(0,horizon)]
c_g[3]=[60 for x in range(0,horizon)]
c_g[4]=[90 for x in range(0,horizon)]



#Price bid for supplying power of competing DA  i in time t
price_d_o=dict()
price_d_o['DAS']= random_price(horizon,12,15)

for i in range(1,ncda+1):
    price_d_o[i] = random_price(horizon,12,15)

c_d_o=[]
for i in range(ncda+1):
    c_d_o.append(price_d_o)
    
# c_d_o = [{'DAS':random_price(horizon,1,12), 1:random_price(horizon,1,12), 2:random_price(horizon,1,12)},
#           {'DAS':random_price(horizon,1,12), 1:random_price(horizon,1,12), 2:random_price(horizon,1,12)},
#           {'DAS':random_price(horizon,1,12), 1:random_price(horizon,1,12), 2:random_price(horizon,1,12)}]


# c_d_o = {'DAS':random_price(horizon,1,2),
#           1:random_price(horizon,1,2),
#           2:random_price(horizon,1,2)}


# Price bid for buying power of competing DA  i in horizon t
price_d_b=dict()
price_d_b['DAS']= random_price(horizon,70,110)

for i in range(1,ncda+1):
    price_d_b[i] = random_price(horizon,70,110)

c_d_b=[]
for i in range(ncda+1):
    c_d_b.append(price_d_b)
    
# c_d_b = [{'DAS':random_price(horizon,70,110),1:random_price(horizon,70,110), 2:random_price(horizon,70,110)},
#          {'DAS':random_price(horizon,70,110),1:random_price(horizon,70,110), 2:random_price(horizon,70,110)},
#          {'DAS':random_price(horizon,70,110),1:random_price(horizon,70,110), 2:random_price(horizon,70,110)}]



# Price bid for supplying power of strategic DA in horizon t
c_DA_o = c_d_o[DABus-1]['DAS'] # random_price(horizon)

# Price bid for buying power of strategic DA in horizon t
c_DA_b = c_d_b[DABus-1]['DAS'] # random_price(horizon)

# Supply offer of generator i in time t
g_s = { 1:[100 for x in range(0,horizon)],
        2:[75 for x in range(0,horizon)],
        3:[50 for x in range(0,horizon)],
        4:[50 for x in range(0,horizon)]}


# 2019 November 15 forecasted temprature
outside_temp=[16.784803,16.094803,15.764802,14.774801,14.834802,14.184802,14.144801,15.314801,16.694803,19.734802,24.414803,25.384802,26.744802,27.144802,27.524803,27.694803,26.834803,26.594803,25.664803,22.594803,21.394802,20.164803,19.584803,20.334803]
irrediance_nov = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 101.55, 237.82, 290.98, 224.05, 96.78, 141.85, 60.03, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

irrediance_nov = np.roll(irrediance_nov,-15)

irradiance_april = [0, 0, 0, 0, 0, 0, 211, 1200, 3188, 5954, 9317, 6609, 6178, 7082, 5790, 4117, 2321, 1399, 780, 186, 0, 0, 0, 0]
irradiance_april = np.roll(irradiance_april,-15)

# Adding solar power to randomly selected houses.
def solar_power_generator(index_len):
    return [random.random()*0.05 for i in range(index_len)]


# This function adds solar power into inflexible loads
# It is raplaced by adding new variable as solar power into model
def random_solar_power_var(in_loads, j):
    random.seed((j+2)**2)
    length = len(in_loads)
    # Select 20 percent of households containt solar power
    random_index = [random.randrange(1, length, 1) for i in range(int(length/4))]
    
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
# DA_solar_power =[]        
# for j in range(1,ncda+2):
#     IN_loads, profiles = load_data(str(j))
#     DA_solar_power.append(random_solar_power_var(IN_loads, j))


def random_solar_power_var(in_loads, j):
    random.seed((j+2)**2)
    length = len(in_loads)
    
    # Select 20 percent of households containt solar power
    random_index = [random.randrange(1, length, 1) for i in range(int(length/3))]
    
    #selected_time = ['16','17','18','19','30','31','32','33','34','35','36','37','38','39']
    selected_time = [16,17,18,19,30,31,32,33,34,35,36,37,38,39]
    
    solar_power = np.zeros(in_loads.shape)
    
    for i in range(len(selected_time)):
        random_power = solar_power_generator(len(random_index))
        counter = 0
        for j in random_index:
            solar_power[j,selected_time[i]-16] = random_power[counter]
            counter +=1
    
    return solar_power

# # List of solar powers
# DA_solar_power =[]        
# for j in range(1,ncda+2):
#     IN_loads, profiles = load_data(str(j))
#     DA_solar_power.append(random_solar_power_var(IN_loads, j))



# Penetration of EVs in each strategic DA prosumers
# Select EVs for scheduling
EVs_penetration=None
EVs_list = dict()


for j in range(1,ncda+2):
    if j %2 == 0:
        EVs_penetration=0.35
    elif j % 3== 0:
        EVs_penetration=0.35
    else:
        EVs_penetration=0.35
    # Adding random EVs for prosumers
    NO_of_EVs = int(EVs_penetration * NO_prosumers)
    EVs_list[j] = random.choices([i+1 for i in range(NO_prosumers)],k=NO_of_EVs )

# Solar power penetration.
Solar_penetration= None
Solar_list=dict()

for j in range(1,ncda+2):
    if j % 2 == 0:
        Solar_penetration=0.50
    elif j % 3 == 0:
        Solar_penetration=0.30
    else:
        Solar_penetration=0.20
    # Adding random solar panels to prosumers
    NO_solar_prosumers = int(Solar_penetration * NO_prosumers)
    Solar_list[j] = random.choices([i+1 for i in range(NO_prosumers)],k=NO_solar_prosumers )


def random_irrediance_solar_power(irrediance, in_loads, j, solar_list):
    random.seed((j+2)**2)
    length = len(in_loads)
    
    
    solar_power = np.zeros(in_loads.shape)
    
    for da in solar_list[j]:
        for i in range(horizon):
            area = random.choice([1,2])
            solar_power[da-1,i] = 0.000157 * area * irrediance[i] * (1 - 0.001*random.random()* (outside_temp[i]-25))*load_multiply
    
    return solar_power
        
# List of solar powers
DA_solar_power =[]        
for j in range(1,ncda+2):
    IN_loads, profiles = load_data(str(j))
    DA_solar_power.append(random_irrediance_solar_power(irrediance_nov, IN_loads, j, Solar_list))
    
"""
Solve once and find range for offers and bids
using diagonalization method
"""

check=False
no_iteration = 3
rate=0.01  #learning rate like gradient descent
infeasibility_counter_DA =[0,0,0]
timestr = time.strftime("%Y%m%d-%H%M%S")

temp_bid = demand_bid 
temp_offer = offers_bid

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
        charge_power = profiles['EV_Power']*load_multiply
        EV_soc_low   = profiles['EV_soc_low']*load_multiply
        EV_soc_up   = profiles['EV_soc_up']*load_multiply
        EV_soc_arrive = profiles['EV_soc_arr']*load_multiply
        EV_demand = profiles['EV_demand']*load_multiply
        
                
        # Shiftable loads
        SL_loads=[]
        SL_loads.append(profiles['SL_loads1']*load_multiply/10)
        SL_loads.append(profiles['SL_loads2']*load_multiply/10)
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

        DABus=CDABus[j-1][1]
        # offers_bid , demand_bid = random_offer(ncda, horizon)
        F_d_o, F_d_b = select_bid(j, offers_bid, demand_bid)
        
        #F_d_b = demand_bid[j-1]
        
        # Price bid for supplying power of strategic DA in time t
        c_DA_o = c_d_o[CDABus[j-1][0]-1]['DAS'] # random_price(time)
        
        # Price bid for buying power of strategic DA in time t
        c_DA_b = c_d_b[CDABus[j-1][0]-1]['DAS'] # random_price(time)        
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
                        EVs_list[j], Solar_list[j])
       
        SOLVER_NAME="gurobi"  #'cplex'
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
    # # Step 4 check if epsilon difference exist
    # for key in new_offers:
    #     zipped_lists = zip(offers_bid[key], new_offers[key])
    #     sum_zip =  [round((x + y+max(new_offers[key])),6) for (x, y) in zipped_lists]
    #     offers_bid[key] = sum_zip
        
    #     zipped_lists = zip(demand_bid[key], new_bids[key])
    #     sum_zip =  [round((x + y+ max(new_bids[key])),6) for (x, y) in zipped_lists]
    #     demand_bid[key] = sum_zip
    
    for key in new_offers:
       zipped_lists = zip(temp_offer[key], new_offers[key])
       sum_zip =  [round((x + y+max(new_offers[key])),6) for (x, y) in zipped_lists]
       temp_offer[key] = sum_zip
       
       zipped_lists = zip(temp_bid[key], new_bids[key])
       sum_zip =  [round((x + y+ max(new_bids[key])),6) for (x, y) in zipped_lists]
       temp_bid[key] = sum_zip
    
    offers_bid = new_bids
    demand_bid = new_offers



offers_bid =temp_offer
demand_bid = temp_bid

for key in new_offers:
    offers_bid[key] =[x*10 for x in offers_bid[key]]
    #demand_bid[key]  =[x*2 for x in demand_bid[key]]
    
    
"""
going for FICTITIOUS PLAY algortihm
"""
# Discretizing offers and bids
discrete_bid = dict()
discrete_offer = dict()

# Create dictionary for each strategic DA counting it's discrete value
def make_discrte_value(step):
     
    for i in range(1, ncda+2):
        discrete_bid[i]={}
        discrete_offer[i]={}
        max_offer_t = max(offers_bid[i])
        max_bid_t = max(demand_bid[i])
        offers_temp = dict()
        demand_temp= dict()
        
        for t in range(horizon):
            offers_temp[t] = {}
            demand_temp[t] = {}
            offers = np.linspace(0, (offers_bid[i][t]+max_offer_t)*3, step).tolist()
            offers = np.around(offers, 6)
            
            demands = np.linspace(0, (demand_bid[i][t]*max_bid_t)*3, step).tolist()
            demands = np.around(demands, 6)
            
            offers_temp[t][(0,0)] = 0
            demand_temp[t][(0,0)] = 0
            for value in range(step-1):
                offers_temp[t][(offers[value], offers[value+1])] = 0
                demand_temp[t][(demands[value], demands[value+1])] = 0
        
        discrete_bid[i] = demand_temp
        discrete_offer[i] = offers_temp
    pass
# Calling this function to make values discrete
make_discrte_value(no_strategies)

# Discretize not based on strategies but based on epsilon difference
def make_epsilon_discrete_value(epsilon):
    for i in range(1, ncda+2):
        discrete_bid[i]={}
        discrete_offer[i]={}
        max_offer_t = max(offers_bid[i])
        max_bid_t = max(demand_bid[i])
        offers_temp = dict()
        demand_temp= dict()
        
        for t in range(horizon):
            offers_temp[t] = {}
            demand_temp[t] = {}
            offers = np.arange(0, (offers_bid[i][t]+max_offer_t)*2, epsilon).tolist()
            # offers = np.arange(0, offers_bid[i][t], epsilon).tolist()
            offers = np.around(offers, 6)
            
            demands = np.arange(0, (demand_bid[i][t]+max_bid_t), epsilon).tolist()
            # demands = np.arange(0, demand_bid[i][t], epsilon).tolist()
            demands = np.around(demands, 6)
            
            offers_temp[t][(0,0)] = 0
            demand_temp[t][(0,0)] = 0
            for v in range(len(offers)-1):
                offers_temp[t][(offers[v], offers[v+1])] = 0
        
            for v in range(len(demands)-1):
                demand_temp[t][(demands[v], demands[v+1])] = 0
            
        discrete_bid[i] = demand_temp
        discrete_offer[i] = offers_temp
    pass

make_epsilon_discrete_value(0.01)

# After each iteration update discrete offers and bids by counting them
def check_boundry(new_d_o, new_d_b, j):
    bid_action = np.zeros((horizon,no_strategies), dtype=np.int8)
    offer_action= np.zeros((horizon,no_strategies), dtype=np.int8)
    
    # Check number of boundaries become true
    check_found_boundary = np.zeros(len(new_d_o))

    for i in range(len(new_d_o)):
        count_row=0
        for key in discrete_offer[j][i]:
            if new_d_o[i] == 0.0:
                discrete_offer[j][i][(0,0)] += 1
                offer_action[i,count_row]=1
                check_found_boundary[i] = 1
                break
            elif new_d_o[i] > key[0] and new_d_o[i]<= key[1]:
                discrete_offer[j][i][key] += 1
                offer_action[i,count_row]=1 
                check_found_boundary[i] = 1
            count_row+=1 
    
    if sum(check_found_boundary) != len(new_d_o):
        print('\n !!!!!!!! Problem in  offer boundary !!!!!!!!!!', sum(check_found_boundary))
        # print(offer_action)
    
    # Check number of boundaries become true
    check_found_boundary = np.zeros(len(new_d_o))
    
    for i in range(len(new_d_b)):
        count_row=0
        for key in discrete_bid[j][i]:
            if new_d_b[i] == 0.0:
                discrete_bid[j][i][(0,0)] += 1
                bid_action[i,count_row]=1
                check_found_boundary[i] = 1
                break
            elif new_d_b[i] > key[0] and new_d_b[i]<= key[1]:
                discrete_bid[j][i][key] += 1
                bid_action[i,count_row]=1
                check_found_boundary[i] = 1
            count_row+=1 
    if sum(check_found_boundary) != len(new_d_o):
        print('\n !!!!!!!! Problem in bid boundary !!!!!!!!!!', sum(check_found_boundary))
        # print(bid_action)
        
    return bid_action.flatten(), offer_action.flatten()

def check_epsilon_boundry(new_d_o, new_d_b, j):
    
    bid_action = []
    offer_action= []
    # Check number of boundaries become true
    check_found_boundary = np.zeros(len(new_d_o))
    
    for i in range(len(new_d_o)):
        count_row=0
        offer_action_row = np.zeros(len(discrete_offer[j][i]))
        for key in discrete_offer[j][i]:
            if new_d_o[i] == 0.0:
                discrete_offer[j][i][(0,0)] += 1
                offer_action_row[count_row]=1
                check_found_boundary[i] = 1
                break
            elif new_d_o[i] > key[0] and new_d_o[i]<= key[1]:
                discrete_offer[j][i][key] += 1
                offer_action_row[count_row]=1
                # offer_action[i,count_row]=1 
                check_found_boundary[i] = 1
            count_row+=1
        for value in offer_action_row.tolist():
            offer_action.append(value)
    
    if sum(check_found_boundary) != len(new_d_o):
        print('\n !!!!!!!! Problem in  offer boundary !!!!!!!!!!', sum(check_found_boundary))
        # print(offer_action)
    
    # Check number of boundaries become true
    check_found_boundary = np.zeros(len(new_d_o))
    
    for i in range(len(new_d_b)):
        count_row=0
        bid_action_row = np.zeros(len(discrete_bid[j][i]))
        for key in discrete_bid[j][i]:
            if new_d_b[i] == 0.0:
                discrete_bid[j][i][(0,0)] += 1
                bid_action_row[count_row] = 1
                # bid_action[i,count_row]=1
                check_found_boundary[i] = 1
                break
            elif new_d_b[i] > key[0] and new_d_b[i]<= key[1]:
                discrete_bid[j][i][key] += 1
                # bid_action[i,count_row]=1
                bid_action_row[count_row] = 1
                check_found_boundary[i] = 1
            count_row+=1
        for value in bid_action_row.tolist():
            bid_action.append(value)
    if sum(check_found_boundary) != len(new_d_o):
        print('\n !!!!!!!! Problem in bid boundary !!!!!!!!!!', sum(check_found_boundary))
        # print(bid_action)
        
    return np.array(bid_action), np.array(offer_action)
    pass
    
# hash function to unique id for each action with zero or one
# Needs: python -m pip install numpy xxhash
def array_id(a, *, include_dtype = False, include_shape = False, algo = 'sha256'):
    data = bytes()
    if include_dtype:
        data += str(a.dtype).encode('ascii')
    data += b','
    if include_shape:
        data += str(a.shape).encode('ascii')
    data += b','
    data += a.tobytes()
    if algo == 'sha256':
        #import hashlib
        return hashlib.sha256(data).hexdigest().upper()
    else:
        assert False, algo
    
    pass

# After finishing inner iteration for solving MPECs and updating boundry
# Before next round update ooffers and demands based on prbability
# of discrete values 
def update_offers_demands_by_prob(iter_n):
    
    for DA in offers_bid.keys():
        temp_d_o=[]
        for t in range(horizon):
            sum_BIDs=0
            for BID in discrete_offer[DA][t]:
                prob = discrete_offer[DA][t][BID]/iter_n
                sum_BIDs += prob*BID[1]
            temp_d_o.append(sum_BIDs)
        offers_bid[DA]=temp_d_o
    
    for DA in demand_bid.keys():
        temp_d_b=[]
        for t in range(horizon):
            sum_BIDs=0
            for BID in discrete_bid[DA][t]:
                prob = discrete_bid[DA][t][BID]/iter_n
                sum_BIDs += prob*BID[1]
            temp_d_b.append(sum_BIDs)
        demand_bid[DA] = temp_d_b
    pass
        
               
# Update offers_bid, demand_bid dictionaries
def keywithmaxval(d):
     """ a) create a list of the dict's keys and values; 
         b) return the key with the max value"""  
     v=list(d.values())
     k=list(d.keys())
     return k[v.index(max(v))]
 
def update_offers_demands():
    rate=0.001
    for key in discrete_bid.keys():
        temp_d_o = [] #offers_bid[key]
        temp_d_b = [] #demand_bid[key]
        for i in range(horizon):
            max_key_d_b = keywithmaxval(discrete_bid[key][i])
            max_key_d_o = keywithmaxval(discrete_offer[key][i])
            temp_d_b.append((max_key_d_b[0]*rate + max_key_d_b[1]*(1-rate)))
            temp_d_o.append((max_key_d_o[0]*rate + max_key_d_o[1]*(1-rate)))
        
        # Updarte demand and offer bids
        offers_bid[key] = np.around(temp_d_o,4)
        demand_bid[key] = np.around(temp_d_b,4)
    pass

def select_best_action(j, objective_function, ncda, n_iteration ):
    
    df_obj = pd.read_csv('diagonalizaton_results.csv')
    counter= 1
    count=1
    
    d_o=dict()
    d_b=dict()
    for i in range(ncda+1):
        if counter != j:
            min_obj_index = np.argmin(objective_function[counter][1:n_iteration])+1
            
            print('min offer=', min_obj_index, '   min_demand=',min_obj_index)
            
            temp_offer = df_obj['offer_0'+str(counter)][df_obj.Iteration == min_obj_index].tolist()
            temp_bid = df_obj['bids_0'+str(counter)][df_obj.Iteration == min_obj_index].tolist()
            
            # print(i)
            # temp_offer = offers_bid[i+1]
            # temp_bid   = demand_bid[i+1]
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

feasible_bid = dict()
feasible_offer = dict()

check=False
no_iteration = 300
epsilon= 0.01
# distance between current iteration and it's prevoius probabilities
# FOR every bid "b" in D: Set the probability_of_b  = (times that "b" was played in epochs 901 - 1000) / 100
# Set the PREVIOUS_probability_of_b = (times that "b" was played in epochs 851 - 950) / 100
# then:
# IF for every bid "b" in D, it is:
#       | probability_of_b - PREVIOUS_probability_of_b | < epsilon   
#            THEN we say that the algorithm has converged to an epsilon-CCEquilibrium 
distance = 50
infeasibility_counter=0
infeasibility_counter_DA =[0,0,0]
objective_function = dict()

# store action selection in action history
# at each iteration which action vector is used
action_history = np.zeros((ncda+1,no_iteration))

# Store number of acction played by looking into it's hash action dictionary
# Check action_hash_set dictionary below to find number of action based on hash a1, a2, ...
action_played=dict()


# Store hash of the vectore and it's corresponding label as action number
action_hash_set = dict()
for j in range(1,ncda+2):
    action_hash_set[j]=dict()

# Store counter of occurance for each hashed action
action_hash_count = dict()
for j in range(1,ncda+2):
    action_hash_count[j]=dict()


# Store action vectores in ditionaries
file_name_bid=dict()
for key in discrete_bid.keys():
    file_name_bid[key] = "Model_CSV/discrete_bid_DA"+str(key)+"_"+timestr+".csv"
    temp_bid=[]
    for t in discrete_bid[key].keys():
        for BID in discrete_bid[key][t]:
            temp_bid.append(BID[1])
    with open(file_name_bid[key],'w', newline='') as file:          
        csv_writer = writer(file)
        csv_writer.writerow(temp_bid)

# Store action vectores in ditionaries
file_name_offer=dict()
for key in discrete_offer.keys():
    file_name_offer[key] = "Model_CSV/discrete_offer_DA"+str(key)+"_"+timestr+".csv"
    temp_bid=[]
    for t in discrete_offer[key].keys():
        for BID in discrete_offer[key][t]:
            temp_bid.append(BID[1])
    with open(file_name_offer[key],'w', newline='') as file:          
        csv_writer = writer(file)
        csv_writer.writerow(temp_bid)


# Count number of discrete actions played by each DA
counter_played_actions=np.zeros(ncda+1)

# Create DAs as agent number to shuffle before each round
DAs_list=[]
for j in range(1,ncda+2):
    DAs_list.append(j)


offers_bid , demand_bid = random_offer(ncda, horizon)


# Columns to be added into diag file results
['offer_01','offer_02','offer_03', 'bids_01','bids_02', 'bids_03']
dig_col=[]
for i in range(1,ncda+2):
    dig_col.append('offer_0'+str(i))

for i in range(1,ncda+2):
    dig_col.append('bids_0'+str(i))
    

print("\n\n********** Starting FICTITIOUS PLAY algortihm ********")
for n in range(no_iteration):
# for n in range(100, no_iteration):
    
    print("********************* start round {} *******************".format(n+1))
    
    # Shuffle Agents in th List
    random.shuffle(DAs_list)
    
    # for j in range(1,ncda+2):
    for j in DAs_list:
        
        IN_loads, profiles = load_data(str(j))
               
        # EVs properties 
        arrival = profiles['Arrival']
        depart  = profiles['Depart']
        charge_power = profiles['EV_Power']*load_multiply
        EV_soc_low   = profiles['EV_soc_low']*load_multiply
        EV_soc_up   = profiles['EV_soc_up']*load_multiply
        EV_soc_arrive = profiles['EV_soc_arr']*load_multiply
        EV_demand = profiles['EV_demand']*load_multiply
        
                
        # Shiftable loads
        SL_loads=[]
        SL_loads.append(profiles['SL_loads1']*load_multiply/10)
        SL_loads.append(profiles['SL_loads2']*load_multiply/10)
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

        # DABus=j
        DABus=CDABus[j-1][1]
        # offers_bid , demand_bid = random_offer(ncda, horizon)
        F_d_o, F_d_b = select_bid(j, offers_bid, demand_bid)
        
        #F_d_b = demand_bid[j-1]
        
        # Price bid for supplying power of strategic DA in time t
        c_DA_o = c_d_o[CDABus[j-1][0]-1]['DAS'] # random_price(time)
        
        # Price bid for buying power of strategic DA in time t
        c_DA_b = c_d_b[CDABus[j-1][0]-1]['DAS'] # random_price(time)
        
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
                        EVs_list[j], Solar_list[j])
       
        SOLVER_NAME="gurobi"  #'cplex'
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
            model_to_csv_iteration(model, IN_loads.sum(0), n, str(j), timestr, EVs_list[j], load_multiply*PU_DA)
            new_d_o, new_d_b = solved_model_bids(model)
            # bid_action_vec, offer_action_vec = check_boundry(new_d_o, new_d_b, j)
            bid_action_vec, offer_action_vec = check_epsilon_boundry(new_d_o, new_d_b, j)
            feasible_bid[j] =   new_d_b
            feasible_offer[j] = new_d_o
            
            if j in objective_function.keys():
                objective_function[j].append(value(model.obj))
            else:
                objective_function[j] = [value(model.obj)]
            
            #  # Create hash bid
            # hash_bid = array_id(bid_action_vec)
            
            # # If hash bid exist it's not unique action otherwise it's unique
            # if hash_bid in action_hash_set[j].keys():
            #     action_hash_count[j][hash_bid]+=1
            #     if j in action_played.keys():
            #         action_played[j].append(action_hash_set[j][hash_bid])
            #     else:
            #         action_played[j]=[action_hash_set[j][hash_bid]]
            # else:
            #     counter_played_actions[j-1]+=1
            #     action_hash_count[j][hash_bid]=1
            #     action_hash_set[j][hash_bid] = counter_played_actions[j-1]
            #     if j in action_played.keys():
            #         action_played[j].append(counter_played_actions[j-1])
            #     else:
            #         action_played[j]=[counter_played_actions[j-1]]
            
            # Store action vectors in related files
            with open(file_name_bid[j],'a', newline='') as file:          
                csv_writer = writer(file)
                csv_writer.writerow(list(bid_action_vec))
            
            with open(file_name_offer[j],'a', newline='') as file:          
                csv_writer = writer(file)
                csv_writer.writerow(list(offer_action_vec))
        
        else:
             infeasibility_counter+=1
             infeasibility_counter_DA[j-1] += 1
             new_d_o = feasible_offer[j] # random_offer(ncda, horizon)[0][j]
             new_d_b = feasible_bid[j]   # random_offer(ncda, horizon)[1][j]
             objective_function[j].append('NAN')
     
        new_offers[j]=new_d_o
        new_bids[j]= new_d_b        
        
        # update_offers_demands()
        
    check=False
    # if check_bids(offers_bid,new_offers,epsilon) and check_bids(demand_bid,new_bids,epsilon) : # and (infeasibility_counter < ncda+1)
    #     check=True
    #     diag_df = pd.concat([pd.DataFrame.from_dict(new_offers), pd.DataFrame.from_dict(new_bids)], axis=1)
    #     diag_df.columns = dig_col
    #     results_to_csv(diag_df, n)
    #     print("solution found in bids epsilon difference iteration:",n+1)
    #     break
    # else:
    #     # print(pd.concat([pd.DataFrame.from_dict(offers_bid), pd.DataFrame.from_dict(new_offers)], axis=1))
    #     # print(pd.concat([pd.DataFrame.from_dict(demand_bid), pd.DataFrame.from_dict(new_bids)], axis=1))
    #     #print(pd.concat([pd.DataFrame.from_dict(new_offers), pd.DataFrame.from_dict(new_bids)], axis=1))
    #     # saving results of the iterations
    #     diag_df = pd.concat([pd.DataFrame.from_dict(new_offers), pd.DataFrame.from_dict(new_bids)], axis=1)
    #     diag_df.columns = dig_col
    #     results_to_csv(diag_df, n)
        
        # print('\nno EPEC, End of round:',n+1,'\n********************')
    
    # update offers and bids
    update_offers_demands_by_prob(n+1)
    
    if n>=1.5*distance and check_bids_dis_prob(file_name_offer,n,distance, epsilon) and check_bids_dis_prob(file_name_offer,n,distance, epsilon):
        check=True
        diag_df = pd.concat([pd.DataFrame.from_dict(new_offers), pd.DataFrame.from_dict(new_bids)], axis=1)
        diag_df.columns = dig_col
        results_to_csv(diag_df, n)
        print("solution found in probability epsilon difference iteration:",n+1)
        break
    else:
        diag_df = pd.concat([pd.DataFrame.from_dict(new_offers), pd.DataFrame.from_dict(new_bids)], axis=1)
        diag_df.columns = dig_col
        results_to_csv(diag_df, n)
        print('\nno EPEC, End of round:',n+1,'\n********************')
    
    
    # if (n < no_iteration-1): # (not check) and
    #     for key in new_offers:
    #         zipped_lists = zip(offers_bid[key], new_offers[key])
    #         sum_zip =  [y*rate + (1-rate)*x for (x, y) in zipped_lists]
    #         offers_bid[key] = sum_zip
            
    #         zipped_lists = zip(demand_bid[key], new_bids[key])
    #         sum_zip =  [y*rate + (1-rate)*x for (x, y) in zipped_lists]
    #         demand_bid[key] = sum_zip
            

# save model objective function results
pd.DataFrame.from_dict(objective_function).to_csv('Model_CSV/objective_'+timestr+'.csv', index=False)

# pd.DataFrame.from_dict(action_hash_set).to_csv('Model_CSV/Action_hash_set_'+timestr+'.csv', index=False)

# pd.DataFrame.from_dict(action_hash_count).to_csv('Model_CSV/Action_hash_count_'+timestr+'.csv', index=False)

# pd.DataFrame.from_dict(action_played).to_csv('Model_CSV/Action_hash_played_'+timestr+'.csv', index=False)


with open('Model_CSV/EVs_list_'+timestr+'.csv','w', newline='') as file:          
    csv_writer = writer(file)
    for j in EVs_list.keys():
        csv_writer.writerow(EVs_list[j])

with open('Model_CSV/Solar_list_'+timestr+'.csv','w', newline='') as file:          
    csv_writer = writer(file)
    for j in EVs_list.keys():
        csv_writer.writerow(Solar_list[j])


if check:
    print('Solution is found:')
    print(pd.DataFrame.from_dict(offers_bid))
    print(pd.DataFrame.from_dict(demand_bid))
    # print("Offers differences:")
    # print(pd.DataFrame.from_dict(offers_bid) - pd.DataFrame.from_dict(feasible_offer))
    # print("Bid Differences:")
    # print(pd.DataFrame.from_dict(demand_bid) - pd.DataFrame.from_dict(feasible_bid))
else:
    print('No EPEC is found')
    print("Offers differences:")
    print(pd.DataFrame.from_dict(offers_bid) - pd.DataFrame.from_dict(feasible_offer))
    print("Bid Differences:")
    print(pd.DataFrame.from_dict(demand_bid) - pd.DataFrame.from_dict(feasible_bid))


# with open('DA_Bilevel.txt', 'w') as f:
#     f.write("Description of the Bilevel model for strategic day ahead aggregator:\n")
#     model.display(ostream=f)

# with open('DA_Bilevel_pprint.txt', 'w') as f:
#     f.write("Description of the Bilevel model for strategic day ahead aggregator:\n")
#     model.pprint(ostream=f)