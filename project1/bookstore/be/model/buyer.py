import sqlite3 as sqlite
import uuid
import json
import logging
from be.model import db_conn
from be.model import error
from be.model.order import Order


class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)
    
    def search_book(self, key: str, page = 0) -> (int,str,list):
        try:
            if page > 0:
                size = 10
                skip = (page - 1)*size
                results = self.collection_books.find({'$text': {'$search': key}}).skip(skip).limit(size)

            else:
                results = self.collection_books.find({'$text': {'$search': key}})


            result = []
            for row in results:
                book =  {
                    "id":row['id'],
                    "title": row['title'],
                    "author": row['author']
                }
                result.append(book)
                
        except Exception as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""

        return 200, "ok", result

    def search_book_in_store(self, store_id: int, key: str) -> (int,str,list):
        try: 
            store_book = self.collection_stores.find({"store_id": store_id})
            
            all_book = self.collection_books.find({'$text': {'$search': key}})
            result = []
            for s_b in store_book:
                for a_b in all_book:
                    if s_b['book_id'] == a_b['id']:
                        book =  {
                            "id":a_b['id'],
                            "title": a_b['title'],
                            "author": a_b['author']
                        }
                        result.append(book)
    
                
        except Exception as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""

        return 200, "ok", result

    def check_user(self, user_id):
        user = self.collection_users.find({"user_id": user_id}, {"user_id": 1})

        if user is None:
            return False
        else:
            return True

        # 测试是否存在user

    def check_store(self, store_id):
        store = self.collection_users.find_one({"store_id": store_id}, {"store_id": 1})

        if store is None:
            return False
        else:
            return True
        


    def add_money(self, user_id, password, add_value):
        user = self.user_collection.find_one({"user_id": user_id}, {"password": password    })
        if user is None:
            return error.error_authorization_fail()
        if user["password"] != password:
            return error.error_authorization_fail()
        self.user_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": add_value}}
        )
        return 200, "ok"
    
    def new_order(
        self, user_id: str, store_id: str, id_and_count: [(str, int)]
    ) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

            for book_id, count in id_and_count:
                cursor = self.store_collection.find_one({"store_id": store_id, "book_id": book_id})
                if not cursor:
                    return error.error_non_exist_book_id(book_id) + (order_id,)
                stock_level = cursor["stock_level"]
                book_info = cursor["book_info"] 
                book_info_json = json.loads(book_info)
                price = book_info_json.get("price")

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)


                updated = self.store_collection.update_one(
                    {"store_id": store_id, "book_id": book_id},
                    {"$inc": {"stock_level": -count}}
                )
                if updated.modified_count == 0:
                    return error.error_stock_level_low(book_id) + (order_id,)
                self.new_order_detail_collection.insert_one({
                    "order_id": uid,
                    "book_id": book_id,
                    "count": count,
                    "price": price
                })



            self.order_collection.insert_one({
                "order_id": uid,
                "store_id": store_id,
                "user_id": user_id,
                "id_and_count": [{'book_id': book_id, 'count': count} for book_id, count in id_and_count],
                "status": '未发货'
            }) 
            self.new_order_collection.delete_one({
                "order_id": uid,
                "store_id": store_id,
                "user_id": user_id
                })
            order_id = uid

        except Exception as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        conn = self.conn
        try:
            order = self.order_collection.find_one({"order_id": order_id})
            if not order:
                return error.error_invalid_order_id(order_id)
            order_id = order["order_id"]
            buyer_id = order["user_id"]
            store_id = order["store_id"]


            if buyer_id != user_id:
                return error.error_authorization_fail()

            buyer = self.user_collection.find_one({"user_id": buyer_id})
            if not buyer:
                return error.error_non_exist_user_id(buyer_id)
            balance = buyer["balance"]

            if password != buyer["password"]:
                return error.error_authorization_fail()

            store = self.user_store_collection.find_one({"store_id": store_id})
            if not store:
                return error.error_non_exist_store_id(store_id)
            seller_id = store["user_id"]



            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            order_detail = self.new_order_detail_collection.find({"order_id": order_id})
            total_price = 0
            for detail in order_detail:
                count = detail["count"]
                price = detail["price"]
                total_price += count * price

            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)

            updated = self.user_collection.update_one(
                {"user_id": buyer_id, "balance": {"$gte": total_price}},
                {"$inc": {"balance": -total_price}}
            )
            if updated.modified_count == 0:
                return error.error_not_sufficient_funds(order_id)

            updated = self.user_collection.update_one(  
                {"user_id": seller_id},
                {"$inc": {"balance": total_price}}
            )
            if updated.modified_count == 0:
                return error.error_non_exist_user_id(seller_id)


            deleted_order = self.new_order_collection.delete_one({"order_id": order_id})
            if deleted_order.deleted_count == 0:
                return error.error_invalid_order_id(order_id)


            # conn.commit()
            deleted_order_detail = self.new_order_detail_collection.delete_many({"order_id": order_id})
            if deleted_order_detail.deleted_count == 0:
                return error.error_invalid_order_id(order_id)

        except Exception as e:
            return 528, "{}".format(str(e))

        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            user = self.user_collection.find_one({"user_id": user_id})
            if user is None:
                return error.error_non_exist_user_id()
            if user["password"] != password:
                return error.error_authorization_fail()
            
            updated = self.user_collection.update_one(
                {"user_id": user_id},
                {"$inc": {"balance": add_value}}
            )
            if updated.modified_count == 0:
                return error.error_non_exist_user_id(user_id)   

        except Exception as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"
    # def cancel_order(self, buyer_id, order_id) -> (int, str):
    #     try:
    #         order = self.order_collection.find_one({"order_id": order_id})
    #         if not order:
    #             return error.error_invalid_order_id(order_id)
    #         if not self.user_id_exist(buyer_id):
    #             return error.error_non_exist_user_id(buyer_id)
    #         if not self.order_id_exist(order_id):
    #             return error.error_invalid_order_id(order_id)
            
    #         # delete_unpaid_order(order_id)
    #         # o = Order()
    #         # o.cancel_order(order_id)

    #     except Exception as e:
    #         return 528, "{}".format(str(e))
    #     except BaseException as e:
    #         return 530,"{}".format(str(e))
    #     return 200, "ok"
