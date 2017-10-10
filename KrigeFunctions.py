# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 16:22:02 2017

@author: 212614565
"""

import pandas as pd
import re
from pandas import DataFrame, Series
import config
import numpy as np
from pykrige.rk import Krige
from pykrige.compat import GridSearchCV
from pykrige.ok import OrdinaryKriging
from pykrige.uk import UniversalKriging
import pykrige.kriging_tools as kt
import math
from scipy import signal
import csv
from geopandas import GeoDataFrame
from shapely.geometry import Polygon, Point
import geopandas as gpd


###################
#VARIABLES
###################

#Regions allow you to specify the area you are interested in
regions = {}
regions['east'] = [28.4, 49, -106, -86.75]
#eg: regions['new'] = [min latitude, max latitude, min longitude, max longitude]


##Option to use states as regions
#import ast
#states = pd.read_csv('StateBoundingBoxes.csv')
#states['State'] = states['State'].str.replace('\d','')
#for i in range(len(states['BoundingBox'])):
#    states['BoundingBox'][i] = ast.literal_eval(states['BoundingBox'][i])
#states = states.set_index('State')['BoundingBox'].to_dict()


###################
#FUNCTIONS
###################

'''
input requirements for GetWeatherData:
    dateRange: list of strings (either a single date, or the min/max of a range)
    metrics: list of strings
    time: string ('day' or 'month')
    function: string ('mean') *other functionality to be added
'''

def GetWeatherData(dateRange, metrics, time, function):
    #add in datetime and station ids, these are required for every query
    metrics.insert(0,'date_time')
    metrics.insert(0,'stationpoints_id')
    #if the request is only for data from one day
    if len(dateRange) == 1:
        s="" #initiate empty string, add each metric to string for query
        for i in metrics:
            if i != metrics[-1]:
                s += str(i)
                s += ', '
            else:
                s += str(i)
        #create SQL queries. q is for the weather data, q1 is for the station data (includes gps locations)
        q = 'SELECT '+s+' FROM public.mesowest_weather_data_2011 WHERE date_time::date BETWEEN '+str(dateRange)[1:-1]+' AND '+str(dateRange)[1:-1]
        q1 = "SELECT geom, objectid, latitude, longitude, status FROM public.mesowest_stationpoints WHERE objectid IN(SELECT stationpoints_id FROM public.mesowest_weather_data_2011 WHERE date_time::date BETWEEN "+str(dateRange)[1:-1]+" AND "+str(dateRange)[1:-1]+")"
    #if the request is for a date range 
    elif len(dateRange) == 2:
        s="" #initiate empty string, add each metric to string for query
        for i in metrics:
            if i != metrics[-1]:
                s += str(i)
                s += ', '
            else:
                s += str(i)
        #create SQL queries. q is for the weather data, q1 is for the station data (includes gps locations)
        q = "SELECT " + s +" FROM public.mesowest_weather_data_2011 WHERE date_time::date BETWEEN '"+dateRange[0]+"' AND '"+dateRange[1]+"'"
        q1 = "SELECT geom, objectid, latitude, longitude, status FROM public.mesowest_stationpoints WHERE objectid IN (SELECT stationpoints_id FROM public.mesowest_weather_data_2011 WHERE date_time::date BETWEEN '"+dateRange[0]+"' AND '"+dateRange[1]+"')"
        print(q1)
    #connect to database and query
    db_data = config.connect(q)
    db_stations = config.connect(q1)
    #change results from database into dataframes
    df_data = DataFrame.from_records(db_data, columns=metrics)
    df_stations = DataFrame.from_records(db_stations, columns=['geom','station_id','latitude','longitude','status'])
    for m in metrics: #change columns to numeric
        df_data[m] = pd.to_numeric(df_data[m], errors='coerce')
    #change date_time column into a date and time column
    temp = pd.DatetimeIndex(df_data['date_time'])
    df_data['date'], df_data['time'] = temp.date, temp.time
    del df_data['date_time']
    del temp
    df_data.rename(columns={'stationpoints_id':'station_id'}, inplace=True) #match col names across df_data and df_stations (necessary for merge)
    return df_data, df_stations

#TEST
#dates=['2011-01-10','2011-01-12']
#metrics=['air_temp_set_1','altimeter_set_1']
#df_data, df_stations = GetWeatherData(dates, metrics, 'Day', 'Mean')

###################
###################

'''
input requirements for GetWeatherData:
    time: string ('day') *other functionality to be added
    weatherDF: df_data produced from GetWeatherData function
    stationsDF: df_stations produced from GetWeatherData function
'''

def MergeData(time, weatherDF, stationsDF):
    if time == 'day':
        df_data = weatherDF.groupby(['station_id','date'], as_index=False).mean() #Combine by station, with average
        df_combo = pd.merge(df_data, stationsDF, how='left', on=['station_id']) #join on station (giving temperature a lat/long)
        df_combo['date'] = df_combo['date'].apply(lambda x: x.strftime('%Y-%m-%d')) #format date
        return df_combo
    elif time == 'month':
        print ('Functionality to be added.')
    else:
        print (" 'time' parameter must be either 'day' or 'month'. ")

#TEST
#df_1 = MergeData('day',df_data, df_stations)

###################
###################

'''
input requirements for dataPrep:
    df: df_combo produced by MergeData
    region: string ('east' or any other option added above in the VARIABLES section)
    date: string (format: '2011-XX-XX') *must be a date from within the original date range used for GetWeatherData
    metric: string (any metric from the original list of metrics used for GetWeatherData)
'''

def dataPrep(df, region, date, metric):
    df1 = df[df['date'] == date] #select date
    df1 = df1[(df1['latitude'] > regions[region][0]) & (df1['latitude'] < regions[region][1]) &
              (df1['longitude'] < regions[region][3]) & (df1['longitude'] > regions[region][2])] #reduce region
    df1 = df1[df1['status'] == 'ACTIVE'] #remove inactive stations
    df1 = df1[['longitude','latitude', metric]] #select necessary columns
    sh1 = df1.shape[0]
    df1 = df1[np.abs(df1[metric]-df1[metric].mean())<=(3*df1[metric].std())] #remove outliers
    sh2 = df1.shape[0]
    print ('Number of outliers removed: {}'.format(sh1-sh2)) #print number of outliers removed
    P = np.array(df1[['longitude','latitude', metric]]) #change to ndarray, necessary for Krige function
    return P

#TEST
#P = dataPrep(df_combo, 'east', '2011-01-10', 'air_temp_set_1')

###################
###################

'''
input requirements for KrigeCV:
    P: P ndarray produced by dataPrep
    lags: list of numbers
    date: string (format: '2011-XX-XX') *must be a date from within the original date range used for GetWeatherData
    metric: string (any metric from the original list of metrics used for GetWeatherData)
    output: string ('ASCII') *additional functionality to be added
'''

def KrigeCV(P, lags, date, metric, output):
    #create dictionary for gridsearch to use in parameter tuning
    param_dict = {"method": ["ordinary","universal"],
              "variogram_model": ["exponential","gaussian","linear","power","spherical"],
              "nlags": lags,
              "weight": [True, False]
              }
    estimator = GridSearchCV(Krige(), param_dict, verbose=False, cv=2) ###This cv=2 could be adjusted
    X = (P[:,0:2]) #select x variables
    y = P[:,2] #select y variable
    estimator.fit(X=X, y=y)
    if hasattr(estimator, 'best_score_'):
        print('best_score R² = {:.3f}'.format(estimator.best_score_))
        print('Optimal Lags: {}'.format(estimator.best_params_['nlags']))
        print('best_params = ', estimator.best_params_)
        
    #define grid
    dist = .15
    gridx = np.arange(math.floor(min(P[:,0])), math.ceil(max(P[:,0])), dist)
    gridy = np.arange(math.floor(min(P[:,1])), math.ceil(max(P[:,1])), dist)
    ##to be used for shapefile output
    #gridxShape = np.arange(math.floor(min(P[:,0])) - (.5*dist), math.ceil(max(P[:,0])) + (.5*dist), dist)
    #gridyShape = np.arange(math.floor(min(P[:,1])) - (.5*dist), math.ceil(max(P[:,1])) + (.5*dist), dist)
    
    if estimator.best_params_['method'] == 'universal': #for all universal kriging
        UK = UniversalKriging(P[:, 0], P[:, 1], P[:, 2], variogram_model=estimator.best_params_['variogram_model'],
                     nlags = estimator.best_params_['nlags'], weight = estimator.best_params_['weight'],
                     verbose=False, enable_plotting=True) #perform kriging with params chosen by gridsearch
        z, ss = UK.execute('grid', gridx, gridy)
        if output == 'ASCII':
            filename = str(date)+'_'+str(metric)+'.asc' #Create unique filename
            kt.write_asc_grid(gridx, gridy, z, filename=filename) #write out as ASCII file
        elif output == 'Shapefile':
            geo_df = OutputShape(z,gridxShape,gridyShape)
            filename = str(date)+'_'+str(metric)+'.shp'
            geo_df.to_file(filename)
        else:
            print ("output parameter must be 'ASCII' or 'Shapefile'. ")
    elif estimator.best_params_['method'] == 'ordinary': #for all ordinary kriging
        OK = OrdinaryKriging(P[:, 0], P[:, 1], P[:, 2], variogram_model=estimator.best_params_['variogram_model'],
                     nlags = estimator.best_params_['nlags'], weight = estimator.best_params_['weight'],
                     verbose=False, enable_plotting=True) #perform kriging with params chosen by gridsearch
        z, ss = OK.execute('grid', gridx, gridy)
        if output == 'ASCII':
            filename = str(date)+'_'+str(metric)+'.asc' #Create unique filename
            kt.write_asc_grid(gridx, gridy, z, filename=filename) #write out as ASCII file
        elif output == 'Shapefile':
            geo_df = OutputShape(z,gridxShape,gridyShape)
            filename = str(date)+'_'+str(metric)+'.shp'
            geo_df.to_file(filename)
        else:
            print ("output parameter must be 'ASCII' or 'Shapefile'. ")
    else:
        print ('Kriging method not recognized as Universal or Ordinary')
    sub=[] #create and fill list, to save Rsquared and other outputs/parameters
    sub.extend((date,metric,estimator.best_score_,estimator.best_params_))
    return sub

#TEST
#lags = [10,30,60]
#lst = KrigeCV(P, lags, '2011-07-31', 'air_temp_set_1', output='ASCII')

###################
###################

'''
input requirements for KrigeCV:
    df: df_combo produced by MergeData
    region: string ('east' or any other option added above in the VARIABLES section)
    dates: list of strings (format: '2011-XX-XX') *must be date(s) from within the original date range used for GetWeatherData
    metrics: list of strings (any metric from the original list of metrics used for GetWeatherData)
    printCSV: True/False (will write out a CSV with details for each krige performed)
    output: string ('ASCII') *additional functionality to be added
'''

def DailyKrige(df, region, dates, metrics, printCSV, output):
    #initiate list to collect data for CSV output
    details=[]
    cols = ['Date','Metric','R-Squared','Optimal Kriging Options']
    details.append(cols) #add column titles to CSV output
    if 'stationpoints_id' in metrics:
        metrics.remove('stationpoints_id')
    if 'date_time' in metrics:
        metrics.remove('date_time')
    for j in metrics:
        for i in dates:
            P = dataPrep(df, region, i, j) #clean data
#            lags = [2,4]
            lags = [2,4,6,8,10,12,14,16,18,20,22,24,26,28,30]
            lst = KrigeCV(P, lags, i, j, output) #perform kriging
            details.append(lst)
    if printCSV==False:
        pass
    else:
        with open('Details.csv', 'w', newline='') as f: #create CSV output
            writer = csv.writer(f)
            writer.writerows(details)

#TEST
#DailyKrige(df_combo, 'east', ['air_temp_set_1','altimeter_set_1'],['2011-01-10','2011-01-12'],csv=True )




