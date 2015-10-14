from flask import Flask, request
from flask.ext.restplus import Api, Resource, fields
import pymongo, json, string
import utils
from bson.objectid import ObjectId
from CONSTANTS import *

app = Flask(__name__)
app.debug = True

client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
col = client[MEMO_DB_NAME][MEMO_COL_NAME]

api = Api(app, version="0.1", title="Memo API", 
    description="Analytics-Framework API supporting Memos for data (Copyright &copy 2015, Georgia Tech Research Institute)")

ns = api.namespace('memo')

api.model('memo_get',{ 
                'user_id': fields.String(description='user id', required=True),
                'element_id': fields.String(description='element id',required=True)
                })

api.model('memo_put',{ 
                'user_id': fields.String(description='user id', required=True),
                'element_id': fields.String(description='element id',required=True),
                'parent_id': fields.String(description='parent id',required=True),
                'text': fields.String(description='text', required=True)
                })

api.model('memo_post',{ 
                'user_id': fields.String(description='user id', required=True),
                'element_id': fields.String(description='element id',required=True),
                'text': fields.String(description='updated text', required=True)
                })

@ns.route('/')
class Memo(Resource):

	@ns.route('/<user_id>/<element_id>/')
	class Memo_Get(Resource): 
		def get(self, user_id,element_id):
			memo = col.find_one({"user_id":user_id,"element_id":element_id}, {'_id':0})
			if memo == None:
				return "Object Not Found",404
			memo['text'] = [memo['text']]
			curr = memo
			while curr['parent_id'] != -1:
			 	curr = col.find_one({"user_id":user_id,"element_id":curr['parent_id']})
			 	memo['text'].append(curr['text'])
			return memo,200			

	@api.doc(body='memo_put')
	def put(self):
		data = json.loads(request.data)
		memo = col.find_one({"user_id":data['user_id'],"element_id":data['element_id']}, {'_id':0})
		if memo != None:
			return "Object already exists",409

		col.insert_one(data)
		return "Success",201


	@api.doc(body='memo_post')
	def post(self):
		data = json.loads(request.data)
		user_id = data['user_id']
		element_id = data['element_id']
		text = data['text']
		memo = col.find_one({"user_id":user_id,"element_id":element_id}, {'_id':0})
		if memo == None:
			return "Object Not Found",404
		col.update_one({"user_id":user_id,"element_id":element_id},{'$set':{"text":text}})
		return "Success",200


	############################################################### 
	#Please be aware that this call only deletes 
	#the particular memo being mentioned.
	#It does not go through and delete children or update parents. 
	#You will have to manually update this information in the JS. 
	#Failing to do so will cause memos to not be returned properly. 
	################################################################
	@api.doc(body='memo_get')
	def delete(Self):
		data = json.loads(request.data)
		user_id = data['user_id']
		element_id = data['element_id']
		memo = col.find_one({"user_id":user_id,"element_id":element_id}, {'_id':0})
		if memo == None:
			return "Object Not Found",404
		col.delete_one({"user_id":user_id,"element_id":element_id})
		return "Deleted",200 