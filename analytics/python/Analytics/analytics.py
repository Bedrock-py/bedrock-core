#****************************************************************
#  File: analytics.py
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

import os, pymongo
import numpy as np
from datetime import datetime


ALGDIR = '/var/www/analytics-framework/analytics/python/Analytics/algorithms/'
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB_NAME = 'analytics'
ANALYTCS = 'analytics'

def initialize(alg, parameters):
    #options can be specific and unique for each algorithm
    for each in parameters:
        setattr(alg, each['attrname'], each['value'])

def get_metadata(analytic_id):
    exec("import algorithms." + analytic_id)
    filename = "algorithms." + analytic_id
    classname = filename.split(".")[-1]
    objectname = "algorithms." + analytic_id + '.' + classname
    alg = eval(objectname)() #create the object specified
    metadata = {}
    metadata['name'] = alg.get_name()
    metadata['classname'] = classname
    metadata['description'] = alg.get_description()
    metadata['parameters'] = alg.get_parameters_spec()
    metadata['inputs'] = alg.get_inputs()
    metadata['outputs'] = alg.get_outputs()
    metadata['type'] = alg.get_type()
    return metadata


def run_analysis(queue, analytic_id, parameters, inputs, storepath, name):
    exec("import algorithms." + analytic_id)
    filename = "algorithms." + analytic_id
    classname = filename.split(".")[-1]
    objectname = "algorithms." + analytic_id + '.' + classname
    alg = eval(objectname)() #create the object specified
    initialize(alg, parameters)
    if alg.check_parameters():
        try:
            alg.compute(inputs, storepath=storepath, name=name)
        except:
            raise
            queue.put(None)
        alg.write_results(storepath)
        print classname + ' successful'
        # return alg.get_outputs()
        queue.put(alg.get_outputs())
    else:
        queue.put(None)

def classify(analytic_id, parameters, inputs):
    exec("import algorithms." + analytic_id)
    filename = "algorithms." + analytic_id
    classname = filename.split(".")[-1]
    objectname = "algorithms." + analytic_id + '.' + classname
    alg = eval(objectname)()
    initialize(alg, parameters)
    if alg.check_parameters():
        return list(alg.classify(inputs))
    else:
        return []

#runs simple dense matrix test
def test_analysis(analytic_id, filepath, storepath):
    exec("import algorithms." + analytic_id)
    filename = "algorithms." + analytic_id
    classname = filename.split(".")[-1]
    objectname = "algorithms." + analytic_id + '.' + classname
    alg = eval(objectname)() #create the object specified
    initialize(alg, alg.parameters_spec)

    if alg.check_parameters():
        try:
            alg.compute(filepath, storepath=storepath)
            alg.write_results(storepath)
        except:
            return False
        else:
            return True
    else:
        return False

def write_analytic(text, classname):
    time = datetime.now()
    analytic_id = classname 
    # + str(time.year) + str(time.month) + str(time.day) + str(time.hour) + str(time.minute) + str(time.second)

    with open(ALGDIR + analytic_id + '.py', 'w') as alg:
        alg.write(text)

    #get the metadata from the file
    metadata = get_metadata(analytic_id)
    metadata['analytic_id'] = analytic_id

    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    col = client[MONGO_DB_NAME][ANALYTCS]

    col.insert(metadata)


class Algorithm(object):
    def __init__(self):
        self.results = {}


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


    def write_results(self, storepath):
        for key, res in self.results.items():
            self.write_output(storepath, key, res)


    def write_output(self, rootpath, key, outputData):
        with open(rootpath + key, 'w') as featuresFile:
            if 'json' in key:
                featuresFile.write(outputData)
            elif 'txt' in key:
                line = '\n'.join([str(x) for x in outputData]) + '\n'
                featuresFile.write(line)
            elif 'analytic' in key:
                write_analytic(outputData['text'], outputData['classname'])
            else:
                #check if each element is a single element or list
                try:
                    len(outputData[0])
                except TypeError:
                    if 'csv' in key:
                        line = ','.join([str(x) for x in outputData])
                        featuresFile.write(line)
                    elif 'txt' in key:
                        assert(len(outputData[0] == 1))
                        line = '\n'.join([str(x) for x in outputData])
                        featuresFile.write(line)

                else:
                    #list
                    if 'csv' in key:
                        for element in outputData:
                            line = ','.join([str(x) for x in element])
                            featuresFile.write(line + '\n')
                    elif 'json' in key:
                        featuresFile.write(outputData) 

    def get_results(self):
        return self.get_outputs()

    def get_inputs(self):
        return self.inputs

    def get_name(self):
        return self.name

    def get_type(self):
        return self.type

    def get_description(self):
        return self.description

    def get_parameters_spec(self):
        return self.parameters_spec

    def get_outputs(self):
        return self.outputs


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


