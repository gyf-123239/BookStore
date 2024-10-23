from be.model import store
from pymongo import MongoClient
from fe.conf import MONGO_URI, MONGO_DB_NAME

class DBConn:
    def __init__(self):
        # self.conn = store.get_db_conn()
        self.client = MongoClient(MONGO_URI)
        self.db = self.client['bookstore']
        self.book_collection = self.db['books']
        self.user_collection = self.db['user']
        self.store_collection = self.db['store']
        self.user_store_collection = self.db['user_store']
        self.order_collection = self.db['order']
        self.new_order_collection = self.db['new_order']
        self.new_order_detail_collection = self.db['new_order_detail']
        

    def user_id_exist(self, user_id):
        user = self.user_collection.find_one({"user_id": user_id})
        return user is not None

    def book_id_exist(self, store_id, book_id):
        book = self.store_collection.find_one({"store_id":store_id,"book_id": book_id})
        return book is not None

    def store_id_exist(self, store_id):
        store = self.user_store_collection.find_one({"store_id": store_id})
        return store is not None


    def order_id_exist(self, order_id):
        order = self.order_collection.find_one({"order_id": order_id})
        return order is not None

        

    # def user_id_exist(self, user_id):
    #     cursor = self.conn.execute(
    #         "SELECT user_id FROM user WHERE user_id = ?;", (user_id,)
    #     )
    #     row = cursor.fetchone()
    #     if row is None:
    #         return False
    #     else:
    #         return True

    # def book_id_exist(self, store_id, book_id):
    #     cursor = self.conn.execute(
    #         "SELECT book_id FROM store WHERE store_id = ? AND book_id = ?;",
    #         (store_id, book_id),
    #     )
    #     row = cursor.fetchone()
    #     if row is None:
    #         return False
    #     else:
    #         return True

    # def store_id_exist(self, store_id):
    #     cursor = self.conn.execute(
    #         "SELECT store_id FROM user_store WHERE store_id = ?;", (store_id,)
    #     )
    #     row = cursor.fetchone()
    #     if row is None:
    #         return False
    #     else:
    #         return True
        