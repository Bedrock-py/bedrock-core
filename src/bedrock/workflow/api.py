#****************************************************************
#  File: AnalyticsAPIv01.py
#
# Copyright (c) 2015, Georgia Tech Research Institute
# All rights reserved.
#
# This unpublished material is the property of the Georgia Tech
# Research Institute and is protected under copyright law.
# The methods and techniques described herein are considered
# trade secrets and/or confidential. Reprod*********************************************/
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
from bson.objectid import ObjectId
from bson.json_util import dumps
from flask import (Flask, Response, abort, g, jsonify, redirect, request,
                   send_from_directory, stream_with_context, url_for)
import flask_restful as restful
from flask_restplus import Api, Resource, fields
from werkzeug import secure_filename
import logging

import utils
from bedrock.CONSTANTS import MONGO_HOST, MONGO_PORT, ANALYTICS_DB_NAME, ANALYTICS_COL_NAME, ANALYTICS_OPALS
from bedrock.core.db import drop_id_key, db_client
from bedrock.CONSTANTS import RESULTS_COL_NAME, RESULTS_PATH
from bedrock.core.exceptions import asserttype, InvalidUsage
import bedrock.client.workflow as flow

flowdb = 'flows'
flowcol = 'flows'
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


@app.teardown_appcontext
def teardown_db(exception):
    """closes the database connection"""
    db = getattr(g, '_mongodb', None)
    if db is not None:
        db.close()
###################################################################################################

@api.route('/<uid>')
class Flow(Resource):
    """The main endpoint for the url service"""
    def get(self, uid):
        print('flow called')
        resp = {'method':request.method, 'mesg':'','uid':uid}
        client = db_client()[flowdb][flowcol]
        try:
            resp['workflow'] = drop_id_key(client.find({'_id':ObjectId(uid)})[0])
        except IndexError:
            return 'No such object %s'%uid, 404
        if request.method == 'DELETE':
            resp['mesg'] = 'Removing %s'%uid
        resp['mesg'] = "You asked for %s" % uid
        return resp
    def put(self, uid):
        resp = {'method':request.method, 'mesg':'','uid':uid}
        client = db_client()
        body = request.get_json()
        res = client.flows.flows.insert_one(body)
        if request.method == 'POST':
            resp['mesg'] ='You told me to post %s'%uid
            data = request.get_json()
        return str(res.inserted_id)
