# -*- coding: utf-8 -*-
"""
Created on Wed Dec  9 12:40:33 2020

@author: alire
"""

import pandas as pd
import random
import numpy as np
import datetime


# Custom functions
from occupancy_simulation import RunOccupancySimulation
from Lighting_simulation import lighting_load
from gant_chart import gant_chart




def configure_appliances_in_dwelling(appliances_df):
    
    """
    Set presence of appliances in the list
    """
    for j in range(len(appliances_df)):
        rnd = random.random()
        
        #Get the proportion of houses with this appliance
        proportion = appliances_df.loc[1,'Proportion_of_dwellings_with_appliance']
        
        # Determine if this simulated house has this appliance
        if rnd < proportion:
            appliances_df.at[j,'Dwelling_configuration'] = True
        else:
            appliances_df.at[j,'Dwelling_configuration'] = False
    pass



    
def new_cycle_length(mean_cycle_length, appliance_type):
    # Set the value to that provided in the configuration
    cycle_length = mean_cycle_length
    
    # Use the TV watching length data approximation, derived from the TUS data
    if appliance_type == 'TV1' or appliance_type =='TV2' or appliance_type=='TV3':
        
        # The cycle length is approximated by the following function
        # The avergage viewing time is approximately 73 minutes
        cycle_length = int(70 * ((0-np.log(1-random.random()))**1.1))
    
    if appliance_type == 'STORAGE_HEATER' or appliance_type =='ELEC_SPACE_HEATING':
        cycle_length = np.random.normal(mean_cycle_length, mean_cycle_length*0.1)
    
    return cycle_length

def get_power_usage(cycle_time_left, rated_power, appliance_type, standby_power):
    # Set the return power to the rated power
    power_usage = rated_power
    
    # Some appliances have a custom (variable) power profile depending on the time left
    if appliance_type == 'WASHING_MACHINE' or appliance_type =='WASHER_DRYER':
        total_cycle_time = 0
        
        # Calculate the washing cycle time
        if appliance_type == 'WASHING_MACHINE':
            total_cycle_time = 138
        else:
            total_cycle_time = 198
            
        # This is an example power profile for an example washing machine
        # This simplistic model is based upon data from personal communication with a major washing maching manufacturer
        case = total_cycle_time - cycle_time_left + 1
        
        if case >=1 and case <=8:
            power_usage = 73     # Start-up and fill
        elif case >=9 and case <=30:
            power_usage = 2056   # Heating
        elif case >=30 and case <=81:
            power_usage = 73     # Wash and drain
        elif case >=82 and case <=92:
            power_usage = 73     # Spin
        elif case >=93 and case <=94:
            power_usage = 250    # Rinse
        elif case >=95 and case <=105:
            power_usage = 73     # Spin
        elif case >=106 and case <=107:
            power_usage = 250    # Rinse
        elif case >=108 and case <=118:
            power_usage = 73     # Spin
        elif case >=119 and case <=120:
            power_usage = 250    # Rinse
        elif case >=121 and case <=131:
            power_usage = 73     # Spin
        elif case >=132 and case <=133:
            power_usage = 250    # Rinse
        elif case >=134 and case <=138:
            power_usage = 568    # Fast Spin
        elif case >=139 and case <=198:
            power_usage = 2500   # Drying Cycle
        else:
            power_usage = standby_power
    
    return power_usage
    
    

     
def run_appliance_simulation(activity_profile, appliances_df, activity_stats, day_type, month):
    
    # Define the relative monthly temperatures
    # Data derived from MetOffice temperature data for the Midlands in 2007
    # (http://www.metoffice.gov.uk/climate/uk/2007/) Crown Copyright
    monthly_relative_temperature_modifier = [0, 1.63, 1.821, 1.595, 0.867, 0.763, 0.191, 0.156, 0.087, 0.399, 0.936, 1.561, 1.994]    
    

    
    for appliance in range(len(appliances_df)):
        
        # Initialisation
        cycle_time_left = 0
        restart_time_left = 0
        
        # Get the appliance details
        appliance_type    =        appliances_df['Short_name'][appliance]
        mean_cycle_length =        appliances_df['Mean_cycle_length_(m)'][appliance]
        cycles_per_year   =        appliances_df['Calibrated_cycles/y_(n)'][appliance]
        standby_power     =        appliances_df['Standby_power_(W)'][appliance]
        rated_power       =        appliances_df['Mean_cycle_power_(W)'][appliance]
        calibration       =        appliances_df['Calibration_scalar'][appliance]
        ownership         =        appliances_df['Proportion_of_dwellings_with_appliance'][appliance]
        target_average_year=       appliances_df['Total_energy_(kWh/y)'][appliance]
        user_profile      =        appliances_df['Activity_use_profile'][appliance]
        restart_delay     =        appliances_df['Delay_restart_after_cycle_(m)'][appliance]
        has_appliance     =        appliances_df['Dwelling_configuration'][appliance]
        
        # store load power from each appliance
        simulation_list = [0] * len(activity_profile)
        
        if has_appliance :
            
            # Randomly delay the start of appliances that have a restart delay (e.g. cold appliances with more regular intervals)
            restart_delay_time_left = round(random.random() * restart_delay * 2)  #Weighting is 2 just to provide some diversity
            
            # Make the rated power variable over a normal distribution to provide some variation
            if rated_power :
                rated_power = abs(np.random.normal(rated_power, 0.1*rated_power))
            
            # Get the weekday or weekend flag
            if day_type == "wd":
                weekend=0
            else:
                weekend=1
            
            # Loop through each minute of the day
            minute=1
            
            while (minute <= 1440):
                # Set the default (standby) power demand at this time step
                power = standby_power
                
                # Get the ten minute period count
                ten_minute_count = (minute-1)//10
                
                # Get the number of current active occupants for this minute
                # Convert from 10 minute to 1 minute resolution
                active_occupants = activity_profile['Active_Occupancy'][minute-1]
                
                # If this appliance is off having completed a cycle (ie. a restart delay)
                if cycle_time_left <=0 and restart_delay_time_left > 0 :
                    
                    # Decrement the cycle time left
                    restart_delay_time_left -= 1
               
                # *****************************************
                # *****************************************
                
                # Else if this appliance is off
                elif cycle_time_left <= 0:
                    
                    # There must be active occupants, 
                    #or the profile must not depend on occupancy for a start event to occur
                    if (active_occupants > 0 and user_profile != 'CUSTOM') or (user_profile=='LEVEL'):
                        #Variable to store the event probability (default to 1)
                        activate_probability = 1
                        
                        # For appliances that depend on activity profiles and is not a custom profile ...
                        if user_profile != 'LEVEL' and user_profile != 'ACTIVE_OCC' and user_profile != 'CUSTOM':
                            # Get the activity statistics for this profile
                            query='Weekend_flag=='+str(weekend) +' and ' +\
                                'Active_occupant_count=='+str(active_occupants) +\
                                    ' and ' +'Appliance_name=='+ '"'+ str(user_profile)+'"'
                            activate_probability = activity_stats.query(query)[ten_minute_count+1].tolist()[0]
                        elif appliance_type == 'ELEC_SPACE_HEATING':
                            #f this appliance is an electric space heater, 
                            #then then activity probability is a function of the month of the year
                            activate_probability = monthly_relative_temperature_modifier [month]
                    
                        #Check the probability of a start event
                        if random.random() < (calibration * activate_probability):
                            # start appliance:                            
                            cycle_length = new_cycle_length(mean_cycle_length, appliance_type)
                            
                            # 1) Determine how long this appliance is going to be on for
                            cycle_time_left =cycle_length
                            
                            # 2) Determine if this appliance has a delay after the cycle before it can restart
                            restart_delay_time_left = restart_delay
                            
                            # 3) Set the power
                            power = get_power_usage(cycle_time_left, rated_power, appliance_type, standby_power)
                            
                            # 4) Decrement the cycle time left
                            cycle_time_left -= 1
                            
                            # cycle_length = start_appliance(mean_cycle_length, appliance_type)
               
                
                    # Custom appliance handler: storage heaters have a simple representation
                    elif user_profile == 'CUSTOM' and appliance_type =='STORAGE_HEATER':
                    
                        # The number of cycles (one per day) set out in the calibration sheet
                        # is used to determine whether the storage heater is used
                        
                        # This model does not account for the changes in the Economy 7 time
                        # It assumes that the time starts at 00:30 each day
                        if ten_minute_count == 4: # ie. 00:30 - 00:40
                        
                            # Assume January 14th is the coldest day of the year
                            start_date = datetime.date(1997, 1, 14)
                            
                            # Get the month and day when the storage heaters 
                            # are turned on and off, using the number of cycles per year
                            date_off = start_date + datetime.timedelta(days=cycles_per_year//2)
                            date_on  = start_date - datetime.timedelta(days=cycles_per_year//2)
                            
                            month_off = date_off.month
                            month_on  = date_on.month
                            
                            date_probability = 0
                            # If this is a month in which the appliance is turned on of off
                            if month == month_off or month == month_on :
                                #Pick a 50% chance since this month has only a month of year resolution
                                date_probability = 0.5 / 10  # (since there are 10 minutes in this period)
                            elif month > month_off and month < month_on:
                                # The appliance is not used in summer
                                date_probability = 0
                            else:
                                # The appliance is used in winter
                                date_probability = 1
                            
                            if(random.random() < date_probability):
                                # start appliance:                            
                                cycle_length = new_cycle_length(mean_cycle_length, appliance_type)
                            
                                # 1) Determine how long this appliance is going to be on for
                                cycle_time_left =cycle_length
                                
                                # 2) Determine if this appliance has a delay after the cycle before it can restart
                                restart_delay_time_left = restart_delay
                                
                                # 3) Set the power
                                power = get_power_usage(cycle_time_left, rated_power, appliance_type, standby_power)
                                
                                # 4) Decrement the cycle time left
                                cycle_time_left -= 1
                                
                
                # *****************************************
                # *****************************************
                else:
                    # The appliance is on - if the occupants become inactive, switch off the appliance
                    if active_occupants ==0 and user_profile != 'LEVEL' and user_profile != 'ACT_LAUNDRY' and user_profile != 'CUSTOM':
                        # Do nothing. The activity will be completed upon the return of the active occupancy.
                        # Note that LEVEL means that the appliance use is not related to active occupancy.
                        # Note also that laundry appliances do not switch off upon a transition to inactive occupancy.
                        aaa=0
                    else:
                        #Set the power
                        power = get_power_usage(cycle_time_left, rated_power, appliance_type, standby_power)
                        
                        #Decrement the cycle time left
                        cycle_time_left -=1
                
                # *****************************************
                # *****************************************
                
                # Set the appliance power at this time step
                simulation_list[minute-1]=power   
                
                # Increment the time
                minute +=1 
            
            # ******* end of while *************
            
            # Add the appliance loads to activity profile
            activity_profile[appliance_type] = simulation_list
            
        
       

    pass

def main():
    # Datas file
    f_name="Data.xlsx"
    
    # Set the week day
    # wd = weekday 
    # we = weekend
    day_type='wd'
    
    
    # Set the month between 1 to 12
    month_list=['January','February','March','April','May','June','July','August','September','October','November','December']
    month=2
    
    # Set the number of residents in the house
    # Random number between 1 to 5
    residents=2
    
    # Select Irradiance data for the selected month
    sheet="Irradiance"
    Month=month_list[month-1]
    activity_profile=pd.read_excel(f_name,sheet_name=sheet)
        
    activity_profile=activity_profile[['Minute_of_day','reference',Month]]
    # It will store the activity profile for the house
    activity_profile=activity_profile.astype({'Minute_of_day':int,Month:int})
    
    
    #Step 1: Determine the active occupancy start state between 00:00 and 00:10
    if day_type=='wd':
        sheet='Weekday'
    else:
        sheet='Weekend'
    
    
    # Load Transition probaility between occupancy for start states
    transition_prob=pd.read_excel(f_name,sheet_name=sheet)
    
    
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
    
    activity_profile.to_csv("simulation_profile.csv", header=True)
    
    gant_chart(num_bulbs, activity_profile)
    pass

if __name__ == "__main__":
    main()
    
    