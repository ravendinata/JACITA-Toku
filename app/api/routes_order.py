from flask import jsonify, request

from app.api import api
from app.extensions import db
from app.models.orders import Orders
from helper.core import generate_order_id
from helper.endpoint import HTTPStatus, check_fields
from helper.status import OrderStatusTransitionError

# =================================
# STANDARD CRUD OPERATION ENDPOINTS
# =================================

@api.route('/orders', methods = ['GET'])
def api_get_orders():
    orders = Orders.query.all()
    return jsonify([ order.to_dict() for order in orders ]), HTTPStatus.OK

@api.route('/order/<string:order_id>', methods = ['GET'])
def api_get_order(order_id):
    order = Orders.query.get(order_id)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    return jsonify(order.to_dict()), HTTPStatus.OK

@api.route('/order', methods = ['POST'])
def api_create_order():
    check_field = check_fields(request, 'order/create')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST
    
    period = request.form.get('period')
    division_id = request.form.get('division_id')
    created_by = request.form.get('created_by')
    
    id = generate_order_id(period, division_id)

    order = Orders(id = id, period = period, division_id = division_id, created_by = created_by)
    
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while creating order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Order created successfully', 'order_details': order.to_dict() }), HTTPStatus.CREATED

@api.route('/order/<string:order_id>', methods = ['PATCH'])
def api_update_order(order_id):
    check_field = check_fields(request, 'order/update')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST

    order = Orders.query.get(order_id)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    order.period = request.form.get('period', order.period)
    order.division_id = request.form.get('division_id', order.division_id)
    
    try:
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while updating order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Order updated successfully', 'order_details': order.to_dict() }), HTTPStatus.OK

@api.route('/order/<string:order_id>', methods = ['DELETE'])
def api_delete_order(order_id):
    order = Orders.query.get(order_id)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    try:
        db.session.delete(order)
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while deleting order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Order deleted successfully' }), HTTPStatus.NO_CONTENT

# ==================================
# ORDER-SPECIFIC OPERATION ENDPOINTS
# ==================================

@api.route('/order/<string:order_id>/submit', methods = ['POST'])
def api_submit_order(order_id):
    order = Orders.query.get(order_id)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    try:
        order.submit()
        db.session.commit()
    except OrderStatusTransitionError as e:
        return jsonify({ 'error': 'Forbidden transition', 'details': f"{e}" }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({ 'error': 'Error while submitting order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Order submitted successfully' }), HTTPStatus.OK

@api.route('/order/<string:order_id>/cancel', methods = ['POST'])
def api_cancel_order(order_id):
    order = Orders.query.get(order_id)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    try:
        order.cancel()
        db.session.commit()
    except OrderStatusTransitionError as e:
        return jsonify({ 'error': 'Forbidden transition', 'details': f"{e}" }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({ 'error': 'Error while cancelling order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Order cancelled successfully', 'order_details': order.to_dict() }), HTTPStatus.OK

@api.route('/order/<string:order_id>/approve/<string:by>', methods = ['POST'])
def api_approve_order(order_id, by):
    check_field = check_fields(request, 'order/approve')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST
    
    order = Orders.query.get(order_id)
    
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
    
    return jsonify({ 'message': 'Order approved successfully' }), HTTPStatus.OK

@api.route('/order/<string:order_id>/reject/<string:by>', methods = ['POST'])
def api_reject_order(order_id, by):
    check_field = check_fields(request, 'order/reject')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST
    
    order = Orders.query.get(order_id)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND

    try:
        order.reject(by, request.form.get('username'))
        db.session.commit()
    except OrderStatusTransitionError as e:
        return jsonify({ 'error': 'Forbidden transition', 'details': f"{e}" }), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({ 'error': 'Error while rejecting order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Order rejected successfully' }), HTTPStatus.OK

@api.route('/order/<string:order_id>/fulfill', methods = ['POST'])
def api_fulfill_order(order_id):
    order = Orders.query.get(order_id)
    
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
    
    return jsonify({ 'message': 'Order fulfilled successfully' }), HTTPStatus.OK