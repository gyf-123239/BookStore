from pymongo import MongoClient
from be.model import db_conn
from datetime import datetime
from bson import ObjectId

class Order(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def cancel_order(self, order_id, end_status):
        try:
            order_query = {"_id": ObjectId(order_id)}
            order = self.new_order_collection.find_one_delete(order_query)
            if not order:
                return 404, f"Invalid order_id: {order_id}"

            # 构建订单信息
            order_info = {
                "order_id": str(order["_id"]),
                "user_id": order["user_id"],
                "store": order["store_id"],
                "total_price": order["total_price"],
                "order_time": order["order_time"],
                "status": end_status
            }


            # 删除订单详情
            detail_query = {"order_id": order_id}
            order_detail = self.new_order_detail_collection.find(detail_query)
            book = []
            for detail in order_detail:
                book = {
                    "book_id": detail["book_id"],
                "count": detail["count"]
                }
                if end_status == 0:
                    store_query = {
                        "store_id": order_info["store_id"],
                        "book_id": book["book_id"]
                    }
                    update_query = {
                            "$inc": {
                            "stock_level": book["count"]
                        }
                    }
                    result = self.store_collection.update_one(store_query, update_query)
                    if result.modified_count == 0:
                        return 404, f"Non-existent book_id: {book['book_id']} for store_id: {order_info['store_id']}"
                books.append(book)
            
            # 更新订单信息
            order_info["books"] = books
            return 200, "ok", order_info
        except Exception as e:
            return 528, f"Internal Server Error: {str(e)}"
