# -*- coding: utf-8 -*-
"""
Created on Sun Jan 16 18:38:17 2022

@author: alire
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image





def remove_transparency(im, bg_colour=(255, 255, 255)):

    # Only process if image has transparency (http://stackoverflow.com/a/1963146)
    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):

        # Need to convert to RGBA if LA format due to a bug in PIL (http://stackoverflow.com/a/1963146)
        alpha = im.convert('RGBA').split()[-1]

        # Create a new background image of our matt color.
        # Must be RGBA because paste requires both images have the same format
        # (http://stackoverflow.com/a/8720632  and  http://stackoverflow.com/a/9459208)
        bg = Image.new("RGBA", im.size, bg_colour + (255,))
        bg.paste(im, mask=alpha)
        return bg

    else:
        return im
    
 



"""
One Example
"""

image_png = 'C:/Users/alire/Pictures/SEST_2022_Photos/Power_Network.png'
fig = Image.open(image_png)
if fig.mode in ('RGBA', 'LA'):
    fig = remove_transparency(fig)
    fig = fig.convert('RGB')
    
fig.save('C:/Users/alire/Pictures/SEST_2022_Photos/Power_Network.eps', lossless = True)

"""
Second Example
"""

img = mpimg.imread('C:/Users/alire/Pictures/SEST_2022_Photos/Power_Network.png')



#print(img)
ax=plt.gca()

#ax.axes.xaxis.set_visible(False)
ax.axes.yaxis.set_visible(False)

plt.tick_params(
    axis='x',          # changes apply to the x-axis
    which='both',      # both major and minor ticks are affected
    bottom=False,      # ticks along the bottom edge are off
    top=False,        # ticks along the top edge are off
    labelbottom=False) # labels along the bottom edge are off

ax.set_rasterized(True)

plt.xlabel("Power Network Schematic")
imgplot = plt.imshow(img)

plt.savefig('C:/Users/alire/Pictures/SEST_2022_Photos/Power_Network5.eps', bbox_inches='tight', dpi=100, lossless = True)