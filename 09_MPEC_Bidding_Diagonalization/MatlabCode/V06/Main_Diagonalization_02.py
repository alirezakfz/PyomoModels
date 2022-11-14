# -*- coding: utf-8 -*-
"""
Created on Fri Oct  8 12:15:07 2021

@author: Alireza
"""

# -*- coding: utf-8 -*-
"""
Created on Tue May 25 16:05:41 2021

@author: alire

Hourly radiation
#https://joint-research-centre.ec.europa.eu/pvgis-photovoltaic-geographical-information-system/pvgis-tools/hourly-radiation_en
"""

import random
import time
import pandas as pd
import numpy as np
import collections
from csv import writer
import os
# from samples_gen import generate_price, generate_temp
#from MPEC_Concrete_Model_ver01 import mpec_model
from MPEC_Concrete_Model_ver08 import mpec_model
from pyomo.environ import *
from pyomo.opt import SolverFactory

from Model_to_CSV import model_to_csv, model_to_csv_iteration, model_obj_to_csv
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
        data_pd.to_csv('Model_CSV/diagonalizaton_results.csv', header=True, mode='w')
    else:
        data_pd.to_csv('Model_CSV/diagonalizaton_results.csv', header=False, mode='a')
    
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
    df1 = pd.read_csv('prosumers_data/inflexible_profiles_scen_'+file_index+'.csv').round(5)*load_multiply/(1000*1000*MVA) #*load_multiply/100 #*load_multiply #/1000
    
    # Just selecting some prosumers like 500 or 600 or 1000
    df1 = df1[:NO_prosumers]
    # print(df1.shape)
    df2 = pd.read_csv('prosumers_data/prosumers_profiles_scen_'+file_index+'.csv')
    df2 = df2[:NO_prosumers]
    
    df3 = pd.read_csv('prosumers_data/occupancy_profiles_scen_'+file_index+'.csv')
    df3 = df3[:NO_prosumers]
    return df1 , df2, df3



gen_capacity =[100, 75, 50, 50]
# gen_capacity =[50000, 50000, 50000]

random.seed(42)

# Time Horizon
NO_prosumers = 30
no_iteration = 5
epsilon= 0.0001
horizon=24
H = range(16,horizon+16)    
MVA = 30 # Power Base
PU_DA = 1/(1000*MVA)
load_multiply = 3000

nl = 7    # Number of network lines
nb = 6    # Number of network buses

FromBus = [1,1,2,2,3,4,5] # Vector with network lines' "sending buses"
ToBus = [2,4,3,4,6,5,6]   # Vector with network lines' "receiving buses"

LinesSusc = [5.8824, 3.8760, 27.0270, 5.0761, 55.5556, 27.0270, 7.1429]  #Vector with per unit susceptance of the network 
# LinesSusc = [5,6,7]

ng = 4    # Number of Generators
ncda = 8  # Number of competing 
ndas = 9  # Number of participant DAs

GenBus = [1,2,6,6]  # Vector with Generation Buses
CDABus = [[1, 3], [2,3],[3,3],[4,4],[5,4],[6,4],[7,5],[8,5],[9,5]]      # Vector with competing DAs Buses
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
            
            
            temp_offer = [x/MVA for x in temp_offer]
            temp_bid = [x/MVA for x in temp_bid]
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

df_price = pd.DataFrame().from_dict( price_d_o)
df_price.to_csv("Model_CSV/price_d_o.csv",index=False)

c_d_o=[]
for i in range(ncda+1):
    c_d_o.append(price_d_o)


# Price bid for buying power of competing DA  i in horizon t
price_d_b=dict()
price_d_b['DAS']= random_price(horizon,70,110)

for i in range(1,ncda+1):
    price_d_b[i] = random_price(horizon,70,110)

df_price = pd.DataFrame().from_dict(price_d_b)
df_price.to_csv("Model_CSV/price_d_b.csv",index=False)

c_d_b=[]
for i in range(ncda+1):
    c_d_b.append(price_d_b)



# Price bid for supplying power of strategic DA in horizon t
c_DA_o = c_d_o[DABus-1]['DAS'] # random_price(horizon)

# Price bid for buying power of strategic DA in horizon t
c_DA_b = c_d_b[DABus-1]['DAS'] # random_price(horizon)

# Supply offer of generator i in time t gen_capacity =[100, 75, 50, 50]
g_s = { 1:random_generation(horizon,10, 12),
        2:random_generation(horizon,5, 10),
        3:random_generation(horizon,15, 20),
        4:random_generation(horizon,1, 50)}


g_s = { 1:[100 for x in range(0,horizon)],
        2:[75 for x in range(0,horizon)],
        3:[50 for x in range(0,horizon)],
        4:[50 for x in range(0,horizon)]}


# 2019 November 15 forecasted temprature
outside_temp=[27.694803,26.834803,26.594803,25.664803,22.594803,21.394802,20.164803,19.584803,20.334803,16.784803,16.094803,15.764802,14.774801,14.834802,14.184802,14.144801,15.314801,16.694803,19.734802,24.414803,25.384802,26.744802,27.144802,27.524803]
#outside_temp = [x for x in outside_temp]

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
    IN_loads, profiles, _ = load_data(str(j))
    DA_solar_power.append(random_solar_power_var(IN_loads, j))
    
    
# Penetration of EVs in each strategic DA prosumers
# Select EVs for scheduling
EVs_penetration=None
EVs_list = dict()



for j in range(1,ncda+2):
    if j %2 == 0:
        EVs_penetration= 1 #0.7
    elif j % 3== 0:
        EVs_penetration= 1 #1.0
    elif j % 5 == 0:
        EVs_penetration= 1 #0.35
    else:
        EVs_penetration= 1 # 0.10
    # Adding random EVs for prosumers
    NO_of_EVs = int(EVs_penetration * NO_prosumers)
    EVs_list[j] = random.choices([i+1 for i in range(NO_prosumers)],k=NO_of_EVs )


# Solar power penetration.
Solar_penetration= None
Solar_list=dict()

for j in range(1,ncda+2):
    if j %2 == 0:
        Solar_penetration=  1 # 0.7
    elif j % 3== 0:
        Solar_penetration= 1 # 0.1
    elif j % 5 == 0:
        Solar_penetration=  1 #0.35
    else:
        Solar_penetration=  1 #0.1
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
            solar_power[da-1,i] = 0.000157 * area * irrediance[i] * (1 - 0.001*random.random()* (outside_temp[i]-25))*load_multiply/(1000*MVA)
    
    return solar_power
        
# List of solar powers
DA_solar_power =[]        
for j in range(1,ncda+2):
    IN_loads, profiles, _ = load_data(str(j))
    DA_solar_power.append(random_irrediance_solar_power(irrediance_nov, IN_loads, j, Solar_list)) # changed from irradiance_nov


# Create DAs as agent number to shuffle before each round
DAs_list=[]
for j in range(1,ncda+2):
    DAs_list.append(j)


objective_function = dict()



check=False
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
        
        
        
        IN_loads, profiles, oc_profiles = load_data(str(j))
        
        
        
        # EVs properties 
        arrival = profiles['Arrival']
        depart  = profiles['Depart']
        charge_power = profiles['EV_Power']*load_multiply/(1000*MVA)#*load_multiply
        EV_soc_low   = profiles['EV_soc_low']*load_multiply/(1000*MVA)#*load_multiply
        EV_soc_up   = profiles['EV_soc_up']*load_multiply/(1000*MVA)#*load_multiply
        EV_soc_arrive = profiles['EV_soc_arr']*load_multiply/(1000*MVA)#*load_multiply
        EV_demand = profiles['EV_demand']*load_multiply/(1000*MVA)#*load_multiply
        
                
        # Shiftable loads
        SL_loads=[]
        SL_loads.append(profiles['SL_loads1']*load_multiply/(1000*MVA*100))#*load_multiply/10)
        SL_loads.append(profiles['SL_loads2']*load_multiply/(1000*MVA*100))#*load_multiply/10)
        SL_low   = profiles['SL_low']
        SL_up    = profiles['SL_up']
        SL_cycle = len(SL_loads)
        
        # Thermostatically loads
        TCL_R   = profiles['TCL_R']
        TCL_C   = profiles['TCL_C']
        TCL_COP = profiles['TCL_COP']
        TCL_Max = profiles['TCL_MAX'] + 30#*load_multiply/(1000*MVA)
        TCL_Beta= profiles['TCL_Beta']
        TCL_temp_low = profiles['TCL_temp_low']
        
        TCL_temp_up  = profiles['TCL_temp_up']+3
        #TCL_temp_up  = profiles['TCL_temp_low']+4

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
                        TCL_Max, TCL_R, TCL_Beta, TCL_temp_low, TCL_temp_up, outside_temp, TCL_COP, 
                        SL_low, SL_up, SL_cycle, SL_loads,
                        dic_G, dic_Bus_CDA, DABus, B, Yline, dic_G_Bus, 
                        c_g, c_d_o[j-1], c_d_b[j-1], 
                        dic_CDA_Bus, g_s, F_d_o, F_d_b, FMAX,
                        c_DA_o, c_DA_b, DA_solar_power[j-1],
                        EVs_list[j], Solar_list[j],
                        load_multiply, MVA, oc_profiles)
        
        
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
            model_to_csv_iteration(model, IN_loads.sum(0), n, str(j), timestr, EVs_list[j], load_multiply, MVA)
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
        
        # Save model Objective function based on time
        model_obj_to_csv(model, n, j, timestr, MVA, c_g, c_d_o[j-1], c_d_b[j-1], g_s, F_d_o, F_d_b, FMAX)
        
        
        # model_to_csv(model, IN_loads.sum(0))
        
        # Finishing Step 3
    # Step 4 check if epsilon difference exist
     
    
    # check=False
    if check_bids(offers_bid,new_offers,epsilon) and check_bids(demand_bid,new_bids,epsilon) and (infeasibility_counter < ncda+1):
        check=True
        diag_df = pd.concat([pd.DataFrame.from_dict(new_offers), pd.DataFrame.from_dict(new_bids)], axis=1)
        diag_df.columns= dig_col
        results_to_csv(diag_df, n)
        print("solution found in iteration:",n)
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
    
    
    offers_bid=new_offers
    demand_bid=new_bids
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
# save solar power for each DA for each Timeslot
m_time = [t for t in range(16,40)]

solar_production = dict()
for i in range(0, ndas):
    temp_df = pd.DataFrame().from_dict(DA_solar_power[i])/1000
    solar_production[i] = temp_df.sum().tolist()
    
solar_df = pd.DataFrame().from_dict(solar_production).T

name_dic = dict()
for i in range(len(solar_df.columns)):
    name_dic[solar_df.columns[i]] = "t="+str(m_time[i])

solar_df.rename(columns=name_dic, inplace=True)

name_dic = dict()
for i in range(len(solar_df.index)):
    name_dic[solar_df.index[i]] = "SDA "+str(i+1)
    
solar_df.rename(index=name_dic, inplace=True)
solar_df = solar_df/load_multiply

if os.path.exists("Model_CSV/Renewable Production.xlsx"):
    with pd.ExcelWriter("Model_CSV/Renewable Production.xlsx",  engine='openpyxl', mode='a',if_sheet_exists="replace")  as writer: 
        solar_df.to_excel(writer, sheet_name='Sheet1' )
else:
    with pd.ExcelWriter("Model_CSV/Renewable Production.xlsx", engine='openpyxl')  as writer: 
        solar_df.to_excel(writer, sheet_name='Sheet1' )
