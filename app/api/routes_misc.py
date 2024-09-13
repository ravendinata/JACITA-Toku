from flask import jsonify, request

from app.api import api
from app.models.misc import Category, QuantityUnit
from helper.core import generate_item_id
from helper.endpoint import HTTPStatus

# ===============
# CATEGORY ROUTES
# ===============

@api.route('/categories', methods = ['GET'])
def api_get_categories():
    categories = Category.query.all()
    return jsonify([ category.to_dict() for category in categories ]), HTTPStatus.OK

# ====================
# QUANTITY UNIT ROUTES
# ====================

@api.route('/units', methods = ['GET'])
def api_get_units():
    units = QuantityUnit.query.all()
    return jsonify([ unit.to_dict() for unit in units ]), HTTPStatus.OK

# ==================
# MISC HELPER ROUTES
# ==================

# Item ID Generator
@api.route('/helper/generate_item_id', methods = ['POST'])
def api_generate_item_id():
    brand = request.form.get('brand')
    name = request.form.get('name')
    variant = request.form.get('variant')

    id = generate_item_id(brand, name, variant)

    return jsonify({ 'id': id, 'brand': brand, 'name': name, 'variant': variant }), HTTPStatus.OK