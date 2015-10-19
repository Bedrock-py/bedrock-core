from flask import Flask, request
from flask.ext.restplus import Api, Resource, fields
import pymongo, json, string
from bson import json_util
from datetime import datetime
import utils
from bson.objectid import ObjectId
from CONSTANTS import *
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)
app.debug = True

client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)

api = Api(app, version="0.1", title="User Memo API", 
    description="Analytics-Framework API supporting Users and their related Memo data (Copyright &copy 2015, Georgia Tech Research Institute)")

ns_m = api.namespace('memo')
ns_u = api.namespace('user')


api.model('memo',{ 
                'user_name': fields.String(description='user name', required=True),
                'element_id': fields.String(description='the id of a source, matrix, or visulazation that the memo is attached to.',required=True),
                'parent_id': fields.String(description='parent id',required=False),
                'text': fields.String(description='text', required=False)
                })

api.model('user',{
	            'user_name': fields.String(description='user name', required=True),#permanent
	            'user_id' : fields.String(description='user id', required=False),#permanent                
                'role' : fields.String(description='role', required=False),#can update
                'groups': fields.List(fields.String,description='groups', required=False),#can update
                'elements_owned': fields.List(fields.String,description='elements owned', required=False),#can update
                'password_hash' : fields.String(description='password', required=False),#can update
                'old_password_hash' : fields.String(description='old password', required=False),#can update
				#'account_creation': fields.DateTime(dt_format='iso8601',description='account creation', required=False),#permanent
                #'last_modified': fields.DateTime(dt_format='iso8601',description='last modified', required=False),#automatic update on post
                #'last_login': fields.DateTime(dt_format='iso8601',description='last_login', required=False),#automatic update on post
      			#'last_pw_modification' : fields.DateTime(dt_format='iso8601',description='last modified', required=False),#automatic update on post
				})


@ns_u.route('/')
class User(Resource):


	@ns_u.route('/<user_name>/')
	class User_Get(Resource): 
		def get(self, user_name):	
			col = client[USERMEMO_DB_NAME][USER_COL_NAME]
			user = col.find_one({"user_name":user_name}, {'_id':0.'password_hash':0})
			if user == None:
				return "Bad Request",400
			else:
				return json.dumps(user, default=json_util.default),200		


	@ns_u.route('/create_user/')
	class User_create(Resource): 
		@api.doc(body='user')
		def put(self):
			col = client[USERMEMO_DB_NAME][USER_COL_NAME]
			data = json.loads(request.data)
			user = col.find_one({"user_name":data['user_name']}, {'_id':0})
			if user != None:
				return "Bad Request",400
			for key in data.keys():
				if len(data.keys()) != 6 or key not in ["user_id","user_name","role","groups","elements_owned","password_hash"]:
					return "Bad Request",400

			data['account_creation'] = datetime.utcnow()
			data['last_modified'] = datetime.utcnow()
			data['last_login'] = datetime.utcnow()
			data['last_pw_modification'] = datetime.utcnow()

			password = pbkdf2_sha256.encrypt(data['password_hash'])
			data['password_hash'] = password
			col.create_index(data["user_name"],unique =True)

			result = col.insert_one(data)
			if result.modified_count:
					return "Success",201
			return "Bad Request",400



	@ns_u.route('/login/')
	class User_login(Resource): 
		@api.doc(body='user')#/login
		def post(self):
			col = client[USERMEMO_DB_NAME][USER_COL_NAME]
			data = json.loads(request.data)
			
			if not data.has_key('password_hash'):
				return "Invalid Login", 401

			user = col.find_one({"user_name":data['user_name']}, {'_id':0})

			if user == None:
				return "Invalid Login", 401

			if pbkdf2_sha256.verify(data['password_hash'], user['password_hash']):
				result = col.update_one({"user_name":data['user_name']},{'$set':{"last_login":datetime.utcnow()}})
				if result.modified_count:
					return "Valid Login",200
			return "Invalid Login", 401


	@ns_u.route('/update_info/')
	class User_update_info(Resource): 
		@api.doc(body='user')
		def post(self):
			col = client[USERMEMO_DB_NAME][USER_COL_NAME]
			data = json.loads(request.data)
			
			user = col.find_one({"user_name":data['user_name']}, {'_id':0})
			if user == None:
				return "Bad Request",400
			changed = False
			for key in data.keys():
				if key in ["role","groups","elements_owned"]:
					result = col.update_one({"user_name":data['user_name']},{'$set':{key:data[key],"last_modified":datetime.utcnow()}})
					if result.modified_count:
						changed = True
			if changed:
				return "Success",200
			
			return "Bad Request",400


	@ns_u.route('/update_password/')
	class User_update_password(Resource): 
		@api.doc(body='user')
		def post(self):
			col = client[USERMEMO_DB_NAME][USER_COL_NAME]
			data = json.loads(request.data)
			
			user = col.find_one({"user_name":data['user_name']}, {'_id':0})
			if user == None:
				return "Bad Request",400

			if not data.has_key('password_hash') or not data.has_key('old_password_hash'):
				return "Bad Request",400

			if pbkdf2_sha256.verify(data['old_password_hash'], user['password_hash']):
				password_hash = pbkdf2_sha256.encrypt(data['password_hash'])
				result = col.update_one({"user_name":data['user_name']},{'$set':{"password_hash":password_hash,"last_modified":datetime.utcnow(),'last_pw_modification':datetime.utcnow()}})
				if result.modified_count:
					return "Success",200
				
			return "Bad Request",400
			

	@ns_u.route('/delete_user/')
	class User_delete(Resource): 
		@api.doc(body='user')
		def delete(self):
			col = client[USERMEMO_DB_NAME][USER_COL_NAME]
			data = json.loads(request.data)
			
			user = col.find_one({"user_name":data['user_name']}, {'_id':0})
			if user == None:
				return "Bad Request",400
			col.delete_one({"user_name":data['user_name']})
			return "Deleted",200
	
	@ns_u.route('/logout_user/')
	class User_logout(Resource): 
		@api.doc(body='user')
		def post(self):
			pass
	
@ns_m.route('/')
class Memo(Resource):


	@ns_m.route('/create_memo/')
	class Memo_create(Resource):
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
				return "Bad Request",400

			user = col2.find_one({"user_name":data['user_name']}, {'_id':0})
			if user == None:
				return "Bad Request",400

			user["elements_owned"].append(data['element_id'])
			result = col2.update_one({"user_name":data['user_name']},{'$set':{"last_login":datetime.utcnow(),"elements_owned":user["elements_owned"]}})
			if not result:
				return "Bad Request",400

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
	class Memo_update(Resource):
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
	class Memo_delete(Resource):
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
