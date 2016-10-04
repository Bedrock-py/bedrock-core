import flask
from flask import Flask, request, Response
from flask.ext.restplus import Api, Resource, fields
import flask.ext.login as flask_login
from flask.ext.login import LoginManager, login_required, fresh_login_required
import pymongo
import json
import string
from bson import json_util
from datetime import datetime
from CONSTANTS import *
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)
app.secret_key = '\xfd\x03\xc9\xc6\xbe\xd0\xe8\xd6S5\\>\xe8\xb87\x11\xac\xcaJ\xdb\x9a\xfd(z'
app.debug = True

client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
col = client[USER_DB_NAME][USER_COL_NAME]
col.create_index("username", unique=True)

'''
Flask Login Manager initialization
'''
login_manager = LoginManager()
login_manager.init_app(app)

'''
Flask Login User class
'''
class User(flask_login.UserMixin):
    pass

'''
User Loader Callback
'''
@login_manager.user_loader
def load_user(username):
    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    col = client[USER_DB_NAME][USER_COL_NAME]
    data = col.find_one({"username": username}, {'_id': 0,'password_hash': 0})
    if data is None:
        return
    user = User()
    user.id = data["username"]
    return user

'''
Unauthorized Callback
'''
@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'


api = Api(app, version="0.1", title="User Management API",
    description="Analytics-Framework API supporting User Management (Copyright &copy 2015, Georgia Tech Research Institute)")

ns_u = api.namespace('user')

api.model('UserAuth',{
                    'username' : fields.String (description='username', required=True),
                    'password' : fields.String (description='password', required=True)
            })

api.model('UserChange',{
                    'username' : fields.String (description='username', required=True),
                    'password' : fields.String (description='password', required=True),
                    'new_password' : fields.String (description='password', required=True)
            })

api.model('UserCreate',{
                    'username' : fields.String (description='username', required=True),
                    'password' : fields.String (description='password', required=True),
                    'email'    : fields.String (description='email', required=True)
            })

api.model('UserInfo',{
                    'username'      : fields.String (description='username', required=True),
                    'role'          : fields.String (description='role'),
                    'groups'        : fields.List (fields.String, description='groups'),
                    'elements_owned': fields.List (fields.String, description='elements owned'),
                    'email'         : fields.String (description='email')
            })


@ns_u.route('/')
class UserManagement(Resource):

    @ns_u.route('/<username>')
    class User_Get(Resource):
        @login_required
        def get(self, username):
            '''
            Returns all information about a particular user in the database or None
            '''
            client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
            col = client[USER_DB_NAME][USER_COL_NAME]
            user = col.find_one({"username": username}, {'_id': 0, 'password_hash': 0, 'old_password_hash': 0})
            if user is None:
                return "Bad Request", 400

            return Response(response=json.dumps(user, default=json_util.default), status=200, mimetype="application/json")


    @ns_u.route('/create_user')
    class User_Create(Resource):
        @api.doc(body='UserCreate')
        def put(self):
            '''
            Create a new user
            '''
            client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
            col = client[USER_DB_NAME][USER_COL_NAME]
            data = json.loads(request.data)
            user = col.find_one({"username": data['username']}, {'_id':0})
            if user is not None:
                return "Bad Request", 400

            try:
                if data['username'] is None or len(data['username']) == 0:
                    return "Bad Request", 400
                if data['password'] is None or len(data['password']) == 0:
                    return "Bad Request", 400
                if data['email'] is None or len(data['email']) == 0:
                    return "Bad Request", 400
            except KeyError:
                return "Bad Request", 400

            user = {}
            user['username'] = data['username']
            user['email'] = data['email']
            user['role'] = None
            user['groups'] = [ "users" ]
            user['elements_owned'] = []
            user['account_creation'] = datetime.utcnow()
            user['last_modified'] = datetime.utcnow()
            user['last_login'] = datetime.utcnow()
            user['last_pw_modification'] = datetime.utcnow()

            password = pbkdf2_sha256.encrypt(data['password'])
            user['password_hash'] = password
            user['old_password_hash'] = None
            result = col.insert_one(user)

            if result.acknowledged:
                return "Success", 201

            return "Bad Request", 400


    @ns_u.route('/login')
    class User_Login(Resource):
        @api.doc(body='UserAuth')
        def post(self):
            '''
            Login as user
            '''
            client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
            col = client[USER_DB_NAME][USER_COL_NAME]
            data = json.loads(request.data)

            if not data.has_key('password'):
                return "Invalid Login", 400

            user = col.find_one({"username": data['username']}, {'_id':0})

            if user is None:
                return "Invalid Login", 400

            if pbkdf2_sha256.verify(data['password'], user['password_hash']):
                user = User()
                user.id = data['username']
                flask_login.login_user(user)
                result = col.update_one({
                                            "username": data['username']
                                        },
                                        {
                                            '$set':
                                                {
                                                    "last_login":datetime.utcnow()
                                                }
                                        })
                if result.acknowledged:
                    return "Valid Login", 200

            return "Invalid Login", 400


    @ns_u.route('/update_info')
    class User_Update_Info(Resource):
        @api.doc(body='UserInfo')
        @fresh_login_required
        def post(self):
            '''
            Change user profile information
            '''
            client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
            col = client[USER_DB_NAME][USER_COL_NAME]
            data = json.loads(request.data)

            user = col.find_one({"username": data['username']}, {'_id':0})

            if user is None:
                return "Bad Request", 400

            changed = False
            for key in data.keys():
# TODO: email probably shouldn't be here
                if key in ["role","groups","elements_owned","email"]:
                    result = col.update_one({
                                                "username": data['username']
                                            },
                                            {
                                                '$set':
                                                    {
                                                        key: data[key],
                                                        "last_modified": datetime.utcnow()
                                                    }
                                            })
                    if result.acknowledged:
                        changed = True

            if changed:
                return "Success", 200

            return "Bad Request", 400


    @ns_u.route('/update_password')
    class User_Update_Password(Resource):
        @api.doc(body='UserChange')
        @login_required
        def post(self):
            '''
            Change the user password
            '''
            client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
            col = client[USER_DB_NAME][USER_COL_NAME]
            data = json.loads(request.data)

            if flask_login.current_user.id is not data['username']:
                return "Bad Request", 400

            user = col.find_one({'username': data['username']}, {'_id':0})

            if user is None:
                return "Bad Request", 400

            if not data.has_key('password') or not data.has_key('new_password'):
                return "Bad Request", 400

            if pbkdf2_sha256.verify(data['password'], user['password_hash']):
                new_password_hash = pbkdf2_sha256.encrypt(data['new_password'])
                result = col.update_one({
                                            'username': data['username']
                                        },
                                        {
                                            '$set':
                                                {
                                                    'password_hash': new_password_hash,
                                                    'old_password_hash': user['password_hash'],
                                                    'last_modified': datetime.utcnow(),
                                                    'last_pw_modification': datetime.utcnow()
                                                }
                                        })
                if result.acknowledged:
                    return "Success", 200

            return "Bad Request", 400


    @ns_u.route('/protected')
    class Test_Protected(Resource):
        @login_required
        def get(self):
            '''
            Test endpoint
            '''
            return 'Logged in as: ' + flask_login.current_user.id


    @ns_u.route('/logout')
    class User_Logout(Resource):
        def get(self):
            '''
            Logout the current user
            '''
            flask_login.logout_user()
            return "Success", 200


if __name__ == '__main__':
    app.run()
