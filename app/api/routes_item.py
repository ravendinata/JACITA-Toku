import copy
import re

from flask import jsonify, request, session

import helper.trail as trail
from app.api import api
from app.extensions import db
from app.models.items import Items, ViewItems, NonvalItems, ViewNonvalItems
from helper.core import generate_item_id, jumble_string
from helper.endpoint import HTTPStatus, check_fields, check_api_permission

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

@api.route('/items/validated', methods = ['POST'])
@check_api_permission('item_validated/create')
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
    description = request.form.get('description')

    check_item = Items.query.filter_by(brand = brand, name = name, variant = variant).first()
    if check_item:
        return jsonify({ 'error': 'Item already exists' }), HTTPStatus.CONFLICT

    id = generate_item_id(brand, name, variant)

    item = Items(id = id, created_by = created_by,
                 brand = brand, name = name, variant = variant, 
                 base_price = base_price, description = description,
                 category_id = category_id, qty_unit_id = qty_unit_id)
    
    try:
        db.session.add(item)
        db.session.commit()
    except Exception as e:
        print(f"Error while creating item: {e}")
        return jsonify({ 'error': 'Error while creating item', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR

    trail.log_creation(item, created_by)
    return jsonify({ 'message': 'Item created successfully' }), HTTPStatus.CREATED

@api.route('/items/validated/bulk', methods = ['POST'])
@check_api_permission('item_validated/create')
def api_create_bulk_items():
    check_field = check_fields(request, 'item/create_bulk')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST
    
    created_by = request.form.get('created_by')

    brands = request.form.getlist('brand[]')
    names = request.form.getlist('name[]')
    variants = request.form.getlist('variant[]')
    base_prices = request.form.getlist('base_price[]')
    category_ids = request.form.getlist('category_id[]')
    qty_unit_ids = request.form.getlist('qty_unit_id[]')

    items = []
    for i in range(len(brands)):
        brand = brands[i]
        name = names[i]
        variant = variants[i]
        base_price = base_prices[i]
        category_id = category_ids[i]
        qty_unit_id = qty_unit_ids[i]

        check_item = Items.query.filter_by(brand = brand, name = name, variant = variant).first()
        if check_item:
            return jsonify({ 'error': 'Item already exists', 'details': f"{brand} {name} {variant} already exists" }), HTTPStatus.CONFLICT
        
        id = generate_item_id(brand, name, variant)
        print(f"Generated ID for {brand} {name} {variant}: {id}")

        item = Items(id = id, created_by = created_by,
                     brand = brand, name = name, variant = variant, 
                     base_price = base_price,
                     category_id = category_id, qty_unit_id = qty_unit_id)
        
        if item.id in [ i.id for i in items ]:
            item.id = generate_item_id(brand, name, jumble_string(variant))
        
        items.append(item)

    try:
        db.session.add_all(items)
        db.session.commit()
    except Exception as e:
        print(f"Error while creating bulk items: {e}")
        return jsonify({ 'error': 'Error while creating items in bulk', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    for item in items:
        trail.log_creation(item, created_by)

    return jsonify({ 'message': 'Bulk items created successfully' }), HTTPStatus.CREATED

@api.route('/items/validated/bulk/edit', methods = ['PATCH'])
@check_api_permission('item_validated/update_bulk')
def api_update_bulk_items():
    check_field = check_fields(request, 'item_validated/update_bulk')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST
    
    username = session.get('user')

    item_ids = request.form.getlist('item_id[]')
    brands = request.form.getlist('brand[]')
    names = request.form.getlist('name[]')
    variants = request.form.getlist('variant[]')
    base_prices = request.form.getlist('base_price[]')
    category_ids = request.form.getlist('category_id[]')
    qty_unit_ids = request.form.getlist('qty_unit_id[]')

    items = []
    old_items = []

    for i in range(len(item_ids)):
        item_id = item_ids[i]
        brand = brands[i]
        name = names[i]
        variant = variants[i]
        base_price = base_prices[i]
        category_id = category_ids[i]
        qty_unit_id = qty_unit_ids[i]

        item = Items.query.get(item_id)
        if item is None:
            return jsonify({ 'error': 'Item not found', 'details': f"Item with ID {item_id} not found" }), HTTPStatus.NOT_FOUND
        
        old_item = copy.deepcopy(item)
        
        item.brand = brand
        item.name = name
        item.variant = variant
        item.base_price = base_price
        item.category_id = category_id
        item.qty_unit_id = qty_unit_id
        item.modification_by = username

        old_items.append(old_item)
        items.append(item)

    try:
        db.session.commit()
    except Exception as e:
        print(f"Error while updating bulk items: {e}")
        return jsonify({ 'error': 'Error while updating items in bulk', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    for i in range(len(items)):
        trail.log_update(items[i], old_items[i], username)

    return jsonify({ 'message': 'Bulk items updated successfully' }), HTTPStatus.OK

@api.route('/items/validated/bulk/delete', methods = ['DELETE'])
@check_api_permission('item_validated/delete_bulk')
def api_delete_bulk_items():
    item_ids = request.form.getlist('item_id[]')

    for item_id in item_ids:
        item = Items.query.get(item_id)
        if item is None:
            return jsonify({ 'error': 'Item not found', 'details': f"Item with ID {item_id} not found" }), HTTPStatus.NOT_FOUND

        try:
            db.session.delete(item)
            db.session.commit()
            trail.log_deletion(item, session.get('user'))
        except Exception as e:
            print(f"Error while deleting bulk items: {e}")
            return jsonify({ 'error': 'Error while deleting items in bulk', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Bulk items deleted successfully' }), HTTPStatus.OK

@api.route('/items/validated/<string:item_id>', methods = ['PATCH'])
@check_api_permission('item_validated/update')
def api_update_item(item_id):

    check_field = check_fields(request, 'item_validated/update')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST
    
    username = session.get('user')
    
    item = Items.query.get(item_id)
    old_item = copy.deepcopy(item)

    if item is None:
        return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND
    
    item.brand = request.form.get('brand', item.brand)
    item.name = request.form.get('name', item.name)
    item.variant = request.form.get('variant', item.variant)
    item.base_price = request.form.get('base_price', item.base_price)
    item.category_id = request.form.get('category_id', item.category_id)
    item.qty_unit_id = request.form.get('qty_unit_id', item.qty_unit_id)
    
    if item.description:
        match = re.search(r'\(Originally Created by (.*?)\)', item.description)
        if match:
            original_creator = match.group(1)
            new_description = request.form.get('description', '')
            if f"(Originally Created by {original_creator})" not in new_description:
                return jsonify({'error': 'Cannot change description of validated item',
                                'details': "You should not remove or change the '(Originally Created by ...)' part of the description"}), HTTPStatus.BAD_REQUEST
    else:
        item.description = request.form.get('description', item.description)

    item.modification_by = username

    try:
        db.session.commit()
    except Exception as e:
        print(f"Error while updating item: {e}")
        return jsonify({ 'error': 'Error while updating item', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    trail.log_update(item, old_item, username)
    return jsonify({ 'message': 'Item updated successfully' }), HTTPStatus.OK

@api.route('/items/validated/<string:item_id>', methods = ['DELETE'])
@check_api_permission('item_validated/delete')
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
    
    trail.log_deletion(item, session.get('user'))
    return jsonify({ 'message': 'Item deleted successfully' }), HTTPStatus.OK

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

@api.route('/items/nonvalidated', methods = ['POST'])
@check_api_permission('item_nonvalidated/create')
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
    description = request.form.get('description')

    check_item = NonvalItems.query.filter_by(brand = brand, name = name, variant = variant).first()
    if check_item:
        return jsonify({ 'error': 'Item already exists' }), HTTPStatus.CONFLICT

    id = generate_item_id(brand, name, variant)

    item = NonvalItems(id = id, 
                       brand = brand, name = name, variant = variant, 
                       base_price = base_price, description = description,
                       category_id = category_id, created_by = created_by)
    
    try:
        db.session.add(item)
        db.session.commit()
    except Exception as e:
        print(f"Error while creating non-validated item: {e}")
        return jsonify({ 'error': 'Error while creating non-validated item', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    trail.log_creation(item, created_by)
    return jsonify({ 'message': 'Non-validated item created successfully' }), HTTPStatus.CREATED

@api.route('/items/nonvalidated/<string:item_id>', methods = ['PATCH'])
@check_api_permission('item_nonvalidated/update')
def api_update_nonval_item(item_id):
    check_field = check_fields(request, 'item_nonvalidated/update')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST
    
    username = session.get('user')
    
    item = NonvalItems.query.get(item_id)
    old_item = copy.deepcopy(item)

    if item is None:
        return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND
    
    item.brand = request.form.get('brand', item.brand)
    item.name = request.form.get('name', item.name)
    item.variant = request.form.get('variant', item.variant)
    item.base_price = request.form.get('base_price', item.base_price)
    item.category_id = request.form.get('category_id', item.category_id)
    item.description = request.form.get('description', item.description)        

    item.modification_by = username

    try:
        db.session.commit()
    except Exception as e:
        print(f"Error while updating non-validated item: {e}")
        return jsonify({ 'error': 'Error while updating non-validated item', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    trail.log_update(item, old_item, username)
    return jsonify({ 'message': 'Non-validated item updated successfully' }), HTTPStatus.OK

@api.route('/items/nonvalidated/<string:item_id>', methods = ['DELETE'])
@check_api_permission('item_nonvalidated/delete')
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
    
    trail.log_deletion(item, session.get('user'))
    return jsonify({ 'message': 'Non-validated item deleted successfully' }), HTTPStatus.OK

@api.route('/items/nonvalidated/<string:item_id>/validate', methods = ['POST'])
@check_api_permission('item_nonvalidated/validate')
def api_validate_nonval_item(item_id):
    item = NonvalItems.query.get(item_id)
    if item is None:
        return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND
    
    validator = session.get('user')

    if validator != request.form.get('validator'):
        return jsonify({ 'error': 'Validator does not match the current user', 'details': f"User in Form: {request.form.get('validator')}, Session User: {validator}" }), HTTPStatus.FORBIDDEN

    description = f"{item.description} (Originally Created by {item.created_by})"

    item_val = Items(id = item.id, brand = item.brand, name = item.name, variant = item.variant,
                     base_price = item.base_price, category_id = item.category_id, qty_unit_id = 0,
                     created_by = validator, description = description)

    try:
        db.session.add(item_val)
        db.session.delete(item)
        db.session.commit()
    except Exception as e:
        print(f"Error while validating non-validated item: {e}")
        return jsonify({ 'error': 'Error while validating non-validated item', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Non-validated item validated successfully' }), HTTPStatus.CREATED

# ======================
# AGGREGATED ITEM ROUTES
# ======================

@api.route('/items', methods = ['GET'])
def api_get_all_items():
    items_val = ViewItems.query.all()
    items_nonval = ViewNonvalItems.query.all()

    data = []
    for item in items_val:
        obj = item.to_dict()
        obj.pop('description')
        obj['validated'] = True
        data.append(obj)

    for item in items_nonval:
        obj = item.to_dict()
        obj.pop('description')
        obj['validated'] = False
        obj['qty_unit'] = None
        data.append(obj)

    return jsonify(data), HTTPStatus.OK

@api.route('/item/<string:item_id>', methods = ['GET'])
def api_get_item(item_id):
    human_readable = request.args.get('human_readable')

    if human_readable == 'true':
        item_val = ViewItems.query.get(item_id)
        item_nonval = ViewNonvalItems.query.get(item_id)
    else:
        item_val = Items.query.get(item_id)
        item_nonval = NonvalItems.query.get(item_id)

    if item_val is None and item_nonval is None:
        return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND
    
    if item_val is not None:
        obj = item_val.to_dict()
        obj['validated'] = True
        return jsonify(item_val.to_dict()), HTTPStatus.OK
    else:
        obj = item_nonval.to_dict()
        obj['validated'] = False
        obj['qty_unit'] = None
        return jsonify(obj), HTTPStatus.OK