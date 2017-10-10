# -*- coding: utf-8 -*-
"""
Created on Thu Jun 22 14:20:22 2017

@author: 212614565
"""

#%%
from configparser import ConfigParser
from os import chdir
import psycopg2
#
#chdir('C:/Users/212614565/Desktop/Weather/PostGres/ConnectPostGres')

def config(filename='database.ini', section='postgres'):
    parser = ConfigParser()
    parser.read(filename)
    db={}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
    return db

#connect function
def connect(query):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()
 
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
 
        # create a cursor
        cur = conn.cursor()
        
 # execute a statement
        cur.execute(query)
 
        # display the PostgreSQL database server version
        db_d = cur.fetchall()
        #print(db_data)
       
     # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
            return db_d