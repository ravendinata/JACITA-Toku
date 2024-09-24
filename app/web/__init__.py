from flask import Blueprint

web = Blueprint('web', __name__)

from app.web import routes_main, routes_user, routes_item, routes_order