import copy
from uuid import uuid4

from flask import jsonify, request, session
from sqlalchemy import desc, or_

import helper.trail as trail
from app.api import api
from app.extensions import db
from app.models.orders import Orders
from app.models.order_items import OrderItems, OrderNonvalItems
from app.models.items import Items, NonvalItems
from app.models.logs import OrderRejectLog
from helper.core import generate_order_id
from helper.endpoint import HTTPStatus, check_fields, check_api_permission, check_api_permissions
from helper.status import OrderStatusTransitionError, OrderStatus

def calculateTotal(orders):
    total = 0

    for order in orders:
        order_items = OrderItems.query.filter_by(order_id = order.id).all()
        order_nonval_items = OrderNonvalItems.query.filter_by(order_id = order.id).all()

        for item in order_items:
            item_data = Items.query.get(item.item_id)
            total += item_data.base_price * float(item.quantity)

        for item in order_nonval_items:
            item_data = NonvalItems.query.get(item.item_id)
            total += item_data.base_price * float(item.quantity)

    return total

# =================================
# STANDARD CRUD OPERATION ENDPOINTS
# =================================

@api.route('/orders', methods = ['GET'])
def api_get_orders():
    queryable_paramereters = ['period', 'division_id', 'created_by', 'status']
    filter_criteria = { key: request.args.get(key) for key in queryable_paramereters if request.args.get(key) is not None }

    if filter_criteria:
        orders = Orders.query.filter_by(**filter_criteria).all()
    else:
        orders = Orders.query.all()

    return jsonify([ order.to_dict() for order in orders ]), HTTPStatus.OK

@api.route('/order/<string:order_id>', methods = ['GET'])
def api_get_order(order_id):
    order = Orders.query.get(order_id)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    return jsonify(order.to_dict()), HTTPStatus.OK

@api.route('/order', methods = ['POST'])
@check_api_permission('order/create')
@check_fields('order/create')    
def api_create_order():
    period = request.form.get('period')
    division_id = request.form.get('division_id')
    created_by = request.form.get('created_by')

    active_order = Orders.query.filter(~Orders.status.in_([10, 99]), Orders.created_by == created_by).order_by(desc(Orders.created_date)).first()
    if active_order:
        return jsonify({ 'error': 'Active order exists', 'details': f"Active order already exists for {created_by}. Your currently active order: {active_order.id}" }), HTTPStatus.FORBIDDEN
    
    id = generate_order_id(period, division_id)

    order = Orders(id = id, period = period, division_id = division_id, created_by = created_by)
    
    try:
        db.session.add(order)
        db.session.commit()
        session['active_order'] = id
    except Exception as e:
        return jsonify({ 'error': 'Error while creating order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    trail.log_creation(order, created_by)
    return jsonify({ 'message': 'Order created successfully', 'order_details': order.to_dict() }), HTTPStatus.CREATED

@api.route('/order/<string:order_id>', methods = ['PATCH'])
@check_api_permission('order/update')
@check_fields('order/update')
def api_update_order(order_id):
    order = Orders.query.get(order_id)
    old_order = copy.deepcopy(order)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    order.period = request.form.get('period', order.period)
    order.division_id = request.form.get('division_id', order.division_id)
    
    try:
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while updating order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    trail.log_update(order, old_order, session.get('user'))
    return jsonify({ 'message': 'Order updated successfully', 'order_details': order.to_dict() }), HTTPStatus.OK

@api.route('/order/<string:order_id>', methods = ['DELETE'])
@check_api_permission('order/delete')
def api_delete_order(order_id):
    order = Orders.query.get(order_id)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    try:
        db.session.delete(order)
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while deleting order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    trail.log_deletion(order, session.get('user'))
    return jsonify({ 'message': 'Order deleted successfully' }), HTTPStatus.OK

# ==================================
# ORDER-SPECIFIC OPERATION ENDPOINTS
# ==================================

@api.route('/order/<string:order_id>/total', methods = ['GET'])
def api_get_order_total(order_id):
    order_items = OrderItems.query.filter_by(order_id = order_id).all()
    order_nonval_items = OrderNonvalItems.query.filter_by(order_id = order_id).all()

    total = 0

    for item in order_items:
        item_data = Items.query.get(item.item_id)
        total += item_data.base_price * float(item.quantity)

    for item in order_nonval_items:
        item_data = NonvalItems.query.get(item.item_id)
        total += item_data.base_price * float(item.quantity)

    return jsonify({ 'total': total }), HTTPStatus.OK

@api.route('/order/<string:order_id>/submit', methods = ['POST'])
@check_api_permission('order/submit')
def api_submit_order(order_id):
    order = Orders.query.get(order_id)
    old_order = copy.deepcopy(order)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    items = OrderItems.query.filter_by(order_id = order_id).all() + OrderNonvalItems.query.filter_by(order_id = order_id).all()
    if not items:
        return jsonify({ 'error': 'No items in order', 'details': 'Order must have at least one item to be submitted.' }), HTTPStatus.BAD_REQUEST
    
    try:
        order.submit()
        db.session.commit()
    except OrderStatusTransitionError as e:
        return jsonify({ 'error': 'Forbidden transition', 'details': f"{e}" }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({ 'error': 'Error while submitting order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    trail.log_update(order, old_order, session.get('user'))
    return jsonify({ 'message': 'Order submitted successfully' }), HTTPStatus.OK

@api.route('/order/<string:order_id>/cancel', methods = ['POST'])
@check_api_permission('order/cancel')
def api_cancel_order(order_id):
    order = Orders.query.get(order_id)
    old_order = copy.deepcopy(order)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    try:
        order.cancel()
        db.session.commit()
    except OrderStatusTransitionError as e:
        return jsonify({ 'error': 'Forbidden transition', 'details': f"{e}" }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({ 'error': 'Error while cancelling order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    trail.log_update(order, old_order, session.get('user'))
    return jsonify({ 'message': 'Order cancelled successfully', 'order_details': order.to_dict() }), HTTPStatus.OK

@api.route('/order/<string:order_id>/approve/<string:by>', methods = ['POST'])
@check_api_permissions([ 'order/approve_division', 'order/approve_finance' ])
@check_fields('order/approve')
def api_approve_order(order_id, by):
    order = Orders.query.get(order_id)
    old_order = copy.deepcopy(order)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    if order.is_approved(by):
        return jsonify({ 'error': 'Approval denied', 'details': f"Order has already been approved at {by} level." }), HTTPStatus.FORBIDDEN

    try:
        order.approve(by, request.form.get('username'))
        db.session.commit()
    except OrderStatusTransitionError as e:
        return jsonify({ 'error': 'Forbidden transition', 'details': f"{e}" }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({ 'error': 'Error while approving order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    trail.log_update(order, old_order, request.form.get('username'))
    return jsonify({ 'message': 'Order approved successfully' }), HTTPStatus.OK

@api.route('/order/<string:order_id>/reject/<string:by>', methods = ['POST'])
@check_api_permissions([ 'order/approve_division', 'order/approve_finance' ])
@check_fields('order/reject')
def api_reject_order(order_id, by):
    order = Orders.query.get(order_id)
    old_order = copy.deepcopy(order)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND

    try:
        order.reject(by, request.form.get('username'))
        log = OrderRejectLog(order_id = order_id, reason = request.form.get('reason'), user = request.form.get('username'), level = by, id = str(uuid4()))
        db.session.add(log)
        db.session.commit()
    except OrderStatusTransitionError as e:
        return jsonify({ 'error': 'Forbidden transition', 'details': f"{e}" }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({ 'error': 'Error while rejecting order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    trail.log_update(order, old_order, request.form.get('username'))
    return jsonify({ 'message': 'Order rejected successfully' }), HTTPStatus.OK

@api.route('/order/<string:order_id>/fulfill', methods = ['POST'])
@check_api_permission('order/fulfill')
def api_fulfill_order(order_id):
    order = Orders.query.get(order_id)
    old_order = copy.deepcopy(order)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND

    if order.is_fulfilled():
        return jsonify({ 'error': 'Fulfillment denied', 'details': 'Order has already been fulfilled.'}), HTTPStatus.FORBIDDEN
    
    try:
        order.fulfill()
        db.session.commit()
    except OrderStatusTransitionError as e:
        return jsonify({ 'error': 'Forbidden transition', 'details': f"{e}" }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({ 'error': 'Error while fulfilling order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    trail.log_update(order, old_order, session.get('user'))
    return jsonify({ 'message': 'Order fulfilled successfully' }), HTTPStatus.OK

# ==================================
# COMBINED ORDER OPERATION ENDPOINTS
# ==================================

@api.route('/order/<string:period>/<string:division_id>/total', methods = ['GET'])
def api_get_total_order(period, division_id):
    status = request.args.get('status')
    period = f"{period[:4]}/{period[4:]}"

    if status:
        orders = Orders.query.filter_by(period = period, division_id = division_id).filter(Orders.status >= status).all()
    else:
        orders = Orders.query.filter_by(period = period, division_id = division_id).all()

    total = calculateTotal(orders)
 
    return jsonify({ 'total': total }), HTTPStatus.OK

@api.route('/order/<string:period>/<string:division_id>/approve/<string:by>', methods = ['POST'])
@check_api_permissions([ 'order/approve_division', 'order/approve_finance' ])
@check_fields('order/approve')
def api_approve_orders(period, division_id, by):
    period = f"{period[:4]}/{period[4:]}"
    if by not in ['division', 'finance']:
        return jsonify({ 'error': 'Invalid approval level', 'details': 'Approval level must be either division or finance.' }), HTTPStatus.BAD_REQUEST
    
    orders = Orders.query.filter_by(period = period, division_id = division_id).all()

    if by == 'finance':
        reject_ids = [ order.id for order in orders if not order.is_approved('division') ]
        if reject_ids:
            return jsonify({ 'error': 'Some orders not approved at division level', 
                            'details': f"Orders {', '.join(reject_ids)} are not at division approved state. Please resolve all conflicts before proceeding." }), HTTPStatus.FORBIDDEN
    elif by == 'division':
        reject_ids = [ order.id for order in orders if not order.status in [1, 6] ]
        if reject_ids:
            return jsonify({ 'error': 'Some orders not submitted', 
                            'details': f"Orders {', '.join(reject_ids)} are not yet submitted or have gone beyond submission level. Please resolve all conflicts before proceeding." }), HTTPStatus.FORBIDDEN

    old_orders = []
    for order in orders:
        old_order = copy.deepcopy(order)
        old_orders.append(old_order)
        order.approve(by, request.form.get('username'))
    
    try:
        db.session.commit()
    except OrderStatusTransitionError as e:
        return jsonify({ 'error': 'Forbidden transition', 'details': f"{e}" }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({ 'error': 'Error while approving order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    for order, old_order in zip(orders, old_orders):
        trail.log_update(order, old_order, request.form.get('username'))

    return jsonify({ 'message': 'Orders approved successfully' }), HTTPStatus.OK

@api.route('/order/<string:period>/<string:division_id>/reject/<string:by>', methods = ['POST'])
@check_api_permissions([ 'order/approve_division', 'order/approve_finance' ])
@check_fields('order/reject')
def api_reject_orders(period, division_id, by):
    period = f"{period[:4]}/{period[4:]}"
    if by not in ['division', 'finance']:
        return jsonify({ 'error': 'Invalid rejection level', 'details': 'Rejection level must be either division or finance.' }), HTTPStatus.BAD_REQUEST
    
    orders = Orders.query.filter_by(period = period, division_id = division_id).all()

    if by == 'finance':
        reject_ids = [ order.id for order in orders if not order.is_approved('division') ]
        if reject_ids:
            return jsonify({ 'error': 'Some orders not approved at division level', 
                            'details': f"Orders {', '.join(reject_ids)} are not at division approved level. Please resolve all conflicts before proceeding." }), HTTPStatus.FORBIDDEN
    elif by == 'division':
        reject_ids = [ order.id for order in orders if not order.status in [1, 6] ]
        if reject_ids:
            return jsonify({ 'error': 'Some orders not submitted', 
                            'details': f"Orders {', '.join(reject_ids)} are not yet submitted or have gone beyond submission level. Please resolve all conflicts before proceeding." }), HTTPStatus.FORBIDDEN

    logs = []
    old_orders = []
    for order in orders:
        old_order = copy.deepcopy(order)
        old_orders.append(old_order)
        
        order.reject(by, request.form.get('username'))

        log = OrderRejectLog(order_id = order.id, reason = request.form.get('reason'), user = request.form.get('username'), level = by, id = str(uuid4()))
        logs.append(log)
    
    try:
        db.session.add_all(logs)
        db.session.commit()
    except OrderStatusTransitionError as e:
        return jsonify({ 'error': 'Forbidden transition', 'details': f"{e}" }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({ 'error': 'Error while rejecting order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    for order, old_order in zip(orders, old_orders):
        print(order, old_order)
        trail.log_update(order, old_order, request.form.get('username'))
    
    return jsonify({ 'message': 'Orders rejected successfully' }), HTTPStatus.OK

@api.route('/order/<string:period>/<string:division_id>/fulfill', methods = ['POST'])
@check_api_permission('order/fulfill')
def api_fulfill_orders(period, division_id):
    period = f"{period[:4]}/{period[4:]}"
    orders = Orders.query.filter_by(period = period, division_id = division_id).all()

    reject_ids = [ order.id for order in orders if not order.is_approved('finance') ]
    if reject_ids:
        return jsonify({ 'error': 'Some orders not approved at finance level', 
                        'details': f"Orders {', '.join(reject_ids)} are not approved at finance level. Please resolve all conflicts before proceeding." }), HTTPStatus.FORBIDDEN

    old_orders = []
    for order in orders:
        old_order = copy.deepcopy(order)
        old_orders.append(old_order)
        order.fulfill()
    
    try:
        db.session.commit()
    except OrderStatusTransitionError as e:
        return jsonify({ 'error': 'Forbidden transition', 'details': f"{e}" }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({ 'error': 'Error while fulfilling order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    for order, old_order in zip(orders, old_orders):
        trail.log_update(order, old_order, session.get('user'))
    
    return jsonify({ 'message': 'Orders fulfilled successfully' }), HTTPStatus.OK

# =========================
# PERIOD SPECIFIC ENDPOINTS
# =========================

@api.route('/procurement/<string:period>/total', methods = ['GET'])
def api_get_total_procurement(period):
    period = f"{period[:4]}/{period[4:]}"

    orders = Orders.query.filter_by(period = period).filter(Orders.status >= OrderStatus.FINANCE_APPROVED).all()
    total = calculateTotal(orders)

    return jsonify({ 'total': total }), HTTPStatus.OK