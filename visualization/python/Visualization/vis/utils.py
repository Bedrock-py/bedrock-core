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