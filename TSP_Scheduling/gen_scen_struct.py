# -*- coding: utf-8 -*-
"""
Created on Fri Dec  4 12:07:22 2020

@author: alire
"""

def scenario_structure(no_scenario):
    
    f= open("ScenarioStructure.dat","w")
    
    
    f.write("set Stages := FirstStage SecondStage ; \n\n " )
    
    f.write("set Nodes := RootNode\n" )
    for i in range(no_scenario):
        f.write("\t     Scenario%dNode\n"%(i+1))
    
    
    
    

def main():
    scenario_structure(10)
    
if __name__ == "__main__":
    main()