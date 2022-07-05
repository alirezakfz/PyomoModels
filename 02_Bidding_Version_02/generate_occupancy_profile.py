# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 20:53:36 2020

@author: alire
"""

import pandas as pd
import random
import numpy as np
import datetime
import csv



import matplotlib.pyplot as plt

# Custom functions
from occupancy_simulation import RunOccupancySimulation
from appliance_simulation import run_appliance_simulation, configure_appliances_in_dwelling
from Lighting_simulation import lighting_load
from make_dat_file import create_dat_files
from EVs_simulation import electric_vehicles
# from save_result import results_to_csv
from samples_gen import generate_temp, generate_price
from gant_chart import gant_chart

from create_scen_struct import scenario_structure

# usage profile of WM for hour1, hour2
# Dataset location 
# https://ari.vt.edu/research-data.html



# creating "inflexible loads" based on the month, random number of residents
# And day type: week-day or weekend using transition probability matrix TPM
# for states of active residents to change into inactive one 
def prosumers_load_profile(number_of_prosumers=2):
    # Datas file
    f_name="Data_2.xlsx"
    
    # Set the week day
    # wd = weekday 
    # we = weekend
    day_type='wd'    
    
    # Set the month between 1 to 12
    month_list=['January','February','March','April','May','June','July','August','September','October','November','December']
    month=11
    
    # Select Irradiance data for the selected month
    sheet="Irradiance"
    Month=month_list[month-1]
    activity_profile_main=pd.read_excel(f_name,sheet_name=sheet)
    
    activity_profile_main=activity_profile_main[['Minute_of_day','reference',Month]]
    # It will store the activity profile for the house
    activity_profile_main=activity_profile_main.astype({'Minute_of_day':int,Month:int})
    
     #Step 1: Determine the active occupancy start state between 00:00 and 00:10
    if day_type=='wd':
        sheet='Weekday'
    else:
        sheet='Weekend'
        
    # Load Transition probaility between occupancy for start states
    transition_prob=pd.read_excel(f_name,sheet_name=sheet)
    
    #Store the summary of loads
    summary_loads=[]
    residents_list=[]
    occupancy_activity=[]
    
    for i in range(number_of_prosumers):
        
        activity_profile = activity_profile_main.copy(deep=True)
        
        #Randomly select number of residents
        # Set the number of residents in the house
        # Random number between 1 to 5
        residents=random.randint(1, 5)
        
        residents_list.append(residents)
    
        #load the transition probability for active occupants in state
        if day_type=='wd':
            sheet='tpm'+str(residents)+'_'+'wd'
        else:
            sheet='tpm'+str(residents)+'_'+'wd'
        
        #load the transition probability for active occupants in state
        tpm_prob=pd.read_excel(f_name,sheet_name=sheet)
    
    
        """
        Create the activity occupancy for the number of residents
        """
        # Step 2: Create occupancy profile for the selected house
        RunOccupancySimulation(activity_profile, transition_prob,tpm_prob, residents)
        
        
        occupancy_activity.append(activity_profile['Active_Occupancy'])
    
    #gant_chart(0, activity_profile)
    return occupancy_activity


# Change the loads from minutes to hourly for each day
# from 1440 minutes in day into 24 hours     
def minute_to_hour(occupancy_activity):
      
    occupancy=[]
    for occ in occupancy_activity:
        array=np.array(occ)
        hourly=[]
        for x in range(0,len(array),60):
            temp=array[x:min(x+59,len(array))].sum()
            temp = 1 if temp else 0
            hourly.append(temp)
        occupancy.append(hourly)
    
            
    return occupancy


# Write list of list to CSV file        
def write_to_csv( occupancy_profiles, scenario):
    # The 24 hour simulation is from 16:00 to 40:00 
    # So change the order and time
       
    # part for saving occupancy activity
    temp=[x for x  in range(16,40)]
    writelist=[]
    writelist.append(temp)
    for occ in occupancy_profiles:
        temp=np.roll(occ,-15)
        temp=temp.tolist()
        writelist.append(temp)
    
    f_name="prosumers_data/occupancy_profiles_scen_"+str(scenario)+".csv"
    with open(f_name, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(writelist)
    pass


def main():
    
    # create profiles for each prosumers: lighting, ordinary appliances
    number_of_prosumers=1000
    number_of_scenarios=20
    
    # Day Ahead price for NOV-15 2019
    price=[70,69.99,67.99,68.54,66.1,74.41,74.43,70,68.89,65.93,59.19,59.19,65.22,66.07,70.41,75.15,84.4,78.19,74.48,69.24,69.32,69.31,68.07,70.06]
    
    # November 15 forecasted temprature
    temp=[16.784803,16.094803,15.764802,14.774801,14.834802,14.184802,14.144801,15.314801,16.694803,19.734802,24.414803,25.384802,26.744802,27.144802,27.524803,27.694803,26.834803,26.594803,25.664803,22.594803,21.394802,20.164803,19.584803,20.334803]
    
    
    temperatures = generate_temp(temp, number_of_scenarios)
    
    prices= generate_price(price, number_of_scenarios)
    
    for scenario in range(1,number_of_scenarios+1):
        
        occupancy_activity =prosumers_load_profile(number_of_prosumers)
        
        #sample plot of loads
        # x=range(0,len(summary_loads[0]))
        # plt.plot(x,summary_loads[0])
        # plt.plot(x,summary_loads[1])
        
        # Make prosumers load from minute interval to hour interval
        # For creating inflexible loads
        # loads_hourly, occupancy_profiles = minute_to_hour(summary_loads, occupancy_activity)
        # write_to_csv(loads_hourly, occupancy_profiles, scenario)
        
        occupancy_profiles = minute_to_hour(occupancy_activity)
        write_to_csv(occupancy_profiles, scenario)
        
        
        
        # # Calling flexible and EVs simulation function 
        # # By following function
        # number_of_EVs=number_of_prosumers
        # run_evs_flexible_loads(residents_list, number_of_EVs, scenario)
        
    #     #*******************************
    #     # Make dat file 
    #     f_inflexible="prosumers_data/inflexible_profiles_scen_"+str(scenario)+".csv"
    #     f_occupancy= "prosumers_data/occupancy_profiles_scen_"+str(scenario)+".csv"
    #     f_prosumers= "prosumers_data/prosumers_profiles_scen_"+str(scenario)+".csv"
        
    #     create_dat_files(f_inflexible, f_occupancy, f_prosumers, temperatures[scenario-1], prices[scenario-1], scenario)
    
   
    # #gant_chart(num_bulbs, activity_profile)
    # scenario_structure(number_of_scenarios)
    pass

if __name__ == "__main__":
    main()
    
    