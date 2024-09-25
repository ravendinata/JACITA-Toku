from flask import render_template, session

from app.web import web
from app.models.orders import Orders
from helper.auth import check_login

@web.route('/order/<string:id>')
@check_login
def page_order_view(id):
    order = Orders.query.get(id)
    if order is None:
        return render_template('error/standard.html', title = "Not Found", code = 404, message = "Order not found."), 404

    return render_template('orders/detail.html', use_datatables = True, title = "View Order", order = order)