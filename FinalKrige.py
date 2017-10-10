# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 15:44:12 2017

@author: 212614565
"""


'''
INSTRUCTIONS

STEP 1. Choose the date range and metrics you would like to Krige,
    and enter them into lists
    *a full list of potential metrics can be found in '2011_Meso_All_Metrics'.
STEP 2. GetWeatherData: Pass in the two lists created in step 2. 
    This will connect to the database and pull down all necessary data     
STEP 3. MergeData: Pass in two outputs from step 2, and the temporal granularity desired.
    *monthly funcitonality currently missing, to be added.
STEP 4. DailyKrige: Pass in output from step 3, select region, choose to create an output CSV,
    and specify output type.
    * Shapefile output currently missing, to be added. 

'''

#%%
#IMPORTS
from os import chdir
chdir("C:/Users/212614565/BeckyWeather/Krige Functions")
import KrigeFunctions
from KrigeFunctions import *

#%
'''STEP 1'''
dates=['2011-03-13']
metrics=['air_temp_set_1','dew_point_temperature_set_1d']

#%
'''STEP 2'''
df_data, df_stations = GetWeatherData(dates, metrics, 'Day', 'Mean')

#%
'''STEP 3'''
df_combo = MergeData('day',df_data, df_stations)

#%
'''STEP 4'''
DailyKrige(df_combo, 'east', dates, metrics, printCSV=True, output='ASCII' )


#%%












