from flask import jsonify, request

from app.api import api
from app.extensions import db
from app.models.items import Items, ViewItems, NonvalItems, ViewNonvalItems
from helper.core import generate_item_id
from helper.endpoint import HTTPStatus, check_fields

# =====================
# VALIDATED ITEM ROUTES
# =====================

@api.route('/items/validated', methods = ['GET'])
def api_get_items():
    human_readable = request.args.get('human_readable')

    if human_readable == 'true':
        items = ViewItems.query.all()
    else:
        items = Items.query.all()
    
    return jsonify([ item.to_dict() for item in items ]), HTTPStatus.OK

@api.route('/items/validated/<string:item_id>', methods = ['GET'])
def api_get_item(item_id):
    human_readable = request.args.get('human_readable')

    if human_readable == 'true':
        item = ViewItems.query.get(item_id)
    else:
        item = Items.query.get(item_id)

    if item is None:
        return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND
    
    return jsonify(item.to_dict()), HTTPStatus.OK

@api.route('/items/validated', methods = ['POST'])
def api_create_item():
    check_field = check_fields(request, 'item/create')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST

    brand = request.form.get('brand')
    name = request.form.get('name')
    variant = request.form.get('variant')
    base_price = request.form.get('base_price')
    category_id = request.form.get('category_id')
    qty_unit_id = request.form.get('qty_unit_id')
    created_by = request.form.get('created_by')

    check_item = Items.query.filter_by(brand = brand, name = name, variant = variant).first()
    if check_item:
        return jsonify({ 'error': 'Item already exists' }), HTTPStatus.CONFLICT

    id = generate_item_id(brand, name, variant)

    item = Items(id = id, created_by = created_by,
                 brand = brand, name = name, variant = variant, 
                 base_price = base_price, 
                 category_id = category_id, qty_unit_id = qty_unit_id)
    
    try:
        db.session.add(item)
        db.session.commit()
    except Exception as e:
        print(f"Error while creating item: {e}")
        return jsonify({ 'error': 'Error while creating item', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify({ 'message': 'Item created successfully' }), HTTPStatus.CREATED

@api.route('/items/validated/<string:item_id>', methods = ['PATCH'])
def api_update_item(item_id):
    check_field = check_fields(request, 'item_validated/update')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST
    
    item = Items.query.get(item_id)

    if item is None:
        return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND

    brand = request.form.get('brand')
    name = request.form.get('name')
    variant = request.form.get('variant')
    base_price = request.form.get('base_price')
    category_id = request.form.get('category_id')
    qty_unit_id = request.form.get('qty_unit_id')

    if brand is not None:
        item.brand = brand
    if name is not None:
        item.name = name
    if variant is not None:
        item.variant = variant
    if base_price is not None:
        item.base_price = base_price
    if category_id is not None:
        item.category_id = category_id
    if qty_unit_id is not None:
        item.qty_unit_id = qty_unit_id

    try:
        db.session.commit()
    except Exception as e:
        print(f"Error while updating item: {e}")
        return jsonify({ 'error': 'Error while updating item', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Item updated successfully' }), HTTPStatus.OK

@api.route('/items/validated/<string:item_id>', methods = ['DELETE'])
def api_delete_item(item_id):
    item = Items.query.get(item_id)

    if item is None:
        return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND

    try:
        db.session.delete(item)
        db.session.commit()
    except Exception as e:
        print(f"Error while deleting item: {e}")
        return jsonify({ 'error': 'Error while deleting item', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Item deleted successfully' }), HTTPStatus.NO_CONTENT

# =========================
# NON-VALIDATED ITEM ROUTES
# =========================

@api.route('/items/nonvalidated', methods = ['GET'])
def api_get_nonval_items():
    human_readable = request.args.get('human_readable')

    if human_readable == 'true':
        items = ViewNonvalItems.query.all()
    else:
        items = NonvalItems.query.all()

    return jsonify([ item.to_dict() for item in items ]), HTTPStatus.OK

@api.route('/items/nonvalidated/<string:item_id>', methods = ['GET'])
def api_get_nonval_item(item_id):
    human_readable = request.args.get('human_readable')

    if human_readable == 'true':
        item = ViewNonvalItems.query.get(item_id)
    else:
        item = NonvalItems.query.get(item_id)

    if item is None:
        return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND
    
    return jsonify(item.to_dict()), HTTPStatus.OK

@api.route('/items/nonvalidated', methods = ['POST'])
def api_create_nonval_item():
    check_field = check_fields(request, 'nonvalitem/create')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST
    
    brand = request.form.get('brand')
    name = request.form.get('name')
    variant = request.form.get('variant')
    base_price = request.form.get('base_price')
    category_id = request.form.get('category_id')
    created_by = request.form.get('created_by')

    check_item = NonvalItems.query.filter_by(brand = brand, name = name, variant = variant).first()
    if check_item:
        return jsonify({ 'error': 'Item already exists' }), HTTPStatus.CONFLICT

    id = generate_item_id(brand, name, variant)

    item = NonvalItems(id = id, 
                       brand = brand, name = name, variant = variant, 
                       base_price = base_price, 
                       category_id = category_id, created_by = created_by)
    
    try:
        db.session.add(item)
        db.session.commit()
    except Exception as e:
        print(f"Error while creating non-validated item: {e}")
        return jsonify({ 'error': 'Error while creating non-validated item', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Non-validated item created successfully' }), HTTPStatus.CREATED

@api.route('/items/nonvalidated/<string:item_id>', methods = ['PATCH'])
def api_update_nonval_item(item_id):
    check_field = check_fields(request, 'item_nonvalidated/update')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST
    
    item = NonvalItems.query.get(item_id)

    if item is None:
        return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND

    brand = request.form.get('brand')
    name = request.form.get('name')
    variant = request.form.get('variant')
    base_price = request.form.get('base_price')
    category_id = request.form.get('category_id')

    if brand is not None:
        item.brand = brand
    if name is not None:
        item.name = name
    if variant is not None:
        item.variant = variant
    if base_price is not None:
        item.base_price = base_price
    if category_id is not None:
        item.category_id = category_id

    try:
        db.session.commit()
    except Exception as e:
        print(f"Error while updating non-validated item: {e}")
        return jsonify({ 'error': 'Error while updating non-validated item', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Non-validated item updated successfully' }), HTTPStatus.OK

@api.route('/items/nonvalidated/<string:item_id>', methods = ['DELETE'])
def api_delete_nonval_item(item_id):
    item = NonvalItems.query.get(item_id)

    if item is None:
        return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND

    try:
        db.session.delete(item)
        db.session.commit()
    except Exception as e:
        print(f"Error while deleting non-validated item: {e}")
        return jsonify({ 'error': 'Error while deleting non-validated item', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Non-validated item deleted successfully' }), HTTPStatus.NO_CONTENT

# ======================
# AGGREGATED ITEM ROUTES
# ======================

@api.route('/items', methods = ['GET'])
def api_get_all_items():
    human_readable = request.args.get('human_readable')

    if human_readable == 'true':
        items_val = ViewItems.query.all()
        items_nonval = ViewNonvalItems.query.all()
    else:
        items_val = Items.query.all()
        items_nonval = NonvalItems.query.all()

    data = []
    for item in items_val:
        obj = item.to_dict()
        obj['validated'] = True
        data.append(obj)

    for item in items_nonval:
        obj = item.to_dict()
        obj['validated'] = False
        obj['qty_unit'] = None
        data.append(obj)

    return jsonify(data), HTTPStatus.OK