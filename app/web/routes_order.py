from datetime import datetime

from flask import render_template, session
from sqlalchemy import asc, desc, or_

from app.web import web
from app.models.orders import Orders
from app.models.user import User
from helper.auth import check_login
from helper.endpoint import check_page_permission
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

@web.route('/orders/administration')
@check_login
@check_page_permission('order/administer')
def page_order_administration():
    user = User.query.get(session['user'])
    this_month = f"{datetime.now().year}/{datetime.now().month:02d}"
    if datetime.now().month == 12:
        next_month = f"{datetime.now().year + 1}/01"
    else:
        next_month = f"{datetime.now().year}/{datetime.now().month + 1:02d}"

    can_do = {
        'order/approve_division': False,
        'order/approve_finance': False,
        'order/fulfill': False
    }

    for action in can_do:
        try:
            can_do[action] = user.can_do(action)
        except InsufficientPermissionError:
            can_do[action] = False

    if can_do['order/approve_division']:
        orders = Orders.query.filter(Orders.status != OrderStatus.PENDING, or_(Orders.period == this_month, Orders.period == next_month),
                                     Orders.division_id == user.division_id).order_by(asc(Orders.period)).all()
        
        grouped_orders = {}
        for order in orders:
            if order.period not in grouped_orders:
                grouped_orders[order.period] = []
            grouped_orders[order.period].append(order)
        
        return render_template('orders/administration.html', use_datatables = True, title = "Order Administration", 
                           period = {'this_month': this_month, 'next_month': next_month},
                           orders = grouped_orders, can_do = can_do, division = user.division_id)
    
    if can_do['order/approve_finance']:
        orders = Orders.query.filter(or_(Orders.status == OrderStatus.DIVISION_APPROVED, Orders.status == OrderStatus.FINANCE_REJECTED),
                                     or_(Orders.period == this_month, Orders.period == next_month)).order_by(asc(Orders.period)).all()
    elif can_do['order/fulfill']:
        orders = Orders.query.filter(Orders.status == OrderStatus.FINANCE_APPROVED, 
                                     or_(Orders.period == this_month, Orders.period == next_month)).order_by(asc(Orders.period)).all()
        
    grouped_orders = {}
    for order in orders:
        period = order.period
        division = order.get_division()

        if period not in grouped_orders:
            grouped_orders[period] = {}

        if division not in grouped_orders[period]:
            grouped_orders[period][division] = []

        grouped_orders[period][division].append(order)

    return render_template('orders/administration.html', use_datatables = True, title = "Order Administration",
                            period = {'this_month': this_month, 'next_month': next_month},
                            grouped_orders = grouped_orders, can_do = can_do)

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

@web.route('/order/<string:period>/<int:division_id>')
@check_login
def page_division_order_view(period, division_id):
    period = f"{period[:4]}/{period[4:]}"
    orders = Orders.query.filter(Orders.period == period, Orders.division_id == division_id).order_by(desc(Orders.created_date)).all()

    if len(orders) == 0:
        return render_template('error/standard.html', title = "Not Found", code = 404, message = "Order not found."), 404
    
    user = User.query.get(session['user'])
    
    can_do = {
        'orderitem/delete': False,
        'order/approve_division': False,
        'order/approve_finance': False,
        'order/fulfill': False
    }

    sync = len(set([order.status for order in orders])) == 1

    def check_permission(action):
        try:
            return user.can_do(action)
        except InsufficientPermissionError:
            return False
        
    if sync:
        status = orders[0].status
        
        if status in [OrderStatus.PENDING, OrderStatus.DIVISION_REJECTED]:
            can_do['orderitem/delete'] = check_permission('orderitem/delete')
        
        if status in [OrderStatus.SUBMITTED,  OrderStatus.FINANCE_REJECTED]:
            can_do['order/approve_division'] = check_permission('order/approve_division')
            can_do['orderitem/delete'] = check_permission('orderitem/delete')
        
        if status == OrderStatus.DIVISION_APPROVED:
            can_do['order/approve_finance'] = check_permission('order/approve_finance')
        
        if status == OrderStatus.FINANCE_APPROVED:
            can_do['order/fulfill'] = check_permission('order/fulfill')

    division = {'id': division_id, 'name': orders[0].get_division()}

    return render_template('orders/collection_detail.html', use_datatables = True, title = "Division Orders", can_do = can_do, sync = sync,
                           orders = orders, period = period, division = division, last_modification_date = orders[0].last_modification_date)

@web.route('/procurement/<string:period>')
@check_login
@check_page_permission('order/fulfill')
def page_procurement_order_view(period):
    period = f"{period[:4]}/{period[4:]}"
    orders = Orders.query.filter(Orders.period == period)\
            .order_by(asc(Orders.division_id), desc(Orders.last_modification_date))\
            .all()
    
    if len(orders) == 0:
        return render_template('error/standard.html', title = "Not Found", code = 404, message = "Order not found."), 404

    divisions = {}
    for order in orders:
        division = order.get_division()
        if division not in divisions:
            divisions[division] = order.division_id

    grouped_orders = {}
    for order in orders:
        division = order.get_division()
        if division not in grouped_orders:
            grouped_orders[division] = []
        grouped_orders[division].append(order)

    statuses = [order.status for order in orders]
    sync = len(set(statuses)) == 1
    can_fulfill = True if sync and OrderStatus.FINANCE_APPROVED in statuses else False

    print(sync, can_fulfill)

    return render_template('orders/procurement_view.html', use_datatables = True, title = "Procurement Orders", can_fulfill = can_fulfill, sync = sync,
                           orders = grouped_orders, period = period, division = divisions, last_modification_date = orders[0].last_modification_date)