# -*- coding: utf-8 -*-
"""
Created on Fri Sep  4 19:02:03 2020

@author: Ali
"""

import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

file_name='EVs_Info_No_Delay20200904-135744.csv'

data=pd.read_csv(file_name)

plt.hist(data["Arrival"],100)
plt.show()

arrive=data[["Arrival"]]
count=Counter(arrive)
counter=list(count.items())
counter.sort()

plt.plot([x[0] for x in counter], [y[1] for y in counter])  
plt.hist(arrive,10)


plt.xticks(range(0,24))
plt.xlabel("Time Horizon")
years=list(map(str,range(1980,2014)))

data.describe()

small= [x for x in range(len(data["Demand"])) if data["Demand"][x]<=0]


######################################################
data=pd.read_csv(file_name)

data.head

senario=data["senario"].tolist()

data.columns.tolist()

sc=data[(data['senario'] >= 1) & (data['senario'] <=200)]

