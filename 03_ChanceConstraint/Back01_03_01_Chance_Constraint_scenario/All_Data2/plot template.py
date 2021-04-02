# -*- coding: utf-8 -*-
"""
Created on Sun Jan 31 08:16:04 2021

@author: geots
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns



"""
Figure 1: Percentage of installed chargers of each charger type
"""
data=pd.read_csv('Summary/installed_chargers_info.csv')
data.plot

x_axis=np.arange(10,65,5) #number of evs

y_axis_1=data.loc[data['Levels']=='Level 1', 'Count']
y_axis_1=y_axis_1.to_numpy()   #Level 1 chargers

y_axis_2= data.loc[data['Levels']=='Level 2', 'Count']
y_axis_2=y_axis_2.to_numpy()

y_axis_3=data.loc[data['Levels']=='Level 3', 'Count']
y_axis_3=y_axis_3.to_numpy()

fig = plt.figure()
ax = fig.add_axes([0,0,1,1])
# ax.bar(X + 0.00, data[0], color = 'b', width = 0.25)
ax.bar(x_axis + 0.00, y_axis_1, width = 0.25)
ax.bar(x_axis + 0.25, y_axis_2, width = 0.25)
ax.bar(x_axis + 0.50, y_axis_3, width = 0.25)
ax.set_ylabel('Percentage of intalled chargers')
ax.set_title('Scores by group and gender')
ax.set_xticks(x_axis)
ax.set_yticks(np.arange(0,1,0.1))
ax.legend(labels=['Level 1', 'Level 2', 'Level 3'])
plt.show()




x_axis = np.array([...])

y_axis_1 = np.array([...])
y_axis_2 = np.array([...])
y_axis_3 = np.array([...])
y_axis_4 = np.array([...])

plt.plot( x_axis, y_axis_1, '.--',label= '...')
plt.plot( x_axis, y_axis_2, '.--',label= '...')
plt.plot( x_axis, y_axis_3, '.--',label= '...')
plt.plot( x_axis, y_axis_4, '.--',label= '...')


plt.legend(loc = 'upper left')
plt.xlabel('Number of DR requests')
plt.ylabel('...')

plt.savefig('[your_path].eps', format='eps')
# in [your_path] you may have to use "/" instead of "\"

plt.show()