from flask import jsonify, request

from app.api import api
from app.extensions import db
from app.models.orders import Orders
from app.models.items import Items, NonvalItems
from app.models.order_items import OrderItems, OrderNonvalItems
from helper.endpoint import check_fields

@api.route('/order/<string:order_id>/items', methods = ['GET'])
def api_get_order_items(order_id):
    if Orders.query.get(order_id) is None:
        return jsonify({ 'error': 'Order not found' }), 404

    items = OrderItems.query.filter_by(order_id = order_id).all()
    nonval_items = OrderNonvalItems.query.filter_by(order_id = order_id).all()
    
    return jsonify({ 'items': [ item.to_dict() for item in items ],
                    'nonval_items': [ item.to_dict() for item in nonval_items ] })

@api.route('/order/<string:order_id>/item/<string:item_id>', methods = ['GET'])
def api_get_order_item(order_id, item_id):
    item = OrderItems.query.get((order_id, item_id))
    if item is None:
        item = OrderNonvalItems.query.get((order_id, item_id))
        if item is None:
            return jsonify({ 'error': 'Item not found in order' }), 404
    
    return jsonify(item.to_dict())

@api.route('/order/<string:order_id>/item', methods = ['POST'])
def api_add_order_item(order_id):
    check_field = check_fields(request, 'order_item/create')
    if not check_field['pass']:
        return jsonify(check_field), 400

    if Orders.query.get(order_id) is None:
        return jsonify({ 'error': 'Order not found' }), 404
    
    item_type = 'validated'
    item_id = request.form.get('item_id')
    quantity = request.form.get('quantity')
    remarks = request.form.get('remarks')

    check_item = Items.query.get(item_id)
    if check_item is None:
        check_item = NonvalItems.query.get(item_id)
        if check_item is None:
            return jsonify({ 'error': 'Item not found' }), 404
        else:
            item_type = 'nonvalidated'

    item = None
    if item_type == 'validated':
        item = OrderItems(order_id = order_id, item_id = item_id, quantity = quantity, remarks = remarks)
    elif item_type == 'nonvalidated':
        item = OrderNonvalItems(order_id = order_id, item_id = item_id, quantity = quantity, remarks = remarks)
    
    try:
        db.session.add(item)
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while adding item to order', 'details': f"{e}" }), 500
    
    return jsonify({ 'message': 'Item added to order successfully' })

@api.route('/order/<string:order_id>/item/<string:item_id>', methods = ['PATCH'])
def api_update_order_item(order_id, item_id):
    check_field = check_fields(request, 'order_item/update')
    if not check_field['pass']:
        return jsonify(check_field), 400

    item = OrderItems.query.get((order_id, item_id))
    if item is None:
        item = OrderNonvalItems.query.get((order_id, item_id))
        if item is None:
            return jsonify({ 'error': 'Item not found in order' }), 404
    
    item.quantity = request.form.get('quantity', item.quantity)
    item.remarks = request.form.get('remarks', item.remarks)
    
    try:
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while updating item in order', 'details': f"{e}" }), 500
    
    return jsonify({ 'message': 'Item updated in order successfully', 'item_details': item.to_dict() })

@api.route('/order/<string:order_id>/item/<string:item_id>', methods = ['DELETE'])
def api_remove_order_item(order_id, item_id):
    item = OrderItems.query.get((order_id, item_id))
    if item is None:
        item = OrderNonvalItems.query.get((order_id, item_id))
        if item is None:
            return jsonify({ 'error': 'Item not found in order' }), 404
    
    try:
        db.session.delete(item)
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while removing item from order', 'details': f"{e}" }), 500
    
    return jsonify({ 'message': 'Item removed from order successfully' })