#****************************************************************
#  File: DataLoaderAPIv01.py
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

from flask import Flask, jsonify, request, redirect, url_for, send_from_directory, Response
from datetime import datetime
from django.utils.encoding import smart_str, smart_unicode
from flask.ext import restful
from flask.ext.restplus import Api, Resource, fields
import pymongo, sys, json, os, socket, shutil, string, re
from bson.json_util import dumps
import utils
# raise Exception(utils)
from werkzeug import secure_filename
from bson.objectid import ObjectId
import requests
import urllib2
from CONSTANTS import *

app = Flask(__name__)
app.debug = True

ALLOWED_EXTENSIONS = set(['csv', 'tsv', 'mtx', 'xls', 'xlsx', 'zip','txt'])

api = Api(app, version="0.1", title="DataLoader API", 
    description="Analytics-Framework API supporting creation and use of matrices (Copyright &copy 2015, Georgia Tech Research Institute)")

ns = api.namespace('sources')
ns_i = api.namespace('ingest')
ns_f = api.namespace('filters')

@api.model(fields={ 
                'attrname': fields.String(description='Python variable name', required=True),
                'name': fields.String(description='Name to use for display', required=True),
                'type': fields.String(description='Kind of html input type to display', required=True),
                'value': fields.String(description='Default value to use', required=True),
                })
class Params(fields.Raw):
    def format(self, value):
        return { 
                'attrname': value.attrname,
                'name': value.name,
                'type': value.type,
                'value': value.value,
                }

api.model('Filter', {
    'filter_id': fields.String(description='Unique ID for the filter', required=True),
    'classname': fields.String(description='Classname within the python file', required=True),
    'description': fields.String(description='Description for the filter'),
    'name': fields.String(description='Filter name'),
    'input': fields.String(description='Datatype this filter can be applied to'),
    'outputs': fields.List(fields.String, description='List of output files generated by the filter', required=True),
    'parameters': fields.List(Params, description='List of input parameters needed by the filter'),
    'possible_names': fields.List(fields.String, description='List of names that could indicate appropriateness for this filter', required=True),
    'stage': fields.String(description='Stage at which to apply the filter: {before, after}', required=True),
    'type': fields.String(description='Type of filter: {extract, convert, add}', required=True),
})

api.model('Ingest', {
    'ingest_id': fields.String(description='Unique ID for the ingest module', required=True),
    'classname': fields.String(description='Classname within the python file', required=True),
    'description': fields.String(description='Description for the ingest module'),
    'name': fields.String(description='Ingest module name'),
    'parameters': fields.List(Params, description='List of input parameters needed by the ingest module'),
})


@api.model(fields={ 
                'created': fields.String(description='Timestamp of creation'),
                'id': fields.String(description='Unique ID for the matrix', required=True),
                'src_id': fields.String(description='Unique ID for the source used to generate the matrix', required=True),
                'mat_type': fields.String(description='Matrix type'),
                'name': fields.String(description='Matrix name'),
                'outputs': fields.List(fields.String, description='List of output files associated with the matrix', required=True),
                'rootdir': fields.String(description='Path to the associated directory', required=True),
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

api.model('Source', {
    'created': fields.String(description='Timestamp of creation'),
    'src_id': fields.String(description='Unique ID for the source', required=True),
    'name': fields.String(description='Source name'),
    'src_type': fields.String(description='Source type'),
    'matrices_count': fields.Integer(description='Number of matrices generated from this source'),
    'matrices': fields.List(Matrix, description='List of matrices generated from this source', required=True),
})

api.model('Features', {
    'features': fields.List(fields.String, description='List of features for this matrix', required=True),
})

@api.model(fields={ 
                'examples': fields.List(fields.String, description='Example samples for this field'),
                'key': fields.String(description='Name of this field', required=True),
                'key_usr': fields.String(description='User-edited name of this field', required=True),
                'suggestion': fields.String(description='Top suggested filter for this field'),
                'suggestions': fields.List(fields.String, description='List of other possible filters for this field', required=True),
                'type': fields.List(fields.String, description='Basic type for this field', required=True),
                })
class Schema(fields.Raw):
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

api.model('Schemas', {
    'name_of_source': fields.List(Schema, description='List of schemas for this source', required=True),
})


@ns_i.route('/')
class IngestModules(Resource):
    @api.doc(model='Ingest')
    def get(self):
        '''
        Returns a list of available ingest modules.
        All ingest modules registered in the system will be returned. If you believe there is an ingest module that exists in the system but is not present here, it is probably not registered in the MongoDB database.
        '''
        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        col = client[DATALOADER_DB_NAME][INGEST_COL_NAME]
        cur = col.find()
        ingest = []
        for c in cur:
            response = {key: value for key, value in c.items() if key != '_id'}
            ingest.append(response)
        
        return ingest

    @ns_i.route('/<ingest_id>/')
    class Ingest(Resource):
        @api.doc(model='Ingest')
        def get(self, ingest_id):
            '''
            '''
            client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
            col = client[DATALOADER_DB_NAME][INGEST_COL_NAME]

            try:
                src = col.find({'ingest_id':ingest_id})[0]

            except IndexError:
                return 'No resource at that URL', 401

            else:
                response = {key: value for key, value in src.items() if key != '_id'}

                return response


@ns_f.route('/')
class Filters(Resource):
    @api.doc(model='Filter')
    def get(self):
        '''
        Returns a list of available filters.
        All filters registered in the system will be returned. If you believe there is a filter that exists in the system but is not present here, it is probably not registered in the MongoDB database.
        '''
        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        col = client[DATALOADER_DB_NAME][FILTERS_COL_NAME]
        cur = col.find()
        filters = []
        for c in cur:
            response = {key: value for key, value in c.items() if key != '_id'}
            filters.append(response)
        
        return filters


@ns.route('/')
class Sources(Resource):
    @api.doc(model='Source')
    def get(self):
        '''
        Returns a list of available sources.
        All sources registered in the system will be returned.
        '''
        client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
        col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
        cur = col.find()
        sources = []
        for src in cur:
            try:
                sources.append({key: value for key, value in src.items() if key != '_id' and key != 'stash'})
            except KeyError:
                print src
        return sources

    @api.hide
    def delete(self):
        '''
        Deletes all stored sources.
        This will permanently remove all sources from the system. USE CAREFULLY!
        '''
        col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
        #remove the entries in mongo
        col.remove({})
        #remove the actual files
        for directory in os.listdir(DATALOADER_PATH):
            file_path = os.path.join(DATALOADER_PATH, directory)
            shutil.rmtree(file_path)

        return '', 204

    @ns.route('/download/<src_id>/<matrix_id>/<output_file>/<file_download_name>/')
    class Download(Resource):
        def get(self,src_id,matrix_id,output_file,file_download_name):
            '''
            Downloads the specified matrix file.
            Returns the specific file indicated by the user.
            '''

            client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
            col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
            try:
                matrices = col.find({'src_id':src_id})[0]['matrices']
            except IndexError:
                response = {}
                # return ('No resource at that URL.', 404)
            else:
                for matrix in matrices:
                    if matrix['id'] == matrix_id:
                        return send_from_directory(matrix['rootdir'],output_file, as_attachment=True, attachment_filename=file_download_name)
                        
    @ns.route('/<name>/<ingest_id>/<group_name>/')
    class NewSource(Resource):
        @api.doc(model='Source')
        def put(self, name, ingest_id, group_name=""):
            '''
            Saves a new resource with a ID.
            Payload can be either a file or JSON structured configuration data. Returns the metadata for the new source.
            '''
            src_id = utils.getNewId()
            t = utils.getCurrentTime()
            conn_info = request.get_json()
            if conn_info == None:
                file = request.files['file']
                ext = re.split('\.', file.filename)[1]
                # if not ext in ALLOWED_EXTENSIONS:.

                #     return ('This filetype is not supported.', 415)

                if 'zip' in file.filename:
                    src_type = 'zip'
                else:
                    src_type = 'file'

                rootpath = DATALOADER_PATH + src_id + '/source/'
                filename = secure_filename(file.filename)
                if not os.path.exists(rootpath):
                    os.makedirs(rootpath, 0775)
                filepath = os.path.join(rootpath, filename)
                file.save(filepath)
            
            else:
                conn_info = request.get_json()

                src_type = 'conf'
                dirOriginal = DATALOADER_PATH + src_id + '/source/'

                os.makedirs(dirOriginal, 0775)
                filepath = os.path.join(dirOriginal, 'conf.json')

                with open(filepath, 'w') as outfile:
                    json.dump(conn_info, outfile)


            client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
            col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]

            rootpath = DATALOADER_PATH  + src_id + '/'

            source = {}
            source['name'] = name
            source['host'] = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][-1]
            source['rootdir'] = rootpath
            source['src_id'] = src_id
            source['src_type'] = src_type
            source['created'] = t
            source['matrices'] = []
            source['ingest_id'] = ingest_id
            source['status'] = None
            source['count'] = 0
            source['stash'] = []
            source['group_name'] = group_name

            col.insert(source)

            response = {}
            response['name'] = name
            response['host'] = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][-1]
            response['rootdir'] = rootpath
            response['src_id'] = src_id
            response['src_type'] = src_type
            response['created'] = t
            response['matrices_count'] = len(source['matrices'])

            return response, 201


    @ns.route('/explorable/')
    class Explorable(Resource):
        @api.doc(model='Matrix')
        def get(self):
            '''
            Returns a list of generated matrices.
            '''

            client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
            col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
            cur = col.find()
            explorable = []
            for src in cur:
                for matrix in src['matrices']:
                    exp = {}
                    exp['rootdir'] = matrix['rootdir']
                    exp['src_id'] = src['src_id']
                    exp['id'] = matrix['id']
                    exp['outputs'] = matrix['outputs']
                    exp['name'] = matrix['name']
                    exp['created'] = matrix['created']
                    exp['mat_type'] = matrix['mat_type']
                    explorable.append(exp)

            return explorable

    @ns.route('/group/<group_name>/')
    class Group(Resource):
        @api.doc(model='Matrix')
        def get(self, group_name):
            '''
            Returns a list of sources within a particular group.
            '''

            client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
            col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
            sources = col.find({'group_name':group_name})
            response = [{key: value for key, value in src.items() if key != '_id'} for src in sources]

            return response

    @ns.route('/groups/')
    class Groups(Resource):
        @api.doc(model='Matrix')
        def get(self):
            '''
            Returns a list of groups available.
            '''

            client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
            col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
            groups = col.aggregate([{"$group":{"_id": "$group_name"}}])
            response = [src["_id"] for src in groups]

            return response

    @ns.route('/<src_id>/')
    class Source(Resource):
        @api.doc(model='Matrix')
        def get(self, src_id):
            '''
            Returns metadata and a list of matrices available for a particular source.
            '''
            client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
            col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
            try:
                src = col.find({'src_id':src_id})[0]

            except IndexError:
                return 'No resource at that URL', 401

            else:
                response = {key: value for key, value in src.items() if key != '_id'}

                return response

        def delete(self, src_id):
            '''
            Deletes specified source.
            This will permanently remove this source from the system. USE CAREFULLY!
            '''
            client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
            col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
            res_col = client[DATALOADER_DB_NAME][RESULTS_COL_NAME]

            try:
                src = col.find({'src_id':src_id})[0]
                matrices = col.find({'src_id':src_id})[0]['matrices']

            except IndexError:
                return 'No resource at that URL.', 404

            else:
                for each in matrices:
                    mat_id = each['id']
                    shutil.rmtree(DATALOADER_PATH + src_id + '/' + mat_id)

                    try:
                        res = res_col.find({'src_id':mat_id})[0]['results']
                        print 'going to remove', RESPATH + mat_id
                        shutil.rmtree(RESPATH + mat_id)
                        res_col.remove({'src_id':mat_id})

                    except IndexError:
                        pass

                utils.delete(src)

                col.remove({'src_id':src_id})
                shutil.rmtree(DATALOADER_PATH + src_id)
                return '', 204



        @api.doc(model='Matrix', body='Source')
        def post(self, src_id):
            '''
            Generate a matrix from the source stored at that ID.
            Returns metadata for that matrix.
            '''
            posted_data = request.get_json(force=True)
            client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
            col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]

            try:
                src = col.find({'src_id':src_id})[0]

            except IndexError:
                return 'No resource at that URL.', 404

            error, matricesNew = utils.ingest(posted_data, src)

            if error:
                return 'Unable to create matrix.', 406

            matrices = []
            for each in src['matrices']:
                matrices.append(each)
            matrices.extend(matricesNew)
            col.update({'src_id':src_id}, { '$set': {'matrices': matrices} })


            return matricesNew, 201


        @ns.route('/<src_id>/explore/')
        class Explore(Resource):
            @api.doc(model='Schemas')
            def get(self, src_id):
                '''
                Returns a list of schemas for a particular source.
                '''

                client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
                col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
                try:
                    src = col.find({'src_id':src_id})[0]
                except IndexError:
                    return 'No resource at that URL.', 404

                filepath = src['rootdir'] + '/source/' 

                #get filters
                f_client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
                f_col = client[DATALOADER_DB_NAME][FILTERS_COL_NAME]
                filters = f_col.find()

                return utils.explore(src['ingest_id'], filepath, filters)


        @ns.route('/<src_id>/custom/<param1>/')
        # @ns.route('/<src_id>/custom/<param1>/<param2>/')
        # @ns.route('/<src_id>/custom/<param1>/<param2>/<param3>/')
        class Custom(Resource):
            def get(self, src_id, param1):
#            def get(self, src_id, param1=None, param2=None, param3=None):
                client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
                col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
                try:
                    src = col.find({'src_id':src_id})[0]
                except IndexError:
                    return 'No resource at that URL.', 404
                filepath = src['rootdir'] 
                return utils.custom(src['ingest_id'], filepath, param1=param1)

            def post(self, src_id, param1=None, param2=None, param3=None):
                client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
                col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
                try:
                    src = col.find({'src_id':src_id})[0]
                except IndexError:
                    return 'No resource at that URL.', 404
                filepath = src['rootdir'] 
                return utils.custom(src['ingest_id'], filepath, param1=param1, param2=param2, param3=param3, payload=request.get_json())
        #api.add_resource(Custom, '/<src_id>/custom/<param1>/', '/<src_id>/custom/<param1>/<param2>/', '/<src_id>/custom/<param1>/<param2>/<param3>/')


        @ns.route('/<src_id>/stream/')
        class Stream(Resource):
            def post(self, src_id):
                '''
                For streaming, start or end the streaming service.
                No payload is sent for this request.
                '''
                client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
                col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
                try:
                    src = col.find({'src_id':src_id})[0]

                except IndexError:
                    return 'No resource at that URL.', 404

                filepath = src['rootdir'] 

                #get filters
                f_client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
                f_col = client[DATALOADER_DB_NAME][FILTERS_COL_NAME]
                filters = f_col.find()
                return utils.stream(src['ingest_id'], filepath)

            def patch(self, src_id):
                '''
                For streaming, toggles streaming on or off.
                This request is used in conjunction with the POST request to this same endpoint.

                '''
                client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
                col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
                try:
                    src = col.find({'src_id':src_id})[0]

                except IndexError:
                    return 'No resource at that URL.', 404

                filepath = src['rootdir'] 

                #get filters
                f_client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
                f_col = client[DATALOADER_DB_NAME][FILTERS_COL_NAME]
                filters = f_col.find()
                utils.update(src['ingest_id'], filepath)
                return


        @ns.route('/<src_id>/<mat_id>/')
        class Matrix(Resource):
            @api.doc(model='Matrix')
            def get(self, src_id, mat_id):
                '''
                Returns metadata for the matrix specified.
                '''
                client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
                col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
                try:
                    matrices = col.find({'src_id':src_id})[0]['matrices']

                except IndexError:
                    return 'No resource at that URL.', 404

                else:
                    for matrix in matrices:
                        if matrix['id'] == mat_id:
                            response = {key: value for key, value in matrix.items() if key != '_id'}

                            return response

                    return 'No resource at that URL.', 404

            def delete(self, src_id, mat_id):
                '''
                Deletes specified matrix.
                This will permanently remove this matrix and any results generated from it from the system. USE CAREFULLY!
                '''
                client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
                col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
                try:
                    matrices = col.find({'src_id':src_id})[0]['matrices']

                except IndexError:
                    return 'No resource at that URL.', 404

                else:
                    matrices_new = []
                    found = False
                    for each in matrices:
                        if each['id'] != mat_id:
                            matrices_new.append(each)
                        else:
                            found = True
                    if found:
                        col.update({'src_id':src_id}, { '$set': {'matrices': matrices_new} })
                    else:
                        return 'No resource at that URL.', 404

                    shutil.rmtree(DATALOADER_PATH + src_id + '/' + mat_id)

                    col = client[DATALOADER_DB_NAME][RESULTS_COL_NAME]
                    try:
                        col.remove({'src_id':mat_id})
                        shutil.rmtree(RESPATH + mat_id)

                    except:
                        pass

                    else:
                        return '', 204


            @ns.route('/<src_id>/<mat_id>/output/')
            class Output(Resource):
                def get(self, src_id, mat_id):
                    '''
                    Returns the REAMDME content for the specified matrix.
                    '''
                    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
                    col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
                    try:
                        matrices = col.find({'src_id':src_id})[0]['matrices']

                    except IndexError:
                        return 'No resource at that URL.', 404

                    else:
                        for matrix in matrices:
                            if matrix['id'] == mat_id:
                                output_path = matrix['rootdir'] + 'output.txt'
                                with open(output_path) as output:
                                    text = output.read()

                                return text

                        return 'No resource at that URL.', 404

            @ns.route('/<src_id>/<mat_id>/features/')
            class Features(Resource):
                @api.doc(model='Features')
                def get(self, src_id, mat_id):
                    '''
                    Returns features for the specified matrix.
                    Features are the names for the columns within the matrix.
                    '''
                    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
                    col = client[DATALOADER_DB_NAME][DATALOADER_COL_NAME]
                    try:
                        matrices = col.find({'src_id':src_id})[0]['matrices']

                    except IndexError:
                        return 'No resource at that URL.', 404

                    else:
                        for matrix in matrices:
                            if matrix['id'] == mat_id:
                                rootdir = matrix['rootdir']
                                try:
                                    features_filepath = rootdir + 'features.txt'
                                    with open(features_filepath) as features_file:
                                        features = features_file.read().split("\n")
                                        features.pop()
                                    response = features
                                except IOError:
                                    response = []

                                return response

                        return 'No resource at that URL.', 404
