from flask import jsonify, request

from app.api import api
from app.extensions import db
from app.models.user import User
from helper.auth import generate_password_hash

@api.route('/users', methods = ['GET'])
def api_get_users():
    users = User.query.all()
    return jsonify([ user.to_dict() for user in users ])

@api.route('/users/<string:username>', methods = ['GET'])
def api_get_user(username):
    user = User.query.get(username)

    if user is None:
        return jsonify({ 'error': 'User not found' }), 404
    
    return jsonify(user.to_dict())

@api.route('/users', methods = ['POST'])
def api_create_user():
    required_fields = ['username', 'first_name', 'last_name', 'division_id', 'role', 'email', 'password']
    if not all([ field in request.form for field in required_fields ]):
        return jsonify({ 'error': 'Missing required fields', 'required_fields': required_fields }), 400

    username = request.form.get('username')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    division_id = request.form.get('division_id')
    role = request.form.get('role')
    email = request.form.get('email')

    password = request.form.get('password')
    password = generate_password_hash(password)

    check_user = User.query.get(username)
    if check_user:
        return jsonify({ 'error': 'User already exists' }), 400

    user = User(username = username, password = password, 
                first_name = first_name, last_name = last_name, 
                division_id = division_id, role = role,
                email = email)
    
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        print(f"Error while creating user: {e}")
        return jsonify({ 'error': 'Error while creating user', 'details': f"{e}" }), 500

    return jsonify({ 'message': 'User created', 'user_details': user.to_dict() })

@api.route('/user/<string:username>', methods = ['PATCH'])
def api_update_user(username):
    user = User.query.get(username)

    if user is None:
        return jsonify({ 'error': 'User not found' }), 404
    
    modifiable_fields = ['first_name', 'last_name', 'email', 'division_id']
    if not any([ request.form.get(field) for field in modifiable_fields ]):
        return jsonify({ 'error': 'No modifiable fields provided' }), 400

    user.first_name = request.form.get('first_name', user.first_name)
    user.last_name = request.form.get('last_name', user.last_name)
    user.email = request.form.get('email', user.email)
    user.division_id = request.form.get('division_id', user.division_id)

    db.session.commit()

    return jsonify({ 'message': 'User updated', 'new_user_details': user.to_dict() })

@api.route('/user/<string:username>', methods = ['DELETE'])
def api_delete_user(username):
    user = User.query.get(username)

    if user is None:
        return jsonify({ 'error': 'User not found' }), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({ 'message': 'User deleted' })

@api.route('/user/<string:username>/change_password', methods = ['POST'])
def api_change_password(username):
    user = User.query.get(username)

    if user is None:
        return jsonify({ 'error': 'User not found' }), 404

    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')

    if user.check_password(old_password) is False:
        return jsonify({ 'error': 'Invalid password' }), 401

    user.set_password(new_password)
    db.session.commit()

    return jsonify({ 'message': 'Password changed' })

@api.route('/auth/login', methods = ['POST'])
def api_login_user():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.get(username)

    if user is None:
        return jsonify({ 'success': False, 'error': 'User not found' }), 404

    if user.check_password(password) is False:
        return jsonify({ 'success': False, 'error': 'Invalid password' }), 401

    return jsonify({ 'success': True, 'message': 'Login successful' })