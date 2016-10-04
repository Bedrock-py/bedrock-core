from flask import Flask, request
from flask.ext.restplus import Api, Resource, fields
import pymongo, json, string
from bson import json_util
from datetime import datetime
import utils
from bson.objectid import ObjectId
from CONSTANTS import *

app = Flask(__name__)
app.debug = True

client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)

api = Api(app, version="0.1", title="Memo API", 
    description="Analytics-Framework API supporting Memo data (Copyright &copy 2015, Georgia Tech Research Institute)")

ns_m = api.namespace('memo')

api.model('memo',{ 
                'user_name': fields.String(description='user name', required=True),
                'element_id': fields.String(description='the id of a source, matrix, or visulazation that the memo is attached to.',required=True),
                'parent_id': fields.String(description='parent id',required=False),
                'text': fields.String(description='text', required=False)
                })


@ns_m.route('/')
class Memo(Resource):


	@ns_m.route('/create_memo/')
	class Memo_Create(Resource):
		@api.doc(body='memo')
		def put(self):
			col = client[USERMEMO_DB_NAME][MEMO_COL_NAME]
			col2 = client[USERMEMO_DB_NAME][USER_COL_NAME]
			data = json.loads(request.data)
			if not data.has_key('text'):
				data['text'] = ''
			if not data.has_key('parent_id') or data['parent_id'] == "-1":
				data['parent_id'] = "-1"
			elif col.find_one({"element_id":data['parent_id']}, {'_id':0}) == None:
				return "Bad Request",400

			memo = col.find_one({"user_name":data['user_name'],"element_id":data['element_id']}, {'_id':0})
			if memo != None:
				return "Bad Request",401

			user = col2.find_one({"user_name":data['user_name']}, {'_id':0})
			if user == None:
				return "Bad Request",402

			user["elements_owned"].append(data['element_id'])
			result = col2.update_one({"user_name":data['user_name']},{'$set':{"last_login":datetime.utcnow(),"elements_owned":user["elements_owned"]}})
			if not result:
				return "Bad Request",403

			col.insert_one(data)

			return "Success",201


	@ns_m.route('/<user_name>/<element_id>/')
	class Memo_Get(Resource): 
		def get(self, user_name,element_id):
			col = client[USERMEMO_DB_NAME][MEMO_COL_NAME]
			memo = col.find_one({"user_name":user_name,"element_id":element_id}, {'_id':0})
			if memo == None:
				return "Bad Request",400
			memo['text'] = [memo['text']]
			curr = col.find_one({"user_name":user_name,"element_id":memo['parent_id']})

			while curr != None and curr['parent_id'] != -1:
				memo['text'].append(curr['text'])
			 	curr = col.find_one({"user_name":user_name,"element_id":curr['parent_id']})
			return memo,200			


	@ns_m.route('/update_memo/')
	class Memo_Update(Resource):
		@api.doc(body='memo')
		def post(self):
			col = client[USERMEMO_DB_NAME][MEMO_COL_NAME]
			data = json.loads(request.data)
			if not data.has_key('text'):
				return "Bad Request",400

			memo = col.find_one({"user_name":data['user_name'],"element_id":data['element_id']}, {'_id':0})
			if memo == None:
				return "Bad Request",400
			result = col.update_one({"user_name":data['user_name'],"element_id":data['element_id']},{'$set':{"text":data['text']}})
			if result:
				return "Success",200
			return "Bad Request",400



	############################################################### 
	#Please be aware that this call only deletes 
	#the particular memo being mentioned.
	#It does not go through and delete children or update parents. 
	#You will have to manually update this information in the JS. 
	#Failing to do so will cause memos to not be returned properly. 
	################################################################
	@ns_m.route('/delete_memo/')
	class Memo_Delete(Resource):
		@api.doc(body='memo')
		def delete(Self):
			col = client[USERMEMO_DB_NAME][MEMO_COL_NAME]
			col2 = client[USERMEMO_DB_NAME][USER_COL_NAME]
			data = json.loads(request.data)

			memo = col.find_one({"user_name":data['user_name'],"element_id":data['element_id']}, {'_id':0})
			if memo == None:
				return "Bad Request",400
			result = col.delete_one({"user_name":data['user_name'],"element_id":data['element_id']})
			if not result:
				return "Bad Request",400

			user = col2.find_one({"user_name":data['user_name']}, {'_id':0})
			if user == None:
				return "Bad Request",400
			user["elements_owned"].remove(data['element_id'])
			result = col2.update_one({"user_name":data['user_name']},{'$set':{"last_login":datetime.utcnow(),"elements_owned":user["elements_owned"]}})
			if result:
				return "Deleted",200
