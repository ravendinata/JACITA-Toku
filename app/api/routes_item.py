from flask import jsonify, request

from app.api import api
from app.extensions import db
from app.models.items import Items, ViewItems
from helper.core import generate_item_id

# =====================
# VALIDATED ITEM ROUTES
# =====================

@api.route('/items/validated', methods = ['GET'])
    items = ViewItems.query.all()
def api_get_items():
    return jsonify([ item.to_dict() for item in items ])

@api.route('/items/validated/<string:item_id>', methods = ['GET'])
    item = ViewItems.query.get(item_id)
def api_get_item(item_id):

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