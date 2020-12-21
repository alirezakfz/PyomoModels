# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 16:21:21 2020

@author: alire
"""
import pandas as pd
import random
 



def RunOccupancySimulation(activity_profile, transition_prob, tpm_prob, residents=2):
    """
    Domestic Active Occupancy Model - Simulation Example Code
    RunOccupancySimulation Function - This function runs a single day active occupancy simulation

    Returns
    -------
    Data Farme containing minutes,irradiance for selected month, 
    active occupancy in a house with known residents number 
    Adding new 'Active_Occupancy' column into activity_profile data frame 

    """

    # A varible to store a cumulative probability
    p_cumulative=0
    
    # The current number of active occupants
    current=0
    
    rand=random.random()
    
    active_occupant=['Zero_active_occupants','One_active_occupant','Two_active_occupants',\
                     'Three_active_occupants','Four_active_occupants','Five _active_occupants',\
                         'Six_active_occupants']
    
    state=residents
    #Determine the start state at time 00:00 by checking the 
    #random number against the distribution
    for current in range(len(active_occupant)):
        # Add the probability for this number of active occupants
        p_cumulative += transition_prob.loc[current,state]
        
        if rand < p_cumulative:
            #This is the start state
            state=current
            #print(current)
            break
    
    number_of_occupant=[]
    number_of_occupant.append(state)
    
    #Step 3: Determine the active occupancy transitions for each ten minute period of the day
       
    active_occupant=['pr_to_zero', 'pr_to_one', 'pr_to_two',\
                     'pr_to_three', 'pr_to_four', 'pr_to_five', 'pr_to_six']
    
    for time_step in range(143):
        #generate random number
        rand=random.random()
        
        #Reset the cumulative probability count
        p_cumulative=0
        
        #select the active occupant prob transition row
        row=time_step*7+state
        
        for current in range(len(active_occupant)):
            
            #select the column for transition check
            col=active_occupant[current]
            # Add the probability for this number of active occupants
            p_cumulative += tpm_prob[col][row]
            
            if rand < p_cumulative:
                #This is the start state
                state=current
                break
        number_of_occupant.append(state)
    
    #Add Active occupancy times and persons to data frame
    current=0
    new_list=[]
    for time_step in range(len(activity_profile['reference'])):
        if time_step>0 and time_step % 10 ==0:
            current+=1
        new_list.append(number_of_occupant[current])
        
    activity_profile['Active_Occupancy']=new_list
    
    pass
    #return activity



    
    