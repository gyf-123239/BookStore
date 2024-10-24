from flask import Blueprint
from flask import request
from flask import jsonify
from be.model.order import Order

bp_order = Blueprint("order", __name__, url_prefix="/order")


@bp_order.route("new_order_cancel/", methods=["POST"])
def new_order_cancel():
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")
    s = Order()
    code, message = s.new_order_cancel(user_id, order_id)
    return jsonify({"message": message}), code


@bp_order.route("/check_order", methods=["POST"])
def check_order():
    user_id: str = request.json.get("user_id")
    s = Order()
    code, message = s.check_order(user_id)
    return jsonify({"message": message}), code


@bp_order.route("check_order_status/", methods=["POST"])
def check_order_status():
    s = Order()
    code, message = s.check_order_status()
    return jsonify({"message": message}), code