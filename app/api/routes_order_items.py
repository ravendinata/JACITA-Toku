from flask import jsonify, request, session
from sqlalchemy import asc

from app.api import api
from app.extensions import db
from app.models.misc import QuantityUnit
from app.models.orders import Orders
from app.models.items import Items, NonvalItems
from app.models.order_items import OrderItems, OrderNonvalItems
from app.models.user import User
from helper.endpoint import HTTPStatus, check_fields, check_api_permission
from helper.status import OrderStatus
from helper.role import Role

def collectItems(orders):
    data = []
    for order in orders:
        for order_item in order.items:
            data_dict = {item_data['item_id']: item_data for item_data in data}
            item = Items.query.get(order_item.item_id) or NonvalItems.query.get(order_item.item_id)
            
            if item.id in data_dict:
                item_data = data_dict[item.id]
                item_data['quantity'] += order_item.quantity
                item_data['subtotal'] += item.base_price * float(order_item.quantity)
                item_data['in_orders'] += 1
                item_data['orders'].append(order_item.order_id)

                remarks = ''
                if order_item.remarks and order_item.remarks != '':
                    remarks = f"{order_item.order_id}: {order_item.remarks}"

                item_data['remarks'] = item_data['remarks'] + ';' + remarks if item_data['remarks'] else remarks
            else:
                order_item_dict = order_item.to_dict()
                order_item_dict.pop('order_id')
                order_item_dict['brand'] = item.brand
                order_item_dict['name'] = item.name
                order_item_dict['variant'] = item.variant
                order_item_dict['price'] = item.base_price
                order_item_dict['qty_unit'] = QuantityUnit.query.get(item.qty_unit_id).unit if isinstance(item, Items) else QuantityUnit.query.get(0).unit
                order_item_dict['validated'] = isinstance(item, Items)
                order_item_dict['subtotal'] = item.base_price * float(order_item_dict['quantity'])
                order_item_dict['in_orders'] = 1
                order_item_dict['orders'] = [order_item.order_id]
            
                if order_item.remarks and order_item.remarks != '':
                    order_item_dict['remarks'] = f"{order_item.order_id}: {order_item.remarks}"
                else:
                    order_item_dict['remarks'] = ''

                data.append(order_item_dict)
                data_dict[item.id] = order_item_dict

    return data

@api.route('/order/<string:order_id>/items', methods = ['GET'])
def api_get_order_items(order_id):
    order = Orders.query.get(order_id)
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND

    data = collectItems([order])
    
    return jsonify(data), HTTPStatus.OK

@api.route('/order/<string:order_id>/item/<string:item_id>', methods = ['GET'])
def api_get_order_item(order_id, item_id):
    item = OrderItems.query.get((order_id, item_id)) or OrderNonvalItems.query.get((order_id, item_id))
    if item is None:
        return jsonify({ 'error': 'Item not found in order' }), HTTPStatus.NOT_FOUND
    
    return jsonify(item.to_dict()), HTTPStatus.OK

@api.route('/order/<string:order_id>/item', methods = ['POST'])
@check_api_permission('orderitem/create')
@check_fields('orderitem/create')
def api_add_order_item(order_id):
    order = Orders.query.get(order_id)
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    if order.status not in [OrderStatus.PENDING, OrderStatus.DIVISION_REJECTED]:
        return jsonify({ 'error': 'Forbidden operation', 'details': 'The active order is currently not able to accept new items' }), HTTPStatus.FORBIDDEN
    
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
    check_order_item = OrderItems.query.get((order_id, item_id)) or OrderNonvalItems.query.get((order_id, item_id))

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
@check_fields('orderitem/update')
def api_update_order_item(order_id, item_id):
    order = Orders.query.get(order_id)
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    if order.status not in [OrderStatus.PENDING, OrderStatus.DIVISION_REJECTED, OrderStatus.FINANCE_REJECTED]:
        return jsonify({ 'error': 'Forbidden operation', 'details': 'The current active order is not able to accept item updates because of its status' }), HTTPStatus.FORBIDDEN

    user = User.query.get(session['user'])
    if order.status == OrderStatus.FINANCE_REJECTED and user.role not in [Role.DIVISION_LEADER, Role.ADMINISTRATOR]:
        return jsonify({ 'error': 'Insufficient permissions', 'details': 'Only division leaders can update items in a finance-rejected order' }), HTTPStatus.FORBIDDEN

    item = OrderItems.query.get((order_id, item_id)) or OrderNonvalItems.query.get((order_id, item_id))
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
    order = Orders.query.get(order_id)
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND
    
    if order.status not in [OrderStatus.PENDING, OrderStatus.DIVISION_REJECTED, OrderStatus.FINANCE_REJECTED]:
        return jsonify({ 'error': 'Forbidden operation', 'details': 'The current active order is not able to accept item removals because of its status' }), HTTPStatus.FORBIDDEN

    user = User.query.get(session['user'])
    if order.status == OrderStatus.FINANCE_REJECTED and user.role not in [Role.DIVISION_LEADER, Role.ADMINISTRATOR]:
        return jsonify({ 'error': 'Insufficient permissions', 'details': 'Only division leaders can update items in a finance-rejected order' }), HTTPStatus.FORBIDDEN
    
    item = OrderItems.query.get((order_id, item_id)) or OrderNonvalItems.query.get((order_id, item_id))
    if item is None:
        return jsonify({ 'error': 'Item not found in order' }), HTTPStatus.NOT_FOUND
    
    try:
        db.session.delete(item)
        db.session.commit()
    except Exception as e:
        return jsonify({ 'error': 'Error while removing item from order', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Item removed from order successfully' }), HTTPStatus.OK

@api.route('/order/<string:order_id>/items/count', methods = ['GET'])
def api_get_order_item_count(order_id):
    order = Orders.query.get(order_id)
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND    
    return jsonify({ 'total': order.item_count }), HTTPStatus.OK

@api.route('/order/<string:order_id>/items/top', methods = ['GET'])
def api_get_order_top_items(order_id):
    order = Orders.query.get(order_id)
    if order is None:
        return jsonify({ 'error': 'Order not found' }), HTTPStatus.NOT_FOUND

    top_items = []
    for item in order.items:
        top_items.append({ 'item_id': item.item_id, 'quantity': item.quantity })
    
    top_items.sort(key = lambda x: x['quantity'], reverse = True)
    top_items = top_items[:5] # Get top 5 items only

    for order_item in top_items:
        item = Items.query.get(order_item['item_id']) or NonvalItems.query.get(order_item['item_id'])
        qty_unit = QuantityUnit.query.get(item.qty_unit_id) if isinstance(item, Items) else QuantityUnit.query.get(0)

        order_item['brand'] = item.brand
        order_item['name'] = item.name
        order_item['variant'] = item.variant
        order_item['qty_unit'] = qty_unit.unit
    
    return top_items, HTTPStatus.OK

# ====================================
# COMBINED ORDER ORDER ITEMS ENDPOINTS
# ====================================

@api.route('/order/<string:period>/<string:division_id>/items', methods = ['GET'])
def api_get_combined_order_items(period, division_id):
    period = f"{period[:4]}/{period[4:]}"
    orders = Orders.query.filter(Orders.period == period, Orders.division_id == division_id).all()
    if len(orders) == 0:
        return jsonify({ 'error': 'No orders found' }), HTTPStatus.NOT_FOUND

    data = collectItems(orders)
    
    return jsonify(data), HTTPStatus.OK

@api.route('/order/<string:period>/<string:division_id>/item/<string:item_id>', methods = ['DELETE'])
@check_api_permission('orderitem/delete')
def api_remove_combined_order_item(period, division_id, item_id):
    period = f"{period[:4]}/{period[4:]}"
    orders = Orders.query.filter(Orders.period == period, Orders.division_id == division_id).order_by(asc(Orders.id)).all()
    if len(orders) == 0:
        return jsonify({ 'error': 'No orders found' }), HTTPStatus.NOT_FOUND
    
    order_items_to_remove = []
    for order in orders:
        item = OrderItems.query.get((order.id, item_id)) or OrderNonvalItems.query.get((order.id, item_id))
        if item is not None:
            order_items_to_remove.append(item)

    try:
        for item in order_items_to_remove:
            db.session.delete(item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({ 'error': 'Error while removing item from all orders', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify({ 'message': 'Item removed from all orders successfully' }), HTTPStatus.OK

# ============================
# PERIOD ORDER ITEMS ENDPOINTS
# ============================

@api.route('/procurement/<string:period>/items', methods = ['GET'])
def api_get_period_order_items(period):
    period = f"{period[:4]}/{period[4:]}"

    orders = Orders.query.filter(Orders.period == period).filter(Orders.status >= OrderStatus.FINANCE_APPROVED).order_by(asc(Orders.division_id)).all()
    if len(orders) == 0:
        return jsonify({ 'error': 'No orders found' }), HTTPStatus.NOT_FOUND

    data = collectItems(orders)

    return jsonify(data), HTTPStatus.OK