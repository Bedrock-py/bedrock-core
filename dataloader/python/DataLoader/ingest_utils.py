#****************************************************************
#  File: ingest_utils.py
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
import filter_utils
import json

def get_metadata(ingest_id):
    exec("import ingest." + ingest_id)
    filename = "ingest." + ingest_id
    classname = filename.split(".")[-1]
    objectname = "ingest." + ingest_id + '.' + classname
    mod = eval(objectname)() #create the object specified
    metadata = {}
    metadata['name'] = mod.get_name()
    metadata['classname'] = classname
    metadata['description'] = mod.get_description()
    metadata['parameters'] = mod.get_parameters_spec()
    # metadata['inputs'] = mod.get_inputs()
    return metadata

def explore(ingest_id, filepath, filters):
    exec("import ingest." + ingest_id)
    filename = "ingest." + ingest_id
    classname = filename.split(".")[-1]
    objectname = "ingest." + ingest_id + '.' + classname
    mod = eval(objectname)() #create the object specified
    mod.initialize_filters(filters)
    return mod.explore(filepath)


def ingest(posted_data, src):
    exec("import ingest." + src['ingest_id'])
    filename = "ingest." + src['ingest_id']
    classname = filename.split(".")[-1]
    objectname = "ingest." + src['ingest_id'] + '.' + classname
    mod = eval(objectname)() #create the object specified
    return mod.ingest(posted_data, src)

def stream(ingest_id, filepath):#update for function 
    exec("import ingest." + ingest_id)
    filename = "ingest." + ingest_id
    classname = filename.split(".")[-1]
    objectname = "ingest." + ingest_id + '.' + classname
    mod = eval(objectname)() #create the object specified
    multiprocessing.Process(target=mod.stream, args=[filepath]).start()
    return 

    # mod.stream(filepath)

def update(ingest_id, filepath):#update for function 
    exec("import ingest." + ingest_id)
    filename = "ingest." + ingest_id
    classname = filename.split(".")[-1]
    objectname = "ingest." + ingest_id + '.' + classname
    mod = eval(objectname)() #create the object specified
    return mod.update(filepath)

class IngestModule(object):
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
        if type_name == 'String':
            for filt in self.string_filters_id:
                if filter_utils.check(filt, name, sample):
                    return self.string_filters[self.string_filters_id.index(filt)]
        elif type_name == 'Numeric':
            for filt in self.num_filters_id:
                if filter_utils.check(filt, name, sample):
                    return self.num_filters[self.num_filters_id.index(filt)]

    def apply_filter(self, filter_id, parameters, col):
        return filter_utils.apply(filter_id, parameters, col)

    def get_inputs(self):
        return self.inputs

    def get_name(self):
        return self.name
        
    def get_description(self):
        return self.description

    def get_parameters_spec(self):
        return self.parameters_spec
