"""db.py is a layer for interacting with the database across all of the bedrock apis."""
import pymongo
from CONSTANTS import *

def db_client():
    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    return client

def db_column(client, column_name):
    col = client[DATALOADER_DB_NAME][column_name]
    return col

def db_connect(column_name):
    client = db_client()
    column = db_column(client, column_name)
    return client, column
