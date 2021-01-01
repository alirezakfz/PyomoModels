# -*- coding: utf-8 -*-
"""
Created on Sat Dec 12 12:08:46 2020

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


def electric_vehicles(number_of_EVs=10, 
             number_of_timeslot=24, 
             Charger_Type=[3,7],
             slot=1):
    
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
    u_mile=40 #40
    std_mile=15 #20
    x_dist=get_truncated_normal(u_mile, std_mile, low=1, upp=40)
    distance=[]
    
    demand=[]
    
    u_arrival   = 7#7
    std_arrival = 1.73# 4.2,1.73
    x_arrival=get_truncated_normal(u_arrival, std_arrival, low=5, upp=14)
    arrival_time=[]
    
    u_depart    = 18#18
    std_depart  = 1.73#4.2, 1.73  
    x_depart=get_truncated_normal(u_depart, std_depart, low=15, upp=24)
    depart_time=[]
    
    check=True
    #count=0
    
    min_charge=min(Charger_Type)
    charge_power=[]
    
    soc=[]
    
    #For each EV generate data that is consistent to use
    for ev in EV_samples:
        
        charge_rate=EV_types[ev]["charge_rate"]
        # Randomly select charge rate between 3 and 7
        charge_rate = random.choice(Charger_Type)
        
        while check:
            dist= x_dist.rvs() #[0]
            dist=round(dist,3)
            
            if dist > EV_types[ev]["max_distance"]:
                dem=round(EV_types[ev]["capacity"])
                # demand.append(round(EV_types[ev]["capacity"]))
            else:                
                dem=round(1.0*dist * EV_types[ev]["energy_consumption"])
                # demand.append(round(1.0*distance[count]*EV_types[ev]["energy_consumption"]))
            
            # set the minimum battery SOC to 0.25
            dem = max(dem, EV_types[ev]["capacity"]*0.25)
            
            dem_time=math.ceil(dem/charge_rate)
            
            arrive=x_arrival.rvs()*slot#[0]
            arrive=round(arrive)
            
            # depart=max((arrive+dem_time)%(number_of_timeslot*slot) ,x_depart.rvs()*slot)#[0]
            depart = x_depart.rvs()*slot
            depart=round(depart)
            
            #Check if there is consistency between generated data
            if  (arrive + dem_time < depart) and depart <= time_slot*slot:
                check=False
        distance.append(dist)
        arrival_time.append(arrive)
        depart_time.append(depart)
        demand.append(dem)
        charge_power.append(charge_rate)
        soc.append(EV_types[ev]["capacity"]) # -dem
        check=True    
        #count+=1              
                
    return arrival_time, depart_time, distance , charge_power, EV_samples, demand, soc
    