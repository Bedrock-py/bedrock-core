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

import argparse, multiprocessing, uuid, datetime

def getNewId():
    return uuid.uuid4().hex

def getCurrentTime():
    return str(datetime.datetime.now())


def initialize(work, options):
    #options can be specific and unique for each workflow
    for each in options:
        setattr(work, each['attrname'], each['value'])

def get_metadata(workflow_id):
    exec("import work." + workflow_id)
    filename = "work." + workflow_id
    classname = filename.split(".")[-1]
    objectname = "work." + workflow_id + '.' + classname
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