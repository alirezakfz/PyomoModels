# -*- coding: utf-8 -*-
"""
Created on Mon Oct 12 12:02:25 2020

@author: Ali
"""
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import norm

model_info=pd.read_csv('Model_Data_All.csv')
evs_info=pd.read_csv('EVs_Info_All.csv')





def delay_plot(data, axes):
        
    
    delay_info=pd.DataFrame(columns=['Model','Scenario','Number_of_EVs','Delay'],data=data)
    delay_info=delay_info.drop(delay_info[delay_info.Model=='NoDelay'].index)
    # delay_info['DelayCeil']=delay_info['Delay'].apply(np.ceil)
    
    delay_info=delay_info.groupby(['Model','Scenario','Number_of_EVs']).sum()
    delay_info.reset_index(inplace=True)
    
    # delay_info['Delay']= delay_info['Delay'] / delay_info['Number_of_EVs']
    
    delay_info.drop('Scenario',axis='columns', inplace=True)
    
    delay_info=delay_info.groupby(['Model','Number_of_EVs']).mean()
    delay_info.reset_index(inplace=True)
    
    # delay_info['Delay']= 100*delay_info['Delay'] / delay_info['Number_of_EVs']
    sns.lineplot(x='Number_of_EVs',y='Delay',hue='Model',data=delay_info, ax=axes)   
    axes.set(ylabel='Average Delay', xlabel='Number of EVS')
    
                   
    return axes

delay_fig, delay_ax=plt.subplots()
delay_ax=delay_plot(evs_info, delay_ax )
# delay_ax.set_rasterized(True)
plt.show()
delay_fig.savefig('delay.eps')



def gama_plot(data, axes):
    # data=evs_info
    gama=pd.DataFrame(columns=['Model','Scenario','Number_of_EVs','Delay'],data=data)
    gama=gama.drop(gama[gama.Model=='NoDelay'].index)
    
    gama=gama.groupby(['Model','Scenario','Number_of_EVs']).sum()
    gama.reset_index(inplace=True)
    
    gama['Delay']= gama['Delay'] / gama['Number_of_EVs']
    
    gama.drop('Scenario',axis='columns', inplace=True)
    
    gama=gama.groupby(['Model','Number_of_EVs']).mean()
    gama.reset_index(inplace=True)
    
    
    
    sns.lineplot(x='Number_of_EVs', y='Delay', hue='Model', data=gama, ax=axes)  
    axes.set(ylabel='Gama 'r'$\frac{\sum\zeta_i}{|N|}$', xlabel='Number of EVS')
    
    return axes

fig_gama, axes_gama=plt.subplots()
axes_gama=gama_plot(evs_info, axes_gama)
# axes_gama.set_rasterized(True)
fig_gama.savefig('gamaplot.eps')
 


    
def objective_plot(data, axes):
    # data=model_info
    obj=pd.DataFrame(data=data, columns=['Model', 'number_of_EVs','obj_value'])
    obj=obj.groupby(['Model', 'number_of_EVs']).mean()
    obj.reset_index(inplace=True)
    sns.lineplot(x='number_of_EVs', y='obj_value', hue='Model', data=obj, ax=axes)
    axes.set(xlabel='Number of EVs', ylabel='Average of installation cost', title='')
    return axes
    
fig_obj, axes_obj = plt.subplots()
axes_obj=objective_plot(model_info, axes_obj)
# axes_obj.set_rasterized(True)
fig_obj.savefig('Objective.eps')




def chargers_plot(data, axes):
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
    
    chargers['Levels'].replace({'InstalledType_4':'Level1', 'InstalledType_8':'Level_2', 'InstalledType_19':'Level_3'},inplace=True)
    sns.barplot(x='number_of_EVs', y='Count' , hue='Levels', data=chargers, ax=axes)
    axes.set(xlabel='Number of EVs', ylabel='Percentage of installation')
    
    return axes
      
fig_ch, axes_ch=plt.subplots()
axes_ch=chargers_plot(model_info, axes_ch)
# axes_ch.set_rasterized(True)
fig_ch.savefig('chargers_installations.eps')
plt.show() 
    

"""
Analysing EVS information
""" 
    
def arrival_plot(data, axes):
    # data=evs_info    
    sns.distplot(data['Arrival'],  kde=False, ax=axes) #fit=norm
    axes.set(xlabel='Arrival Time', ylabel='Distribution')
    
    return axes

fig_arr, axes_arr=plt.subplots()
axes_arr=arrival_plot(evs_info, axes_arr)
axes_arr.set_rasterized(True)
fig_arr.savefig('ArrivalDistribution.eps')


def depart_plot(data, axes):
    sns.distplot(evs_info['Depart'],  kde=False, ax=axes) #fit=norm
    axes.set(xlabel='Depart Time', ylabel='Distribution')
    
    return axes

fig_dep, axes_dep=plt.subplots()
axes_dep=depart_plot(evs_info, axes_dep)
# axes_dep.set_rasterized(True)
fig_arr.savefig('DepartDistribution.eps')


"""
EV Types Analysis
"""
def evs_plot(data, axes):
    EV_types=pd.DataFrame(columns=['Model','EV_Type','Alloc_charger'],data=data)
    
    # EV_types=EV_types.drop(EV_types[EV_types.Model=='FreeDelay'].index)
    
    # EV_types=EV_types.drop(EV_types[EV_types.Model=='OneSlotDelay'].index)
    
    EV_types.drop('Model', axis='columns', inplace=True)    
    EV_types['count']=0
    
    
    EV_types=EV_types.groupby(['EV_Type','Alloc_charger']).count()
    EV_types.reset_index(inplace=True)
    
    EV_types['count']=100*EV_types['count']/EV_types['count'].sum()
    EV_types['Alloc_charger'].replace({4.0:'Level1', 8.0:'Level_2', 19.0:'Level_3', 50.0:'Level_4'},inplace=True)

        
    #EVs Allocation to Chargers
    sns.barplot(x='EV_Type', y='count', hue='Alloc_charger', data=EV_types, order=['Small','Sedan','SUV','Truck'],ax=axes)
    axes.set(xlabel="Types of EVs", ylabel='percentage of assignment')
    
    return axes

fig_ev, axes_ev=plt.subplots()
axes_ev=evs_plot(evs_info, axes_ev)
# axes_ev.set_rasterized(True)
fig_ev.savefig('EV_Types_to_Chargers.eps')
  

  

def charger_install(data, axes):
    data=model_info
    chargers=pd.DataFrame(data=data, columns=['Model', 'InstalledType_4', 'InstalledType_8', 'InstalledType_19'])
    
    chargers=chargers.groupby(['Model']).sum()
    chargers.reset_index(inplace=True)
    
    chargers=pd.melt(chargers, id_vars='Model',  var_name='Levels', value_name='Count')
    chargers['Levels'].replace({'InstalledType_4':'Level1', 'InstalledType_8':'Level_2', 'InstalledType_19':'Level_3'},inplace=True)
    
    
    sns.barplot(x='Levels', y='Count' ,hue='Model',  data=chargers, ax=axes)
    axes.set(xlabel='Charger levels', ylabel='Installation')
    
    return axes

fig_install, ax_install=plt.subplots()
ax_install=charger_install(model_info, ax_install)
# ax_install.set_rasterized(True)
fig_install.savefig('InstalledChargers.eps')