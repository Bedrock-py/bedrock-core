#****************************************************************
#  File: filter_utils.py
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

import os
import numpy as np


def initialize(filter, parameters):
    #options can be specific and unique for each filter
    for each in parameters:
        setattr(filter, each['attrname'], each['value'])

def get_metadata(filter_id):
    exec("import filters." + filter_id)
    filename = "filters." + filter_id
    classname = filename.split(".")[-1]
    objectname = "filters." + filter_id + '.' + classname
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

def check(filter_id, name, col):
    exec("import filters." + filter_id)
    filename = "filters." + filter_id
    classname = filename.split(".")[-1]
    objectname = "filters." + filter_id + '.' + classname
    filt = eval(objectname)() #create the object specified
    return filt.check(name, col)

def apply(filter_id, parameters, col):
    exec("import filters." + filter_id)
    filename = "filters." + filter_id
    classname = filename.split(".")[-1]
    objectname = "filters." + filter_id + '.' + classname
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

# if __name__=='__main__':

#     DIRPATH = '/var/www/analytics-framework/dataloader/data/'
#     RESPATH = ''
#     res_id = 'testing/'
#     # matrix = { "created": "2014-11-12 17:28:03.585073","filters": [],"mat_id": "3846b9469ed545918f874dfda94506d8","mat_type": "csv","name": "city_pop","src_id": "6e0cde8003c1495989b3613e70b7b755"}
#     # filepath = DIRPATH + matrix['src_id'] + '/' + matrix['mat_id'] + '/matrix.' + matrix['mat_type']
#     storepath = RESPATH + res_id
#     # os.makedirs(storepath)
#     analytic_id = 'kmeans'
#     # print filepath
#     filepath = "../iris.txt"
#     # inputData = data[:,[0,1]]
#     # labels = data[:,2]
    
#     classname = "Kmeans"
#     inputs =  [ { "name" : "Clusters", "pyID" : "numClusters", "value" : 3, "type" : "int" } ]
#     run_analysis(classname,analytic_id, inputs, filepath, storepath)


