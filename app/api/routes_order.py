from flask import jsonify, request

from app.api import api
from app.extensions import db
from app.models.orders import Orders
from helper.core import generate_order_id

@api.route('/orders', methods = ['GET'])
def api_get_orders():
    orders = Orders.query.all()
    return jsonify([ order.to_dict() for order in orders ])

@api.route('/order/<string:order_id>', methods = ['GET'])
def api_get_order(order_id):
    order = Orders.query.get(order_id)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), 404
    
    return jsonify(order.to_dict())

@api.route('/order', methods = ['POST'])
def api_create_order():
    required_fields = ['period', 'division_id', 'created_by']
    if not all([ field in request.form for field in required_fields ]):
        return jsonify({ 'error': 'Missing required fields', 'required_fields': required_fields }), 400
    
    period = request.form.get('period')
    division_id = request.form.get('division_id')
    created_by = request.form.get('created_by')
    
    id = generate_order_id(period, division_id)

    order = Orders(id = id, period = period, division_id = division_id, created_by = created_by)
    
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while creating order', 'details': f"{e}" }), 500
    
    return jsonify({ 'message': 'Order created successfully', 'order_details': order.to_dict() })

@api.route('/order/<string:order_id>', methods = ['PATCH'])
def api_update_order(order_id):
    order = Orders.query.get(order_id)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), 404
    
    modifiable_fields = ['period', 'division_id']
    if not any([ field in request.form for field in modifiable_fields ]):
        return jsonify({ 'error': 'No modifiable fields provided', 'modifiable_fields': modifiable_fields }), 400
    
    order.period = request.form.get('period', order.period)
    order.division_id = request.form.get('division_id', order.division_id)
    
    try:
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while updating order', 'details': f"{e}" }), 500
    
    return jsonify({ 'message': 'Order updated successfully', 'order_details': order.to_dict() })

@api.route('/order/<string:order_id>', methods = ['DELETE'])
def api_delete_order(order_id):
    order = Orders.query.get(order_id)
    
    if order is None:
        return jsonify({ 'error': 'Order not found' }), 404
    
    try:
        db.session.delete(order)
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while deleting order', 'details': f"{e}" }), 500
    
    return jsonify({ 'message': 'Order deleted successfully' })