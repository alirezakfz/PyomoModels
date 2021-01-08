# -*- coding: utf-8 -*-
"""
Created on Tue Sep 15 17:19:40 2020

@author: alire
"""
import math
import random
import numpy as np
from numpy.random import seed
from numpy.random import randint
from numpy.random import rand
from scipy.stats import truncnorm


def get_truncated_normal(mean=0, sd=1, low=0, upp=10):
    return truncnorm(
        (low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)


def dataFile(number_of_EVs, 
             number_of_timeslot, 
             Charger_Type,
             charger_cost,
             slot):
             
    
    
        
    #initiallizing variables to make them shorter
    ev_no=number_of_EVs
    time_slot=number_of_timeslot
    
    """
    EVs specification
    """    
    EV_list=['Small','Sedan','SUV','Truck']
    
    EV_types={   
            "Small":{
                    "energy_consumption":0.3790,
                    "capacity":16,  
                    "max_distance":42.2163,
                    "charge_rate":8/slot
                    },
            "Sedan":{
                    "energy_consumption":0.4288,
                    "capacity":24,
                    "max_distance":55.9701,
                    "charge_rate":19/slot
                    },
            "SUV":{
                    "energy_consumption":0.5740,
                    "capacity":54,
                    "max_distance":94.0766,
                    "charge_rate":50/slot
                    },
            "Truck":{
                    "energy_consumption":0.8180,
                    "capacity":70,
                    "max_distance":85.5745,
                    "charge_rate":50/slot
                    }
            }
    
    
    parking_share = [0.4,0.3,0.2,0.1]  #Probability of EV 
    
    EV_samples=random.choices(EV_list,k=ev_no,weights=parking_share)
   
    """
    statistical driving pattern parameters
    """
    seed=np.random.randint(1,1000)
    np.random.seed(seed)
    random.seed(seed)
    
    """
    Demand for each EV
    """
    u_mile=40
    std_mile=20
    x_dist=get_truncated_normal(u_mile, std_mile, low=5, upp=80)
    distance=[]
    
    demand=[]
    
    u_arrival   = 8.5#7
    std_arrival = 2.2# 4.2,1.73
    x_arrival=get_truncated_normal(u_arrival, std_arrival, low=1, upp=15)
    arrival_time=[]
    
    u_depart    = 19.5#18
    std_depart  = 2.2#4.2, 1.73  
    x_depart=get_truncated_normal(u_depart, std_depart, low=16, upp=24)
    depart_time=[]
    
    check=True
    #count=0
    
    min_charge=min(Charger_Type)
    soc=[]
   
    #For each EV generate data that is consistent to use
    for ev in EV_samples:
        
        charge_rate=EV_types[ev]["charge_rate"]
        
        while check:
            dist= x_dist.rvs() #[0]
            dist=round(dist,3)
            
            if dist > EV_types[ev]["max_distance"]:
                dem=round(EV_types[ev]["capacity"])
                temp_soc= 0
                # demand.append(round(EV_types[ev]["capacity"]))
            else:                
                dem=round(1.0*dist * EV_types[ev]["energy_consumption"])
                temp_soc = EV_types[ev]["capacity"] - dem
                # demand.append(round(1.0*distance[count]*EV_types[ev]["energy_consumption"]))
            
            dem_time=math.ceil(dem/charge_rate)
            
            arrive=x_arrival.rvs()#[0]
            arrive=round(arrive)
            
            depart=max(arrive+dem_time,x_depart.rvs()*slot)#[0]
            depart=round(depart)
            
            #Check if there is consistency between generated data
            if arrive> 1 and (arrive+dem_time<depart) and depart <=time_slot*slot:
                check=False
        distance.append(dist)
        arrival_time.append(arrive)
        depart_time.append(depart)
        demand.append(dem)
        soc.append(temp_soc)
        check=True    
        #count+=1                
                
    """
    Assumption for Number of each required chrager based on the demand
    """
    #limit the number of chargers 
        
    total_demand=sum(demand)
    
    #Total number of available chargers that could be installed
    total_chargers=0
    for ch in Charger_Type:
        total_chargers += math.ceil((total_demand/(ch*time_slot)))
        
    
    required_chargers=[]
    
    installed_chargers=[]
    installed_cost=[]
    for i in range(len(Charger_Type)):
        ch=Charger_Type[i]
        cost=charger_cost[i]
        no=math.ceil((total_demand/(ch*time_slot))) + 1 #+ int(total_demand/(ev_no*10))
        #limit the number of availabel chargers. Maximum 30 percent of possible chargers
        if ch ==4 and ev_no>25:
            # no=math.ceil((total_chargers *0.4)/ev_no)
            no=math.ceil((total_chargers *0.07))
            # print("Available CH4:",no)
        
        if ch==8 and ev_no>25:
            # no=math.ceil((total_chargers *0.8)/ev_no)
            no=math.ceil((total_chargers *0.25))
            # print("Available CH8:",no)
        
        if ch==19 and ev_no>25:
            # no=math.ceil((total_chargers *0.07*19)/ev_no)
            no=math.ceil((total_chargers *0.2))
            # print("Available CH19:",no)
            
        # if ch==50 and ev_no>25:
        if ch==50:
            # no=math.ceil((total_chargers *0.3)/ev_no)
            no= 1
            # no=math.ceil((total_chargers *0.05))
            # print("Available CH50:",no)
            
        
        # if (no > 0.3*total_chargers) and (ev_no > 25): # and (ev_no > 25)
        #     no=math.ceil(0.3*total_chargers)
        
        # if (no>0.15*total_chargers) and (ch==4) and (ev_no>25):# and (ev_no>25):
        #     no=math.ceil(0.15*total_chargers)
            
        for i in range(no):
            installed_chargers.append(ch)
            installed_cost.append(cost)
    
    """
    Power to charge each EV in each Charger
    """
    charge_power=np.empty((ev_no,len(installed_chargers)))
    for i in range(ev_no):
        for j in range(len(installed_chargers)):
            charge_power[i,j]=min(EV_types[EV_samples[i]]["charge_rate"],installed_chargers[j]/slot)
    
    
    # TFC=np.empty((ev_no,len(installed_chargers)))
    # for i in range(ev_no):
    #     for j in range(len(installed_chargers)):
    #         TFC[i,j]=math.ceil(demand[i]/charge_power[i,j])
    
    
    
    return arrival_time, depart_time, distance, demand, charge_power,installed_chargers,\
             installed_cost, EV_samples, soc
    
