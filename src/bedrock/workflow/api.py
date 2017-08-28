
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
from bedrock.core.db import drop_id_key, serialize_id_key, db_client
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

def newresp(req, uid):
    """Creates a new json for the response body that you can add to."""
    resp = {'method':req.method, 'mesg':'', 'uid':uid}
    return resp

@api.route('/<uid>')
class Flow(Resource):
    """The main endpoint for the url service"""
    def get(self, uid):
        """
        Get a workflow from the backing database (mongo), special uid=='all' returns
        the whole list. the workflow will be stored in the response as a json at the key workflow.
        If you ask for 'all' then there will be a field 'workflows' containing an array of workflows.
        """
        print('flow called')
        client = db_client()[flowdb][flowcol]
        resp = newresp(request, uid)
        if uid == 'all':
            try:
                resp['workflows'] = map(serialize_id_key, client.find())
            except Exception as ex:
                print(ex)
                return "failed builk read to mongo", 500
        else:
            try:
                resp['workflow'] = serialize_id_key(client.find({'_id':ObjectId(uid)})[0])
            except IndexError:
                return 'No such object %s'%uid, 404
        resp['mesg'] = "You asked for %s" % uid
        return resp
    def post(self, uid):
        """Store a new workflow in the database. returns the uid which is the mongo objectid"""
        resp = newresp(request, uid)
        client = db_client()
        body = request.get_json()
        try:
            res = client.flows.flows.insert_one(body)
            resp['mesg'] = 'Succesfully inserted workflow'
            resp['_id'] = str(res.inserted_id)
            return resp, 201
        except Exception as ex:
            resp['mesg'] = 'Could not create workflow %s:\n %s'%(uid, ex)
            return resp, 500
        return resp, 201
    def delete(self, uid):
        resp = newresp(request, uid)
        client = db_client()
        body = request.get_json()
        resp['mesg'] = 'Removing %s'%uid
        try:
            res = client.flows.flows.remove({'_id': ObjectId(uid)})
            print(res)
        except Exception as ex:
            print("exception in deletion of workflow:\n", ex)
            resp['error'] = "failed to delete %s\n%s" % (uid, ex )
            return resp, 500
        return resp, 200
        

