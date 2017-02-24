#****************************************************************
#  File: VisualizationAPIv01.py
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
import flask_restful as restful
from flask_restplus import Api, Resource, fields
import utils

from bedrock.CONSTANTS import VIS_COL_NAME, VIS_DB_NAME, DATALOADER_PATH
from bedrock.core.db import db_client, db_collection, find_matrix
from bedrock.core.io import write_source_file, write_source_config
from bedrock.core.models import Source, SourceCreated

app = Flask(__name__)
app.debug = True

api = Api(app, version="0.1", title="Visualization API",
    description="Analytics-Framework API supporting visualization of data (Copyright &copy 2015, Georgia Tech Research Institute)")

ns = api.namespace('visualization')

###################################################################################################


@api.model(fields={
                'outputs': fields.List(fields.String, description='List of output files associated with the dataset or result', required=True),
                'rootdir': fields.String(description='Path to the associated directory', required=True),
                })
class Input(fields.Raw):
    def format(self, value):
        return {
                'outputs': value.outputs,
                'rootdir': value.rootdir
                }

@api.model(fields={
                'attrname': fields.String(description='Python variable name', required=True),
                'max': fields.Float(description='Max value to allow for input'),
                'min': fields.Float(description='Min value to allow for input'),
                'name': fields.String(description='Name to use for display', required=True),
                'step': fields.Float(description='Step to use for numeric values'),
                'type': fields.String(description='Kind of html input type to display', required=True),
                'value': fields.String(description='Default value to use', required=True),
                })
class VisParams(fields.Raw):
    def format(self, value):
        return {
                'attrname': value.attrname,
                'max': value.max,
                'min': value.min,
                'name': value.name,
                'step': value.step,
                'type': value.type,
                'value': value.value,
                }



@api.model(fields={
                'vis_id': fields.String(description='Unique ID for the visualization', required=True),
                'name': fields.String(description='Result name'),
                'parameters': fields.List(VisParams, description='List of input parameters used by the visualization'),
                'inputs': fields.List(fields.String, description='List of input files required for this visualization', required=True),
                'classname': fields.String(description='Classname within the source file assocaited with this visualization', required=True),
                'description': fields.String(description='Description for this visualization'),
                })
class VisSpec(fields.Raw):
    def format(self, value):
        return {
                'vis_id': value.vis_id,
                'name': value.name,
                'parameters': value.parameters,
                'inputs': value.inputs,
                'classname': value.classname,
                'description': value.description
                }


api.model('Vis', {
    'data': fields.String(description='Json-encded set of data OR html script tag with the generated visualization', required=True),
    'id': fields.String(description='Unique ID for this visualization', required=True),
    'type': fields.String(description='Type of visualization (used for handling in the UI)', required=True),
})


###################################################################################################

@ns.route('/')
class Options(Resource):
    @api.doc(body='Input', model='VisSpec', params={'payload':
            '''Must be a list of the model described to the right. Try this:
            [{
              "outputs": [
                "matrix.csv",
                "assignments.csv"]
            }]
            '''})
    def post(self):
        '''
        Returns a list of applicable available visualizations.
        Not all visualizations are applicable for every dataset. This request requires a list of inputs and will return the visualizations options available based on those inputs.
        '''
        data = request.get_json()

        vis_options = []

        client = db_client()
        col = db_collection(client, VIS_DB_NAME, VIS_COL_NAME)
        cur = col.find()
        if len(data) != 1:
            outputsPersist = []
            for res in data:
                outputsPersist.extend(res['outputs'])
        else:
            outputsPersist = data[0]['outputs']

        if 'selected_features' in data[0]:
            outputsPersist.append('selected_features')

        outputsPersist.append('names')

        for vis in cur:
            print vis
            contains = False
            outputs = outputsPersist[:]
            for i in vis['inputs']:
                if i in outputs:
                    contains = True
                    outputs.pop(outputs.index(i))
                else:
                    contains = False
                    break
            if contains:
                response = {key: value for key, value in vis.items() if key != '_id'}
                vis_options.append(response)

        return vis_options

    @api.doc(model='VisSpec')
    def get(self):
        '''
        Returns a list of all available visualizations.
        All visualizations registered in the system will be returned. If you believe there is a visualization that exists in the system but is not present here, it is probably not registered in the MongoDB database.
        '''
        vis_options = []

        client = db_client()
        col = db_collection(client, VIS_DB_NAME, VIS_COL_NAME)
        cur = col.find()
        for c in cur:
            response = {key: value for key, value in c.items() if key != '_id'}
            vis_options.append(response)

        return vis_options

@ns.route('/<vis_id>/')
class Vis(Resource):
    @api.doc(body='Input', model='Vis')
    def post(self, vis_id):
        '''
        Creates the specified visualization and returns the data necessary to render it.

        '''
        data = request.get_json()
        parameters = data['parameters']
        inputs = data['inputs']
        return utils.generate_vis(vis_id, inputs, parameters)
