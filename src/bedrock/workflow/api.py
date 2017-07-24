#****************************************************************
#  File: AnalyticsAPIv01.py
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

import json
import os
import re
from os.path import splitext
import shutil
import socket
import string
import subprocess
import sys
import traceback
from datetime import datetime
from multiprocessing import Process, Queue

import pymongo
from pymongo import MongoClient
from flask import (Flask, Response, abort, g, jsonify, redirect, request,
                   send_from_directory, stream_with_context, url_for)
import flask_restful as restful
from flask_restplus import Api, Resource, fields
from werkzeug import secure_filename
import logging

import utils
from bedrock.CONSTANTS import MONGO_HOST, MONGO_PORT, ANALYTICS_DB_NAME, ANALYTICS_COL_NAME, ANALYTICS_OPALS
from bedrock.core.db import drop_id_key
from bedrock.CONSTANTS import RESULTS_COL_NAME, RESULTS_PATH
from bedrock.core.exceptions import asserttype, InvalidUsage

ALLOWED_EXTENSIONS = ['py']

app = Flask(__name__)
app.debug = True

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

api = Api(
    app,
    version="0.2",
    title="Workflow API",
    description="Workflow-Framework API supporting creation and execution of workflows"
)

ns_a = api.namespace('workflows')
ns_r = api.namespace('experiments')



@app.teardown_appcontext
def teardown_db(exception):
    """closes the database connection"""
    db = getattr(g, '_mongodb', None)
    if db is not None:
        db.close()
###################################################################################################

@ns_a.route('/<id>')
def get(id):
    return "You asked for %s"%id
