import json
from flask import jsonify, request, session

from app.api import api
from app.models.misc import Category, QuantityUnit
from helper.core import generate_item_id, generate_order_id
from helper.endpoint import HTTPStatus, check_api_permission

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

# Order ID Generator
@api.route('/helper/generate_order_id', methods = ['POST'])
def api_generate_order_id():
    period = request.form.get('period')
    division_id = request.form.get('division_id')

    id = generate_order_id(period, division_id)

    return jsonify({ 'id': id, 'period': period, 'division_id': division_id }), HTTPStatus.OK

@api.route('helper/test_cookies', methods = ['GET'])
def api_test_cookies():
    return jsonify({ 'cookies': request.cookies }), HTTPStatus.OK

@api.route('helper/test_session', methods = ['GET'])
def api_test_session():
    return jsonify({ 'session': session }), HTTPStatus.OK

# ===================
# ANNOUNCEMENT ROUTES
# ===================

@api.route('/announcement/status', methods = ['GET'])
def api_announcement_status():
    try:
        with open('announcement.json', 'r') as f:
            announcement = json.load(f)
    except FileNotFoundError:
        return jsonify({ 'enable': False }), HTTPStatus.OK
    
    return jsonify({ 'enable': announcement['enable'] }), HTTPStatus.OK

@api.route('/announcement/change_state', methods = ['POST'])
@check_api_permission('announcement/create')
def api_announcement_change_state():
    with open('announcement.json', 'r') as f:
        announcement = json.load(f)

    enable = True if request.form.get('enable') == "true" else False
    announcement['enable'] = enable
    new_state = 'enabled' if announcement['enable'] else 'disabled'

    with open('announcement.json', 'w') as f:
        json.dump(announcement, f, indent = 4)

    return jsonify({ 'message': f"Announcement {new_state}!" }), HTTPStatus.OK

@api.route('/announce', methods = ['POST'])
@check_api_permission('announcement/create')
def api_announce():
    # Get the announcement from the request
    announcement_type = request.form.get('type')
    display_icon = request.form.get('icon')
    title = request.form.get('title')
    message = request.form.get('message')

    # Save the announcement to announcement.json and beautify it
    with open('announcement.json', 'w') as f:
        f.write(f'''{{\n\t"enable": true,\n\t"type": "{announcement_type}",\n\t"icon": "{display_icon}",\n\t"title": "{title}",\n\t"message": "{message}"\n}}''')

    return jsonify({ 'message': 'Announcement sent!' }), HTTPStatus.OK