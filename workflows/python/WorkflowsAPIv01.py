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

from flask import Flask, jsonify, request, redirect, url_for
import requests
from flask import stream_with_context, request, Response
import pymongo, sys, json, os, socket, shutil, string, re
from flask.ext import restful
from flask.ext.restplus import Api, Resource, fields
from Workflows import workflows

DIRPATH = '/var/www/analytics-framework/dataloader/data/'
RESPATH = '/var/www/analytics-framework/analytics/data/'
WORKPATH = '/var/www/analytics-framework/workflows/data/'
ALGDIR = '/var/www/analytics-framework/analytics/python/Analytics/algorithms/'
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_DB_NAME = 'visualization'
ALLOWED_EXTENSIONS = ['py']
ANALYTCS_API = 'http://10.90.23.200:81/analytics/api/0.1/'
DATALOADER_API = 'http://10.90.23.200:81/dataloader/api/0.1/'
VIS = 'visualizations'
MONGO_WORK_NAME = 'workflows'
COL = 'registered'
COL_MOD = 'modules'



app = Flask(__name__)
app.debug = True

api = Api(app, version="0.1", title="Workflows API", 
    description="Analytics-Framework API supporting workflows (Copyright &copy 2015, Georgia Tech Research Institute)")

ns = api.namespace('workflows')
ns_m = api.namespace('workflow_modules')


@ns_m.route('/')
class WorkflowModules(Resource):
    def get(self):
        '''
        Returns a list of all workflow modules.
        '''        
        workflows_registered = []

        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        col = client[MONGO_WORK_NAME][COL_MOD]
        cur = col.find()
        for c in cur:
            response = {key: value for key, value in c.items() if key != '_id'}
            workflows_registered.append(response)

        return workflows_registered


@ns.route('/')
class Workflows(Resource):
    def get(self):
        '''
        Returns a list of all workflows and their statuses.
        '''        
        workflows_registered = []

        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        col = client[MONGO_WORK_NAME][COL]
        cur = col.find()
        for c in cur:
            response = {key: value for key, value in c.items() if key != '_id' and key != 'stash'}
            workflows_registered.append(response)
        # from bson.json_util import dumps

        # return dumps(workflows_registered)
        return workflows_registered

    def post(self):
        '''
        Creates a new workflow.
        '''        
        work_id = workflows.getNewId()
        t = workflows.getCurrentTime()
        data = request.get_json()

        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        col = client[MONGO_WORK_NAME][COL]
        
        rootpath = WORKPATH  + work_id + '/'

        workflow = {}
        workflow['name'] = data['name']
        workflow['host'] = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][-1]
        workflow['parameters'] = data['parameters']
        workflow['rootdir'] = rootpath
        workflow['work_id'] = work_id
        workflow['created'] = t
        workflow['workflow_id'] = data['workflow_id']
        workflow['status'] = None
        workflow['count'] = 0
        workflow['stash'] = []

        col.insert(workflow)

        response = {key: value for key, value in workflow.items() if key != '_id'}

        return response, 201

@ns.route('/<work_id>/')
class Workflow(Resource):
    def post(self, work_id):
        '''
        Start or stop the specified workflow

        '''
        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        col = client[MONGO_WORK_NAME][COL]
        try:
            work = col.find({'work_id':work_id})[0]

        except IndexError:
            return 'No resource at that URL.', 404

        return workflows.toil(work['workflow_id'], work['parameters'], WORKPATH + work_id + '/')

    def patch(self, work_id):
        '''
        Update the status of the workflow.

        '''
        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        col = client[MONGO_WORK_NAME][COL]
        try:
            work = col.find({'work_id':work_id})[0]

        except IndexError:
            return 'No resource at that URL.', 404

        workflows.update(work['workflow_id'], WORKPATH + work_id + '/')

    def get(self, work_id):
        '''
        Returns the details of that workflow.
        '''         
        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        col = client[MONGO_WORK_NAME][COL]
        try:
            work = col.find({'work_id':work_id})[0]

        except IndexError:
            return 'No resource at that URL.', 404

        return {key: value for key, value in work.items() if key != '_id' and key != 'stash'}

    def delete(self, work_id):
        '''
        Deletes specified workflow.
        This will permanently remove this workflow from the system. USE CAREFULLY!
        '''
        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        col = client[MONGO_WORK_NAME][COL]

        try:
            col.remove({'work_id':work_id})

        except IndexError:
            return 'No resource at that URL.', 404
        try:
            shutil.rmtree(WORKPATH + work_id)
        except OSError:
            pass

        return '', 204



