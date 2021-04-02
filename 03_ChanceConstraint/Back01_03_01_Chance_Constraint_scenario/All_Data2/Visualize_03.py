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
compare_info= pd.read_csv('Model_data_FCFS_85EVs.csv')


"""
Figure 1: 
    Percentage of installed chargers of each charger type for different numbers of EVs
"""
def chargers_plot(data, axes):
    data=model_info
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
    
    
    #Range to drop from plot
    x_range=np.arange(10,40,5)
    for x in x_range:
        indexes = chargers[chargers['number_of_EVs']==x].index
        chargers.drop(indexes, inplace=True)
    
    # ss_colors=['purple','brown','red']
    chargers['Levels'].replace({'InstalledType_4':'Level 1', 'InstalledType_8':'Level 2', 'InstalledType_19':'Level 3'},inplace=True)
    sns.barplot(x='number_of_EVs', y='Count' , hue='Levels', data=chargers, ax=axes) #palette=ss_colors
    axes.set(xlabel='Number of EVs', ylabel='Percentage of installed chargers')
    
    labels=['Level 1', 'Level 2', 'Level 3']
    h, l = axes.get_legend_handles_labels()
    axes.legend(h, labels, title="")
    
    return axes
      
fig_ch, axes_ch=plt.subplots()
axes_ch=chargers_plot(model_info, axes_ch)
# axes_ch.set_rasterized(True)
fig_ch.savefig('SS_ChargerPercentages.eps')
plt.show() 


"""
EV Types Analysis

Figure 2:
    Percentages of EV assignments to each charger type, for all EV types
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
    axes.set(xlabel="Types of EVs", ylabel='Percentage of EV assignment to charger type')
    
    labels=['Level 1', 'Level 2', 'Level 3']
    h, l = axes.get_legend_handles_labels()
    axes.legend(h, labels, title="")
    return axes

fig_ev, axes_ev=plt.subplots()
axes_ev=evs_plot(evs_info, axes_ev)
# axes_ev.set_rasterized(True)
# fig_ev.savefig('EV_Types_to_Chargers.eps')
fig_ev.savefig('Assignments.eps')
  

"""
Figure 3:
    Cost of installing chargers
"""
def objective_plot(data, axes):
    # data=model_info
    obj=pd.DataFrame(data=data, columns=['Model', 'number_of_EVs','obj_value'])
    obj=obj.groupby(['Model', 'number_of_EVs']).mean()
    obj.reset_index(inplace=True)
    sns.lineplot(x='number_of_EVs', y='obj_value', hue='Model', data=obj,
                 ax=axes, style=True, dashes=[(2,2)],markers= ["o"])
    axes.set(xlabel='Number of EVs', ylabel='Average cost of installed chargers ($)', 
             title='', xticks=np.arange(10,65,5))
    
    axes.legend(['NoDelay', 'OneSlotDelay'])
    return axes
    
fig_obj, axes_obj = plt.subplots()
axes_obj=objective_plot(model_info, axes_obj)
# axes_obj.set_rasterized(True)
fig_obj.savefig('cost.eps')



"""
Figure 4:
    Probability of suffering delay for different numbers of 
"""
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
    
    
    
    sns.lineplot(x='Number_of_EVs', y='Delay', hue='Model', data=gama, ax=axes,
                 style=True, dashes=[(2,2)],markers= ["o"] )  
    axes.set(ylabel='Probability of suffering delay ('r'$\frac{\sum\zeta_i}{|N|}$)', xlabel='Number of EVS', xticks=np.arange(10,65,5))
    
    axes.legend(['NoDelay', 'OneSlotDelay'])
    return axes

fig_gama, axes_gama=plt.subplots()
axes_gama=gama_plot(evs_info, axes_gama)
# axes_gama.set_rasterized(True)
fig_gama.savefig('Delay_Probability.eps')
 


"""
Figure 5:
    Comparison of the cost of installed chargers as a function of arriving tasks for smart charging and first-come-first-serve
"""

def FCS_smart_comparison(data, axes):
    # data= compare_info
    info = pd.DataFrame(columns=['Model','obj_value','number_of_EVs'],data=data)
    
    info = info.loc[info['number_of_EVs']<70]
    
    info=info.groupby(['Model', 'number_of_EVs']).mean()
    info.reset_index(inplace=True)
    
    sns.lineplot(x='number_of_EVs', y='obj_value', hue='Model', data=info, ax=axes,
                 style=True, dashes=[(2,2)],markers= ["o"] )
    
    axes.set(ylabel='Cost of installed chargers', xlabel='Number of EVS', xticks=np.arange(10,70,5))
    axes.legend(['Smart charging', 'FCS'])
    
    return axes

fig_compare, axes_compare=plt.subplots()
axes_compare=FCS_smart_comparison(compare_info, axes_compare)
fig_compare.savefig('Comparison.eps')


"""
Figure 6: new 
    Comparison of paid charging price
"""

def charging_price(data, axes):
    # data = model_info
    w=10000
    info = pd.DataFrame(columns=['Model','load_price','number_of_EVs'],data=data)
    
    info=info.groupby(['Model', 'number_of_EVs']).mean()
    info.reset_index(inplace=True)
    
    info['load_price'] = w*info['load_price']
    
    sns.lineplot(x='number_of_EVs', y='load_price', hue='Model', data=info, ax=axes,
                 style=True, dashes=[(2,2)],markers= ["o"] )
    
    axes.set(ylabel='Charging price', xlabel='Number of EVS', xticks=np.arange(10,70,5))
    axes.legend(['NoDelay', 'OneSlotDelay'])
    
    return axes

fig_price, axes_price=plt.subplots()
axes_price=charging_price(model_info, axes_price)
fig_price.savefig('ChargingPrice.eps')



"""
New models together
Figure 3
""" 
  
compare_info=pd.read_csv('Model_Data_BothModels_70EVS.csv')

def all_models(data, axes):
    data=compare_info
    # columns=['Model', 'number_of_EVs', 'InstalledType_4', 'InstalledType_8', 'InstalledType_19']
    info = pd.DataFrame(columns=['Model', 'number_of_EVs', 'InstalledType_4', 'InstalledType_8', 'InstalledType_19'],data=data)
    
    info = info.loc[info['number_of_EVs']<70]
    info.drop('number_of_EVs',axis='columns',inplace=True)
    
    info['Model'].replace({'CC_OneSlotDelay':'SmartCharging_OneSlotDelay'}, inplace=True)
    info['Model'].replace({'CC_NoDelay':'SmartCharging_NoDelay'},inplace=True)
    info['Model'].replace({'OneSlotDelay':'SmartScheduling_OneSlotDelay'},inplace=True)
    info['Model'].replace({'FreeDelay':'SmartScheduling_FreeDelay'},inplace=True)
    info['Model'].replace({'NoDelay':'SmartScheduling_NoDelay'},inplace=True)
    
    xticks=["Smart Charging\nOneSlotDelay",
            "Smart Charging\nNoDelay",
            "FCFS",
            "Smart Scheduling\nOneSlotDelay",
            "Smart Scheduling\nFreeDelay",
            "Smart Scheduling\nNoDelay"]
    # info=info.groupby(['Model', 'number_of_EVs']).sum()
    info=info.groupby(['Model']).sum()
    info.reset_index(inplace=True)
    
    
    
    info['sum']=info.loc[:,'InstalledType_4':'InstalledType_19'].sum(axis=1)
    info.loc[:,'InstalledType_4':'InstalledType_19']=info.loc[:,'InstalledType_4':'InstalledType_19'].div(info['sum'],axis=0)
    info.drop('sum',axis='columns',inplace=True)
    
    info=pd.melt(info, id_vars='Model',  var_name='Levels', value_name='Count')
    
    info['Levels'].replace({'InstalledType_4':'Level 1', 'InstalledType_8':'Level 2', 'InstalledType_19':'Level 3'},inplace=True)
    
    orders=['SmartCharging_NoDelay','SmartCharging_OneSlotDelay','FCFS','SmartScheduling_NoDelay','SmartScheduling_OneSlotDelay','SmartScheduling_FreeDelay']
    sns.barplot(x='Model', y='Count' , hue='Levels', data=info, ax=axes, order=orders) #palette=ss_colors
    # axes.set(xlabel='Models', ylabel='Percentage of installed chargers in all scenarios')
    
    labels=['Level 1', 'Level 2', 'Level 3']
    h, l = axes.get_legend_handles_labels()
    axes.legend(h, labels, title="")
    
    axes.set_xticklabels(xticks,rotation=20)
    plt.ylabel('Percentage of installed chargers in all scenarios',size=12)
    plt.xlabel('Models',size=12)
    plt.xticks(size=14)
    plt.yticks(size=14)
    # plt.xticks(rotation=20)
    
    return axes

fig_allModels, axes_allModels=plt.subplots()
axes_allModels=all_models(compare_info, axes_allModels)

fig_allModels.savefig('all_models_chargers.eps')


# Plotting models costs
def all_models_cost(data,axes):
    # data=compare_info
    # axes=axes_allCosts
    info=pd.DataFrame(data=data, columns=['Model', 'number_of_EVs','Installation_cost'])
    
    indexes = info[info['number_of_EVs'] > 70].index
    info.drop(indexes, inplace=True)
    
    """
    Plot only for smart charging, smart scheduling, FSFS
    """
    temp=info.copy(deep=True)
    # temp = temp.loc[temp['Model'].isin(['FCFS','CC_OneSlotDelay','OneSlotDelay'])]
    # # temp=temp.groupby(['Model','number_of_EVs']).mean()
    # temp.reset_index(inplace=True)
    # temp['Model'].replace({'CC_OneSlotDelay':'Smart Charging', 'OneSlotDelay':'Smart Scheduling'}, inplace=True)
    # sns.lineplot(x='number_of_EVs', y='Installation_cost', hue='Model', data=temp, ax=axes, style=True, dashes=[(2,2)],markers= ["o"],ci='sd' )
    # axes.set(ylabel='Average cost of installed chargers $', xlabel='Number of EVS', xticks=np.arange(10,75,5))
    # axes.legend(['Smart Charging','FCFS', 'Smart Scheduling'])
    
   
    """
    Plot whole data with boundary
    """
    info['Model'].replace({'CC_OneSlotDelay':'Smart Charging'}, inplace=True)
    info['Model'].replace({'CC_NoDelay':'Smart Charging'},inplace=True)
    info['Model'].replace({'OneSlotDelay':'Smart Scheduling'},inplace=True)
    info['Model'].replace({'FreeDelay':'Smart Scheduling'},inplace=True)
    info['Model'].replace({'NoDelay':'Smart Scheduling'},inplace=True)
    # Finding the Max for models
    info=info.groupby(['Model','number_of_EVs']).max()
    info.reset_index(inplace=True)
    sns.lineplot(x='number_of_EVs', y='Installation_cost', hue='Model', data=info, ax=axes, style=True, dashes=[(2,2)],markers= ["o"], ci='sd' )  
    axes.set(ylabel='Cost of installed chargers $', xlabel='Number of EVS', xticks=np.arange(10,75,5))
    axes.legend(['Smart Charging', 'Smart Scheduling','FCFS'])
                        
    
    # indexes = info[info['number_of_EVs'] < 40].index
    # info.drop(indexes, inplace=True)
    
    
    
    # info=info.groupby(['Model','number_of_EVs']).mean()
    # info.reset_index(inplace=True)
    
    # sns.lineplot(x='number_of_EVs', y='Installation_cost', hue='Model', data=info, ax=axes, style=True, dashes=[(2,2)],markers= ["o"] )  
    # axes.set(ylabel='Average cost of installed chargers $', xlabel='Number of EVS', xticks=np.arange(10,75,5))
    
    # axes.legend(['Smart Charging','FCFS', 'Smart Scheduling'])
    return axes

fig_allCosts, axes_allCosts=plt.subplots()
axes_allCosts=all_models_cost(compare_info, axes_allCosts)
fig_allCosts.savefig('all_models_cost_02.eps')

"""
Extra Plots
"""
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

# delay_fig, delay_ax=plt.subplots()
# delay_ax=delay_plot(evs_info, delay_ax )
# plt.show()
# delay_fig.savefig('delay.eps')


def arrival_plot(data, axes):
    # data=evs_info    
    sns.distplot(data['Arrival'],  kde=False, ax=axes) #fit=norm
    axes.set(xlabel='Arrival Time', ylabel='Distribution')
    
    return axes

# fig_arr, axes_arr=plt.subplots()
# axes_arr=arrival_plot(evs_info, axes_arr)
# axes_arr.set_rasterized(True)
# fig_arr.savefig('ArrivalDistribution.eps')


def depart_plot(data, axes):
    sns.distplot(evs_info['Depart'],  kde=False, ax=axes) #fit=norm
    axes.set(xlabel='Depart Time', ylabel='Distribution')
    
    return axes

# fig_dep, axes_dep=plt.subplots()
# axes_dep=depart_plot(evs_info, axes_dep)
# # axes_dep.set_rasterized(True)
# fig_arr.savefig('DepartDistribution.eps')




  

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

# fig_install, ax_install=plt.subplots()
# ax_install=charger_install(model_info, ax_install)
# # ax_install.set_rasterized(True)
# fig_install.savefig('Number_of_InstalledChargers.eps')
