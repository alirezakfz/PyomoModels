# -*- coding: utf-8 -*-
"""
Created on Sun Jan  3 12:36:16 2021

@author: alire
"""

import pandas as pd
import time
from pyomo.environ import *

def save_model(model, installed_chargers, demand,EV_samples,arrival, depart):
    
    col = ["EV_Number","EV_Type","Arrival","Depart","Demand","AssignedCharger","ChargerType","Delay","Total_load"]
    data=pd.DataFrame(columns=(col))
    data["EV_Number"]=[x for x in range(1,len(arrival)+1)]
    data["Arrival"]  = arrival
    data["Depart"]   = depart
    data["Demand"]   = demand
    data["EV_Type"]  = EV_samples
    
    Assigned_chargers=[]
    charger_type=[]
    
    for i in model.N:
        for j in model.M:
            if value(model.y[i,j])==1:
                Assigned_chargers.append(value(j))
                charger_type.append(installed_chargers[value(j)-1])
    
    data["AssignedCharger"]= Assigned_chargers
    data["ChargerType"]    = charger_type
    
    delay=[]
    for i in model.N:
        temp = sum(value(model.c[i,t]*t) for t in model.T) 
        delay.append(temp)
    
    data["Delay"] = delay
    
    load=[]
    for i in model.N:
        temp=sum(value(model.p[i,j,t]) for j in model.M for t in model.T)
        load.append(temp)
    
    data["Total_load"] = load
    
    target_file = "result_"+time.strftime("%Y%m%d_%H%M%S")+".csv"
    data.to_csv(target_file, index=False)
    pass