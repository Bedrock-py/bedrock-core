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
col = client[USERMEMO_DB_NAME][USER_COL_NAME]
col.create_index("user_name",unique =True)


api = Api(app, version="0.1", title="User API", 
    description="Analytics-Framework API supporting User data and profiles (Copyright &copy 2015, Georgia Tech Research Institute)")

ns_u = api.namespace('user')

api.model('user',{
	            'user_name': fields.String(description='user name', required=True),#permanent
	            'user_id' : fields.String(description='user id', required=False),#permanent                
                'role' : fields.String(description='role', required=False),#can update
                'groups': fields.List(fields.String,description='groups', required=False),#can update
                'elements_owned': fields.List(fields.String,description='elements owned', required=False),#can update
                'password_hash' : fields.String(description='password', required=False),#can update
                'old_password_hash' : fields.String(description='old password', required=False),#can update
                'email' : fields.String(description='email', required=False),#can update
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
			user = col.find_one({"user_name":user_name}, {'_id':0,'password_hash':0})
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
				if len(data.keys()) != 7 or key not in ["user_id","user_name","role","groups","elements_owned","password_hash","email"]:
					return "Bad Request",400

			data['account_creation'] = datetime.utcnow()
			data['last_modified'] = datetime.utcnow()
			data['last_login'] = datetime.utcnow()
			data['last_pw_modification'] = datetime.utcnow()

			password = pbkdf2_sha256.encrypt(data['password_hash'])
			data['password_hash'] = password
			result = col.insert_one(data)

			if result.acknowledged:
					return "Success",201
			return "Bad Request",400



	@ns_u.route('/login/')
	class User_login(Resource): 
		@api.doc(body='user')#/login
		def post(self):
			col = client[USERMEMO_DB_NAME][USER_COL_NAME]
			data = json.loads(request.data)
			
			if not data.has_key('password_hash'):
				return "Invalid Login", 400

			user = col.find_one({"user_name":data['user_name']}, {'_id':0})

			if user == None:
				return "Invalid Login", 400

			if pbkdf2_sha256.verify(data['password_hash'], user['password_hash']):
				result = col.update_one({"user_name":data['user_name']},{'$set':{"last_login":datetime.utcnow()}})
				if result.acknowledged:
					return "Valid Login",200
			return "Invalid Login", 400


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
				if key in ["role","groups","elements_owned","email"]:
					result = col.update_one({"user_name":data['user_name']},{'$set':{key:data[key],"last_modified":datetime.utcnow()}})
					if result.acknowledged:
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
				if result.acknowledged:
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
	

	@ns_u.route('/logout/')
	class User_logout(Resource): 
		@api.doc(body='user')
		def post(self):
			pass
