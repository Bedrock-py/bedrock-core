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
from werkzeug.utils import secure_filename
import logging

from . import utils
from bedrock.CONSTANTS import MONGO_HOST, MONGO_PORT, ANALYTICS_DB_NAME, ANALYTICS_COL_NAME, ANALYTICS_OPALS, \
    DATALOADER_DB_NAME, DATALOADER_COL_NAME
from bedrock.core.db import drop_id_key, db_client, db_collection, find_source
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
    title="Analytics API",
    description="Analytics-Framework API supporting creation and use of analytics"
)

ns_a = api.namespace('analytics')
ns_r = api.namespace('results')


def analytics_oftype(typename):
    '''analytics_oftype(typename): returns a list of analytics where the type is typename

    allows clients to find analytics matching a specific type. Options include Clustering, DimensionReduction, Classification

    usage: analytics_oftype('Clustering')
    '''
    _, col = analytics_collection()
    analytics = col.find({"type": typename}, {"_id": 0})

    return list(analytics)


def published_model(src):
    """predicate for an analytic being a published model"""
    return src['type'] == 'Model' and 'published' in src and src['published']


def ismodel(src):
    """predict if the argument is a model"""
    return src['type'] == 'Model'


def analytics_list(col):
    """gets the list of analytics including published models"""
    cur = col.find({}, {"_id": 0})
    return [src for src in cur
            if published_model(src) or src['type'] != 'Model']


def analytics_collection():
    """connect to the database if necessary and return the analytics collection"""
    db = getattr(g, '_mongodb', None)
    if db is None:
        db = g._mongodb = MongoClient(MONGO_HOST, MONGO_PORT)
    return db, db[ANALYTICS_DB_NAME][ANALYTICS_COL_NAME]


def results_collection():
    """connect to the database if necessary and return the analytics collection"""
    db = getattr(g, '_mongodb', None)
    if db is None:
        db = g._mongodb = MongoClient(MONGO_HOST, MONGO_PORT)
    return db, db[ANALYTICS_DB_NAME][RESULTS_COL_NAME]


def get_results_source(src_id):
    _, col = results_collection()
    res = col.find_one({'src_id': src_id}, {"_id": 0})
    if not res:
        res = col.find_one({'src.name': src_id}, {"_id": 0})

    return res


@app.teardown_appcontext
def teardown_db(exception):
    """closes the database connection"""
    db = getattr(g, '_mongodb', None)
    if db is not None:
        db.close()


###################################################################################################


@api.model(fields={
    'created': fields.String(description='Timestamp of creation'),
    'id': fields.String(
        description='Unique ID for the matrix', required=True),
    'src_id': fields.String(
        description='Unique ID for the source used to generate the matrix',
        required=True),
    'mat_type': fields.String(description='Matrix type'),
    'name': fields.String(description='Matrix name'),
    'outputs': fields.List(
        fields.String,
        description='List of output files associated with the matrix',
        required=True),
    'rootdir': fields.String(
        description='Path to the associated directory', required=True),
})
class Matrix(fields.Raw):
    def format(self, value):
        return {
            'created': value.created,
            'id': value.id,
            'src_id': value.src_id,
            'mat_type': value.mat_type,
            'name': value.name,
            'outputs': value.outputs,
            'rootdir': value.rootdir
        }


@api.model(fields={
    'attrname': fields.String(
        description='Python variable name', required=True),
    'max': fields.Float(description='Max value to allow for input'),
    'min': fields.Float(description='Min value to allow for input'),
    'name': fields.String(
        description='Name to use for display', required=True),
    'step': fields.Float(description='Step to use for numeric values'),
    'type': fields.String(
        description='Kind of html input type to display', required=True),
    'value': fields.String(
        description='Default value to use', required=True),
})
class AnalyticParams(fields.Raw):
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


api.model(
    'Analytic', {
        'analytic_id': fields.String(
            description='Unique ID for the analytic', required=True),
        'classname': fields.String(
            description='Classname within the python file', required=True),
        'description':
            fields.String(description='Description for the analytic'),
        'inputs': fields.List(
            fields.String,
            description='List of input files for the analytic',
            required=True),
        'name': fields.String(description='Analytic name'),
        'parameters': fields.List(
            AnalyticParams,
            description='List of input parameters needed by the analytic'),
        'outputs': fields.List(
            fields.String,
            description='List of output files generated by the analytic',
            required=True),
        'type': fields.String(
            description='Type of analytic: {Dimension Reduction, Clustering, Classification, Statistics}',
            required=True),
    })


@api.model(fields={
    'analytic_id': fields.String(
        description='Unique ID for the analytic used to generate the result',
        required=True),
    'created': fields.String(description='Timestamp of creation'),
    'id': fields.String(
        description='Unique ID for the result', required=True),
    'name': fields.String(description='Result name'),
    'parameters': fields.List(
        AnalyticParams,
        description='List of input parameters used by the analytic'),
    'outputs': fields.List(
        fields.String,
        description='List of output files associated with that result',
        required=True),
    'rootdir': fields.String(
        description='Path to the associated directory', required=True),
    'src_id': fields.String(
        description='Unique ID for the matrix used to generate the result',
        required=True),
})
class Result(fields.Raw):
    def format(self, value):
        return {
            'analytic_id': value.analytic_id,
            'created': value.created,
            'id': value.id,
            'name': value.name,
            'parameters': value.parameters,
            'outputs': value.outputs,
            'rootdir': value.rootdir,
            'src_id': value.src_id
        }


api.model(
    'Results', {
        'results': fields.List(
            Result,
            description='List of results for this particular matrix',
            required=True),
        'rootdir': fields.String(
            description='Path to the associated directory', required=True),
        'src':
            Matrix(description='Matrix from which these results were generated'),
        'src_id': fields.String(
            description='Unique ID for the matrix', required=True),
    })


###################################################################################################


@ns_a.route('/')
class Analytics(Resource):
    @api.doc(model='Analytic')
    def get(self):
        '''
        Returns a list of available analytics.
        All analytics registered in the system will be returned.

        If you believe there is an analytic that exists in the system but is not present here, it is probably not registered in the MongoDB database.
        '''
        _, col = analytics_collection()
        analytics = analytics_list(col)
        return analytics

    @api.hide
    @api.doc(responses={201: 'Success', 415: 'Unsupported filetype'})
    def put(self):
        '''
        Add a new analytic via file upload. This is a security risk.
        '''
        try:
            time = datetime.now()
            # make the id more meaningful
            file = request.files['file']
            filename = secure_filename(file.filename)
            name, ext = splitext(filename)
            if not ext in ALLOWED_EXTENSIONS:
                return 'This filetype is not supported.', 415

            # save the file
            analytic_id = name + str(time.year) + str(time.month) + str(
                time.day) + str(time.hour) + str(time.minute) + str(
                time.second)
            filepath = ANALYTICS_OPALS + analytic_id + '.py'
            file.save(filepath)

            # get the metadata from the file
            metadata = utils.get_metadata(analytic_id)
            metadata['analytic_id'] = analytic_id

            _, col = analytics_collection()
            col.insert(metadata)
            meta = drop_id_key(metadata)
        except:
            tb = traceback.format_exc()
            return tb, 406

        return meta, 201

    # @api.hide
    # @api.doc(responses={201: 'Success', 406: 'Error with analytic content'})
    # def post(self):
    #     '''
    #     Add a new analytic via form
    #     '''
    #     time = datetime.now()
    #     # make the id more meaningful
    #     data = request.get_json()

    #     #create a temp file
    #     time = datetime.now()
    #     analytic_id = data['classname'] + str(time.year) + str(time.month) + str(time.day) + str(time.hour) + str(time.minute) + str(time.second)

    #     with open(ANALYTICS_OPALS + analytic_id + '.py', 'w') as temp:
    #         temp.write('def get_classname():\n    return \'' + data['classname'] + '\'\n\n')
    #         temp.write(data['code'] + '\n\n')

    #     #test the alg with a dense matrix, show traceback, delete analytic file
    #     success = utils.test_analysis(analytic_id, TESTFILEPATH, TESTSTOREPATH)
    #     if not success:
    #             os.remove(ANALYTICS_OPALS + analytic_id + '.py')
    #             return 'Problem with provided algorithm', 406

    #     #save the file, delete results
    #     else:
    #         for i in os.listdir(TESTSTOREPATH):
    #             os.remove(TESTSTOREPATH + i)
    #         #get the metadata from the file
    #         metadata = utils.get_metadata(analytic_id)
    #         metadata['analytic_id'] = analytic_id

    #         _, col = analytics_collection()

    #         col.insert(metadata)
    #         meta = {key: value for key, value in metadata.items() if key != '_id'}

    #         return meta, 201

    #     return ''

    @ns_a.route('/options/')
    class Options(Resource):
        @api.doc(
            body='Matrix',
            params={
                'payload':
                    '''Must be a list of the model described to the right. Try this:
            [{
              "created": "string",
              "id": "string",
              "mat_type": "string",
              "name": "string",
              "outputs": [
                "matrix.csv"
              ],
              "rootdir": "string",
              "src_id": "string"
            }]
            '''
            })
        def post(self):
            '''
            Returns the applicable analytics.
            Not all analytics are applicable for every dataset.
            This request requires a list of inputs and will return the analytics options available based on those inputs.
            '''
            data = request.get_json()
            asserttype(data, list)

            _, col = analytics_collection()
            cur = col.find({}, {"_id": 0})
            analytics = []
            if len(data) != 1:
                outputsPersist = []
                for res in data:
                    outputsPersist.extend(res['outputs'])
            else:
                outputsPersist = data[0]['outputs']
            asserttype(outputsPersist, list)
            for src in cur:
                contains = False
                outputs = outputsPersist[:]
                for i in src['inputs']:
                    if i in outputs:
                        contains = True
                        outputs.remove(i)
                    else:
                        contains = False
                        break
                if contains:
                    response = src
                    if published_model(response) or response['type'] != 'Model':
                        analytics.append(response)
            return analytics

    @ns_a.route('/clustering/')
    class Clustering(Resource):
        @api.doc(model='Analytic')
        def get(self):
            '''
            Returns a list of available clustering analytics.
            All analytics registered in the system with a type of 'Clustering' will be returned. If you believe there is an analytic that exists in the system but is not present here, it is probably not registered in the MongoDB database.
            '''
            return analytics_oftype('Clustering')

    @ns_a.route('/classification/')
    class Classification(Resource):
        @api.doc(model='Analytic')
        def get(self):
            '''
            Returns a list of available classification analytics.
            All analytics registered in the system with a type of 'Classification' will be returned. If you believe there is an analytic that exists in the system but is not present here, it is probably not registered in the MongoDB database.
            '''
            return analytics_oftype('Classification')

    @ns_a.route('/dimred/')
    class DimensionReduction(Resource):
        @api.doc(model='Analytic')
        def get(self):
            '''
            Returns a list of available dimension reduction analytics.
            All analytics registered in the system with a type of 'Dimension Reduction' will be returned. If you believe there is an analytic that exists in the system but is not present here, it is probably not registered in the MongoDB database.
            '''
            return analytics_oftype('Dimension Reduction')

    @ns_a.route('/stats/')
    class Statistical(Resource):
        @api.doc(model='Analytic')
        def get(self):
            '''
            Returns a list of available statistical analytics.
            All analytics registered in the system with a type of 'Statistical' will be returned. If you believe there is an analytic that exists in the system but is not present here, it is probably not registered in the MongoDB database.
            '''
            return analytics_oftype('Statistical')

    @ns_a.route('/models/')
    class Models(Resource):
        @api.doc(model='Analytic')
        def get(self):
            '''
            Returns a list of available trained models.
            All analytics registered in the system with a type of 'Model' will be returned. If you believe there is an analytic that exists in the system but is not present here, it is probably not registered in the MongoDB database.
            '''
            _, col = analytics_collection()
            cur = col.find({}, {"_id": 0})
            return [src for src in cur if ismodel(src)]

    @ns_a.route('/models/published/')
    class Published(Resource):
        @api.doc(model='Analytic')
        def get(self):
            '''
            Returns a list of published models.
            '''
            _, col = analytics_collection()
            cur = col.find({}, {"_id": 0})
            return [src for src in cur if published_model(src)]

    @ns_a.route('/models/publish/<model_id>/<flag>/')
    class Publish(Resource):
        @api.doc(params={},
                 responses={
                     201: 'Success',
                     406: 'Error',
                     404: 'No resource at that URL'
                 })
        def post(self, model_id, flag):
            '''
            Publish/unpublish a model.
            This request is only applicable to analytics that are of type 'Model'.
            '''
            # get the analytic
            _, col = analytics_collection()
            try:
                analytic = col.find({'analytic_id': model_id})[0]
            except IndexError:
                return 'No resource at that URL.', 404

            # unpublish the model
            if flag == '0':
                result = col.update_one({
                    "analytic_id": analytic['analytic_id'],
                    "_id": analytic['_id']
                }, {'$set': {
                    "published": False
                }})
                if result:
                    return "Succesfully unpublished model " + model_id, 200

            # publish the model
            else:
                result = col.update_one({
                    "analytic_id": analytic['analytic_id'],
                    "_id": analytic['_id']
                }, {'$set': {
                    "published": True
                }})
                if result:
                    # still need to add appropriate host/IP
                    return "Analytic available from /analytics/models/" + analytic[
                        'analytic_id'] + '/', 200

            return "Bad Request", 400

    @ns_a.route('/models/<model_id>/')
    class Classify(Resource):
        @api.doc(
            params={'payload': 'Must be list of data to have classified.'},
            responses={
                201: 'Success',
                406: 'Error',
                404: 'No resource at that URL'
            })
        def post(self, model_id):
            '''
            Apply a published model to the provided input data and return the results.
            This request is only applicable to analytics that are of type 'Model' and have been published.
            '''
            # get the analytic
            _, col = analytics_collection()
            try:
                analytic = col.find({'analytic_id': model_id})[0]
            except IndexError:
                return 'No resource at that URL.', 404

            # make sure it is of type 'Model'
            if analytic['type'] != 'Model':
                return "This analytic is not of type 'Model'", 406

            if 'published' not in analytic or not analytic['published']:
                return "No resource at that URL", 404

            # get the input data
            print("hi25")
            data = request.get_json()
            print(data)
            parameters = data['parameters']
            inputs = data['inputs']
            result = utils.classify(model_id, parameters, inputs)
            return result, 200

    # @app.route('/analytics/<analytic_id>/', methods=['DELETE'])
    @ns_a.route('/<analytic_id>/')
    @api.doc(
        params={'analytic_id': 'The ID assigned to a particular analytic'})
    class Analytic(Resource):
        @api.doc(responses={
            204: 'Resource removed successfully',
            404: 'No resource at that URL'
        })
        def delete(self, analytic_id):
            '''
            Deletes specified analytic.
            This will permanently remove this analytic from the system. USE CAREFULLY!
            '''
            _, col = analytics_collection()
            try:
                analytic = col.find({'analytic_id': analytic_id})[0]

            except IndexError:
                return 'No resource at that URL.', 404

            else:
                col.remove({'analytic_id': analytic_id})
                os.remove(ANALYTICS_OPALS + analytic_id + '.py')

                return '', 204

        @api.doc(responses={200: 'Success', 404: 'No resource at that URL'})
        @api.doc(model='Analytic')
        def get(self, analytic_id):
            '''
            Returns the details of the specified analytic.
            '''
            _, col = analytics_collection()
            try:
                analytic = col.find({'analytic_id': analytic_id})[0]
            except IndexError:
                try:
                    analytic = col.find({'name': analytic_id})[0]
                except IndexError:
                    return 'No resource at that URL.', 404

            else:
                return {
                    key: value
                    for key, value in analytic.items() if key != '_id'
                }

        @api.doc(responses={201: 'Success', 406: 'Error'})
        @api.doc(params={
            'payload': 'Must be a list of the model defined to the right.'
        },
            body='Matrix')
        def post(self, analytic_id):
            '''
            Apply a certain analytic to the provided input data.
            The input must be a list of datasets, which can be matrices and/or results.

            '''
            # get the analytic
            _, col = analytics_collection()
            isResultSource = False

            # get the input data
            data = request.get_json(force=True)
            datasrc = data['src'][0]
            if isinstance(datasrc, list):
                msg = "When Posting Analytic %s, datasrc was a list" % (
                    analytic_id)
                print(msg)
                return msg, 400  # Bad Request
            else:
                print("Datasource is a <%s>" % type(datasrc))

            src_id = datasrc['src_id']
            sub_id = datasrc['id']
            parameters = data['parameters']
            inputs = data['inputs']
            name = data['name']
            res_id = utils.getNewId()
            # see if the input data is a result
            if 'analytic_id' in datasrc:
                isResultSource = True
                mat_id = datasrc['src_id']
            else:
                mat_id = sub_id
            storepath = os.path.join(RESULTS_PATH, mat_id, res_id) + "/"
            os.makedirs(storepath)

            # print("Extracted info for analytic:%s\n %s"%(analytic_id, {
            #     'src_id': src_id,
            #     'sub_id': sub_id,
            #     'parameters': parameters,
            #     'inputs': inputs,
            #     'name': name,
            #     'res_id': res_id
            # }))
            # run analysis
            queue = Queue()
            try:
                # single process for now
                utils.run_analysis(queue, analytic_id, parameters, inputs,
                                   storepath, name)

                # multiprocess solution from before
                # p = Process(target=utils.run_analysis, args=(queue, analytic_id, parameters, inputs, storepath, name))
                # p.start()
                # p.join() # this blocks until the process terminates
                outputs = queue.get()
            except:
                tb = traceback.format_exc()
                logging.error(tb)
                return tb, 406

            if outputs != None:
                # store metadata
                _, res_col = results_collection()
                try:
                    src = res_col.find({'src_id': mat_id})[0]
                except IndexError:
                    src = {}
                    src['rootdir'] = os.path.join(RESULTS_PATH, mat_id) + '/'
                    src['src'] = data['src'][0]
                    src['src_id'] = data['src'][0]['id']
                    src['results'] = []
                    res_col.insert(src)
                    src = res_col.find({'src_id': mat_id})[0]

                res = {}
                res['id'] = res_id
                res['rootdir'] = storepath
                res['name'] = name
                res['src_id'] = mat_id
                res['created'] = utils.getCurrentTime()
                res['analytic_id'] = analytic_id
                res['parameters'] = parameters
                res['outputs'] = outputs
                if isResultSource:
                    res['res_id'] = [el['id'] for el in data['src']]
                results = []
                for each in src['results']:
                    results.append(each)
                results.append(res)
                res_col.update({
                    'src_id': mat_id
                }, {'$set': {
                    'results': results
                }})

                return res, 201
            else:
                tb = traceback.format_exc()
                logging.error(tb)
                return tb, 406

        @api.doc(
            params={'payload': 'Must be list of data to have classified.'},
            responses={
                201: 'Success',
                406: 'Error',
                404: 'No resource at that URL'
            })
        def patch(self, analytic_id):
            '''
            Apply a certain analytic to the provided input data and return the classification label(s).
            This request is only applicable to analytics that are of type 'Classificaiton'.
            '''
            # get the analytic
            _, col = analytics_collection()
            try:
                analytic = col.find({'analytic_id': analytic_id})[0]
            except IndexError:
                return 'No resource at that URL.', 404

            classname = analytic['classname']
            alg_type = analytic['type']

            # make sure it is of type 'Classification'
            if alg_type == 'Classification':
                return "This analytic is not of type 'Classification'", 406

            # get the input data
            data = request.get_json()
            parameters = data['parameters']
            inputs = data['inputs']
            result = analytic.classify(analytic_id, parameters, inputs)
            return result, 200

    @ns_a.route('/<analytic_id>/custom/<src_id>/<param1>/')
    class Custom_1(Resource):

        def post(self, analytic_id, src_id, param1=None):
            client = db_client()
            col = db_collection(client, DATALOADER_DB_NAME, DATALOADER_COL_NAME)
            try:
                src = find_source(col, src_id)
            except IndexError:
                return 'No resource at that URL.', 404
            filepath = src['rootdir']
            return utils.run_algorithm_custom(analytic_id, filepath=filepath, param1=param1, src_id=src_id)

@ns_r.route('/')
class Results(Resource):
    @api.doc(model='Results')
    def get(self):
        '''
        Returns a list of available results.
        '''
        _, col = results_collection()
        cur = col.find()
        results = []
        for src in cur:
            response = {
                key: value
                for key, value in src.items() if key != '_id'
            }
            results.append(response)

        return results

    # @api.doc(responses={204: 'Resource removed successfully'})
    @api.hide
    def delete(self):
        '''
        Deletes all stored results.
        '''
        _, col = results_collection()
        # remove the entries in mongo
        col.remove({})
        # remove the actual files
        for directory in os.listdir(RESULTS_PATH):
            file_path = os.path.join(RESULTS_PATH, directory)
            shutil.rmtree(file_path)

        return '', 204

    @ns_r.route('/explorable/')
    class Explorable(Resource):
        @api.doc(model='Result')
        def get(self):
            '''
            Returns a list of explorable results.
            '''
            _, col = results_collection()
            cur = col.find()
            explorable = []
            for src in cur:
                for result in src['results']:
                    exp = {}
                    exp['rootdir'] = src['rootdir']
                    exp['src_id'] = src['src_id']
                    exp['id'] = result['id']
                    exp['outputs'] = result['outputs']
                    exp['name'] = result['name']
                    exp['created'] = result['created']
                    explorable.append(exp)

            return explorable

    @ns_r.route('/<src_id>/')
    @api.doc(
        params={'src_id': 'The ID assigned to a particular result\'s source'})
    class ResultSrc(Resource):
        @api.doc(responses={
            204: 'Resource removed successfully',
            404: 'No resource at that URL'
        })
        def delete(self, src_id):
            '''
            Deletes specified result tree.
            This will permanently remove this result tree from the system. USE CAREFULLY!

            '''
            res = get_results_source(src_id)

            try:
                src = src['results']
            except IndexError:
                return 'No resource at that URL.', 404
            else:
                col.remove(res)
                shutil.rmtree(os.path.join(RESULTS_PATH + src_id))
                return '', 204

        @api.doc(model='Results')
        def get(self, src_id):
            '''
            Returns the specified result tree.
            '''
            res = get_results_source(src_id)
            if not res:
                return ('Not found', 404)

            return res

    @ns_r.route('/<src_id>/<res_id>/')
    @api.doc(
        params={'src_id': 'The ID assigned to a particular result\'s source'})
    @api.doc(params={'res_id': 'The ID assigned to a particular result'})
    class Result(Resource):
        @api.doc(responses={
            204: 'Resource removed successfully',
            404: 'No resource at that URL'
        })
        def delete(self, src_id, res_id):
            '''
            Deletes specified result.
            This will permanently remove this result from the system. USE CAREFULLY!
            '''
            try:
                res = get_results_source(src_id)
                res = res['results']

            except IndexError:
                return 'No resource at that URL.', 404

            else:
                results_new = []
                found = False
                for each in res:
                    if each['id'] != res_id and each['name'] != res_id:
                        results_new.append(each)
                    else:
                        found = True
                if found:
                    col.update({
                        'src_id': src_id
                    }, {'$set': {
                        'results': results_new
                    }})
                else:
                    return 'No resource at that URL.', 404

                shutil.rmtree(os.path.join(RESULTS_PATH, src_id, res_id))
                return '', 204

        @api.doc(responses={200: 'Success', 404: 'No resource at that URL'})
        @api.doc(model='Result')
        def get(self, src_id, res_id):
            '''
            Returns the specified result.
            '''
            try:
                res = get_results_source(src_id)
                res = res['results']

            except IndexError:
                response = {}
                # return ('No resource at that URL.', 404)

            else:
                for result in res:
                    if result['id'] == res_id or result['name'] == res_id:
                        return {'result': result}

            return 'No resource at that URL.', 404

        @ns_r.route(
            '/<src_id>/<res_id>/download/<output_file>/<file_download_name>/')
        class Download(Resource):
            def get(self, src_id, res_id, output_file, file_download_name):
                '''
                Downloads the specified result.
                Returns the specific file indicated by the user.
                '''
                res = get_results_source(src_id)

                if not res:
                    pass
                else:
                    res = res['results']
                    for result in res:
                        if result['id'] == res_id or result['name'] == res_id:
                            return send_from_directory(
                                result['rootdir'],
                                output_file,
                                as_attachment=True,
                                attachment_filename=file_download_name)

                return 'No resource at that URL.', 404
