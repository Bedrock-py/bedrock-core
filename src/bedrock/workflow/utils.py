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
from __future__ import print_function

import csv
from datetime import datetime
from importlib import import_module
import os
import uuid
from bedrock.CONSTANTS import MONGO_HOST, MONGO_PORT, ANALYTICS_COL_NAME, ANALYTICS_DB_NAME, ANALYTICS_OPALS
from bedrock.core.utils import get_class
# import numpy as np
# import pandas as pd
# import pymongo
# import logging
# import traceback


def getNewId():
    """makes a uuid"""
    return uuid.uuid4().hex


def getCurrentTime():
    """gets the current time as a string"""
    return str(datetime.now())


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
