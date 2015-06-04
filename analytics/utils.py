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

import os
import pymongo
import numpy as np
from datetime import datetime
import csv
from datetime import datetime
import pandas as pd
import uuid

def getNewId():
	return uuid.uuid4().hex

def getCurrentTime():
	return str(datetime.now())

#get a unique folder name and create the folder, return the filepath
def setUpDirectory():
    dirName = uuid.uuid4().hex
    # dirName = datetime.now().strftime("%Y%m%d%H%M%S%f")
    rootpath = DIRPATH + dirName + '/'
    os.makedirs(rootpath)
    return DIRPATH, dirName

def setUpDirectoryMatrix(src_id):
    dirName = uuid.uuid4().hex
    # dirName = datetime.now().strftime("%Y%m%d%H%M%S%f")
    rootpath = DIRPATH + src_id + '/' + dirName + '/'
    os.makedirs(rootpath)
    return rootpath, dirName


#use pandas to load the csv file into the dataframe, 
#using a header if appropriate
def loadMatrix(filepath):
    with open(filepath, 'rbU') as csvfile:
        snippet = csvfile.read(2048)
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(snippet)

    if sniffer.has_header(snippet):
        df = pd.read_csv(filepath, dialect=dialect)
    else:
        df = pd.read_csv(filepath, dialect=dialect, header=None)

    return df

#write the output files associated with each loaded file
#matrix.csv, features.txt, features_original.txt, and any non-numeric fields' mappings
def writeFiles(maps, matrixFeatures, matrixFeaturesOriginal, rootpath, return_data=False):
	#make directory
    if not os.path.exists(rootpath):
        os.makedirs(rootpath)

    #write output files
    toWrite = []
    #list of features to write to the output features.txt file
    features = []
    featuresOrig = []

    #determine if a feature is numeric or has a label mapping
    for i, each in enumerate(matrixFeatures):
    # for each in maps.keys():
        if isinstance(maps[each], list):
            toWrite.append(maps[each])
        #since the feature has a label mapping, write out the label values in order for later reference
        #filename is the feature name + .txt
        else:
            try:
                toWrite.append([str(x) for x in maps[each]['values']])
            except KeyError:
                pass #ignore, since this is the mongoids field and has no values
            #write the features to output
            writeOutput(rootpath, each, maps[each]['indexToLabel'])
        if matrixFeaturesOriginal[i] != '_id': #don't do this for mongoids
            features.append(each)
            featuresOrig.append(matrixFeaturesOriginal[i])


    #write out the list of features
    writeOutput(rootpath, 'features_original', featuresOrig)
    writeOutput(rootpath, 'features', features)

    toReturn = []
    #convert lists to numpy arrays
    #matrix is documents x features (i.e. rows = individual items and columns = features)
    with open(rootpath + '/' + 'matrix.csv', 'w') as matrix:        
        for i in range(len(toWrite[0])):
            temp = []
            for each in toWrite:
                temp.append(each[i])
                if return_data:
                	toReturn.append(temp)
            matrix.write(','.join(temp) + '\n')

    if return_data:
        return toReturn

def updateFiles(maps, matrixFeatures, matrixFeaturesOriginal, rootpath, return_data=False):

    #write output files
    toWrite = []

    #determine if a feature is numeric or has a label mapping
    for i, each in enumerate(matrixFeatures):
    # for each in maps.keys():
        if isinstance(maps[each], list):
            toWrite.append(maps[each])
        #since the feature has a label mapping, write out the label values in order for later reference
        #filename is the feature name + .txt
        else:
            try:
                toWrite.append([str(x) for x in maps[each]['values']])
            except KeyError:
                pass #ignore, since this is the mongoids field and has no values
            #write the features to output
            appendOutput(rootpath, each, maps[each]['indexToLabel'])

    toReturn = []
    #convert lists to numpy arrays
    #matrix is documents x features (i.e. rows = individual items and columns = features)
    with open(rootpath + '/' + 'matrix.csv', 'a') as matrix:        
        for i in range(len(toWrite[0])):
            temp = []
            for each in toWrite:
                temp.append(each[i])
            matrix.write(','.join(temp) + '\n')
            if return_data:
            	toReturn.append(temp)

    if return_data:
        return toReturn

def initialize(alg, parameters):
    #options can be specific and unique for each algorithm
    for each in parameters:
        setattr(alg, each['attrname'], each['value'])

def get_metadata(analytic_id):
    exec("import opals." + analytic_id)
    filename = "opals." + analytic_id
    classname = filename.split(".")[-1]
    objectname = "opals." + analytic_id + '.' + classname
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
    exec("import opals." + analytic_id)
    filename = "opals." + analytic_id
    classname = filename.split(".")[-1]
    objectname = "opals." + analytic_id + '.' + classname
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


