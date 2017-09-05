
from __future__ import print_function

import csv
from datetime import datetime
from importlib import import_module
import os
import uuid
from bedrock.CONSTANTS import MONGO_HOST, MONGO_PORT, ANALYTICS_COL_NAME, ANALYTICS_DB_NAME, ANALYTICS_OPALS
from bedrock.core.utils import get_class
import numpy as np
import pandas as pd
import pymongo
import logging
import traceback


def getNewId():
    return uuid.uuid4().hex


def getCurrentTime():
    return str(datetime.now())

def setUpDirectory():
    """get a unique folder name and create the folder, return the filepath"""
    dirName = getNewId()
    # dirName = datetime.now().strftime("%Y%m%d%H%M%S%f")
    rootpath = os.path.join(DIRPATH, dirName)
    os.makedirs(rootpath)
    return DIRPATH, dirName


def setUpDirectoryMatrix(src_id):
    dirName = getNewId()
    # dirName = datetime.now().strftime("%Y%m%d%H%M%S%f")
    rootpath = os.path.join(DIRPATH, src_id, dirName)
    os.makedirs(rootpath)
    return rootpath, dirName


def loadMatrix(filepath):
    """
    use pandas to load the csv file into the dataframe,
    using a header if appropriate
    """
    with open(filepath, 'rbU') as csvfile:
        snippet = csvfile.read(2048)
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(snippet)
    if sniffer.has_header(snippet):
        df = pd.read_csv(filepath, dialect=dialect)
    else:
        df = pd.read_csv(filepath, dialect=dialect, header=None)

    return df


def writeFiles(maps,
               matrixFeatures,
               matrixFeaturesOriginal,
               rootpath,
               return_data=False):
    """
    write the output files associated with each loaded file
    matrix.csv, features.txt, features_original.txt, and any non-numeric fields' mappings
    """
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
                pass    #ignore, since this is the mongoids field and has no values
            #write the features to output
            writeOutput(rootpath, each, maps[each]['indexToLabel'])
        if matrixFeaturesOriginal[i] != '_id':    #don't do this for mongoids
            features.append(each)
            featuresOrig.append(matrixFeaturesOriginal[i])

    #write out the list of features
    writeOutput(rootpath, 'features_original', featuresOrig)
    writeOutput(rootpath, 'features', features)

    toReturn = []
    #convert lists to numpy arrays
    #matrix is documents x features (i.e. rows = individual items and columns = features)
    with open(os.path.join(rootpath, 'matrix.csv'), 'w') as matrix:
        for i in range(len(toWrite[0])):
            temp = []
            for each in toWrite:
                temp.append(each[i])
                if return_data:
                    toReturn.append(temp)
            matrix.write(','.join(temp) + '\n')

    if return_data:
        return toReturn


def updateFiles(maps,
                matrixFeatures,
                matrixFeaturesOriginal,
                rootpath,
                return_data=False):

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
                pass    #ignore, since this is the mongoids field and has no values
            #write the features to output
            appendOutput(rootpath, each, maps[each]['indexToLabel'])

    toReturn = []
    #convert lists to numpy arrays
    #matrix is documents x features (i.e. rows = individual items and columns = features)
    with open(os.path.join(rootpath, 'matrix.csv'), 'a') as matrix:
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
    alg = get_class(analytic_id)
    metadata = {}
    metadata['name'] = alg.get_name()
    metadata['classname'] = analytic_id.split('.')[-1]
    metadata['description'] = alg.get_description()
    metadata['parameters'] = alg.get_parameters_spec()
    metadata['inputs'] = alg.get_inputs()
    metadata['outputs'] = alg.get_outputs()
    metadata['type'] = alg.get_type()
    return metadata


def run_analysis(queue, analytic_id, parameters, inputs, storepath, name):
    alg = get_class(analytic_id)
    initialize(alg, parameters)
    if alg.check_parameters():
        try:
            alg.compute(inputs, storepath=storepath, name=name)
        except:
            tb = traceback.format_exc()
            logging.error("Error running compute for analytics")
            logging.error(tb)
            queue.put(None)
        alg.write_results(storepath)
        print(analytic_id.split('.')[-1] + ' successful')
        # return alg.get_outputs()
        queue.put(alg.get_outputs())
    else:
        logging.error("Check Parameters failed")
        queue.put(None)


def classify(analytic_id, parameters, inputs):
    alg = get_class(analytic_id)
    initialize(alg, parameters)
    if alg.check_parameters():
        return list(alg.classify(inputs))
    else:
        return []


#runs simple dense matrix test
def test_analysis(analytic_id, filepath, storepath):
    '''test_analysis: run the analytics on the matrix stored at filepath and put results in storepath.
    returns True if the analytic does not raise an exception when compute or write_results is called.
    returns False if either fails'''
    alg = get_class(analytic_id)
    initialize(alg, alg.parameters_spec)

    if alg.check_parameters():
        try:
            alg.compute(filepath, storepath=storepath)
            alg.write_results(storepath)
        except:
            print("Running Analytic %s failed on file %s storepath=%s".format(
                analytic_id, filepath, storepath))
            return False
        else:
            return True
    else:
        return False

# BROKEN: WONTFIX
def write_analytic(text, classname):
    time = datetime.now()
    analytic_id = classname
    # + str(time.year) + str(time.month) + str(time.day) + str(time.hour) + str(time.minute) + str(time.second)

    with open(ANALYTICS_OPALS + analytic_id + '.py', 'w') as alg:
        alg.write(text)

    #get the metadata from the file
    metadata = get_metadata(analytic_id)
    metadata['analytic_id'] = analytic_id

    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    col = client[ANALYTICS_DB_NAME][ANALYTICS_COL_NAME]

    col.insert(metadata)


class Algorithm(object):
    def __init__(self):
        self.results = {}

    def check_parameters(self):
        #check to make sure inputs are set
        try:
            for each in self.parameters:
                getattr(self,each)
            return True
        except AttributeError:
            logging.error('Necessary attribute(s) not initialized')
            return False

    def write_results(self, storepath):
        for key, res in self.results.items():
            self.write_output(storepath, key, res)

    def write_output(self, rootpath, key, outputData):
        filepath = rootpath + '/' + key

        with open(filepath, 'w') as featuresFile:
            if key.endswith('.json'):
                featuresFile.write(outputData)
            elif key.endswith('.txt'):
                if (key == 'summary.txt') | (key == 'prior_summary.txt'):
                    featuresFile.write(outputData)
                else:
                    line = '\n'.join([str(x) for x in outputData]) + '\n'
                    featuresFile.write(line)
            elif 'analytic' in key:
                write_analytic(outputData['text'], outputData['classname'])
            else:
                #check if each element is a single element or list
                if len(outputData) == 0:
                    return
                try:
                    len(outputData[0])
                except TypeError:
                    if key.endswith('.csv'):
                        line = ','.join(['"' + str(x) + '"' for x in outputData])
                        featuresFile.write(line)
                    elif key.endswith('.txt'):
                        assert (len(outputData[0] == 1))
                        line = '\n'.join([str(x) for x in outputData])
                        featuresFile.write(line)
                else:
                    #list
                    if key.endswith('.csv'):
                        for element in outputData:
                            line = ','.join(['"' + str(x) + '"' for x in element])
                            featuresFile.write(line + '\n')
                    elif key.endswith('.json'):
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

    def compute(self):
        pass
