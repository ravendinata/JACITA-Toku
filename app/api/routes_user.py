import copy
import json

from flask import jsonify, request, session
from flask_wtf.csrf import generate_csrf

import helper.trail as trail
from app.api import api
from app.extensions import csrf, db
from app.models.user import User
from helper.auth import generate_password_hash, is_authenticated
from helper.endpoint import HTTPStatus, check_fields, check_api_permission
from helper.role import Role

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
@check_api_permission('user/administer')
@check_fields('user/create')
def api_create_user():
    acting_user = request.form.get('created_by')
    if acting_user != session.get('user'):
        trail.log_system_event("api.user.create", f"User fingerprint mismatch. User in Form: {acting_user}, Session User: {session.get('user')}. Request denied.")
        return jsonify({ 'error': 'User fingerprint mismatch',
                         'details': f"Are you trying to impersonate someone? Logged in user does not match the fulfiller in the request." }), HTTPStatus.FORBIDDEN

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

    trail.log_creation(user, acting_user)
    return jsonify({ 'message': 'User created', 'user_details': user.to_dict() }), HTTPStatus.CREATED

@api.route('/user/<string:username>', methods = ['PATCH'])
@check_fields('user/update')
def api_update_user(username):
    acting_user = request.form.get('modified_by')
    if acting_user != session.get('user'):
        trail.log_system_event("api.user.update", f"User fingerprint mismatch. User in Form: {acting_user}, Session User: {session.get('user')}. Request denied.")
        return jsonify({ 'error': 'User fingerprint mismatch',
                         'details': f"Are you trying to impersonate someone? Logged in user does not match the fulfiller in the request." }), HTTPStatus.FORBIDDEN

    user = User.query.get(username)
    old_user = copy.deepcopy(user)

    if user is None:
        return jsonify({ 'error': 'User not found' }), HTTPStatus.NOT_FOUND

    user.first_name = request.form.get('first_name', user.first_name)
    user.last_name = request.form.get('last_name', user.last_name)
    user.email = request.form.get('email', user.email)
    user.division_id = request.form.get('division_id', user.division_id)

    try:
        db.session.commit()
    except Exception as e:
        print(f"Error while updating user: {e}")
        return jsonify({ 'error': 'Error while updating user', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR

    trail.log_update(user, old_user, acting_user)
    return jsonify({ 'message': 'User updated', 'new_user_details': user.to_dict() }), HTTPStatus.OK

@api.route('/user/<string:username>', methods = ['DELETE'])
@check_fields('user/delete')
def api_delete_user(username):
    acting_user = request.form.get('deleted_by')
    if acting_user != session.get('user'):
        trail.log_system_event("api.user.delete", f"User fingerprint mismatch. User in Form: {username}, Session User: {session.get('user')}. Request denied.")
        return jsonify({ 'error': 'User fingerprint mismatch',
                         'details': f"Are you trying to impersonate someone? Logged in user does not match the fulfiller in the request." }), HTTPStatus.FORBIDDEN
    
    acting_user_obj = User.query.get(acting_user)
    if acting_user_obj.role not in [ Role.ADMINISTRATOR, Role.SYSTEM ] and acting_user != username:
        return jsonify({ 'error': 'Insufficient permission', 'details': 'Only administrators and system users can delete other users' }), HTTPStatus.FORBIDDEN

    user = User.query.get(username)

    if user is None:
        return jsonify({ 'error': 'User not found' }), HTTPStatus.NOT_FOUND

    try:
        db.session.delete(user)
        db.session.commit()
    except Exception as e:
        print(f"Error while deleting user: {e}")
        return jsonify({ 'error': 'Error while deleting user', 'details': f"{e}" }), HTTPStatus.INTERNAL_SERVER_ERROR

    if 'user' in session and acting_user == username:
        session.pop('user')

    trail.log_deletion(user, acting_user)
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
@check_fields('auth/login')
@csrf.exempt
def api_login_user():

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

    with open('config.json') as config_file:
        config = json.load(config_file)

    csrf_token = generate_csrf(config['app_secret_key'])

    trail.log_login(user.username, request.remote_addr)
    return jsonify({ 'success': True, 'message': 'Login successful', 'csrf_token': csrf_token }), HTTPStatus.OK

@api.route('/auth/logout', methods = ['POST'])
def api_logout_user():
    if not is_authenticated():
        return jsonify({ 'success': False, 'error': 'User not logged in' }), HTTPStatus.UNAUTHORIZED

    user = session.get('user')
    session.clear()

    trail.log_logout(user)
    return jsonify({ 'success': True, 'message': 'Logout successful' }), HTTPStatus.OK