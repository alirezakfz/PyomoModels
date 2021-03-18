# -*- coding: utf-8 -*-
"""
Created on Wed Mar 17 20:30:53 2021

@author: alire
"""
import random
from pyomo.environ import *
from pyomo.opt import SolverFactory


#Setting the random seed
random.seed(10)

def random_generation(n,min_g, max_g):
    temp=[]
    for i in range(0,n):
        temp.append(random.randint(min_g,max_g))
    return temp

def random_price(n):
    temp=[]
    for i in range(0,n):
        temp.append(random.randint(10,50))
    return temp

"""
Sets included in the power system model
"""
time=24

# Time Horizon
H = range(1,time+1)            

#Set of competing DAs participating in the day ahead energy market
DA = ['DA1','DA2','DA3']  

# Set of transmission network busses
N  = ['bus1','bus2','bus3','bus4','bus5','bus6']    

# Set of generators participating in the day ahead energy market
G  = {'bus1':['G1'],
      'bus2':['G2'], 
      'bus6':['G3','G4']}                           


#Set of transmission network lines
#L  = {1:[2,4], 2:[1,3,4], 3:[2,6], 4:[1,2,5], 5:[4,6], 6:[3,5]} 
L=[(1,2),(1,4),(2,3),(2,4),(3,6),(4,5),(5,6)]

"""
Defining Parameters
"""
bigM =100
bigF = 100

#Price bid of generator i in time t
c_g = { 'G1':random_price(time),
        'G2':random_price(time),
        'G3':random_price(time),
        'G4':random_price(time)}  

#Price bid for supplying power of competing DA  i in time t
c_o = {'DA1':random_price(time),
       'DA2':random_price(time),
       'DA3':random_price(time)}

# Price bid for buying power of competing DA  i in time t
c_b = {'DA1':random_price(time),
       'DA2':random_price(time),
       'DA3':random_price(time)}

# Price bid for supplying power of strategic DA in time t
c_DA_o = random_price(time)

# Price bid for buying power of strategic DA in time t
c_DA_b = random_price(time)

# Admittance of transmission line ij (connecting bus  i to bus j)
y = {(1,2):5.882352941,
     (1,4):3.875968992,
     (2.3):27.02702703,
     (2,4):5.076142132,
     (3.6):55.55555556,
     (4.5):27.027002703,
     (5.6):7.142857143,}

# Supply offer of generator i in time t
g_s = { 'G1':random_generation(time,1, 100),
        'G2':random_generation(time,1, 75),
        'G3':random_generation(time,1, 50),
        'G4':random_generation(time,1, 50)}

# Supply offer of competing DA i in time t
def random_offer(DA_list, time):
    pivot=0.25
    offer_dict=dict()
    bid_dict=dict()
    for competitor in DA_list:
        temp_offer=[]
        temp_bid=[]
        for t in range(0,time):
            if random.random() >= pivot:
                temp_offer.append(0)
                temp_bid.append(random.randint(5, 100))
            else:
                temp_bid.append(0)
                temp_offer.append(random.randint(5, 100))
        offer_dict(competitor)=temp_offer
        bid_dict(competotor)=temp_bid
    
    return offer_dict, bid_dict

# Supply offer of competing DA i in time t
# Demand bid of competing DA i in time t
d_o , d_b = random_offer(DA, time)

# Capacity limit of transmission line ij (connecting bus  i to bus j)
T = {(1,2):150, (1,4):150, (2,3):150, (2,4):33, (3,6):150, (4,5):150, (5,6):150}
