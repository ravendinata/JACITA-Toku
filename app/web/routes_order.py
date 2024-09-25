from flask import render_template, session
from sqlalchemy import desc

from app.web import web
from app.models.orders import Orders
from app.models.user import User
from helper.auth import check_login

@web.route('/orders')
@check_login
def page_order_list():
    username = session['user']
    active_order = Orders.query.get(session['active_order']) if 'active_order' in session else None
    past_orders = Orders.query.filter(Orders.status.in_([10, 99]), Orders.created_by == username).order_by(desc(Orders.created_date)).all()

    user = User.query.get(username).to_dict()
    division = user['division']

    return render_template('orders/view_all.html', use_datatables = True, title = "My Orders",
                           active_order = active_order, past_orders = past_orders, division = division)

@web.route('/order/<string:id>')
@check_login
def page_order_view(id):
    order = Orders.query.get(id)
    if order is None:
        return render_template('error/standard.html', title = "Not Found", code = 404, message = "Order not found."), 404

    return render_template('orders/detail.html', use_datatables = True, title = "View Order", order = order)