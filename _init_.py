#!/usr/bin/env python3 
# coding:utf-8
import requests
import os
from configparser import ConfigParser

def read_config(section):
    """ Read database configuration file and return a dictionary object
    :param filename: name of the configuration file
    :param section: section of database configuration
    :return: a dictionary of database parameters
    """
    # create parser and read ini configuration file
    dir = os.getcwd()
    filename = dir + '/config.ini'
    parser = ConfigParser()
    parser.read(filename)
 
    # get section, default to mysql
    db = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            db[item[0]] = item[1]
    else:
        raise Exception('{0} not found in the {1} file'.format(section, filename))
 
    return db
    
def is_alive(site):
    '''function to ckeck if the site is alive'''
    r = requests.get(site , verify=False)
    if r.status_code == 200:
        print("Welcome to " + site)
    else:
        raise Exception('Error {0}: {1}'.format(r.status_code,r.exception.RequestException))
        
