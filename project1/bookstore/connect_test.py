from pymongo import MongoClient
from fe.conf import MONGO_URI, MONGO_DB_NAME

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

   # 测试连接
print(db.list_collection_names())