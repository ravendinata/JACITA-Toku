from flask import Blueprint

api = Blueprint('api', __name__)

from app.api import routes_misc, routes_order, routes_item, routes_order_items, routes_user