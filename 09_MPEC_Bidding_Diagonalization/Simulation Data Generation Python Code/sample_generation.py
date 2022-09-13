# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 12:23:59 2020

@author: alire
"""

import numpy as np
import scipy.stats
import matplotlib.pyplot as plt

def my_distribution(min_val, max_val, mean, std):
    scale = max_val - min_val
    location = min_val
    # Mean and standard deviation of the unscaled beta distribution
    unscaled_mean = (mean - min_val) / scale
    unscaled_var = (std / scale) ** 2
    # Computation of alpha and beta can be derived from mean and variance formulas
    t = unscaled_mean / (1 - unscaled_mean)
    beta = ((t / unscaled_var) - (t * t) - (2 * t) - 1) / ((t * t * t) + (3 * t * t) + (3 * t) + 1)
    alpha = beta * t
    # Not all parameters may produce a valid distribution
    if alpha <= 0 or beta <= 0:
        raise ValueError('Cannot create distribution for the given parameters.')
    # Make scaled beta distribution with computed parameters
    return scipy.stats.beta(alpha, beta, scale=scale, loc=location)



def main():
    
    np.random.seed(100)
    min_val = 1.5
    max_val = 35
    mean = 9.87
    std = 3.1
    my_dist = my_distribution(min_val, max_val, mean, std)
    # Plot distribution PDF
    x = np.linspace(min_val, max_val, 100)
    plt.plot(x, my_dist.pdf(x))
    # Stats
    print('mean:', my_dist.mean(), 'std:', my_dist.std())
    # Get a large sample to check bounds
    sample = my_dist.rvs(size=100000)
    print('min:', sample.min(), 'max:', sample.max())
    

if __name__ == "__main__":
    main()