from pymongo import MongoClient
from be.model import db_conn
from be.model import error
from datetime import datetime, timedelta
from bson import ObjectId
import uuid
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from fe.conf import MONGO_URI, MONGO_DB_NAME

class Order(db_conn.DBConn):
    def __init__(self):
        # 初始化MongoDB连接
        self.client = MongoClient(MONGO_URI)
        self.db = self.client['bookstore']

    def new_order_cancel(self, user_id: str, order_id: str) -> (int, str):
        """
        取消订单的方法
        :param user_id: 用户ID
        :param order_id: 订单ID
        :return: 状态码和消息
        """
        store_id = ""
        price = ""
        # 查找未支付的订单
        new_order = self.db.new_orders.find_one({"order_id": order_id})
        
        # 处理未支付订单的取消
        if new_order is None:
            buyer_id = new_order["user_id"]
            if buyer_id != user_id:
                return error.error_authorization_fail()
            self.db.new_orders.delete_one({"order_id": order_id})
        else:
            # 处理已支付订单的取消
            new_order_paid = self.db.new_order_paid.find_one({"order_id": order_id})
            if new_order_paid:
                buyer_id = new_order_paid["user_id"]            

                if buyer_id != user_id:
                    return error.error_authorization_fail()
                
                # 获取订单相关信息
                store_id = new_order_paid["store_id"]
                price = new_order_paid["price"]

                # 查找卖家信息
                user_store = self.db.user_stores.find_one({"store_id": store_id})
                seller_id = user_store["user_id"]

                # 更新卖家余额（减少）
                condition = {"$inc":{"balance": -price}}
                seller = {"user_id": seller_id}
                self.db.users.update_one(seller, condition)

                # 更新买家余额（增加）
                buyer = {"user_id": buyer_id}
                condition = {"$inc": {"balance": price}}
                self.db.used.update_one(buyer, condition)

                # 删除已支付订单
                self.db.new_order_paid.delete_one({"order_id": order_id})
            else:
                return error.error_invalid_order_id(order_id)

        # 恢复书籍库存
        orders = self.db.new_order_details.find({"order_id": order_id})
        for order in orders:
            book_id = order["book_id"]
            count = order["count"]
            store_book = {"store_id": store_id, "book_id": book_id}
            condition = {"$inc": {"stock_level": count}}
            result = self.db.stores.update_one(store_book, condition)

        return 200, "ok"

    def check_order(self, user_id: str):
        """
        查询用户历史订单
        :param user_id: 用户ID
        :return: 状态码和消息
        """
        # 检查用户是否存在
        user = self.db.users.find_one({"user_id": user_id})
        if user is None:
            return error.error_non_exist_user_id(user_id)

        # 查询未付款订单
        user = {"user_id": user_id}
        new_orders = self.db.new_order_details.find(user)
        if new_orders:
            for new_order in new_orders:
                order_id = new_order["order_id"]
                order = {"order_id": order_id}
                new_order_details = self.db.new_order_details.find(order)

                if new_order_details is None:
                    return error.error_invalid_order_id(order_id)

        # 查询已付款订单
        new_orders_paid = self.db.new_order_paid.find(user)
        if new_orders_paid:
            for new_order_paid in new_orders_paid:
                order_id = new_order_paid["order_id"]
                order = {"order_id": order_id}
                new_order_details = self.db.new_order_details.find(order)
                if new_order_details is None:
                    return error.error_invalid_order_id(order_id)

        return 200, "ok"

    def check_order_status(self):
        """
        检查并取消超时订单
        """
        # 计算超时时间点
        timeout_datetime = datetime.now() - timedelta(seconds = 5)
        # 查找超时的订单
        condition = {"order_time": {"$lte": timeout_datetime}}
        orders = self.db.new_orders.find(condition)
        if orders is not None:
            for order in orders:
                order_id = order["order_id"]
                # 删除超时订单
                self.db.new_orders.delete_one({"order_id": order_id})

        return 200, "ok"

# 创建Order实例
b = Order()
# 设置定时任务
scheduler = BackgroundScheduler()
scheduler.add_job(b.check_order_status, 'interval',  seconds=5)
scheduler.start()