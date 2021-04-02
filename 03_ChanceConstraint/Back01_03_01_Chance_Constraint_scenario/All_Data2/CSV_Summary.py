# -*- coding: utf-8 -*-
"""
Created on Mon Feb  1 23:30:08 2021

@author: Alireza
"""
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import norm

# Reading the raw data
model_info=pd.read_csv('Model_Data_All.csv')
evs_info=pd.read_csv('EVs_Info_All.csv')

# Summary/Mean of delays for all models
def delay_file(data):
    
    delay_info=pd.DataFrame(columns=['Model','Scenario','Number_of_EVs','Delay'],data=data)
    # delay_info=delay_info.drop(delay_info[delay_info.Model=='NoDelay'].index)
    # delay_info['DelayCeil']=delay_info['Delay'].apply(np.ceil)
    
    delay_info=delay_info.groupby(['Model','Scenario','Number_of_EVs']).sum()
    delay_info.reset_index(inplace=True)
    
    # delay_info['Delay']= delay_info['Delay'] / delay_info['Number_of_EVs']
    
    delay_info.drop('Scenario',axis='columns', inplace=True)
    
    delay_info=delay_info.groupby(['Model','Number_of_EVs']).mean()
    delay_info.reset_index(inplace=True)
    
    delay_info.to_csv('Summary/delay_info.csv', index=False)
    pass

delay_file(evs_info)


# Summary/Mean of Gama for all models
def gama_info(data):
    data=evs_info
    gama=pd.DataFrame(columns=['Model','Scenario','Number_of_EVs','Delay'],data=data)
    # gama=gama.drop(gama[gama.Model=='NoDelay'].index)
    
    gama=gama.groupby(['Model','Scenario','Number_of_EVs']).sum()
    gama.reset_index(inplace=True)
    
    gama['Delay']= gama['Delay'] / gama['Number_of_EVs']
    
    gama.drop('Scenario',axis='columns', inplace=True)
    
    gama=gama.groupby(['Model','Number_of_EVs']).mean()
    gama.reset_index(inplace=True)
    
    gama.to_csv('Summary/gama_info.csv',index=False)
    
    
    pass

gama_info(evs_info)


# Summary/mean of installation cost
def installation_cost(data):
    # data=model_info
    obj=pd.DataFrame(data=data, columns=['Model', 'number_of_EVs','Installation_cost'])
    obj=obj.groupby(['Model', 'number_of_EVs']).mean()
    obj.reset_index(inplace=True)
    
    obj.to_csv('Summary/installation_cost_info.csv', index=False)
    
    pass

installation_cost(model_info)


#Summary/mean of charging cost
def charging_cost(data):
    # data=model_info
    obj=pd.DataFrame(data=data, columns=['Model', 'number_of_EVs','load_price'])
    obj=obj.groupby(['Model', 'number_of_EVs']).mean()*10000
    obj.reset_index(inplace=True)
    
    obj.to_csv('Summary/charging_cost_info.csv', index=False)
    
    pass

charging_cost(model_info)


def chargers_info(data):
    # data=model_info
    # chargers=pd.DataFrame(data=data, columns=['Model', 'number_of_EVs', 'InstalledType_4', 'InstalledType_8', 'InstalledType_19'])
    chargers=pd.DataFrame(data=data, columns=['number_of_EVs', 'InstalledType_4', 'InstalledType_8', 'InstalledType_19'])
    
    # chargers=chargers.groupby(['Model', 'number_of_EVs']).sum()
    chargers=chargers.groupby(['number_of_EVs']).sum()
    
    chargers.reset_index(inplace=True)
    chargers['sum']=chargers.loc[:,'InstalledType_4':'InstalledType_19'].sum(axis=1)
    chargers.loc[:,'InstalledType_4':'InstalledType_19']=chargers.loc[:,'InstalledType_4':'InstalledType_19'].div(chargers['sum'],axis=0)
    
    chargers.drop('sum',axis='columns',inplace=True)
    # chargers.drop('Model', axis='columns', inplace=True)
    chargers=pd.melt(chargers, id_vars='number_of_EVs',  var_name='Levels', value_name='Count')
    
    chargers['Levels'].replace({'InstalledType_4':'Level 1', 'InstalledType_8':'Level 2', 'InstalledType_19':'Level 3'},inplace=True)
    
    chargers.to_csv('Summary/installed_chargers_info.csv', index=False)
    
    pass

chargers_info(model_info)

def evs_chargers_info(data):
    data=evs_info
    EV_types=pd.DataFrame(columns=['Model','EV_Type','Alloc_charger'],data=data)
    
    # EV_types=EV_types.drop(EV_types[EV_types.Model=='FreeDelay'].index)
    
    # EV_types=EV_types.drop(EV_types[EV_types.Model=='OneSlotDelay'].index)
    
    EV_types.drop('Model', axis='columns', inplace=True)    
    EV_types['count']=0
    
    
    EV_types=EV_types.groupby(['EV_Type','Alloc_charger']).count()
    EV_types.reset_index(inplace=True)
    
    EV_types['count']=100*EV_types['count']/EV_types['count'].sum()
    EV_types['Alloc_charger'].replace({4.0:'Level 1', 8.0:'Level 2', 19.0:'Level 3', 50.0:'Level 4'},inplace=True)

    EV_types.to_csv('Summary/EVs_to_Chargers_info.csv',index=False)
    
    pass

evs_chargers_info(evs_info)


def installed_chargers_info(data):
    
    chargers=pd.DataFrame(data=data, columns=['Model', 'InstalledType_4', 'InstalledType_8', 'InstalledType_19'])
    
    chargers=chargers.groupby(['Model']).sum()
    chargers.reset_index(inplace=True)
    
    chargers=pd.melt(chargers, id_vars='Model',  var_name='Levels', value_name='Count')
    chargers['Levels'].replace({'InstalledType_4':'Level 1', 'InstalledType_8':'Level 2', 'InstalledType_19':'Level 3'},inplace=True)
    
    chargers.to_csv('Summary/installed_chargers_info_2.csv', index=False)
    pass

installed_chargers_info(model_info)