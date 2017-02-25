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

import numpy as np
import pandas as pd
import uuid
from scipy.io import mmread
from scipy.sparse import csc_matrix
from bedrock.core.utils import get_class

def get_new_id():
    return uuid.uuid4().hex

def load_assignments(assign_filepath):
    return np.genfromtxt(assign_filepath, delimiter=',')

def load_features(features_filepath):
    with open(features_filepath) as features:
        features_loaded = features.read().split("\n")
        features_loaded.pop()
    return features_loaded

def load_dense_matrix(filepath, **kwargs):
    if 'names' in kwargs:
        return pd.read_csv(filepath, names=kwargs['names'])
    else:
        matrix = pd.DataFrame.from_csv(filepath, header=None, index_col=None)
        features = ['Feature ' + str(x + 1) for x in list(matrix.columns)]
        matrix.columns = features
        return matrix

def load_json(filepath):
    with open(filepath) as res:
        return res.read()

def load_sparse_matrix(filepath):
    return csc_matrix(mmread(filepath))


def initialize(vis, options):
    #options can be specific and unique for each vis
    for each in options:
        setattr(vis, each['attrname'], each['value'])

def get_metadata(vis_id):
    vis = get_class(vis_id)

    metadata = {}
    metadata['name'] = vis.get_name()
    metadata['classname'] = vis_id.split('.')[-1]
    metadata['description'] = vis.get_description()
    metadata['parameters'] = vis.get_parameters_spec()
    metadata['inputs'] = vis.get_inputs()
    return metadata

def generate_vis(vis_id, inputs, parameters):
    vis = get_class(vis_id)
    vis.initialize(inputs)
    print 'PARAMS',parameters
    initialize(vis, parameters)

    # if vis.check_parameters():
    return vis.create()
    # else:
        # return {}


class Visualization(object):
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

    def initialize(self, inputs):
        # this is for loading in data from filepaths provided by the UI
        pass
