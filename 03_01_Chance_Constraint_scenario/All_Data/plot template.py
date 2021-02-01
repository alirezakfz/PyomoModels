# -*- coding: utf-8 -*-
"""
Created on Sun Jan 31 08:16:04 2021

@author: geots
"""

import numpy as np
import matplotlib.pyplot as plt


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