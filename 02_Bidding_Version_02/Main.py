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

washing_machine=[[15.242,0],
                 [10.783,0],
                 [5.938,0],
                 [3.045,0],
                 [86.377,0],
                 [83.097,0],
                 [57.822,0],
                 [24.344,0]]

def flexible_loads(number_of_prosumers, arrival, depart):
    SL_loads =[] # choosing washing loads randomly
    SL_low   =[] # The min time for starting the load
    SL_up    =[] # The max allowed time to finish the job
    
    for i in range(number_of_prosumers):
        SL_loads.append(random.choice(washing_machine))
        time=[]
        if (arrival[i] + 2) < 24:
            time.append([arrival[i], 23])
        if (depart[i] -2) > 29:
            time.append([29,depart[i]])
        if (depart[i] + 2)  < 40:
            time.append([depart[i],39])
        
        choose = random.choice(time)
        SL_low.append(choose[0])
        SL_up.append(choose[1])
    
    return SL_loads, SL_low, SL_up
        
        
        
def TCL_loads(number_of_prosumers):
    # Physical parameters
    TCL_R   = []
    TCL_C   = []
    TCL_COP = []
    TCL_MAX = []
    TCL_Beta =[]
    TCL_temp_low=[]
    TCL_temp_up =[]
    
    for i in range(number_of_prosumers):
        TCL_R.append(round(random.uniform(6.7, 50.1),2))
        TCL_C.append(round(random.uniform(0.5, 3.6),2))
        TCL_COP.append(round(random.uniform(4.6, 4.8),2))
        TCL_MAX.append(round(random.uniform(0.9, 1.25),2))
        TCL_Beta.append(round(np.exp(-1/(TCL_C[i]*TCL_R[i])),3))
        TCL_temp_low.append(round(random.randint(19, 21),2))
        TCL_temp_up.append(round(random.randint(21, 23),2))
    
    return TCL_R, TCL_C, TCL_COP, TCL_MAX, TCL_Beta, TCL_temp_low, TCL_temp_up
        



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
        
        
        """
        Run the light simulation for the some random house
        with known number of residents
        """
        sheet_name="bulbs_list"
        
        #Read the bulbs data from excel sheet
        bulbs_df = pd.read_excel(f_name,sheet_name=sheet_name)
        bulbs_df.fillna(0, inplace=True)
        
        # step 3: light (bulbs) simulation
        num_bulbs=lighting_load(activity_profile, bulbs_df ,month)
        
        
        
        """
        Default data needed for appliance simulation
        """
        
        #load the appliance data sheet into a pandas data frame
        sheet_name = "appliances"
        appliances_df = pd.read_excel(f_name,sheet_name=sheet_name)
        
        #Set the random presence of appliance in the house 
        #based on proportion presence probability of each appliance
        configure_appliances_in_dwelling(appliances_df)
        
        #load the appliance activity statistics sheet
        # into a pandas data frame
        sheet_name = "activity_stats"
        activity_stats= pd.read_excel(f_name,sheet_name=sheet_name)
        
        # Run the simulatiom for appliances
        run_appliance_simulation(activity_profile, appliances_df, activity_stats, day_type, month)
        
        # Disabled to create different scenarios for different number of prosumers
        # save_file="profiles/simulation_profile"+str(i)+".csv"
        # activity_profile.to_csv(save_file, header=True)
        
        column_list=activity_profile.columns[4:]
       
        summary_loads.append(activity_profile[column_list].sum(axis=1))
        
        occupancy_activity.append(activity_profile['Active_Occupancy'])
    
    #gant_chart(0, activity_profile)
    return summary_loads, residents_list, occupancy_activity


# Change the loads from minutes to hourly for each day
# from 1440 minutes in day into 24 hours     
def minute_to_hour(summary_loads, occupancy_activity):
    
    # array=np.array(summmary_loads)
    # hourly=[np.sum(array[x:np.min(len(array),x+59)]) for x in range(0,len(array),59)]
    hours=[]
    for loads in summary_loads:
        array=np.array(loads)
        
        hourly=[]
        for x in range(0,len(array),60):
            temp=array[x:min(x+59,len(array))].sum()
            temp=temp/1000     # from watt to KWh
            hourly.append(temp)
        # hourly=[np.sum(array[x:np.min(len(array),x+59)]) for x in range(0,len(array),59)]
        hours.append(hourly)
    
    occupancy=[]
    for occ in occupancy_activity:
        array=np.array(occ)
        hourly=[]
        for x in range(0,len(array),60):
            temp=array[x:min(x+59,len(array))].sum()
            temp = 1 if temp else 0
            hourly.append(temp)
        occupancy.append(hourly)
    
            
    return hours, occupancy


# Write list of list to CSV file        
def write_to_csv(loads, occupancy_profiles, scenario):
    # The 24 hour simulation is from 16:00 to 40:00 
    # So change the order and time
    temp=[x for x  in range(16,40)]
    
    writelist=[]
    writelist.append(temp)
    
    # uprange=range(15,24)
    # downrange=range(14,-1,-1)
    
    # for l in loads:
    #     temp=[]
    #     for x in uprange:
    #         temp.append(l[x])
    #     for x in downrange:
    #         temp.append(l[x])
    #     writelist.append(temp)   
    
    # Shift times 15 hours so simulation become from 16 to 40 as next 24 hour
    # to find bidding price
    for l in loads:
        temp=np.roll(l,-15)
        temp=temp.tolist()
        writelist.append(temp)
        
    f_name="prosumers_data/inflexible_profiles_scen_"+str(scenario)+".csv"
    with open(f_name, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(writelist)
    
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


# Calling required function for flexible loads and EVs and Thermostetically loads
def run_evs_flexible_loads(residents_list, number_of_EVs, scenario):
    
    # Required parameters to create EVs for prosumers
    number_of_timeslot=24
    Charger_Type=[3,7]
    slot=1
    
    # EVs info 
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
    
    # Aquiring the EVs info for each prosumer
    arrival_time, depart_time, distance , charge_power, EV_samples, demand, soc = electric_vehicles(number_of_EVs, 
                                                                                               number_of_timeslot, 
                                                                                               Charger_Type,
                                                                                               slot)
    # Create data frame to store generated data into CSV file
    df_info=pd.DataFrame()
    df_info['NO_Residents'] = residents_list
    df_info['EV_Type']    = EV_samples
    df_info['Arrival']    = arrival_time
    df_info['Depart']     = depart_time
    df_info['EV_demand']  = demand
    df_info['EV_Power']      = charge_power
    df_info['EV_Distance']   = distance
    df_info['EV_soc_low']    = [round(EV_types[x]['capacity']*0.25,2) for x in EV_samples]
    df_info['EV_soc_up']     = [round(EV_types[x]['capacity']*0.95,2) for x in EV_samples]
    df_info['EV_soc_arr']    = soc
    
    # Calling the Shiftable load
    # Washing machine with 6 choices of loads
    # Time for running and finishing the loads choose randomly between
    # 3 following choices randomly
    # arrival to midnight, 5 in morning to depart, from depart to 16
    SL_loads, SL_low, SL_up = flexible_loads(number_of_EVs, arrival_time, depart_time)
    
    # Add info to data frame
    df_info['SL_loads1'] = [l[0] for l in SL_loads]
    df_info['SL_loads2'] = [l[1] for l in SL_loads]
    df_info['SL_low']    = SL_low
    df_info['SL_up']    =  SL_up
    
    
    # Thermostatic load TCL
    # Call the random generator
    TCL_R, TCL_C, TCL_COP, TCL_MAX, TCL_Beta, TCL_temp_low, TCL_temp_up = TCL_loads(number_of_EVs)
    
    # Add the results of TCL_loads to data Frame
    df_info['TCL_R']   = TCL_R
    df_info['TCL_C']   = TCL_C
    df_info['TCL_COP'] = TCL_COP
    df_info['TCL_MAX'] = TCL_MAX
    df_info['TCL_Beta'] = TCL_Beta
    df_info['TCL_temp_low'] = TCL_temp_low
    df_info['TCL_temp_up'] = TCL_temp_up
    
    
    # Writing Data frame info CSV file
    f_name="prosumers_data/prosumers_profiles_scen_"+str(scenario)+".csv"
    df_info.to_csv(f_name, index=False, header=True)
    
    
    
    
    pass


def main():
    
    # create profiles for each prosumers: lighting, ordinary appliances
    number_of_prosumers=400
    number_of_scenarios=20
    
    # Day Ahead price for NOV-15 2019
    price=[70,69.99,67.99,68.54,66.1,74.41,74.43,70,68.89,65.93,59.19,59.19,65.22,66.07,70.41,75.15,84.4,78.19,74.48,69.24,69.32,69.31,68.07,70.06]
    
    # November 15 forecasted temprature
    temp=[16.784803,16.094803,15.764802,14.774801,14.834802,14.184802,14.144801,15.314801,16.694803,19.734802,24.414803,25.384802,26.744802,27.144802,27.524803,27.694803,26.834803,26.594803,25.664803,22.594803,21.394802,20.164803,19.584803,20.334803]
    
    
    temperatures = generate_temp(temp, number_of_scenarios)
    
    prices= generate_price(price, number_of_scenarios)
    
    for scenario in range(1,number_of_scenarios+1):
        
        summary_loads, residents_list, occupancy_activity =prosumers_load_profile(number_of_prosumers)
        
        #sample plot of loads
        # x=range(0,len(summary_loads[0]))
        # plt.plot(x,summary_loads[0])
        # plt.plot(x,summary_loads[1])
        
        # Make prosumers load from minute interval to hour interval
        # For creating inflexible loads
        loads_hourly, occupancy_profiles = minute_to_hour(summary_loads, occupancy_activity)
        write_to_csv(loads_hourly, occupancy_profiles, scenario)
        
        
        
        # Calling flexible and EVs simulation function 
        # By following function
        number_of_EVs=number_of_prosumers
        run_evs_flexible_loads(residents_list, number_of_EVs, scenario)
        
        #*******************************
        # Make dat file 
        f_inflexible="prosumers_data/inflexible_profiles_scen_"+str(scenario)+".csv"
        f_occupancy= "prosumers_data/occupancy_profiles_scen_"+str(scenario)+".csv"
        f_prosumers= "prosumers_data/prosumers_profiles_scen_"+str(scenario)+".csv"
        
        create_dat_files(f_inflexible, f_occupancy, f_prosumers, temperatures[scenario-1], prices[scenario-1], scenario)
    
   
    #gant_chart(num_bulbs, activity_profile)
    scenario_structure(number_of_scenarios)
    pass

if __name__ == "__main__":
    main()
    
    