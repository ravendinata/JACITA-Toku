from flask import render_template, session
from sqlalchemy import asc, desc, or_

import helper.periods as periods
from app.web import web
from app.models.logs import OrderRejectLog
from app.models.orders import Orders
from app.models.user import User
from helper.auth import check_login
from helper.endpoint import HTTPStatus, check_page_permission
from helper.role import InsufficientPermissionError, Role
from helper.status import OrderStatus

@web.route('/orders')
@check_login
@check_page_permission('order/create')
def page_order_list():
    username = session['user']
    active_order = Orders.query.get(session['active_order']) if 'active_order' in session else None
    past_orders = Orders.query.filter(Orders.status.in_([10, 99]), Orders.created_by == username).order_by(desc(Orders.created_date)).all()

    user = User.query.get(username).to_dict()
    division = user['division']

    return render_template('orders/view_all.html', use_datatables = True, title = "My Orders", available_periods = periods.get_available_periods(),
                           active_order = active_order, past_orders = past_orders, division = division)

@web.route('/orders/administration')
@check_login
@check_page_permission('order/administer')
def page_order_administration():
    user = User.query.get(session['user'])
    this_month = periods.get_current_month()
    next_month = periods.get_next_month()

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
        orders = Orders.query.filter(Orders.status == OrderStatus.DIVISION_APPROVED,
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

@web.route('/orders/history')
@check_login
@check_page_permission('order/administer')
def page_order_history():
    return render_template('orders/history.html', use_datatables = True, title = "Order History")

@web.route('/order/<string:id>')
@check_login
def page_order_view(id):
    order = Orders.query.get(id)
    if order is None:
        return render_template('error/standard.html', title = "Not Found", code = HTTPStatus.NOT_FOUND, message = "Order not found."), HTTPStatus.NOT_FOUND

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
        'order/fulfill': False,
        'order/cancel': False
    }
    
    # Check permissions based on order status
    if order.status in [OrderStatus.PENDING, OrderStatus.DIVISION_REJECTED]:
        can_do['order/update'] = check_permission('order/update')
        can_do['orderitem/create'] = check_permission('orderitem/create')
        can_do['orderitem/update'] = check_permission('orderitem/update')
        can_do['order/cancel'] = check_permission('order/cancel')
    
    if order.status in [OrderStatus.SUBMITTED,  OrderStatus.FINANCE_REJECTED]:
        can_do['order/approve_division'] = check_permission('order/approve_division')
        can_do['orderitem/update'] = check_permission('orderitem/update')
    
    if order.status == OrderStatus.DIVISION_APPROVED:
        can_do['order/approve_finance'] = check_permission('order/approve_finance')
    
    if order.status == OrderStatus.FINANCE_APPROVED:
        can_do['order/fulfill'] = check_permission('order/fulfill')
        can_do['order/cancel'] = check_permission('order/cancel')
        if user.role in [Role.DIVISION_LEADER, Role.DIVISION_USER]:
            can_do['order/cancel'] = False

    active_order = session['active_order'] if 'active_order' in session else None
    if order.id != active_order and user.role not in [Role.ADMINISTRATOR, Role.DIVISION_LEADER]:
        can_do['orderitem/update'] = False

    if order.status in [OrderStatus.DIVISION_REJECTED, OrderStatus.FINANCE_REJECTED]:
        latest_rejection = OrderRejectLog.query.filter(OrderRejectLog.order_id == id).order_by(desc(OrderRejectLog.date)).first()

    try:
        reject_reason = latest_rejection.reason if order.status in [OrderStatus.DIVISION_REJECTED, OrderStatus.FINANCE_REJECTED] else None
    except AttributeError:
        reject_reason = None
        return render_template('error/standard.html', title = "Database Error", code = HTTPStatus.INTERNAL_SERVER_ERROR,
                               message = "Order is rejected but system has failed to retrieve rejection reason. Please contact Administrator."), HTTPStatus.INTERNAL_SERVER_ERROR

    return render_template('orders/detail.html', use_datatables = True, title = "View Order", order = order, 
                           can_do = can_do, reject_reason = reject_reason)

@web.route('/order/<string:period>/<int:division_id>')
@check_login
def page_division_order_view(period, division_id):
    period = f"{period[:4]}/{period[4:]}"
    orders = Orders.query.filter(Orders.period == period, Orders.division_id == division_id).order_by(desc(Orders.last_modification_date)).all()

    if len(orders) == 0:
        return render_template('error/standard.html', title = "Not Found", code = HTTPStatus.NOT_FOUND, message = "Order not found."), HTTPStatus.NOT_FOUND
    
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

    division = { 'id': division_id, 'name': orders[0].get_division() }

    return render_template('orders/collection_detail.html', use_datatables = True, title = "Division Orders", can_do = can_do, sync = sync,
                           orders = orders, period = period, division = division, last_modification_date = orders[0].last_modification_date)

@web.route('/procurement/<string:period>')
@check_login
@check_page_permission('order/fulfill')
def page_procurement_order_view(period):
    period = f"{period[:4]}/{period[4:]}"
    orders = Orders.query.filter(Orders.period == period, Orders.status > 6)\
            .order_by(asc(Orders.division_id), desc(Orders.last_modification_date))\
            .all()
    
    if len(orders) == 0:
        return render_template('error/standard.html', title = "Not Found", code = HTTPStatus.NOT_FOUND, message = "Order not found."), HTTPStatus.NOT_FOUND

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

    return render_template('orders/procurement_view.html', use_datatables = True, title = "Procurement Orders", can_fulfill = can_fulfill, sync = sync,
                           orders = grouped_orders, period = period, division = divisions, last_modification_date = orders[0].last_modification_date)