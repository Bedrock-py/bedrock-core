#****************************************************************
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

import os, multiprocessing
import numpy as np
import json
import uuid
from datetime import datetime
import pymongo
from CONSTANTS import *


def explore(ingest_id, filepath, filters):
    exec("import opals." + ingest_id)
    filename = "opals." + ingest_id
    classname = filename.split(".")[-1]
    objectname = "opals." + ingest_id + '.' + classname
    mod = eval(objectname)() #create the object specified
    mod.initialize_filters(filters)
    return mod.explore(filepath)

def custom(ingest_id, filepath, param1=None, param2=None, param3=None, payload=None):
    exec("import opals." + ingest_id)
    filename = "opals." + ingest_id
    classname = filename.split(".")[-1]
    objectname = "opals." + ingest_id + '.' + classname
    mod = eval(objectname)() #create the object specified
    return mod.custom(filepath, param1=param1, param2=param2, param3=param3, payload=payload)


def initialize(filter, parameters):
    #options can be specific and unique for each filter
    for each in parameters:
        setattr(filter, each['attrname'], each['value'])

def get_metadata(id, api=None):
    if api == 'ingest':
        exec("import opals." + id)
        filename = "opals." + id
        classname = filename.split(".")[-1]
        objectname = "opals." + id + '.' + classname
        mod = eval(objectname)() #create the object specified
        metadata = {}
        metadata['name'] = mod.get_name()
        metadata['classname'] = classname
        metadata['description'] = mod.get_description()
        metadata['parameters'] = mod.get_parameters_spec()
        # metadata['inputs'] = mod.get_inputs()
    elif api == 'filters':
        exec("import opals." + id)
        filename = "opals." + id
        classname = filename.split(".")[-1]
        objectname = "opals." + id + '.' + classname
        filt = eval(objectname)() #create the object specified
        metadata = {}
        metadata['name'] = filt.get_name()
        metadata['type'] = filt.get_type()
        metadata['stage'] = filt.get_stage()
        metadata['input'] = filt.get_input()
        metadata['ouptuts'] = filt.get_outputs()
        metadata['possible_names'] = filt.get_possible_names()
        metadata['classname'] = classname
        metadata['description'] = filt.get_description()
        metadata['parameters'] = filt.get_parameters_spec()

    return metadata


def ingest(posted_data, src):
    exec("import opals." + src['ingest_id'])
    filename = "opals." + src['ingest_id']
    classname = filename.split(".")[-1]
    objectname = "opals." + src['ingest_id'] + '.' + classname
    mod = eval(objectname)() #create the object specified
    return mod.ingest(posted_data, src)

def delete(src):
    exec("import opals." + src['ingest_id'])
    filename = "opals." + src['ingest_id']
    classname = filename.split(".")[-1]
    objectname = "opals." + src['ingest_id'] + '.' + classname
    mod = eval(objectname)() #create the object specified
    return mod.delete(src['rootdir'])


def stream(ingest_id, filepath):#update for function 
    exec("import opals." + ingest_id)
    filename = "opals." + ingest_id
    classname = filename.split(".")[-1]
    objectname = "opals." + ingest_id + '.' + classname
    mod = eval(objectname)() #create the object specified
    multiprocessing.Process(target=mod.stream, args=[filepath]).start()
    return 

    # mod.stream(filepath)

def update(ingest_id, filepath):#update for function 
    exec("import opals." + ingest_id)
    filename = "opals." + ingest_id
    classname = filename.split(".")[-1]
    objectname = "opals." + ingest_id + '.' + classname
    mod = eval(objectname)() #create the object specified
    return mod.update(filepath)

def get_status(src_id):

    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
    try:
        status = col.find({'src_id':src_id})[0]['status']
        return status
    except IndexError:
        return False

def update_status(src_id):

    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
    try:
        status = col.find({'src_id':src_id})[0]['status']
        col.update({'src_id':src_id}, {'$set':{'status': not status}})

    except IndexError:
        pass

def get_count(src_id):

    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
    try:
        count = col.find({'src_id':src_id})[0]['count']
        return count
    except IndexError:
        return 0

def increment_count(src_id):

    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
    try:
        count = col.find({'src_id':src_id})[0]['count']
        col.update({'src_id':src_id}, {'$set':{'count': count+1}})
        return count+1

    except IndexError:
        return 0

def get_stash(src_id):

    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
    try:
        vis = col.find({'src_id':src_id})[0]['stash']
        return vis
    except IndexError:
        return []

def set_stash(src_id, new):

    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
    try:
        vis = col.find({'src_id':src_id})[0]['stash']
        col.update({'src_id':src_id}, { '$set': {'stash': new} })

    except IndexError:
        pass

def getNewId():
    return uuid.uuid4().hex

def getCurrentTime():
    return str(datetime.now())

#get a unique folder name and create the folder, return the filepath
def setUpDirectory():
    dirName = uuid.uuid4().hex
    # dirName = datetime.now().strftime("%Y%m%d%H%M%S%f")
    rootpath = DIRPATH + dirName + '/'
    os.makedirs(rootpath, 777)
    return DIRPATH, dirName

def setUpDirectoryMatrix(src_id):
    dirName = uuid.uuid4().hex
    # dirName = datetime.now().strftime("%Y%m%d%H%M%S%f")
    rootpath = DIRPATH + src_id + '/' + dirName + '/'
    os.makedirs(rootpath, 777)
    return rootpath, dirName
    
def check(filter_id, name, col):
    exec("import opals." + filter_id)
    filename = "opals." + filter_id
    classname = filename.split(".")[-1]
    objectname = "opals." + filter_id + '.' + classname
    filt = eval(objectname)() #create the object specified
    return filt.check(name, col)

def apply(filter_id, parameters, col):
    exec("import opals." + filter_id)
    filename = "opals." + filter_id
    classname = filename.split(".")[-1]
    objectname = "opals." + filter_id + '.' + classname
    filt = eval(objectname)() #create the object specified
    initialize(filt, parameters)
    return filt.apply(col)

class Filter(object):
    def __init__(self):
        pass

    def get_input(self):
        return self.input

    def get_outputs(self):
        return self.outputs

    def get_type(self):
        return self.type

    def get_stage(self):
        return self.stage

    def get_name(self):
        return self.name
        
    def get_description(self):
        return self.description

    def get_parameters_spec(self):
        return self.parameters_spec

    def get_possible_names(self):
        return self.possible_names

class Ingest(object):
    def __init__(self):
        pass

    def initialize(self, conf_filepath):
        with open(conf_filepath) as json_data:
            data = json.loads(json_data.read())
        for each in data:
            setattr(self, each['attrname'], each['value'])


    def initialize_filters(self, filters):
        self.string_filters_id = []
        self.string_filters = []
        # self.float_filters = []
        self.num_filters_id = []
        self.num_filters = []
        for filt in filters:
            if filt['input'] == 'String':
                self.string_filters.append(filt['name'])
                self.string_filters_id.append(filt['filter_id'])
            elif filt['input'] == 'Numeric':
                self.num_filters.append(filt['name'])
                self.num_filters_id.append(filt['filter_id'])

        #print self.string_filters
            # elif filt['input'] == 'Float':
            #     self.float_filters.append({key: value for key, value in filt.items() if key != '_id'})


    def get_filters(self, type_name):
        if type_name == 'String':
            return self.string_filters
        elif type_name == 'Numeric':
            return self.num_filters

    def get_best_filter(self, type_name, name, sample):
        # if type_name == 'String':
        #     for filt in self.string_filters_id:
        #         if utils.check(filt, name, sample):
        #             return self.string_filters[self.string_filters_id.index(filt)]
        # elif type_name == 'Numeric':
        #     for filt in self.num_filters_id:
        #         if utils.check(filt, name, sample):
        #             return self.num_filters[self.num_filters_id.index(filt)]
        return None

    def apply_filter(self, filter_id, parameters, col):
        return apply(filter_id, parameters, col)

    def get_inputs(self):
        return self.inputs

    def get_name(self):
        return self.name
        
    def get_description(self):
        return self.description

    def get_parameters_spec(self):
        return self.parameters_spec

    def delete(self, rootpath):
        return
        
