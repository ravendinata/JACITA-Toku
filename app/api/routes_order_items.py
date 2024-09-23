from flask import jsonify, request

from app.api import api
from app.extensions import db
from app.models.misc import QuantityUnit
from app.models.orders import Orders
from app.models.items import Items, NonvalItems
from app.models.order_items import OrderItems, OrderNonvalItems
from helper.endpoint import HTTPStatus, check_fields, check_api_permission

@api.route('/order/<string:order_id>/items', methods = ['GET'])
def api_get_order_items(order_id):
    if Orders.query.get(order_id) is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND

    items = OrderItems.query.filter_by(order_id = order_id).all()
    nonval_items = OrderNonvalItems.query.filter_by(order_id = order_id).all()
    
    return jsonify({ 'items': [ item.to_dict() for item in items ],
                    'nonval_items': [ item.to_dict() for item in nonval_items ] }), HTTPStatus.OK

@api.route('/order/<string:order_id>/item/<string:item_id>', methods = ['GET'])
def api_get_order_item(order_id, item_id):
    item = OrderItems.query.get((order_id, item_id))
    if item is None:
        item = OrderNonvalItems.query.get((order_id, item_id))
        if item is None:
            return jsonify({ 'error': 'Item not found in order' }), HTTPStatus.NOT_FOUND
    
    return jsonify(item.to_dict()), HTTPStatus.OK

@api.route('/order/<string:order_id>/item', methods = ['POST'])
@check_api_permission('orderitem/create')
def api_add_order_item(order_id):
    check_field = check_fields(request, 'orderitem/create')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST

    if Orders.query.get(order_id) is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    item_type = 'validated'
    item_id = request.form.get('item_id')
    quantity = request.form.get('quantity')
    remarks = request.form.get('remarks')

    check_item = Items.query.get(item_id)
    if check_item is None:
        check_item = NonvalItems.query.get(item_id)
        if check_item is None:
            return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND
        else:
            item_type = 'nonvalidated'

    # Check if item already exists in order
    check_order_item = OrderItems.query.get((order_id, item_id))
    if check_order_item is None:
        check_order_item = OrderNonvalItems.query.get((order_id, item_id))

    # If item already exists, update the quantity instead of adding a new item
    if check_order_item is not None:
        try:
            check_order_item.quantity += int(quantity)
            db.session.commit()
        except Exception as e:
            return jsonify({ 'error': 'Error while updating order item quantity', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
        
        return jsonify({ 'message': 'Item quantity updated instead of adding a new item' }), HTTPStatus.OK

    item = None
    if item_type == 'validated':
        item = OrderItems(order_id = order_id, item_id = item_id, quantity = quantity, remarks = remarks)
    elif item_type == 'nonvalidated':
        item = OrderNonvalItems(order_id = order_id, item_id = item_id, quantity = quantity, remarks = remarks)
    
    try:
        db.session.add(item)
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while adding item to order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Item added to order successfully' }), HTTPStatus.CREATED

@api.route('/order/<string:order_id>/item/<string:item_id>', methods = ['PATCH'])
@check_api_permission('orderitem/update')
def api_update_order_item(order_id, item_id):
    check_field = check_fields(request, 'orderitem/update')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST

    item = OrderItems.query.get((order_id, item_id))
    if item is None:
        item = OrderNonvalItems.query.get((order_id, item_id))
        if item is None:
            return jsonify({ 'error': 'Item not found in order' }), HTTPStatus.NOT_FOUND
    
    item.quantity = request.form.get('quantity', item.quantity)
    item.remarks = request.form.get('remarks', item.remarks)
    
    try:
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while updating item in order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Item updated in order successfully', 'item_details': item.to_dict() }), HTTPStatus.OK

@api.route('/order/<string:order_id>/item/<string:item_id>', methods = ['DELETE'])
@check_api_permission('orderitem/delete')
def api_remove_order_item(order_id, item_id):
    item = OrderItems.query.get((order_id, item_id))
    if item is None:
        item = OrderNonvalItems.query.get((order_id, item_id))
        if item is None:
            return jsonify({ 'error': 'Item not found in order' }), HTTPStatus.NOT_FOUND
    
    try:
        db.session.delete(item)
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while removing item from order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Item removed from order successfully' }), HTTPStatus.NO_CONTENT

@api.route('/order/<string:order_id>/items/count', methods = ['GET'])
def api_get_order_item_count(order_id):
    if Orders.query.get(order_id) is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND

    items = OrderItems.query.filter_by(order_id = order_id).all()
    nonval_items = OrderNonvalItems.query.filter_by(order_id = order_id).all()

    total = 0
    for item in items:
        total += item.quantity
    for item in nonval_items:
        total += item.quantity
    
    return jsonify({ 'total': total }), HTTPStatus.OK

@api.route('/order/<string:order_id>/items/top', methods = ['GET'])
def api_get_order_top_items(order_id):
    if Orders.query.get(order_id) is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND

    items = OrderItems.query.filter_by(order_id = order_id).all()
    nonval_items = OrderNonvalItems.query.filter_by(order_id = order_id).all()

    top_items = []
    for item in items:
        top_items.append({ 'item_id': item.item_id, 'quantity': item.quantity })
    for item in nonval_items:
        top_items.append({ 'item_id': item.item_id, 'quantity': item.quantity })
    
    top_items.sort(key = lambda x: x['quantity'], reverse = True)
    top_items = top_items[:5] # Get top 5 items only

    for order_item in top_items:
        item = Items.query.get(order_item['item_id'])
        if item is None:
            item = NonvalItems.query.get(order_item['item_id'])
            qty_unit = QuantityUnit.query.get(0)
        else:
            qty_unit = QuantityUnit.query.get(item.qty_unit_id)

        order_item['brand'] = item.brand
        order_item['name'] = item.name
        order_item['variant'] = item.variant
        order_item['qty_unit'] = qty_unit.unit
    
    return top_items, HTTPStatus.OK