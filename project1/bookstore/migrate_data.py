import sqlite3
from pymongo import MongoClient
from fe.conf import MONGO_URI
import json

# 连接到SQLite数据库
sqlite_conn = sqlite3.connect('bookstore/fe/data/book.db')
sqlite_cursor = sqlite_conn.cursor()

# 连接到MongoDB
# mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client['bookstore']
mongo_collection = mongo_db['books']

# 从SQLite读取数据
sqlite_cursor.execute("SELECT * FROM book")
books = sqlite_cursor.fetchall()

# 获取列名
columns = [description[0] for description in sqlite_cursor.description]

# 将数据转换为字典并插入MongoDB
for book in books:
    book_dict = dict(zip(columns, book))
    
    # 处理BLOB类型的picture字段
    if 'picture' in book_dict and book_dict['picture']:
        book_dict['picture'] = str(book_dict['picture'])
    
    mongo_collection.insert_one(book_dict)

print(f"已成功迁移 {len(books)} 条记录到MongoDB。")

# 关闭连接
sqlite_conn.close()
mongo_client.close()