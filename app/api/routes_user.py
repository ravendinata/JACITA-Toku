import copy

from flask import jsonify, request, session
from sqlalchemy import desc

import helper.trail as trail
from app.api import api
from app.extensions import db
from app.models.user import User
from helper.auth import generate_password_hash, is_authenticated
from helper.endpoint import HTTPStatus, check_fields, check_api_permission

@api.route('/users', methods = ['GET'])
def api_get_users():
    users = User.query.all()
    return jsonify([ user.to_dict() for user in users ]), HTTPStatus.OK

@api.route('/users/<string:username>', methods = ['GET'])
def api_get_user(username):
    user = User.query.get(username)

    if user is None:
        return jsonify({ 'error': 'User not found' }), HTTPStatus.NOT_FOUND
    
    return jsonify(user.to_dict()), HTTPStatus.OK

@api.route('/users', methods = ['POST'])
def api_create_user():
    check_field = check_fields(request, 'user/create')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST

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
        return jsonify({ 'error': 'User already exists' }), HTTPStatus.CONFLICT

    user = User(username = username, password = password, 
                first_name = first_name, last_name = last_name, 
                division_id = division_id, role = role,
                email = email)
    
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        print(f"Error while creating user: {e}")
        return jsonify({ 'error': 'Error while creating user', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR

    trail.log_creation(user, session.get('user'))
    return jsonify({ 'message': 'User created', 'user_details': user.to_dict() }), HTTPStatus.CREATED

@api.route('/user/<string:username>', methods = ['PATCH'])
def api_update_user(username):
    check_field = check_fields(request, 'user/update')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST

    user = User.query.get(username)
    old_user = copy.deepcopy(user)

    if user is None:
        return jsonify({ 'error': 'User not found' }), HTTPStatus.NOT_FOUND

    user.first_name = request.form.get('first_name', user.first_name)
    user.last_name = request.form.get('last_name', user.last_name)
    user.email = request.form.get('email', user.email)
    user.division_id = request.form.get('division_id', user.division_id)

    db.session.commit()

    trail.log_update(user, old_user, session.get('user'))
    return jsonify({ 'message': 'User updated', 'new_user_details': user.to_dict() }), HTTPStatus.OK

@api.route('/user/<string:username>', methods = ['DELETE'])
def api_delete_user(username):
    user = User.query.get(username)

    if user is None:
        return jsonify({ 'error': 'User not found' }), HTTPStatus.NOT_FOUND

    db.session.delete(user)
    db.session.commit()

    if 'user' in session:
        session.pop('user')

    trail.log_deletion(user, session.get('user'))
    return jsonify({ 'message': 'User deleted' }), HTTPStatus.OK

@api.route('/user/<string:username>/change_password', methods = ['POST'])
def api_change_password(username):
    user = User.query.get(username)

    if user is None:
        return jsonify({ 'error': 'User not found' }), HTTPStatus.NOT_FOUND

    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')

    if user.check_password(old_password) is False:
        return jsonify({ 'error': 'The old password is incorrect' }), HTTPStatus.UNAUTHORIZED

    user.set_password(new_password)
    db.session.commit()

    return jsonify({ 'message': 'Password changed' }), HTTPStatus.OK

@api.route('/user/<string:username>/change_password/bypass', methods = ['POST'])
@check_api_permission('user/administer')
def api_reset_password(username):
    user = User.query.get(username)

    if user is None:
        return jsonify({ 'error': 'User not found' }), HTTPStatus.NOT_FOUND

    password = request.form.get('password')

    user.set_password(password)
    db.session.commit()

    return jsonify({ 'message': 'Password reset' }), HTTPStatus.OK

@api.route('/auth/login', methods = ['POST'])
def api_login_user():
    check_field = check_fields(request, 'auth/login')
    if not check_field['pass']:
        return jsonify(check_field), HTTPStatus.BAD_REQUEST

    username = request.form.get('username')
    password = request.form.get('password')

    if is_authenticated():
        return jsonify({ 'success': False, 'error': 'User already logged in', 'session': session['user'] }), HTTPStatus.CONFLICT

    user = User.query.get(username)

    if user is None:
        return jsonify({ 'success': False, 'error': 'User not found' }), HTTPStatus.NOT_FOUND

    if user.check_password(password) is False:
        return jsonify({ 'success': False, 'error': 'Invalid password' }), HTTPStatus.UNAUTHORIZED
    
    # SUCCESS - Session setup
    session['user'] = user.username
    
    if 'next' in session:
        session.pop('next')

    trail.log_login(user.username, request.remote_addr)
    return jsonify({ 'success': True, 'message': 'Login successful' }), HTTPStatus.OK

@api.route('/auth/logout', methods = ['POST'])
def api_logout_user():
    if not is_authenticated():
        return jsonify({ 'success': False, 'error': 'User not logged in' }), HTTPStatus.UNAUTHORIZED

    user = session.get('user')
    session.clear()

    trail.log_logout(user)
    return jsonify({ 'success': True, 'message': 'Logout successful' }), HTTPStatus.OK