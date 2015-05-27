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

import csv
from datetime import datetime
import os
import pandas as pd
import uuid
import pymongo


MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB_NAME = 'workflows'
MONGO_COL_NAME = 'registered'

def get_status(host, src_id):

    client = pymongo.MongoClient(host, MONGO_PORT)
    col = client[MONGO_DB_NAME][MONGO_COL_NAME]
    try:
        status = col.find({'work_id':src_id})[0]['status']
        return status
    except IndexError:
        return False

def update_status(host, src_id):

    client = pymongo.MongoClient(host, MONGO_PORT)
    col = client[MONGO_DB_NAME][MONGO_COL_NAME]
    try:
        status = col.find({'work_id':src_id})[0]['status']
        col.update({'work_id':src_id}, {'$set':{'status': not status}})

    except IndexError:
        pass

def get_count(host, src_id):

    client = pymongo.MongoClient(host, MONGO_PORT)
    col = client[MONGO_DB_NAME][MONGO_COL_NAME]
    try:
        count = col.find({'work_id':src_id})[0]['count']
        return count
    except IndexError:
        return 0

def increment_count(host, src_id):

    client = pymongo.MongoClient(host, MONGO_PORT)
    col = client[MONGO_DB_NAME][MONGO_COL_NAME]
    try:
        count = col.find({'work_id':src_id})[0]['count']
        col.update({'work_id':src_id}, {'$set':{'count': count+1}})
        return count+1

    except IndexError:
        return 0

def get_stash(host, src_id):

    client = pymongo.MongoClient(host, MONGO_PORT)
    col = client[MONGO_DB_NAME][MONGO_COL_NAME]
    try:
        vis = col.find({'work_id':src_id})[0]['stash']
        return vis
    except IndexError:
        return []

def set_stash(host, src_id, new):

    client = pymongo.MongoClient(host, MONGO_PORT)
    col = client[MONGO_DB_NAME][MONGO_COL_NAME]
    vis = col.find({'work_id':src_id})[0]['stash']
    col.update({'work_id':src_id}, { '$set': {'stash': new} })

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

#description of the maps variable:
#the label's index in the array at each key is used as the id for the label in the matrix
#i.e. 'AZ' is assigned at index 10, therefore the matrix will contain '10' for
#every instance of 'AZ' in the original data
#if the labels are repetitive, there will be fewer values in 'indexToLabel' than 'values'

#add a new field to the maps input (used for csv loading)
def addField(maps, key, values, type):
    #if data is of string type, convert to ids
    if type == 'String':
        maps[key] = {}
        maps[key]['indexToLabel'] = list(set(values))
        maps[key]['values'] = [maps[key]['indexToLabel'].index(x) + 1 for x in values]
    #just add the values directly do the array
    else:
        maps[key] = [str(x) for x in values]

#update field to the maps input (used for csv loading)
def updateField(maps, key, values, type, storepath):

    if type == 'String':
        with open(storepath + key + '.txt') as features:
            fieldvalues = features.read().split("\n")
            fieldvalues.pop()

        maps[key] = {}
        maps[key]['indexToLabel'] = list(set(values))
        for value in maps[key]['indexToLabel']:
            if value in fieldvalues:
                maps[key]['indexToLabel'].remove(value)
        fieldvalues.extend(maps[key]['indexToLabel'])
        maps[key]['values'] = [fieldvalues.index(x) + 1 for x in values]
    #just add the values directly do the array
    else:
        maps[key] = [str(x) for x in values]

#any fields that were added in the filtering processes are added to maps
def updateAdditions(maps, additions, matrixFeatures, storepath):
    if len(additions) > 0:
        for addition in additions:
            updateField(maps, addition['key'], addition['values'], addition['type'], storepath)
            matrixFeatures.append(addition['key'])


#any fields that were added in the filtering processes are added to maps
def processAdditions(maps, additions, matrixFeatures):
    if len(additions) > 0:
        for addition in additions:
            addField(maps, addition['key'], addition['values'], addition['type'])
            matrixFeatures.append(addition['key'])

#write the data at the specified roopath with the specified filename
def writeOutput(rootpath, fileName, outputData):
    with open(rootpath + fileName + '.txt', 'w') as featuresFile:
        for element in outputData:
            featuresFile.write(str(element) + '\n')

#write the data at the specified roopath with the specified filename
def appendOutput(rootpath, fileName, outputData):
    with open(rootpath + fileName + '.txt', 'a') as featuresFile:
        for element in outputData:
            featuresFile.write(str(element) + '\n')



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
        os.makedirs(rootpath, 0775)

    #write output files
    toWrite = []
    #list of features to write to the output features.txt file
    features = []
    featuresOrig = []
    outputs = []

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
            outputs.append(each + '.txt')
            writeOutput(rootpath, each, maps[each]['indexToLabel'])
        if matrixFeaturesOriginal[i] != '_id': #don't do this for mongoids
            features.append(each)
            featuresOrig.append(matrixFeaturesOriginal[i])


    #write out the list of features
    outputs.extend(['features_original.txt', 'features.txt'])
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
    outputs.append('matrix.csv')

    if return_data:
        return toReturn
    else:
        return outputs

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

