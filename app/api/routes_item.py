from flask import jsonify, request

from app.api import api
from app.extensions import db
from app.models.items import Items, ViewItems
from helper.core import generate_item_id

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
    
    return jsonify([ item.to_dict() for item in items ])

@api.route('/items/validated/<string:item_id>', methods = ['GET'])
def api_get_item(item_id):
    human_readable = request.args.get('human_readable')
    item = None

    if human_readable == 'true':
        item = ViewItems.query.get(item_id)
    else:
        item = Items.query.get(item_id)

    if item is None:
        return jsonify({ 'error': 'Item not found' }), 404
    
    return jsonify(item.to_dict())

@api.route('/items/validated', methods = ['POST'])
def api_create_item():
    brand = request.form.get('brand')
    name = request.form.get('name')
    variant = request.form.get('variant')
    base_price = request.form.get('base_price')
    category_id = request.form.get('category_id')
    qty_unit_id = request.form.get('qty_unit_id')

    id = generate_item_id(brand, name, variant)

    item = Items(id = id, 
                 brand = brand, name = name, variant = variant, 
                 base_price = base_price, 
                 category_id = category_id, qty_unit_id = qty_unit_id)
    
    try:
        db.session.add(item)
        db.session.commit()
    except Exception as e:
        print(f"Error while creating item: {e}")
        return jsonify({ 'error': 'Error while creating item' }), 500

    return jsonify({ 'message': 'Item created successfully' })