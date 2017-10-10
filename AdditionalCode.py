# -*- coding: utf-8 -*-
"""
Created on Thu Aug  3 12:09:57 2017

@author: 212614565
"""


#%%
#Create Koppen shapefile
import geopandas as gpd
import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Point
#read in koppen
chdir('C:/Users/212614565/Desktop/Weather/Kriging')
kop = pd.read_csv('KoppenClasses.csv')
#kopCfa = kop[kop['Class']=='Cfa']
kop['gps'] = kop.apply(lambda x: [x.Lat, x.Long], axis=1)

geometry = [Point(xy) for xy in zip(kop.Long, kop.Lat)]
kop.drop(['Long','Lat','gps'], axis=1, inplace=True)
crs = {'init':'epsg:4326'}
geo_df = GeoDataFrame(kop, crs=crs, geometry=geometry)

#write out file
out1 = r"C:/Users/212614565/Desktop/Weather/Kriging/Koppen.shp"
geo_df.to_file(out1)

#%%
def MonthlyKrige(df, region, metrics, csv):
    months=[1,2,3,4,5,6,7,8,9,10,11,12]
    details=['Month','Metric','R-Squared','Optimal Kriging Options']
    for j in metrics:
        for i in months:
            P = dataPrep(df, 'east', i, j)
            lags = [2,4,6,8,10,12,14,16,18,20,22,24,26,28,30]
            lst = KrigeCV(P, lags, i, j, 'ASCII')
            details.append(lst)
    if csv==False:
        pass
    else:
        with open('Details.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(details)
            
TEST
MonthlyKrige(df3, 'east', ['MeanTemp'], csv)

#%%
####FUNCTION TO EXPORT TO SHAPEFILE INSTEAD OF ASCII
#create shapefile from grids and Z

##BROKEN - SHIFTS EACH POLYGON 
from geopandas import GeoDataFrame
from shapely.geometry import Polygon
import geopandas as gpd

gdf = gpd.GeoDataFrame(data=z,index=pd.Series(gridy), columns=pd.Series(gridx))

#replace with function created below
gdf['ind2'] = gdf.index
gdf.ind2 = gdf.ind2.shift(-1)
gdf['new'] = tuple(zip(gdf.index,gdf.ind2))
gdf.set_index('new', inplace=True, drop=True)
gdf.drop('ind2', axis=1, inplace=True)

#create function to do this for both columns and rows
colN = list(gdf.columns)
newCols = []
for i in range(len(colN)-1):
    newCols.append((colN[i],colN[i+1]))
gdf = gdf.iloc[0:-1,0:-1]
gdf.columns = newCols

gdf['ind'] = gdf.index
ngdf = pd.melt(gdf, id_vars=['ind'])

ngdf['coords'] = ngdf.apply(lambda row: [[(a,b) for a in list(row.variable) for b in list(row.ind)]], axis=1)
ngdf.coords = ngdf.coords.apply(lambda x: [[x[0][0],x[0][1],x[0][3],x[0][2],x[0][0]]])
ngdf.coords = ngdf.coords.apply(lambda x: x[0])
ngdf['geometry'] = ngdf.coords.apply(lambda x: Polygon(x))
ngdf = ngdf[['geometry','value']]
geometry = ngdf.geometry

crs = {'init':'epsg:4326'}
geo_df = GeoDataFrame(ngdf, crs=crs, geometry=geometry)

#write out file
out1 = r"C:/Users/212614565/Desktop/Weather/Kriging/practice.shp"
geo_df.to_file(out1)


#%%
#ATTEMPT TO FIX ABOVE PROBLEM BY SHIFTING BOXES BY HALF DIST (.075)
OK = OrdinaryKriging(P[:, 0], P[:, 1], P[:, 2])
z, ss = OK.execute('grid', gridx, gridy)
        
        
#create geodataframe
gdf = gpd.GeoDataFrame(data=z,index=pd.Series(gridy), columns=pd.Series(gridx))
#maniuplate index and column names to prep for polygon creation
gdf['ind3'] = gdf.index
gdf['ind3'] = gdf.index - .075
gdf['ind4'] = gdf.index + .075
gdf['new'] = tuple(zip(gdf.ind3,gdf.ind4))
gdf.set_index('new', inplace=True, drop=True)
gdf.drop('ind3', axis=1, inplace=True)
gdf.drop('ind4', axis=1, inplace=True)
colN = list(gdf.columns)
newCols = []
for i in range(len(colN)-1):
    newCols.append((colN[i]-.075,colN[i+1]-.075))
gdf = gdf.iloc[0:-1,0:-1]
gdf.columns = newCols
gdf['ind'] = gdf.index
gdf = pd.melt(gdf, id_vars=['ind'])
#create polygons and assign to geometry
gdf['coords'] = gdf.apply(lambda row: [[(a,b) for a in list(row.variable) for b in list(row.ind)]], axis=1)
gdf.coords = gdf.coords.apply(lambda x: [[x[0][0],x[0][1],x[0][3],x[0][2],x[0][0]]])
gdf.coords = gdf.coords.apply(lambda x: x[0])
gdf['geometry'] = gdf.coords.apply(lambda x: Polygon(x))
gdf = gdf[['geometry','value']]
geometry = gdf.geometry
#define crs and create final geodataframe
crs = {'init':'epsg:4326'}
geo_df = GeoDataFrame(gdf, crs=crs, geometry=geometry)
return geo_df



geo_df.to_file('attempt.shp')