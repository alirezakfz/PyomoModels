# -*- coding: utf-8 -*-
"""
Created on Wed Apr 14 19:02:14 2021

@author: alire
"""

from pyomo.environ import *
import time



# Constraint (b.2), power balance at each bus i of the power grid, that must hold at every timeslot t. 
def network_power_balance_rule(model, B, dic_G, dic_Bus_CDA, DABus):
    check=True
    error =[]
    for i in model.BUS:
        for t in model.T:
            sum1=0
            if i in dic_G.keys():
                sum1=sum(-value(model.g[x,t]) for x in dic_G[i])
            
            sum3=0
            sum2=0
            if i in dic_Bus_CDA.keys() :
                if i == DABus:
                    sum2= -value(model.E_DA_G[t])
                    sum3= value(model.E_DA_L[t])
                else:
                    x=dic_Bus_CDA[i]
                    sum3 =value(model.d_b[x,t])   # if x != 'DAs'
                    sum2 = -value(model.d_o[x,t])
            
            sumB = sum(B[i-1,j-1]*value(model.teta[j,t]) for j in model.BUS)
            sum_t= round(sum1+sum2+sum3+sumB,2)
        
            if sum_t  != 0:
                check=False
                error.append((i,t,sum_t))
    return check, error  #+ model.b2_1[i,t] - model.b2_2[i,t]


# Constraint (C.1) generators dual price
def generator_dual_price_rule(model, c_g, dic_G_Bus):
    check=True
    error =[]
    for i in model.G:
        for t in model.T:
            bus=dic_G_Bus[i]
            sum_t =  c_g[i][t-16]-value(model.Lambda[bus,t]) - value(model.w_g_low[i,t]) + value(model.w_g_up[i,t])
        
            sum_t = round(sum_t,2)
            if sum_t != 0:
                check=False
                error.append((i,t,sum_t))
    return check, error  #+ model.c1_1[i,t] - model.c1_2[i,t]


# Constrint (C.2) competitor suuply to grid offer
def competitor_offer_dual_rule(model, dic_CDA_Bus, c_d_o):
    check=True
    error =[]
    
    for i in model.NCDA:
        bus=dic_CDA_Bus[i]
        for t in model.T:
            sum_t=round(c_d_o[i][t-16] - value(model.Lambda[bus,t]) - value(model.w_do_low[i,t]) + value(model.w_do_up[i,t]),2)
        
            if sum_t != 0:
                check=False
                error.append((i,t,sum_t))
    return check, error  #c_d_o[i][t-16]


# Constraint (C.3) competitors demand bid
def competitor_demand_dual_rule(model, c_d_b, dic_CDA_Bus):
    check=True
    error =[]
    
    for i in model.NCDA:
        bus=dic_CDA_Bus[i]
        for t in model.T:
            sum_t = round(-c_d_b[i][t-16] + value(model.Lambda[bus,t]) - value(model.w_db_low[i,t]) + value(model.w_db_up[i,t]),2)
        
            if sum_t != 0:
                check=False
                error.append((i,t,sum_t))
            
    return  check, error 


# Constraint (c.4) Strategic Aggregator supply into grid offer
def strategic_offer_dual_rule(model,DABus, c_DA_o):
    check=True
    error =[]
    
    bus=DABus
    for t in model.T:
        sum_t = round(c_DA_o[t-16]- value(model.Lambda[bus,t]) - value(model.w_DAo_low[t]) + value(model.w_DAo_up[t]),2)
        if sum_t != 0:
            check=False
            error.append((t,sum_t))
            
    return check, error

# Constraint (C.5) Strategic aggregator demand bid from grid
def strategic_demand_dual_rule(model, c_DA_b, DABus):
    check=True
    error =[]
    
    bus=DABus
    for t in model.T:
        sum_t = round(-c_DA_b[t-16] + value(model.Lambda[bus,t]) - value(model.w_DAb_low[t])  + value( model.w_DAb_up[t]),2)
        if sum_t != 0:
            check=False
            error.append((t,sum_t))
            
    return check, error


# Constraint (C.6) Transmission Line constraint   
def transmission_line_dual_rule(model, Yline ,B):
    check=True
    error =[]
    
    for i in model.BUS:
        for t in model.T:
            B_T=B.transpose()
            # sum1= sum(B_T[i-1,j-1]*(model.Lambda[i,t]-model.Lambda[j,t]) for j in model.BUS if i != j)
            sum1= sum(B_T[i-1,j-1] * value(model.Lambda[j,t]) for j in model.BUS )
            
            Yline_T = Yline.transpose()
            sum2= sum(Yline_T[i-1,j-1] * value(model.w_line_low[j,t]) for j in model.LINES )
            
            sum3= sum(Yline_T[i-1, j-1] * value(model.w_line_up[j,t]) for j in model.LINES )
            
            sum_t = round(sum1 + sum2 + sum3,2)
            
            if sum_t != 0:
                check=False
                error.append((i,t,sum_t))
    
    return check, error

# KKT constraint (D.1)
def KKT_gen_low_rule(model, bigM):
    check=True
    error=[]
    
    for i in model.G:
        for t in model.T:
            if round(value(model.g[i,t]),3) > value(model.u_g_low[i,t]) * bigM:
                check=False
                error.append((i,t))
    return check, error


#KKT Constrainr (D.2)
def KKT_gen_low_2_rule(model, bigM):
    check=True
    error=[]
    
    for i in model.G:
        for t in model.T:
            if round(value(model.w_g_low[i,t]),3) > (1-value(model.u_g_low[i,t])) * bigM:
                check=False
                error.append((i,t))
                
    return check, error

#KKT Constraint (D.3)
def KKT_gen_up_rule (model, g_s, bigM):
    check=True
    error=[]
    
    for i in model.G:
        for t in model.T:
            if round(g_s[i][t-16] - value(model.g[i,t]),3) > value(model.u_g_up[i,t]) *bigM:
                check= False
                error.append((g_s[i][t-16], value(model.g[i,t]), value(model.u_g_up[i,t]), t ))
    return  check, error

# KKT Constraint (D.4)
def KKT_gen_up_2_rule (model, bigM):
    check=True
    error=[]
    
    for i in model.G:
        for t in model.T:
            if round(value(model.w_g_up[i,t]),3) > (1-value(model.u_g_up[i,t])) * bigM:
                check=False
                error.append((value(w_g_up[i,t]), value(model.u_g_up[i,t]), t))
            
    return check, error


# KKT Constraint (D.5)
def KKT_DAs_supply_offer_low_rule (model, bigM):
    check=True
    error=[]
    
    for i in model.NCDA:
        for t in model.T:
            if round(value(model.d_o[i,t]),3) > value(model.u_do_low[i,t]) * bigM:
                check=False
                error.append((i,t))
    return check, error


# KKT Constraint(D.6)
def KKT_DAs_supply_offer_low_2_rule(model, bigM):
    check=True
    error=[]
    for i in model.NCDA:
        for t in model.T:
            if round(value(model.w_do_low[i,t]),3) > (1-value(model.u_do_low[i,t])) * bigM :
                check=False
                error.append((i,t))
    return check, error


# KKT Constraint (D.7)
def KKT_DAs_supply_offer_up_rule (model, F_d_o, bigM):
    check=True
    error=[]
    for i in model.NCDA:
        for t in model.T:
            if round(F_d_o[i][t-16] -value(model.d_o[i,t]),3) > value(model.u_do_up[i,t]) * bigM :
                check=False
                error.append((i,t))
                
    return check, error

# KKT Constraint (D.8)
def KKT_DAs_supply_offer_up_2_rule(model, bigM):
    check=True
    error=[]
    for i in model.NCDA:
        for t in model.T:
            if round(value(model.w_do_up[i,t]),3) > (1- value(model.u_do_up[i,t])) * bigM :
                check=False
                error.append((i,t))
                
    return check, error

#KKT Constraint (D.9)
def KKT_DAs_demand_bid_low_rule(model, bigM):
    check=True
    error=[]
    for i in model.NCDA:
        for t in model.T:
            if round(value(model.d_b[i,t]),3) > (value(model.u_db_low[i,t])) * bigM :
                check=False
                error.append((i,t))
                
    return check, error

# KKT Constraint (D.10)
def KKT_DAs_demand_bid_low_2_rule (model, bigM):
    check=True
    error=[]
    for i in model.NCDA:
        for t in model.T:
            if round(value(model.w_db_low[i,t]),3) > (1- value(model.u_db_low[i,t])) * bigM :
                check=False
                error.append((i,t))
    return check, error


#KKT Constraint (D.11)
def KKT_DAs_demand_bid_up_rule (model, F_d_b , bigM):
    check=True
    error=[]
    for i in model.NCDA:
        for t in model.T:
            if round(F_d_b[i][t-16]- value(model.d_b[i,t]),3) > (value(model.u_db_up[i,t])) * bigM :
                check=False
                error.append((i,t))
                
    return check, error

# KKT Constraint (D.12)
def KKT_DAs_demand_bid_up_2_rule (model, bigM):
    check=True
    error=[]
    for i in model.NCDA:
        for t in model.T:
            if  round(value(model.w_db_up[i,t]),3) > (1-value(model.u_db_up[i,t])) * bigM :
                check=False
                error.append((i,t))
                
    return check, error

# KKT Constraint (D.13)
def KKT_strategic_DA_bid_low_rule (model, bigM):
    check=True
    error=[]
    for t in model.T:
        if round(value(model.E_DA_G[t]),3) > value(model.u_DAs_o_low[t]) * bigM:
            check=False
            error.append(t)
    return check, error


#KKT Constraint (D.14)
def KKT_strategic_DA_bid_low_2_rule (model, bigM):
    check=True
    error=[]
    for t in model.T:
        if round(value(model.w_DAo_low[t]),3) >(1- value(model.u_DAs_o_low[t])) * bigM:
            check=False
            error.append(t)
    return check, error

# KKT Constraint (D.15)
def KKT_stKrategic_DA_bid_up_rule (model,bigM):
    check=True
    error=[]
    
    for t in model.T:
        if round(value(model.DA_supply[t]) - value(model.E_DA_G[t]),3) > value(model.u_DAs_o_up[t]) * bigM:
            check = False
            error.append((value(model.DA_supply[t]),value(model.E_DA_G[t]),value(model.u_DAs_o_up[t]), t ))
    
    return check , error


# KKT Constraint (D.16)
def KKT_strategic_DA_bid_up_2_rule (model,bigM):
    check=True
    error=[]
    
    for t in model.T:
        if round(value(model.w_DAo_up[t]),3)  > (1-value(model.u_DAs_o_up[t])) * bigM:
            check = False
            error.append(t)
            
    return check, error


# KKT Constraint (D.17)
def KKT_strategic_demand_low_rule (model, bigM):
    check=True
    error=[]
    
    for t in model.T:
        if round(value(model.E_DA_L[t]),3)  > (value(model.u_DAs_b_low[t])) * bigM:
            check = False
            error.append(t)
    return check, error

# KKT Constraint (D.18)
def KKT_strategic_demand_low_2_rule (model, bigM):
    check=True
    error=[]
    
    for t in model.T:
        if value(model.w_DAb_low[t])  > (1-value(model.u_DAs_b_low[t])) * bigM:
            check = False
            error.append(t)
    return check, error

# KKT Constraint (D.19)
def KKT_strategic_demand_up_rule (model, bigM):
    check=True
    error=[]
    
    for t in model.T:
        if round(value(model.DA_demand[t]) - value(model.E_DA_L[t]),3) > value(model.u_DAs_b_up[t]) * bigM:
            check=False
            error.append((value(model.DA_demand[t]), value(model.E_DA_L[t]), value(model.u_DAs_b_up[t]), t ))
            
    return check, error

# KKT Constraint (D.20)
def KKT_strategiv_demand_up_2_rule (model,bigM):
    check=True
    error=[]
    
    for t in model.T:
        if value(model.w_DAb_up[t])  > (1-value(model.u_DAs_b_up[t])) * bigM:
            check = False
            error.append(t)
            
    return check, error


# KKT Transmission line Constraint (D.21)
def KKT_transmission_low_rule (model, Yline, FMAX, bigM):
    check=True
    error=[]
    for i in model.LINES:
        for t in model.T:
            if sum(Yline[i-1, j-1] * value(model.teta[j,t]) for j in model.BUS ) + FMAX[i-1] >   value(model.u_line_low[i,t]) * bigM :
                check= False
                error.append((i,t))
    #Yline[i-1, j-1]
    return check, error


# KKT Transmission line Constraint (D.22)
def KKT_transmission_low_2_rule (model, bigM):
    check=True
    error=[]
    for i in model.LINES:
        for t in model.T:
            if value(model.w_line_low[i,t])  >   (1-value(model.u_line_low[i,t])) * bigM :
                check= False
                error.append((i,t))
    return check, error


# KKT Transmission line Constraint (D.23)
def KKT_transmission_up_rule(model, Yline, FMAX, bigM):
    check=True
    error=[]
    for i in model.LINES:
        for t in model.T:
            if sum(-Yline[i-1,j-1] * value(model.teta[j,t]) for j in model.BUS) + FMAX[i-1] > value(model.u_line_up[i,t]) * bigM :
                check= False
                error.append((i,t))
    return check, error


# KKT Transmission line Constraint (D.24)
def KKT_transmission_up_2_rule(model, bigM):
    check=True
    error=[]
    for i in model.LINES:
        for t in model.T:
            if value(model.w_line_up[i,t]) > (1-value(model.u_line_up[i,t])) * bigM :
                check= False
                error.append((i,t))
                
    return check, error



def check_constraints(model, Yline, B,dic_G, dic_Bus_CDA, DABus, c_g, dic_G_Bus, dic_CDA_Bus, c_d_o, c_d_b, c_DA_o, c_DA_b, bigM, bigF, g_s, F_d_o, F_d_b, FMAX ):
    
    
    timestr = time.strftime("%Y%m%d-%H%M%S")
    
    f_name="Model_Check_Con"+timestr+".txt"
    f= open(f_name,"w")
    
    check, error = network_power_balance_rule(model, B, dic_G, dic_Bus_CDA, DABus)
    f.write("Constraint b.2: power balance at each bus\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("(bus:%d,time:%d,value:%f)"%(e[0],e[1],e[2]))
        f.write(", ")
    
    check, error = generator_dual_price_rule(model, c_g, dic_G_Bus)
    f.write("\n\nConstraint C.1:generators dual price\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("(Gen:%d,time:%d,value:%f)"%(e[0],e[1],e[2]))
        f.write(", ")
    
    check, error = competitor_offer_dual_rule(model, dic_CDA_Bus, c_d_o)
    f.write("\n\nConstraint C.2:competitor suuply to grid offer\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("(CDA:%d,time:%d,value:%f)"%(e[0],e[1],e[2]))
        f.write(", ")
        
    check, error = competitor_demand_dual_rule(model, c_d_b, dic_CDA_Bus)
    f.write("\n\nConstraint C.3:competitors demand bid\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("(CDA:%d,time:%d,value:%f)"%(e[0],e[1],e[2]))
        f.write(", ")
    
    check, error = strategic_offer_dual_rule(model,DABus, c_DA_o)
    f.write("\n\nConstraint C.4:Strategic Aggregator supply into grid offer\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("(time:%d,value:%f)"%(e[0],e[1]))
        f.write(", ")
    
    check, error = strategic_demand_dual_rule(model, c_DA_b, DABus)
    f.write("\nConstraint C.5:Strategic aggregator demand bid from grid\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("(time:%d,value:%f)"%(e[0],e[1]))
        f.write(", ")
    
    check, error = transmission_line_dual_rule(model, Yline ,B)
    f.write("\n\nConstraint C.6:Transmission Line constraint\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("(CDA:%d,time:%d,value:%f)"%(e[0],e[1],e[2]))
        f.write(", ")
    
    check, error = KKT_gen_low_rule(model, bigM)
    f.write("\n\nConstraint D.1:KKT Generator\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("(Gen:%d,Time:%f)"%(e[0],e[1]))
        f.write(", ")
    
    check, error = KKT_gen_low_2_rule(model, bigM)
    f.write("\n\nConstraint D.2:KKT Generator\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("(Gen:%d,Time:%f)"%(e[0],e[1]))
        f.write(", ")
    
    check, error = KKT_strategic_demand_up_rule (model, bigM)
    f.write("\n\nConstraint D.3:KKT_strategic_demand_up_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("DA_demand:%0.2f -E_DA_L[t]:%0.2f > u_DAs_b_up:%0.2f * %0.2f at time:%d)"%(e[0],e[1],e[2],bigM,e[3]))
        f.write(", ")
    
    check, error = KKT_gen_up_2_rule (model, bigM)
    f.write("\n\nConstraint D.4:KKT_gen_up_2_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("DA_demand:%0.2f -E_DA_L:%0.2f > u_DAs_b_up:%0.2F * %0.2f at time:%d)"%(e[0],e[1],e[2],bigM,e[3]))
        f.write(", ")
    
    check, error = KKT_DAs_supply_offer_low_rule (model, bigM)    
    f.write("\n\nConstraint D.5:KKT_DAs_supply_offer_low_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("CDA:%d, time:%d"%(e[0],e[1]))
        f.write(", ")
    
    check, error = KKT_DAs_supply_offer_low_2_rule(model, bigM)
    f.write("\n\nConstraint D.6:KKT_DAs_supply_offer_low_2_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("CDA:%d, time:%d"%(e[0],e[1]))
        f.write(", ")
    
    check, error = KKT_DAs_supply_offer_up_rule (model, F_d_o, bigM)
    f.write("\n\nConstraint D.7:KKT_DAs_supply_offer_up_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("CDA:%d, time:%d"%(e[0],e[1]))
        f.write(", ")
    
    check, error = KKT_DAs_supply_offer_up_2_rule(model, bigM)
    f.write("\n\nConstraint D.8:KKT_DAs_supply_offer_up_2_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("CDA:%d, time:%d"%(e[0],e[1]))
        f.write(", ")
  
    check, error = KKT_DAs_demand_bid_low_rule(model, bigM)
    f.write("\n\nConstraint D.9:KKT_DAs_demand_bid_low_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("CDA:%d, time:%d"%(e[0],e[1]))
        f.write(", ")
    
    check, error = KKT_DAs_demand_bid_low_2_rule (model, bigM)
    f.write("\n\nConstraint D.10:KKT_DAs_demand_bid_low_2_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("CDA:%d, time:%d"%(e[0],e[1]))
        f.write(", ")
    
    check, error = KKT_DAs_demand_bid_up_rule (model, F_d_b , bigM)
    f.write("\n\nConstraint D.11: KKT_DAs_demand_bid_up_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("CDA:%d, time:%d"%(e[0],e[1]))
        f.write(", ")
    
    check, error = KKT_DAs_demand_bid_up_2_rule (model, bigM)
    f.write("\n\nConstraint D.12: KKT_DAs_demand_bid_up_2_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("CDA:%d, time:%d"%(e[0],e[1]))
        f.write(", ")
    
    check, error = KKT_strategic_DA_bid_low_rule (model, bigM)
    f.write("\n\nConstraint D.13: KKT_strategic_DA_bid_low_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("time:%d"%(e))
        f.write(", ")
    
    check, error = KKT_strategic_DA_bid_low_2_rule (model, bigM)
    f.write("\n\nConstraint D.14: KKT_strategic_DA_bid_low_2_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("time:%d"%(e))
        f.write(", ")
    
       
    check, error = KKT_stKrategic_DA_bid_up_rule (model,bigM)
    f.write("\n\nConstraint D.15:KKT_stKrategic_DA_bid_up_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("(DA_supply:%0.2f - E_DA_G:%0.2f > u_DAs_o_up:%d * %0.2f at Time:%d)"%(e[0],e[1],e[2],bigM,e[3]))
        f.write(", ")
    
    
    check, error = KKT_strategic_DA_bid_up_2_rule (model,bigM)
    f.write("\n\nConstraint D.16: KKT_strategic_DA_bid_up_2_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("time:%d"%(e))
        f.write(", ")
    
    
    check, error = KKT_strategic_demand_low_rule (model, bigM)
    f.write("\n\nConstraint D.17: KKT_strategic_demand_low_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("time:%d"%(e))
        f.write(", ")
    
    check, error = KKT_strategic_demand_low_2_rule (model, bigM)
    f.write("\n\nConstraint D.18: KKT_strategic_demand_low_2_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("time:%d"%(e))
        f.write(", ") 
    
    check, error = KKT_strategic_demand_up_rule (model, bigM)
    f.write("\n\nConstraint D.19:KKT_strategic_demand_up_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("(DA_demand:%0.2f - E_DA_L:%0.2f > u_DAs_b_up%d * %0.2f at Time:%d)"%(e[0],e[1],e[2],bigM,e[3]))
        f.write(", ")
   
    check, error = KKT_strategiv_demand_up_2_rule (model,bigM)
    f.write("\n\nConstraint D.20:KKT_strategiv_demand_up_2_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("Time:%d)"%(e))
        f.write(", ")


    check, error = KKT_transmission_low_rule (model, Yline, FMAX, bigM)
    f.write("\n\nConstraint D.21:KKT_transmission_low_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("Line:%d ,Time:%d)"%(e[0], e[1]))
        f.write(", ")

    check, error = KKT_transmission_low_2_rule (model, bigM)
    f.write("\n\nConstraint D.22:KKT_transmission_low_2_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("Line:%d ,Time:%d)"%(e[0], e[1]))
        f.write(", ")
    
    check, error = KKT_transmission_up_rule(model, Yline, FMAX, bigM)
    f.write("\n\nConstraint D.23:KKT_transmission_up_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("Line:%d ,Time:%d)"%(e[0], e[1]))
        f.write(", ")

    check, error = KKT_transmission_up_2_rule(model, bigM)
    f.write("\n\nConstraint D.24:KKT_transmission_up_2_rule\n")
    f.write("\tcheck=%d\n"%(check))
    f.write("\terror=")
    for e in error:
        f.write("Line:%d ,Time:%d)"%(e[0], e[1]))
        f.write(", ")    

    
    f.close()
