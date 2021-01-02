# -*- coding: utf-8 -*-
"""
Created on Fri Dec  4 12:07:22 2020

@author: alire
"""

def scenario_structure(no_scenario):
    
    f= open("scenariodata\\ScenarioStructure.dat","w")
    
    
    f.write("set Stages := FirstStage SecondStage ; \n\n " )
    
    f.write("set Nodes := RootNode\n" )
    for i in range(no_scenario):
        f.write("\t      Scenario%dNode\n"%(i+1))
    f.write(";\n\n")
    
    f.write("param NodeStage := RootNode             FirstStage\n" )
    for i in range(no_scenario):
        f.write("\t\t   Scenario%dNode\tSecondStage\n"%(i+1))
    f.write(";\n\n")
    
    f.write("set Children[RootNode] :=\n" )
    for i in range(no_scenario):
        f.write("\t\t   Scenario%dNode\n"%(i+1))
    f.write(";\n\n")
    
    
    pr=1/no_scenario
    pr=round(pr, 3)
    f.write("param ConditionalProbability :=\n\t\t   RootNode\t\t    1.0\n" )
    for i in range(no_scenario):
        f.write("\t\t   Scenario%dNode\t    %.3f\n"%(i+1,pr))
    f.write(";\n\n")
    
    
    f.write("set Scenarios :=\n" )
    for i in range(no_scenario):
        f.write("\t\t   Scenario%d\n"%(i+1))
    f.write(";\n\n")
    
    f.write("param ScenarioLeafNode :=\n" )
    for i in range(no_scenario):
        f.write("\t\t   Scenario%d\tScenario%dNode\n"%(i+1,i+1))
    f.write(";\n\n")
    
    f.write("set StageVariables[FirstStage] := q[*] ;\n\n" )
    f.write("set StageVariables[SecondStage] := z[*];\n\n" )
    f.write("param StageCostVariable :=\n\t\t   FirstStage    FirstStageCost\n" )
    f.write("\t\t   SecondStage   SecondStageCost ;\n\n")
    f.write("#param ScenarioBasedData := False ;")
    
    f.close()
    
    

def main():
    scenario_structure(10)
    
if __name__ == "__main__":
    main()