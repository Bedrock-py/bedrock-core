#****************************************************************
#  File: utils.py
#
# Copyright (c) 2015, Georgia Tech Research Institute
# All rights reserved.
#
# This unpublished material is the property of the Georgia Tech
# Research Institute and is protected under copyright law.
# The methods and techniques described herein are considered
# trade secrets and/or confidential. Reproduction or distribution,
# in whole or in part, is forbidden except by the express written
# permission of the Georgia Tech Research Institute.
#****************************************************************/

#This file contains helper functions used in the various Loader files

import argparse, multiprocessing, uuid, datetime

import csv
from datetime import datetime
import os
import pandas as pd
import uuid
import pymongo
from CONSTANTS import *

def get_status(host, src_id):

    client = pymongo.MongoClient(host, MONGO_PORT)
    col = client[WORKFLOWS_DB_NAME][WORKFLOWS_REGISTERED_NAME]
    try:
        status = col.find({'work_id':src_id})[0]['status']
        return status
    except IndexError:
        return False

def update_status(host, src_id):

    client = pymongo.MongoClient(host, MONGO_PORT)
    col = client[WORKFLOWS_DB_NAME][WORKFLOWS_REGISTERED_NAME]
    try:
        status = col.find({'work_id':src_id})[0]['status']
        col.update({'work_id':src_id}, {'$set':{'status': not status}})

    except IndexError:
        pass

def get_count(host, src_id):

    client = pymongo.MongoClient(host, MONGO_PORT)
    col = client[WORKFLOWS_DB_NAME][WORKFLOWS_REGISTERED_NAME]
    try:
        count = col.find({'work_id':src_id})[0]['count']
        return count
    except IndexError:
        return 0

def increment_count(host, src_id):

    client = pymongo.MongoClient(host, MONGO_PORT)
    col = client[WORKFLOWS_DB_NAME][WORKFLOWS_REGISTERED_NAME]
    try:
        count = col.find({'work_id':src_id})[0]['count']
        col.update({'work_id':src_id}, {'$set':{'count': count+1}})
        return count+1

    except IndexError:
        return 0

def get_stash(host, src_id):

    client = pymongo.MongoClient(host, MONGO_PORT)
    col = client[WORKFLOWS_DB_NAME][WORKFLOWS_REGISTERED_NAME]
    try:
        vis = col.find({'work_id':src_id})[0]['stash']
        return vis
    except IndexError:
        return []

def set_stash(host, src_id, new):

    client = pymongo.MongoClient(host, MONGO_PORT)
    col = client[WORKFLOWS_DB_NAME][WORKFLOWS_REGISTERED_NAME]
    vis = col.find({'work_id':src_id})[0]['stash']
    col.update({'work_id':src_id}, { '$set': {'stash': new} })

def getNewId():
	return uuid.uuid4().hex

def getCurrentTime():
	return str(datetime.now())

def initialize(work, options):
    #options can be specific and unique for each workflow
    for each in options:
        setattr(work, each['attrname'], each['value'])

def get_metadata(workflow_id):
    exec("import opals." + workflow_id)
    filename = "opals." + workflow_id
    classname = filename.split(".")[-1]
    objectname = "opals." + workflow_id + '.' + classname
    work = eval(objectname)() #create the object specified

    metadata = {}
    metadata['name'] = work.get_name()
    metadata['classname'] = classname
    metadata['description'] = work.get_description()
    metadata['parameters'] = work.get_parameters_spec()
    # metadata['inputs'] = work.get_inputs()
    return metadata

# def explore(work_id):
#     exec("import work." + work_id)
#     filename = "work." + work_id
#     classname = filename.split(".")[-1]
#     objectname = "work." + work_id + '.' + classname
#     work = eval(objectname)() 
#     return work.explore()

def update(workflow_id, filepath):
    exec("import work." + workflow_id)
    filename = "work." + workflow_id
    classname = filename.split(".")[-1]
    objectname = "work." + workflow_id + '.' + classname
    work = eval(objectname)() 
    work.update(filepath)

def toil(workflow_id, parameters, filepath):
    exec("import work." + workflow_id)
    filename = "work." + workflow_id
    classname = filename.split(".")[-1]
    objectname = "work." + workflow_id + '.' + classname
    work = eval(objectname)() 
    initialize(work, parameters)
    multiprocessing.Process(target=work.toil, args=[filepath]).start()
    return 

class Workflow(object):
    def __init__(self):
        pass

    def check_parameters(self):
        #check to make sure inputs are set
        try:
            for each in self.parameters:
                eval("self." + each)
            return True
        except AttributeError:
            raise
            print 'Necessary attribute(s) not initialized'
            return False


    def get_inputs(self):
        return self.inputs

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def get_parameters_spec(self):
        return self.parameters_spec

