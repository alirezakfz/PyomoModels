# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import numpy as np

file="prosumers_data/inflexible_profiles_scen_"

df_all = pd.concat([pd.read_csv(file+str(1)+".csv"), pd.read_csv(file+str(2)+".csv"), pd.read_csv(file+str(3)+".csv"), pd.read_csv(file+str(4)+".csv")])

# number_of_chunks = 1000

# for idx, chunk in enumerate(np.array_split(df_all, number_of_chunks)):
#     chunk.to_csv(f'/New_prosumers_data/inflexible_profiles_scen_{idx}.csv')
    

# no of csv files with row size
k = 20
size = 1000

for i in range(k):
    df = df_all[size*i:size*(i+1)]
    df.to_csv(f'New_prosumers_data/inflexible_profiles_scen_{i+1}.csv', index=False)







file="prosumers_data/prosumers_profiles_scen_"

df_all = pd.concat([pd.read_csv(file+str(1)+".csv"), pd.read_csv(file+str(2)+".csv"), pd.read_csv(file+str(3)+".csv"), pd.read_csv(file+str(4)+".csv")])

# no of csv files with row size
k = 20
size = 1000

for i in range(k):
    df = df_all[size*i:size*(i+1)]
    df.to_csv(f'New_prosumers_data/prosumers_profiles_scen_{i+1}.csv', index=False)