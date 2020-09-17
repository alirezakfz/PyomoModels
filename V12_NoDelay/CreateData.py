# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 12:55:54 2020

@author: Ali
"""

import math
import numpy as np
from numpy.random import seed
from numpy.random import randint
from numpy.random import rand

def dataFile(ev_no=20,time_slot=24,Charger_Type=[11,20,30],charger_cost=[300,1000,5000], slot=1):
    
    seed=np.random.randint(1,1000)
    np.random.seed(seed)
    """
    statistical driving pattern parameters
    """    
    u_arrival   = 8.5#7
    std_arrival = 2.2#1.73
    alow=6
    ahigh=11
    #    arrival_time=np.random.rand(ev_no)*std_arrival+u_arrival
#    arrival_time=np.random.normal(u_arrival,std_arrival,ev_no).round()
    arrival_time=np.random.uniform(alow,ahigh,ev_no).round()
    
    
    
    u_depart    = 18.5#18
    std_depart  = 3.2#1.73  
    
    dlow=15
    dhigh=22
#    depart_time=np.random.normal(u_depart,std_depart,ev_no).round()
    depart_time=np.random.uniform(dlow,dhigh,ev_no).round()
    depart_time*=slot
    
    
    
    """
    Distance, Dialy milage statistics
    """
    u_mile=40
    std_mile=15
    
    low_mile=25
    high_mile=55
#    distance=np.random.normal(u_mile,std_mile,ev_no).round()
    distance=np.random.uniform(low_mile,high_mile,ev_no).round()
    
    
    
    """
    EVs specification
    """    
    EV_list=['small','sedan','suv','truck']
    # data from paper 06 and 02
    
    EV_types={   
            "small":{
                    "energy_consumption":0.3790,
                    "capacity":16,  
                    "max_distance":42.2163,
                    "charge_rate":8/slot
                    },
            "sedan":{
                    "energy_consumption":0.4288,
                    "capacity":24,
                    "max_distance":55.9701,
                    "charge_rate":19/slot
                    },
            "suv":{
                    "energy_consumption":0.5740,
                    "capacity":54,
                    "max_distance":94.0766,
                    "charge_rate":50/slot
                    },
            "truck":{
                    "energy_consumption":0.8180,
                    "capacity":70,
                    "max_distance":85.5745,
                    "charge_rate":50/slot
                    }
            }
    
    
    parking_share = [0.4,0.3,0.2,0.1]  #Probability of EV 
    
    EV_samples=np.random.choice(EV_list,ev_no,parking_share)
    
    
    """
    Demand for each EV
    """
    demand=[]
    count=0
    for ev in EV_samples:
        if distance[count] > EV_types[ev]["max_distance"]:
            demand.append(round(EV_types[ev]["capacity"]))
        else:
            demand.append(round(1.0*distance[count]*EV_types[ev]["energy_consumption"]))
        count+=1
    

    
    
    """
    Assumption for Number of each required chrager based on the demand
    """
    total_demand=sum(demand)
    installed_chargers=[]
    installed_cost=[]
    for i in range(len(Charger_Type)):
        ch=Charger_Type[i]
        cost=charger_cost[i]
        no=math.ceil((total_demand/(ch*time_slot))) + int(total_demand/(ev_no*10))
        for i in range(no):
            installed_chargers.append(ch)
            installed_cost.append(cost)
    
    """
    Power to charge each EV in each Charger
    """
#    Charger_Type=[11,20,30]
#    charger_cost=[300, 1000, 5000]
    charge_power=np.empty((ev_no,len(installed_chargers)))
    for i in range(ev_no):
        for j in range(len(installed_chargers)):
            charge_power[i,j]=min(EV_types[EV_samples[i]]["charge_rate"],installed_chargers[j]/slot)
            
    
    """
    Time needed to complete charging EV based on charger
    """
    TFC=np.empty((ev_no,len(installed_chargers)))
    for i in range(ev_no):
        for j in range(len(installed_chargers)):
            TFC[i,j]=math.ceil(demand[i]/charge_power[i,j])
            #check the validity of the test
            while(TFC[i,j] > (depart_time[i]-arrival_time[i])):
                distance[i]=round(np.random.uniform(low_mile,high_mile))
                if distance[i] > EV_types[EV_samples[i]]["max_distance"]:
                    demand[i]=(round(EV_types[EV_samples[i]]["capacity"]))
                else:
                    demand[i]=(round(1.0*distance[i]*EV_types[EV_samples[i]]["energy_consumption"]))
                TFC[i,j]=math.ceil(demand[i]/charge_power[i,j])
    
        
    return arrival_time, depart_time, distance, demand, charge_power, installed_chargers, installed_cost, TFC, EV_samples
    
    