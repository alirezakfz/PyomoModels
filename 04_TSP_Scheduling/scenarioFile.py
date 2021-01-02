# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 12:34:10 2020

@author: Ali
"""

# generate random integer values


def scenario_File(ev_no, charge_no, installed_cost, time_slot, arrival, depart, TFC):
    
    
    f= open("data.dat","w")
    
    f.write("set N := " )
    for i in range(ev_no):
        f.write(" %d"%(i+1))
    f.write(" ;\n\n")
    
    
    f.write("set M := " )
    for i in range(charge_no):
        f.write(" %d"%(i+1))
    f.write(" ;\n\n")

    #f.write("param T :=  %d" %(t_no) )
    f.write("set T := " )
    for i in range(time_slot+1):
        f.write(" %d"%(i))
    f.write(" ;\n\n")
    
        
    f.write("param arrival := \n"  )
    for i in range(ev_no):
        f.write("    %d %d\n"%(i+1,arrival[i]))
    f.write(" ;\n\n")
    
    f.write("param depart := \n")
    for i in range(ev_no):
        f.write("    %d %d\n"%(i+1,depart[i]))
    f.write(" ;\n\n")
    
    f.write("param TFC := \n")
    for j in range(charge_no):
        for i in range(ev_no):
            f.write("    %d %d %d\n"%(i+1,j+1,TFC[i][j]))
    f.write(" ;\n\n")
    
    # f.write("param TFC := \n")
    # for i in range(ev_no):
    #     for j in range(charge_no):
    #         f.write("    %d %d %d\n"%(j+1,i+1,TFC[i][j]))
    # f.write(" ;\n\n")
    
    f.write("param installed_cost := \n" )
    for i in range(charge_no):
        f.write("    %d %d\n"%(i+1,installed_cost[i]))
    f.write(" ;\n\n")
    
    f.write("param number_of_timeslot := %d ;\n"%(time_slot)  )
    
    f.close()
    

def write_scenario(ev_no, charge_no, installed_cost, time_slot, arrival, depart, TFC, f_name):
    
    f= open(f_name,"w")
    
    f.write("set N := " )
    for i in range(ev_no):
        f.write(" %d"%(i+1))
    f.write(" ;\n\n")
    
    
    f.write("set M := " )
    for i in range(charge_no):
        f.write(" %d"%(i+1))
    f.write(" ;\n\n")

    #f.write("param T :=  %d" %(t_no) )
    f.write("set T := " )
    for i in range(time_slot+1):
        f.write(" %d"%(i))
    f.write(" ;\n\n")
    
        
    f.write("param arrival := \n"  )
    for i in range(ev_no):
        f.write("    %d %d\n"%(i+1,arrival[i]))
    f.write(" ;\n\n")
    
    f.write("param depart := \n")
    for i in range(ev_no):
        f.write("    %d %d\n"%(i+1,depart[i]))
    f.write(" ;\n\n")
    
    f.write("param TFC := \n")
    for j in range(charge_no):
        for i in range(ev_no):
            f.write("    %d %d %d\n"%(i+1,j+1,TFC[i][j]))
    f.write(" ;\n\n")
    
    # f.write("param TFC := \n")
    # for i in range(ev_no):
    #     for j in range(charge_no):
    #         f.write("    %d %d %d\n"%(j+1,i+1,TFC[i][j]))
    # f.write(" ;\n\n")
    
    f.write("param installed_cost := \n" )
    for i in range(charge_no):
        f.write("    %d %d\n"%(i+1,installed_cost[i]))
    f.write(" ;\n\n")
    
    f.write("param number_of_timeslot := %d ;\n"%(time_slot)  )
    
    f.close()
    
        

   
    

