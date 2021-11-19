# -*- coding: utf-8 -*-
"""
Created on Fri Oct  8 12:15:07 2021

@author: Alireza
"""

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
from csv import writer
# from samples_gen import generate_price, generate_temp
#from MPEC_Concrete_Model_ver01 import mpec_model
from MPEC_Concrete_Model_ver06 import mpec_model
from pyomo.environ import *
from pyomo.opt import SolverFactory

from Model_to_CSV import model_to_csv, model_to_csv_iteration
# from Model_Constraints import check_constraints


def solved_model_bids(model):
    new_d_o=[]
    new_d_b=[]
    for t in model.T:
        # new_d_b.append(value(model.E_DA_L[t]))
        # new_d_o.append(value(model.E_DA_G[t]))
        new_d_b.append(round(value(model.E_DA_L[t]),6))
        new_d_o.append(round(value(model.E_DA_G[t]),6))
    return np.array(new_d_o), np.array(new_d_b)



def compare_lists(old, new, epsilon):
    check=[]
    for i in range(len(old)):
        if abs(old[i]-new[i]) < epsilon:
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
            

def results_to_csv(data_pd, j_iter):
    data_pd['Time'] =[x for x in range(16,16+24)]
    data_pd['Iteration'] = j_iter
    if j_iter==0:
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


gen_capacity =[152,152,350,591,60,155,155,400,400,300,310,350]
# gen_capacity =[50000, 50000, 50000]

random.seed(42)

# Time Horizon
NO_prosumers=20
epsilon= 0.01
horizon=24
H = range(16,horizon+16)    
MVA = 100 # Power Base
PU_DA = 1/(1000*MVA)
load_multiply=200

nl = 34    # Number of network lines
nb = 24    # Number of network buses

FromBus = [1,1,1,2,2,3,3,4,5,6,7,8,8,9,9,10,10,11,11,12,12,13,14,15,15,15,16,16,17,17,18,19,20,21] # Vector with network lines' "sending buses"
ToBus = [2,3,5,4,6,9,24,9,10,10,8,9,10,11,12,11,12,13,14,13,23,23,16,16,21,24,17,19,18,22,21,20,23,22]   # Vector with network lines' "receiving buses"

LinesSusc = [68.49315068,4.438526409,11.02535832,7.374631268,4.87804878,7.867820614,11.9047619,9.009009009,
             10.63829787,15.57632399,15.33742331,5.675368899,5.675368899,11.9047619,11.9047619,11.9047619,
             11.9047619,20.49180328,23.4741784,20.49180328,10.15228426,11.31221719,16.83501684,58.13953488,
             40.16064257,18.90359168,38.02281369,42.73504274,69.93006993,9.35453695,75.75757576,
             49.26108374,89.28571429,14.45086705]  #Vector with per unit susceptance of the network 

LinesSusc = [round(x,4) for x in LinesSusc]
# LinesSusc = [5,6,7]

ng = 10   # Number of Generators
ncda = 16  # Number of competing 
ndas = 17  # Number of participant DAs

GenBus = [1,2,7,13,15,16,18,21,22,23]  # Vector with Generation Buses
# [1,2,3,4,5,6,7,8,9,10,13,14,15,16,18,19,20]
CDABus = [[1, 1], [2,2],[3,3],[4,4],[5,5],[6,6],[7,7],[8,8],[9,9],[10,10],[11,13],[12,14],[13,15],[14,16],[15,18],[16,19],[17,20]]      # Vector with competing DAs Buses
DABus = 1           # DA Bus

FMAX = [175,175,350,175,175,175,400,175,350,175,350,175,175,400,400,400,400,500,500,500,500,200,250,500,400,500,500,500,500,500,1000,1000,1000,500]
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

c_g[1]=[16 for x in range(0,horizon)]
c_g[2]=[19 for x in range(0,horizon)]
c_g[3]=[25 for x in range(0,horizon)]
c_g[4]=[100 for x in range(0,horizon)]

price_g =16
for g in range(len(GenBus)):
    c_g[g+1] = [price_g + price_g*(g+0.5) for x in range(0,horizon)]


#Price bid for supplying power of competing DA  i in time t
price_d_o=dict()
price_d_o['DAS']= random_price(horizon,12,15)

for i in range(1,ncda+1):
    price_d_o[i] = random_price(horizon,12,15)

c_d_o=[]
for i in range(ncda+1):
    c_d_o.append(price_d_o)


# Price bid for buying power of competing DA  i in horizon t
price_d_b=dict()
price_d_b['DAS']= random_price(horizon,70,110)

for i in range(1,ncda+1):
    price_d_b[i] = random_price(horizon,70,110)

c_d_b=[]
for i in range(ncda+1):
    c_d_b.append(price_d_b)



# Price bid for supplying power of strategic DA in horizon t
c_DA_o = c_d_o[DABus-1]['DAS'] # random_price(horizon)

# Price bid for buying power of strategic DA in horizon t
c_DA_b = c_d_b[DABus-1]['DAS'] # random_price(horizon)

# Supply offer of generator i in time t
g_s = { 1:random_generation(horizon,10, 12),
        2:random_generation(horizon,5, 10),
        3:random_generation(horizon,15, 20),
        4:random_generation(horizon,1, 50)}


for g in range(len(GenBus)):
    g_s[g+1] = random_generation(horizon,int(gen_capacity[g]/2), gen_capacity[g])

# 2019 November 15 forecasted temprature
outside_temp=[27.694803,26.834803,26.594803,25.664803,22.594803,21.394802,20.164803,19.584803,20.334803,16.784803,16.094803,15.764802,14.774801,14.834802,14.184802,14.144801,15.314801,16.694803,19.734802,24.414803,25.384802,26.744802,27.144802,27.524803]


irrediance_nov = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 101.55, 237.82, 290.98, 224.05, 96.78, 141.85, 60.03, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

irrediance_nov = np.roll(irrediance_nov,-15)

irradiance_april = [0, 0, 0, 0, 0, 0, 211, 1200, 3188, 5954, 9317, 6609, 6178, 7082, 5790, 4117, 2321, 1399, 780, 186, 0, 0, 0, 0]
irradiance_april = np.roll(irradiance_april,-15)


# outside_temp = [i+1 for i in outside_temp]

feasible_bid = dict()
feasible_offer = dict()

# Adding solar power to randomly selected houses.
def solar_power_generator(index_len):
    return [random.random()*0.05 for i in range(index_len)]
    
    
    
# This function adds solar power into inflexible loads
# It is raplaced by adding new variable as solar power into model
def random_solar_power(in_loads, j):
    random.seed((j+2)**2)
    length = len(in_loads)
    # Select 20 percent of households containt solar power
    random_index = [random.randrange(1, length, 1) for i in range(int(length/3))]
    
    selected_time = ['16','17','18','19','30','31','32','33','34','35','36','37','38','39']
    
    for i in range(len(selected_time)):
        random_power = solar_power_generator(len(random_index))
        in_loads.loc[random_index,selected_time[i]]= in_loads.loc[random_index,selected_time[i]]-random_power
        
    return in_loads

    
feasible_bid = dict()
feasible_offer = dict()


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


# List of solar powers
DA_solar_power =[]        
for j in range(1,ncda+2):
    IN_loads, profiles = load_data(str(j))
    DA_solar_power.append(random_solar_power_var(IN_loads, j))
    
 



# Penetration of EVs in each strategic DA prosumers
# Select EVs for scheduling
EVs_penetration=None
EVs_list = dict()


for j in range(1,ncda+2):
    if j %2 == 0:
        EVs_penetration=0.75
    elif j % 3== 0:
        EVs_penetration=0.50
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
    DA_solar_power.append(random_irrediance_solar_power(irradiance_april, IN_loads, j, Solar_list)) # changed from irradiance_nov


# Create DAs as agent number to shuffle before each round
DAs_list=[]
for j in range(1,ncda+2):
    DAs_list.append(j)


objective_function = dict()



check=False
no_iteration = 3
rate=0.01  #learning rate like gradient descent
infeasibility_counter_DA =[0*i for i in range(ncda+1) ]
timestr = time.strftime("%Y%m%d-%H%M%S")


dig_col=[]
for i in range(1,ncda+2):
    dig_col.append('offer_0'+str(i))

for i in range(1,ncda+2):
    dig_col.append('bids_0'+str(i))

print("Running diagonalization Method")
for n in range(no_iteration+1):
    new_offers=dict()
    new_bids=dict()
    infeasibility_counter=0
    
    print("********************* start round {} *******************".format(n+1))
    
    
    for j in range(1,ncda+2):
        
        
        
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
        
        # model = mpec_model(ng, nb, nl, ncda,IN_loads, gen_capacity, 
        #                 arrival, depart, charge_power,EV_soc_arrive,EV_soc_low, EV_soc_up, 
        #                 TCL_Max, TCL_R, TCL_Beta, TCL_temp_low, outside_temp, 
        #                 SL_low, SL_up, SL_cycle, SL_loads,
        #                 dic_G, dic_Bus_CDA, DABus, B, Yline, dic_G_Bus, 
        #                 c_g, c_d_o[j-1], c_d_b[j-1], 
        #                 dic_CDA_Bus, g_s, F_d_o, F_d_b, FMAX,
        #                 c_DA_o, c_DA_b, DA_solar_power[j-1],
        #                 EVs_list[j], Solar_list[j])
        model = mpec_model(ng, nb, nl, ncda,IN_loads, gen_capacity, 
                        arrival, depart, charge_power,EV_soc_arrive,EV_soc_low, EV_soc_up, 
                        TCL_Max, TCL_R, TCL_Beta, TCL_temp_low, outside_temp, 
                        SL_low, SL_up, SL_cycle, SL_loads,
                        dic_G, dic_Bus_CDA, DABus, B, Yline, dic_G_Bus, 
                        c_g, c_d_o[j-1], c_d_b[j-1], 
                        dic_CDA_Bus, g_s, F_d_o, F_d_b, FMAX,
                        c_DA_o, c_DA_b, DA_solar_power[j-1],
                        EVs_list[j], Solar_list[j])
        
        
        SOLVER_NAME= "gurobi"  #'cplex'
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
            model_to_csv_iteration(model, IN_loads.sum(0), n, str(j), timestr, EVs_list[j],load_multiply)
            new_d_o, new_d_b = solved_model_bids(model)
            feasible_bid[j] =   new_d_b
            feasible_offer[j] = new_d_o
            
            if j in objective_function.keys():
                objective_function[j].append(value(model.obj))
            else:
                objective_function[j] = [value(model.obj)]
        else:
            infeasibility_counter+=1
            infeasibility_counter_DA[j-1] += 1
            new_d_o = feasible_offer[j] # random_offer(ncda, horizon)[0][j]
            new_d_b = feasible_bid[j]   # random_offer(ncda, horizon)[1][j]
            objective_function[j].append('NAN')
            
        
        new_offers[j]=new_d_o
        new_bids[j]= new_d_b
        
        
        
        # model_to_csv(model, IN_loads.sum(0))
        
        # Finishing Step 3
    # Step 4 check if epsilon difference exist
        
    # check=False
    if check_bids(offers_bid,new_offers,epsilon) and check_bids(demand_bid,new_bids,epsilon) and (infeasibility_counter < ncda+1):
        check=True
        print("solution found in iteration:",n)
        diag_df = pd.concat([pd.DataFrame.from_dict(new_offers), pd.DataFrame.from_dict(new_bids)], axis=1)
        diag_df.columns= dig_col
        results_to_csv(diag_df, n)
        break
    else:
        # print(pd.concat([pd.DataFrame.from_dict(offers_bid), pd.DataFrame.from_dict(new_offers)], axis=1))
        # print(pd.concat([pd.DataFrame.from_dict(demand_bid), pd.DataFrame.from_dict(new_bids)], axis=1))
        #print(pd.concat([pd.DataFrame.from_dict(new_offers), pd.DataFrame.from_dict(new_bids)], axis=1))
        # saving results of the iterations
        diag_df = pd.concat([pd.DataFrame.from_dict(new_offers), pd.DataFrame.from_dict(new_bids)], axis=1)
        diag_df.columns= dig_col
        results_to_csv(diag_df, n)
        
        print('\nno EPEC, End of round:',n+1,'\n******************')
        
    # Step 6
    
    # if j==3:
    #     break
    offers_bid = new_offers
    demand_bid = new_bids
    
        
    # if (not check) and (n < no_iteration-1):
    #     for j in range(1,ncda+2):
    #         offers_bid[j] = offers_bid[j]*rate + (1-rate)*new_offers[j]
    #         demand_bid[j] = demand_bid[j]*rate +(1-rate)*new_bids[j]
    
    # if (infeasibility_counter == ncda+1):
    #     offers_bid , demand_bid = random_offer(ncda, horizon)



# model_to_csv(model, IN_loads.sum(0))

# save model objective function results
pd.DataFrame.from_dict(objective_function).to_csv('Model_CSV/objective_'+timestr+'.csv', index=False)

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


# pd.concat([pd.DataFrame.from_dict(offers_bid), pd.DataFrame.from_dict(feasible_offer)], axis=1)
# pd.concat([pd.DataFrame.from_dict(demand_bid), pd.DataFrame.from_dict(feasible_bid)], axis=1)

"""
Check model feasibility after solving agents MPEC for first time
"""
# for j in range(1,ncda+2):
    
#     IN_loads, profiles = load_data(str(j))
        
#     # Adding random solar power
#     # if j == 1:
#     IN_loads = random_solar_power(IN_loads, j)
    
#     # EVs properties 
#     arrival = profiles['Arrival']
#     depart  = profiles['Depart']
#     charge_power = profiles['EV_Power']
#     EV_soc_low   = profiles['EV_soc_low']
#     EV_soc_up   = profiles['EV_soc_up']
#     EV_soc_arrive = profiles['EV_soc_arr']
#     EV_demand = profiles['EV_demand']/2
    
            
#     # Shiftable loads
#     SL_loads=[]
#     SL_loads.append(profiles['SL_loads1'])
#     SL_loads.append(profiles['SL_loads2'])
#     SL_low   = profiles['SL_low']
#     SL_up    = profiles['SL_up']
#     SL_cycle = len(SL_loads)
    
#     # Thermostatically loads
#     TCL_R   = profiles['TCL_R']
#     TCL_C   = profiles['TCL_C']
#     TCL_COP = profiles['TCL_COP']
#     TCL_Max = profiles['TCL_MAX']
#     TCL_Beta= profiles['TCL_Beta']
#     TCL_temp_low = profiles['TCL_temp_low']
#     TCL_temp_up  = profiles['TCL_temp_up']

#     # Creating dictionary mapping current DA as strategic in MPEC model
#     dic_CDA_Bus, dic_Bus_CDA, dic_G, dic_G_Bus = dictionar_bus(GenBus, CDABus, j)

#     DABus=j
#     # offers_bid , demand_bid = random_offer(ncda, horizon)
#     F_d_o, F_d_b = select_bid(j, offers_bid, demand_bid)
    
#     #F_d_b = demand_bid[j-1]
    
#     # Price bid for supplying power of strategic DA in time t
#     c_DA_o = c_d_o[DABus-1]['DAS'] # random_price(time)
    
#     # Price bid for buying power of strategic DA in time t
#     c_DA_b = c_d_b[DABus-1]['DAS'] # random_price(time)
    
#     ##Timer
#     solver_time = time.time()
    
#     model = mpec_model(ng, nb, nl, ncda,IN_loads, gen_capacity, 
#                     arrival, depart, charge_power,EV_soc_arrive,EV_soc_low, EV_soc_up, 
#                     TCL_Max, TCL_R, TCL_Beta, TCL_temp_low, outside_temp, 
#                     SL_low, SL_up, SL_cycle, SL_loads,
#                     dic_G, dic_Bus_CDA, DABus, B, Yline, dic_G_Bus, 
#                     c_g, c_d_o[j-1], c_d_b[j-1], 
#                     dic_CDA_Bus, g_s, F_d_o, F_d_b, FMAX,
#                     c_DA_o, c_DA_b)
    
   
#     SOLVER_NAME="gurobi"  #'cplex'
#     solver=SolverFactory(SOLVER_NAME)
#     results = solver.solve(model)
    
#     bigM =100.0
#     bigF = 100.0
#     check_constraints(model, Yline, 
#                       B,dic_G, dic_Bus_CDA, 
#                       DABus, c_g, dic_G_Bus, 
#                       dic_CDA_Bus, c_d_o[j-1], c_d_b[j-1], c_DA_o, 
#                       c_DA_b, bigM, bigF, g_s, F_d_o, F_d_b, FMAX )    

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

with open('DA_Bilevel_pprint.txt', 'w') as f:
      f.write("Description of the Bilevel model for strategic day ahead aggregator:\n")
      model.KKT_transmission_up_3_con.pprint(ostream=f)
