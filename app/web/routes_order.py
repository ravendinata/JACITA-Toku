from flask import render_template, session
from sqlalchemy import desc

from app.web import web
from app.models.orders import Orders
from app.models.user import User
from helper.auth import check_login
from helper.role import InsufficientPermissionError
from helper.status import OrderStatus

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

    # Append GMT to the dates
    order.created_date = order.created_date.strftime('%Y-%m-%d %H:%M:%S GMT')
    order.last_modification_date = order.last_modification_date.strftime('%Y-%m-%d %H:%M:%S GMT') if order.last_modification_date is not None else None
    order.approval_division_date = order.approval_division_date.strftime('%Y-%m-%d %H:%M:%S GMT') if order.approval_division_date is not None else None
    order.approval_finance_date = order.approval_finance_date.strftime('%Y-%m-%d %H:%M:%S GMT') if order.approval_finance_date is not None else None
    order.fulfillment_date = order.fulfillment_date.strftime('%Y-%m-%d %H:%M:%S GMT') if order.fulfillment_date is not None else None

    user = User.query.get(session['user'])

    can_do = {}

    def check_permission(action):
        try:
            return user.can_do(action)
        except InsufficientPermissionError:
            return False
    
    # Initialize can_do dictionary
    can_do = {
        'order/update': False,
        'orderitem/create': False,
        'orderitem/update': False,
        'order/approve_division': False,
        'order/approve_finance': False,
        'order/fulfill': False
    }
    
    # Check permissions based on order status
    if order.status in [OrderStatus.PENDING, OrderStatus.DIVISION_REJECTED]:
        can_do['order/update'] = check_permission('order/update')
        can_do['orderitem/create'] = check_permission('orderitem/create')
        can_do['orderitem/update'] = check_permission('orderitem/update')
    
    if order.status in [OrderStatus.SUBMITTED,  OrderStatus.FINANCE_REJECTED]:
        can_do['order/approve_division'] = check_permission('order/approve_division')
        can_do['orderitem/update'] = check_permission('orderitem/update')
    
    if order.status == OrderStatus.DIVISION_APPROVED:
        can_do['order/approve_finance'] = check_permission('order/approve_finance')
    
    if order.status == OrderStatus.FINANCE_APPROVED:
        can_do['order/fulfill'] = check_permission('order/fulfill')

    return render_template('orders/detail.html', use_datatables = True, title = "View Order", order = order, can_do = can_do)