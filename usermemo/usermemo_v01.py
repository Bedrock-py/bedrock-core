from flask import Flask, request
from flask.ext.restplus import Api, Resource, fields
import pymongo, json, string
from bson import json_util
from datetime import datetime
import utils
from bson.objectid import ObjectId
from CONSTANTS import *
from passlib.hash import sha256_crypt

app = Flask(__name__)
app.debug = True

client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)

api = Api(app, version="0.1", title="User Memo API", 
    description="Analytics-Framework API supporting Users and their related Memo data (Copyright &copy 2015, Georgia Tech Research Institute)")

ns_m = api.namespace('memo')
ns_u = api.namespace('user')

api.model('memo',{ 
                'user_name': fields.String(description='user name', required=True),
                'element_id': fields.String(description='element id',required=True),
                'parent_id': fields.String(description='parent id',required=False),
                'text': fields.String(description='text', required=False)
                })

api.model('user',{
	            'user_name': fields.String(description='user name', required=True),#permanete
	            'user_id' : fields.String(description='user id', required=False),#permanete                
                'role' : fields.String(description='role', required=False),#can update
                'groups': fields.List(fields.String,description='groups', required=False),#can update
                'elements_owned': fields.List(fields.String,description='elements owned', required=False),#can update
                'password' : fields.String(description='password', required=False),#can update
                'old_password' : fields.String(description='old_password', required=False),#can update
				#'account_creation': fields.DateTime(dt_format='iso8601',description='account creation', required=False),#permanete
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
			user = col.find_one({"user_name":user_name}, {'_id':0})
			if user == None:
				return "User Not Found",404
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
				return "User Already Exists",409
			for key in data.keys():
				if len(data.keys()) != 6 or key not in ["user_id","user_name","role","groups","elements_owned","password"]:
					return "Missing Data",400

			data['account_creation'] = datetime.utcnow()
			data['last_modified'] = datetime.utcnow()
			data['last_login'] = datetime.utcnow()
			data['last_pw_modification'] = datetime.utcnow()

			password = sha256_crypt.encrypt(data['password'])
			data['password'] = password

			col.insert_one(data)
			return "Success",201


	@ns_u.route('/login/')
	class User_login(Resource): 
		@api.doc(body='user')#/login
		def post(self):
			col = client[USERMEMO_DB_NAME][USER_COL_NAME]
			data = json.loads(request.data)
			
			if not data.has_key('password'):
				return "Password Not Present",400

			user = col.find_one({"user_name":data['user_name']}, {'_id':0})

			if user == None:
				return "User Does Not Exist",404

			if sha256_crypt.verify(data['password'], user['password']):
				col.update_one({"user_name":data['user_name']},{'$set':{"last_login":datetime.utcnow()}})
				return "Password Correct",200
			else:
				return "Password Inccorect",401


	@ns_u.route('/update_info/')
	class User_update_info(Resource): 
		@api.doc(body='user')
		def post(self):
			col = client[USERMEMO_DB_NAME][USER_COL_NAME]
			data = json.loads(request.data)
			
			user = col.find_one({"user_name":data['user_name']}, {'_id':0})
			if user == None:
				return "User Does Not Exist",404
			changed = False
			for key in data.keys():
				if key in ["role","groups","elements_owned"]:
					col.update_one({"user_name":data['user_name']},{'$set':{key:data[key],"last_modified":datetime.utcnow()}})
					changed = True
			if changed:
				return "Success",200
			else:
				return "Nothing Avalible To Update",404


	@ns_u.route('/update_password/')
	class User_update_password(Resource): 
		@api.doc(body='user')
		def post(self):
			col = client[USERMEMO_DB_NAME][USER_COL_NAME]
			data = json.loads(request.data)
			
			user = col.find_one({"user_name":data['user_name']}, {'_id':0})
			if user == None:
				return "User Does Not Exist",404

			if not data.has_key('password') or not data.has_key('old_password'):
				return "Password Or Old Password Not Present",400

			if sha256_crypt.verify(data['old_password'], user['password']):
				password = sha256_crypt.encrypt(data['password'])
				col.update_one({"user_name":data['user_name']},{'$set':{"password":password,"last_modified":datetime.utcnow(),'last_pw_modification':datetime.utcnow()}})
				return "Success",200
			else:
				return "Old Password Inccorect",401
			

	@ns_u.route('/delete_user/')
	class User_delete(Resource): 
		@api.doc(body='user')
		def delete(self):
			col = client[USERMEMO_DB_NAME][USER_COL_NAME]
			data = json.loads(request.data)
			
			user = col.find_one({"user_name":data['user_name']}, {'_id':0})
			if user == None:
				return "User Does Not Exist",404
			col.delete_one({"user_name":data['user_name']})
			return "Deleted",200
	
	
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
				return "Parent ID Doesn't Exist",404

			memo = col.find_one({"user_name":data['user_name'],"element_id":data['element_id']}, {'_id':0})
			if memo != None:
				return "Memo already exists",409

			user = col2.find_one({"user_name":data['user_name']}, {'_id':0})
			if user == None:
				return "User Doesn't exists",404

			user["elements_owned"].append(data['element_id'])
			col2.update_one({"user_name":data['user_name']},{'$set':{"last_login":datetime.utcnow(),"elements_owned":user["elements_owned"]}})

			col.insert_one(data)

			return "Success",201


	@ns_m.route('/<user_name>/<element_id>/')
	class Memo_Get(Resource): 
		def get(self, user_name,element_id):
			col = client[USERMEMO_DB_NAME][MEMO_COL_NAME]
			memo = col.find_one({"user_name":user_name,"element_id":element_id}, {'_id':0})
			if memo == None:
				return "Memo Not Found",404
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
				return "Text Not Found",400

			memo = col.find_one({"user_name":data['user_name'],"element_id":data['element_id']}, {'_id':0})
			if memo == None:
				return "Memo Not Found",404
			col.update_one({"user_name":data['user_name'],"element_id":data['element_id']},{'$set':{"text":data['text']}})
			return "Success",200


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
				return "Memo Not Found",404
			col.delete_one({"user_name":data['user_name'],"element_id":data['element_id']})
			user = col2.find_one({"user_name":data['user_name']}, {'_id':0})
			if user == None:
				return "User Doesn't exists",404
			user["elements_owned"].remove(data['element_id'])
			col2.update_one({"user_name":data['user_name']},{'$set':{"last_login":datetime.utcnow(),"elements_owned":user["elements_owned"]}})

			return "Deleted",200
