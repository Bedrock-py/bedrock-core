#****************************************************************
#  File: visualization.py
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

import argparse

MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB_NAME = 'dataloader'
VIS = 'visualizations'

def initialize(vis, options):
    #options can be specific and unique for each vis
    for each in options:
        setattr(vis, each['attrname'], each['value'])

def get_metadata(vis_id):
    exec("import vis." + vis_id)
    filename = "vis." + vis_id
    classname = filename.split(".")[-1]
    objectname = "vis." + vis_id + '.' + classname
    vis = eval(objectname)() #create the object specified

    metadata = {}
    metadata['name'] = vis.get_name()
    metadata['classname'] = classname
    metadata['description'] = vis.get_description()
    metadata['parameters'] = vis.get_parameters_spec()
    metadata['inputs'] = vis.get_inputs()
    return metadata

def generate_vis(vis_id, inputs, parameters):
    exec("import vis." + vis_id)
    filename = "vis." + vis_id
    classname = filename.split(".")[-1]
    objectname = "vis." + vis_id + '.' + classname
    vis = eval(objectname)() 
    vis.initialize(inputs)
    print 'PARAMS',parameters
    initialize(vis, parameters)

    # if vis.check_parameters():
    return vis.create()
    # else:
        # return {}


class VisBase(object):
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

        
if __name__=='__main__':

    parser = argparse.ArgumentParser(description="Manually add new vis to system")
    parser.add_argument('--filename', action='store', required=True, metavar='filename')
    parser.add_argument('--classname', action='store', required=True, metavar='classname')
    args = parser.parse_args()

    vis_id = args.filename.split('.')[0]
    metadata = get_metadata(vis_id, args.classname)
    metadata['vis_id'] = vis_id

    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    col = client[MONGO_DB_NAME][VIS]

    col.insert(metadata)
    meta = {key: value for key, value in metadata.items() if key != '_id'}

    print {'vis': meta}

