# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 13:38:51 2021

@author: alire
"""

from pyomo.environ import *
from csv import writer
import time

def model_to_csv(model):
    timestr = time.strftime("%Y%m%d-%H%M%S")

    
    row=['DAs_load', 'DAs_generation', 'DAs_demand_bid','DAs_supply_offer',\
         'EVs_Charge', 'EVs_Discharge', 'TCL_Power', 'SL_Power',\
             'Gen1','Gen2','Gen3','CDA1_suply','CDA2_supply', 'CDA1_demand', 'CDA2_demand',\
                 'Bus1_price','Bus2_price','Bus3_price']
    list_row=[]
    list_row.append(row)
    
    
    
    for t in model.T:
        row=[]
        row.append(value(model.E_DA_L[t]))
        row.append(value(model.E_DA_G[t]))
        row.append(value(model.DA_demand[t]))
        row.append(value(model.DA_supply[t]))
        
        row.append(sum(value(model.E_EV_CH[i,t]) for i in model.N))
        row.append(sum(value(model.E_EV_DIS[i,t]) for i in model.N))
        
        row.append(sum(value(model.POWER_TCL[i,t]) for i in model.N))
        row.append(sum(value(model.POWER_SL[i,t]) for i in model.N))
        
        for g in model.G:
            row.append(value(model.g[g,t]))
        
        for cda in model.NCDA:
            row.append(value(model.d_o[cda,t]))
        
        for cda in model.NCDA:
            row.append(value(model.d_b[cda,t]))
            
        for b in model.BUS:
            row.append(value(model.Lambda[b,t]))
                
        list_row.append(row)
    
    model_file='Model_data_'+timestr+'.csv'
    with open(model_file, 'w', newline='') as file:
        csv_writer = writer(file)
        for rw in list_row:
                csv_writer.writerow(rw)