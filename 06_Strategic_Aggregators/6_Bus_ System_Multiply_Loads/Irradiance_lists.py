# -*- coding: utf-8 -*-
"""
Created on Fri Oct 29 13:05:10 2021

@author: Alireza
"""

import numpy as np

# June Irradiance
ir_list = [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,3,2,2,2,3,3,3,2,2,3,2,3,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,1,1,1,1,2,1,2,2,2,2,2,2,2,2,3,2,2,2,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,2,2,2,3,2,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,4,4,4,4,3,4,4,4,4,4,5,5,6,6,7,8,7,7,8,9,8,8,8,8,9,9,9,9,10,10,10,11,12,12,12,13,13,14,14,14,15,15,15,15,15,15,16,15,16,16,17,18,18,19,20,20,21,21,21,21,22,21,21,21,21,22,23,23,23,24,25,25,26,27,29,31,32,34,35,37,38,40,42,43,45,47,49,52,53,55,57,59,60,61,62,63,64,65,66,68,70,73,76,79,82,87,92,96,100,105,108,110,112,113,114,116,116,116,115,114,113,112,111,110,109,109,108,109,109,109,108,109,108,107,106,104,101,99,95,92,89,86,83,80,76,74,71,69,67,65,63,62,60,59,59,57,57,56,56,55,54,53,51,51,51,50,49,49,49,48,49,49,50,50,51,52,54,55,55,56,57,58,58,58,58,58,59,59,59,59,59,60,60,61,61,61,63,64,66,67,69,71,72,73,74,75,75,76,76,77,78,78,79,80,81,82,83,84,86,87,89,90,91,91,92,92,92,93,94,94,96,96,97,98,98,98,97,96,95,93,92,91,91,90,89,89,89,90,90,90,91,92,92,92,92,93,93,94,95,97,99,101,103,106,107,108,109,108,108,106,106,105,105,104,103,102,101,101,101,103,106,109,113,116,118,120,122,124,126,127,129,132,135,138,142,146,149,152,154,156,157,158,157,157,156,154,152,151,149,146,144,143,142,141,141,140,140,140,141,142,142,144,146,147,149,151,152,153,154,154,154,154,155,155,155,155,156,157,160,163,166,168,168,168,167,164,162,159,156,154,152,151,149,149,150,150,151,152,153,154,155,155,157,157,156,154,153,151,149,149,149,148,146,145,144,142,140,138,136,133,130,126,124,122,121,118,115,114,112,111,110,109,109,110,110,110,112,112,111,110,110,110,111,112,110,106,102,99,97,100,105,110,115,122,128,134,137,137,135,134,133,138,144,151,154,157,158,158,157,156,156,154,149,144,140,136,133,130,128,129,131,131,131,129,126,123,120,116,114,113,111,109,109,109,109,111,114,120,123,124,122,121,123,125,126,127,128,129,129,132,132,129,125,120,115,110,107,104,101,98,96,95,94,94,96,97,102,107,109,110,108,107,106,105,104,104,103,102,103,103,104,105,106,105,104,105,107,107,105,102,101,99,98,98,97,98,100,101,101,100,98,96,94,93,92,91,90,89,89,89,89,91,93,95,101,108,114,119,125,134,147,154,159,159,156,152,147,143,139,133,129,128,131,132,135,149,166,189,215,251,276,304,345,371,390,392,405,416,427,448,461,461,463,465,490,496,508,509,511,513,517,517,515,510,511,522,528,534,537,540,538,550,554,570,571,569,567,563,575,586,599,664,715,749,768,782,796,811,763,752,767,778,726,682,647,647,676,699,720,737,750,719,704,725,731,747,711,685,670,695,717,722,734,754,771,775,787,800,814,794,812,798,766,726,751,772,763,783,804,769,726,695,728,749,765,773,780,789,797,747,755,774,732,752,706,671,641,609,578,549,521,493,466,444,429,472,467,521,544,583,615,581,612,625,589,553,581,605,625,641,655,667,676,685,694,703,709,716,716,722,726,729,732,734,736,735,734,733,732,732,731,731,732,736,740,734,683,692,688,638,592,551,517,505,481,463,444,423,403,384,367,358,350,343,336,355,397,403,401,380,377,390,422,448,468,437,406,382,360,387,414,436,456,473,450,425,398,373,401,426,399,422,396,396,417,436,453,437,449,463,475,486,454,423,395,368,345,325,309,307,334,366,373,354,333,314,295,278,262,249,240,233,228,227,231,253,252,248,244,240,235,232,233,245,283,284,285,315,325,331,350,338,356,358,373,384,392,399,389,369,361,345,325,308,296,283,272,263,255,249,244,240,235,232,230,228,228,227,224,219,215,212,208,205,201,194,187,178,169,161,154,149,156,173,191,206,216,228,239,248,256,265,262,268,275,282,286,287,270,253,239,227,218,207,199,190,181,173,167,161,155,151,148,146,145,144,144,141,139,136,134,132,130,128,125,123,120,116,113,111,117,117,114,110,107,103,98,95,92,89,88,87,85,85,84,83,82,79,77,74,72,68,65,62,59,56,55,53,52,53,55,56,58,59,60,60,59,59,57,56,55,53,53,53,52,52,53,54,58,59,60,62,62,62,61,60,60,60,60,60,60,60,59,58,57,56,55,54,52,51,50,48,47,46,44,42,40,40,39,38,37,36,35,34,33,33,32,30,29,28,27,27,26,25,24,23,23,22,22,21,21,20,19,18,17,16,15,15,14,12,11,11,11,10,10,9,8,8,8,7,7,7,6,6,6,6,5,5,5,5,5,5,5,4,4,4,4,4,4,4,4,4,4,4,4,4,4,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,2,3,3,3,3,3,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,3,3,3,3,3,2,3,3,2,2,2,2,2,2,2,2,2,3,3,3,3,3,3,2,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3]

ir_24=[]

step=60

counter=0

while(counter < len(ir_list) ):
    ir_24.append(sum(ir_list[counter:counter+step]))
    
    counter+=step
    
print(len(ir_24))


# April Irradiance
ir_list=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,3,3,3,4,4,5,5,5,5,6,6,6,6,6,6,6,6,6,6,7,7,7,8,9,10,11,12,12,12,12,13,13,14,14,15,15,15,15,15,15,14,14,14,13,13,13,13,13,13,12,12,12,12,12,12,12,12,13,13,13,13,13,13,13,14,15,16,16,17,17,18,19,20,21,21,22,23,25,28,33,38,42,46,49,51,55,59,60,61,62,63,64,64,64,63,64,65,66,68,68,66,64,63,62,61,60,59,58,57,56,54,53,52,50,48,47,46,45,45,45,45,45,44,43,42,42,42,42,42,42,42,42,42,43,43,43,43,43,45,48,51,53,55,57,59,60,63,64,65,66,66,66,66,67,69,72,74,75,76,77,77,77,77,77,77,77,79,82,85,89,93,96,99,101,104,106,108,109,110,109,108,107,104,103,101,100,99,100,102,105,109,114,120,126,130,133,133,133,133,132,132,130,128,125,123,121,118,114,110,105,101,99,97,96,96,96,96,97,98,100,104,110,114,118,122,127,132,138,144,150,156,163,170,175,179,183,188,193,198,202,203,202,200,199,197,196,195,194,193,193,195,197,198,196,192,186,180,174,170,166,163,159,156,154,152,151,150,149,146,141,135,128,122,117,112,109,108,107,107,108,108,108,108,106,104,101,99,96,94,92,90,88,88,87,88,89,93,97,101,105,109,113,116,118,120,121,121,121,120,118,117,115,113,111,110,108,108,109,110,113,116,118,120,119,118,117,115,113,112,110,107,103,99,96,92,89,86,84,82,81,81,82,84,86,88,89,88,87,86,86,86,87,88,88,88,88,89,90,91,93,95,98,102,108,114,121,126,129,131,131,130,127,124,120,116,113,110,109,109,110,112,114,117,120,122,125,128,131,136,140,144,147,147,146,144,141,138,135,132,130,128,127,127,126,125,122,119,116,112,108,104,101,98,96,95,95,96,97,98,101,104,107,109,110,111,111,111,111,111,112,112,111,110,109,108,108,109,111,113,117,123,127,128,128,127,126,125,122,119,116,114,112,110,110,110,111,113,112,110,108,105,102,99,97,95,93,91,90,90,90,91,92,93,93,94,95,98,100,101,101,100,98,96,93,90,87,85,83,81,78,77,76,78,79,82,84,87,90,93,95,96,96,97,99,101,104,105,105,104,104,105,104,104,103,102,101,98,95,92,89,86,84,83,81,78,76,74,71,69,67,65,62,60,58,57,56,56,56,55,55,54,54,54,54,54,55,55,55,55,55,55,55,55,56,57,57,58,57,57,57,57,57,58,58,57,57,57,57,57,56,55,55,54,53,53,52,51,51,51,50,50,49,48,47,46,45,44,44,43,42,41,40,39,39,38,37,37,38,37,37,37,37,36,36,35,34,34,33,32,31,31,30,29,29,28,28,28,28,28,27,27,27,27,26,26,26,26,26,25,25,25,24,25,25,26,27,27,28,29,30,30,30,30,30,29,28,28,27,27,26,25,25,24,24,24,23,23,23,22,22,22,22,22,21,20,19,19,19,19,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,19,19,18,18,18,18,18,18,17,17,17,17,17,16,16,16,16,16,16,15,15,15,15,14,14,14,14,13,13,13,12,12,12,12,11,11,11,10,10,10,10,10,9,9,9,9,9,9,9,9,9,9,9,8,8,8,8,8,8,8,7,7,7,7,6,6,6,6,6,5,5,5,5,4,4,4,4,4,4,3,3,3,3,3,3,3,3,3,3,3,3,3,2,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

ir_24=[]

step=60

counter=0

while(counter < len(ir_list) ):
    ir_24.append(sum(ir_list[counter:counter+step]))
    
    counter+=step
    
print(len(ir_24))