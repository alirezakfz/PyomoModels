# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 10:58:33 2020

@author: alire
"""

import random
import math
import pandas as pd
from scipy.stats import truncnorm

def get_truncated_normal(mean=0, sd=1, low=0, upp=10):
    return truncnorm(
        (low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)
    


def lighting_load(activity, bulbs_df ,month=2):
    
    #Select Irradiance data for the selected month
    # f_name="Data.xlsx"
    # sheet="bulbs_list"
    
    month_list=['January','February','March','April','May','June','July','August','September','October','November','December']
    
    Month=month_list[month-1]
    
    #define the mean and std for irradiance threshold
    #House external global irradiance threshold  W/m2
    mean=60
    std=10
    upp=max(activity[Month])
    low=min(activity[Month])
    dist=get_truncated_normal(mean, std, low, upp)
    
    
    #Determine the irradiance threshold of this house
    irradiance_threshold=int(dist.rvs())
    #This calibration scaler is used to calibrate the model
    #so that it provides a particular average output over a large number of runs.
    calibratin=0.00815368639667705
    
    #Choose a random house from the list of 100 provided in the bulbs sheet
    rand_house=random.randint(1, 100)
    
    # #Read the bulbs data from excel sheet
    # bulbs_df = pd.read_excel(f_name,sheet_name=sheet)
    # bulbs_df.fillna(0, inplace=True)
    
    
    #Selectd random house bulbs in list
    bulbs_list = bulbs_df.iloc[rand_house-1]
    bulbs_list=bulbs_list[bulbs_list!=0]
    
    #selected month irradiance list
    ir_list=activity[Month]
    
    # Active occupancy for the house during simulation time
    active_oc_list= activity["Active_Occupancy"]
    
    #Number of bulbs in selected house
    num_bulbs=int(bulbs_list['bulbs_count'])
    
    #Set the calibration scalar
    claibration_scalar = 0.008153686
    
    #Simulation array to store data
    simulation_lists=[]
    
    # Total lighting power consumption
    total_lighting = [0]*1440
    
    # Effective occupancy represents the sharing of light use.
    # Derived from:	U.S. Department of Energy, Energy Information Administration, 1993 Residential Energy Consumption Survey, 							
	# Mean Annual Electricity Consumption for Lighting, by Family Income by Number of Household Members
    # Number of active occupants   0      1         2         3         4       5
    # Effective occupancy          0.000  1.000     1.528     1.694     1.983   2.094
    effective_occupancy=[0.000, 1.000 , 1.528 , 1.694, 1.983 , 2.094]



    # Lighting event duration model
    # This model defines how long a bulb will stay on for, if a switch-on event occurs.
    # Source:	M. Stokes, M. Rylatt, K. Lomas, A simple model of domestic lighting demand, Energy and Buildings 36 (2004) 103-116															
	# Mean Annual Electricity Consumption for Lighting, by Family Income by Number of Household Members							
    # range of equal probability number:  1           2       3      4      5      6      7      8     9
    #lower value (minutes):               1           2       3      5      9      17     28     50    92
    # upper value(minutes):               1           2       4      8      16     27     49     91    259   
    # cumulative probability:         0.111111111  0.222222222  0.333333333  0.444444444  0.555555556   0.666666667   0.777777778   0.888888889  1
    low_duration  = [1, 2, 3, 5, 9, 17, 28, 50, 92]
    up_duration = [1, 2, 4, 8, 16, 27, 49, 91, 259]
    duration_cumulative_prob= [0.111111111, 0.222222222, 0.333333333, 0.444444444, 0.555555556, 0.666666667, 0.777777778, 0.888888889, 1]
    
    # For each bulb
    for i in range(num_bulbs):
        
        #Get the bulb rating
        rating = bulbs_list[i+1]
        
        temp_list=[]
        
        #Store the bulb in progress rating
        # temp_list.append(rating)
        temp_list.append(num_bulbs)
        
        #Assign a random bulb use weighting to this bulb
        #Note that the calibration scalar is multiplied here to save processing time later
        calibrated_relative_use_weighting = - claibration_scalar * math.log(random.random(),math.e)        
        temp_list.append(calibrated_relative_use_weighting)
        
        # Calculate the bulb usage at each minute of the day
        time=1
        while(time <= 1440):
            
            """
            Is this bulb switched on to start with?
            This concept is not implemented in this example.
            The simplified assumption is that all bulbs are off to start with.
            """
            
            # Get the irradiance for this minute
            irradiance=ir_list[time-1]
            
            # Get the number of current active occupants for this minute
            # Convert from 10 minute to 1 minute resolution
            active_occupants = active_oc_list[time-1]
            
            # Determine if the bulb switch-on condition is passed
            # ie. Insuffient irradiance and at least one active occupant
            # There is a 5% chance of switch on event if the irradiance is above the threshold
            blow_irradiance = irradiance < irradiance_threshold or random.random() < 0.05
            
            # Get the effective occupancy for this number of active occupants to allow for sharing
            effective_occ=effective_occupancy[active_occupants]
            
            # Check the probability of a switch on at this time
            if (blow_irradiance and random.random() < effective_occ * calibrated_relative_use_weighting):
                #This is a switch on event
                
                #Determine how long this bulb is on for
                rnd=random.random()
                cml = 0
                
                for j in range(1,10):
                    #Get the cumulative probability of this duration
                    cml = duration_cumulative_prob [j-1]
                    
                    if(rnd < cml):
                        lower_duration = low_duration[j-1]
                        upper_duration = up_duration[j-1]
                        
                        #Get another random number
                        rnd2 = random.random()
                       
                        # Guess a duration in this range
                        light_duration = round(rnd2 * (upper_duration - lower_duration) + lower_duration)
                        break
                for j in range(1, light_duration):
                    #range check
                    if time > 1440:
                        break
                    
                    #Get the number of current active occupants for this minute
                    active_occupants = active_oc_list[time-1]
                    
                    # If there are no active occupants, turn off the light
                    if active_occupants == 0:
                        break
                    
                    # Store the demand
                    temp_list.append(rating)
                    
                    #increment timing
                    time = time +1
            else:
                temp_list.append(0)
                
                #increment timing
                time = time +1
        
        #end of while
        
        # simulation_lists.append(temp_list)
        
        #add it to activity profile
        # col='Bulbs'+str(i+1)+'_'+str(rating)+'W'
        temp_list=temp_list[2:]
        # activity[col]=temp_list
        
        # Add amount of current bulb load to total load
        for i in range(len(temp_list)):
            total_lighting[i] += temp_list[i]
        #end of for in bulbs
    
    #Add total consumption to activity profile
    activity["Total_lighting"]=total_lighting
    
    return  num_bulbs 
    
    #simulation_lists

    
