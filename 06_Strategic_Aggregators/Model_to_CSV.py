# -*- coding: utf-8 -*-
"""
Created on Wed Mar 31 13:38:51 2021

@author: alire
"""

from pyomo.environ import *
from csv import writer
import time

def model_to_csv(model, IN_loads):
    timestr = time.strftime("%Y%m%d-%H%M%S")

    
    row=['DAs_load\nE_DAs_L', 'DAs_generation\nE_DAs_G', 'DAs_demand_bid\nb_t','DAs_supply_offer\no_t',\
         'EVs_Charge', 'EVs_Discharge', 'TCL_Power', 'SL_Power', 'Inflexible_loads']
    
    for g in model.G:
        row.append('Gen'+str(value(g)))
    
    for cda in model.NCDA:
        row.append('CDA'+str(value(cda))+'_supply')
    
    for cda in model.NCDA:
        row.append('CDA'+str(value(cda))+'_demand')
    
    for b in model.BUS:
        row.append('Bus'+str(value(b))+'_price')
    
    for b in model.BUS:
        row.append('Theta_bus_'+str(value(b)))
             
    list_row=[]
    list_row.append(row)
    
    
    
    for t in model.T:
        row=[]
        row.append(value(model.E_DA_L[t]))
        row.append(value(model.E_DA_G[t]))
        row.append(value(model.DA_demand[t]))
        row.append(value(model.DA_supply[t]))
        
        row.append(sum(value(model.E_EV_CH[i,t]) for i in model.N)/1000)
        row.append(sum(value(model.E_EV_DIS[i,t]) for i in model.N)/1000)
        
        row.append(sum(value(model.POWER_TCL[i,t]) for i in model.N)/1000)
        row.append(sum(value(model.POWER_SL[i,t]) for i in model.N)/1000)
        row.append(IN_loads[t-16]/1000)
        
        for g in model.G:
            row.append(value(model.g[g,t]))
        
        for cda in model.NCDA:
            row.append(value(model.d_o[cda,t]))
        
        for cda in model.NCDA:
            row.append(value(model.d_b[cda,t]))
            
        for b in model.BUS:
            row.append(value(model.Lambda[b,t]))
        
        for b in model.BUS:
            row.append(value(model.teta[b,t]))
            
        list_row.append(row)
    
    model_file='Model_CSV/Model_data_'+timestr+'.csv'
    with open(model_file, 'w', newline='') as file:
        csv_writer = writer(file)
        for rw in list_row:
                csv_writer.writerow(rw)
    
    
    row=[]
    list_row=[]
    
    row.append('F_min_DAo')
    row.append('F_max_DAo')
    row.append('F_min_DAb')
    row.append('F_max_DAb')
    
    for g in model.G:
        row.append('F_min_g_'+str(value(g)))
        row.append('F_max_g_'+str(value(g)))
    
    for cda in model.NCDA:
        row.append('F_min_do_'+str(value(cda)))
        row.append('F_max_do_'+str(value(cda)))
    
    for cda in model.NCDA:
        row.append('F_min_db_'+str(value(cda)))
        row.append('F_max_db_'+str(value(cda)))
    
    for l in model.LINES:
        row.append('F_min_l_'+str(value(l)))
        row.append('F_max_l_'+str(value(l)))
    
    
    list_row.append(row)
    for t in model.T:
        row=[]
        row.append(value(model.w_DAo_low[t]))
        row.append(value(model.w_DAo_up[t]))
        row.append(value(model.w_DAb_low[t]))
        row.append(value(model.w_DAb_up[t]))
        
        for g in model.G:
            row.append(value(model.w_g_low[g,t]))
            row.append(value(model.w_g_up[g,t]))
        
        for cda in model.NCDA:
            row.append(value(model.w_do_low[cda,t]))
            row.append(value(model.w_do_up[cda,t]))
        
        for cda in model.NCDA:
            row.append(value(model.w_db_low[cda,t]))
            row.append(value(model.w_db_up[cda,t]))
        
        for l in model.LINES:
            row.append(value(model.w_line_low[l,t]))
            row.append(value(model.w_line_up[l,t]))
        
        list_row.append(row)
        
    
    dual_file='Model_CSV/Model_dual_variables_'+timestr+'.csv'
    with open(dual_file, 'w', newline='') as file:
        csv_writer = writer(file)
        for rw in list_row:
                csv_writer.writerow(rw)
    