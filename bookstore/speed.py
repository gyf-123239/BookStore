# 建立索引
from pymongo import MongoClient
from fe.conf import MONGO_URI


client = MongoClient(MONGO_URI)
db = client['bookstore']

user_collection = db['user']
user_collection.create_index([('user_id', 1)])

book_collection = db['book']
book_collection.create_index([('title', 1)])

store_collection = db['store']
store_collection.create_index([('store_id', 1)])

client.close()