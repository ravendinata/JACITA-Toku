import copy
import re
from uuid import uuid4

from flask import jsonify, request, session
from sqlalchemy import asc

import helper.trail as trail
from app.api import api
from app.extensions import db
from app.models.items import Items, ViewItems, NonvalItems, ViewNonvalItems, ViewGroupedItems, ViewGroupedNonvalItems
from app.models.logs import ItemPriceUpdateLog
from app.models.misc import QuantityUnit
from app.models.order_items import OrderItems, OrderNonvalItems
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
@check_fields('item_validated/create')
def api_create_item():
    created_by = request.form.get('created_by')
    if session.get('user') != created_by:
        trail.log_system_event("api.item.create", f"User fingerprint mismatch. User in Form: {created_by}, Session User: {session.get('user')}. Request denied.")
        return jsonify({ 'error': 'User fingerprint mismatch',
                         'details': f"Are you trying to impersonate someone? Logged in user does not match the creator in the request." }), HTTPStatus.FORBIDDEN
    
    brand = request.form.get('brand')
    name = request.form.get('name')
    variant = request.form.get('variant')
    base_price = request.form.get('base_price')
    category_id = request.form.get('category_id')
    qty_unit_id = request.form.get('qty_unit_id')
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
@check_api_permission('item_validated/create_bulk')
@check_fields('item_validated/create_bulk')
def api_create_bulk_items():
    created_by = request.form.get('created_by')
    if session.get('user') != created_by:
        trail.log_system_event("api.item.create_bulk", f"User fingerprint mismatch. User in Form: {created_by}, Session User: {session.get('user')}. Request denied.")
        return jsonify({ 'error': 'User fingerprint mismatch',
                         'details': f"Are you trying to impersonate someone? Logged in user does not match the creator in the request." }), HTTPStatus.FORBIDDEN

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
            
            module = "api.item.create_bulk"
            event_text = f"ID clash! Regenerated ID {brand} {name} {variant} (Jumbled): {item.id}"
            
            print(f"[{module}] {event_text}")
            trail.log_system_event(module, event_text)
        
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
@check_fields('item_validated/update_bulk')
def api_update_bulk_items():
    username = request.form.get('modified_by')

    if session.get('user') != username:
        trail.log_system_event("api.item.update_bulk", f"User fingerprint mismatch. User in Form: {username}, Session User: {session.get('user')}. Request denied.")
        return jsonify({ 'error': 'User fingerprint mismatch',
                         'details': f"Are you trying to impersonate someone? Logged in user does not match the modifier in the request." }), HTTPStatus.FORBIDDEN

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
        item = Items.query.get(item_ids[i])
        if item is None:
            return jsonify({ 'error': 'Item not found', 'details': f"Item with ID {item_ids[i]} not found" }), HTTPStatus.NOT_FOUND
        
        old_item = copy.deepcopy(item)
        
        item.brand = brands[i]
        item.name = names[i]
        item.variant = variants[i]
        item.base_price = base_prices[i]
        item.category_id = category_ids[i]
        item.qty_unit_id = qty_unit_ids[i]
        item.modification_by = username

        if float(item.base_price) != float(old_item.base_price):
            item_price_update = ItemPriceUpdateLog(id = f"{item.id}-{str(uuid4())[:8]}",
                                                   item_id = item.id,
                                                   price_original = old_item.base_price,
                                                   price_new = item.base_price,
                                                   user = username)
            
            if ItemPriceUpdateLog.query.filter_by(item_id = item.id).count() == 0:
                initial_price = ItemPriceUpdateLog(id = f"{item.id}-init",
                                                   item_id = item.id,
                                                   price_original = old_item.base_price,
                                                   price_new = old_item.base_price,
                                                   date = old_item.created_date,
                                                   user = old_item.created_by)
                
                try:
                    db.session.add(initial_price)
                except Exception as e:
                    print(f"Error while logging initial price update: {e}")
                    return jsonify({ 'error': 'Error while logging initial price update', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR

            try:
                db.session.add(item_price_update)
            except Exception as e:
                print(f"Error while logging price update: {e}")
                return jsonify({ 'error': 'Error while logging price update', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR

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
@check_fields('item_validated/delete_bulk')
def api_delete_bulk_items():
    username = request.form.get('deleted_by')
    if session.get('user') != username:
        trail.log_system_event("api.item.delete_bulk", f"User fingerprint mismatch. User in Form: {username}, Session User: {session.get('user')}. Request denied.")
        return jsonify({ 'error': 'User fingerprint mismatch',
                         'details': f"Are you trying to impersonate someone? Logged in user does not match the deleter in the request." }), HTTPStatus.FORBIDDEN
    
    item_ids = request.form.getlist('item_id[]')

    for item_id in item_ids:
        item = Items.query.get(item_id)
        if item is None:
            return jsonify({ 'error': 'Item not found', 'details': f"Item with ID {item_id} not found" }), HTTPStatus.NOT_FOUND

        try:
            db.session.delete(item)
            db.session.commit()
            trail.log_deletion(item, username)
        except Exception as e:
            print(f"Error while deleting bulk items: {e}")
            return jsonify({ 'error': 'Error while deleting items in bulk', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return jsonify({ 'message': 'Bulk items deleted successfully' }), HTTPStatus.OK

@api.route('/items/validated/<string:item_id>', methods = ['PATCH'])
@check_api_permission('item_validated/update')
@check_fields('item_validated/update')
def api_update_item(item_id):    
    username = request.form.get('modified_by')
    if session.get('user') != username:
        trail.log_system_event("api.item.update", f"User fingerprint mismatch. User in Form: {username}, Session User: {session.get('user')}. Request denied.")
        return jsonify({ 'error': 'User fingerprint mismatch',
                         'details': f"Are you trying to impersonate someone? Logged in user does not match the modifier in the request." }), HTTPStatus.FORBIDDEN
    
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

    if float(old_item.base_price) != float(item.base_price):
        item_price_update = ItemPriceUpdateLog(id = f"{item.id}-{str(uuid4())[:8]}",
                                               item_id = item_id,
                                               price_original = old_item.base_price,
                                               price_new = item.base_price,
                                               user = username)
        
        if ItemPriceUpdateLog.query.filter_by(item_id = item_id).count() == 0:
            initial_price = ItemPriceUpdateLog(id = f"{item.id}-init",
                                               item_id = item_id,
                                               price_original = old_item.base_price,
                                               price_new = old_item.base_price,
                                               date = old_item.created_date,
                                               user = old_item.created_by)
            
            try:
                db.session.add(initial_price)
            except Exception as e:
                print(f"Error while logging initial price update: {e}")
                return jsonify({ 'error': 'Error while logging initial price update', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR

        try:
            db.session.add(item_price_update)
        except Exception as e:
            print(f"Error while logging price update: {e}")
            return jsonify({ 'error': 'Error while logging price update', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    if item.description:
        match = re.search(r'\(Originally Created by (.*?)\)', item.description)
        if match:
            original_creator = match.group(1)
            new_description = request.form.get('description', item.description)
            if f"(Originally Created by {original_creator})" not in new_description:
                return jsonify({'error': 'Cannot change description of validated item',
                                'details': "You should not remove or change the '(Originally Created by ...)' part of the description"}), HTTPStatus.BAD_REQUEST
        item.description = new_description
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
@check_fields('item_validated/delete')
def api_delete_item(item_id):
    username = request.form.get('deleted_by')
    if session.get('user') != username:
        trail.log_system_event("api.item.delete", f"User fingerprint mismatch. User in Form: {username}, Session User: {session.get('user')}. Request denied.")
        return jsonify({ 'error': 'User fingerprint mismatch',
                         'details': f"Are you trying to impersonate someone? Logged in user does not match the deleter in the request." }), HTTPStatus.FORBIDDEN

    item = Items.query.get(item_id)
    if item is None:
        return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND

    try:
        db.session.delete(item)
        db.session.commit()
    except Exception as e:
        print(f"Error while deleting item: {e}")
        return jsonify({ 'error': 'Error while deleting item', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    trail.log_deletion(item, username)
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
@check_fields('item_nonvalidated/create')
def api_create_nonval_item():   
    created_by = request.form.get('created_by')
    if session.get('user') != created_by:
        trail.log_system_event("api.item.create", f"User fingerprint mismatch. User in Form: {created_by}, Session User: {session.get('user')}. Request denied.")
        return jsonify({ 'error': 'User fingerprint mismatch',
                         'details': f"Are you trying to impersonate someone? Logged in user does not match the creator in the request." }), HTTPStatus.FORBIDDEN

    brand = request.form.get('brand')
    name = request.form.get('name')
    variant = request.form.get('variant')
    base_price = request.form.get('base_price')
    category_id = request.form.get('category_id')
    description = request.form.get('description')

    id = generate_item_id(brand, name, variant, abort_on_duplicate = True)

    check_by_id = NonvalItems.query.get(id) or Items.query.get(id)
    check_item = NonvalItems.query.filter_by(brand=brand, name=name, variant=variant).first() or \
                 Items.query.filter_by(brand=brand, name=name, variant=variant).first()
    
    if check_item or check_by_id:
        return jsonify({'error': 'Potential item duplication',
                        'details': f"A similar or same item already exists. Please do not create duplicate items! If the item is actually different, please contact the administrator to assist you."}), HTTPStatus.CONFLICT

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
@check_fields('item_nonvalidated/update')
def api_update_nonval_item(item_id):   
    username = request.form.get('modified_by')
    if session.get('user') != username:
        trail.log_system_event("api.item.update", f"User fingerprint mismatch. User in Form: {username}, Session User: {session.get('user')}. Request denied.")
        return jsonify({ 'error': 'User fingerprint mismatch',
                         'details': f"Are you trying to impersonate someone? Logged in user does not match the modifier in the request." }), HTTPStatus.FORBIDDEN
    
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
@check_fields('item_nonvalidated/delete')
def api_delete_nonval_item(item_id):
    username = request.form.get('deleted_by')
    if session.get('user') != username:
        trail.log_system_event("api.item.delete", f"User fingerprint mismatch. User in Form: {username}, Session User: {session.get('user')}. Request denied.")
        return jsonify({ 'error': 'User fingerprint mismatch',
                         'details': f"Are you trying to impersonate someone? Logged in user does not match the deleter in the request." }), HTTPStatus.FORB

    item = NonvalItems.query.get(item_id)
    if item is None:
        return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND

    try:
        db.session.delete(item)
        db.session.commit()
    except Exception as e:
        print(f"Error while deleting non-validated item: {e}")
        return jsonify({ 'error': 'Error while deleting non-validated item', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    trail.log_deletion(item, username)
    return jsonify({ 'message': 'Non-validated item deleted successfully' }), HTTPStatus.OK

@api.route('/items/nonvalidated/<string:item_id>/validate', methods = ['POST'])
@check_api_permission('item_nonvalidated/validate')
@check_fields('item_nonvalidated/validate')
def api_validate_nonval_item(item_id):
    validator = session.get('user')
    if validator != request.form.get('validator'):
        trail.log_system_event("api.item.validate", f"User fingerprint mismatch. User in Form: {request.form.get('validator')}, Session User: {validator}. Request denied.")
        return jsonify({ 'error': 'User fingerprint mismatch',
                         'details': f"Are you trying to impersonate someone? Logged in user does not match the validator in the request." }), HTTPStatus.FORBIDDEN
    
    item = NonvalItems.query.get(item_id)
    if item is None:
        return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND

    description = f"{item.description} (Originally Created by {item.created_by})"

    item_val = Items(id = item.id, brand = item.brand, name = item.name, variant = item.variant,
                     base_price = item.base_price, category_id = item.category_id, qty_unit_id = 0,
                     created_by = validator, description = description)

    try:
        # Move non-validated order items to validated order items
        nonvalidated_order_items = OrderNonvalItems.query.filter_by(item_id = item_id).all()
        for order_item in nonvalidated_order_items:
            order_item_val = OrderItems(order_id = order_item.order_id, item_id = order_item.item_id,
                                        quantity = order_item.quantity, remarks = order_item.remarks)
            
            db.session.add(order_item_val)
            db.session.delete(order_item)

            trail.log_deletion(order_item, f"{validator} via system@validate")
            trail.log_creation(order_item_val, f"{validator} via system@validate")
        
        db.session.add(item_val)
        db.session.delete(item)
        db.session.commit()
    except Exception as e:
        print(f"Error while validating non-validated item: {e}")
        return jsonify({ 'error': 'Error while validating non-validated item', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR
    
    trail.log_deletion(item, f"{validator} via system@validate")
    trail.log_creation(item_val, f"{validator} via system@validate")

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
        item = ViewItems.query.get(item_id) or ViewNonvalItems.query.get(item_id)
    else:
        item = Items.query.get(item_id) or NonvalItems.query.get(item_id)

    if item is None:
        return jsonify({ 'error': 'Item not found' }), HTTPStatus.NOT_FOUND
    
    obj = item.to_dict()
    obj['validated'] = isinstance(item, Items) or isinstance(item, ViewItems)

    # Convert all dates into ISO 8601 format
    for key in obj.keys():
        if '_date' in key and obj[key] is not None:
            obj[key] = obj[key].isoformat()
        
    return jsonify(obj), HTTPStatus.OK

# ===================
# GROUPED ITEM ROUTES
# ===================

@api.route('/items/grouped', methods = ['GET'])
def api_get_grouped_items():
    items = ViewGroupedItems.query.all()
    nonval_items = ViewGroupedNonvalItems.query.all()

    data = []
    for item in items:
        obj = item.to_dict()
        obj['validated'] = True
        data.append(obj)

    for item in nonval_items:
        obj = item.to_dict()
        obj['validated'] = False
        data.append(obj)

    return jsonify(data), HTTPStatus.OK

@api.route('/items/grouped/variants', methods = ['POST'])
def api_get_grouped_variants():
    brand = request.form.get('brand')
    name = request.form.get('name')

    qty_unit = QuantityUnit.query.all()

    items = Items.query.filter_by(brand = brand, name = name).order_by(Items.variant).all() or \
            NonvalItems.query.filter_by(brand = brand, name = name).order_by(NonvalItems.variant).all()
    
    if not items:
        return jsonify({ 'error': 'No items found' }), HTTPStatus.NOT_FOUND
    
    data = []
    for item in items:
        obj = item.to_dict()
        
        remove_keys = ['brand', 'name', 'category_id', 'created_by', 'created_date', 'modification_by', 'modification_date']
        for key in remove_keys:
            obj.pop(key)

        if 'qty_unit_id' in obj:
            obj['qty_unit'] = [ unit.to_dict() for unit in qty_unit if unit.id == item.qty_unit_id ][0]
            obj.pop('qty_unit_id')
        else:
            obj['qty_unit'] = [ unit.to_dict() for unit in qty_unit if unit.id == 0 ][0]

        data.append(obj)

    return jsonify(data), HTTPStatus.OK

# =================
# PRICE UPDATE LOGS
# =================

@api.route('/item/<string:item_id>/price_history', methods = ['GET'])
def api_get_price_updates(item_id):
    updates = ItemPriceUpdateLog.query.filter_by(item_id = item_id).order_by(asc(ItemPriceUpdateLog.date)).all()

    if not updates:
        return jsonify({ 'error': 'No price updates yet' }), HTTPStatus.OK
    
    return jsonify([ update.to_dict() for update in updates ]), HTTPStatus.OK